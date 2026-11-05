import os
import sys
from xml.sax.saxutils import escape as E

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SURUM = open(os.path.join(ROOT, 'VERSION'), encoding='utf-8').read().strip()      # ör. R21
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'dist', 'e-PYS IDS Kontrol.pyp')
L=[]
def p(name,text,vtype,value=None,extra='',vis=None,en=None):
    s='<Parameter><Name>%s</Name><Text>%s</Text>'%(name,E(text))
    if value is not None: s+='<Value>%s</Value>'%E(str(value))
    s+='<ValueType>%s</ValueType>%s'%(vtype,extra)
    if vis: s+='<Visible>%s</Visible>'%E(vis)
    if en is not None: s+='<Enable>%s</Enable>'%en
    return s+'</Parameter>'
def group(name,text,vtype,children,vis=None,extra=''):
    s='<Parameter><Name>%s</Name><Text>%s</Text>%s<ValueType>%s</ValueType>'%(name,E(text),extra,vtype)
    if vis: s+='<Visible>%s</Visible>'%E(vis)
    return s+'<Parameters>'+''.join(children)+'</Parameters></Parameter>'
def radio(name,text,val,opts,vis=None):
    return group(name,text,'RadioButtonGroup',[p(name+'_%d'%v,t,'RadioButton',v) for v,t in opts],vis,'<Value>%d</Value>'%val)
def combo(name,text,val,lst,vis=None):
    return p(name,text,'StringComboBox',val,'<ValueList>%s</ValueList>'%E(lst),vis)
def cb(name,text,val=True,vis=None): return p(name,text,'CheckBox',val,vis=vis)
def st(name,text,val='',vis=None,en=None): return p(name,text,'String',val,vis=vis,en=en)
def btn(name,text,ev,vis=None,label=''): return group('Row_'+name,label,'Row',[p(name,text,'Button',extra='<EventId>%s</EventId>'%ev)],vis)
def row(name,text,kids,vis=None): return group(name,text,'Row',kids,vis)
def sep(name,vis=None): return p(name,'','Separator',vis=vis)

