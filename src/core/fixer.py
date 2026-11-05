# -*- coding: utf-8 -*-
"""IFC'yi IDS'e göre otomatik düzeltir (yalnız dosyada zaten bulunan bilgiyle). ALUPLAN – PP09."""
import re
import uuid
from ifc_step import Ref, Enum, Typed, _parse_args
from ifc_model import IfcModel, is_empty, plain

# ------------------------------------------------------------------ yardımcılar
_TR = str.maketrans("çğıöşüÇĞİÖŞÜâÂîÎûÛ", "cgiosuCGIOSUaAiIuU")


def ascii_tr(s):
    return (s or "").translate(_TR)


def aciklama_temizle(s, ascii_=True, upper=True):
    """Ek-5 açıklama alanı: boşluk, '-', '/', '.' -> '_' ; '-' yasak."""
    s = (s or "").strip()
    if ascii_:
        s = ascii_tr(s)
    s = re.sub(r"[\s\-/\\.,;:()]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s.upper() if upper else s


_B64 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_$"


def new_guid():
    n = uuid.uuid4().int
    out = []
    for _ in range(22):
        out.append(_B64[n % 64])
        n //= 64
    out[-1] = _B64[(uuid.uuid4().int % 4)]   # ilk karakter 0-3 olmalı (ters sırada son)
    return "".join(reversed(out))


def step_str(s):
    s = s.replace("\\", "\\\\").replace("'", "''")
    out = []
    buf = []
    for ch in s:
        if ord(ch) < 128:
            if buf:
                out.append("\\X2\\" + "".join("%04X" % ord(c) for c in buf) + "\\X0\\")
                buf = []
            out.append(ch)
        else:
            if ord(ch) > 0xFFFF:
                if buf:
                    out.append("\\X2\\" + "".join("%04X" % ord(c) for c in buf) + "\\X0\\")
                    buf = []
                out.append("\\X4\\%08X\\X0\\" % ord(ch))
            else:
                buf.append(ch)
    if buf:
        out.append("\\X2\\" + "".join("%04X" % ord(c) for c in buf) + "\\X0\\")
    return "'" + "".join(out) + "'"


def ser(v):
    if v is None:
        return "$"
    if isinstance(v, Ref):
        return "#%d" % int(v)
    if isinstance(v, Enum):
        return "." + str(v) + "."
    if isinstance(v, bool):
        return ".T." if v else ".F."
    if isinstance(v, Typed):
        return "%s(%s)" % (v.type, ser(v.value))
    if isinstance(v, str):
        if v == "*":
            return "*"
        return step_str(v)
    if isinstance(v, float):
        r = repr(v)
        if "e" in r or "E" in r:
            r = "%.12E" % v
        elif "." not in r:
            r += "."
        return r
    if isinstance(v, int):
        return str(v)
    if isinstance(v, (list, tuple)):
        return "(" + ",".join(ser(x) for x in v) + ")"
    return str(v)


# Sınıf -> (EK-5 kodu, Türkçe adı)
SINIF_KOD = {
    "IFCWALL": ("DVR", "Duvar"), "IFCCOLUMN": ("KLN", "Kolon"), "IFCBEAM": ("KRS", "Kiriş"),
    "IFCSLAB": ("DSM", "Döşeme"), "IFCFOOTING": ("TML", "Temel"), "IFCSTAIR": ("MRD", "Merdiven"),
    "IFCDOOR": ("KAP", "Kapı"), "IFCWINDOW": ("PNC", "Pencere"), "IFCRAILING": ("KRK", "Korkuluk"),
    "IFCCURTAINWALL": ("GDC", "Giydirme Cephe"), "IFCROOF": ("CAT", "Çatı"), "IFCCHIMNEY": ("BAC", "Baca"),
    "IFCCOVERING": ("KPL", "Kaplama"), "IFCMEMBER": ("ELM", "Eleman"), "IFCOPENINGELEMENT": ("ACL", "Açıklık"),
    "IFCZONE": ("ZON", "Zon"), "IFCBUILDING": ("BNA", "Bina"), "IFCBUILDINGSTOREY": ("BNK", "Bina Katı"),
    "IFCSITE": ("SAH", "Saha"), "IFCPLATE": ("PLK", "Plaka"), "IFCRAMP": ("RMP", "Rampa"), "IFCPILE": ("KZK", "Kazık"),
}
ROL_ENUM = {"SUPPLIER", "MANUFACTURER", "CONTRACTOR", "SUBCONTRACTOR", "ARCHITECT", "STRUCTURALENGINEER",
            "COSTENGINEER", "CLIENT", "BUILDINGOWNER", "BUILDINGOPERATOR", "MECHANICALENGINEER", "ELECTRICALENGINEER",
            "PROJECTMANAGER", "FACILITIESMANAGER", "CIVILENGINEER", "COMMISSIONINGENGINEER", "ENGINEER", "OWNER",
            "CONSULTANT", "CONSTRUCTIONMANAGER", "FIELDCONSTRUCTIONMANAGER", "RESELLER"}
ROL_TR = {"ARCHITECT": "Mimar", "STRUCTURALENGINEER": "İnşaat Mühendisi (Statik)", "CIVILENGINEER": "İnşaat Mühendisi",
          "MECHANICALENGINEER": "Makine Mühendisi", "ELECTRICALENGINEER": "Elektrik Mühendisi", "ENGINEER": "Mühendis",
          "OWNER": "Mal Sahibi", "BUILDINGOWNER": "Yapı Sahibi", "CLIENT": "İşveren", "CONTRACTOR": "Yüklenici",
          "PROJECTMANAGER": "Proje Yöneticisi", "CONSULTANT": "Danışman", "CONSTRUCTIONMANAGER": "Şantiye Şefi"}
KOD_SINIF = {"TML": "IFCFOOTING", "BAC": "IFCCHIMNEY"}
# disiplin kısıtları (IDS)
DISIPLIN_IZIN = {
    "IFCDOOR": ("MM", "IM"), "IFCWINDOW": ("MM", "IM"), "IFCCOVERING": ("MM", "IM"),
    "IFCFOOTING": ("AL", "ST", "ZE"), "IFCPILE": ("ST",),
    "IFCWALL": ("MM", "IM", "PY", "AL", "ST", "ZE"), "IFCCOLUMN": ("MM", "IM", "PY", "AL", "ST", "ZE"),
    "IFCBEAM": ("MM", "IM", "PY", "AL", "ST", "ZE"), "IFCSLAB": ("MM", "IM", "PY", "AL", "ST", "ZE"),
    "IFCSTAIR": ("MM", "IM", "PY", "AL", "ST", "ZE"),
}
ENUM_GECERLI = {  # PredefinedType için USERDEFINED dışındaki geçerli değerler (IFC4)
    "IFCCHIMNEY": {"USERDEFINED", "NOTDEFINED"},
    "IFCFOOTING": {"CAISSON_FOUNDATION", "FOOTING_BEAM", "PAD_FOOTING", "PILE_CAP", "STRIP_FOOTING", "USERDEFINED", "NOTDEFINED"},
}
SLAB_TO_FOOTING_PT = {"BASESLAB": "USERDEFINED"}


def ad_duzelt(ad, sinif, disiplin_varsayilan="MM", yedek_aciklama=""):
    """Ek-5 biçimine getirir: DD-KOD-AÇIKLAMA. Yeni ad ya da None (değişiklik yoksa)."""
    kod = SINIF_KOD.get(sinif, (None,))[0]
    if not kod:
        return None
    orj = ad or ""
    s = orj.strip()
    izin = DISIPLIN_IZIN.get(sinif)
    m = re.match(r"^([A-Za-z]{2})[\s_\-]+([A-Za-z]{3})[\s_\-]+(.+)$", s)
    if m and m.group(2).upper() in (kod,) + tuple(c for c, _ in SINIF_KOD.values()):
        dis, rest = m.group(1).upper(), m.group(3)
    else:
        m2 = re.match(r"^([A-Za-z]{2})[\s_\-]+(.+)$", s)
        if m2 and m2.group(1).upper() in ("MM", "IM", "PY", "AL", "ST", "ZE", "EE", "MK", "HR", "YN", "GS", "AK"):
            dis, rest = m2.group(1).upper(), m2.group(2)
        else:
            dis, rest = disiplin_varsayilan, s
    if izin and dis not in izin:
        dis = izin[0] if disiplin_varsayilan not in izin else disiplin_varsayilan
    acik = aciklama_temizle(rest) or aciklama_temizle(yedek_aciklama) or SINIF_KOD[sinif][1].upper()
    acik = aciklama_temizle(acik)
    yeni = "%s-%s-%s" % (dis, kod, acik)
    return None if yeni == orj else yeni


def mahal_no_duzelt(ad, kat_kodu):
    """K##/B##_XXX_### biçimi; eksik kat önekini kattan tamamlar."""
    s = (ad or "").strip().upper()
    if re.fullmatch(r"(K\d{2}|B\d{2})_[A-ZÇĞİÖŞÜ0-9]{3}_\d{3}", s):
        return None
    m = re.fullmatch(r"Z(\d{2})_([A-Z0-9ÇĞİÖŞÜ]{3})_(\d{3})", s)
    if m:
        return "K%s_%s_%s" % (m.group(1), m.group(2), m.group(3))
    if not kat_kodu:
        return None
    m = re.fullmatch(r"_?([A-Z0-9ÇĞİÖŞÜ]{3})_(\d{1,3})", s)
    if m:
        return "%s_%s_%03d" % (kat_kodu, m.group(1), int(m.group(2)))
    m = re.fullmatch(r"([A-Z]{3})_([A-Z0-9ÇĞİÖŞÜ]{3})_(\d{3})", s)   # OAL_OAL_001, BDR_BDR_001
    if m:
        return "%s_%s_%s" % (kat_kodu, m.group(2), m.group(3))
    return None


# ------------------------------------------------------------------ yazıcı
class IfcWriter(object):
    def __init__(self, model):
        self.m = model
        self.f = model.f
        self.mod = {}        # eid -> (cls, args)
        self.new = []        # (eid, cls, args)
        self._new_idx = {}   # eid -> [cls, args]
        self.next_id = max(self.f._index) + 1 if self.f._index else 1
        self.owner = None
        oh = list(self.f.of("IFCOWNERHISTORY"))
        self.owner = Ref(oh[0]) if oh else None

    def args(self, eid):
        eid = int(eid)
        if eid in self.mod:
            return self.mod[eid][1]
        if eid in self._new_idx:
            return self._new_idx[eid][1]
        return self.f.args(eid)

    def cls(self, eid):
        eid = int(eid)
        if eid in self.mod:
            return self.mod[eid][0]
        if eid in self._new_idx:
            return self._new_idx[eid][0]
        return self.f.cls(eid)

    def set_arg(self, eid, idx, val, new_cls=None):
        eid = int(eid)
        cls = self.cls(eid)
        a = list(self.args(eid))
        while len(a) <= idx:
            a.append(None)
        a[idx] = val
        if eid in self._new_idx:
            self._new_idx[eid][0] = new_cls or cls
            self._new_idx[eid][1][:] = a
            return
        self.mod[eid] = (new_cls or cls, a)

    def set_cls(self, eid, new_cls):
        eid = int(eid)
        self.mod[eid] = (new_cls, list(self.args(eid)))

    def add(self, cls, args):
        eid = self.next_id
        self.next_id += 1
        rec = [cls, list(args)]
        self._new_idx[eid] = rec
        self.new.append((eid, rec))
        return Ref(eid)

    # -------- pset işlemleri
    def _rels_of(self, eid):
        if not hasattr(self, "_rel_idx"):
            self._rel_idx = {}
            for rid in self.f.of("IFCRELDEFINESBYPROPERTIES"):
                a = self.f.args(rid)
                for o in a[4]:
                    self._rel_idx.setdefault(int(o), []).append(rid)
        return self._rel_idx.get(int(eid), [])

    def _pset_users(self, pid):
        if not hasattr(self, "_pset_use"):
            self._pset_use = {}
            for rid in self.f.of("IFCRELDEFINESBYPROPERTIES"):
                a = self.f.args(rid)
                self._pset_use[int(a[5])] = self._pset_use.get(int(a[5]), 0) + len(a[4])
        return self._pset_use.get(int(pid), 0)

    def find_pset(self, eid, name, cls="IFCPROPERTYSET"):
        for rid in self._rels_of(eid):
            pid = self.args(rid)[5]
            if self.cls(pid) == cls and self.args(pid)[2] == name:
                return int(pid)
        for rid, pid in getattr(self, "_new_rel", {}).get(int(eid), []):
            if self.cls(pid) == cls and self.args(pid)[2] == name:
                return int(pid)
        return None

    def set_property(self, eid, pset, prop, value, ifc_type):
        """Özellik yoksa ekler, varsa değerini değiştirir."""
        val = Typed(ifc_type, value)
        pid = self.find_pset(eid, pset)
        if pid is not None:
            pa = self.args(pid)
            for pr in pa[4] or []:
                if self.cls(pr) == "IFCPROPERTYSINGLEVALUE" and self.args(pr)[0] == prop:
                    self.set_arg(pr, 2, val)
                    return
            newp = self.add("IFCPROPERTYSINGLEVALUE", [prop, None, val, None])
            if self._pset_users(pid) <= 1:
                self.set_arg(pid, 4, list(pa[4] or []) + [newp])
                return
            # paylaşılan pset: kopyala
            props = list(pa[4] or []) + [newp]
            self._new_pset(eid, pset, props, replace=pid)
            return
        newp = self.add("IFCPROPERTYSINGLEVALUE", [prop, None, val, None])
        self._new_pset(eid, pset, [newp])

    def _new_pset(self, eid, pset, props, replace=None, cls="IFCPROPERTYSET"):
        if cls == "IFCPROPERTYSET":
            pid = self.add(cls, [new_guid(), self.owner, pset, None, props])
        else:
            pid = self.add(cls, [new_guid(), self.owner, pset, None, None, props])
        if replace is not None:
            for rid in self._rels_of(eid):
                ra = self.args(rid)
                if int(ra[5]) == int(replace):
                    objs = [o for o in ra[4] if int(o) != int(eid)]
                    self.set_arg(rid, 4, objs)
        self.add("IFCRELDEFINESBYPROPERTIES", [new_guid(), self.owner, None, None, [Ref(eid)], pid])
        if not hasattr(self, "_new_rel"):
            self._new_rel = {}
        self._new_rel.setdefault(int(eid), []).append((None, pid))
        return pid

    def set_quantity(self, eid, qset, qname, value, qcls):
        """qcls: IFCQUANTITYAREA / IFCQUANTITYLENGTH ..."""
        pid = self.find_pset(eid, qset, "IFCELEMENTQUANTITY")
        if pid is not None:
            for qq in self.args(pid)[5] or []:
                if self.args(qq)[0] == qname:
                    self.set_arg(qq, 3, float(value))
                    return
        q = self.add(qcls, [qname, None, None, float(value), None])
        if pid is not None:
            pa = self.args(pid)
            self.set_arg(pid, 5, list(pa[5] or []) + [q])
            return
        self._new_pset(eid, qset, [q], cls="IFCELEMENTQUANTITY")

    # -------- dosya yaz
    def write(self, path):
        f = self.f
        text = f.text
        spans = []
        for eid, (cls, a) in self.mod.items():
            start_cls, apos = f._index[eid]
            m = re.compile(r"#%d\s*=" % eid).search(text, max(0, apos - 200))
            s0 = m.start() if m else apos
            _, end = _parse_args(text, apos)
            e = text.find(";", end)
            spans.append((s0, e + 1, "#%d=%s%s;" % (eid, cls, ser(a))))
        spans.sort()
        out = []
        last = 0
        for s0, e, rep in spans:
            out.append(text[last:s0])
            out.append(rep)
            last = e
        rest = text[last:]
        # yeni varlıkları DATA bölümünün sonuna ekle
        k = rest.rfind("ENDSEC;")
        new_lines = "".join("#%d=%s%s;\n" % (i, r[0], ser(r[1])) for i, r in self.new)
        if k >= 0:
            rest = rest[:k] + new_lines + rest[k:]
        else:
            rest += new_lines
        out.append(rest)
        data = "".join(out)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(data)


# ------------------------------------------------------------------ düzeltici
class Duzeltme(object):
    __slots__ = ("sinif", "eid", "ad", "alan", "eski", "yeni", "kaynak")

    def __init__(self, sinif, eid, ad, alan, eski, yeni, kaynak):
        self.sinif, self.eid, self.ad, self.alan, self.eski, self.yeni, self.kaynak = sinif, eid, ad, alan, eski, yeni, kaynak


VARSAYILAN_AYAR = {
    "tag_kod_yazisi": True,        # Tag <- Kod yazısı (değişken adlı ve katmanlı AllplanAttributes dahil)
    "predefined_userdefined": True,
    "ad_bicim": True,              # Ek-5 ad biçimi (ayraç, kod, açıklama)
    "sinif_duzelt": True,          # TML -> IfcFooting, BAC -> IfcChimney
    "mahal_no": True,              # K## öneki katla tamamlanır, Z00 -> K00
    "mahal_kaplama": True,         # Pset_SpaceCoveringRequirements <- mahaldeki kaplamalar
    "kat_bilgi": True,             # ElevationOfSSLRelative, NetFloorArea
    "bina_bilgi": True,            # NumberOfStoreys, Gross/NetFloorArea, GrossPlannedArea ...
    "oto_bilgi": True,             # R5: ada/parsel, alanlar, yükseklik, yapım tekniği, kullanım, açıklama (geometriden)
    "giydirme_cephe": True,        # R5: tiriz/travers <- bağlı olduğu giydirme cephe (dış eleman, Tag+sıra, malzeme)
    "gdc_malzeme": "",             # Proje Bilgi Formu: giydirme cephe malzemesi
    "gdc_profil_malzeme": "",      # Proje Bilgi Formu: tiriz/travers profil malzemesi
    "adres": True,                 # Pset_Address <- IfcPostalAddress
    "zon": True,                   # MM-ZON-xxx, LongName, ObjectType
    "kacis_yolu": True,            # Pset_StairCommon.FireExit <- 'Acil Çıkış'
    "dis_eleman": True,            # kapı/pencere IsExternal <- boşluğun 'Dış Yapı Elemanı'; çatı TRUE
    "yangin_dakika": True,         # F120 -> 120
    "disiplin": "MM",
    "bina_adi": "",                # örn. MM-BNA-A_BLOK
    "bina_uzun_ad": "",
    "proje_adi": "",               # 10 bloklu e-PYS proje kodu
    "varsayilanlar": [],           # [(sınıf, 'Pset.Özellik' ya da nitelik, değer, tip)]
}

ZON_LONG = {"OAL": "Ortak Alan", "ORT": "Ortak Alan", "BDR": "Bodrum", "OPK": "Otopark", "DKN": "Dükkan",
            "DEP": "Depo", "LOB": "Lobi", "KHL": "Kat Holü", "OFS": "Ofis", "TRS": "Teras", "CTK": "Çatı Katı"}


def _kod_yazisi(model, eid):
    ps = model.psets(eid)
    best = None
    for pn, props in ps.items():
        if not pn.startswith("AllplanAttributes"):
            continue
        for k, (v, t) in props.items():
            if k == "Kod yazısı" and not is_empty(v):
                return str(v)
            if k.endswith(".Kod yazısı") and not is_empty(v) and best is None:
                best = str(v)
    return best


def _allplan_attr(model, eid, name):
    ps = model.psets(eid)
    for pn, props in ps.items():
        if not pn.startswith("AllplanAttributes"):
            continue
        if name in props and not is_empty(props[name][0]):
            return props[name][0]
        for k, (v, t) in props.items():
            if k.endswith("." + name) and not is_empty(v):
                return v
    return None


# ---------------------------------------------------------------------------
# R5: basit geometri (ekstrüzyon profilleri) – alan ve kot hesapları
def _shoelace(pts):
    a = 0.0
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i][0], pts[i][1]
        x2, y2 = pts[(i + 1) % n][0], pts[(i + 1) % n][1]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2.0


