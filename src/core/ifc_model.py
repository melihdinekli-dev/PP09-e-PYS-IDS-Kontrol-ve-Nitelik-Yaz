# -*- coding: utf-8 -*-
"""IFC nesne bilgisi: nitelikler, Pset'ler, malzeme. ALUPLAN – PP09."""
from ifc_step import IfcFile, Ref, Enum, Typed

# IFC4 / IFC4X3 doğrudan nitelik sıraları (IfcRoot: 0 GlobalId,1 OwnerHistory,2 Name,3 Description)
_OBJ = ["GlobalId", "OwnerHistory", "Name", "Description", "ObjectType"]
_PROD = _OBJ + ["ObjectPlacement", "Representation"]
_ELEM = _PROD + ["Tag"]
ATTR_LAYOUT = {
    "_ELEMENT": _ELEM + ["PredefinedType"],
    "IFCDOOR": _ELEM + ["OverallHeight", "OverallWidth", "PredefinedType", "OperationType", "UserDefinedOperationType"],
    "IFCWINDOW": _ELEM + ["OverallHeight", "OverallWidth", "PredefinedType", "PartitioningType", "UserDefinedPartitioningType"],
    "IFCSPACE": _PROD + ["LongName", "CompositionType", "PredefinedType", "ElevationWithFlooring"],
    "IFCBUILDINGSTOREY": _PROD + ["LongName", "CompositionType", "Elevation"],
    "IFCBUILDING": _PROD + ["LongName", "CompositionType", "ElevationOfRefHeight", "ElevationOfTerrain", "BuildingAddress"],
    "IFCSITE": _PROD + ["LongName", "CompositionType", "RefLatitude", "RefLongitude", "RefElevation", "LandTitleNumber", "SiteAddress"],
    "IFCZONE": _OBJ + ["LongName"],
    "IFCPROJECT": _OBJ + ["LongName", "Phase", "RepresentationContexts", "UnitsInContext"],
    "IFCOPENINGELEMENT": _ELEM + ["PredefinedType"],
    "IFCBUILDINGELEMENTPART": _ELEM + ["PredefinedType"],
    "IFCPERSON": ["Identification", "FamilyName", "GivenName", "MiddleNames", "PrefixTitles", "SuffixTitles", "Roles", "Addresses"],
    "IFCORGANIZATION": ["Identification", "Name", "Description", "Roles", "Addresses"],
    "IFCPERSONANDORGANIZATION": ["ThePerson", "TheOrganization", "Roles"],
    "IFCACTORROLE": ["Role", "UserDefinedRole", "Description"],
    "IFCSYSTEM": _OBJ, "IFCDISTRIBUTIONSYSTEM": _OBJ + ["LongName", "PredefinedType"],
    "IFCSPATIALZONE": _PROD + ["LongName", "PredefinedType"],
    "IFCANNOTATION": _PROD + ["PredefinedType"],
    "IFCMAPCONVERSION": ["SourceCRS", "TargetCRS", "Eastings", "Northings", "OrthogonalHeight", "XAxisAbscissa", "XAxisOrdinate", "Scale"],
    "IFCPROJECTEDCRS": ["Name", "Description", "GeodeticDatum", "VerticalDatum", "MapProjection", "MapZone", "MapUnit"],
    "IFCGEOMETRICREPRESENTATIONCONTEXT": ["ContextIdentifier", "ContextType", "CoordinateSpaceDimension", "Precision", "WorldCoordinateSystem", "TrueNorth"],
}
# IFC2x3: kapı/pencerede PredefinedType yok
ATTR_LAYOUT_2X3 = dict(ATTR_LAYOUT)
ATTR_LAYOUT_2X3["IFCDOOR"] = _ELEM + ["OverallHeight", "OverallWidth"]
ATTR_LAYOUT_2X3["IFCWINDOW"] = _ELEM + ["OverallHeight", "OverallWidth"]
ATTR_LAYOUT_2X3["IFCSPACE"] = _PROD + ["LongName", "CompositionType", "InteriorOrExteriorSpace", "ElevationWithFlooring"]
ATTR_LAYOUT_2X3["IFCZONE"] = _OBJ
ATTR_LAYOUT_2X3["_ELEMENT"] = _ELEM + ["PredefinedType"]


