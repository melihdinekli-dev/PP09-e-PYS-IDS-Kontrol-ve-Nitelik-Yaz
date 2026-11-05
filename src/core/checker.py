# -*- coding: utf-8 -*-
"""IDS denetimi (gömülü e-PYS kuralları). ALUPLAN – PP09."""
import re
from ifc_model import IfcModel, is_empty
from ifc_step import Ref

_PCLASS = {
    "Lu": "A-ZÀ-ÖØ-ÞĀĂĄĆĈĊČĎĐĒĔĖĘĚĜĞĠĢĤĦĨĪĬĮİĲĴĶĹĻĽĿŁŃŅŇŊŌŎŐŒŔŖŘŚŜŞŠŢŤŦŨŪŬŮŰŲŴŶŸŹŻŽ",
    "Ll": "a-zß-öø-ÿāăąćĉċčďđēĕėęěĝğġģĥħĩīĭįıĳĵķĺļľŀłńņňŋōŏőœŕŗřśŝşšţťŧũūŭůűųŵŷźżž",
    "L": "A-Za-zÀ-ÖØ-öø-ɏͰ-ϿЀ-ӿ",
    "N": "0-9²³¹¼-¾",
    "Nd": "0-9",
    "P": "!\"#%&'()*,\\-./:;?@\\[\\\\\\]_{}¡§«¶·»¿",
    "S": "$+<=>\\^`|~¢-¦¨©¬®-±´×÷",
    "Z": "  ",
}


def xsd_to_py(p):
    """XSD desenini Python'a çevirir (tam eşleşme; \\p{..} sınıfları dahil)."""
    out = []
    i = 0
    n = len(p)
    in_cls = False
    while i < n:
        c = p[i]
        if c == "\\" and i + 1 < n and p[i + 1] in "pP" and i + 2 < n and p[i + 2] == "{":
            j = p.index("}", i)
            name = p[i + 3:j]
            body = _PCLASS.get(name, _PCLASS.get(name[:1], "\\w"))
            neg = p[i + 1] == "P"
            if in_cls:
                out.append(body)          # [^..] içinde \P desteklenmez; yaklaşık
            else:
                out.append("[%s%s]" % ("^" if neg else "", body))
            i = j + 1
            continue
        if c == "\\" and i + 1 < n:
            out.append(p[i:i + 2])
            i += 2
            continue
        if c == "[" and not in_cls:
            in_cls = True
        elif c == "]" and in_cls:
            in_cls = False
        out.append(c)
        i += 1
    return re.compile("".join(out), re.S)


_RX = {}


def rx(p):
    r = _RX.get(p)
    if r is None:
        r = _RX[p] = xsd_to_py(p)
    return r


def match(p, v):
    if v is None:
        return False
    return rx(p).fullmatch(str(v)) is not None


QTO_TYPES = {"IFCQUANTITYLENGTH": "IFCLENGTHMEASURE", "IFCQUANTITYAREA": "IFCAREAMEASURE",
             "IFCQUANTITYVOLUME": "IFCVOLUMEMEASURE", "IFCQUANTITYCOUNT": "IFCCOUNTMEASURE",
             "IFCQUANTITYWEIGHT": "IFCMASSMEASURE", "IFCQUANTITYTIME": "IFCTIMEMEASURE"}

# IDS'te bilinen hata: duvar ad deseninde '+' eksik
IDS_DUZELTMELERI = {"(MM|IM|PY|AL|ST|ZE)-DVR-[^-]": "(MM|IM|PY|AL|ST|ZE)-DVR-[^-]+"}


def _fmt(v):
    if v is None:
        return "(boş)"
    if v is True:
        return "TRUE"
    if v is False:
        return "FALSE"
    if isinstance(v, float):
        return ("%.4f" % v).rstrip("0").rstrip(".")
    if isinstance(v, list):
        return ", ".join(_fmt(x) for x in v)
    return str(v)


class Sonuc(object):
    """Bir eleman × gereksinim sonucu"""
    __slots__ = ("kural", "sinif", "eid", "ad", "gereksinim", "bulunan", "beklenen", "gecti", "not_")

    def __init__(self, kural, sinif, eid, ad, gereksinim, bulunan, beklenen, gecti, not_=""):
        self.kural, self.sinif, self.eid, self.ad = kural, sinif, eid, ad
        self.gereksinim, self.bulunan, self.beklenen, self.gecti, self.not_ = gereksinim, bulunan, beklenen, gecti, not_


