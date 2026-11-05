# -*- coding: utf-8 -*-
# Telif Hakkı (c) 2026 ALUPLAN – Allplan Türkiye Distribütörü. Tüm hakları saklıdır.
# Kapalı kaynak, tescilli yazılım – bkz. LICENSE. Yetkisiz kopyalama ve dağıtım yasaktır.
"""PP09 e-PYS IDS Kontrol ve Nitelik Atama – Allplan 2026 – ALUPLAN

İki iş yapar:
  1) IFC Denetim / Düzelt: Allplan'dan alınan IFC'yi bakanlığın e-PYS IDS kurallarına
     göre denetler, dosyadaki bilgilerle düzeltir (<ad>_IDS.ifc) ve Excel rapor yazar.
  2) Nitelik Ata: seçilen elemanlara IDS'in istediği nitelikleri (İsim, Yangın dayanımı,
     Dış eleman, Taşıyıcı, Kaçış yolu, Malzeme, IFC obje kategorisi + serbest nitelikler)
     tek seferde yazar ya da yalnız ön kontrol raporu verir.
"""
from __future__ import annotations

import os
import re
import sys
import time
import datetime
import traceback

import NemAll_Python_BaseElements as AllplanBaseEle
import NemAll_Python_IFW_ElementAdapter as AllplanEleAdapter
import NemAll_Python_Utility as AllplanUtil

from BaseScriptObject import BaseScriptObject, BaseScriptObjectData
from CreateElementResult import CreateElementResult
from ScriptObjectInteractors.MultiElementSelectInteractor import MultiElementSelectInteractor, MultiElementSelectInteractorResult
from ScriptObjectInteractors.OnCancelFunctionResult import OnCancelFunctionResult

_DIR = os.path.dirname(os.path.abspath(__file__))
if _DIR not in sys.path:
    sys.path.insert(0, _DIR)

import importlib                       # noqa: E402
import ePYS_IDS_core as core          # noqa: E402
try:
    importlib.reload(core)            # Allplan açıkken güncellenen çekirdeği yükle
except Exception:
    pass

SURUM = "R21"
LOG = os.path.join(os.environ.get("TEMP", _DIR), "ePYS_IDS.log")
# R20: nitelik yazma raporları Belgeler\e-PYS IDS Raporları klasörüne (IFC raporu IFC'nin yanına) yazılır
RAPOR_KLASOR = os.path.join(os.path.expanduser("~"), "Documents", "e-PYS IDS Raporları")
SON_RAPOR_DOSYA = os.path.join(os.environ.get("TEMP", _DIR), "ePYS_IDS_son_rapor.txt")


def log(*a):
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(datetime.datetime.now().strftime("%H:%M:%S ") + " ".join(str(x) for x in a) + "\n")
    except Exception:
        pass


try:
    with open(LOG, "w", encoding="utf-8") as _f:
        _f.write("Script yüklendi %s – %s\n" % (SURUM, datetime.datetime.now().strftime("%d.%m.%Y %H:%M")))
except Exception:
    pass


def check_allplan_version(_build_ele, _version):
    return True


def create_preview(build_ele, _doc):
    try:
        from Utils import LibraryBitmapPreview
        png = os.path.join(build_ele.pyp_file_path, os.path.splitext(os.path.basename(build_ele.pyp_file_name))[0] + ".png")
        return CreateElementResult(LibraryBitmapPreview.create_library_bitmap_preview(png))
    except Exception:
        return CreateElementResult()


def create_script_object(build_ele, script_object_data: BaseScriptObjectData):
    return EpysIds(build_ele, script_object_data)


# ---------------------------------------------------------------- eleman kategorileri
# R12: Eleman tanıma PP02 e-PYS Nitelik Yaz R62'den aktarıldı (Allplan tip UUID'si + tip adı,
# ParaObje -> kapı/pencere, katman/parça -> ana eleman, mahal içindeki kaplamalar).
# Kategori: (palet kutusu, palette görünen ad, aile). Aile, yazma/kontrol kurallarında kullanılır.
from collections import OrderedDict  # noqa: E402

NY_KAT = OrderedDict([
    # Statik
    ("TEMEL",        ("CatTemel",         "Temel",            "Temel")),
    ("KOLON",        ("CatKolon",         "Kolon",            "Kolon")),
    ("KIRIS",        ("CatKiris",         "Kiriş",            "Kiriş")),
    ("DOSEME",       ("CatDoseme",        "Döşeme",           "Döşeme")),
    ("MERDIVEN",     ("CatMerdiven",      "Merdiven",         "Merdiven")),
    # Mimari
    ("DUVAR",        ("CatDuvar",         "Duvar",            "Duvar")),
    ("BACA",         ("CatBaca",          "Baca",             "Baca")),
    ("ODA",          ("CatOda",           "Oda",              "Mahal")),
    ("KORKULUK",     ("CatKorkuluk",      "Korkuluk",         "Korkuluk")),
    ("GIYDIRME",     ("CatGiydirme",      "Giydirme Cephe",   "Giydirme Cephe")),
    ("CATI_ORTU",    ("CatCatiOrtu",      "Çatı Örtüsü",      "Çatı")),
    ("CATI_PENCERE", ("CatCatiPencere",   "Çatı Penceresi",   "Pencere")),
    ("KAPI",         ("CatKapi",          "Kapı",             "Kapı")),
    ("PENCERE",      ("CatPencere",       "Pencere",          "Pencere")),
    # Kaplama (IFC'de IfcCovering)
    ("DUVAR_KPL",    ("CatDuvarKpl",      "Duvar Kaplaması",  "Kaplama")),
    ("TAVAN",        ("CatTavan",         "Tavan Kaplaması",  "Kaplama")),
    ("DOSEME_KPL",   ("CatDosemeKpl",     "Döşeme Kaplaması", "Kaplama")),
    ("SUPURGELIK",   ("CatSupurgelik",    "Süpürgelik",       "Kaplama")),
])
NY_GRUP = OrderedDict([
    ("CatGrupStatik",  ["TEMEL", "KOLON", "KIRIS", "DOSEME", "MERDIVEN"]),
    ("CatGrupMimari",  ["DUVAR", "BACA", "ODA", "KORKULUK", "GIYDIRME", "CATI_ORTU", "CATI_PENCERE",
                        "KAPI", "PENCERE"]),
    ("CatGrupKaplama", ["DUVAR_KPL", "TAVAN", "DOSEME_KPL", "SUPURGELIK"]),
])
KAPLAMA_KAT = ("DUVAR_KPL", "TAVAN", "DOSEME_KPL", "SUPURGELIK")
KAPI_PENCERE = ("KAPI", "PENCERE")

# Aile -> (EK-5 kodu, varsayılan disiplin)
KAT = {
    "Duvar": ("DVR", "MM"), "Kolon": ("KLN", "ST"), "Kiriş": ("KRS", "ST"), "Döşeme": ("DSM", "ST"),
    "Temel": ("TML", "ST"), "Merdiven": ("MRD", "MM"), "Kapı": ("KAP", "MM"), "Pencere": ("PNC", "MM"),
    "Korkuluk": ("KRK", "MM"), "Giydirme Cephe": ("GDC", "MM"), "Çatı": ("CAT", "MM"), "Baca": ("BAC", "MM"),
    "Kaplama": ("KPL", "MM"), "Mahal": (None, "MM"),
}
YAPISAL = {"Kolon", "Kiriş", "Döşeme", "Temel"}