I='Calisma == 1'; N='Calisma == 2'
params=[]
params.append(radio('Calisma','',1,[(1,'IFC dosyasını kontrol et ve düzelt'),(2,'ALLPLAN modeline nitelik yaz')]))
# ---------- IFC
params.append(group('ExpIfc','Dosyalar','Expander',[
  p('IfcDosya','IFC dosyası','String','', '<ValueDialog>OpenFileDialog</ValueDialog><FileFilter>IFC dosyaları(*.ifc)|*.ifc|</FileFilter><FileExtension>ifc</FileExtension><DefaultDirectories>usr|std</DefaultDirectories>'),
  radio('IfcIslem','İşlem',2,[(1,'Yalnız kontrol et (rapor)'),(2,'Kontrol et ve düzelt')]),
  st('CiktiIfc','Kaydedilecek IFC (boşsa: …_IDS.ifc)','',vis='IfcIslem == 2'),
  p('IdsDosya','IDS dosyası (boşsa: Bakanlığın son IDS’i)','String','', '<ValueDialog>OpenFileDialog</ValueDialog><FileFilter>IDS dosyaları(*.ids)|*.ids|</FileFilter><FileExtension>ids</FileExtension><DefaultDirectories>usr|std</DefaultDirectories>'),
  cb('RaporAc','Raporu Excel’de aç',True),
],vis=I))
params.append(group('ExpProje','Proje bilgileri','Expander',[
  st('ProjeKodu','Proje kodu (boşsa formdan)',''),
  st('BinaAdi','Bina adı (ör. MM-BNA-A_BLOK)',''),
  st('BinaUzunAd','Bina görünen adı (ör. A Blok)',''),
  combo('D_Disiplin','Disiplin (MM = Mimari)','MM','MM|IM|PY|ST|AL|ZE'),
  btn('BtnForm','Düzenle/Aç','EV_FORM',label='Proje Bilgi Formu (arsa, müellif, koordinat)'),
  st('FormDosya','Form dosyası','',en='False'),
],vis=I))
params.append(group('ExpP3','Allplan nitelikleri','Expander',[
  cb('P3_Esle','İsim, Açıklama, Kod yazısı → Tag, CSB_Mahal → Mahal adı aktar'),
  cb('P3_Temizle','AllplanAttributes setlerini sil'),
  btn('BtnEsleme','Düzenle','EV_ESLEME',label='Aktarma kurallarını düzenle (kural ekle/değiştir)'),
],vis=I))
params.append(group('ExpDuzelt','e-PYS Yönetmeliğe göre otomatik düzeltmeler','Expander',[
  cb('D_Tag','1. Kod yazısını Tag alanına yaz (boş olanlara)'),
  cb('D_Oto','2. Formda boş kalan bina/arsa bilgilerini modelden hesapla'),
  cb('D_Gdc','3. Giydirme cephe tiriz/travers ← giydirme cephe (dış eleman, Kod yazısı, malzeme)'),
  cb('D_Predef','4. Boş eleman tipini doldur (PredefinedType → USERDEFINED)'),
  cb('D_Ad','5. Eleman isimlerini Ek-5 biçimine değiştir (MM-KAP-…)'),
  cb('D_Sinif','6. Yanlış IFC sınıfını düzelt (TML → temel, BAC → baca)'),
  cb('D_MahalNo','7. Mahal numarasına eksik kat önekini ekle (K01_…)'),
  cb('D_Kaplama','8. Mahal kaplamaları (Pset_SpaceCoveringRequirements)'),
  cb('D_Kat','9. Kat kotu ve kat net alanını otomatik hesapla'),
  cb('D_Bina','10. Bina ve arsa adını, kat sayısını ve alanlarını otomatik hesapla'),
  cb('D_Adres','11. Bina ve arsa adresini doldur (formda yoksa Allplan’dan)'),
  cb('D_Zon','12. Daire (zon) bilgilerini doldur'),
  cb('D_Kacis','13. Merdiven FireExit ← Acil Çıkış'),
  cb('D_Dis','14. Kapı, pencere ve çatıya dış eleman bilgisi ver'),
  cb('D_Yangin','15. Yangın dayanımını dakikaya çevir (F120 → 120)'),
],vis=I+' and IfcIslem == 2'))
params.append(btn('BtnCalistir','▶ Çalıştır','EV_CALISTIR',vis=I,label='IFC kontrolünü başlat'))
# ---------- Nitelik
W=lambda n:'<WidthInRow>%d</WidthInRow>'%n
def tx(name,val,w): return p(name,'','Text',val,W(w))
def cbw(name,val=True): return p(name,'','CheckBox',val,W(8))
def orow(name,kids,vis=None): return group(name,'Satır '+name,'Row',kids,vis,'<Value>OVERALL</Value>')  # benzersiz Text: Allplan aynı adlı satırları birleştiriyor
_ri=[0]
def kat_row(pairs):
    _ri[0]+=1; i=_ri[0]
    kids=[tx('TxtLd%d'%i,'',2)]
    for prm,lbl in pairs:
        kids+=[cbw(prm),tx('Txt'+prm,lbl,40)]
    if len(pairs)==1:
        kids+=[tx('TxtDlg%da'%i,'',8),tx('TxtDlg%db'%i,'',40)]
    return orow('RowKat%d'%i,kids)
def grp_row(prm,lbl):
    _ri[0]+=1; i=_ri[0]
    return orow('RowGrp%d'%i,[tx('TxtLd%d'%i,'',2),cbw(prm),tx('Txt'+prm,lbl,88)])
