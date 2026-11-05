# -*- coding: utf-8 -*-
"""Ortak test ayarları: kaynak yolları, Allplan taklidi ve derlenmiş çekirdek."""
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, "src", "core")
IDS = os.path.join(ROOT, "resources", "ePYS_IDS_Kurallar.ids")
MINI = os.path.join(ROOT, "tests", "fixtures", "mini.ifc")

if CORE not in sys.path:
    sys.path.insert(0, CORE)


@pytest.fixture(scope="session")
def paket_dizini(tmp_path_factory):
    """src/core'u tek dosyaya birleştirip (ePYS_IDS_core.py) Allplan dizin düzenini kurar."""
    d = tmp_path_factory.mktemp("ALUPLAN")
    subprocess.check_call([sys.executable, os.path.join(ROOT, "tools", "merge.py"), str(d / "ePYS_IDS_core.py")])
    subprocess.check_call([sys.executable, os.path.join(ROOT, "tools", "gen_pyp.py"), str(d / "e-PYS IDS Kontrol.pyp")])
    import shutil
    shutil.copy(os.path.join(ROOT, "src", "allplan", "ePYS_IDS.py"), d)
    shutil.copy(os.path.join(ROOT, "src", "allplan", "ePYS_IDS_IfcDuzenle.py"), d)
    shutil.copy(IDS, d)
    return d