# Kapı / pencere: niteliğin yazılacağı yer
DW_BOTH = "Boşluk + ParaObje"
DW_OPENING = "Boşluk"
DW_PARAOBJE = "ParaObje"
# İşlem ve dolu nitelik seçenekleri (palette açılır liste)
ISLEM_YAZ = "Nitelik yaz"
ISLEM_DENE = "Önce dene (yazmadan rapor ver)"
ISLEM_KONTROL = "Yalnız kontrol et (rapor)"
ISLEM_SIL = "Nitelik sil"
DOLU_BOS = "Dokunma, yalnız boşlara yaz"
DOLU_UZERINE = "Üzerine yaz"

# Ara sınıflar: üst/alt elemana bakılarak kesin kategoriye çevrilir
RAW_SMARTPART = "_SMARTPART"
RAW_ROOF_OPENING = "_ROOF_OPENING"
RAW_YOK = "_YOK"

TYPE_UUID_NAMES = {
    "TEMEL":    ["IndividualFoundation_TypeUUID", "StripFoundation_TypeUUID",
                 "SlabFoundation_TypeUUID", "SlabFoundationTier_TypeUUID", "BlockFoundation_TypeUUID"],
    "KOLON":    ["Column_TypeUUID"],
    "KIRIS":    ["Beam_TypeUUID", "Downstand_TypeUUID", "Upstand_TypeUUID", "UpstandBeam_TypeUUID", "Joist_TypeUUID"],
    "DOSEME":   ["Slab_TypeUUID"],
    "MERDIVEN": ["Stair_TypeUUID", "Stairs_TypeUUID", "Staircase_TypeUUID", "StairCase_TypeUUID",
                 "StairModel_TypeUUID"],
    "DUVAR":    ["WallTier_TypeUUID", "CircularWallTier_TypeUUID", "PolygonWallTier_TypeUUID",
                 "SplineWallTier_TypeUUID"],
    "BACA":     ["Chimney_TypeUUID", "ChimneyTier_TypeUUID"],
    "KORKULUK": ["Railing_TypeUUID", "RailingTier_TypeUUID", "Rail_TypeUUID", "SubRail_TypeUUID"],
    "PENCERE":  ["WindowTier_TypeUUID", "Window_TypeUUID"],
    "KAPI":     ["DoorTier_TypeUUID", "Door_TypeUUID"],
    "GIYDIRME": ["CurtainWall_TypeUUID", "CurtainWallTier_TypeUUID", "Facade_TypeUUID", "FacadeElement_TypeUUID"],
    "ODA":      ["Room_TypeUUID"],
    "CATI_ORTU": ["RoofCovering_TypeUUID", "RoofCoveringTier_TypeUUID", "RoofSkin_TypeUUID"],
    "CATI_PENCERE": ["RoofWindow_TypeUUID", "RoofCoveringWindow_TypeUUID", "Skylight_TypeUUID"],
    RAW_SMARTPART: ["SmartPart_TypeUUID"],
    RAW_ROOF_OPENING: ["RoofCoveringOpening_TypeUUID", "RoofOpening_TypeUUID"],
    RAW_YOK: ["SmartSymbol_TypeUUID", "MacroPlacement_TypeUUID", "Macro_TypeUUID",
              "SlabOpening_TypeUUID", "SlabRecess_TypeUUID"],
}

TYPE_NAME_SPECIAL = [
    ("CATI_PENCERE",   ["roofwindow", "roof window", "dachfenster", "skylight"]),
    (RAW_ROOF_OPENING, ["roofcoveringopening", "roofopening", "dachöffnung", "dachoeffnung"]),
    (RAW_YOK,          ["slabopening", "slabrecess", "deckenöffnung", "deckenoeffnung", "deckenaussparung",
                        "smartsymbol", "smart symbol", "macroplacement", "makro", "macro"]),
    (RAW_SMARTPART,    ["smartpart"]),
]
TYPE_NAME_KEYWORDS = [
    ("CATI_ORTU", ["roofcovering", "roof covering", "dachhaut", "dachdeckung", "roofskin"]),
    ("GIYDIRME", ["curtainwall", "curtain wall", "facade", "fassade", "cephe"]),
    ("MERDIVEN", ["stair", "treppe", "merdiven"]),
    ("ODA",      ["room", "raum", "oda"]),
    ("TEMEL",    ["foundation", "fundament", "temel"]),
    ("PENCERE",  ["window", "fenster", "pencere"]),
    ("KAPI",     ["door", "kapı", "kapi"]),
    ("KORKULUK", ["railing", "geländer", "gelaender", "korkuluk"]),
    ("BACA",     ["chimney", "schornstein", "baca"]),
    ("KOLON",    ["column", "stütze", "stuetze", "kolon"]),
    ("KIRIS",    ["beam", "unterzug", "überzug", "ueberzug", "joist", "downstand", "upstand", "kiriş", "kiris"]),
    ("DOSEME",   ["slab", "decke", "döşeme", "doseme"]),
    ("DUVAR",    ["wall", "wand", "duvar"]),
]
TYPE_NAME_EXCLUDE = ["opening", "öffnung", "oeffnung", "niche", "nische", "recess", "aussparung",
                     "label", "text", "dimension", "axis", "joint", "container", "group",
                     "reinf", "bars", "mesh", "pythonpart", "hatch", "line"]
PART_EXCLUDE = ["reveal", "sill", "swing", "leibung", "schwelle", "anschlag"]
PROMOTE_SKIP = {"TEMEL", "KOLON", "KIRIS", "DOSEME", "MERDIVEN"}
PROMOTE_PARENTS = ["wall", "door", "window", "windowdoor", "chimney", "railing", "rail",
                   "facade", "roofcovering", "hyperroofcovering", "room"]


def kaplama_kat(type_name):
    """Allplan kaplama (IfcCovering) tip adı -> kategori; değilse None."""
    n = (type_name or "").lower().replace("_typeuuid", "")
    if not n or any(x in n for x in ("smartsymbol", "macro", "label", "text", "dimension", "roof", "dach",
                                      "opening", "recess", "plan", "landscaping", "gelaende")):
        return None
    fin = ("finish", "surface", "cover", "cladding", "lining", "bekleid", "belag", "flaeche", "fläche")
    if any(w in n for w in ("baseboard", "skirting", "plinth", "leiste")):
        return "SUPURGELIK"
    if "ceiling" in n or ("decke" in n and any(w in n for w in fin)):
        return "TAVAN"
    if ("floor" in n or "boden" in n) and (any(w in n for w in fin) or n.endswith("ing")):
        return "DOSEME_KPL"
    if any(w in n for w in ("side", "vertical", "wall", "seiten", "wand")) and any(w in n for w in fin):
        return "DUVAR_KPL"
    return None


def ada_gore_kat(type_name):
    n = (type_name or "").lower()
    if not n or any(x in n for x in ("label", "text", "dimension")) or any(x in n for x in PART_EXCLUDE):
        return None
    for key, words in TYPE_NAME_SPECIAL:
        if any(w in n for w in words):
            return key
    cov = kaplama_kat(n)
    if cov:
        return cov
    if any(x in n for x in TYPE_NAME_EXCLUDE):
        return None
    for key, words in TYPE_NAME_KEYWORDS:
        if any(w in n for w in words):
            return key
    return None


