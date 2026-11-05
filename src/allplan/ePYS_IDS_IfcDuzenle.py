# -*- coding: utf-8 -*-
"""
e-PYS IFC Düzenleyici – çekirdek modül (ALUPLAN)

Allplan'ın IFC dışa aktarımında "AllplanAttributes" property set'ine düşen
nitelikleri, IFC'nin kendi öznitelik alanlarına (Name, Description,
ObjectType, Tag, LongName) ya da istenen adlı bir Pset'e taşır.
İstenirse taşınan nitelikleri AllplanAttributes'tan siler.

Dış kütüphane gerektirmez. Hem Allplan PythonPart'ı (EPYS_IfcDuzenle.py)
tarafından hem de komut satırından kullanılabilir:

    python EPYS_IfcDuzenle_core.py model.ifc --map eslestirme.txt
    python EPYS_IfcDuzenle_core.py model.ifc --analiz

Eşleştirme satırı biçimi (her satır bir kural, # ile başlayan satır yorumdur):

    KaynakNitelik -> Hedef
    IfcSinifi[,IfcSinifi2]: KaynakNitelik -> Hedef

Hedef:  Name | Description | ObjectType | Tag | LongName
        ya da  PsetAdi.OzellikAdi   (örn. ePYS.Mahal_No)
        ya da  PsetAdi.             (özellik adı kaynakla aynı kalır)
"""

import csv
import datetime
import os
import re
import uuid
from collections import Counter, OrderedDict

# --------------------------------------------------------------------------
# IFC şema bilgileri (IFC2x3 ve IFC4'te aynı konumlar)
# --------------------------------------------------------------------------

ENTITY_TARGETS = OrderedDict([
    ("NAME", "Name"),
    ("DESCRIPTION", "Description"),
    ("OBJECTTYPE", "ObjectType"),
    ("TAG", "Tag"),
    ("LONGNAME", "LongName"),
])

# Türkçe hedef adları (eşleştirme dosyasında Name yerine İsim yazılabilir)
TR_TARGETS = {
    "ISIM": "NAME", "AD": "NAME",
    "ACIKLAMA": "DESCRIPTION", "AÇIKLAMA": "DESCRIPTION",
    "TIP": "OBJECTTYPE", "TİP": "OBJECTTYPE", "OBJETIPI": "OBJECTTYPE",
    "ETIKET": "TAG",
    "UZUNAD": "LONGNAME", "UZUNISIM": "LONGNAME",
}

SPATIAL = {
    "IFCSITE", "IFCBUILDING", "IFCBUILDINGSTOREY", "IFCSPACE",
    "IFCSPATIALZONE", "IFCEXTERNALSPATIALELEMENT", "IFCFACILITY",
    "IFCFACILITYPART", "IFCBRIDGE", "IFCROAD", "IFCRAILWAY", "IFCMARINEFACILITY",
}

NO_TAG = SPATIAL | {
    "IFCPROJECT", "IFCPROJECTLIBRARY", "IFCGRID", "IFCPROXY", "IFCANNOTATION",
    "IFCPORT", "IFCDISTRIBUTIONPORT", "IFCGROUP", "IFCZONE", "IFCSYSTEM",
    "IFCDISTRIBUTIONSYSTEM", "IFCDISTRIBUTIONCIRCUIT", "IFCBUILDINGSYSTEM",
    "IFCBUILTSYSTEM", "IFCASSET", "IFCINVENTORY", "IFCALIGNMENT",
    "IFCSTRUCTURALANALYSISMODEL", "IFCSTRUCTURALLOADGROUP",
    "IFCSTRUCTURALLOADCASE", "IFCSTRUCTURALRESULTGROUP",
}


def attr_index(target, cls):
    """Hedef öznitelik için argüman sırası; uygun değilse None."""
    if cls.endswith("TYPE") or cls.endswith("STYLE"):
        # Tip nesnelerinde yalnızca Name/Description güvenli
        return {"NAME": 2, "DESCRIPTION": 3}.get(target)
    if target == "NAME":
        return 2
    if target == "DESCRIPTION":
        return 3
    if target == "OBJECTTYPE":
        return 4
    if target == "TAG":
        if cls in NO_TAG or cls.startswith("IFCSTRUCTURAL"):
            return None
        return 7
    if target == "LONGNAME":
        if cls == "IFCPROJECT":
            return 5
        if cls in SPATIAL:
            return 7
        return None
    return None