def plain(v):
    """IFC değerini düz Python değerine çevirir."""
    if isinstance(v, Typed):
        return plain(v.value)
    if isinstance(v, Enum):
        if v == "T":
            return True
        if v == "F":
            return False
        if v == "U":
            return None
        return str(v)
    if isinstance(v, list):
        return [plain(x) for x in v]
    return v


def is_empty(v):
    if v is None:
        return True
    if isinstance(v, str) and v.strip() == "":
        return True
    if isinstance(v, list) and len(v) == 0:
        return True
    return False


class IfcModel(object):
    def __init__(self, path):
        self.f = IfcFile(path)
        self.schema = self.f.schema
        self.layout = ATTR_LAYOUT_2X3 if self.schema.startswith("IFC2X3") else ATTR_LAYOUT
        self._psets = None
        self._mats = None
        self._type_of = None

    # ---------------------------------------------------------------- nitelik
    def attr(self, eid, name):
        cls = self.f.cls(eid)
        lay = self.layout.get(cls)
        if lay is None:
            lay = self.layout["_ELEMENT"]
        a = self.f.args(eid)
        if name not in lay:
            return None, False          # sınıfta bu nitelik yok
        i = lay.index(name)
        if i >= len(a):
            return None, False
        v = a[i]
        if v == "*":
            return None, True
        if isinstance(v, Ref):
            return v, True
        return plain(v), True

    def name(self, eid):
        return self.attr(eid, "Name")[0]

    # ---------------------------------------------------------------- Pset
    def _build_psets(self):
        self._psets = {}
        self._type_of = {}
        f = self.f
        for rid in f.of("IFCRELDEFINESBYPROPERTIES"):
            a = f.args(rid)
            objs = a[4] if isinstance(a[4], list) else [a[4]]
            pdef = a[5]
            for o in objs:
                self._psets.setdefault(int(o), []).append(int(pdef))
        for rid in f.of("IFCRELDEFINESBYTYPE"):
            a = f.args(rid)
            for o in a[4]:
                self._type_of[int(o)] = int(a[5])

    def pset_ids(self, eid, with_type=True):
        if self._psets is None:
            self._build_psets()
        ids = list(self._psets.get(int(eid), []))
        if with_type:
            t = self._type_of.get(int(eid))
            if t:
                ta = self.f.args(t)
                hp = ta[5] if len(ta) > 5 else None
                if isinstance(hp, list):
                    ids = [int(x) for x in hp] + ids     # örnek değerleri tip değerlerini ezer
        return ids

    def type_id(self, eid):
        if self._psets is None:
            self._build_psets()
        return self._type_of.get(int(eid))

    def _props_of_set(self, pid):
        """{özellik adı: (değer, ifc tipi)}"""
        f = self.f
        cls = f.cls(pid)
        a = f.args(pid)
        out = {}
        if cls == "IFCPROPERTYSET":
            name = a[2]
            for pr in a[4] or []:
                self._read_prop(int(pr), out)
        elif cls == "IFCELEMENTQUANTITY":
            name = a[2]
            for q in a[5] or []:
                qa = f.args(q)
                qc = f.cls(q)
                val = qa[3] if len(qa) > 3 else None
                out[qa[0]] = (plain(val), qc.replace("IFCQUANTITY", "Ifc") + "Measure")
        else:
            name = a[2] if len(a) > 2 else None
        return name, out

    def _read_prop(self, pr, out):
        f = self.f
        pc = f.cls(pr)
        pa = f.args(pr)
        if pc == "IFCPROPERTYSINGLEVALUE":
            v = pa[2]
            out[pa[0]] = (plain(v), v.type if isinstance(v, Typed) else None)
        elif pc == "IFCPROPERTYENUMERATEDVALUE":
            v = pa[2]
            vals = [plain(x) for x in v] if isinstance(v, list) else ([plain(v)] if v is not None else [])
            t = v[0].type if isinstance(v, list) and v and isinstance(v[0], Typed) else None
            out[pa[0]] = (vals[0] if len(vals) == 1 else (vals or None), t)
        elif pc == "IFCCOMPLEXPROPERTY":
            sub = {}
            for x in pa[3] or []:
                self._read_prop(int(x), sub)
            for k, v in sub.items():
                out.setdefault(pa[0] + "." + k, v)
        else:
            out[pa[0]] = (None, None)

    def psets(self, eid, with_type=True):
        """{pset adı: {özellik: (değer, tip)}}"""
        res = {}
        for pid in self.pset_ids(eid, with_type):
            n, props = self._props_of_set(pid)
            if n is None:
                continue
            res.setdefault(n, {}).update(props)
        return res

    def gruplar(self, eid):
        """Elemanın IfcRelAssignsToGroup ile bağlı olduğu grup sınıfları"""
        if not hasattr(self, "_grp"):
            self._grp = {}
            for rid in self.f.of("IFCRELASSIGNSTOGROUP"):
                a = self.f.args(rid)
                gc = self.f.cls(a[6]) if len(a) > 6 and isinstance(a[6], Ref) else None
                for o in a[4] or []:
                    self._grp.setdefault(int(o), []).append(gc)
        return [g for g in self._grp.get(int(eid), []) if g]

    # ---------------------------------------------------------------- malzeme
    def _build_mats(self):
        self._mats = {}
        f = self.f
        for rid in f.of("IFCRELASSOCIATESMATERIAL"):
            a = f.args(rid)
            names = self._mat_names(a[5])
            for o in a[4]:
                self._mats.setdefault(int(o), []).extend(names)

    def _mat_names(self, mid, depth=0):
        if mid is None or depth > 6:
            return []
        f = self.f
        c = f.cls(mid)
        a = f.args(mid)
        if c == "IFCMATERIAL":
            return [a[0]]
        if c == "IFCMATERIALLAYERSETUSAGE":
            return self._mat_names(a[0], depth + 1)
        if c == "IFCMATERIALLAYERSET":
            out = []
            for l in a[0] or []:
                out += self._mat_names(l, depth + 1)
            if len(a) > 1 and a[1]:
                out.append(a[1])
            return out
        if c == "IFCMATERIALLAYER":
            out = self._mat_names(a[0], depth + 1)
            if len(a) > 3 and isinstance(a[3], str):
                out.append(a[3])
            return out
        if c == "IFCMATERIALPROFILESETUSAGE":
            return self._mat_names(a[0], depth + 1)
        if c == "IFCMATERIALPROFILESET":
            out = [a[0]] if a[0] else []
            for p in a[2] or []:
                out += self._mat_names(p, depth + 1)
            return out
        if c == "IFCMATERIALPROFILE":
            out = [a[0]] if a[0] else []
            return out + self._mat_names(a[2], depth + 1)
        if c == "IFCMATERIALCONSTITUENTSET":
            out = [a[0]] if a[0] else []
            for p in a[2] or []:
                out += self._mat_names(p, depth + 1)
            return out
        if c == "IFCMATERIALCONSTITUENT":
            out = [a[0]] if a[0] else []
            return out + self._mat_names(a[2], depth + 1)
        if c == "IFCMATERIALLIST":
            out = []
            for m in a[0] or []:
                out += self._mat_names(m, depth + 1)
            return out
        return []

    def materials(self, eid):
        if self._mats is None:
            self._build_mats()
        names = list(self._mats.get(int(eid), []))
        t = self.type_id(eid)
        if t and not names:
            names = list(self._mats.get(int(t), []))
        return [n for n in names if n]