def kesinlestir(raw, ust_tip=""):
    """Ara sınıfı üst elemana göre kesin kategoriye çevirir (ParaObje -> kapı/pencere)."""
    p = (ust_tip or "").lower()
    if raw == RAW_SMARTPART:
        if any(w in p for w in ("roof", "dach", "skylight")):
            return "CATI_PENCERE"
        if "door" in p or "tür" in p:
            return "KAPI"
        if "window" in p or "fenster" in p:
            return "PENCERE"
        return None
    if raw == RAW_ROOF_OPENING:
        return "CATI_PENCERE"
    return raw if raw in NY_KAT else None


def ust_elemana_cik(cocuk, ust):
    c = (cocuk or "").lower().replace("_typeuuid", "")
    p = (ust or "").lower().replace("_typeuuid", "")
    if not c or not p or p not in PROMOTE_PARENTS:
        return False
    if c.endswith("tier") and c[:-4] in (p, "circular" + p, "polygon" + p, "spline" + p):
        return True
    if c.startswith("sub") and c[3:] in (p, "facade", "rail") and p in ("facade", "rail", c[3:]):
        return True
    return False


def tip_bilgi(ele):
    try:
        t = ele.GetElementAdapterType()
        try:
            g = str(t.GetGuid())
        except Exception:
            g = ""
        return g, t.GetTypeName()
    except Exception:
        return "", ""


def tip_adi(ele):
    return tip_bilgi(ele)[1] or ""


def uuid_listesi():
    """[(TypeUUID, kategori)]; sürümde olmayan sabitler atlanır."""
    out = []
    for cat, names in TYPE_UUID_NAMES.items():
        for nm in names:
            uid = getattr(AllplanEleAdapter, nm, None)
            if uid is not None:
                out.append((uid, cat))
    try:
        for nm in dir(AllplanEleAdapter):
            if nm.endswith("_TypeUUID"):
                cat = kaplama_kat(nm)
                if cat:
                    out.append((getattr(AllplanEleAdapter, nm), cat))
    except Exception:
        pass
    return out


def ust(ele):
    try:
        p = AllplanEleAdapter.BaseElementAdapterParentElementService.GetParentElement(ele)
        if p is None or p.IsNull():
            return None
        return p
    except Exception:
        return None


def altlar(ele):
    try:
        return list(AllplanEleAdapter.BaseElementAdapterChildElementsService.GetChildModelElements(ele, True))
    except Exception:
        return []


def eid(ele):
    for m in ("GetElementUUID", "GetModelElementUUID"):
        try:
            v = str(getattr(ele, m)())
            if v and v != "00000000-0000-0000-0000-000000000000":
                return v
        except Exception:
            continue
    return str(id(ele))


def ham_sinif(ele, uuids):
    for uid, cat in uuids:               # Allplan örneklerindeki yöntem: ele == X_TypeUUID
        try:
            if ele == uid:
                return cat
        except Exception:
            break
    g, t = tip_bilgi(ele)
    for uid, cat in uuids:
        if g and g == str(uid):
            return cat
    return ada_gore_kat(t)


def kategori(ele, uuids):
    """(kategori ya da None, tip adı)"""
    raw = ham_sinif(ele, uuids)
    t = tip_adi(ele)
    if raw is None or raw == RAW_YOK:
        return None, t
    if raw in (RAW_SMARTPART, RAW_ROOF_OPENING):
        p = ust(ele)
        return kesinlestir(raw, tip_adi(p) if p is not None else ""), t
    if raw == "DUVAR":
        p = ust(ele)          # R19: bacanın katmanları Allplan'da WallTier olarak geliyor -> Baca
        if p is not None and "chimney" in tip_adi(p).lower():
            return "BACA", t
    return (raw if raw in NY_KAT else None), t


def ana_eleman(ele, kat):
    """Katman/parça ya da ParaObje seçildiyse niteliğin yazılacağı ana eleman (Allplan'da
    WallTier -> Wall, DoorTier/ParaObje -> Door, SubFacade -> Facade). Statik ve kaplamaya dokunmaz."""
    if kat in PROMOTE_SKIP or kat in KAPLAMA_KAT:
        return ele
    if kat == "BACA":
        return ele            # R21: baca katmanına (WallTier) kendisine yazılır – Allplan her katmanı ayrı IfcChimney olarak aktarıyor
    if "smartpart" in tip_adi(ele).lower() or kat in KAPI_PENCERE + ("CATI_PENCERE",):
        hedef = ("roofwindow", "skylight", "roofcoveringopening", "roofopening", "dachfenster") \
            if kat == "CATI_PENCERE" else ("door", "window", "windowdoor")
        cur = ele
        for _ in range(5):
            tl = tip_adi(cur).lower().replace("_typeuuid", "")
            if "smartpart" not in tl and ((tl in hedef) or (kat == "CATI_PENCERE" and any(w in tl for w in hedef))):
                return cur
            p = ust(cur)
            if p is None:
                break
            cur = p
        if "smartpart" in tip_adi(ele).lower():
            return ele
    cur = ele
    for _ in range(5):
        p = ust(cur)
        if p is None:
            break
        ct, pt = tip_adi(cur), tip_adi(p)
        if ust_elemana_cik(ct, pt) or ("subfacade" in ct.lower() and "subfacade" in pt.lower()):
            cur = p
            continue
        break
    return cur


def kaplamalari_ekle(secim, acik):
    """Kaplamalar Allplan'da mahalin alt öğesidir; pencereyle seçimde yalnız mahal gelir.
    Kaplama kutuları açıksa seçilen elemanların altındaki kaplamalar da seçime eklenir."""
    if not any(acik.get(k) for k in KAPLAMA_KAT):
        return list(secim), 0
    out = list(secim)
    have = {eid(e) for e in out}
    eklenen = 0
    for ele in list(secim):
        level = [ele]
        for _ in range(3):
            nxt = []
            for o in level:
                for k in altlar(o):
                    nxt.append(k)
                    if kaplama_kat(tip_adi(k)) and eid(k) not in have:
                        have.add(eid(k))
                        out.append(k)
                        eklenen += 1
            level = nxt
            if not level:
                break
    return out, eklenen


def paraobjeler(ele):
    """Kapı/pencerenin içindeki ParaObje'ler (…OpeningSmartPart)."""
    found, level, seen = [], [ele], set()
    for _ in range(4):
        nxt = []
        for o in level:
            for k in altlar(o):
                if eid(k) in seen:
                    continue
                seen.add(eid(k))
                nxt.append(k)
                if "smartpart" in tip_adi(k).lower():
                    found.append(k)
        level = nxt
        if not level:
            break
    return found


def ele_key(ele):
    for m in ("GetModelElementUUID", "GetElementUUID"):
        try:
            return str(getattr(ele, m)())
        except Exception:
            pass
    return str(id(ele))


def oku_nitelikler(ele):
    try:
        return dict(ele.GetAttributes(AllplanBaseEle.eAttibuteReadState.ReadAll))
    except Exception:
        try:
            return dict(AllplanBaseEle.ElementsAttributeService.GetAttributes(ele))
        except Exception:
            return {}


class _Progress:
    """R16: PP02 R61'deki ilerleme çubuğu (Allplan'da denenmiş yol). Açılamazsa sessizce devre dışı."""
    MIN_STEPS = 30

    def __init__(self, total):
        self.bar, self.left = None, 0
        try:
            total = int(total)
            if total >= self.MIN_STEPS:
                self.bar = AllplanUtil.ProgressBar(total, 0, False)
                self.left = total
        except Exception:
            self.bar = None

    def step(self):
        if self.bar is None or self.left <= 0:
            return
        try:
            self.bar.Step()
            self.left -= 1
        except Exception:
            self.bar = None

    def close(self):
        if self.bar is None:
            return
        try:
            while self.left > 0:
                self.bar.Step()
                self.left -= 1
            for fn in ("CloseProgressbar", "Close", "Hide"):
                f = getattr(self.bar, fn, None)
                if callable(f):
                    f()
                    break
        except Exception:
            pass
        self.bar = None