def pairs(lst): return [lst[i:i+2] for i in range(0,len(lst),2)]
ISL='Nitelik yaz|Önce dene (yazmadan rapor ver)|Nitelik sil|Yalnız kontrol et (rapor)'
params.append(group('ExpIslem','İşlem','Expander',[
  combo('NY_Islem','İşlem','Nitelik yaz',ISL),
  combo('NY_Dolu','Nitelik doluysa','Dokunma, yalnız boşlara yaz','Dokunma, yalnız boşlara yaz|Üzerine yaz',
        vis='NY_Islem != "Yalnız kontrol et (rapor)" and NY_Islem != "Nitelik sil"'),
  p('NY_SilBilgi','','Text','İşaretli nitelikler seçilen elemanlardan silinir (değer boşaltılır)',vis='NY_Islem == "Nitelik sil"'),
  p('NY_Bilgi','','Text','Elemanları seçin (pencereyle toplu seçim olur). ESC: çıkış'),
],vis=N))
STA=[('CatTemel','Temel'),('CatKolon','Kolon'),('CatKiris','Kiriş'),('CatDoseme','Döşeme'),('CatMerdiven','Merdiven')]
MIM=[('CatDuvar','Duvar'),('CatCatiOrtu','Çatı Örtüsü'),('CatBaca','Baca'),('CatCatiPencere','Çatı Penceresi'),
     ('CatOda','Oda'),('CatKapi','Kapı'),('CatKorkuluk','Korkuluk'),('CatPencere','Pencere'),('CatGiydirme','Giydirme Cephe')]
