# -*- coding: utf-8 -*-
"""e-PYS Proje Bilgi Formu şablonu (build/ePYS_Proje_Bilgi_Formu.xlsx) – alanlar engine.FORM_ALANLAR'dan."""
import os
import sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src', 'core'))
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, Protection
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import FormulaRule
from openpyxl.utils import get_column_letter
from engine import FORM_ALANLAR, FORM_LISTELER, ORNEK_KONTROL

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'dist', 'ePYS_IDS_Form.xlsx')
NAVY = '1F3864'
th = Side(style='thin', color='BFBFBF')
B = Border(left=th, right=th, top=th, bottom=th)
BOLUM_RENK = {'PROJE': 'DDEBF7', 'MÜELLİF': 'E2EFDA', 'ARSA': 'FFF2CC', 'BİNA': 'FCE4D6', 'KOORDİNAT': 'EDE7F6',
              'ELEMANLAR': 'E7E6E6'}
DURUM = {'Z': 'Zorunlu', 'O': 'Otomatik bulunur', 'S': 'İsteğe bağlı'}

wb = openpyxl.Workbook()
ws = wb.active
ws.title = 'Form'
li = wb.create_sheet('Listeler')
nas = wb.create_sheet('Nasıl kullanılır')

# listeler
lref = {}
for i, (ad, vals) in enumerate(FORM_LISTELER.items()):
    col = get_column_letter(i + 1)
    li.cell(1, i + 1, ad)
    for j, v in enumerate(vals):
        li.cell(j + 2, i + 1, int(v) if ad == 'DAKIKA' else v)
    lref[ad] = "Listeler!$%s$2:$%s$%d" % (col, col, len(vals) + 1)
li.sheet_state = 'hidden'

ws['B1'] = 'e-PYS Proje Bilgi Formu'
ws['B1'].font = Font(bold=True, size=16, color=NAVY)
ws['B2'] = ("Bu bilgiler Allplan modelinde yok; e-PYS IDS kontrolü için zorunlu. Proje başına BİR KEZ doldurun. "
            "Yalnız sarı 'Değer' sütununa yazın. PP09 e-PYS IDS Kontrol 'Düzelt + denetle' bu formu okuyup IFC'ye yazar.")
ws['B2'].alignment = Alignment(wrap_text=True, vertical='top')
ws.merge_cells('B2:I2')
ws.row_dimensions[2].height = 34
ws['B3'] = 'Zorunlu alanlar:'
ws['B3'].font = Font(bold=True)
ws['B4'] = 'Kontrol edilecek:'
ws['B4'].font = Font(bold=True)

H = ['Anahtar', 'Bölüm', 'Soru', 'Değer', 'Birim / biçim', 'Örnek', 'Nereden bulunur', 'Gerekli mi?', 'Durum']
HR = 6
for c, h in enumerate(H, 1):
    x = ws.cell(HR, c, h)
    x.font = Font(bold=True, color='FFFFFF')
    x.fill = PatternFill('solid', fgColor=NAVY)
    x.alignment = Alignment(vertical='center', wrap_text=True)
    x.border = B

YEL = PatternFill('solid', fgColor='FFF9C4')
r = HR + 1
ilk = r
for (k, bol, soru, dur, tur, birim, ornek, nereden, liste) in FORM_ALANLAR:
    D = 'D%d' % r
    vals = [k, bol, soru, None, birim, ornek, nereden, DURUM[dur]]
    for c, v in enumerate(vals, 1):
        x = ws.cell(r, c, v)
        x.border = B
        x.alignment = Alignment(wrap_text=True, vertical='top')
        x.protection = Protection(locked=(c != 4))
    ws.cell(r, 2).fill = PatternFill('solid', fgColor=BOLUM_RENK.get(bol, 'FFFFFF'))
    ws.cell(r, 4).fill = YEL
    bos = 'IF(H%d="Zorunlu","✗ Boş – doldurun","○ Boş (otomatik / isteğe bağlı)")' % r
    if tur.startswith('sayi'):
        lo, hi = tur[5:-1].split(',')
        dv = DataValidation(type='decimal', operator='between', formula1=lo, formula2=hi, allow_blank=True,
                            showErrorMessage=True, errorTitle='Geçersiz değer',
                            error='%s: %s ile %s arasında bir sayı girin (%s). Ondalık için virgül kullanın.' % (soru, lo, hi, birim))
        # R15: yazı olarak girilen sayılar da (yapıştırma, '0,30' / '0.30') kabul edilir
        NV = ('IFERROR(VALUE(%s),IFERROR(VALUE(SUBSTITUTE(%s,",",".")),IFERROR(VALUE(SUBSTITUTE(%s,".",",")),"x")))'
              % (D, D, D))
        ok = 'AND(ISNUMBER(%s),%s>=%s,%s<=%s)' % (NV, NV, lo, NV, hi)
        hata = '"⚠ Sayı %s – %s olmalı"' % (lo.replace('.', ','), hi.replace('.', ','))
        ws.cell(r, 4).number_format = '0.00##'
    elif tur == 'liste':
        dv = DataValidation(type='list', formula1='=' + lref[liste], allow_blank=True, showErrorMessage=True,
                            errorTitle='Listeden seçin', error='Lütfen açılır listeden bir değer seçin.')
        ok = 'COUNTIF(%s,%s)>0' % (lref[liste], D)
        hata = '"⚠ Listeden seçin"'
    elif tur == 'kod':
        dv = DataValidation(type='textLength', operator='equal', formula1='13', allow_blank=True, showErrorMessage=True,
                            errorTitle='Proje kodu', error='Biçim: MM-PRJ- ve 6 büyük harf/rakam (örn. MM-PRJ-202645), toplam 13 karakter.')
        ok = 'AND(LEN(%s)=13,MID(%s,3,5)="-PRJ-",EXACT(%s,UPPER(%s)))' % (D, D, D, D)
        hata = '"⚠ Biçim: MM-PRJ-xxxxxx"'
        ws.cell(r, 4).number_format = '@'
    else:
        dv = None
        ok = 'LEN(TRIM(%s))>0' % D
        hata = '"⚠"'
        ws.cell(r, 4).number_format = '@'
    if dv is not None:
        ws.add_data_validation(dv)
        dv.add(D)
    if dv is None or tur == 'kod' or tur == 'liste':
        pass
    if dv is not None and tur != 'liste':
        dv.promptTitle = soru
        dv.prompt = ('%s – örnek: %s' % (birim, ornek))[:250]
        dv.showInputMessage = True
    if k in ORNEK_KONTROL:
        tamam = 'IF(SUBSTITUTE(TRIM(%s&""),".",",")=SUBSTITUTE(TRIM(F%d&""),".",","),"⚠ Örnek değer – gerçeğini yazın","✓ Tamam")' % (D, r)
    else:
        tamam = '"✓ Tamam"'
    ws.cell(r, 9, '=IF(%s="",%s,IF(%s,%s,%s))' % (D, bos, ok, tamam, hata)).border = B
    ws.cell(r, 9).protection = Protection(locked=True)
    r += 1