def _curve_area(f, c):
    cls = f.cls(c)
    if cls == "IFCPOLYLINE":
        pts = [f.args(p)[0] for p in f.args(c)[0]]
        if len(pts) > 1 and pts[0] == pts[-1]:
            pts = pts[:-1]
        return _shoelace(pts)
    if cls == "IFCINDEXEDPOLYCURVE":
        pl = f.args(c)[0]
        pts = f.args(pl)[0]
        if len(pts) > 1 and pts[0] == pts[-1]:
            pts = pts[:-1]
        return _shoelace(pts)
    return 0.0


def _profile_area(f, p):
    cls = f.cls(p)
    a = f.args(p)
    if cls == "IFCRECTANGLEPROFILEDEF":
        return float(a[3]) * float(a[4])
    if cls == "IFCARBITRARYCLOSEDPROFILEDEF":
        return _curve_area(f, a[2])
    if cls == "IFCARBITRARYPROFILEDEFWITHVOIDS":
        return max(0.0, _curve_area(f, a[2]) - sum(_curve_area(f, v) for v in (a[3] or [])))
    if cls == "IFCCIRCLEPROFILEDEF":
        return 3.141592653589793 * float(a[3]) ** 2
    return 0.0


def _dikey(f, d):
    if d is None:
        return True
    v = f.args(d)[0]
    return len(v) > 2 and abs(float(v[2])) > 0.999


