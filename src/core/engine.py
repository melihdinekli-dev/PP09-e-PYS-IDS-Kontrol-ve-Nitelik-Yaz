# -*- coding: utf-8 -*-
"""PP09 akışı: denetle / düzelt + rapor. ALUPLAN – PP09."""
import os
import sys
import re
import datetime


def kural_tipi(kurallar, sinif, hedef):
    """Varsayılan değer için IDS'teki veri tipini bulur."""
    sinif = sinif.upper()
    if "." in hedef:
        ps, pr = hedef.split(".", 1)
        for k in kurallar:
            if sinif in k["siniflar"]:
                for g in k["gereksinimler"]:
                    if g["tur"] == "ozellik" and g["pset"] == ps and g["ad"] == pr and g.get("tip"):
                        return g["tip"]
        if ps.startswith("Qto_"):
            if "Area" in pr:
                return "IFCAREAMEASURE"
            if "Volume" in pr:
                return "IFCVOLUMEMEASURE"
            return "IFCLENGTHMEASURE"
        return "IFCLABEL"
    if hedef in ("RefElevation",):
        return "IFCREAL"
    return None


def varsayilan_oku(path, kurallar):
    """'Sınıf; Hedef; Değer[; Tip]' satırları. # ile başlayanlar ve '?' içeren değerler atlanır."""
    out = []
    if not path or not os.path.isfile(path):
        return out
    with open(path, "r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            p = [x.strip() for x in line.split(";")]
            if len(p) < 3 or not p[2] or "?" in p[2]:
                continue
            sinif = p[0].upper()
            if not sinif.startswith("IFC"):
                sinif = "IFC" + sinif
            tip = p[3].upper() if len(p) > 3 and p[3] else kural_tipi(kurallar, sinif, p[1])
            out.append((sinif, p[1], p[2], tip))
    return out


# R9: paket dosya adları (eski adlar da okunur)
PAKET = {"ids": ("ePYS_IDS_Kurallar.ids", "EPYS_IDS.ids"), "form": ("ePYS_IDS_Form.xlsx", "ePYS_Proje_Bilgi_Formu.xlsx"),
         "esleme": ("ePYS_IDS_Eslestirme.txt", "EPYS_IfcEslestirme.txt")}


def paket_dosyasi(anahtar, klasor=None):
    klasor = klasor or os.path.dirname(os.path.abspath(__file__))
    for ad in PAKET[anahtar]:
        p = os.path.join(klasor, ad)
        if os.path.isfile(p):
            return p
    return os.path.join(klasor, PAKET[anahtar][0])


def _p3_yukle(log):
    """PP03 e-PYS IFC çekirdeği (ePYS_IDS_IfcDuzenle.py; eski adı EPYS_IfcDuzenle_core.py) – aynı klasörde."""
    d = os.path.dirname(os.path.abspath(__file__))
    if d not in sys.path:
        sys.path.insert(0, d)
    try:
        try:
            import ePYS_IDS_IfcDuzenle as p3
        except ImportError:
            import EPYS_IfcDuzenle_core as p3
        return p3
    except Exception as ex:
        log("e-PYS IFC çekirdeği yüklenemedi: %s" % ex)
        return None


def _allplan_seti_var(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            if "IFCPROPERTYSET(" in line and "'AllplanAttributes" in line:
                return True
    return False


def calistir(ifc_yolu, duzelt_=True, ayar=None, varsayilan_dosyasi=None, cikti=None, rapor=None,
             kurallar=None, ek5=None, ids_duzelt=True, log=print, ids_yolu=None, form_dosyasi=None):
    from ifc_model import IfcModel
    from checker import denetle
    from fixer import duzelt
    from report import rapor_yaz
    from ids_reader import ids_oku
    ids_bilgi = {}
    if kurallar is None:
        ids_yolu = ids_yolu or paket_dosyasi("ids")
        ids_bilgi, kurallar = ids_oku(ids_yolu)
        log("IDS: %s v%s (%s) – %d kural" % (ids_bilgi.get("title", ""), ids_bilgi.get("version", ""),
                                              ids_bilgi.get("date", ""), len(kurallar)))
    t0 = datetime.datetime.now()
    log("IFC okunuyor: %s" % ifc_yolu)
    m = IfcModel(ifc_yolu)
    log("Şema %s, %d varlık" % (m.schema, len(m.f._index)))
    oz0, s0 = denetle(m, kurallar, ids_duzelt, ek5)
    hata0 = sum(1 for s in s0 if not s.gecti)
    log("Denetim: %d hatalı kontrol" % hata0)
    D, U = [], []
    oz1, s1 = oz0, s0
    base = os.path.splitext(ifc_yolu)[0]
    if duzelt_:
        a = dict(ayar or {})
        a["varsayilanlar"] = varsayilan_oku(varsayilan_dosyasi, kurallar)
        form_uy = []
        if form_dosyasi and os.path.isfile(form_dosyasi):
            try:
                fd = form_oku(form_dosyasi)
                fa, fv, fh, fe = form_cevir(fd)
                for k, v in fa.items():
                    if not a.get(k):
                        a[k] = v
                a["varsayilanlar"] = fv + a["varsayilanlar"]
                log("Proje Bilgi Formu: %d alan dolu, %d hatalı, %d zorunlu eksik" % (len(fd), len(fh), len(fe)))
                form_uy += ["Proje Bilgi Formu – " + (h if h.startswith("ÖRNEK") else "HATALI DEĞER (yazılmadı): " + h) for h in fh]
                if fe:
                    form_uy.append("Proje Bilgi Formu – boş zorunlu alanlar: " + ", ".join(fe))
            except Exception as ex:
                form_uy.append("Proje Bilgi Formu okunamadı (%s): %s" % (os.path.basename(form_dosyasi), ex))
        elif form_dosyasi:
            form_uy.append("Proje Bilgi Formu bulunamadı: %s – paletteki 'Proje Bilgi Formu'nu aç' ile oluşturun" % form_dosyasi)
        # R7: e-PYS IFC (PP03) – Allplan nitelik eşlemesi (CSB_Mahal -> mahal adı, Kod yazısı -> Tag …) PP09'dan ÖNCE
        p3 = _p3_yukle(log) if (a.get("p3_esle") or a.get("p3_temizle")) else None
        p3_uy = []
        mfix = m
        if p3 and a.get("p3_esle") and _allplan_seti_var(ifc_yolu):
            ep = a.get("esleme_dosyasi") or paket_dosyasi("esleme")
            if os.path.isfile(ep):
                kurallar3, hatalar3 = p3.read_rules_file(ep)
                p3_uy += ["e-PYS IFC eşleme dosyası hatası: %s" % h for h in hatalar3]
                if kurallar3:
                    import tempfile
                    tmp1 = os.path.join(tempfile.gettempdir(), "ePYS_IDS_esleme_tmp.ifc")
                    r3 = p3.process(ifc_yolu, kurallar3, out_path=tmp1, remove_moved=False, remove_whole_pset=False,
                                    overwrite=True, report_dir=tempfile.gettempdir(), log=log)
                    c3 = r3["counts"]
                    p3_uy.append("e-PYS IFC eşleme (%s): IFC alanına yazılan %d, Pset'e taşınan %d"
                                 % (os.path.basename(ep), c3.get("yazildi", 0), c3.get("pset", 0)))
                    if c3.get("yazildi", 0) or c3.get("pset", 0):
                        mfix = IfcModel(tmp1)
            else:
                p3_uy.append("e-PYS IFC eşleme dosyası bulunamadı: %s" % ep)
        w, D, U = duzelt(mfix, a, log)
        U = form_uy + p3_uy + U
        cikti = (cikti or "").strip().strip('"') or (base + "_IDS.ifc")
        # R10: yalnız dosya adı yazıldıysa IFC'nin klasörüne; uzantı yoksa .ifc
        if not os.path.isabs(cikti):
            cikti = os.path.join(os.path.dirname(os.path.abspath(ifc_yolu)), cikti)
        if not cikti.lower().endswith(".ifc"):
            cikti += ".ifc"
        os.makedirs(os.path.dirname(cikti), exist_ok=True)
        if os.path.abspath(cikti) == os.path.abspath(ifc_yolu):
            cikti = base + "_IDS.ifc"
        w.write(cikti)
        log("Düzeltme: %d değişiklik, %d yeni varlık → %s" % (len(D), len(w.new), cikti))
        # R7: teslim için AllplanAttributes setlerini temizle (PP03 'tamamen sil')
        if p3 and a.get("p3_temizle") and _allplan_seti_var(cikti):
            import tempfile
            tmp2 = cikti + ".tmp.ifc"
            r3 = p3.process(cikti, [], out_path=tmp2, remove_moved=False, remove_whole_pset=True,
                            report_dir=tempfile.gettempdir(), log=log)
            os.replace(tmp2, cikti)
            U.insert(0, "e-PYS IFC temizlik: AllplanAttributes setleri silindi (%d set, %d nitelik)"
                     % (r3["counts"].get("pset_silindi", 0), r3["counts"].get("nitelik_silindi", 0)))
        m2 = IfcModel(cikti)
        oz1, s1 = denetle(m2, kurallar, ids_duzelt, ek5)
    hata1 = sum(1 for s in s1 if not s.gecti)
    # bakanlık aracının saydığı gibi (IDS deseni aynen, sınıf-yok satırları hariç)
    def resmi(mm):
        _, ss = denetle(mm, kurallar, False, None)
        # bakanlık aracı IfcGeometricRepresentationContext'i bulamıyor -> "sınıf yok" sayılır
        bag = "IFCGEOMETRICREPRESENTATIONCONTEXT"
        el = sum(1 for x in ss if not x.gecti and x.eid and x.sinif != bag)
        yok = sum(1 for x in ss if not x.gecti and not x.eid) + (1 if any(x.sinif == bag for x in ss) else 0)
        return el, yok
    r0 = resmi(m)
    r1 = resmi(IfcModel(cikti)) if duzelt_ else r0
    if not m.schema.startswith("IFC4X3"):
        U.insert(0, "Bilgi: IDS şeması IFC4X3_ADD2, dosya %s. IfcAnnotation (SURVEY) yalnız IFC 4.3'te karşılanabilir." % m.schema)
    rapor = rapor or (base + ("_IDS_Rapor.xlsx" if duzelt_ else "_IDS_Denetim.xlsx"))
    bilgi = {"cikti": cikti if duzelt_ else None, "tarih": t0.strftime("%d.%m.%Y %H:%M"),
             "ids": "%s v%s (%s) – %d kural, modele uygulanan %d" % (ids_bilgi.get("title", "IDS"), ids_bilgi.get("version", ""),
                    ids_bilgi.get("date", ""), len(kurallar), sum(1 for o in oz1 if o["durum"] != "Uygulanmadı")),
             "hata_once": hata0,
             "resmi": "Bakanlık IDS aracının sayımıyla: eleman hatası %d → %d · modelde olmayan zorunlu sınıf: %d"
                      % (r0[0], r1[0], r1[1]),
             "ids_notu": ("IDS'teki bilinen desen hatası düzeltilerek denetlendi; IDS'in kendi deseniyle kalanlar 'IDS Hatası' sayfasında."
                          if any(o.get("ids_hatasi") for o in oz1) else "")}
    rapor_yaz(rapor, bilgi, oz0, oz1, s1, D, U, os.path.basename(ifc_yolu))
    log("Rapor: %s (%d → %d hatalı kontrol)" % (rapor, hata0, hata1))
    return {"once": hata0, "sonra": hata1, "duzeltme": len(D), "uyari": len(U), "cikti": cikti if duzelt_ else None,
            "rapor": rapor, "ozet": oz1}


# ===========================================================================
# R5: e-PYS Proje Bilgi Formu (Excel) – proje başına bir kez doldurulur
# ===========================================================================
# (anahtar, bölüm, soru, durum: Z=zorunlu / O=otomatik bulunur / S=isteğe bağlı, tür, birim/biçim, örnek, nereden, ek)
#   tür: metin | sayi(min,max) | liste(adı) | kod
FORM_ALANLAR = [
    ("proje_kodu", "PROJE", "Proje kodu", "Z", "kod", "MM-PRJ- + 6 büyük harf/rakam", "MM-PRJ-202645", "e-PYS başvurusu", None),
    ("proje_aciklama", "PROJE", "Proje açıklaması", "O", "metin", "serbest metin", "Ada 20892 Parsel 10 Konut Projesi", "Boşsa arsa adı + kullanımdan yazılır", None),
    ("proje_turu", "PROJE", "Proje türü", "Z", "liste", "listeden seçin", "Yeni Yapı", "Ruhsat başvurusu", "PROJE_TURU"),
    ("muellif_ad", "MÜELLİF", "Müellif adı", "Z", "metin", "", "Melih", "", None),
    ("muellif_soyad", "MÜELLİF", "Müellif soyadı", "Z", "metin", "", "Dinekli", "", None),
    ("sicil_no", "MÜELLİF", "Oda sicil numarası", "Z", "metin", "yalnız rakam", "123456", "Meslek odası üye belgesi", None),
    ("meslek", "MÜELLİF", "Meslek / rol", "Z", "liste", "listeden seçin", "Mimar", "", "MESLEK"),
    ("buro_adi", "MÜELLİF", "Büro / şirket adı", "Z", "metin", "", "ALUPLAN Mimarlık Ltd.", "", None),
    ("buro_no", "MÜELLİF", "Büro tescil no veya vergi no", "Z", "metin", "", "1234567890", "Büro tescil belgesi / vergi levhası", None),
    ("il", "ARSA", "İl", "Z", "metin", "", "İstanbul", "Tapu / imar durumu", None),
    ("ilce", "ARSA", "İlçe", "Z", "metin", "", "Ataşehir", "Tapu / imar durumu", None),
    ("mahalle", "ARSA", "Mahalle", "Z", "metin", "", "İçerenköy", "Tapu", None),
    ("acik_adres", "ARSA", "Cadde / sokak / no", "S", "metin", "", "Topçu İbrahim Sk. No 5", "Numarataj", None),
    ("posta_kodu", "ARSA", "Posta kodu", "Z", "metin", "5 rakam", "34752", "PTT posta kodu sorgu", None),
    ("ada", "ARSA", "Ada no", "O", "metin", "rakam", "20892", "Tapu. Boşsa Allplan arsa adından okunur", None),
    ("parsel", "ARSA", "Parsel no", "O", "metin", "rakam", "10", "Tapu. Boşsa Allplan arsa adından okunur", None),
    ("tapu_no", "ARSA", "Tapu kimlik no (taşınmaz no)", "Z", "metin", "", "12345678", "Tapu senedi / TKGM parsel sorgu", None),
    ("arsa_alani", "ARSA", "Arsa alanı", "Z", "sayi(1,1000000)", "m²", "1436", "Tapu / aplikasyon", None),
    ("taks", "ARSA", "TAKS", "Z", "sayi(0.01,1)", "0 ile 1 arası", "0,30", "İmar durumu belgesi", None),
    ("kaks", "ARSA", "KAKS (emsal)", "Z", "sayi(0.01,20)", "sayı", "1,50", "İmar durumu belgesi", None),
    ("cekme_on", "ARSA", "Ön bahçe mesafesi", "Z", "sayi(0,100)", "m", "5", "İmar durumu belgesi", None),
    ("cekme_yan", "ARSA", "Yan bahçe mesafesi", "Z", "sayi(0,100)", "m", "3", "İmar durumu belgesi", None),
    ("cekme_arka", "ARSA", "Arka bahçe mesafesi", "Z", "sayi(0,100)", "m", "3", "İmar durumu belgesi", None),
    ("kot", "ARSA", "±0.00 kotunun deniz seviyesine göre değeri", "Z", "sayi(-100,5000)", "m", "45,30", "Kot kesit / aplikasyon krokisi", None),
    ("yapi_kimlik", "BİNA", "Yapı kimlik no", "S", "metin", "", "", "Yapı ruhsatı. Boşsa bina adı geçici kimlik olarak yazılır", None),
    ("kullanim", "BİNA", "Bina kullanımı", "O", "liste", "listeden seçin", "Konut", "Boşsa mahal adlarından bulunur", "KULLANIM"),
    ("yapim", "BİNA", "Yapım tekniği", "O", "liste", "listeden seçin", "Betonarme karkas", "Boşsa taşıyıcı malzemeden bulunur", "YAPIM"),
    ("yangin_sinifi", "BİNA", "Yangın yönetmeliğine göre bina sınıfı", "O", "liste", "listeden seçin", "Düşük bina", "Boşsa bina yüksekliğinden (21,50 m)", "YANGIN_SINIF"),
    ("brut_alan", "BİNA", "Toplam inşaat alanı (brüt)", "O", "sayi(1,10000000)", "m²", "1850", "Proje alan hesabı. Boşsa modelden yaklaşık hesaplanır – girmeniz önerilir", None),
    ("net_alan", "BİNA", "Toplam net alan", "O", "sayi(1,10000000)", "m²", "1620", "Boşsa mahallerden hesaplanır", None),
    ("yukseklik", "BİNA", "Bina yüksekliği", "O", "sayi(1,1000)", "m", "15,70", "Kesit. Boşsa modelden hesaplanır", None),
    ("tm_dilimi", "KOORDİNAT", "Koordinat sistemi (TM dilimi)", "Z", "liste", "listeden seçin", "TM30 – İstanbul, Bursa, Kocaeli, Eskişehir, Antalya…", "Aplikasyon krokisi / harita mühendisi", "TM"),
    ("saga", "KOORDİNAT", "Proje 0,0 noktasının Sağa (Y) değeri", "Z", "sayi(100000,900000)", "m", "425123,45", "Aplikasyon krokisi (harita mühendisi)", None),
    ("yukari", "KOORDİNAT", "Proje 0,0 noktasının Yukarı (X) değeri", "Z", "sayi(3900000,4700000)", "m", "4536789,12", "Aplikasyon krokisi (harita mühendisi)", None),
    ("kuzey_acisi", "KOORDİNAT", "Kuzey açısı", "Z", "sayi(-360,360)", "derece; plan yukarısı kuzeyse 0, saat yönünde +", "0", "Vaziyet planı kuzey oku", None),
    ("cati_yangin", "ELEMANLAR", "Çatı yangın dayanımı", "Z", "liste", "dakika", "60", "Yangın yönetmeliği / proje müellifi", "DAKIKA"),
    ("gdc_yangin", "ELEMANLAR", "Giydirme cephe yangın dayanımı", "Z", "liste", "dakika", "60", "Yangın yönetmeliği / proje müellifi", "DAKIKA"),
    ("gdc_malzeme", "ELEMANLAR", "Giydirme cephe malzemesi", "O", "metin", "Malzeme_Özellik", "Alüminyum_Cam", "Boşsa giydirme cephe adından (ALU)", None),
    ("gdc_profil_malzeme", "ELEMANLAR", "Giydirme cephe tiriz/travers malzemesi", "O", "metin", "Malzeme_Özellik", "Alüminyum_Profil", "Boşsa giydirme cephe adından (ALU)", None),
    ("kaplama_malzeme", "ELEMANLAR", "Malzemesi olmayan kaplamalar için malzeme", "S", "metin", "Malzeme_Özellik", "Seramik_Süpürgelik", "Yalnız malzemesi boş kaplamalara yazılır", None),
]

FORM_LISTELER = {
    "PROJE_TURU": ["Yeni Yapı", "İlave", "Tadilat", "Güçlendirme", "Yıkım ve Yeniden Yapım"],
    "MESLEK": ["Mimar", "İnşaat Mühendisi (Statik)", "İnşaat Mühendisi", "Makine Mühendisi", "Elektrik Mühendisi",
               "Harita Mühendisi", "Peyzaj Mimarı", "Şehir Plancısı", "Jeoloji Mühendisi"],
    "KULLANIM": ["Konut", "Konut + Ticaret", "Ticaret", "Ofis", "Eğitim", "Sağlık", "Konaklama", "Sanayi", "Kamu", "Diğer"],
    "YAPIM": ["Betonarme karkas", "Betonarme perde (tünel kalıp)", "Çelik karkas", "Yığma", "Ahşap", "Prefabrik", "Karma"],
    "YANGIN_SINIF": ["Düşük bina", "Yüksek bina"],
    "TM": ["TM27 – İzmir, Manisa, Aydın, Balıkesir, Edirne…", "TM30 – İstanbul, Bursa, Kocaeli, Eskişehir, Antalya…",
           "TM33 – Ankara, Konya, Bolu, Karabük…", "TM36 – Kayseri, Adana, Mersin, Samsun, Sivas…",
           "TM39 – Malatya, Elazığ, Diyarbakır, Trabzon, Erzincan…", "TM42 – Erzurum, Van, Ağrı, Kars…",
           "TM45 – Hakkari, Iğdır (doğu uç)…"],
    "DAKIKA": ["15", "30", "45", "60", "90", "120", "180"],
}

_MESLEK_ROL = {"Mimar": "ARCHITECT", "İnşaat Mühendisi (Statik)": "STRUCTURALENGINEER",
               "İnşaat Mühendisi": "CIVILENGINEER", "Makine Mühendisi": "MECHANICALENGINEER",
               "Elektrik Mühendisi": "ELECTRICALENGINEER", "Harita Mühendisi": "Harita Mühendisi",
               "Peyzaj Mimarı": "LANDSCAPEARCHITECT", "Şehir Plancısı": "Şehir Plancısı",
               "Jeoloji Mühendisi": "Jeoloji Mühendisi"}
_TM_EPSG = {"TM27": 5253, "TM30": 5254, "TM33": 5255, "TM36": 5256, "TM39": 5257, "TM42": 5258, "TM45": 5259}


def form_oku(path):
    """Proje Bilgi Formu (xlsx) -> {anahtar: değer}. Yalnız standart kütüphane."""
    import zipfile
    import xml.etree.ElementTree as ET
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
          "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
    z = zipfile.ZipFile(path)
    ss = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", ns):
            ss.append("".join(t.text or "" for t in si.iter("{%s}t" % ns["m"])))
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    rmap = {r.get("Id"): r.get("Target") for r in rels}
    hedef = None
    for sh in wb.find("m:sheets", ns):
        if sh.get("name") == "Form":
            hedef = rmap.get(sh.get("{%s}id" % ns["r"]))
    if not hedef:
        raise ValueError("Formda 'Form' sayfası yok")
    hedef = hedef.lstrip("/")
    if not hedef.startswith("xl/"):
        hedef = "xl/" + hedef
    rows = {}
    for c in ET.fromstring(z.read(hedef)).iter("{%s}c" % ns["m"]):
        ref = c.get("r")
        col = "".join(ch for ch in ref if ch.isalpha())
        row = int("".join(ch for ch in ref if ch.isdigit()))
        t = c.get("t")
        v = c.find("m:v", ns)
        if t == "s" and v is not None:
            val = ss[int(v.text)]
        elif t == "inlineStr":
            val = "".join(x.text or "" for x in c.iter("{%s}t" % ns["m"]))
        elif t == "b" and v is not None:
            val = v.text == "1"
        elif v is not None and v.text is not None:
            try:
                val = float(v.text)
            except ValueError:
                val = v.text
        else:
            val = None
        rows.setdefault(row, {})[col] = val
    out = {}
    anahtarlar = {a[0] for a in FORM_ALANLAR}
    for r in rows.values():
        k = r.get("A")
        if k in anahtarlar:
            v = r.get("D")
            if isinstance(v, str):
                v = v.strip()
            if v not in (None, ""):
                out[k] = v
    return out


def _sayi(v):
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(" ", "")
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", ".")
    return float(s)


def form_cevir(form):
    """Form değerleri -> (ayar güncellemeleri, varsayılan satırları [zorla], hatalar)."""
    ayar, V, H = {}, [], []
    tanim = {a[0]: a for a in FORM_ALANLAR}

    def z(sinif, hedef, deger, tip=None):
        V.append((sinif, hedef, deger, tip, True))

    for k, v in list(form.items()):
        a = tanim[k]
        tur = a[4]
        if tur.startswith("sayi"):
            lo, hi = [float(x) for x in tur[5:-1].split(",")]
            try:
                n = _sayi(v)
            except Exception:
                H.append("%s: '%s' sayı değil" % (a[2], v))
                del form[k]
                continue
            if not lo <= n <= hi:
                H.append("%s: %s, beklenen aralık %s – %s %s" % (a[2], _fmt_s(n), _fmt_s(lo), _fmt_s(hi), a[5]))
                del form[k]
                continue
            form[k] = n
        elif tur == "liste":
            lst = FORM_LISTELER[a[8]]
            sv = _fmt_s(v) if isinstance(v, float) else str(v)
            if sv not in lst:
                # elle yazılmış değer: baştaki kodla eşleştir (ör. 'TM30 …', 'mimar')
                es = [x for x in lst if x.split(" ")[0].lower() == sv.split(" ")[0].lower()]
                if len(es) == 1:
                    sv = es[0]
            if sv not in lst:
                H.append("%s: '%s' listede yok" % (a[2], sv))
                del form[k]
                continue
            form[k] = sv
        elif tur == "kod":
            sv = str(v).strip().upper()
            if not re.fullmatch(r"[A-Z]{2}-PRJ-[0-9A-ZÇĞİÖŞÜ]{6}", sv):
                H.append("%s: '%s' biçimi yanlış (örn. MM-PRJ-202645)" % (a[2], v))
                del form[k]
                continue
            form[k] = sv
        else:
            form[k] = _fmt_s(v) if isinstance(v, float) else str(v)
    f = form
    if "proje_kodu" in f:
        ayar["proje_adi"] = f["proje_kodu"]
    if "proje_aciklama" in f:
        z("IFCPROJECT", "Description", f["proje_aciklama"])
    if "proje_turu" in f:
        z("IFCPROJECT", "Pset_ProjectCommon.ProjectType", f["proje_turu"], "IFCLABEL")
    if "muellif_ad" in f:
        z("IFCPERSON", "GivenName", f["muellif_ad"])
    if "muellif_soyad" in f:
        z("IFCPERSON", "FamilyName", f["muellif_soyad"])
    if "sicil_no" in f:
        z("IFCPERSON", "Identification", f["sicil_no"])
    if "meslek" in f:
        rol = _MESLEK_ROL.get(f["meslek"], f["meslek"])
        z("IFCPERSON", "Roles", rol)
        z("IFCORGANIZATION", "Roles", rol)
    if "buro_adi" in f:
        z("IFCORGANIZATION", "Name", f["buro_adi"])
    if "buro_no" in f:
        z("IFCORGANIZATION", "Identification", f["buro_no"])
    # adres: arsa + bina Pset_Address
    adr = []
    if f.get("mahalle"):
        adr.append(f["mahalle"] + (" Mah." if "mah" not in f["mahalle"].lower() else ""))
    if f.get("acik_adres"):
        adr.append(f["acik_adres"])
    for sn in ("IFCSITE", "IFCBUILDING"):
        if adr:
            z(sn, "Pset_Address.AddressLines", "; ".join(adr), "IFCLABEL")
        if f.get("il"):
            z(sn, "Pset_Address.Town", f["il"], "IFCLABEL")
        if f.get("ilce"):
            z(sn, "Pset_Address.Region", f["ilce"], "IFCLABEL")
        if f.get("il") or f.get("ilce"):
            z(sn, "Pset_Address.Country", "Türkiye", "IFCLABEL")
        if f.get("posta_kodu"):
            z(sn, "Pset_Address.PostalCode", f["posta_kodu"], "IFCLABEL")
            z(sn, "Pset_Address.PostalBox", f["posta_kodu"], "IFCLABEL")
    if f.get("ada") and f.get("parsel"):
        z("IFCSITE", "Pset_LandRegistration.LandID", "%s/%s" % (f["ada"], f["parsel"]), "IFCIDENTIFIER")
    if "tapu_no" in f:
        z("IFCSITE", "Pset_LandRegistration.LandTitleID", f["tapu_no"], "IFCIDENTIFIER")
    if "arsa_alani" in f:
        z("IFCSITE", "Pset_SiteCommon.TotalArea", f["arsa_alani"], "IFCAREAMEASURE")
    if "taks" in f:
        z("IFCSITE", "TREpys_ParselOzellikSeti.TAKS", f["taks"], "IFCREAL")
        z("IFCSITE", "Pset_SiteCommon.SiteCoverageRatio", f["taks"], "IFCPOSITIVERATIOMEASURE")
    if "kaks" in f:
        z("IFCSITE", "TREpys_ParselOzellikSeti.KAKS", f["kaks"], "IFCREAL")
        z("IFCSITE", "Pset_SiteCommon.FloorAreaRatio", f["kaks"], "IFCPOSITIVERATIOMEASURE")
    for k, p in (("cekme_on", "CekmeOn"), ("cekme_yan", "CekmeYan"), ("cekme_arka", "CekmeArka")):
        if k in f:
            z("IFCSITE", "TREpys_ParselOzellikSeti." + p, f[k], "IFCREAL")
    if "kot" in f:
        z("IFCSITE", "RefElevation", f["kot"], "IFCREAL")
    if "yapi_kimlik" in f:
        z("IFCBUILDING", "Pset_BuildingCommon.BuildingID", f["yapi_kimlik"], "IFCIDENTIFIER")
        z("IFCBUILDING", "Pset_BuildingCommon.IsPermanentID", "TRUE", "IFCBOOLEAN")
    if "kullanim" in f:
        z("IFCBUILDING", "Pset_BuildingCommon.OccupancyType", f["kullanim"], "IFCLABEL")
    if "yapim" in f:
        z("IFCBUILDING", "Pset_BuildingCommon.ConstructionMethod", f["yapim"], "IFCLABEL")
    if "yangin_sinifi" in f:
        z("IFCBUILDING", "Pset_BuildingCommon.FireProtectionClass", f["yangin_sinifi"], "IFCLABEL")
    if "brut_alan" in f:
        z("IFCBUILDING", "Pset_BuildingCommon.GrossPlannedArea", f["brut_alan"], "IFCAREAMEASURE")
        z("IFCBUILDING", "Qto_BuildingBaseQuantities.GrossFloorArea", f["brut_alan"], "IFCAREAMEASURE")
    if "net_alan" in f:
        z("IFCBUILDING", "Pset_BuildingCommon.NetPlannedArea", f["net_alan"], "IFCAREAMEASURE")
        z("IFCBUILDING", "Qto_BuildingBaseQuantities.NetFloorArea", f["net_alan"], "IFCAREAMEASURE")
    if "yukseklik" in f:
        z("IFCBUILDING", "Qto_BuildingBaseQuantities.Height", f["yukseklik"], "IFCLENGTHMEASURE")
    if "tm_dilimi" in f:
        tm = f["tm_dilimi"][:4]
        epsg = _TM_EPSG.get(tm)
        for h, v in (("Name", "EPSG:%d" % epsg), ("Description", "TUREF / %s" % tm), ("GeodeticDatum", "TUREF (ITRF96)"),
                     ("VerticalDatum", "TUDKA-99"), ("MapProjection", "Transverse Mercator"), ("MapZone", tm)):
            z("IFCPROJECTEDCRS", h, v)
    if "saga" in f and "yukari" in f:
        import math
        aci = math.radians(f.get("kuzey_acisi", 0.0) or 0.0)
        for h, v in (("Eastings", f["saga"]), ("Northings", f["yukari"]), ("OrthogonalHeight", f.get("kot", 0.0)),
                     ("XAxisAbscissa", round(math.cos(aci), 9)), ("XAxisOrdinate", round(math.sin(aci), 9)), ("Scale", 1.0)):
            z("IFCMAPCONVERSION", h, v)
    if "kuzey_acisi" in f:
        import math
        aci = math.radians(f["kuzey_acisi"])
        z("IFCGEOMETRICREPRESENTATIONCONTEXT", "TrueNorth", "%.9f,%.9f" % (math.sin(aci), math.cos(aci)))
    if "cati_yangin" in f:
        z("IFCROOF", "Pset_RoofCommon.FireRating", f["cati_yangin"], "IFCLABEL")
    if "gdc_yangin" in f:
        z("IFCCURTAINWALL", "Pset_CurtainWallCommon.FireRating", f["gdc_yangin"], "IFCLABEL")
    if "gdc_malzeme" in f:
        ayar["gdc_malzeme"] = f["gdc_malzeme"]
    if "gdc_profil_malzeme" in f:
        ayar["gdc_profil_malzeme"] = f["gdc_profil_malzeme"]
    if "kaplama_malzeme" in f:
        V.append(("IFCCOVERING", "Malzeme", f["kaplama_malzeme"], None, False))
    eksik = [a[2] for a in FORM_ALANLAR if a[3] == "Z" and a[0] not in f]
    def _ayni(k):
        v, o = f[k], tanim[k][6]
        if isinstance(v, float):
            try:
                return abs(v - _sayi(o)) < 1e-9
            except Exception:
                return False
        return str(v).strip() == str(o).strip()
    ornek = [tanim[k][2] for k in ORNEK_KONTROL if k in f and _ayni(k)]
    if ornek:
        H.append("ÖRNEK DEĞER (formun örnek sütunuyla aynı – gerçek bilgiyle değiştirin; IFC'ye yazıldı): " + ", ".join(ornek))
    return ayar, V, H, eksik


# formdaki örnekleri kopyalanmış olabilecek, projeye özgü resmî değerler
ORNEK_KONTROL = ["sicil_no", "buro_no", "tapu_no", "taks", "kaks", "cekme_on", "cekme_yan", "cekme_arka", "kot", "saga",
                 "yukari", "arsa_alani", "buro_adi"]


def _fmt_s(n):
    if isinstance(n, float) and n == int(n):
        return str(int(n))
    return ("%.6f" % n).rstrip("0").rstrip(".") if isinstance(n, float) else str(n)
