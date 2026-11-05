# -*- coding: utf-8 -*-
"""Çekirdek: IDS okuma, denetim ve düzeltme (sentetik küçük IFC ile)."""
import os
import shutil

from conftest import IDS, MINI

from checker import denetle
from ids_reader import ids_oku
from ifc_model import IfcModel
import engine


def test_ids_161_kural():
    bilgi, kurallar = ids_oku(IDS)
    assert len(kurallar) == 161


def test_denetim_calisir():
    _, kurallar = ids_oku(IDS)
    oz, son = denetle(IfcModel(MINI), kurallar)
    assert son, "hiç kontrol üretilmedi"
    duvar = [o for o in oz if o["sinif"] == "IFCWALL" and o["eleman"]]
    assert duvar, "IfcWall kuralı uygulanmadı"


def test_duzeltme_hata_azaltir(tmp_path):
    ifc = tmp_path / "mini.ifc"
    shutil.copy(MINI, ifc)
    ayar = {"bina_adi": "MM-BNA-A_BLOK", "bina_uzun_ad": "A Blok", "proje_adi": "MM-PRJ-202645", "disiplin": "MM"}
    r = engine.calistir(str(ifc), True, ayar, None, None, None, ids_yolu=IDS, log=lambda *a: None)
    assert r["sonra"] < r["once"], (r["once"], r["sonra"])
    assert os.path.isfile(r["cikti"]) and os.path.isfile(r["rapor"])
    m = IfcModel(r["cikti"])
    w = list(m.f.of("IFCWALL"))[0]
    assert m.name(w) == "MM-DVR-YTONG"                                   # Ek-5 ad biçimi
    assert m.psets(w)["Pset_WallCommon"]["FireRating"][0] == "120"      # F120 -> 120
    b = list(m.f.of("IFCBUILDING"))[0]
    assert m.name(b) == "MM-BNA-A_BLOK"


def test_cikti_yolu_yalniz_ad(tmp_path):
    """R10 hatası: 'Çıktı IFC' alanına yalnız ad yazılınca IFC'nin klasörüne yazılmalı."""
    ifc = tmp_path / "mini.ifc"
    shutil.copy(MINI, ifc)
    r = engine.calistir(str(ifc), True, {"disiplin": "MM"}, None, "yalniz_ad", None, ids_yolu=IDS, log=lambda *a: None)
    assert r["cikti"] == str(tmp_path / "yalniz_ad.ifc")
