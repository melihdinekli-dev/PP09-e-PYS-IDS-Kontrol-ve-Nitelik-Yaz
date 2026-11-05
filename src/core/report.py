# -*- coding: utf-8 -*-
# Telif Hakkı (c) 2026 ALUPLAN – Allplan Türkiye Distribütörü. Tüm hakları saklıdır.
# Kapalı kaynak, tescilli yazılım – bkz. LICENSE. Yetkisiz kopyalama ve dağıtım yasaktır.
"""Bağımlılıksız .xlsx yazıcı ve IDS raporu. ALUPLAN – PP09."""
import zipfile
import datetime
from xml.sax.saxutils import escape


def _col(n):
    s = ""
    n += 1
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


_STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<numFmts count="1"><numFmt numFmtId="164" formatCode="0.0%"/></numFmts>
<fonts count="4"><font><sz val="10"/><name val="Calibri"/></font><font><b/><sz val="10"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font><font><b/><sz val="13"/><color rgb="FF1F3864"/><name val="Calibri"/></font><font><b/><sz val="10"/><name val="Calibri"/></font></fonts>
<fills count="6"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FF1F3864"/></patternFill></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FFE2F0D9"/></patternFill></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FFFCE4D6"/></patternFill></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FFFFF2CC"/></patternFill></fill></fills>
<borders count="2"><border/><border><left style="thin"><color rgb="FFD9D9D9"/></left><right style="thin"><color rgb="FFD9D9D9"/></right><top style="thin"><color rgb="FFD9D9D9"/></top><bottom style="thin"><color rgb="FFD9D9D9"/></bottom></border></borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="10">
<xf numFmtId="0" fontId="0" fillId="0" borderId="1" applyBorder="1"><alignment vertical="top" wrapText="1"/></xf>
<xf numFmtId="0" fontId="1" fillId="2" borderId="1" applyFont="1" applyFill="1"><alignment vertical="center" wrapText="1"/></xf>
<xf numFmtId="0" fontId="2" fillId="0" borderId="0" applyFont="1"/>
<xf numFmtId="0" fontId="0" fillId="3" borderId="1" applyFill="1"><alignment vertical="top" wrapText="1"/></xf>
<xf numFmtId="0" fontId="0" fillId="4" borderId="1" applyFill="1"><alignment vertical="top" wrapText="1"/></xf>
<xf numFmtId="0" fontId="0" fillId="5" borderId="1" applyFill="1"><alignment vertical="top" wrapText="1"/></xf>
<xf numFmtId="164" fontId="0" fillId="0" borderId="1" applyNumberFormat="1"/>
<xf numFmtId="0" fontId="3" fillId="0" borderId="1" applyFont="1"><alignment vertical="top" wrapText="1"/></xf>
<xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>
<xf numFmtId="0" fontId="3" fillId="0" borderId="0" applyFont="1"/>
</cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>"""

ST = {"normal": 0, "baslik": 1, "title": 2, "yesil": 3, "kirmizi": 4, "sari": 5, "yuzde": 6, "kalin": 7, "duz": 8, "baslikk": 9}


class Sheet(object):
    def __init__(self, name, widths=None):
        self.name = name[:31]
        self.rows = []      # list of list of (value, style)
        self.widths = widths or []
        self.header_row = None
        self.freeze = None

    def add(self, values, style="normal", styles=None):
        row = []
        for i, v in enumerate(values):
            st = styles[i] if styles and i < len(styles) and styles[i] else style
            row.append((v, ST.get(st, 0)))
        self.rows.append(row)

    def header(self, values):
        self.add(values, "baslik")
        self.header_row = len(self.rows)
        self.freeze = len(self.rows)

    def xml(self):
        out = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
               '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
               'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">']
        if self.freeze:
            out.append('<sheetViews><sheetView workbookViewId="0"><pane ySplit="%d" topLeftCell="A%d" '
                       'activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>' % (self.freeze, self.freeze + 1))
        if self.widths:
            out.append("<cols>")
            for i, wdt in enumerate(self.widths):
                out.append('<col min="%d" max="%d" width="%s" customWidth="1"/>' % (i + 1, i + 1, wdt))
            out.append("</cols>")
        out.append("<sheetData>")
        maxc = 0
        for r, row in enumerate(self.rows):
            out.append('<row r="%d">' % (r + 1))
            for c, (v, st) in enumerate(row):
                if v is None or v == "":
                    if st:
                        out.append('<c r="%s%d" s="%d"/>' % (_col(c), r + 1, st))
                    continue
                ref = "%s%d" % (_col(c), r + 1)
                if isinstance(v, bool):
                    v = "Evet" if v else "Hayır"
                if isinstance(v, (int, float)):
                    out.append('<c r="%s" s="%d"><v>%s</v></c>' % (ref, st, repr(v) if isinstance(v, float) else v))
                else:
                    t = escape(str(v))
                    out.append('<c r="%s" s="%d" t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>' % (ref, st, t))
                maxc = max(maxc, c + 1)
            out.append("</row>")
        out.append("</sheetData>")
        if self.header_row and len(self.rows) > self.header_row:
            out.append('<autoFilter ref="A%d:%s%d"/>' % (self.header_row, _col(max(maxc, 1) - 1), len(self.rows)))
        out.append("</worksheet>")
        return "".join(out)


def write_xlsx(path, sheets):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        ct = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
              '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
              '<Default Extension="xml" ContentType="application/xml"/>'
              '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
              '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>']
        for i in range(len(sheets)):
            ct.append('<Override PartName="/xl/worksheets/sheet%d.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' % (i + 1))
        ct.append("</Types>")
        z.writestr("[Content_Types].xml", "".join(ct))
        z.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        wb = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
              'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>']
        rels = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">']
        for i, s in enumerate(sheets):
            wb.append('<sheet name="%s" sheetId="%d" r:id="rId%d"/>' % (escape(s.name, {'"': "&quot;"}), i + 1, i + 1))
            rels.append('<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet%d.xml"/>' % (i + 1, i + 1))
            z.writestr("xl/worksheets/sheet%d.xml" % (i + 1), s.xml())
        rels.append('<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>' % (len(sheets) + 1))
        rels.append("</Relationships>")
        wb.append("</sheets></workbook>")
        z.writestr("xl/workbook.xml", "".join(wb))
        z.writestr("xl/_rels/workbook.xml.rels", "".join(rels))
        z.writestr("xl/styles.xml", _STYLES)


# ------------------------------------------------------------------ Allplan önerileri
# Bu modelin IFC'sinden doğrulanan eşleşmeler (Allplan niteliği -> IFC alanı)
ALLPLAN_ESLESME = [
    ("Name", "İsim", "Tüm elemanlar (Ek-5: DD-KOD-AÇIKLAMA, mahalde Ek-3 mahal no)"),
    ("Tag", "Kod yazısı", "PP02 e-PYS Nitelik Yaz ile; PP03/PP09 IFC'de Tag'e taşır"),
    ("Malzeme (IfcMaterial)", "Malzeme", "'Malzeme_Dayanım' biçimi, en az bir '_' (Beton_C30)"),
    ("Pset_*Common.FireRating", "Yangın Dayanım Sınıfı", "Tam sayı dakika: 120 (F120 de okunur, PP09 120'ye çevirir)"),
    ("Pset_*Common.IsExternal", "Dış Yapı Elemanı", "Evet / Hayır"),
    ("Pset_*Common.LoadBearing", "Statik_taşıyıcı", "Evet / Hayır"),
    ("Pset_StairCommon.FireExit", "Acil Çıkış", "Merdivende; PP09 FireExit'e taşır"),
    ("Pset_DoorCommon.FireExit", "Kaçış Yolu", "Kapıda"),
    ("ObjectType", "IFC obje kategorisi", "PredefinedType = USERDEFINED olduğunda tip açıklaması"),
]

ONERI = {
    "Name": "Allplan 'İsim' niteliğini Ek-5 biçiminde girin (PP09 Nitelik Ata → İsim). Mahalde Ek-3 mahal no (K01_D02_007).",
    "Tag": "Allplan 'Kod yazısı' niteliğini doldurun (PP02 e-PYS Nitelik Yaz). Dolu ise PP09 IFC Düzelt Tag'e taşır.",
    "PredefinedType": "PP09 IFC Düzelt boş olanları USERDEFINED yapar. Allplan'da IFC nesne tipi/alt tipi seçerek kalıcı çözün.",
    "FireRating": "Allplan 'Yangın Dayanım Sınıfı' niteliğine dakika girin (ör. 120) – PP09 Nitelik Ata → Yangın dayanımı.",
    "IsExternal": "Allplan 'Dış Yapı Elemanı' niteliğini Evet/Hayır yapın – PP09 Nitelik Ata → Dış eleman.",
    "LoadBearing": "Allplan 'Statik_taşıyıcı' niteliğini Evet/Hayır yapın – PP09 Nitelik Ata → Taşıyıcı.",
    "FireExit": "Kapıda 'Kaçış Yolu', merdivende 'Acil Çıkış' niteliğini Evet/Hayır yapın.",
    "Malzeme": "Allplan 'Malzeme' niteliğini 'Malzeme_Dayanım' biçiminde girin (Beton_C30, Alüminyum_6063). Giydirme cephe tiriz/panellerinde de.",
    "Covering": "Mahale döşeme/duvar/tavan yüzeyi (kaplama) tanımlayın; PP09 IFC Düzelt kaplama malzemesi ve kalınlığından Pset_SpaceCoveringRequirements üretir.",
    "Pset_Building": "Bina bilgileri Allplan'da yok: PP09 'Varsayılan değerler' dosyasına girin (BuildingID, OccupancyType ...).",
    "Qto_Building": "Bina yüksekliği / taban alanı: 'Varsayılan değerler' dosyasına girin.",
    "Pset_Site": "Arsa bilgileri (TAKS, KAKS, çekme mesafeleri, tapu): 'Varsayılan değerler' dosyasına girin.",
    "TREpys": "Arsa bilgileri (TAKS, KAKS, çekme mesafeleri): 'Varsayılan değerler' dosyasına girin.",
    "Pset_Land": "Tapu bilgileri (LandID = ada/parsel, LandTitleID = tapu no): 'Varsayılan değerler' dosyasına girin.",
    "IfcProject": "Proje kodu (10 bloklu e-PYS kodu), Description ve ProjectType: palette ve 'Varsayılan değerler' dosyasına girin.",
    "IfcPerson": "Identification = Oda sicil no, Roles = ARCHITECT: 'Varsayılan değerler' dosyasına girin.",
    "IfcOrganization": "Identification (vergi/büro sicil no), Roles, Addresses = POSTA: 'Varsayılan değerler' dosyasına girin.",
    "CRS": "Koordinat sistemi: 'Varsayılan değerler' dosyasına IfcProjectedCRS ve IfcMapConversion satırlarını girin (ya da Allplan'da coğrafi referans).",
    "IfcAnnotation": "IDS, PredefinedType=SURVEY olan bir IfcAnnotation istiyor; bu yalnız IFC 4.3'te var. IFC4 dışa aktarımda karşılanamaz.",
    "TrueNorth": "Kuzey yönü: 'Varsayılan değerler' dosyasına 'IfcGeometricRepresentationContext; TrueNorth; 0,1' girin. "
                 "Not: bakanlık aracı bu kuralda bağlamı hiç bulamıyor (kural ek bir koşul içeriyor olabilir); TrueNorth tek başına yetmeyebilir.",
    "RefElevation": "Arsa ±0.00 kotunun deniz seviyesine göre değeri: 'Varsayılan değerler' dosyasına girin.",
    "LongName": "Okunur ad (LongName): PP09 bina/arsa/zon için üretir; bina uzun adını palette girin.",
    "ObjectType": "ObjectType (tip açıklaması): 'Varsayılan değerler' dosyasına girin (ör. arsa: 'Konut Parseli').",
}


_ADLAR = ["IfcWall", "IfcColumn", "IfcBeam", "IfcSlab", "IfcFooting", "IfcStair", "IfcDoor", "IfcWindow", "IfcRailing",
          "IfcCurtainWall", "IfcRoof", "IfcChimney", "IfcCovering", "IfcMember", "IfcOpeningElement", "IfcPlate",
          "IfcSpace", "IfcZone", "IfcBuilding", "IfcBuildingStorey", "IfcSite", "IfcProject", "IfcPerson",
          "IfcOrganization", "IfcPersonAndOrganization", "IfcProjectedCRS", "IfcMapConversion",
          "IfcGeometricRepresentationContext", "IfcAnnotation", "IfcBuildingElementPart", "IfcFurniture",
          "IfcSanitaryTerminal", "IfcLightFixture", "IfcFlowTerminal", "IfcRamp", "IfcPile"]
_AD = {a.upper(): a for a in _ADLAR}


def sinif_adi(c):
    c = c or ""
    return _AD.get(c.upper(), ("Ifc" + c[3:].capitalize()) if c.upper().startswith("IFC") else c)


def oneri(sinif, gereksinim):
    g = gereksinim or ""
    if sinif == "IFCANNOTATION":
        return ONERI["IfcAnnotation"]
    if sinif in ("IFCPROJECTEDCRS", "IFCMAPCONVERSION"):
        return ONERI["CRS"]
    if sinif == "IFCPROJECT":
        return ONERI["IfcProject"]
    if sinif == "IFCPERSON":
        return ONERI["IfcPerson"]
    if sinif == "IFCORGANIZATION":
        return ONERI["IfcOrganization"]
    if "TrueNorth" in g:
        return ONERI["TrueNorth"]
    if g.startswith("Pset_SpaceCoveringRequirements"):
        return ONERI["Covering"]
    for k in ("TREpys", "Pset_Land", "Qto_Building"):
        if g.startswith(k):
            return ONERI[k]
    if g.startswith("Pset_BuildingCommon") or g.startswith("Pset_Address"):
        return ONERI["Pset_Building"]
    if g.startswith("Pset_SiteCommon"):
        return ONERI["Pset_Site"]
    last = g.split(".")[-1]
    return ONERI.get(last) or ONERI.get(g) or ""


def rapor_yaz(path, bilgi, ozet_once, ozet_sonra, sonuc_sonra, duzeltmeler, uyarilar, model_adi):
    """bilgi: dict (dosya, çıktı, tarih, ids, ayarlar)"""
    sheets = []
    b = {o["kural"]: o for o in ozet_once}
    hata_once = bilgi.get("hata_once", 0)
    hata_sonra = sum(1 for s in sonuc_sonra if not s.gecti)

    # ---- Özet
    s = Sheet("Özet", [52, 20, 12, 13, 12, 13, 9, 9, 9, 12])
    s.add(["e-PYS IDS Kontrol Raporu – PP09 e-PYS IDS Kontrol (ALUPLAN)"], "title")
    s.add(["Model: %s" % model_adi], "duz")
    s.add(["Çıktı: %s" % (bilgi.get("cikti") or "– (yalnız denetim)")], "duz")
    s.add(["Kurallar: %s · Tarih: %s" % (bilgi.get("ids", ""), bilgi.get("tarih", ""))], "duz")
    s.add(["Hatalı kontrol (eleman × gereksinim): önce %d → sonra %d · otomatik düzeltme: %d · uyarı: %d"
           % (hata_once, hata_sonra, len(duzeltmeler), len(uyarilar))], "baslikk")
    if bilgi.get("resmi"):
        s.add([bilgi["resmi"]], "duz")
    if bilgi.get("ids_notu"):
        s.add([bilgi["ids_notu"]], "duz")
    s.add([])
    s.header(["Kural (Specification)", "IFC Sınıfı", "Önce", "Önce kontrol", "Sonra", "Sonra kontrol",
              "Geçen", "Kısmi", "Kalan", "Başarı %"])
    gizli = sum(1 for o in ozet_sonra if o["durum"] == "Uygulanmadı")
    for o in ozet_sonra:
        if o["durum"] == "Uygulanmadı":
            continue
        p = b.get(o["kural"], {})
        oran = (o["kontrol_gecen"] / float(o["kontrol"])) if o["kontrol"] else None
        st = "yesil" if o["durum"] == "Geçti" else ("normal" if o["durum"] == "Uygulanmadı" else "kirmizi")
        s.add([o["kural"], sinif_adi(o["sinif"]), p.get("durum", ""),
               "%d/%d" % (p.get("kontrol_gecen", 0), p.get("kontrol", 0)) if p else "",
               o["durum"], "%d/%d" % (o["kontrol_gecen"], o["kontrol"]), o["gecen"], o["kismi"], o["kalan"], oran],
              styles=[None, None, None, None, st, None, None, None, None, "yuzde"])
    if gizli:
        s.add([])
        s.add(["Modelde karşılığı olmayan %d IDS kuralı gösterilmedi (uygulanmadı)." % gizli], "duz")
    sheets.append(s)

    # ---- Yapılacaklar (kalan hatalar gruplu)
    grp = {}
    for r in sonuc_sonra:
        if r.gecti:
            continue
        k = (r.kural, r.sinif, r.gereksinim)
        g = grp.setdefault(k, {"n": 0, "ornek": [], "bulunan": {}, "beklenen": r.beklenen, "not": r.not_})
        g["n"] += 1
        if len(g["ornek"]) < 5:
            g["ornek"].append("%s (#%s)" % (r.ad or "", r.eid if r.eid else "-"))
        g["bulunan"][r.bulunan] = g["bulunan"].get(r.bulunan, 0) + 1
    s = Sheet("Yapılacaklar", [5, 44, 18, 36, 9, 34, 34, 30, 60, 14])
    s.header(["#", "Kural", "IFC Sınıfı", "Gereksinim", "Eleman", "Bulunan (adet)", "IDS beklentisi",
              "Örnek elemanlar", "Allplan'da / PP09'da yapılacak", "Durum"])
    for i, (k, g) in enumerate(sorted(grp.items(), key=lambda x: -x[1]["n"])):
        bul = ", ".join("%s (%d)" % (bv, n) for bv, n in sorted(g["bulunan"].items(), key=lambda x: -x[1])[:4])
        s.add([i + 1, k[0], sinif_adi(k[1]), k[2], g["n"], bul, g["beklenen"], "; ".join(g["ornek"]),
               oneri(k[1], k[2]) + ((" · " + g["not"]) if g["not"] else ""), "Yapılmadı"],
              styles=[None] * 9 + ["sari"])
    sheets.append(s)

    # ---- Düzeltmeler
    s = Sheet("Otomatik Düzeltmeler", [18, 10, 34, 44, 30, 30, 38])
    s.header(["IFC Sınıfı", "IFC #", "Eleman adı", "Alan", "Eski değer", "Yeni değer", "Kaynak"])
    for d in duzeltmeler:
        s.add([sinif_adi(d.sinif), "#%d" % d.eid, d.ad, d.alan,
               "(boş)" if d.eski is None else str(d.eski), str(d.yeni), d.kaynak])
    sheets.append(s)

    # ---- Eleman listesi
    s = Sheet("Kalan Hatalar", [18, 40, 34, 10, 40, 30, 34, 40])
    s.header(["IFC Sınıfı", "Kural", "Eleman adı", "IFC #", "Gereksinim", "Bulunan", "IDS beklentisi", "Not"])
    for r in sonuc_sonra:
        if r.gecti:
            continue
        s.add([sinif_adi(r.sinif), r.kural, r.ad, ("#%d" % r.eid) if r.eid else "", r.gereksinim,
               r.bulunan or "(boş)", r.beklenen, r.not_])
    sheets.append(s)

    # ---- IDS hatası nedeniyle kalanlar
    ih = [r for r in sonuc_sonra if r.gecti and r.not_.startswith("IDS HATASI")]
    if ih:
        s = Sheet("IDS Hatası", [18, 40, 34, 10, 20, 60])
        s.header(["IFC Sınıfı", "Kural", "Eleman adı", "IFC #", "Gereksinim", "Açıklama"])
        for r in ih:
            s.add([sinif_adi(r.sinif), r.kural, r.ad, "#%d" % r.eid, r.gereksinim, r.not_])
        sheets.append(s)

    # ---- Uyarılar
    s = Sheet("Uyarılar", [120])
    s.header(["Otomatik düzeltilemeyen ve Allplan'da yapılması gerekenler"])
    for u in uyarilar:
        s.add([u])
    sheets.append(s)

    # ---- Allplan eşleşme
    s = Sheet("Allplan Nitelikleri", [30, 26, 70])
    s.header(["IFC alanı", "Allplan niteliği", "Not"])
    for row in ALLPLAN_ESLESME:
        s.add(list(row))
    sheets.append(s)
    write_xlsx(path, sheets)
