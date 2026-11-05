# -*- coding: utf-8 -*-
"""Allplan çoklu seçim taklidi. START sayacı, seçimin kaç kez başlatıldığını sayar (R17 çökme testi)."""
START = []


class MultiElementSelectInteractorResult:
    def __init__(s):
        s.sel_elements = []


class MultiElementSelectInteractor:
    def __init__(s, r, prompt_msg=""):
        s.r = r
        s.msg = prompt_msg

    def start_input(s, c):
        START.append(s)