# --------------------------------------------------------------------------
# STEP metin yardımcıları
# --------------------------------------------------------------------------

_STMT_RE = re.compile(r"^\s*#(\d+)\s*=\s*([A-Za-z0-9_]+)\s*\((.*)\)\s*;\s*$", re.S)
_REF_RE = re.compile(r"#(\d+)")
_TYPED_RE = re.compile(r"^\s*([A-Za-z0-9_]+)\s*\((.*)\)\s*$", re.S)


def split_args(argstr):
    """En üst düzey argümanları ayırır (string ve parantezlere duyarlı)."""
    args, buf, depth, in_str, i, n = [], [], 0, False, 0, len(argstr)
    while i < n:
        c = argstr[i]
        if in_str:
            buf.append(c)
            if c == "'":
                if i + 1 < n and argstr[i + 1] == "'":
                    buf.append("'")
                    i += 1
                else:
                    in_str = False
        elif c == "'":
            in_str = True
            buf.append(c)
        elif c == "(":
            depth += 1
            buf.append(c)
        elif c == ")":
            depth -= 1
            buf.append(c)
        elif c == "," and depth == 0:
            args.append("".join(buf).strip())
            buf = []
        else:
            buf.append(c)
        i += 1
    if buf or args:
        args.append("".join(buf).strip())
    return args


def decode_step_string(raw):
    """'...' biçimindeki STEP string'ini okunur metne çevirir."""
    if raw is None or raw == "$" or not raw.startswith("'"):
        return ""
    s = raw[1:-1].replace("''", "'")
    out, i, n = [], 0, len(s)
    while i < n:
        if s.startswith("\\X2\\", i):
            end = s.find("\\X0\\", i + 4)
            if end < 0:
                break
            hexs = s[i + 4:end]
            try:
                out.append(bytes.fromhex(hexs).decode("utf-16-be"))
            except ValueError:
                out.append(hexs)
            i = end + 4
        elif s.startswith("\\X4\\", i):
            end = s.find("\\X0\\", i + 4)
            if end < 0:
                break
            hexs = s[i + 4:end]
            try:
                out.append(bytes.fromhex(hexs).decode("utf-32-be"))
            except ValueError:
                out.append(hexs)
            i = end + 4
        elif s.startswith("\\X\\", i) and i + 5 <= n:
            try:
                out.append(chr(int(s[i + 3:i + 5], 16)))
            except ValueError:
                out.append(s[i:i + 5])
            i += 5
        elif s.startswith("\\S\\", i) and i + 3 < n:
            out.append(chr(ord(s[i + 3]) + 128))
            i += 4
        elif s.startswith("\\P", i) and i + 3 < n and s[i + 3] == "\\":
            i += 4
        elif s.startswith("\\\\", i):
            out.append("\\")
            i += 2
        else:
            out.append(s[i])
            i += 1
    text = "".join(out)
    if any(0x80 <= ord(ch) <= 0xFF for ch in text):
        try:  # UTF-8 olarak yazılmış dosyalar
            text = text.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return text


def encode_step_string(text):
    """Metni ISO 10303-21 uyumlu '...' string'ine çevirir."""
    out, wide = [], []

    def flush():
        if wide:
            data = "".join(wide).encode("utf-16-be").hex().upper()
            out.append("\\X2\\" + data + "\\X0\\")
            wide.clear()

    for ch in text:
        if 32 <= ord(ch) < 127:
            flush()
            if ch == "'":
                out.append("''")
            elif ch == "\\":
                out.append("\\\\")
            else:
                out.append(ch)
        else:
            wide.append(ch)
    flush()
    return "'" + "".join(out) + "'"


def value_to_label(nominal):
    """IFCLABEL('x') / IFCREAL(1.5) / IFCBOOLEAN(.T.) -> IFC string literal."""
    if not nominal or nominal == "$":
        return None
    m = _TYPED_RE.match(nominal)
    inner = m.group(2).strip() if m else nominal.strip()
    if inner == "$" or inner == "":
        return None
    if inner.startswith("'"):
        return inner
    if inner in (".T.", ".F.", ".U."):
        return {".T.": "'TRUE'", ".F.": "'FALSE'", ".U.": "'UNKNOWN'"}[inner]
    if inner.startswith("."):
        return "'" + inner.strip(".") + "'"
    if inner.startswith("#") or inner.startswith("("):
        return None
    return "'" + inner + "'"


