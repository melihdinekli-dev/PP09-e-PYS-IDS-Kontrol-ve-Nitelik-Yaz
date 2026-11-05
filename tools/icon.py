# Telif Hakkı (c) 2026 ALUPLAN – Allplan Türkiye Distribütörü. Tüm hakları saklıdır.
# Kapalı kaynak, tescilli yazılım – bkz. LICENSE. Yetkisiz kopyalama ve dağıtım yasaktır.
from PIL import Image, ImageDraw, ImageFont
S=128; im=Image.new('RGBA',(S,S),(0,0,0,0)); d=ImageDraw.Draw(im)
# document
d.rounded_rectangle([18,10,92,112],8,fill=(255,255,255,255),outline=(31,56,100,255),width=6)
for y in (34,52,70): d.line([32,y,78,y],fill=(31,56,100,255),width=6)
# check badge
d.ellipse([60,58,122,120],fill=(237,125,49,255),outline=(255,255,255,255),width=4)
d.line([74,90,87,103],fill=(255,255,255,255),width=9); d.line([86,103,108,74],fill=(255,255,255,255),width=9)
try: f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',22)
except: f=None
d.text((26,84),'IDS',fill=(31,56,100,255),font=f)
im.resize((64,64),Image.LANCZOS).save('build/e-PYS IDS Kontrol.png')
im.save('icon_big.png')
