import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, 'src', 'core')
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'dist', 'ePYS_IDS_core.py')
SURUM = open(os.path.join(ROOT, 'VERSION'), encoding='utf-8').read().strip()
parts=['ifc_step.py','ifc_model.py','ids_reader.py','checker.py','fixer.py','report.py','engine.py']
head='''# -*- coding: utf-8 -*-
"""e-PYS IDS Kontrol ve Nitelik Atama – çekirdek (PP09) – ALUPLAN

Allplan dışında da çalışır (yalnız Python standart kütüphanesi):
  python ePYS_IDS_core.py model.ifc               -> denetim raporu (xlsx)
  python ePYS_IDS_core.py model.ifc --duzelt      -> <ad>_IDS.ifc + rapor
  python ePYS_IDS_core.py model.ifc --duzelt --form ePYS_Proje_Bilgi_Formu.xlsx
"""
import os
import re
import sys
import uuid
import zipfile
import datetime
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

SURUM = "%s"
'''
out=[head % SURUM]
for p in parts:
    s=open(os.path.join(CORE,p),encoding='utf-8').read()
    s=re.sub(r'^# -\*- coding: utf-8 -\*-\n','',s)
    s=re.sub(r'^""".*?"""\n','',s,flags=re.S)
    s=re.sub(r'^(import (re|uuid|zipfile|datetime|os)|from (ifc_step|ifc_model|checker|fixer|report|rules_gen|ids_reader) import .*|from xml\.sax\.saxutils import escape|import xml\.etree\.ElementTree as ET)\n','',s,flags=re.M)
    s=re.sub(r'^    from (ifc_model|checker|fixer|report|ids_reader) import .*\n','',s,flags=re.M)
    s=s.replace('        from rules_gen import IDS_KURALLARI as kurallar, EK5_AD_KODLARI as ek5\n','        from ePYS_IDS_kurallar import IDS_KURALLARI as kurallar, EK5_AD_KODLARI as ek5\n')
    out.append('\n# '+'='*74+'\n# '+p+'\n# '+'='*74+'\n'+s)
tail=open(os.path.join(CORE,'cli.py'),encoding='utf-8').read()
tail=tail[tail.index('def main('):]   # başlık ve importlar birleşik dosyada zaten var
out.append('\n\n'+tail)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT,'w',encoding='utf-8').write('\n'.join(out))
