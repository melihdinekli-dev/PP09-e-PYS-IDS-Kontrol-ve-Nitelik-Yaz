import openpyxl,re,pprint
import sys
# Eski yöntem: bakanlığın IDS Excel listesinden rules_gen.py üretir. R3'ten beri .ids doğrudan okunuyor.
wb=openpyxl.load_workbook(sys.argv[1], data_only=True)
ws=wb['IDS Kuralları (bu model)']
specs={}; order=[]
for r in ws.iter_rows(min_row=2,values_only=True):
    spec,app,kind,nm,zor,dt,val,desc,_=r
    if not spec: continue
    if spec not in specs:
        m=re.match(r'(IFC[A-Z]+)\s*(?:\+ Name Desen: (.+))?',app)
        specs[spec]={'ad':spec,'siniflar':[m.group(1)],'ad_deseni':(m.group(2) or '').strip() or None,
                     'zorunlu_varlik':'en az 1' in app,'gereksinimler':[]}
        order.append(spec)
    g={'tur':{'IFC niteliği':'nitelik','Özellik (Pset)':'ozellik','Malzeme':'malzeme'}[kind],
       'zorunlu': zor=='Zorunlu'}
    if g['tur']=='nitelik': g['ad']=nm
    if g['tur']=='ozellik':
        ps,pr=nm.split('.',1); g['pset']=ps; g['ad']=pr
    if dt:
        g['tip']=re.search(r'\((Ifc\w+)\)',dt).group(1).upper()
    if val:
        if val.startswith('Desen: '): g['desen']=val[7:]
        elif val.startswith('Şunlardan biri: '): g['secenek']=[x.strip() for x in val[16:].split('|')]
    if desc: g['aciklama']=desc
    specs[spec]['gereksinimler'].append(g)
rules=[specs[s] for s in order]
ws=wb['EK-5 Ad Kodları']
codes=[]
for r in ws.iter_rows(min_row=2,values_only=True):
    if r[0] and r[0].startswith('Ifc'):
        codes.append((r[0].upper(),r[3],r[2],r[1]))
with open('rules_gen.py','w',encoding='utf-8') as f:
    f.write('# -*- coding: utf-8 -*-\n# Otomatik üretildi: IDS_Hata_Raporu_EPYS_Allplan_R2.xlsx (EPYS_IDS v0.1.3)\n')
    f.write('IDS_KURALLARI = ');f.write(pprint.pformat(rules,width=120,sort_dicts=False));f.write('\n\n')
    f.write('# (IFC sınıfı, kategori kodu, IDS ad deseni, IDS kural adı)\nEK5_AD_KODLARI = ');f.write(pprint.pformat(codes,width=140));f.write('\n')
print(len(rules),len(codes))