son = r - 1
ws['C3'] = '=COUNTIFS(H%d:H%d,"Zorunlu",I%d:I%d,"✓*")&" / "&COUNTIF(H%d:H%d,"Zorunlu")&" dolu"' % (ilk, son, ilk, son, ilk, son)
ws['C4'] = '=COUNTIF(I%d:I%d,"⚠*")&" değer hatalı"' % (ilk, son)
ws['C3'].font = Font(bold=True, color='C00000')
ws['C4'].font = Font(bold=True, color='C55A11')
rng = 'I%d:I%d' % (ilk, son)
ws.conditional_formatting.add(rng, FormulaRule(formula=['LEFT(I%d,1)="✓"' % ilk], fill=PatternFill('solid', fgColor='C6EFCE'), font=Font(color='006100')))
ws.conditional_formatting.add(rng, FormulaRule(formula=['LEFT(I%d,1)="✗"' % ilk], fill=PatternFill('solid', fgColor='FFC7CE'), font=Font(color='9C0006')))
ws.conditional_formatting.add(rng, FormulaRule(formula=['LEFT(I%d,1)="⚠"' % ilk], fill=PatternFill('solid', fgColor='FFEB9C'), font=Font(color='9C5700')))
ws.conditional_formatting.add(rng, FormulaRule(formula=['LEFT(I%d,1)="○"' % ilk], font=Font(color='808080')))
for col, wd in zip('ABCDEFGHI', [4, 12, 40, 30, 22, 26, 38, 16, 26]):
    ws.column_dimensions[col].width = wd
ws.column_dimensions['A'].hidden = True
ws.freeze_panes = 'D%d' % (HR + 1)
ws.protection.sheet = True
ws.protection.formatColumns = False
ws.protection.formatRows = False
ws.sheet_view.zoomScale = 100

adim = [
    "1) Bu form proje klasöründe durur (IFC dosyalarının yanında). Proje başına bir kez doldurulur; her yeni IFC teslimde aynı form kullanılır.",
    "2) Yalnız sarı 'Değer' sütununa yazın. Diğer sütunlar kilitlidir (yanlışlıkla bozulmaz).",
    "3) Listeli alanlarda hücreye tıklayıp oku kullanın. Sayılarda ondalık için virgül kullanın (0,30). Birimi yazmayın (m, m² …).",
    "4) 'Durum' sütunu: ✓ Tamam · ✗ Boş (zorunlu) · ⚠ Değer hatalı · ○ Boş (PP09 otomatik bulur ya da isteğe bağlı).",
    "5) 'Otomatik bulunur' alanları boş bırakabilirsiniz: PP09 modelden hesaplar (ada/parsel, alanlar, yükseklik, kullanım, yapım tekniği, giydirme cephe). Değer girerseniz sizin değeriniz kullanılır.",
    "6) Allplan → PP09 e-PYS IDS Kontrol → 'Düzelt + denetle'. Rapordaki Uyarılar sayfası formdaki boş/hatalı alanları da listeler.",
    "7) Formda girilen değer IFC'deki mevcut değerin yerine yazılır (ör. yanlış adres, müellif adı).",
]
nas['A1'] = 'e-PYS Proje Bilgi Formu – Nasıl kullanılır'
nas['A1'].font = Font(bold=True, size=14, color=NAVY)
for i, t in enumerate(adim):
    c = nas.cell(3 + i, 1, t)
    c.alignment = Alignment(wrap_text=True, vertical='top')
    nas.row_dimensions[3 + i].height = 34
nas.column_dimensions['A'].width = 120
wb.active = 0
wb.save(OUT)
print('form', OUT, son - ilk + 1, 'alan')