def _plc_z(f, pl):
    z = 0.0
    guard = 0
    while pl is not None and guard < 20:
        guard += 1
        a = f.args(pl)
        if f.cls(pl) != "IFCLOCALPLACEMENT":
            break
        ax = a[1]
        if ax is not None and f.cls(ax) == "IFCAXIS2PLACEMENT3D":
            if not _dikey(f, f.args(ax)[1]):
                return None
            loc = f.args(f.args(ax)[0])[0]
            if len(loc) > 2:
                z += float(loc[2])
        pl = a[0]
    return z


def _solid_items(f, it):
    cls = f.cls(it)
    if cls == "IFCEXTRUDEDAREASOLID":
        return [it]
    if cls in ("IFCBOOLEANCLIPPINGRESULT", "IFCBOOLEANRESULT"):
        return _solid_items(f, f.args(it)[1])
    return []


def geometri(model):
    """{eid: (alan m², alt z, üst z)} – Body ekstrüzyonlarından (yaklaşık)."""
    if getattr(model, "_geo", None) is not None:
        return model._geo
    f = model.f
    out = {}
    for cls in ("IFCSPACE", "IFCSLAB", "IFCWALL", "IFCCOLUMN", "IFCBEAM", "IFCROOF", "IFCCURTAINWALL",
                "IFCCHIMNEY", "IFCFOOTING", "IFCMEMBER", "IFCPLATE", "IFCSTAIR", "IFCRAILING"):
        for e in f.of(cls):
            try:
                a = f.args(e)
                rep = a[6] if len(a) > 6 else None
                if rep is None:
                    continue
                z0 = _plc_z(f, a[5])
                if z0 is None:
                    continue
                alan = 0.0
                lo = hi = None
                for r in f.args(rep)[2] or []:
                    ra = f.args(r)
                    if ra[1] not in ("Body", None):
                        continue
                    for it in ra[3] or []:
                        for so in _solid_items(f, it):
                            sa = f.args(so)
                            pz = 0.0
                            if sa[1] is not None:
                                if not _dikey(f, f.args(sa[1])[1]):
                                    continue
                                loc = f.args(f.args(sa[1])[0])[0]
                                pz = float(loc[2]) if len(loc) > 2 else 0.0
                            d = f.args(sa[2])[0]
                            dz = float(d[2]) if len(d) > 2 else 0.0
                            h = float(sa[3]) * dz
                            b = z0 + pz
                            l_, t_ = min(b, b + h), max(b, b + h)
                            lo = l_ if lo is None else min(lo, l_)
                            hi = t_ if hi is None else max(hi, t_)
                            if abs(dz) > 0.9:
                                alan += _profile_area(f, sa[0])
                if lo is not None:
                    out[int(e)] = (alan, lo, hi)
            except Exception:
                continue
    model._geo = out
    return out


def _kat_haritasi(model):
    """eleman -> kat (içerme + toplama ilişkileri)"""
    f = model.f
    k = {}
    for r in f.of("IFCRELCONTAINEDINSPATIALSTRUCTURE"):
        a = f.args(r)
        if f.cls(a[5]) == "IFCBUILDINGSTOREY":
            for o in a[4]:
                k[int(o)] = int(a[5])
    for r in f.of("IFCRELAGGREGATES"):
        a = f.args(r)
        if f.cls(a[4]) == "IFCBUILDINGSTOREY":
            for o in a[5]:
                k[int(o)] = int(a[4])
    return k


