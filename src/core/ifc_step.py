# -*- coding: utf-8 -*-
"""Bağımlılıksız IFC (STEP / ISO-10303-21) okuyucu. ALUPLAN – PP09."""
import re

_ENT_RE = re.compile(r"#(\d+)\s*=\s*([A-Z0-9_]+)\s*\(", re.S)


class Ref(int):
    """#123 referansı"""
    def __repr__(self):
        return "#%d" % int(self)


class Enum(str):
    """.T. / .USERDEFINED. değeri"""
    def __repr__(self):
        return ".%s." % str(self)


class Typed(object):
    """IFCLABEL('x') gibi tipli değer"""
    __slots__ = ("type", "value")

    def __init__(self, t, v):
        self.type = t
        self.value = v

    def __repr__(self):
        return "%s(%r)" % (self.type, self.value)


def decode_step_string(s):
    """IFC metin kodlamasını çözer: \\X2\\..\\X0\\, \\X\\hh, \\S\\c, ''"""
    if "\\" not in s and "''" not in s:
        return s
    out = []
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c == "\\" and s.startswith("\\X2\\", i):
            j = s.find("\\X0\\", i + 4)
            if j < 0:
                j = n
            hexs = s[i + 4:j]
            for k in range(0, len(hexs) - 3, 4):
                try:
                    out.append(chr(int(hexs[k:k + 4], 16)))
                except ValueError:
                    pass
            i = j + 4
        elif c == "\\" and s.startswith("\\X4\\", i):
            j = s.find("\\X0\\", i + 4)
            if j < 0:
                j = n
            hexs = s[i + 4:j]
            for k in range(0, len(hexs) - 7, 8):
                try:
                    out.append(chr(int(hexs[k:k + 8], 16)))
                except ValueError:
                    pass
            i = j + 4
        elif c == "\\" and s.startswith("\\X\\", i) and i + 5 <= n:
            try:
                out.append(bytes([int(s[i + 3:i + 5], 16)]).decode("latin-1"))
            except ValueError:
                out.append(s[i:i + 5])
            i += 5
        elif c == "\\" and s.startswith("\\S\\", i) and i + 3 < n:
            out.append(chr(ord(s[i + 3]) + 128))
            i += 4
        elif c == "\\" and s.startswith("\\\\", i):
            out.append("\\")
            i += 2
        elif c == "'" and s.startswith("''", i):
            out.append("'")
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def _parse_args(text, pos):
    """text[pos] '(' olmalı. (liste, yeni_pos) döndürür."""
    assert text[pos] == "("
    pos += 1
    items = []
    n = len(text)
    while pos < n:
        c = text[pos]
        if c in " \r\n\t,":
            pos += 1
            continue
        if c == ")":
            return items, pos + 1
        if c == "(":
            sub, pos = _parse_args(text, pos)
            items.append(sub)
            continue
        if c == "'":
            j = pos + 1
            while True:
                j = text.find("'", j)
                if j < 0:
                    j = n
                    break
                if j + 1 < n and text[j + 1] == "'":
                    j += 2
                    continue
                break
            items.append(decode_step_string(text[pos + 1:j]))
            pos = j + 1
            continue
        if c == "#":
            j = pos + 1
            while j < n and text[j].isdigit():
                j += 1
            items.append(Ref(int(text[pos + 1:j])))
            pos = j
            continue
        if c == "$":
            items.append(None)
            pos += 1
            continue
        if c == "*":
            items.append("*")
            pos += 1
            continue
        if c == ".":
            j = text.find(".", pos + 1)
            items.append(Enum(text[pos + 1:j]))
            pos = j + 1
            continue
        if c.isalpha():
            j = pos
            while j < n and (text[j].isalnum() or text[j] == "_"):
                j += 1
            tname = text[pos:j]
            k = j
            while k < n and text[k] in " \t\r\n":
                k += 1
            if k < n and text[k] == "(":
                sub, pos = _parse_args(text, k)
                items.append(Typed(tname, sub[0] if len(sub) == 1 else sub))
            else:
                items.append(Enum(tname))
                pos = j
            continue
        # sayı
        j = pos
        while j < n and text[j] not in ",)":
            j += 1
        tok = text[pos:j].strip()
        try:
            if any(ch in tok for ch in ".eE"):
                items.append(float(tok))
            else:
                items.append(int(tok))
        except ValueError:
            items.append(tok)
        pos = j
    return items, pos


class IfcFile(object):
    """IFC dosyası: ents[id] = (SINIF, argümanlar); ham metin saklanır (yazma için)."""

    def __init__(self, path):
        self.path = path
        with open(path, "rb") as f:
            raw = f.read()
        try:
            self.text = raw.decode("utf-8")
        except UnicodeDecodeError:
            self.text = raw.decode("latin-1")
        m = re.search(r"FILE_SCHEMA\s*\(\s*\(\s*'([^']+)'", self.text)
        self.schema = m.group(1).upper() if m else "IFC4"
        self._index = {}          # id -> (cls, start_of_args)
        self.by_class = {}
        ds = self.text.find("DATA;")
        for m in _ENT_RE.finditer(self.text, ds if ds >= 0 else 0):
            eid = int(m.group(1))
            cls = m.group(2)
            self._index[eid] = (cls, m.end() - 1)
            self.by_class.setdefault(cls, []).append(eid)
        self._cache = {}

    def cls(self, eid):
        t = self._index.get(int(eid))
        return t[0] if t else None

    def args(self, eid):
        eid = int(eid)
        a = self._cache.get(eid)
        if a is None:
            t = self._index.get(eid)
            if not t:
                return None
            a, _ = _parse_args(self.text, t[1])
            self._cache[eid] = a
        return a

    def of(self, *classes):
        for c in classes:
            for eid in self.by_class.get(c.upper(), ()):
                yield eid

    def header_name(self):
        m = re.search(r"FILE_NAME\s*\(\s*'([^']*)'", self.text)
        return decode_step_string(m.group(1)) if m else ""
