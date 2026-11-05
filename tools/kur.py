# -*- coding: utf-8 -*-
# Telif Hakkı (c) 2026 ALUPLAN – Allplan Türkiye Distribütörü. Tüm hakları saklıdır.
# Kapalı kaynak, tescilli yazılım – bkz. LICENSE. Yetkisiz kopyalama ve dağıtım yasaktır.
"""PP09'u Allplan'a kurar (geliştirici bilgisayarı).

    python tools/kur.py                 paketi derler, mevcut PP09 dosyalarını yedekler, yenilerini kopyalar
    python tools/kur.py --geri-al       son yedeği geri yükler
    python tools/kur.py --hedef <yol>   Allplan Usr\\Local klasörü (varsayılan aşağıda)

Allplan Usr\\Local klasörü sırasıyla: --hedef, ALLPLAN_USR_LOCAL ortam değişkeni,
%USERPROFILE%\\Documents\\Nemetschek\\Allplan\\2026\\Usr\\Local.
Yedekler: %USERPROFILE%\\Documents\\e-PYS IDS Yedekler\\<tarih>_<sürüm>\\ (Allplan kütüphanesinin dışında,
böylece eski .pyp kütüphanede görünmez).
Allplan açıkken kurulabilir; değişiklik Allplan yeniden başlatılınca görünür.
"""
import argparse
import datetime
import glob
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import build  # noqa: E402

# Paketteki dosyalar (Allplan'a kopyalananlar). KURULUM.md Allplan'a gitmez.
DOSYALAR = [b for b in build.BEKLENEN if b.startswith(("PythonPartsScripts/", "Library/"))]


def varsayilan_hedef():
    return os.environ.get("ALLPLAN_USR_LOCAL") or os.path.join(
        os.path.expanduser("~"), "Documents", "Nemetschek", "Allplan", "2026", "Usr", "Local")


def yedek_kok():
    return os.environ.get("EPYS_YEDEK") or os.path.join(os.path.expanduser("~"), "Documents", "e-PYS IDS Yedekler")


def kurulu_surum(hedef):
    p = os.path.join(hedef, "PythonPartsScripts", "ALUPLAN", "ePYS_IDS.py")
    try:
        for satir in open(p, encoding="utf-8"):
            if satir.startswith("SURUM = "):
                return satir.split('"')[1]
    except OSError:
        pass
    return None


def pycache_temizle(hedef):
    for p in glob.glob(os.path.join(hedef, "PythonPartsScripts", "ALUPLAN", "__pycache__", "ePYS_IDS*.pyc")):
        try:
            os.remove(p)
        except OSError:
            pass


def yedekle(hedef):
    eski = kurulu_surum(hedef)
    var = [d for d in DOSYALAR if os.path.isfile(os.path.join(hedef, d))]
    if not var:
        return None
    ad = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + (eski or "bilinmiyor")
    kok = os.path.join(yedek_kok(), ad)
    for d in var:
        hedef_yol = os.path.join(kok, d)
        os.makedirs(os.path.dirname(hedef_yol), exist_ok=True)
        shutil.copy2(os.path.join(hedef, d), hedef_yol)
    return kok


def kur(hedef):
    if not os.path.isdir(hedef):
        sys.exit("Allplan Usr\\Local klasörü bulunamadı: %s\n--hedef ile verin." % hedef)
    subprocess.check_call([sys.executable, os.path.join(ROOT, "build.py"), "--kontrol"], cwd=ROOT)
    kaynak = build.STAGE
    eski = kurulu_surum(hedef)
    yedek = yedekle(hedef)
    for d in DOSYALAR:
        h = os.path.join(hedef, d)
        os.makedirs(os.path.dirname(h), exist_ok=True)
        shutil.copy2(os.path.join(kaynak, d), h)
    pycache_temizle(hedef)
    print("Kuruldu: %s -> %s" % (eski or "(yoktu)", build.SURUM))
    print("Hedef  : %s" % hedef)
    if yedek:
        print("Yedek  : %s" % yedek)
    print("Allplan'ı yeniden başlatın; palet başlığında 'e-PYS IDS Kontrol (%s)' görünmeli." % build.SURUM)


def geri_al(hedef):
    yedekler = sorted(glob.glob(os.path.join(yedek_kok(), "*")))
    if not yedekler:
        sys.exit("Yedek bulunamadı: %s" % yedek_kok())
    son = yedekler[-1]
    for d in DOSYALAR:
        y = os.path.join(son, d)
        if os.path.isfile(y):
            h = os.path.join(hedef, d)
            os.makedirs(os.path.dirname(h), exist_ok=True)
            shutil.copy2(y, h)
    pycache_temizle(hedef)
    print("Geri yüklendi: %s (%s)" % (os.path.basename(son), kurulu_surum(hedef)))


def main(argv=None):
    ap = argparse.ArgumentParser(description="PP09'u Allplan'a kur / geri al")
    ap.add_argument("--hedef", default=varsayilan_hedef(), help="Allplan Usr\\Local klasörü")
    ap.add_argument("--geri-al", action="store_true", help="son yedeği geri yükle")
    a = ap.parse_args(argv)
    geri_al(a.hedef) if a.geri_al else kur(a.hedef)


if __name__ == "__main__":
    main()