_GUID_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_$"


def new_guid():
    n = uuid.uuid4().int
    s = []
    for _ in range(22):
        s.append(_GUID_CHARS[n % 64])
        n //= 64
    return "".join(reversed(s))


# --------------------------------------------------------------------------
# Eşleştirme kuralları
# --------------------------------------------------------------------------

_MAP_RE = re.compile(r"^\s*(?:([A-Za-z0-9_,\s]+?)\s*:)?\s*(.+?)\s*(?:->|=>|=)\s*(.+?)\s*$")


class Rule:
    def __init__(self, classes, source, target, line):
        self.classes = classes            # set of upper-case IFC class names or None
        self.source = source              # kaynak nitelik (görünen ad)
        self.source_key = source.strip().lower()
        self.line = line
        t = target.strip()
        self.entity = None                # "NAME" ...
        self.pset = None
        self.prop = None
        if "." in t:
            self.pset, self.prop = t.split(".", 1)
            self.pset = self.pset.strip()
            self.prop = self.prop.strip() or source.strip()
            if not self.pset:
                raise ValueError("Pset adı boş: " + line)
        else:
            key = t.replace(" ", "").replace("İ", "I").replace("ı", "i").upper()
            key = TR_TARGETS.get(key, key)
            if key not in ENTITY_TARGETS:
                raise ValueError(
                    "Geçersiz hedef '%s'. Kullanılabilir: %s ya da PsetAdi.OzellikAdi"
                    % (t, ", ".join(ENTITY_TARGETS.values())))
            self.entity = key
            if self.source_key == "*":
                raise ValueError("'*' yalnızca bir Pset'e yönlendirilebilir (örn. * -> ePYS.): " + line)

    def applies_to(self, cls):
        return self.classes is None or cls in self.classes

    def target_text(self):
        return ENTITY_TARGETS[self.entity] if self.entity else "%s.%s" % (self.pset, self.prop)


def parse_rules(lines):
    rules, errors = [], []
    for raw in lines:
        line = (raw or "").strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue
        m = _MAP_RE.match(line)
        if not m:
            errors.append("Okunamadı: " + line)
            continue
        cls_part, src, tgt = m.groups()
        classes = None
        if cls_part:
            classes = {c.strip().upper() for c in cls_part.split(",") if c.strip()}
            classes = {c if c.startswith("IFC") else "IFC" + c for c in classes}
        try:
            rules.append(Rule(classes, src, tgt, line))
        except ValueError as e:
            errors.append(str(e))
    return rules, errors


# --------------------------------------------------------------------------
# R7: paletten gelen eşleştirme (TXT yazmadan)
# --------------------------------------------------------------------------

# Paletteki "Eleman" seçenekleri -> IFC sınıfları (None = tüm elemanlar).
# IFC2x3'te Allplan duvarı IfcWallStandardCase vb. olarak yazar; ikisi birlikte verilir.
ELEMENT_CLASSES = OrderedDict([
    ("Tüm elemanlar",            None),
    ("Mahal (IfcSpace)",         ["IfcSpace"]),
    ("Duvar (IfcWall)",          ["IfcWall", "IfcWallStandardCase", "IfcWallElementedCase"]),
    ("Kolon (IfcColumn)",        ["IfcColumn", "IfcColumnStandardCase"]),
    ("Kiriş (IfcBeam)",          ["IfcBeam", "IfcBeamStandardCase"]),
    ("Döşeme (IfcSlab)",         ["IfcSlab", "IfcSlabStandardCase", "IfcSlabElementedCase"]),
    ("Temel (IfcFooting)",       ["IfcFooting"]),
    ("Merdiven (IfcStair)",      ["IfcStair", "IfcStairFlight"]),
    ("Kapı (IfcDoor)",           ["IfcDoor", "IfcDoorStandardCase"]),
    ("Pencere (IfcWindow)",      ["IfcWindow", "IfcWindowStandardCase"]),
    ("Korkuluk (IfcRailing)",    ["IfcRailing"]),
    ("Giydirme Cephe (IfcCurtainWall)", ["IfcCurtainWall"]),
    ("Çatı (IfcRoof)",           ["IfcRoof"]),
    ("Baca (IfcChimney)",        ["IfcChimney"]),
    ("Kat (IfcBuildingStorey)",  ["IfcBuildingStorey"]),
])

