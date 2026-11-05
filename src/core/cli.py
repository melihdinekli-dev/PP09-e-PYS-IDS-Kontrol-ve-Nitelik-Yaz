# -*- coding: utf-8 -*-
# Telif Hakkı (c) 2026 ALUPLAN – Allplan Türkiye Distribütörü. Tüm hakları saklıdır.
# Kapalı kaynak, tescilli yazılım – bkz. LICENSE. Yetkisiz kopyalama ve dağıtım yasaktır.
"""Komut satırı: python ePYS_IDS_core.py model.ifc [--duzelt] (tools/merge.py bu dosyayı çekirdeğin sonuna ekler)."""
import sys

from engine import calistir


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="e-PYS IDS Kontrol (PP09) – ALUPLAN")
    ap.add_argument("ifc")
    ap.add_argument("--duzelt", action="store_true", help="IFC'yi düzeltip <ad>_IDS.ifc yaz")
    ap.add_argument("--varsayilan", help="Varsayılan değerler dosyası (.txt, ileri kullanıcı)")
    ap.add_argument("--form", help="e-PYS Proje Bilgi Formu (.xlsx)")
    ap.add_argument("--cikti", help="Düzeltilmiş IFC yolu")
    ap.add_argument("--rapor", help="Rapor .xlsx yolu")
    ap.add_argument("--bina-adi", default="")
    ap.add_argument("--bina-uzun-ad", default="")
    ap.add_argument("--proje-kodu", default="")
    ap.add_argument("--disiplin", default="MM")
    ap.add_argument("--ids", help="IDS dosyası (varsayılan: yanındaki ePYS_IDS_Kurallar.ids)")
    a = ap.parse_args(argv)
    ayar = {"bina_adi": a.bina_adi, "bina_uzun_ad": a.bina_uzun_ad, "proje_adi": a.proje_kodu, "disiplin": a.disiplin}
    r = calistir(a.ifc, a.duzelt, ayar, a.varsayilan, a.cikti, a.rapor, ids_yolu=a.ids, form_dosyasi=a.form)
    print("Önce %d → sonra %d hatalı kontrol; %d düzeltme; rapor: %s" % (r["once"], r["sonra"], r["duzeltme"], r["rapor"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