KPL=[('CatDuvarKpl','Duvar Kaplaması'),('CatTavan','Tavan Kaplaması'),('CatDosemeKpl','Döşeme Kaplaması'),('CatSupurgelik','Süpürgelik')]
kk=[grp_row('CatGrupStatik','Statik – Tümü')]+[kat_row(x) for x in pairs(STA)]
kk+=[sep('SepKat1'),grp_row('CatGrupMimari','Mimari – Tümü')]+[kat_row(x) for x in pairs(MIM)]
kk+=[combo('KapiPencereHedef','Kapı / Pencere: nitelik yazılacak yer','Boşluk + ParaObje','Boşluk + ParaObje|Boşluk|ParaObje')]
kk+=[sep('SepKat2'),grp_row('CatGrupKaplama','Kaplama (IfcCovering) – Tümü')]+[kat_row(x) for x in pairs(KPL)]
kk+=[orow('RowKplNot',[tx('TxtLdKplNot','',2),tx('TxtKplNot','Oda seçilince içindeki kaplamalar da alınır',98)])]
kk+=[sep('SepKat3'),grp_row('CatTumu','Tümü')]
params.append(group('ExpKat','Elemanlar','Expander',kk,vis=N))
A='NY_Islem != "Yalnız kontrol et (rapor)"'
params.append(group('ExpIds','Yazılacak nitelikler','Expander',[
  cb('Y_Isim','İsim (Ek-5 biçiminde)',False),
  combo('Disiplin','   Disiplin','Otomatik','Otomatik|MM|IM|PY|ST|AL|ZE',vis='Y_Isim == True'),
  st('IsimSablon','   Açıklama ({MALZEME} = malzeme, {MEVCUT} = mevcut ad)','{MALZEME}',vis='Y_Isim == True'),
  cb('Ascii','   Türkçe harfleri çevir (Ş→S)',True,vis='Y_Isim == True'),
  cb('BuyukHarf','   Büyük harf',True,vis='Y_Isim == True'),
  row('RowYangin','Yangın dayanımı (dk)',[cb('Y_Yangin','',False),combo('Yangin','','120','30|60|90|120|180|240')]),
  row('RowDis','Dış eleman',[cb('Y_Dis','',False),combo('Dis','','Evet','Evet|Hayır')]),
  row('RowTas','Taşıyıcı',[cb('Y_Tasiyici','',False),combo('Tasiyici','','Evet','Evet|Hayır')]),
  row('RowKacis','Kaçış yolu / Acil çıkış',[cb('Y_Kacis','',False),combo('Kacis','','Hayır','Evet|Hayır')]),
  row('RowMalz','Malzeme (ör. Beton_C30)',[cb('Y_Malzeme','',False),st('Malzeme','','Beton_C30')]),
  row('RowObje','IFC obje kategorisi',[cb('Y_ObjeKat','',False),st('ObjeKat','','')]),
],vis=N+' and '+A))
params.append(group('ExpSerbest','Diğer nitelikler (listeden seç)','Expander',[
  p('Serbest','Nitelikler','AttributeIdValue','[]','<ValueDialog>AttributeSelectionInsert</ValueDialog>'),
],vis=N+' and '+A))
params.append(group('ExpAdlar','Allplan nitelik adları (gerekmedikçe değiştirmeyin)','Expander',[
  st('N_Isim','İsim','İsim|Name'),
  st('N_Kod','Kod yazısı (Tag)','Kod yazısı'),
  st('N_Yangin','Yangın dayanımı','Yangın Dayanım Sınıfı|Yangın dayanım sınıfı'),
  st('N_Dis','Dış eleman','Dış Yapı Elemanı'),
  st('N_Tasiyici','Taşıyıcı','Statik_taşıyıcı|Statik taşıyıcı'),
  st('N_Kacis','Kaçış yolu (kapı)','Kaçış Yolu'),
  st('N_AcilCikis','Acil çıkış (merdiven)','Acil Çıkış|Kaçış Yolu'),
  st('N_Malzeme','Malzeme','Malzeme'),
  st('N_ObjeKat','IFC obje kategorisi','IFC obje kategorisi'),
  st('N_MahalNo','Mahal no','CSB_Mahal'),
  btn('BtnDogrula','Doğrula','EV_NITELIK_DOGRULA',label='Nitelik adlarını doğrula'),
],vis=N,extra='<Value>True</Value>'))
params.append(group('ExpSonuc','Sonuç','Expander',[
  cb('RaporYaz','Excel rapor oluştur',True,vis=N),
  cb('OzetGoster','İşlemden sonra özet göster',True,vis=N),
  st('SonAtama','Son nitelik yazma','',vis=N,en='False'),
  st('SonSonuc','Son IFC sonucu','',vis=I,en='False'),
  st('SonRapor','Rapor dosyası','',en='False'),
  btn('BtnRapor','Aç','EV_RAPOR_AC',label='Son rapor'),
]))
consts=''.join('<Constant><Name>%s</Name><Value>%d</Value><ValueType>Integer</ValueType></Constant>'%(n,1000+i)
               for i,n in enumerate(['EV_CALISTIR','EV_VARSAYILAN','EV_RAPOR_AC','EV_NITELIK_DOGRULA','EV_FORM','EV_ESLEME']))
X=('<?xml version="1.0" encoding="utf-8"?>\n<Element xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
 'xsi:noNamespaceSchemaLocation="https://pythonparts.allplan.com/2026/schemas/PythonPart.xsd">'
 '<Script><Name>ALUPLAN\\ePYS_IDS.py</Name><Title>e-PYS IDS Kontrol (%s)</Title><Version>%s.0</Version>' % (SURUM, SURUM.lstrip('R'))+
 '<ShowFavoriteButtons>True</ShowFavoriteButtons></Script>'
 '<Constants>'+consts+'</Constants>'
 '<Page><Name>Page1</Name><Text>e-PYS IDS Kontrol (%s)</Text><Parameters>' % SURUM +''+''.join(params)+'</Parameters></Page></Element>')
import xml.dom.minidom
pretty=xml.dom.minidom.parseString(X.encode('utf-8')).toprettyxml(indent='  ',encoding='utf-8')
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT,'wb').write(pretty)
print('ok',len(pretty))