def beklenen_metni(g):
    p = []
    if g.get("desen"):
        p.append("Desen: " + g["desen"])
    if g.get("secenek"):
        p.append("Şunlardan biri: " + " | ".join(g["secenek"]))
    if g.get("tur") == "parca":
        p.append("%s ile bir %s'e bağlı olmalı" % (g.get("iliski", ""), g.get("varlik", "")))
    if g.get("card") == "prohibited":
        p.append("Bulunmamalı")
    if g.get("tip"):
        p.append("Veri tipi: " + g["tip"])
    if not p:
        p.append("Dolu olmalı")
    return " · ".join(p)


def gereksinim_adi(g):
    if g["tur"] == "nitelik":
        return g["ad"]
    if g["tur"] == "ozellik":
        return g["pset"] + "." + g["ad"]
    if g["tur"] == "parca":
        return "partOf " + (g.get("varlik") or "")
    return "Malzeme"


def _str(v):
    if v is True:
        return "TRUE"
    if v is False:
        return "FALSE"
    if isinstance(v, float) and v == int(v):
        return repr(v)
    return str(v)


def kosul_uyar(k, v):
    """IDS değer kısıtı. k None ise her dolu değer uyar."""
    if not k:
        return True
    if isinstance(v, list):
        return any(kosul_uyar(k, x) for x in v)
    sv = _str(v)
    if "basit" in k:
        b = k["basit"]
        if sv == b:
            return True
        try:
            return float(sv) == float(b)
        except (TypeError, ValueError):
            return False
    if k.get("secenek") and sv not in k["secenek"]:
        return False
    if k.get("desen") and not any(match(p, sv) for p in k["desen"]):
        return False
    for kk, op in (("minInclusive", lambda a, b: a >= b), ("maxInclusive", lambda a, b: a <= b),
                   ("minExclusive", lambda a, b: a > b), ("maxExclusive", lambda a, b: a < b)):
        if kk in k:
            try:
                if not op(float(v), float(k[kk])):
                    return False
            except (TypeError, ValueError):
                return False
    for kk, op in (("length", lambda a, b: a == b), ("minLength", lambda a, b: a >= b), ("maxLength", lambda a, b: a <= b)):
        if kk in k and not op(len(sv), int(k[kk])):
            return False
    return True


def _kosul(g):
    k = g.get("kosul")
    if k is None and (g.get("desen") or g.get("secenek")):
        k = {}
        if g.get("desen"):
            k["desen"] = [g["desen"]]
        if g.get("secenek"):
            k["secenek"] = g["secenek"]
    return k


def _bul(model, eid, g, cache):
    """(var_mı, değer, uygun_mu) – kart. hariç ham sonuç"""
    t = g["tur"]
    k = _kosul(g)
    if t == "nitelik":
        v, ok = model.attr(eid, g["ad"])
        if isinstance(v, Ref):
            return True, "#%d" % int(v), k is None
        if not ok or is_empty(v):
            return False, None, False
        return True, v, kosul_uyar(k, v)
    if t == "ozellik":
        ps = cache.get(eid)
        if ps is None:
            ps = cache[eid] = model.psets(eid)
        props = ps.get(g["pset"])
        if props is None or g["ad"] not in props:
            return False, None, False
        v, typ = props[g["ad"]]
        if is_empty(v):
            return False, None, False
        if g.get("tip"):
            tt = (typ or "").upper()
            tt = QTO_TYPES.get(tt, tt)
            if tt and tt != g["tip"]:
                return True, "%s (%s)" % (_fmt(v), tt), False
        return True, v, kosul_uyar(k, v)
    if t == "malzeme":
        mats = model.materials(eid)
        if not mats:
            return False, None, False
        return True, ", ".join(mats[:4]), (not k) or any(kosul_uyar(k, m) for m in mats)
    if t == "parca":
        grp = model.gruplar(eid) if hasattr(model, "gruplar") else []
        hedef = (g.get("varlik") or "").upper()
        uy = [c for c in grp if not hedef or c == hedef]
        return bool(grp), ", ".join(grp) or None, bool(uy)
    return True, None, True


def check_req(model, eid, g, cache):
    """(geçti, bulunan) döndürür – IDS kardinalitesine göre."""
    var, v, uy = _bul(model, eid, g, cache)
    card = g.get("card", "required" if g.get("zorunlu", True) else "optional")
    if card == "prohibited":
        return (not var or (_kosul(g) is not None and not uy)), v
    if card == "optional":
        return (not var) or uy, v
    return var and uy, v