def _yapim_teknigi(model):
    from collections import Counter
    c = Counter()
    for cls in ("IFCCOLUMN", "IFCBEAM", "IFCWALL", "IFCSLAB"):
        for e in model.f.of(cls):
            for mt in model.materials(e) or []:
                u = ascii_tr(str(mt)).upper()
                if "BETON" in u or u.startswith("C") and re.match(r"C\d\d", u):
                    c["Betonarme"] += 1
                elif "CELIK" in u or "S235" in u or "S355" in u:
                    c["Celik"] += 1
                elif "AHSAP" in u or "GLULAM" in u:
                    c["Ahsap"] += 1
    if not c:
        return None
    k = c.most_common(1)[0][0]
    return {"Betonarme": "Betonarme_Karkas", "Celik": "Çelik_Karkas", "Ahsap": "Ahşap"}[k]


def _kullanim(model):
    f = model.f
    adlar = [ascii_tr(str(model.attr(s, "LongName")[0] or "")).upper() for s in f.of("IFCSPACE")]
    zon = [model.name(z) or "" for z in f.of("IFCZONE")]
    konut = sum(1 for a in adlar if re.search(r"SALON|YATAK|MUTFAK|BANYO|BALKON|ODASI|ANTRE", a))
    ticari = sum(1 for a in adlar if re.search(r"DUKKAN|MAGAZA|OFIS|BURO|SATIS", a))
    if any(re.search(r"(^|[-_])D\d{2}$", z) for z in zon) or konut > ticari:
        return "Konut" if ticari == 0 else "Konut_Ticaret"
    if ticari:
        return "Ticaret"
    return None


def bina_olculeri(model):
    """Geometriden: net (mahal), brüt (kat döşemeleri), taban alanı, yükseklik, saçak yüksekliği."""
    f = model.f
    g = geometri(model)
    kat = _kat_haritasi(model)
    el = {}
    for st in f.of("IFCBUILDINGSTOREY"):
        v = model.attr(st, "Elevation")[0]
        el[int(st)] = float(v) if isinstance(v, (int, float)) else 0.0
    net = 0.0
    kat_net = {}
    for sp in f.of("IFCSPACE"):
        q = model.psets(sp).get("Qto_SpaceBaseQuantities", {}).get("NetFloorArea", (None,))[0]
        a = q if isinstance(q, (int, float)) else g.get(int(sp), (0.0,))[0]
        net += a
        st = kat.get(int(sp))
        if st:
            kat_net[st] = kat_net.get(st, 0.0) + a
    kat_brut = {}
    for sl in list(f.of("IFCSLAB")) + list(f.of("IFCFOOTING")):
        gg = g.get(int(sl))
        if not gg or gg[0] <= 0:
            continue
        # Allplan döşemeyi alttaki kata bağlar: üst yüzü hangi katın kotundaysa o katın döşemesidir
        yakin = [s for s, e in el.items() if abs(gg[2] - e) <= 0.35]
        if yakin:
            st = min(yakin, key=lambda s: abs(gg[2] - el[s]))
            kat_brut[st] = kat_brut.get(st, 0.0) + gg[0]
    # brüt kat alanı en az o katın net alanı kadar olmalı (döşeme parçalı modellenmiş olabilir)
    for st in set(kat_brut) | set(kat_net):
        kat_brut[st] = max(kat_brut.get(st, 0.0), kat_net.get(st, 0.0))
    brut = sum(kat_brut.values())
    ust = [s for s in kat_brut if el.get(s, 0.0) >= -0.01]
    taban = kat_brut[min(ust, key=lambda s: el[s])] if ust else 0.0
    hi = [v[2] for e, v in g.items() if f.cls(e) in ("IFCWALL", "IFCSLAB", "IFCROOF", "IFCCOLUMN", "IFCCURTAINWALL", "IFCCHIMNEY")]
    buyuk = [v[2] for e, v in g.items() if f.cls(e) in ("IFCSLAB", "IFCROOF") and v[0] >= 20.0]
    return {"net": round(net, 2), "brut": round(brut, 2), "taban": round(taban, 2),
            "yukseklik": round(max(hi), 2) if hi else None, "sacak": round(max(buyuk), 2) if buyuk else None,
            "kat_net": kat_net, "kat_brut": kat_brut}


