# -*- coding: utf-8 -*-
"""Allplan BaseScriptObject taklidi."""


class BaseScriptObjectData:
    pass


class BaseScriptObject:
    def __init__(s, d):
        s.document = None
        s.coord_input = None
        s.script_object_interactor = None