# Paletteki "Hedef" seçenekleri -> Rule hedef adı
PALETTE_TARGETS = OrderedDict([
    ("İsim", "Name"), ("Açıklama", "Description"), ("Tip", "ObjectType"),
    ("Etiket", "Tag"), ("Uzun Ad", "LongName"),
])


def palette_rules(entries):
    """entries: [(eleman_secimi, kaynak_nitelik, hedef_secimi), ...] palet sırasıyla.
    Kaynak boşsa satır atlanır. Dönüş: (kurallar, hatalar) – read_rules_file ile aynı biçim."""
    rules, errors = [], []
    for elem, src, tgt in entries:
        src = (src or "").strip()
        if not src:
            continue
        cls_list = ELEMENT_CLASSES.get((elem or "").strip(), None)
        if (elem or "").strip() and (elem or "").strip() not in ELEMENT_CLASSES:
            errors.append("Bilinmeyen eleman seçimi: %s" % elem)
            continue
        target = PALETTE_TARGETS.get((tgt or "").strip(), (tgt or "").strip())
        classes = {c.upper() for c in cls_list} if cls_list else None
        line = "%s%s -> %s" % ((",".join(cls_list) + ": ") if cls_list else "", src, target)
        try:
            rules.append(Rule(classes, src, target, line))
        except ValueError as e:
            errors.append(str(e))
    return rules, errors


def rules_to_text(rules):
    """Kuralları TXT eşleştirme biçiminde yazar (palet -> gelişmiş dosyaya aktarım için)."""
    return "\n".join(r.line for r in rules) + "\n"