def duzelt(model, ayar=None, log=None):
    """Düzeltmeleri uygular; (writer, düzeltme listesi, uyarılar) döndürür."""
    A = dict(VARSAYILAN_AYAR)
    if ayar:
        A.update(ayar)
    w = IfcWriter(model)
    f = model.f
    D = []
    U = []

    def kayit(eid, alan, eski, yeni, kaynak):
        nm = model.name(eid) if model.f.cls(eid) else ""
        D.append(Duzeltme(w.cls(eid) or "", int(eid), nm or "", alan, eski, yeni, kaynak))

    lay = model.layout

    def idx(cls, name):
        l = lay.get(cls) or lay["_ELEMENT"]
        return l.index(name) if name in l else None

    # 1) sınıf düzeltmesi (TML -> IfcFooting, BAC -> IfcChimney)
    if A["sinif_duzelt"]:
        for cls in ("IFCSLAB", "IFCWALL", "IFCBEAM", "IFCCOLUMN"):
            for e in list(f.of(cls)):
                nm = model.name(e) or ""
                m = re.match(r"^[A-Za-z]{2}[\s_\-]+([A-Za-z]{3})[\s_\-]+", nm)
                if m and m.group(1).upper() in KOD_SINIF and KOD_SINIF[m.group(1).upper()] != cls:
                    yeni = KOD_SINIF[m.group(1).upper()]
                    w.set_cls(e, yeni)
                    pt = model.attr(e, "PredefinedType")[0]
                    if pt is not None and pt not in ENUM_GECERLI.get(yeni, set()):
                        w.set_arg(e, 8, Enum("USERDEFINED"))
                        if is_empty(model.attr(e, "ObjectType")[0]):
                            w.set_arg(e, 4, _allplan_attr(model, e, "IFC obje kategorisi") or SINIF_KOD[yeni][1])
                    kayit(e, "IFC sınıfı", cls, yeni, "Ad kodu " + m.group(1).upper())
                    # ortak Pset adını yeni sınıfa taşı
                    old_ps = "Pset_" + cls[3:].capitalize() + "Common"
                    new_ps = {"IFCFOOTING": "Pset_FootingCommon", "IFCCHIMNEY": "Pset_ChimneyCommon"}[yeni]
                    pid = w.find_pset(e, old_ps.replace("Pset_Slab", "Pset_Slab"))
                    if pid is None:
                        for cand in ("Pset_SlabCommon", "Pset_WallCommon", "Pset_BeamCommon", "Pset_ColumnCommon"):
                            pid = w.find_pset(e, cand)
                            if pid:
                                break
                    if pid is not None:
                        eski_ps = w.args(pid)[2]
                        w.set_arg(pid, 2, new_ps)
                        kayit(e, "Pset adı", eski_ps, new_ps, "Sınıf değişti")

    def ccls(e):
        return w.cls(e)

    elem_classes = ["IFCWALL", "IFCCOLUMN", "IFCBEAM", "IFCSLAB", "IFCFOOTING", "IFCSTAIR", "IFCDOOR", "IFCWINDOW",
                    "IFCRAILING", "IFCCURTAINWALL", "IFCROOF", "IFCCHIMNEY", "IFCCOVERING", "IFCMEMBER",
                    "IFCOPENINGELEMENT", "IFCPLATE"]
    all_elems = []
    for c in elem_classes:
        all_elems += list(f.of(c))

    # 2) ad biçimi
    if A["ad_bicim"]:
        for e in all_elems:
            cls = ccls(e)
            if cls == "IFCPLATE":
                continue
            nm = model.name(e)
            yedek = ""
            if is_empty(nm) or not str(nm).strip():
                mats = model.materials(e)
                if not mats and cls != "IFCROOF":
                    # adı ve malzemesi olmayan eleman: ad vermek onu ek IDS kurallarına sokar (Tag, yangın, malzeme…)
                    U.append("%s #%d: adı ve malzemesi yok – Allplan'da İsim, Malzeme, Yangın dayanımı, Dış eleman ve "
                             "Kod yazısı verin" % (cls, e))
                    continue
                yedek = mats[0] if mats else ""
            yeni = ad_duzelt(nm, cls, A["disiplin"], yedek)
            if yeni:
                w.set_arg(e, 2, yeni)
                kayit(e, "Name", nm, yeni, "Ek-5 ad biçimi")

    # 3) Tag <- Kod yazısı
    if A["tag_kod_yazisi"]:
        for e in all_elems:
            cls = ccls(e)
            if cls == "IFCOPENINGELEMENT":
                continue
            i = idx(cls, "Tag")
            if i is None:
                continue
            tag = model.attr(e, "Tag")[0]
            if is_empty(tag):
                kod = _kod_yazisi(model, e)
                if kod:
                    w.set_arg(e, i, kod)
                    kayit(e, "Tag", tag, kod, "Kod yazısı")

    # 4) PredefinedType boş -> USERDEFINED (+ObjectType)
    if A["predefined_userdefined"]:
        for e in all_elems:
            cls = ccls(e)
            i = idx(cls, "PredefinedType")
            if i is None:
                continue
            a = w.args(e)
            if i < len(a) and a[i] is None:
                w.set_arg(e, i, Enum("USERDEFINED"))
                ot = model.attr(e, "ObjectType")[0]
                if is_empty(ot):
                    ot_new = _allplan_attr(model, e, "IFC obje kategorisi") or _allplan_attr(model, e, "Obje_İsmi") \
                        or SINIF_KOD.get(cls, ("", cls))[1]
                    w.set_arg(e, 4, str(ot_new))
                kayit(e, "PredefinedType", None, "USERDEFINED", "Boş idi; ObjectType ile")

    # 5) yangın dakika biçimi F120 -> 120
    if A["yangin_dakika"]:
        for e in all_elems:
            for pn, props in model.psets(e, with_type=False).items():
                if pn.startswith("Pset_") and "FireRating" in props:
                    v, t = props["FireRating"]
                    if isinstance(v, str):
                        m = re.fullmatch(r"\s*[A-Za-z]{1,3}\s*[-]?\s*(\d{2,3})\s*", v)
                        if m:
                            w.set_property(e, pn, "FireRating", m.group(1), "IFCLABEL")
                            kayit(e, pn + ".FireRating", v, m.group(1), "Tam sayı dakika (IDS açıklaması)")

    # 6) merdiven kaçış yolu
    if A["kacis_yolu"]:
        for e in f.of("IFCSTAIR"):
            ps = model.psets(e)
            sc = ps.get("Pset_StairCommon", {})
            if "FireExit" not in sc:
                v = None
                for pn, props in ps.items():
                    for k, (val, t) in props.items():
                        if k.split(".")[-1] in ("Acil Çıkış", "Kaçış Yolu") and isinstance(val, bool):
                            v = val
                if v is not None:
                    w.set_property(e, "Pset_StairCommon", "FireExit", Enum("T" if v else "F"), "IFCBOOLEAN")
                    kayit(e, "Pset_StairCommon.FireExit", None, "TRUE" if v else "FALSE", "'Acil Çıkış' niteliği")

    # 7) dış eleman
    if A["dis_eleman"]:
        fills = {}
        for r in f.of("IFCRELFILLSELEMENT"):
            a = f.args(r)
            fills[int(a[5])] = int(a[4])
        for cls, pset in (("IFCWINDOW", "Pset_WindowCommon"), ("IFCDOOR", "Pset_DoorCommon")):
            for e in f.of(cls):
                if "IsExternal" in model.psets(e).get(pset, {}):
                    continue
                op = fills.get(int(e))
                v = _allplan_attr(model, op, "Dış Yapı Elemanı") if op else None
                if isinstance(v, bool):
                    w.set_property(e, pset, "IsExternal", Enum("T" if v else "F"), "IFCBOOLEAN")
                    kayit(e, pset + ".IsExternal", None, "TRUE" if v else "FALSE", "Boşluğun 'Dış Yapı Elemanı'")
                else:
                    U.append("%s #%d (%s): IsExternal bilinmiyor – Allplan'da 'Dış Yapı Elemanı' girin" % (cls, e, model.name(e)))
        for e in f.of("IFCROOF"):
            if "IsExternal" not in model.psets(e).get("Pset_RoofCommon", {}):
                w.set_property(e, "Pset_RoofCommon", "IsExternal", Enum("T"), "IFCBOOLEAN")
                kayit(e, "Pset_RoofCommon.IsExternal", None, "TRUE", "Çatı her zaman dış eleman")

    # 7b) R5: giydirme cephe alt elemanları (Allplan'da tiriz/traverse nitelik girilemiyor)
    if A.get("giydirme_cephe"):
        yeni_mat = {}
        def _malz_ekle(e, ad):
            yeni_mat.setdefault(ad, []).append(int(e))
        def _ad_malz(ad):
            u = ascii_tr(ad or "").upper()
            if "ALU" in u:
                return "Alüminyum"
            if "CEL" in u or "STEEL" in u:
                return "Çelik"
            if "AHS" in u or "WOOD" in u:
                return "Ahşap"
            return None
        for r in f.of("IFCRELAGGREGATES"):
            a = f.args(r)
            gc = int(a[4])
            if f.cls(gc) != "IFCCURTAINWALL":
                continue
            gname = model.name(gc)
            gtag = model.attr(gc, "Tag")[0] or _kod_yazisi(model, gc)
            gps = model.psets(gc).get("Pset_CurtainWallCommon", {})
            gdis = gps.get("IsExternal", (None,))[0]
            gmat = model.materials(gc)
            temel = _ad_malz(gname)
            if not gmat and (A.get("gdc_malzeme") or temel):
                _malz_ekle(gc, A.get("gdc_malzeme") or temel + "_Cam")
            sira = 0
            for o in sorted(int(x) for x in a[5]):
                if f.cls(o) != "IFCMEMBER":
                    continue
                sira += 1
                if is_empty(model.attr(o, "Tag")[0]) and gtag:
                    t = "%s_T%02d" % (gtag, sira)
                    w.set_arg(o, 7, t)
                    kayit(o, "Tag", None, t, "Giydirme cephe Kod yazısı + sıra no")
                if "IsExternal" not in model.psets(o).get("Pset_MemberCommon", {}):
                    v = Enum("F") if gdis is False else Enum("T")
                    w.set_property(o, "Pset_MemberCommon", "IsExternal", v, "IFCBOOLEAN")
                    kayit(o, "Pset_MemberCommon.IsExternal", None, "FALSE" if gdis is False else "TRUE",
                          "Bağlı olduğu giydirme cepheden (dış cephe)")
                if not model.materials(o):
                    mt = A.get("gdc_profil_malzeme") or (gmat[0] if gmat else None) or (temel + "_Profil" if temel else None)
                    if mt:
                        _malz_ekle(o, mt)
                    else:
                        U.append("IfcMember #%d (%s): malzeme bulunamadı – Proje Bilgi Formu'nda giydirme cephe profil malzemesini girin" % (o, model.name(o)))
        for ad, els in yeni_mat.items():
            mref = w.add("IFCMATERIAL", [ad, None, None])
            w.add("IFCRELASSOCIATESMATERIAL", [new_guid(), w.owner, None, None, [Ref(e) for e in els], mref])
            for e in els:
                kayit(e, "Malzeme", None, ad, "Giydirme cephe adından (%s)" % ("ALU" if "Alü" in ad else ad))
        model._cw_mat = set(e for els in yeni_mat.values() for e in els)

    # 8) mahal adı ve kaplamaları
    space_storey = {}
    for r in f.of("IFCRELAGGREGATES"):
        a = f.args(r)
        if f.cls(a[4]) == "IFCBUILDINGSTOREY":
            for o in a[5]:
                space_storey[int(o)] = int(a[4])
    for r in f.of("IFCRELCONTAINEDINSPATIALSTRUCTURE"):
        a = f.args(r)
        if f.cls(a[5]) == "IFCBUILDINGSTOREY":
            for o in a[4]:
                space_storey.setdefault(int(o), int(a[5]))

    def kat_kodu(storey):
        if not storey:
            return None
        nm = model.name(storey) or ""
        m = re.search(r"(K\d{2}|B\d{2})\s*$", nm.upper())
        if m:
            return m.group(1)
        m = re.search(r"(K\d{2}|B\d{2})", nm.upper())
        return m.group(1) if m else None

    if A["mahal_no"]:
        for e in f.of("IFCSPACE"):
            nm = model.name(e)
            yeni = mahal_no_duzelt(nm, kat_kodu(space_storey.get(int(e))))
            if yeni:
                w.set_arg(e, 2, yeni)
                kayit(e, "Name", nm, yeni, "Ek-3 mahal no (kat öneki)")
            elif not re.fullmatch(r"(K\d{2}|B\d{2})_[A-ZÇĞİÖŞÜ0-9]{3}_\d{3}", (nm or "").strip()):
                U.append("IfcSpace #%d '%s': mahal numarası otomatik düzeltilemedi (Allplan'da mahal no girin)" % (e, nm))

    if A["mahal_kaplama"]:
        contained = {}
        for r in f.of("IFCRELCONTAINEDINSPATIALSTRUCTURE"):
            a = f.args(r)
            if f.cls(a[5]) == "IFCSPACE":
                contained.setdefault(int(a[5]), []).extend(int(x) for x in a[4])
        for r in f.of("IFCRELCOVERSSPACES"):
            a = f.args(r)
            contained.setdefault(int(a[4]), []).extend(int(x) for x in a[5])
        tur = {"FLOORING": "Floor", "CLADDING": "Wall", "CEILING": "Ceiling"}
        for sp in f.of("IFCSPACE"):
            req = model.psets(sp).get("Pset_SpaceCoveringRequirements", {})
            topla = {}
            for c in contained.get(int(sp), []):
                if f.cls(c) != "IFCCOVERING":
                    continue
                pt = model.attr(c, "PredefinedType")[0]
                if pt not in tur:
                    continue
                mats, kal = _covering_layers(model, c)
                d = topla.setdefault(tur[pt], {"mat": [], "kal": 0.0})
                for mm in mats:
                    if mm not in d["mat"]:
                        d["mat"].append(mm)
                d["kal"] = max(d["kal"], kal)
            for t, d in topla.items():
                if d["mat"] and t + "Covering" not in req:
                    lbl = " + ".join(d["mat"])
                    w.set_property(sp, "Pset_SpaceCoveringRequirements", t + "Covering", lbl, "IFCLABEL")
                    kayit(sp, "Pset_SpaceCoveringRequirements.%sCovering" % t, None, lbl, "Mahaldeki IfcCovering malzemeleri")
                if d["kal"] > 0 and t + "CoveringThickness" not in req:
                    w.set_property(sp, "Pset_SpaceCoveringRequirements", t + "CoveringThickness", round(d["kal"], 4),
                                   "IFCPOSITIVELENGTHMEASURE")
                    kayit(sp, "Pset_SpaceCoveringRequirements.%sCoveringThickness" % t, None, "%.3f m" % d["kal"],
                          "Kaplama katman kalınlıkları toplamı")
            eksik = [t for t in ("Floor", "Wall", "Ceiling") if t not in topla and t + "Covering" not in req]
            if eksik:
                U.append("IfcSpace #%d '%s': %s kaplaması yok – Allplan'da mahal yüzeyi (kaplama) tanımlayın" %
                         (sp, model.name(sp), "/".join({"Floor": "döşeme", "Wall": "duvar", "Ceiling": "tavan"}[x] for x in eksik)))

    # 9) kat bilgileri
    if A["kat_bilgi"]:
        st_area = {}
        for sp, st in space_storey.items():
            if f.cls(sp) != "IFCSPACE":
                continue
            q = model.psets(sp).get("Qto_SpaceBaseQuantities", {})
            v = q.get("NetFloorArea", (None,))[0]
            if not isinstance(v, (int, float)):
                v = geometri(model).get(int(sp), (None,))[0]
            if isinstance(v, (int, float)) and v > 0:
                st_area[st] = st_area.get(st, 0.0) + v
        for st in f.of("IFCBUILDINGSTOREY"):
            ps = model.psets(st)
            el = model.attr(st, "Elevation")[0]
            if "ElevationOfSSLRelative" not in ps.get("Pset_BuildingStoreyCommon", {}) and isinstance(el, (int, float)):
                w.set_property(st, "Pset_BuildingStoreyCommon", "ElevationOfSSLRelative", float(el), "IFCLENGTHMEASURE")
                kayit(st, "Pset_BuildingStoreyCommon.ElevationOfSSLRelative", None, el, "Kat kotu (Elevation)")
            if "NetFloorArea" not in ps.get("Qto_BuildingStoreyBaseQuantities", {}) and st in st_area:
                w.set_quantity(st, "Qto_BuildingStoreyBaseQuantities", "NetFloorArea", round(st_area[st], 3), "IFCQUANTITYAREA")
                kayit(st, "Qto_BuildingStoreyBaseQuantities.NetFloorArea", None, round(st_area[st], 3), "Mahal net alanları toplamı (Qto yoksa mahal geometrisinden)")

    # 10) bina
    if A["bina_bilgi"]:
        storeys = list(f.of("IFCBUILDINGSTOREY"))
        gross = net = 0.0
        for sp in f.of("IFCSPACE"):
            q = model.psets(sp).get("Qto_SpaceBaseQuantities", {})
            g = q.get("GrossFloorArea", (None,))[0]
            n = q.get("NetFloorArea", (None,))[0]
            gross += g if isinstance(g, (int, float)) else 0
            net += n if isinstance(n, (int, float)) else 0
        olc = None
        if A.get("oto_bilgi"):
            try:
                olc = bina_olculeri(model)
            except Exception as ex:
                U.append("Geometriden ölçü hesaplanamadı: %s" % ex)
            if olc:
                if net <= 0:
                    net = olc["net"]
                if gross <= 0:
                    gross = olc["brut"]
        # yalnız katları olan bina(lar)a yaz – kat içermeyen IfcBuilding'ler dışa aktarma hatasıdır
        kat_bina = set()
        for r in f.of("IFCRELAGGREGATES"):
            a = f.args(r)
            if f.cls(a[4]) == "IFCBUILDING" and any(f.cls(o) == "IFCBUILDINGSTOREY" for o in a[5]):
                kat_bina.add(int(a[4]))
        bos_binalar = [b for b in f.of("IFCBUILDING") if int(b) not in kat_bina]
        if kat_bina and bos_binalar:
            U.append("Dosyada katı olmayan %d IfcBuilding var (%s) – Allplan'da bu yapı düzeylerini IFC dışa aktarmaya almayın"
                     % (len(bos_binalar), ", ".join(model.name(b) or "#%d" % b for b in bos_binalar)))
        for b in f.of("IFCBUILDING"):
            ps = model.psets(b)
            bc = ps.get("Pset_BuildingCommon", {})
            if "NumberOfStoreys" not in bc and storeys:
                w.set_property(b, "Pset_BuildingCommon", "NumberOfStoreys", float(len(storeys)), "IFCCOUNTMEASURE")
                kayit(b, "Pset_BuildingCommon.NumberOfStoreys", None, len(storeys), "Kat sayısı")
            qb = ps.get("Qto_BuildingBaseQuantities", {})
            if gross > 0 and "GrossFloorArea" not in qb:
                w.set_quantity(b, "Qto_BuildingBaseQuantities", "GrossFloorArea", round(gross, 3), "IFCQUANTITYAREA")
                kayit(b, "Qto_BuildingBaseQuantities.GrossFloorArea", None, round(gross, 3), "Mahal brüt alanları toplamı")
            if net > 0 and "NetFloorArea" not in qb:
                w.set_quantity(b, "Qto_BuildingBaseQuantities", "NetFloorArea", round(net, 3), "IFCQUANTITYAREA")
                kayit(b, "Qto_BuildingBaseQuantities.NetFloorArea", None, round(net, 3), "Mahal net alanları toplamı")
            if olc and (int(b) in kat_bina or not kat_bina):
                bc2 = bc
                yaz = [("Qto_BuildingBaseQuantities", "FootPrintArea", olc["taban"], "IFCQUANTITYAREA", "Taban alanı (zemin kat döşemesi, geometriden – yaklaşık)"),
                       ("Qto_BuildingBaseQuantities", "Height", olc["yukseklik"], "IFCQUANTITYLENGTH", "±0.00'dan en üst noktaya (geometriden)"),
                       ("Qto_BuildingBaseQuantities", "EavesHeight", olc["sacak"], "IFCQUANTITYLENGTH", "±0.00'dan en üst döşeme/çatı üstüne (geometriden)")]
                for ps_, pr, v, qc, ac in yaz:
                    if v and pr not in qb:
                        w.set_quantity(b, ps_, pr, v, qc)
                        kayit(b, ps_ + "." + pr, None, v, ac)
                for pr, v, ac in (("GrossPlannedArea", gross, "Brüt alan (geometriden – yaklaşık; formda kesin değeri girin)"),
                                  ("NetPlannedArea", net, "Net alan (mahallerden)")):
                    if v and v > 0 and pr not in bc2:
                        w.set_property(b, "Pset_BuildingCommon", pr, round(v, 2), "IFCAREAMEASURE")
                        kayit(b, "Pset_BuildingCommon." + pr, None, round(v, 2), ac)
                if "ConstructionMethod" not in bc2:
                    ym = _yapim_teknigi(model)
                    if ym:
                        w.set_property(b, "Pset_BuildingCommon", "ConstructionMethod", ym, "IFCLABEL")
                        kayit(b, "Pset_BuildingCommon.ConstructionMethod", None, ym, "Taşıyıcı eleman malzemelerinden")
                if "OccupancyType" not in bc2:
                    ku = _kullanim(model)
                    if ku:
                        w.set_property(b, "Pset_BuildingCommon", "OccupancyType", ku, "IFCLABEL")
                        kayit(b, "Pset_BuildingCommon.OccupancyType", None, ku, "Mahal/zon adlarından")
                if "FireProtectionClass" not in bc2 and olc.get("yukseklik"):
                    yk = "Yüksek_Bina" if olc["yukseklik"] > 21.5 else "Düşük_Bina"
                    w.set_property(b, "Pset_BuildingCommon", "FireProtectionClass", yk, "IFCLABEL")
                    kayit(b, "Pset_BuildingCommon.FireProtectionClass", None, yk,
                          "Bina yüksekliğinden (Yangın Yönetmeliği 21,50 m sınırı) – formda kesinleştirin")
                if "BuildingID" not in bc2:
                    _nm = model.name(b) or ""
                    bid = A.get("bina_adi") or (_nm if re.fullmatch(r"[A-Z]{2}-BNA-[^-]+", _nm) else
                                                "%s-BNA-%s" % (A["disiplin"], aciklama_temizle(_nm) or "BINA"))
                    w.set_property(b, "Pset_BuildingCommon", "BuildingID", bid, "IFCIDENTIFIER")
                    w.set_property(b, "Pset_BuildingCommon", "IsPermanentID", Enum("F"), "IFCBOOLEAN")
                    kayit(b, "Pset_BuildingCommon.BuildingID", None, bid, "Bina adı (geçici kimlik; resmî yapı kimlik no formdan girilir)")
            nm = model.name(b)
            if A.get("bina_adi"):
                if nm != A["bina_adi"]:
                    w.set_arg(b, 2, A["bina_adi"])
                    kayit(b, "Name", nm, A["bina_adi"], "Palet: bina adı")
            elif not re.fullmatch(r"[A-Z]{2}-BNA-[^-]+", nm or ""):
                yeni = "%s-BNA-%s" % (A["disiplin"], aciklama_temizle(nm) or "BINA")
                w.set_arg(b, 2, yeni)
                kayit(b, "Name", nm, yeni, "Ek-5 ad biçimi (bina adını palette kesinleştirin)")
            if is_empty(model.attr(b, "LongName")[0]):
                ln = A.get("bina_uzun_ad") or ("Bina " + (nm or "")).strip()
                w.set_arg(b, 7, ln)
                kayit(b, "LongName", None, ln, "Palet / eski ad")
        for s in f.of("IFCSITE"):
            nm = model.name(s)
            if not re.fullmatch(r"[A-Z]{2}-SAH-[^-]+", nm or ""):
                yeni = "%s-SAH-%s" % (A["disiplin"], aciklama_temizle(re.sub(r"\s+", "", nm or "")) or "SAHA")
                w.set_arg(s, 2, yeni)
                kayit(s, "Name", nm, yeni, "Ek-5 ad biçimi")
                if is_empty(model.attr(s, "LongName")[0]) and nm:
                    w.set_arg(s, 7, nm)
                    kayit(s, "LongName", None, nm, "Eski ad")
        if A.get("oto_bilgi"):
            ku = _kullanim(model)
            for s in f.of("IFCSITE"):
                metin = " ".join(str(x or "") for x in (model.name(s), model.attr(s, "LongName")[0]))
                mm = re.search(r"ADA\s*[_:\-]?\s*(\d+)\D{0,12}?PARSEL\s*[_:\-]?\s*(\d+)", ascii_tr(metin).upper())
                lr = model.psets(s).get("Pset_LandRegistration", {})
                if mm and "LandID" not in lr:
                    lid = "%s/%s" % (mm.group(1), mm.group(2))
                    w.set_property(s, "Pset_LandRegistration", "LandID", lid, "IFCIDENTIFIER")
                    kayit(s, "Pset_LandRegistration.LandID", None, lid, "Arsa adından (Ada/Parsel)")
                if is_empty(model.attr(s, "ObjectType")[0]):
                    w.set_arg(s, 4, "Parsel")
                    kayit(s, "ObjectType", None, "Parsel", "Varsayılan")
            for p in f.of("IFCPROJECT"):
                if is_empty(model.attr(p, "Description")[0]):
                    arsa = [model.attr(s, "LongName")[0] or model.name(s) for s in f.of("IFCSITE")]
                    d = ("%s %s Projesi" % (arsa[0] if arsa else "", ku or "")).strip()
                    d = re.sub(r"\s+", " ", d)
                    w.set_arg(p, 3, d)
                    kayit(p, "Description", None, d, "Arsa adı + kullanım")
        if A.get("proje_adi"):
            for p in f.of("IFCPROJECT"):
                nm = model.name(p)
                if nm != A["proje_adi"]:
                    w.set_arg(p, 2, A["proje_adi"])
                    kayit(p, "Name", nm, A["proje_adi"], "Palet: proje kodu")

    # 11) adres
    if A["adres"]:
        for cls, ai in (("IFCSITE", 13), ("IFCBUILDING", 11)):
            for s in f.of(cls):
                a = f.args(s)
                adr = a[ai] if len(a) > ai else None
                if not isinstance(adr, Ref):
                    adrs = list(f.of("IFCPOSTALADDRESS"))
                    adr = Ref(adrs[0]) if adrs else None
                if adr is None:
                    continue
                pa = f.args(adr)
                vals = {"AddressLines": "; ".join(pa[4]) if isinstance(pa[4], list) else pa[4],
                        "PostalBox": pa[5], "Town": pa[6], "Region": pa[7], "PostalCode": pa[8], "Country": pa[9]}
                cur = model.psets(s).get("Pset_Address", {})
                for k in ("AddressLines", "PostalBox", "Town", "Region", "PostalCode", "Country"):
                    v = vals[k]
                    if not is_empty(v) and k not in cur:
                        w.set_property(s, "Pset_Address", k, str(v), "IFCLABEL")
                        kayit(s, "Pset_Address." + k, None, v, "IfcPostalAddress")

    # 12) zon
    if A["zon"]:
        for z in f.of("IFCZONE"):
            nm = model.name(z) or ""
            if not re.fullmatch(r"[A-Z]{2}-ZON-[^-]+", nm):
                yeni = "%s-ZON-%s" % (A["disiplin"], aciklama_temizle(nm) or "ZON")
                w.set_arg(z, 2, yeni)
                kayit(z, "Name", nm, yeni, "Ek-5 ad biçimi")
            m = re.fullmatch(r"D(\d{2})", nm.strip().upper())
            uzun = ("Daire %s" % m.group(1)) if m else ZON_LONG.get(nm.strip().upper(), nm)
            tip = "Daire" if m else (ZON_LONG.get(nm.strip().upper(), "Bölüm"))
            if is_empty(model.attr(z, "LongName")[0]):
                w.set_arg(z, 5, uzun)
                kayit(z, "LongName", None, uzun, "Zon kodu")
            if is_empty(model.attr(z, "ObjectType")[0]):
                w.set_arg(z, 4, tip)
                kayit(z, "ObjectType", None, tip, "Zon kodu")

    # 12b) mevcut IfcActorRole: Description (ve USERDEFINED'da UserDefinedRole) boşsa doldur
    for ar in f.of("IFCACTORROLE"):
        a = f.args(ar)
        rol = str(a[0]) if a[0] is not None else ""
        if is_empty(a[2] if len(a) > 2 else None):
            d = (a[1] if rol == "USERDEFINED" and a[1] else ROL_TR.get(rol, rol.capitalize())) or "Rol"
            w.set_arg(ar, 2, d)
            D.append(Duzeltme("IFCACTORROLE", int(ar), rol, "Description", None, d, "IDS: IfcActorRole açıklaması"))
        if rol == "USERDEFINED" and is_empty(a[1]):
            U.append("IfcActorRole #%d: USERDEFINED rolün adı (UserDefinedRole) boş" % ar)

    # 13) kullanıcı varsayılanları (yalnız eksikse)
    crs = {}
    mapc = {}
    vlist = list(A.get("varsayilanlar") or [])
    if A.get("oto_bilgi"):
        # R5: düşük öncelikli otomatik değerler (listenin sonunda: kullanıcı/form değerleri önce yazılır)
        rol = {"MM": "ARCHITECT", "ST": "STRUCTURALENGINEER", "MK": "MECHANICALENGINEER",
               "EE": "ELECTRICALENGINEER", "PY": "LANDSCAPEARCHITECT", "HR": "CIVILENGINEER"}.get(A.get("disiplin", "MM"))
        if rol:
            vlist += [("IFCPERSON", "Roles", rol, None), ("IFCORGANIZATION", "Roles", rol, None)]
        if list(f.of("IFCPOSTALADDRESS")):
            vlist.append(("IFCORGANIZATION", "Addresses", "POSTA", None))
    for v_ in vlist:
        sinif, hedef, deger, tip = v_[:4]
        zorla = len(v_) > 4 and v_[4]
        sinif = sinif.upper()
        if sinif == "IFCPROJECTEDCRS":
            crs[hedef] = deger
            continue
        if sinif == "IFCMAPCONVERSION":
            mapc[hedef] = deger
            continue
        hedefler = list(f.of(sinif))
        if sinif == "IFCGEOMETRICREPRESENTATIONCONTEXT":
            hedefler = [x for x in hedefler if f.cls(x) == sinif]
        if hedef.lower() in ("malzeme", "material"):
            atanmis = getattr(model, "_cw_mat", set())
            eksik = [e for e in hedefler if not model.materials(e) and int(e) not in atanmis]
            if eksik:
                mat = w.add("IFCMATERIAL", [str(deger), None, None])
                w.add("IFCRELASSOCIATESMATERIAL", [new_guid(), w.owner, None, None, [Ref(e) for e in eksik], mat])
                for e in eksik:
                    kayit(e, "Malzeme", None, deger, "Varsayılan değer dosyası")
            continue
        sayac = 0
        for e in hedefler:
            if "{#}" in str(deger):
                sayac += 1
                deger_e = str(deger).replace("{#}", "%02d" % sayac)
            else:
                deger_e = deger
            if "." in hedef:
                ps_, pr = hedef.split(".", 1)
                cur = model.psets(e).get(ps_, {})
                if pr in cur and not is_empty(cur[pr][0]) and not zorla:
                    continue
                if ps_.startswith("Qto_"):
                    qcls = {"IFCAREAMEASURE": "IFCQUANTITYAREA", "IFCLENGTHMEASURE": "IFCQUANTITYLENGTH",
                            "IFCVOLUMEMEASURE": "IFCQUANTITYVOLUME"}.get(tip, "IFCQUANTITYLENGTH")
                    w.set_quantity(e, ps_, pr, _cast(deger_e, "IFCREAL"), qcls)
                else:
                    w.set_property(e, ps_, pr, _cast(deger_e, tip), tip or "IFCLABEL")
                kayit(e, hedef, None, deger_e, "Varsayılan değer dosyası")
                continue
            i = idx(sinif, hedef)
            if i is None:
                U.append("Varsayılan: %s sınıfında '%s' niteliği yok" % (sinif, hedef))
                continue
            cur = w.args(e)[i] if i < len(w.args(e)) else None
            if not is_empty(cur) and not zorla and not (hedef == "Name" and sinif in ("IFCPROJECT", "IFCBUILDING")):
                continue
            if hedef == "Roles":
                roller = []
                for r in str(deger_e).split(","):
                    r = r.strip()
                    if not r:
                        continue
                    ru = r.upper()
                    # IDS: IfcActorRole Description zorunlu; USERDEFINED'da UserDefinedRole da
                    if ru in ROL_ENUM:
                        roller.append(w.add("IFCACTORROLE", [Enum(ru), None, ROL_TR.get(ru, r)]))
                    else:
                        roller.append(w.add("IFCACTORROLE", [Enum("USERDEFINED"), r, r]))
                val = roller
            elif hedef == "Addresses":
                adrs = list(f.of("IFCPOSTALADDRESS"))
                if not adrs:
                    U.append("Varsayılan: IfcPostalAddress yok, Addresses yazılamadı")
                    continue
                val = [Ref(adrs[0])]
            elif hedef == "TrueNorth":
                xy = [float(x) for x in str(deger_e).replace(";", ",").split(",")[:2]]
                val = w.add("IFCDIRECTION", [xy])
            else:
                val = _cast(deger_e, tip) if tip else deger_e
            w.set_arg(e, i, val)
            kayit(e, hedef, cur if not isinstance(cur, Ref) else None, deger_e, "Varsayılan değer dosyası")
    if crs.get("Name") and not list(f.of("IFCPROJECTEDCRS")):
        units = [u for u in f.of("IFCSIUNIT") if f.args(u)[1] == "LENGTHUNIT"]
        crs_ref = w.add("IFCPROJECTEDCRS", [crs.get("Name"), crs.get("Description"), crs.get("GeodeticDatum"),
                                            crs.get("VerticalDatum"), crs.get("MapProjection"), crs.get("MapZone"),
                                            Ref(units[0]) if units else None])
        kayit(int(crs_ref), "IfcProjectedCRS", None, crs.get("Name"), "Varsayılan değer dosyası")
        ctx = [c for c in f.of("IFCGEOMETRICREPRESENTATIONCONTEXT")]
        if ctx and mapc.get("Eastings") not in (None, "") and mapc.get("Northings") not in (None, ""):
            g = lambda k, d=0.0: _cast(mapc.get(k, d), "IFCREAL")
            mref = w.add("IFCMAPCONVERSION", [Ref(ctx[0]), crs_ref, g("Eastings"), g("Northings"), g("OrthogonalHeight"),
                                              g("XAxisAbscissa", 1.0), g("XAxisOrdinate", 0.0), g("Scale", 1.0)])
            kayit(int(mref), "IfcMapConversion", None, "E=%s N=%s" % (mapc.get("Eastings"), mapc.get("Northings")),
                  "Varsayılan değer dosyası")
    elif mapc and not crs.get("Name"):
        U.append("IfcMapConversion için önce IfcProjectedCRS; Name girilmeli")
    return w, D, U