TANIMSIZ = ("<tanımsız>", "<tanimsiz>", "<undefined>", "<nicht definiert>", "<not defined>", "<undef>")


def bos(v):
    """Boş mu? R19: Allplan tanımsız niteliği '<tanımsız>' yazısıyla döndürüyor; o da boş sayılır."""
    if v is None:
        return True
    if isinstance(v, str):
        x = v.strip()
        return x == "" or x.lower() in TANIMSIZ
    return False


def evet(v):
    return str(v).strip().lower() in ("evet", "1", "true", "e", "yes")


def mesaj(text):
    """PP02 R62 ile aynı: Windows mesaj kutusu (Allplan'ın önünde), olmazsa Allplan mesaj kutusu."""
    log("MESAJ: " + text.replace("\n", " | "))
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, text, "e-PYS IDS Kontrol – Nitelik yaz", 0x40 | 0x40000)
        return
    except Exception:
        pass
    try:
        AllplanUtil.ShowMessageBox(text, AllplanUtil.MB_OK)
    except Exception:
        pass


class EpysIds(BaseScriptObject):

    def __init__(self, build_ele, script_object_data):
        super().__init__(script_object_data)
        self.build_ele = build_ele
        self.sel = MultiElementSelectInteractorResult()
        self.ozet = []
        self.attr_cache = {}
        self.bilinmeyen = {}
        try:
            self.doc = self.document
        except Exception:
            self.doc = None
        try:
            self.uuids = uuid_listesi()
        except Exception:
            self.uuids = []
        try:
            self.tumu_esitle()
        except Exception:
            pass
        log("Palet hazır; tanınan Allplan tipi: %d" % len(self.uuids))

    # ------------------------------------------------------------ giriş
    def execute(self):
        return CreateElementResult()

    def start_input(self):
        b = self.build_ele
        if b.Calisma.value == 1:
            msg = "IFC denetimi: palette IFC dosyasını seçip 'Çalıştır'a basın (ESC = çıkış)"
        else:
            msg = "e-PYS nitelik: elemanları seçin – %s (ESC = çıkış)" % self.islem()
        self.script_object_interactor = MultiElementSelectInteractor(self.sel, prompt_msg=msg)

    def start_next_input(self):
        log("Seçim bitti")
        try:
            if self.build_ele.Calisma.value == 2:
                self.ozet = []
                self.isle(self.sel.sel_elements)
                if self.ozet and self._v("OzetGoster", True):
                    mesaj("\n".join(self.ozet))
        except Exception:
            log("HATA", traceback.format_exc())
            AllplanUtil.ShowMessageBox("PP09 hata:\n%s\n\nAyrıntı: %s" % (sys.exc_info()[1], LOG), AllplanUtil.MB_OK)
        self.sel = MultiElementSelectInteractorResult()
        self.start_input()

    def on_cancel_function(self):
        self.script_object_interactor = None
        return OnCancelFunctionResult.CANCEL_INPUT

    # ---- R12: nitelik yazma ayarları (palette açılır listeler)
    def _v(self, name, default=None):
        prm = getattr(self.build_ele, name, None)
        return prm.value if prm is not None else default

    def islem(self):
        v = str(self._v("NY_Islem", ISLEM_YAZ) or ISLEM_YAZ)
        return v if v in (ISLEM_YAZ, ISLEM_DENE, ISLEM_SIL, ISLEM_KONTROL) else ISLEM_YAZ

    def tumu_esitle(self):
        """Disiplin ve genel Tümü kutularını tek tek kutulara göre ayarlar. Değiştiyse True."""
        b = self.build_ele
        degisti = False
        for gp, uyeler in NY_GRUP.items():
            hepsi = all(bool(self._v(NY_KAT[k][0], True)) for k in uyeler)
            if hasattr(b, gp) and bool(getattr(b, gp).value) != hepsi:
                getattr(b, gp).value = hepsi
                degisti = True
        hepsi = all(bool(self._v(v[0], True)) for v in NY_KAT.values())
        if hasattr(b, "CatTumu") and bool(b.CatTumu.value) != hepsi:
            b.CatTumu.value = hepsi
            degisti = True
        return degisti

    def modify_element_property(self, name, value):
        """Palette değişiklikleri"""
        log("Palet: %s = %r" % (name, value))
        b = self.build_ele
        on = value in (True, 1, "1", "True", "true")
        if name == "CatTumu":
            for v in NY_KAT.values():
                if hasattr(b, v[0]):
                    getattr(b, v[0]).value = on
            self.tumu_esitle()
            return True
        if name in NY_GRUP:
            for k in NY_GRUP[name]:
                if hasattr(b, NY_KAT[k][0]):
                    getattr(b, NY_KAT[k][0]).value = on
            self.tumu_esitle()
            return True
        if name in [v[0] for v in NY_KAT.values()]:
            if hasattr(b, name):
                getattr(b, name).value = on
            return self.tumu_esitle()
        if name in ("Calisma", "NY_Islem"):
            # R17: seçim yeniden başlatılmaz (PP02 R62 gibi). R11–R16'da burada ikinci bir seçim
            # başlatılıyordu; ardından eleman seçilince Allplan kapanıyordu. Değerler seçim bitince okunur.
            return True
        return False

    # ------------------------------------------------------------ düğmeler
    def on_control_event(self, event_id):
        b = self.build_ele
        try:
            if event_id == b.EV_CALISTIR:
                self.ifc_calistir()
            elif event_id == b.EV_VARSAYILAN:
                self.varsayilan_ac()
            elif event_id == getattr(b, "EV_FORM", -999):
                self.form_ac()
            elif event_id == getattr(b, "EV_ESLEME", -999):
                p = core.paket_dosyasi("esleme", _DIR)
                try:
                    import subprocess
                    subprocess.Popen(["notepad.exe", p])
                except Exception:
                    os.startfile(p)
            elif event_id == b.EV_RAPOR_AC:
                self.rapor_ac()
            elif event_id == b.EV_NITELIK_DOGRULA:
                self.nitelik_dogrula()
        except Exception:
            log("HATA", traceback.format_exc())
            AllplanUtil.ShowMessageBox("PP09 hata:\n%s\n\nAyrıntı: %s" % (sys.exc_info()[1], LOG), AllplanUtil.MB_OK)
        return True

    # ------------------------------------------------------------ 1) IFC
    def varsayilan_yolu(self):
        ifc = self.build_ele.IfcDosya.value
        if ifc:
            return os.path.splitext(ifc)[0] + "_Varsayilan.txt"
        return os.path.join(os.environ.get("APPDATA", _DIR), "ALUPLAN", "ePYS_IDS_Varsayilan.txt")

    def form_yolu(self):
        ifc = (self.build_ele.IfcDosya.value or "").strip().strip('"')
        if ifc:
            return os.path.join(os.path.dirname(ifc), "ePYS_Proje_Bilgi_Formu.xlsx")
        return os.path.join(os.environ.get("APPDATA", _DIR), "ALUPLAN", "ePYS_Proje_Bilgi_Formu.xlsx")

    def form_ac(self):
        p = self.form_yolu()
        if not os.path.isfile(p):
            import shutil
            os.makedirs(os.path.dirname(p), exist_ok=True)
            shutil.copyfile(core.paket_dosyasi("form", _DIR), p)
            log("Proje Bilgi Formu oluşturuldu", p)
        self.build_ele.FormDosya.value = p
        try:
            os.startfile(p)
        except Exception:
            AllplanUtil.ShowMessageBox("Form açılamadı, elle açın:\n%s" % p, AllplanUtil.MB_OK)

    def varsayilan_ac(self):
        p = self.varsayilan_yolu()
        if not os.path.isfile(p):
            os.makedirs(os.path.dirname(p), exist_ok=True)
            src = os.path.join(_DIR, "ePYS_IDS_Varsayilan.txt")
            with open(src, "r", encoding="utf-8") as f, open(p, "w", encoding="utf-8") as g:
                g.write(f.read())
        try:
            import subprocess
            subprocess.Popen(["notepad.exe", p])
        except Exception:
            os.startfile(p)
        if hasattr(self.build_ele, "VarsayilanDosya"):
            self.build_ele.VarsayilanDosya.value = p

    def ifc_calistir(self):
        b = self.build_ele
        ifc = (b.IfcDosya.value or "").strip().strip('"')
        if not ifc or not os.path.isfile(ifc):
            AllplanUtil.ShowMessageBox("IFC dosyası bulunamadı:\n%s" % ifc, AllplanUtil.MB_OK)
            return
        duzelt = b.IfcIslem.value == 2
        ayar = {
            "tag_kod_yazisi": b.D_Tag.value, "predefined_userdefined": b.D_Predef.value, "ad_bicim": b.D_Ad.value,
            "sinif_duzelt": b.D_Sinif.value, "mahal_no": b.D_MahalNo.value, "mahal_kaplama": b.D_Kaplama.value,
            "kat_bilgi": b.D_Kat.value, "bina_bilgi": b.D_Bina.value, "adres": b.D_Adres.value, "zon": b.D_Zon.value,
            "kacis_yolu": b.D_Kacis.value, "dis_eleman": b.D_Dis.value, "yangin_dakika": b.D_Yangin.value,
            "disiplin": b.D_Disiplin.value, "bina_adi": b.BinaAdi.value.strip(), "bina_uzun_ad": b.BinaUzunAd.value.strip(),
            "proje_adi": b.ProjeKodu.value.strip(),
            "oto_bilgi": getattr(b, "D_Oto", None).value if hasattr(b, "D_Oto") else True,
            "giydirme_cephe": getattr(b, "D_Gdc", None).value if hasattr(b, "D_Gdc") else True,
            "p3_esle": b.P3_Esle.value if hasattr(b, "P3_Esle") else True,
            "p3_temizle": b.P3_Temizle.value if hasattr(b, "P3_Temizle") else True,
        }
        vy = self.varsayilan_yolu()
        cikti = (b.CiktiIfc.value or "").strip() or None
        t = time.time()
        pb = None
        try:
            pb = AllplanUtil.ProgressBar()
            pb.StartProgressbar(3, "e-PYS IDS: IFC işleniyor…", False, False)
            pb.Step()
        except Exception:
            pb = None
        try:
            ids_yolu = (b.IdsDosya.value or "").strip().strip('"') or core.paket_dosyasi("ids", _DIR)
            if not os.path.isfile(ids_yolu):
                AllplanUtil.ShowMessageBox("IDS dosyası bulunamadı:\n%s" % ids_yolu, AllplanUtil.MB_OK)
                return
            fy = self.form_yolu()
            if hasattr(b, "FormDosya"):
                b.FormDosya.value = fy if os.path.isfile(fy) else ""
            r = core.calistir(ifc, duzelt, ayar, vy if os.path.isfile(vy) else None, cikti, None,
                              ids_duzelt=True, log=log, ids_yolu=ids_yolu,
                              form_dosyasi=fy if os.path.isfile(fy) else None)
        finally:
            if pb:
                try:
                    pb.CloseProgressbar()
                except Exception:
                    pass
        self.son_rapor_kaydet(r["rapor"])
        if duzelt:
            b.SonSonuc.value = "%d → %d hata · %d düzeltme · %.0f sn" % (r["once"], r["sonra"], r["duzeltme"], time.time() - t)
        else:
            b.SonSonuc.value = "%d hatalı kontrol · %.0f sn" % (r["once"], time.time() - t)
        log("IFC sonuç", b.SonSonuc.value)
        if b.RaporAc.value:
            try:
                os.startfile(r["rapor"])
            except Exception:
                pass
        msg = "IDS denetimi bitti.\n\n%s\n\nRapor: %s" % (b.SonSonuc.value, r["rapor"])
        if duzelt:
            msg += "\nDüzeltilmiş IFC: %s" % r["cikti"]
        AllplanUtil.ShowMessageBox(msg, AllplanUtil.MB_OK)

    # ------------------------------------------------------------ 2) nitelik
    def attr_id(self, adlar):
        """'A|B' adlarından ilk bulunan nitelik (id, tip) – yoksa (-1, None)."""
        key = adlar
        if key in self.attr_cache:
            return self.attr_cache[key]
        res = (-1, None)
        for ad in [x.strip() for x in str(adlar).split("|") if x.strip()]:
            try:
                i = AllplanBaseEle.AttributeService.GetAttributeID(self.doc, ad)
            except Exception:
                i = -1
            if i is not None and i != -1:
                try:
                    t = str(AllplanBaseEle.AttributeService.GetAttributeType(self.doc, i))
                except Exception:
                    t = ""
                res = (i, t)
                break
        self.attr_cache[key] = res
        return res

    # ---- R20: son rapor
    def son_rapor_kaydet(self, p):
        """Son raporun yolunu hem palete hem de nesneye ve küçük bir dosyaya yazar (palet yenilenmese de kaybolmaz)."""
        self.son_rapor = p
        try:
            self.build_ele.SonRapor.value = p
        except Exception:
            pass
        try:
            with open(SON_RAPOR_DOSYA, "w", encoding="utf-8") as f:
                f.write(p)
        except Exception:
            pass
        self.palet_yenile()

    def palet_yenile(self):
        """PP02 R62 gibi: paletteki Sonuç alanlarını güncellemeyi dener."""
        for owner in (self, getattr(self, "script_object_data", None)):
            svc = getattr(owner, "palette_service", None) if owner is not None else None
            if svc is None:
                continue
            for call in (lambda: svc.update_palette(-1, False), lambda: svc.update_palette()):
                try:
                    call()
                    return
                except Exception:
                    continue

    def rapor_ac(self):
        aday = [getattr(self, "son_rapor", ""), self._v("SonRapor", "")]
        try:
            with open(SON_RAPOR_DOSYA, encoding="utf-8") as f:
                aday.append(f.read().strip())
        except Exception:
            pass
        for p in aday:
            if p and os.path.isfile(p):
                log("Rapor açılıyor: " + p)
                os.startfile(p)
                return
        log("Açılacak rapor bulunamadı: %r" % aday)
        try:
            os.makedirs(RAPOR_KLASOR, exist_ok=True)
            os.startfile(RAPOR_KLASOR)        # rapor yoksa rapor klasörünü aç
        except Exception:
            AllplanUtil.ShowMessageBox("Henüz rapor yok.", AllplanUtil.MB_OK)

    def nitelik_dogrula(self):
        self.attr_cache = {}
        b = self.build_ele
        satir = []
        for etiket, prm in (("İsim", "N_Isim"), ("Kod yazısı", "N_Kod"), ("Yangın dayanımı", "N_Yangin"),
                            ("Dış eleman", "N_Dis"), ("Taşıyıcı", "N_Tasiyici"), ("Kaçış yolu (kapı)", "N_Kacis"),
                            ("Acil çıkış (merdiven)", "N_AcilCikis"), ("Malzeme", "N_Malzeme"),
                            ("IFC obje kategorisi", "N_ObjeKat"), ("Mahal no", "N_MahalNo")):
            i, t = self.attr_id(getattr(b, prm).value)
            satir.append("%-22s %-28s %s" % (etiket, getattr(b, prm).value,
                                             ("ID %d (%s)" % (i, t)) if i != -1 else "BULUNAMADI"))
        txt = "\n".join(satir)
        log("Nitelik doğrulama\n" + txt)
        AllplanUtil.ShowMessageBox("Allplan nitelik adları:\n\n" + txt, AllplanUtil.MB_OK)

    def deger_cevir(self, val, tip, bool_=False):
        t = (tip or "").lower()
        if bool_:
            v = 1 if evet(val) else 0
            if "double" in t or "real" in t:
                return float(v)
            if "string" in t or "text" in t:
                return "1" if v else "0"
            return v
        if "int" in t:
            try:
                return int(float(str(val).replace(",", ".")))
            except ValueError:
                return val
        if "double" in t or "real" in t or "length" in t:
            try:
                return float(str(val).replace(",", "."))
            except ValueError:
                return val
        return str(val)

    def isle(self, secim):
        b = self.build_ele
        islem = self.islem()
        on_kontrol = islem == ISLEM_KONTROL
        onizleme = islem == ISLEM_DENE
        uzerine = str(self._v("NY_Dolu", DOLU_BOS)) == DOLU_UZERINE
        dw = str(self._v("KapiPencereHedef", DW_BOTH) or DW_BOTH)
        acik = {k: bool(self._v(v[0], True)) for k, v in NY_KAT.items()}
        secim = list(secim or [])
        log("ADIM 1: işlem '%s', seçilen öğe %d, kapı/pencere hedef '%s'" % (islem, len(secim), dw))
        secim, n_kpl = kaplamalari_ekle(secim, acik)
        log("ADIM 2: odalardan eklenen kaplama %d" % n_kpl)
        # ---- seçimi topla (ana eleman, tekil)
        n = len(secim)
        pb = _Progress(n)
        elemanlar = []
        gorulen = set()
        self.bilinmeyen = {}
        kapali = {}
        for i_, ele in enumerate(secim):
            pb.step()
            if i_ % 250 == 0:
                log("ADIM 3: tarama %d/%d" % (i_, n))
            nk, t = kategori(ele, self.uuids)
            if nk is None:
                if t:
                    self.bilinmeyen[t] = self.bilinmeyen.get(t, 0) + 1
                continue
            if not acik.get(nk):
                kk = "%s (%s)" % (NY_KAT[nk][1], t)
                kapali[kk] = kapali.get(kk, 0) + 1
                continue
            ana = ana_eleman(ele, nk)
            k = ele_key(ana)
            if k in gorulen:
                continue
            gorulen.add(k)
            elemanlar.append((ana, NY_KAT[nk][2], nk))
        pb.close()
        if self.bilinmeyen:
            log("Kategori dışı kalan tipler:", ", ".join("%s(%d)" % kv for kv in sorted(self.bilinmeyen.items())))
        if kapali:
            log("Kutusu kapalı olduğu için atlanan:", ", ".join("%s×%d" % kv for kv in sorted(kapali.items())))
        sayim = {}
        for _e, _k, _nk in elemanlar:
            sayim[NY_KAT[_nk][1]] = sayim.get(NY_KAT[_nk][1], 0) + 1
        log("Seçim: %d öğe, işlenecek %d eleman %s" % (n, len(elemanlar), sayim))
        self.ozet.append("İşlem: %s" % islem)
        self.ozet.append("Seçilen öğe: %d%s" % (n, (" (odalardan eklenen kaplama: %d)" % n_kpl) if n_kpl else ""))
        self.ozet.append("İşlenecek eleman: %d  %s" % (len(elemanlar), ", ".join("%s %d" % kv for kv in sayim.items())))
        if kapali:
            self.ozet.append("Elemanlar'da kutusu kapalı olduğu için atlanan: " +
                             ", ".join("%s ×%d" % kv for kv in sorted(kapali.items())))
        if self.bilinmeyen:
            self.ozet.append("Tanınmayan / atlanan öğe: " +
                             ", ".join("%s ×%d" % kv for kv in sorted(self.bilinmeyen.items())[:8]))
        if not elemanlar:
            b.SonAtama.value = "Uygun eleman yok (%d öğe seçildi)" % n
            self.ozet.append("")
            self.ozet.append("Seçimde işaretli eleman türü yok. 'Elemanlar' bölümünde ilgili kutuyu açın.")
            return
        if islem in (ISLEM_YAZ, ISLEM_DENE, ISLEM_SIL):
            secili = [k for k in ("Y_Isim", "Y_Yangin", "Y_Dis", "Y_Tasiyici", "Y_Kacis", "Y_Malzeme", "Y_ObjeKat")
                      if self._v(k, False)]
            if not secili and not (b.Serbest.value or []):
                b.SonAtama.value = "Yazılacak nitelik işaretlenmedi"
                self.ozet.append("")
                self.ozet.append("Hiçbir nitelik işaretli değil. 'Yazılacak nitelikler' bölümünde yazılacak "
                                 "satırın kutusunu işaretleyin (ör. Yangın dayanımı).")
                return
        # ---- nitelik ID'leri
        A = {}
        for prm in ("N_Isim", "N_Kod", "N_Yangin", "N_Dis", "N_Tasiyici", "N_Kacis", "N_AcilCikis", "N_Malzeme",
                    "N_ObjeKat", "N_MahalNo"):
            A[prm] = self.attr_id(getattr(b, prm).value)
        if islem == ISLEM_SIL:
            self.sil(elemanlar, A, dw)
            return
        rapor = []          # (kategori, ad, gereksinim, mevcut, yeni/beklenen, durum)
        yazilan = 0
        yazilan_ele = 0
        log("ADIM 4: nitelik ID'leri %s" % ", ".join("%s=%s" % (k, v[0]) for k, v in A.items()))
        pb = _Progress(len(elemanlar))
        serbest = []
        for it in (b.Serbest.value or []):
            try:
                aid, val = (it.attribute_id, it.value) if hasattr(it, "attribute_id") else (it[0], it[1] if len(it) > 1 else "")
            except Exception:
                continue
            if aid and aid > 0:
                serbest.append((aid, val))
        for ele, kat, nk in elemanlar:
            etiket = NY_KAT[nk][1]
            pos = paraobjeler(ele) if (nk in KAPI_PENCERE and dw in (DW_PARAOBJE, DW_BOTH)) else []
            if dw == DW_PARAOBJE and pos:
                mevcut = oku_nitelikler(pos[0])        # değer ParaObje'den okunur
            else:
                mevcut = None
            pb.step()
            if mevcut is None:
                mevcut = oku_nitelikler(ele)

            def cur(prm):
                i = A[prm][0]
                return mevcut.get(i) if i != -1 else None
            ad_simdi = "" if bos(cur("N_Isim")) else str(cur("N_Isim"))
            degis = []

            def iste(prm, yeni, gereksinim, bool_=False):
                i, tip = A[prm]
                if i == -1:
                    rapor.append((etiket, ad_simdi, gereksinim, "", "nitelik bulunamadı: " + getattr(b, prm).value, "UYARI"))
                    return
                eski = mevcut.get(i)
                if not uzerine and not bos(eski):
                    return
                v = self.deger_cevir(yeni, tip, bool_)
                if str(eski) == str(v):
                    return
                degis.append((i, v))
                rapor.append((etiket, ad_simdi, gereksinim, "" if eski is None else str(eski), str(yeni),
                              "Deneme (yazılmadı)" if onizleme else "Yazıldı"))

            if on_kontrol:
                self.on_kontrol(kat, ad_simdi, cur, rapor, etiket)
                continue
            # İsim (Ek-5)
            if b.Y_Isim.value and kat != "Mahal":
                kod = KAT[kat][0]
                dis = b.Disiplin.value if b.Disiplin.value != "Otomatik" else KAT[kat][1]
                malz = cur("N_Malzeme") or ""
                m = re.match(r"^[A-Za-z]{2}[\s_\-]+[A-Za-z]{3}[\s_\-]+(.+)$", ad_simdi.strip())
                mevcut_acik = m.group(1) if m else ad_simdi
                acik_ = (b.IsimSablon.value or "{MALZEME}").replace("{MALZEME}", str(malz)).replace("{MEVCUT}", str(mevcut_acik))
                acik_ = core.aciklama_temizle(acik_, ascii_=b.Ascii.value, upper=b.BuyukHarf.value) or core.aciklama_temizle(kat)
                yeni_ad = "%s-%s-%s" % (dis, kod, acik_)
                izin = core.DISIPLIN_IZIN.get({"Kapı": "IFCDOOR", "Pencere": "IFCWINDOW", "Kaplama": "IFCCOVERING",
                                               "Temel": "IFCFOOTING"}.get(kat, ""))
                if izin and dis not in izin:
                    yeni_ad = "%s-%s-%s" % (izin[0], kod, acik_)
                if yeni_ad != ad_simdi:
                    i, tip = A["N_Isim"]
                    if i != -1 and (uzerine or bos(ad_simdi) or not re.fullmatch(r"[A-Z]{2}-%s-[^-]+" % kod, ad_simdi)):
                        degis.append((i, yeni_ad))
                        rapor.append((etiket, ad_simdi, "İsim (Ek-5)", ad_simdi, yeni_ad, "Deneme (yazılmadı)" if onizleme else "Yazıldı"))
            if b.Y_Yangin.value and kat not in ("Mahal",):
                iste("N_Yangin", re.sub(r"\D", "", str(b.Yangin.value)) or b.Yangin.value, "Yangın dayanımı (FireRating)")
            if b.Y_Dis.value and kat not in ("Mahal", "Kaplama"):
                iste("N_Dis", b.Dis.value, "Dış eleman (IsExternal)", True)
            if b.Y_Tasiyici.value and kat in ("Duvar", "Kolon", "Kiriş", "Döşeme", "Temel", "Merdiven", "Baca", "Çatı"):
                iste("N_Tasiyici", b.Tasiyici.value, "Taşıyıcı (LoadBearing)", True)
            if b.Y_Kacis.value and kat in ("Kapı", "Merdiven", "Pencere"):
                iste("N_AcilCikis" if kat == "Merdiven" else "N_Kacis", b.Kacis.value, "Kaçış yolu (FireExit)", True)
            if b.Y_Malzeme.value and b.Malzeme.value.strip():
                iste("N_Malzeme", b.Malzeme.value.strip().replace(" ", "_").replace("-", "_"), "Malzeme")
            if b.Y_ObjeKat.value and b.ObjeKat.value.strip():
                iste("N_ObjeKat", b.ObjeKat.value.strip(), "IFC obje kategorisi (ObjectType)")
            for aid, val in serbest:
                eski = mevcut.get(aid)
                if not uzerine and not bos(eski):
                    continue
                if str(eski) == str(val):
                    continue
                degis.append((aid, val))
                try:
                    an = AllplanBaseEle.AttributeService.GetAttributeName(self.doc, aid)
                except Exception:
                    an = str(aid)
                rapor.append((etiket, ad_simdi, an, "" if eski is None else str(eski), str(val), "Deneme (yazılmadı)" if onizleme else "Yazıldı"))
            if degis and not onizleme:
                self.yaz(ele, kat, degis, pos, dw)
                yazilan += len(degis)
                yazilan_ele += 1
        pb.close()
        # ---- rapor
        if on_kontrol:
            hata = sum(1 for r in rapor if r[5] == "Eksik")
            b.SonAtama.value = "Ön kontrol: %d eleman, %d eksik" % (len(elemanlar), hata)
        elif onizleme:
            b.SonAtama.value = "Deneme: %d değişiklik bulundu (yazılmadı)" % len(rapor)
        else:
            b.SonAtama.value = "%d elemana %d nitelik yazıldı" % (yazilan_ele, yazilan)
        log(b.SonAtama.value)
        self.ozet.append("")
        self.ozet.append("Sonuç: " + b.SonAtama.value)
        if not on_kontrol and not rapor:
            self.ozet.append("Değişecek bir şey yok: nitelikler zaten dolu ya da aynı. Dolu olanları değiştirmek için "
                             "'Nitelik doluysa = Üzerine yaz' seçin.")
        self.rapor_yaz(rapor, len(elemanlar), on_kontrol)

    def sil(self, elemanlar, A, dw):
        """R12 (PP02 'Nitelik Sil' gibi): işaretli niteliklerin değerini seçilen elemanlardan boşaltır."""
        b = self.build_ele
        secili = [(prm, ad) for kutu, prm, ad in (
            ("Y_Isim", "N_Isim", "İsim"), ("Y_Yangin", "N_Yangin", "Yangın dayanımı"), ("Y_Dis", "N_Dis", "Dış eleman"),
            ("Y_Tasiyici", "N_Tasiyici", "Taşıyıcı"), ("Y_Kacis", "N_Kacis", "Kaçış yolu"),
            ("Y_Kacis", "N_AcilCikis", "Acil çıkış"), ("Y_Malzeme", "N_Malzeme", "Malzeme"),
            ("Y_ObjeKat", "N_ObjeKat", "IFC obje kategorisi")) if self._v(kutu, False)]
        idler = []
        for prm, ad in secili:
            i, tip = A[prm]
            if i != -1 and i not in [x[0] for x in idler]:
                idler.append((i, tip, ad))
        for it in (b.Serbest.value or []):
            try:
                aid = it.attribute_id if hasattr(it, "attribute_id") else it[0]
            except Exception:
                continue
            if aid and aid > 0 and aid not in [x[0] for x in idler]:
                idler.append((aid, "", str(aid)))
        if not idler:
            b.SonAtama.value = "Silinecek nitelik işaretlenmedi"
            self.ozet.append("")
            self.ozet.append("Silinecek nitelik yok. 'Yazılacak nitelikler' bölümünde silinecek niteliklerin kutusunu işaretleyin.")
            return
        rapor, n_ele = [], 0
        for ele, kat, nk in elemanlar:
            pos = paraobjeler(ele) if nk in KAPI_PENCERE else []
            hedef = AllplanEleAdapter.BaseElementAdapterList()
            if dw != DW_PARAOBJE or not pos:
                hedef.append(ele)
            if dw in (DW_PARAOBJE, DW_BOTH):
                for po in pos:
                    hedef.append(po)
            mevcut = oku_nitelikler(ele)
            ad_simdi = str(mevcut.get(A["N_Isim"][0]) or "") if A["N_Isim"][0] != -1 else ""
            sildi = False
            for i, tip, ad in idler:
                eski = mevcut.get(i)
                if bos(eski):
                    continue
                t = (tip or "").lower()
                sayi = any(w in t for w in ("int", "double", "real", "length"))
                try:
                    if not sayi:          # metin: PP02 'Nitelik Sil' gibi değeri boşalt
                        AllplanBaseEle.ElementsAttributeService.ChangeAttributes([(i, "")], hedef, False, False)
                    else:                 # sayı / evet-hayır: niteliği elemandan kaldır
                        AllplanBaseEle.ElementsAttributeService.ChangeAttributes(
                            [(i, 0.0 if "int" not in t else 0)], hedef, False, True)
                    rapor.append((NY_KAT[nk][1], ad_simdi, ad, str(eski), "", "Silindi"))
                    sildi = True
                except Exception:
                    log("Silinemedi", ad, traceback.format_exc())
                    rapor.append((NY_KAT[nk][1], ad_simdi, ad, str(eski), "", "UYARI"))
            n_ele += 1 if sildi else 0
        b.SonAtama.value = "%d elemandan %d nitelik silindi" % (n_ele, len(rapor))
        log(b.SonAtama.value)
        self.ozet.append("")
        self.ozet.append("Sonuç: " + b.SonAtama.value)
        self.rapor_yaz(rapor, len(elemanlar), False)

    def yaz(self, ele, kat, degis, pos=(), dw=DW_BOTH):
        """Kapı/pencere: dw = Boşluk + ParaObje / Boşluk / ParaObje (ParaObje yoksa boşluğa yazılır)."""
        lst = AllplanEleAdapter.BaseElementAdapterList()
        if dw != DW_PARAOBJE or not pos:
            lst.append(ele)
        if dw in (DW_PARAOBJE, DW_BOTH):
            for po in pos:
                lst.append(po)
        # R16: PP02 R62 ile aynı çağrı (undo servisine sarılmadan, her nitelik ayrı) – Allplan'da denenmiş yol
        log("YAZ %s %s: %s -> %d öğe" % (kat, ele_key(ele), ", ".join("%s=%r" % (i, v) for i, v in degis), len(lst)))
        for aid, val in degis:
            AllplanBaseEle.ElementsAttributeService.ChangeAttributes([(int(aid), val)], lst, False, False)

    def on_kontrol(self, kat, ad, cur, rapor, etiket=None):
        """Allplan nitelikleri üzerinden IDS ön kontrolü (kesin sonuç IFC denetimindedir)."""
        etiket = etiket or kat

        def ekle(g, deger, ok, beklenen):
            rapor.append((etiket, ad, g, "" if deger is None else str(deger), beklenen, "Tamam" if ok else "Eksik"))
        if kat == "Mahal":
            v = cur("N_MahalNo")
            ekle("Mahal no (Ek-3)", v, bool(v) and re.fullmatch(r"(K\d{2}|B\d{2})_[A-ZÇĞİÖŞÜ0-9]{3}_\d{3}", str(v)) is not None,
                 "K01_D02_007")
            return
        kod = KAT[kat][0]
        izin = {"Kapı": "(MM|IM)", "Pencere": "(MM|IM)", "Kaplama": "(MM|IM)", "Temel": "(AL|ST|ZE)"}.get(kat, "[A-Z]{2}")
        ekle("İsim (Ek-5)", ad, re.fullmatch(r"%s-%s-[^-]+" % (izin, kod), ad or "") is not None, "%s-%s-AÇIKLAMA" % (izin, kod))
        v = cur("N_Kod")
        ekle("Kod yazısı (Tag)", v, not bos(v), "dolu")
        yapisal = kat in YAPISAL or (re.match(r"^(ST|AL|ZE)-", ad or "") is not None)
        if kat in ("Duvar", "Kolon", "Kiriş", "Döşeme", "Kapı", "Kaplama", "Giydirme Cephe", "Çatı", "Baca", "Merdiven", "Temel"):
            if kat not in ("Duvar", "Döşeme", "Kolon", "Kiriş", "Merdiven") or yapisal or kat in ("Duvar", "Merdiven"):
                v = cur("N_Yangin")
                ekle("Yangın dayanımı", v, not bos(v), "dakika (ör. 120)")
        if kat in ("Duvar", "Döşeme", "Kapı", "Pencere", "Çatı"):
            v = cur("N_Dis")
            ekle("Dış eleman", v, v is not None, "Evet/Hayır")
        if kat in ("Kolon",):
            v = cur("N_Tasiyici")
            ekle("Taşıyıcı", v, v is not None, "Evet/Hayır")
        if kat == "Kapı":
            v = cur("N_Kacis")
            ekle("Kaçış yolu", v, v is not None, "Evet/Hayır")
        if kat == "Merdiven":
            v = cur("N_AcilCikis")
            ekle("Acil çıkış", v, v is not None, "Evet/Hayır")
        v = cur("N_Malzeme")
        if kat in YAPISAL or kat in ("Baca",) or yapisal:
            ekle("Malzeme", v, not bos(v) and "_" in str(v), "Malzeme_Dayanım (Beton_C30)")
        elif kat not in ("Kapı", "Pencere", "Korkuluk"):
            ekle("Malzeme", v, not bos(v), "dolu")

    def rapor_yaz(self, rapor, n, on_kontrol):
        b = self.build_ele
        if not b.RaporYaz.value:
            return
        try:
            os.makedirs(RAPOR_KLASOR, exist_ok=True)
            d = RAPOR_KLASOR
        except Exception:
            d = os.environ.get("TEMP", _DIR)
        p = os.path.join(d, "ePYS_IDS_%s_%s.xlsx" % ("OnKontrol" if on_kontrol else "Nitelik",
                                                     datetime.datetime.now().strftime("%Y%m%d_%H%M%S")))
        s = core.Sheet("Ön Kontrol" if on_kontrol else "Nitelik Atama", [16, 34, 30, 30, 30, 12])
        s.add(["PP09 e-PYS IDS – %s (%d eleman) – %s" % ("Ön kontrol" if on_kontrol else "Nitelik atama", n,
                                                       datetime.datetime.now().strftime("%d.%m.%Y %H:%M"))], "title")
        if on_kontrol:
            s.add(["Allplan nitelikleri üzerinden yapılan ön kontroldür. Kesin sonuç için IFC'yi dışa aktarıp "
                   "'IFC Denetim' sayfasında denetleyin."], "duz")
        s.header(["Eleman", "Mevcut ad", "Gereksinim", "Mevcut değer", "Yeni / beklenen", "Durum"])
        for r in rapor:
            st = {"Eksik": "kirmizi", "Tamam": "yesil", "UYARI": "sari", "Deneme (yazılmadı)": "sari"}.get(r[5])
            s.add(list(r), styles=[None] * 5 + [st])
        if self.bilinmeyen:
            s2 = core.Sheet("Tanınmayan tipler", [40, 10])
            s2.header(["Allplan tip adı", "Adet"])
            for k, v in sorted(self.bilinmeyen.items()):
                s2.add([k, v])
            core.write_xlsx(p, [s, s2])
        else:
            core.write_xlsx(p, [s])
        self.son_rapor_kaydet(p)
        log("Rapor: " + p)
        try:
            self.ozet.append("Excel rapor: " + p)
        except Exception:
            pass
        if b.RaporAc.value:
            try:
                os.startfile(p)
            except Exception:
                pass