def uygulanir(model, eid, k, cache):
    if k.get("ad_deseni") and not match(k["ad_deseni"], model.name(eid)):
        return False
    pd = k.get("predef")
    if pd:
        pt = model.attr(eid, "PredefinedType")[0]
        if pt == "USERDEFINED":
            pt = model.attr(eid, "ObjectType")[0]
        if pt is None or not kosul_uyar(pd, pt):
            return False
    for g in k.get("uyg_kosullar") or []:
        var, v, uy = _bul(model, eid, g, cache)
        if not (var and uy):
            return False
    return True


def _norm_qto_types(model):
    pass


def denetle(model, kurallar, ids_duzelt=True, ek5=None):
    """Tüm kuralları uygular. (ozet listesi, sonuç listesi) döndürür."""
    ozet = []
    sonuclar = []
    cache = {}
    for k in kurallar:
        siniflar = k["siniflar"]
        eids = []
        for s in siniflar:
            eids.extend(model.f.of(s))
        if k.get("ad_deseni") or k.get("predef") or k.get("uyg_kosullar"):
            eids = [e for e in eids if uygulanir(model, e, k, cache)]
        o = {"kural": k["ad"], "sinif": siniflar[0], "eleman": len(eids), "gecen": 0, "kismi": 0, "kalan": 0,
             "kontrol": 0, "kontrol_gecen": 0, "durum": "", "ids_hatasi": False}
        if not eids:
            if k.get("zorunlu_varlik"):
                o["durum"] = "Kaldı"
                sonuclar.append(Sonuc(k["ad"], siniflar[0], None, "", "(sınıf)", None,
                                      "Modelde en az 1 adet olmalı", False, "Modelde bu sınıf yok"))
            else:
                o["durum"] = "Uygulanmadı"
            ozet.append(o)
            continue
        for e in eids:
            nad = model.name(e)
            ok_say = 0
            n_req = 0
            for g in k["gereksinimler"]:
                gg = g
                ids_h = False
                if ids_duzelt and g.get("desen") in IDS_DUZELTMELERI:
                    gg = dict(g)
                    gg["desen"] = IDS_DUZELTMELERI[g["desen"]]
                    ids_h = True
                    o["ids_hatasi"] = True
                gecti, bul = check_req(model, e, gg, cache)
                n_req += 1
                o["kontrol"] += 1
                if gecti:
                    ok_say += 1
                    o["kontrol_gecen"] += 1
                    if ids_h:
                        gecti_orj, _ = check_req(model, e, g, cache)
                        if not gecti_orj:
                            sonuclar.append(Sonuc(k["ad"], siniflar[0], e, nad, gereksinim_adi(g), _fmt(bul),
                                                  beklenen_metni(g), True,
                                                  "IDS HATASI: IDS deseni '+' eksik; ad doğru, IDS'in kendi deseniyle kalır"))
                else:
                    sonuclar.append(Sonuc(k["ad"], siniflar[0], e, nad, gereksinim_adi(g), _fmt(bul),
                                          beklenen_metni(g), False))
            if ok_say == n_req:
                o["gecen"] += 1
            elif ok_say > 0:
                o["kismi"] += 1
            else:
                o["kalan"] += 1
        o["durum"] = "Geçti" if o["gecen"] == o["eleman"] else "Kaldı"
        ozet.append(o)
    # EK-5 ad kodları: modelde olup kuralı olmayan sınıflar (isteğe bağlı sınıflar)
    if ek5:
        kurallı = set(s for k in kurallar for s in k["siniflar"])
        for cls, kod, desen, kad in ek5:
            if cls in kurallı:
                continue
            eids = list(model.f.of(cls))
            if not eids:
                continue
            o = {"kural": "EK-5 ad kodu – " + cls, "sinif": cls, "eleman": len(eids),
                 "gecen": 0, "kismi": 0, "kalan": 0, "kontrol": 0, "kontrol_gecen": 0, "durum": "", "ids_hatasi": False,
                 "bilgi": True}
            for e in eids:
                nad = model.name(e)
                o["kontrol"] += 1
                if match(desen, nad):
                    o["gecen"] += 1
                    o["kontrol_gecen"] += 1
                else:
                    o["kalan"] += 1
                    sonuclar.append(Sonuc(o["kural"], cls, e, nad, "Name", _fmt(nad), "Desen: " + desen, False,
                                          "Bilgi: IDS bu sınıf için ayrıca kural içerebilir"))
            o["durum"] = "Geçti" if o["kalan"] == 0 else "Kaldı"
            ozet.append(o)
    return ozet, sonuclar