def _cast(v, tip):
    t = (tip or "").upper()
    if t == "IFCBOOLEAN":
        return Enum("T" if str(v).strip().upper() in ("1", "TRUE", "EVET", "T", "E", "YES") else "F")
    if t in ("IFCREAL", "IFCAREAMEASURE", "IFCLENGTHMEASURE", "IFCPOSITIVELENGTHMEASURE", "IFCPOSITIVERATIOMEASURE",
             "IFCCOUNTMEASURE", "IFCVOLUMEMEASURE", "IFCRATIOMEASURE"):
        return float(str(v).replace(",", "."))
    if t == "IFCINTEGER":
        return int(v)
    return str(v)


def _covering_layers(model, c):
    """(malzeme adları, toplam kalınlık m)"""
    f = model.f
    mats = []
    kal = 0.0
    for r in model._mats_rel_for(c) if hasattr(model, "_mats_rel_for") else []:
        pass
    if not hasattr(model, "_cov_mat"):
        model._cov_mat = {}
        for r in f.of("IFCRELASSOCIATESMATERIAL"):
            a = f.args(r)
            for o in a[4]:
                model._cov_mat[int(o)] = a[5]
    mid = model._cov_mat.get(int(c))
    if mid is not None:
        cls = f.cls(mid)
        ls = None
        if cls == "IFCMATERIALLAYERSETUSAGE":
            ls = f.args(mid)[0]
        elif cls == "IFCMATERIALLAYERSET":
            ls = mid
        if ls is not None:
            for l in f.args(ls)[0] or []:
                la = f.args(l)
                if la[0] is not None:
                    mats.append(f.args(la[0])[0])
                if isinstance(la[1], (int, float)):
                    kal += la[1]
        else:
            mats = model.materials(c)
    if kal <= 0:
        v = _allplan_attr(model, c, "Katman_Kalınlığı")
        if isinstance(v, (int, float)):
            kal = v
    return [m for m in mats if m], kal
