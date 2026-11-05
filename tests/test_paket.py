# -*- coding: utf-8 -*-
"""Paket ve palet (.pyp) kontrolleri – daha önce Allplan'da yaşanan sorunların tekrarını önler."""
import collections
import os
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SURUM = open(os.path.join(ROOT, "VERSION"), encoding="utf-8").read().strip()


def test_paket_uretilir_ve_icerik_dogru():
    subprocess.check_call([sys.executable, os.path.join(ROOT, "build.py"), "--kontrol"], cwd=ROOT)
    assert os.path.isfile(os.path.join(ROOT, "dist", "ePYS_IDS_Allplan2026_%s.zip" % SURUM))


def _pyp(paket_dizini):
    return ET.parse(str(paket_dizini / "e-PYS IDS Kontrol.pyp")).getroot()


def test_palet_basliginda_surum(paket_dizini):
    r = _pyp(paket_dizini)
    assert r.find("Script/Title").text == "e-PYS IDS Kontrol (%s)" % SURUM


def test_satir_adlari_benzersiz(paket_dizini):
    """R12: Allplan aynı Text'li Row'ları tek satırda birleştiriyordu."""
    rows = [p.findtext("Text") for p in _pyp(paket_dizini).iter("Parameter") if p.findtext("ValueType") == "Row"
            and p.findtext("Value") == "OVERALL"]
    tekrar = [t for t, n in collections.Counter(rows).items() if n > 1]
    assert rows and not tekrar, tekrar


def test_parametre_adlari_benzersiz(paket_dizini):
    ad = [p.findtext("Name") for p in _pyp(paket_dizini).iter("Parameter")]
    tekrar = [t for t, n in collections.Counter(ad).items() if n > 1]
    assert not tekrar, tekrar


def test_islem_acilir_liste(paket_dizini):
    """R12: Expander içindeki RadioButtonGroup Allplan'da görünmüyordu; İşlem açılır liste olmalı."""
    p = {x.findtext("Name"): x for x in _pyp(paket_dizini).iter("Parameter")}
    assert p["NY_Islem"].findtext("ValueType") == "StringComboBox"
    assert "Nitelik sil" in p["NY_Islem"].findtext("ValueList")
