# -*- coding: utf-8 -*-
"""Allplan NemAll_Python_IFW_ElementAdapter taklidi (yalnız testler için)."""


class _T:
    def __init__(s, n):
        s.n = n

    def GetTypeName(s):
        return s.n


class Ele:
    """Allplan öğesi: tip adı, nitelikler (id -> değer), üst ve alt öğeler."""
    _c = 0

    def __init__(s, t, attrs=None, parent=None, children=()):
        s.t = t
        s.attrs = attrs or {}
        s.parent = parent
        s.children = list(children)
        for k in s.children:
            k.parent = s
        Ele._c += 1
        s.u = Ele._c

    def GetElementAdapterType(s):
        return _T(s.t)

    def GetAttributes(s, rs):
        return list(s.attrs.items())

    def GetModelElementUUID(s):
        return s.u

    def IsNull(s):
        return False


class BaseElementAdapterList(list):
    pass


class BaseElementAdapterParentElementService:
    @staticmethod
    def GetParentElement(e):
        return e.parent


class BaseElementAdapterChildElementsService:
    @staticmethod
    def GetChildModelElements(e, h):
        return e.children
