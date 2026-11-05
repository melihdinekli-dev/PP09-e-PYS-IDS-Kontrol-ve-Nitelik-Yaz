# -*- coding: utf-8 -*-
"""tools/kur.py: Allplan'a kurulum, yedekleme ve geri alma (geçici klasörde)."""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KUR = os.path.join(ROOT, "tools", "kur.py")
SURUM = open(os.path.join(ROOT, "VERSION"), encoding="utf-8").read().strip()


def _calistir(hedef, yedek, *ek):
    env = dict(os.environ, EPYS_YEDEK=str(yedek))
    return subprocess.run([sys.executable, KUR, "--hedef", str(hedef)] + list(ek), env=env,
                          capture_output=True, text=True, check=True).stdout


def test_kur_yedekle_geri_al(tmp_path):
    hedef, yedek = tmp_path / "Usr" / "Local", tmp_path / "yedek"
    scr = hedef / "PythonPartsScripts" / "ALUPLAN"
    scr.mkdir(parents=True)
    (scr / "ePYS_IDS.py").write_text('SURUM = "R10"\n', encoding="utf-8")
    (scr / "__pycache__").mkdir()
    (scr / "__pycache__" / "ePYS_IDS.cpython-313.pyc").write_bytes(b"x")
    (scr / "baska_arac.py").write_text("# dokunulmamalı", encoding="utf-8")

    out = _calistir(hedef, yedek)
    assert "R10 -> %s" % SURUM in out
    assert 'SURUM = "%s"' % SURUM in (scr / "ePYS_IDS.py").read_text(encoding="utf-8")
    assert (hedef / "Library" / "ALUPLAN" / "e-PYS IDS Kontrol.pyp").is_file()
    assert not (scr / "__pycache__" / "ePYS_IDS.cpython-313.pyc").exists()
    assert (scr / "baska_arac.py").read_text(encoding="utf-8") == "# dokunulmamalı"
    yedekler = list(yedek.iterdir())
    assert len(yedekler) == 1 and yedekler[0].name.endswith("_R10")

    _calistir(hedef, yedek, "--geri-al")
    assert (scr / "ePYS_IDS.py").read_text(encoding="utf-8") == 'SURUM = "R10"\n'


def test_hedef_yoksa_durur(tmp_path):
    r = subprocess.run([sys.executable, KUR, "--hedef", str(tmp_path / "yok")], capture_output=True, text=True)
    assert r.returncode != 0 and "bulunamadı" in (r.stderr + r.stdout)
