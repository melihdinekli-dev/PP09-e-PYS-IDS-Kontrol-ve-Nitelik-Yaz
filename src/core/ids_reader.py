# -*- coding: utf-8 -*-
"""IDS 1.0 (.ids) okuyucu -> PP09 kural yapısı. ALUPLAN – PP09."""
import xml.etree.ElementTree as ET

_NS_IDS = "http://standards.buildingsmart.org/IDS"
_NS_XS = "http://www.w3.org/2001/XMLSchema"


def _t(e, name):
    return e.find("{%s}%s" % (_NS_IDS, name))


def _deger(e):
    """<ids:name>/<ids:value> gibi bir öğeden kısıt: {'basit': str} ya da {'desen': [...], 'secenek': [...], ...}"""
    if e is None:
        return None
    sv = _t(e, "simpleValue")
    if sv is not None:
        return {"basit": (sv.text or "").strip()}
    r = e.find("{%s}restriction" % _NS_XS)
    if r is None:
        return None
    k = {}
    for c in r:
        tag = c.tag.split("}")[1]
        v = c.attrib.get("value")
        if tag == "pattern":
            k.setdefault("desen", []).append(v)
        elif tag == "enumeration":
            k.setdefault("secenek", []).append(v)
        elif tag in ("minInclusive", "maxInclusive", "minExclusive", "maxExclusive", "length", "minLength", "maxLength"):
            k[tag] = v
    return k or None


def _ad(e):
    d = _deger(_t(e, "name")) if e is not None else None
    return d.get("basit") if d and "basit" in d else None


def _facet(f, uygulanabilirlik=False):
    tag = f.tag.split("}")[1]
    card = f.attrib.get("cardinality", "required")
    g = {"card": card, "zorunlu": card == "required"}
    if f.attrib.get("instructions"):
        g["aciklama"] = f.attrib["instructions"]
    if tag == "attribute":
        g["tur"] = "nitelik"
        g["ad"] = _ad(f)
        g["kosul"] = _deger(_t(f, "value"))
    elif tag == "property":
        g["tur"] = "ozellik"
        g["pset"] = (_deger(_t(f, "propertySet")) or {}).get("basit")
        g["ad"] = (_deger(_t(f, "baseName")) or {}).get("basit")
        if f.attrib.get("dataType"):
            g["tip"] = f.attrib["dataType"].upper()
        g["kosul"] = _deger(_t(f, "value"))
    elif tag == "material":
        g["tur"] = "malzeme"
        g["kosul"] = _deger(_t(f, "value"))
    elif tag == "partOf":
        g["tur"] = "parca"
        g["iliski"] = f.attrib.get("relation", "")
        ent = _t(f, "entity")
        g["varlik"] = _ad(ent)
    elif tag == "classification":
        g["tur"] = "sinif"
        g["sistem"] = _deger(_t(f, "system"))
        g["kosul"] = _deger(_t(f, "value"))
    elif tag == "entity":
        g["tur"] = "varlik"
        g["ad"] = _ad(f)
        g["kosul"] = _deger(_t(f, "predefinedType"))
    else:
        g["tur"] = tag
    # eski alan adlarıyla uyum
    k = g.get("kosul") or {}
    if k.get("desen"):
        g["desen"] = k["desen"][0] if len(k["desen"]) == 1 else "|".join("(?:%s)" % p for p in k["desen"])
    if k.get("secenek"):
        g["secenek"] = k["secenek"]
    if k.get("basit") is not None:
        g["secenek"] = [k["basit"]]
    return g


def ids_oku(path):
    """(bilgi, kurallar) döndürür."""
    root = ET.parse(path).getroot()
    info = _t(root, "info")
    bilgi = {}
    if info is not None:
        for c in info:
            bilgi[c.tag.split("}")[1]] = (c.text or "").strip()
    kurallar = []
    for s in root.iter("{%s}specification" % _NS_IDS):
        ap = _t(s, "applicability")
        k = {"ad": s.attrib.get("name", "").strip(), "aciklama": s.attrib.get("description", ""),
             "ifc": s.attrib.get("ifcVersion", ""), "siniflar": [], "predef": None, "ad_deseni": None,
             "uyg_kosullar": [], "zorunlu_varlik": False, "gereksinimler": []}
        if ap is not None:
            k["zorunlu_varlik"] = int(ap.attrib.get("minOccurs", "0") or 0) >= 1
            for f in ap:
                g = _facet(f, True)
                if g["tur"] == "varlik":
                    if g.get("ad"):
                        k["siniflar"].append(g["ad"].upper())
                    if g.get("kosul"):
                        k["predef"] = g["kosul"]
                elif g["tur"] == "nitelik" and g.get("ad") == "Name" and g.get("desen"):
                    k["ad_deseni"] = g["desen"]
                else:
                    k["uyg_kosullar"].append(g)
        rq = _t(s, "requirements")
        if rq is not None:
            for f in rq:
                k["gereksinimler"].append(_facet(f))
        kurallar.append(k)
    return bilgi, kurallar
