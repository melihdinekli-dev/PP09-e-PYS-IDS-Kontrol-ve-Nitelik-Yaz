# -*- coding: utf-8 -*-
"""PP09 e-PYS IDS Kontrol – paket üretimi.

    python build.py            -> dist/ePYS_IDS_Allplan2026_<VERSION>.zip
    python build.py --kontrol  -> paket + içerik kontrolü

Sürüm yalnız VERSION dosyasından okunur (ör. R21); palet başlığı, script ve çekirdek bu değeri alır.
"""
import os
import re
import shutil
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist")
SURUM = open(os.path.join(ROOT, "VERSION"), encoding="utf-8").read().strip()
PAKET = "ePYS_IDS_Allplan2026_%s" % SURUM
STAGE = os.path.join(DIST, PAKET)
SCR = os.path.join(STAGE, "PythonPartsScripts", "ALUPLAN")
LIB = os.path.join(STAGE, "Library", "ALUPLAN")

BEKLENEN = [
    "ePYS_IDS_KURULUM.md",
    "PythonPartsScripts/ALUPLAN/ePYS_IDS.py",
    "PythonPartsScripts/ALUPLAN/ePYS_IDS_core.py",
    "PythonPartsScripts/ALUPLAN/ePYS_IDS_IfcDuzenle.py",
    "PythonPartsScripts/ALUPLAN/ePYS_IDS_Kurallar.ids",
    "PythonPartsScripts/ALUPLAN/ePYS_IDS_Eslestirme.txt",
    "PythonPartsScripts/ALUPLAN/ePYS_IDS_Form.xlsx",
    "Library/ALUPLAN/e-PYS IDS Kontrol.pyp",
    "Library/ALUPLAN/e-PYS IDS Kontrol.png",
]


def run(*cmd):
    subprocess.check_call([sys.executable] + list(cmd), cwd=ROOT)


def main():
    if not re.fullmatch(r"R\d+", SURUM):
        sys.exit("VERSION 'R<sayı>' biçiminde olmalı: %r" % SURUM)
    shutil.rmtree(STAGE, ignore_errors=True)
    os.makedirs(SCR)
    os.makedirs(LIB)
    # 1) çekirdek: src/core -> tek dosya (Allplan'da tek modül yüklenir)
    run("tools/merge.py", os.path.join(SCR, "ePYS_IDS_core.py"))
    # 2) Allplan sarmalayıcı (sürüm damgası VERSION'dan)
    w = open(os.path.join(ROOT, "src", "allplan", "ePYS_IDS.py"), encoding="utf-8").read()
    w = re.sub(r'^SURUM = "R\d+"', 'SURUM = "%s"' % SURUM, w, count=1, flags=re.M)
    with open(os.path.join(SCR, "ePYS_IDS.py"), "w", encoding="utf-8", newline="\n") as f:
        f.write(w)
    shutil.copy(os.path.join(ROOT, "src", "allplan", "ePYS_IDS_IfcDuzenle.py"), SCR)
    for f in ("ePYS_IDS_Kurallar.ids", "ePYS_IDS_Eslestirme.txt"):
        shutil.copy(os.path.join(ROOT, "resources", f), SCR)
    # 3) Proje Bilgi Formu şablonu ve palet
    run("tools/gen_form.py", os.path.join(SCR, "ePYS_IDS_Form.xlsx"))
    run("tools/gen_pyp.py", os.path.join(LIB, "e-PYS IDS Kontrol.pyp"))
    shutil.copy(os.path.join(ROOT, "resources", "e-PYS IDS Kontrol.png"), LIB)
    shutil.copy(os.path.join(ROOT, "docs", "KURULUM.md"), os.path.join(STAGE, "ePYS_IDS_KURULUM.md"))
    # 4) zip
    z = os.path.join(DIST, PAKET + ".zip")
    if os.path.exists(z):
        os.remove(z)
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for d, _, fs in os.walk(STAGE):
            for f in sorted(fs):
                p = os.path.join(d, f)
                zf.write(p, os.path.relpath(p, STAGE).replace(os.sep, "/"))
    if "--kontrol" in sys.argv:
        kontrol(z)
    print(z)


def kontrol(z):
    with zipfile.ZipFile(z) as zf:
        ad = sorted(zf.namelist())
        eksik = [b for b in BEKLENEN if b not in ad]
        fazla = [a for a in ad if a not in BEKLENEN]
        if eksik or fazla:
            sys.exit("Paket içeriği hatalı. Eksik: %s Fazla: %s" % (eksik, fazla))
        pyp = zf.read("Library/ALUPLAN/e-PYS IDS Kontrol.pyp").decode("utf-8")
        if "e-PYS IDS Kontrol (%s)" % SURUM not in pyp:
            sys.exit("Palet başlığında sürüm yok")
        for f in ("ePYS_IDS.py", "ePYS_IDS_core.py"):
            if ('SURUM = "%s"' % SURUM) not in zf.read("PythonPartsScripts/ALUPLAN/" + f).decode("utf-8"):
                sys.exit("%s içinde SURUM %s değil" % (f, SURUM))
    print("Paket kontrolü tamam:", len(BEKLENEN), "dosya")


if __name__ == "__main__":
    main()