def read_rules_file(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return parse_rules(f.readlines())


def _expand(rules, props, cls):
    """Sınıfa uyan kuralları (kural, nitelik) çiftlerine açar; '*' kalan tüm nitelikler."""
    used = set()
    pairs = []
    for rule in rules:
        if not rule.applies_to(cls) or rule.source_key == "*":
            continue
        entry = props.get(rule.source_key)
        if entry:
            pairs.append((rule, entry))
            used.add(rule.source_key)
    for rule in rules:
        if rule.source_key == "*" and rule.applies_to(cls):
            for key, entry in props.items():
                if key not in used:
                    pairs.append((rule, entry))
                    used.add(key)
    return pairs


# --------------------------------------------------------------------------
# IFC dosyası okuma / yazma
# --------------------------------------------------------------------------

class IfcText:
    def __init__(self, path):
        self.path = path
        with open(path, "r", encoding="latin-1", newline="") as f:
            data = f.read()
        self.newline = "\r\n" if "\r\n" in data[:4000] else "\n"
        self.prefix = []          # DATA; dahil başlık
        self.stmts = []           # [raw, id, NAME, argstr]
        self.suffix = []
        self._split(data)
        self.by_id = {}
        for idx, st in enumerate(self.stmts):
            if st[1] is not None:
                self.by_id[st[1]] = idx
        self.max_id = max(self.by_id) if self.by_id else 0

    def _split(self, data):
        lines = data.splitlines(True)
        state, buf = 0, ""
        for line in lines:
            if state == 0:
                self.prefix.append(line)
                if line.strip().upper() == "DATA;":
                    state = 1
            elif state == 1:
                if not buf and line.strip().upper() == "ENDSEC;":
                    self.suffix.append(line)
                    state = 2
                    continue
                buf += line
                core = buf.rstrip()
                if core.endswith(";") and buf.count("'") % 2 == 0:
                    m = _STMT_RE.match(buf)
                    if m:
                        self.stmts.append([buf, int(m.group(1)), m.group(2).upper(), m.group(3)])
                    else:
                        self.stmts.append([buf, None, None, None])
                    buf = ""
                elif not core:
                    self.stmts.append([buf, None, None, None])
                    buf = ""
            else:
                self.suffix.append(line)
        if buf:
            self.stmts.append([buf, None, None, None])
        if state == 0:
            raise ValueError("Geçerli bir IFC (STEP) dosyası değil: DATA bölümü bulunamadı.")

    def get(self, eid):
        idx = self.by_id.get(eid)
        if idx is None:
            return None
        return self.stmts[idx]

    def args(self, eid):
        st = self.get(eid)
        return split_args(st[3]) if st else None

    def set_args(self, eid, args):
        idx = self.by_id[eid]
        st = self.stmts[idx]
        st[3] = ",".join(args)
        st[0] = "#%d=%s(%s);%s" % (eid, st[2], st[3], self.newline)

    def remove(self, eid):
        idx = self.by_id.get(eid)
        if idx is not None:
            self.stmts[idx][0] = ""

    def add(self, name, args):
        self.max_id += 1
        eid = self.max_id
        argstr = ",".join(args)
        self.stmts.append(["#%d=%s(%s);%s" % (eid, name, argstr, self.newline), eid, name, argstr])
        self.by_id[eid] = len(self.stmts) - 1
        return eid

    def schema(self):
        head = "".join(self.prefix).upper()
        if "IFC4X3" in head:
            return "IFC4X3"
        if "IFC4" in head:
            return "IFC4"
        if "IFC2X3" in head:
            return "IFC2X3"
        return "?"

    def write(self, path):
        with open(path, "w", encoding="latin-1", newline="") as f:
            f.write("".join(self.prefix))
            for st in self.stmts:
                if st[0]:
                    f.write(st[0])
            f.write("".join(self.suffix))


# --------------------------------------------------------------------------
# Ana işlem
# --------------------------------------------------------------------------

def default_output(path):
    base, ext = os.path.splitext(path)
    return base + "_ePYS" + (ext or ".ifc")


def _read_complex(ifc, cid, layered, inner, depth=0):
    """R10: IFCCOMPLEXPROPERTY ('Object Layer Attributes #n') içindeki nitelikleri toplar.
    Aynı ad birden çok katmanda varsa ilk dolu katman kullanılır."""
    c = ifc.get(cid)
    if not c or c[2] != "IFCCOMPLEXPROPERTY" or depth > 4:
        return
    ca = split_args(c[3])
    for pid in (int(x) for x in _REF_RE.findall(ca[3] if len(ca) > 3 else "")):
        inner.append(pid)
        p = ifc.get(pid)
        if not p:
            continue
        if p[2] == "IFCPROPERTYSINGLEVALUE":
            pa = split_args(p[3])
            pname = decode_step_string(pa[0])
            nominal = pa[2] if len(pa) > 2 else "$"
            key = pname.strip().lower()
            old = layered.get(key)
            if old is None or value_to_label(old[2]) in (None, "''"):
                layered[key] = (pid, pname, nominal)
        elif p[2] == "IFCCOMPLEXPROPERTY":
            _read_complex(ifc, pid, layered, inner, depth + 1)


def _is_source_pset(name, src_key):
    """R10: 'AllplanAttributes' ve 'AllplanAttributes (MM-KAP-…)' gibi adlandırılmış setler."""
    n = name.strip().lower()
    return n == src_key or n.startswith(src_key + " (")


def process(ifc_path, rules, out_path=None, source_pset="AllplanAttributes",
            remove_moved=True, remove_whole_pset=False, overwrite=True,
            skip_empty=True, analyse_only=False, report_dir=None, log=print,
            read_layers=True):
    """
    IFC dosyasını işler. Sonuç sözlüğü döner:
      out_path, report_path, analysis_path, counts, warnings
    """
    ifc = IfcText(ifc_path)
    src_key = source_pset.strip().lower()
    warnings = []

    # 1) Kaynak Pset'leri ve ilişkileri bul
    psets = {}           # pset_id -> dict(owner=..., props=OrderedDict(key -> (pid, name, nominal)), other=[pid])
    for st in ifc.stmts:
        if st[2] == "IFCPROPERTYSET":
            a = split_args(st[3])
            if len(a) >= 5 and _is_source_pset(decode_step_string(a[2]), src_key):
                props, other, layered, inner = OrderedDict(), [], OrderedDict(), []
                for pid in (int(x) for x in _REF_RE.findall(a[4])):
                    p = ifc.get(pid)
                    if p and p[2] == "IFCPROPERTYSINGLEVALUE":
                        pa = split_args(p[3])
                        pname = decode_step_string(pa[0])
                        props[pname.strip().lower()] = (pid, pname, pa[2] if len(pa) > 2 else "$")
                    else:
                        other.append(pid)
                        if p and p[2] == "IFCCOMPLEXPROPERTY":
                            _read_complex(ifc, pid, layered, inner)
                psets[st[1]] = {"owner": a[1], "props": props, "other": other, "objects": [], "rels": [],
                                "layered": layered, "inner": inner}

    for st in ifc.stmts:
        if st[2] == "IFCRELDEFINESBYPROPERTIES":
            a = split_args(st[3])
            if len(a) >= 6:
                ref = _REF_RE.findall(a[5])
                if ref and int(ref[0]) in psets:
                    ps = psets[int(ref[0])]
                    ps["rels"].append(st[1])
                    ps["objects"].extend(int(x) for x in _REF_RE.findall(a[4]))

    # 2) Analiz raporu (her zaman)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = report_dir or os.path.dirname(os.path.abspath(out_path or ifc_path))
    base = os.path.splitext(os.path.basename(ifc_path))[0]
    analysis_path = os.path.join(report_dir, "%s_analiz_%s.csv" % (base, stamp))

    stats = OrderedDict()
    for ps in psets.values():
        classes = Counter()
        for oid in ps["objects"]:
            o = ifc.get(oid)
            if o:
                classes[o[2]] += 1
        items = list(ps["props"].items())
        if read_layers:
            items += [(k, v) for k, v in ps["layered"].items() if k not in ps["props"]]
        for key, (pid, pname, nominal) in items:
            if key not in ps["props"]:
                pname = pname + " (katmanlı)"
            s = stats.setdefault(key, {"name": pname, "count": 0, "classes": Counter(), "sample": ""})
            s["count"] += max(1, len(ps["objects"]))
            s["classes"].update(classes)
            if not s["sample"]:
                lab = value_to_label(nominal)
                if lab and lab != "''":
                    s["sample"] = decode_step_string(lab)

    with open(analysis_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Nitelik (IFC'deki adı)", "Eleman sayısı", "IFC sınıfları", "Örnek değer",
                     "Kural var mı"])
        rule_keys = {r.source_key for r in rules}
        for key, s in sorted(stats.items(), key=lambda kv: kv[1]["name"].lower()):
            cls_txt = ", ".join("%s(%d)" % (c, n) for c, n in s["classes"].most_common())
            w.writerow([s["name"], s["count"], cls_txt, s["sample"],
                    "Evet" if key in rule_keys else ("*" if "*" in rule_keys else "")])

    result = {"out_path": None, "report_path": None, "analysis_path": analysis_path,
              "schema": ifc.schema(), "pset_count": len(psets), "counts": Counter(),
              "warnings": warnings}

    if not psets:
        warnings.append("'%s' adlı property set dosyada bulunamadı." % source_pset)
    for r in rules:
        if r.source_key != "*" and r.source_key not in stats:
            warnings.append("Kaynak nitelik dosyada yok: %s" % r.source)

    if analyse_only:
        log("Analiz tamamlandı: %d nitelik, %d property set." % (len(stats), len(psets)))
        return result

    # 3) Kuralları uygula
    report_rows = []
    new_props = OrderedDict()    # (obj_id, pset_name) -> OrderedDict(prop_name -> nominal)
    owner_for = {}
    counts = result["counts"]

    # R8: Kurallar nesne başına, nesnenin TÜM kaynak setlerindeki nitelikler birleştirilerek
    # bir kez uygulanır. (R7 ve öncesinde her set ayrı işleniyordu; nitelikler iki sete
    # bölünmüşse sonra gelen set, örn. "İsim", mahalde "CSB_Mahal"ı eziyordu.)
    for ps in psets.values():
        ps["moved"] = {}
    obj_props = OrderedDict()            # oid -> OrderedDict(key -> (pid, pname, nominal, ps_id))
    layered_pids = set()                 # R10: katman içi nitelikler (yerinde bırakılır)
    for ps_id, ps in psets.items():
        for oid in OrderedDict.fromkeys(ps["objects"]):
            d = obj_props.setdefault(oid, OrderedDict())
            for key, (pid, pname, nominal) in ps["props"].items():
                if key not in d or value_to_label(d[key][2]) in (None, "''"):
                    d[key] = (pid, pname, nominal, ps_id)
    if read_layers:
        # Üst seviyede olmayan (ya da boş olan) nitelikler katmanlardan tamamlanır.
        for ps_id, ps in psets.items():
            for oid in OrderedDict.fromkeys(ps["objects"]):
                d = obj_props.setdefault(oid, OrderedDict())
                for key, (pid, pname, nominal) in ps["layered"].items():
                    if key not in d or value_to_label(d[key][2]) in (None, "''"):
                        d[key] = (pid, pname, nominal, ps_id)
                        layered_pids.add(pid)

    for oid, merged in obj_props.items():
        obj = ifc.get(oid)
        if not obj:
            continue
        cls = obj[2]
        oargs = split_args(obj[3])
        orig_args = list(oargs)
        gid = decode_step_string(oargs[0]) if oargs else ""
        flat = OrderedDict((k, (v[0], v[1], v[2])) for k, v in merged.items())
        done_here = set()
        for rule, entry in _expand(rules, flat, cls):
            pid, pname, nominal = entry
            ps_id = merged[pname.strip().lower()][3]
            moved = psets[ps_id]["moved"]
            if pid in done_here and rule.source_key == "*":
                continue
            done_here.add(pid)
            if rule.entity:
                lab = value_to_label(nominal)
                if lab is None or (skip_empty and lab == "''"):
                    continue
                idx = attr_index(rule.entity, cls)
                if idx is None or idx >= len(oargs):
                    report_rows.append([oid, cls, gid, rule.source, rule.target_text(), "",
                                        decode_step_string(lab),
                                        "Atlandı: bu sınıfta %s alanı yok" % rule.target_text()])
                    counts["atlandi"] += 1
                    continue
                old = oargs[idx]
                if not overwrite and old not in ("$", "''") and old == orig_args[idx]:
                    report_rows.append([oid, cls, gid, rule.source, rule.target_text(),
                                        decode_step_string(old), decode_step_string(lab),
                                        "Atlandı: alan dolu"])
                    counts["atlandi"] += 1
                    continue
                oargs[idx] = lab
                if pid not in layered_pids:
                    moved.setdefault(pid, set()).add(oid)
                else:
                    counts["katmandan"] += 1
                counts["yazildi"] += 1
                report_rows.append([oid, cls, gid, rule.source, rule.target_text(),
                                    decode_step_string(old), decode_step_string(lab), "Yazıldı"])
            else:
                if nominal in (None, "$"):
                    continue
                if skip_empty and value_to_label(nominal) == "''":
                    continue
                key = (oid, rule.pset)
                prop_name = pname if rule.source_key == "*" else rule.prop
                new_props.setdefault(key, OrderedDict())[prop_name] = nominal
                owner_for[key] = psets[ps_id]["owner"]
                if pid not in layered_pids:
                    moved.setdefault(pid, set()).add(oid)
                counts["pset"] += 1
                report_rows.append([oid, cls, gid, pname, "%s.%s" % (rule.pset, prop_name), "",
                                    decode_step_string(value_to_label(nominal) or ""), "Pset'e taşındı"])
        if oargs != orig_args:
            ifc.set_args(oid, oargs)

    # 4) Yeni Pset'leri oluştur
    for (oid, pset_name), props in new_props.items():
        pids = []
        for pname, nominal in props.items():
            pids.append(ifc.add("IFCPROPERTYSINGLEVALUE",
                                [encode_step_string(pname), "$", nominal, "$"]))
        owner = owner_for[(oid, pset_name)] or "$"
        ps_new = ifc.add("IFCPROPERTYSET", ["'%s'" % new_guid(), owner, encode_step_string(pset_name), "$",
                                            "(" + ",".join("#%d" % p for p in pids) + ")"])
        ifc.add("IFCRELDEFINESBYPROPERTIES", ["'%s'" % new_guid(), owner, "$", "$",
                                              "(#%d)" % oid, "#%d" % ps_new])

    # 5) AllplanAttributes'tan sil
    if remove_moved or remove_whole_pset:
        refcount = Counter()
        for st in ifc.stmts:
            if st[3] and st[0]:
                refcount.update(int(x) for x in _REF_RE.findall(st[3]))
        for ps_id, ps in psets.items():
            all_pids = [v[0] for v in ps["props"].values()] + ps["other"]
            if not all_pids:
                continue
            if remove_whole_pset:
                drop = set(all_pids) | set(ps.get("inner", []))
            else:
                # Pset birden çok nesneye bağlıysa, nitelik ancak hepsinde
                # taşındıysa silinir (sınıf filtresi olan kurallar için).
                objs = set(ps["objects"])
                drop = {pid for pid, done in ps.get("moved", {}).items() if done >= objs}
            if not drop:
                continue
            a = ifc.args(ps_id)
            orig = [int(x) for x in _REF_RE.findall(a[4])]
            keep = [p for p in orig if p not in drop]
            if keep:
                a[4] = "(" + ",".join("#%d" % p for p in keep) + ")"
                ifc.set_args(ps_id, a)
            else:
                ifc.remove(ps_id)
                for rid in ps["rels"]:
                    ifc.remove(rid)
                counts["pset_silindi"] += 1
            for pid in drop:
                if refcount[pid] <= 1 or (remove_whole_pset and pid in ps.get("inner", [])):
                    ifc.remove(pid)
                if pid not in ps.get("inner", []):
                    counts["nitelik_silindi"] += 1

    # 6) Yaz
    out_path = out_path or default_output(ifc_path)
    if os.path.abspath(out_path) == os.path.abspath(ifc_path):
        raise ValueError("Çıktı dosyası girdi dosyasıyla aynı olamaz.")
    ifc.write(out_path)
    result["out_path"] = out_path

    report_path = os.path.join(report_dir, "%s_rapor_%s.csv" % (base, stamp))
    with open(report_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["IFC #", "Sınıf", "GlobalId", "Kaynak nitelik", "Hedef", "Eski değer", "Yeni değer", "Durum"])
        w.writerows(report_rows)
    result["report_path"] = report_path

    log("Yazılan alan: %d, Pset'e taşınan: %d, silinen nitelik: %d, atlanan: %d, katmandan okunan: %d"
        % (counts["yazildi"], counts["pset"], counts["nitelik_silindi"], counts["atlandi"], counts["katmandan"]))
    return result


# --------------------------------------------------------------------------
# Komut satırı
# --------------------------------------------------------------------------

def _main():
    import argparse
    ap = argparse.ArgumentParser(description="e-PYS IFC Düzenleyici (ALUPLAN)")
    ap.add_argument("ifc", help="Allplan'dan alınan IFC dosyası")
    ap.add_argument("--map", help="Eşleştirme dosyası (txt)")
    ap.add_argument("--out", help="Çıktı IFC (varsayılan: <ad>_ePYS.ifc)")
    ap.add_argument("--pset", default="AllplanAttributes", help="Kaynak property set adı")
    ap.add_argument("--analiz", action="store_true", help="Sadece analiz raporu üret")
    ap.add_argument("--koru", action="store_true", help="Taşınan nitelikleri AllplanAttributes'ta bırak")
    ap.add_argument("--hepsini-sil", action="store_true", help="AllplanAttributes setini tamamen sil")
    ap.add_argument("--uzerine-yazma", action="store_true", help="Dolu IFC alanlarını değiştirme")
    ns = ap.parse_args()

    rules = []
    if ns.map:
        rules, errors = read_rules_file(ns.map)
        for e in errors:
            print("UYARI:", e)
    elif not ns.analiz:
        ap.error("--map ya da --analiz gerekli")

    res = process(ns.ifc, rules, ns.out, ns.pset, remove_moved=not ns.koru,
                  remove_whole_pset=ns.hepsini_sil, overwrite=not ns.uzerine_yazma,
                  analyse_only=ns.analiz)
    for wmsg in res["warnings"]:
        print("UYARI:", wmsg)
    print("Analiz :", res["analysis_path"])
    if res["out_path"]:
        print("Çıktı  :", res["out_path"])
        print("Rapor  :", res["report_path"])


if __name__ == "__main__":
    _main()
