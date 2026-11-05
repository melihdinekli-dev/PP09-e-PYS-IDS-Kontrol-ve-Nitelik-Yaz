# -*- coding: utf-8 -*-
"""Allplan NemAll_Python_BaseElements taklidi: nitelik adları/ID'leri ve yazılan değerlerin kaydı."""


class eAttibuteReadState:
    ReadAll = 1


WRITES = []          # (nitelik listesi, öğe tipleri)
NAMES = {"İsim": 498, "Kod yazısı": 1001, "Yangın Dayanım Sınıfı": 1002, "Dış Yapı Elemanı": 1003,
         "Statik_taşıyıcı": 1004, "Kaçış Yolu": 1005, "Malzeme": 508, "IFC obje kategorisi": 1006, "CSB_Mahal": 1007}
TYPES = {498: "String", 1001: "String", 1002: "String", 1003: "Integer", 1004: "Integer", 1005: "Integer",
         508: "String", 1006: "String", 1007: "String"}


class AttributeService:
    @staticmethod
    def GetAttributeID(doc, name):
        return NAMES.get(name, -1)

    @staticmethod
    def GetAttributeType(doc, i):
        return TYPES.get(i, "String")

    @staticmethod
    def GetAttributeName(doc, i):
        return {v: k for k, v in NAMES.items()}.get(i, str(i))


class ElementsAttributeService:
    @staticmethod
    def ChangeAttributes(attrs, lst, *a):
        WRITES.append((list(attrs), [e.t for e in lst], a))
        for e in lst:
            for i, v in attrs:
                e.attrs[i] = v
