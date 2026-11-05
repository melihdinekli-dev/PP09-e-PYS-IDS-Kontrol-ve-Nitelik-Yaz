# -*- coding: utf-8 -*-
"""'ALLPLAN modeline nitelik yaz' bölümü – Allplan taklidiyle (tests/mock).

Gerçek Allplan'ın yerini tutmaz: her sürümden önce docs/ALLPLAN_TEST.md listesiyle Allplan'da da denenir.
"""
import importlib.util
import os
import sys
import xml.etree.ElementTree as ET

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOCK = os.path.join(ROOT, "tests", "mock")


class _P:
    def __init__(s, v):
        s.value = v


class _BE:
    pass


@pytest.fixture()
def pp(paket_dizini, tmp_path, monkeypatch):
    """PythonPart'ı .pyp'deki varsayılan palet değerleriyle başlatır."""
    monkeypatch.setenv("TEMP", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    for p in (MOCK, str(paket_dizini)):
        if p not in sys.path:
            sys.path.insert(0, p)
    import NemAll_Python_BaseElements as BE
    import NemAll_Python_Utility as UT
    from ScriptObjectInteractors import MultiElementSelectInteractor as MSI
    BE.WRITES.clear(); UT.MSG.clear(); MSI.START.clear()
    be = _BE()
    root = ET.parse(str(paket_dizini / "e-PYS IDS Kontrol.pyp")).getroot()
    for c in root.iter("Constant"):
        setattr(be, c.find("Name").text, int(c.find("Value").text))
    for prm in root.iter("Parameter"):
        n = prm.find("Name").text
        vt = prm.find("ValueType").text
        v = prm.find("Value")
        v = v.text if v is not None else None
        if vt in ("Row", "Expander", "RadioButton", "Button", "Separator", "Text"):
            continue
        if vt == "CheckBox":
            v = (v == "True")
        elif vt == "RadioButtonGroup":
            v = int(v)
        elif vt == "AttributeIdValue":
            v = []
        else:
            v = v or ""
        setattr(be, n, _P(v))
    spec = importlib.util.spec_from_file_location("ePYS_IDS", str(paket_dizini / "ePYS_IDS.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(os, "startfile", lambda p: None, raising=False)
    o = mod.create_script_object(be, None)
    o.start_input()
    be.Calisma.value = 2
    return o, be, BE, UT


def sec(o, *ele):
    o.sel.sel_elements = list(ele)
    o.start_next_input()


def E(*a, **k):
    from NemAll_Python_IFW_ElementAdapter import Ele
    return Ele(*a, **k)


def test_varsayilanlar(pp):
    o, be, *_ = pp
    assert be.NY_Islem.value == "Nitelik yaz"
    assert be.NY_Dolu.value == "Dokunma, yalnız boşlara yaz"
    assert be.KapiPencereHedef.value == "Boşluk + ParaObje"
    assert be.CatTumu.value is True and be.OzetGoster.value is True


def test_tumu_kutulari(pp):
    o, be, *_ = pp
    be.CatTavan.value = False
    assert o.modify_element_property("CatTavan", False)
    assert be.CatGrupKaplama.value is False and be.CatTumu.value is False
    o.modify_element_property("CatGrupKaplama", True)
    assert be.CatTavan.value is True and be.CatTumu.value is True
    o.modify_element_property("CatTumu", False)
    assert be.CatDuvar.value is False and be.CatGrupStatik.value is False


def test_secim_yeniden_baslatilmaz(pp):
    """R17: üst seçenek / İşlem değişince seçim ikinci kez başlatılıyordu -> Allplan kapanıyordu."""
    o, be, *_ = pp
    from ScriptObjectInteractors import MultiElementSelectInteractor as MSI
    once = o.script_object_interactor
    o.modify_element_property("Calisma", 2)
    o.modify_element_property("NY_Islem", "Önce dene (yazmadan rapor ver)")
    assert o.script_object_interactor is once
    assert MSI.START == []


def test_dene_yazmaz_yaz_yazar(pp):
    o, be, BE, UT = pp
    be.Y_Yangin.value = True
    duvar = E("Wall", {1002: ""}, children=[E("WallTier")])
    be.NY_Islem.value = "Önce dene (yazmadan rapor ver)"
    sec(o, duvar.children[0])
    assert BE.WRITES == [] and "Deneme" in be.SonAtama.value
    be.NY_Islem.value = "Nitelik yaz"
    sec(o, duvar.children[0])
    assert duvar.attrs[1002] == "120"                       # katman seçildi, ana duvara yazıldı
    assert all(w[2] == (False, False) for w in BE.WRITES)    # R16: PP02'de denenmiş çağrı


def test_tanimsiz_bos_sayilir(pp):
    """R19: Allplan boş niteliği '<tanımsız>' olarak veriyor."""
    o, be, *_ = pp
    be.Y_Yangin.value = True
    d = E("Wall", {1002: "<tanımsız>"})
    sec(o, d)
    assert d.attrs[1002] == "120"


def test_dolu_nitelige_dokunmaz(pp):
    o, be, *_ = pp
    be.Y_Yangin.value = True
    d = E("Wall", {1002: "180"})
    sec(o, d)
    assert d.attrs[1002] == "180"
    be.NY_Dolu.value = "Üzerine yaz"
    sec(o, d)
    assert d.attrs[1002] == "120"


@pytest.mark.parametrize("hedef,beklenen", [("Boşluk + ParaObje", ["Door", "DoorOpeningSmartPart"]),
                                            ("Boşluk", ["Door"]), ("ParaObje", ["DoorOpeningSmartPart"])])
def test_kapi_paraobje(pp, hedef, beklenen):
    o, be, BE, _ = pp
    be.Y_Yangin.value = True
    be.KapiPencereHedef.value = hedef
    sp = E("DoorOpeningSmartPart")
    E("Door", children=[E("DoorTier", children=[sp])])
    sec(o, sp)
    assert BE.WRITES[-1][1] == beklenen


def test_odadaki_kaplamalar_ve_baca(pp):
    o, be, BE, _ = pp
    be.Y_Yangin.value = True
    oda = E("Room", children=[E("CeilingFinish"), E("FloorFinish"), E("SideSurfaceFinish"), E("Baseboard")])
    baca = E("Chimney", children=[E("WallTier"), E("WallTier")])
    sec(o, oda, baca.children[0], baca.children[1])
    tipler = sorted(t for w in BE.WRITES for t in w[1])
    assert tipler == ["Baseboard", "CeilingFinish", "FloorFinish", "SideSurfaceFinish", "WallTier", "WallTier"]
    assert "Baca 2" in "\n".join(o.ozet)                    # R21: baca katmanı Baca sayılır, kendisine yazılır


def test_nitelik_isaretli_degilse_uyarir(pp):
    o, be, BE, _ = pp
    sec(o, E("Wall"))
    assert BE.WRITES == [] and be.SonAtama.value == "Yazılacak nitelik işaretlenmedi"


def test_nitelik_sil(pp):
    o, be, *_ = pp
    be.Y_Yangin.value = True
    be.NY_Islem.value = "Nitelik sil"
    d = E("Wall", {1002: "120"})
    sec(o, d)
    assert d.attrs[1002] == "" and "silindi" in be.SonAtama.value


def test_ozet_ve_rapor(pp, tmp_path):
    o, be, _, UT = pp
    be.Y_Yangin.value = True
    sec(o, E("Wall"))
    assert UT.MSG and "Sonuç:" in UT.MSG[-1]
    rapor = be.SonRapor.value
    assert os.path.isfile(rapor) and "e-PYS IDS Raporları" in rapor   # R20
