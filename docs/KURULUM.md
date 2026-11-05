# PP09 e-PYS IDS Kontrol ve Nitelik Atama – Kurulum ve Kullanım (Allplan 2026) – R21

Bakanlığın IDS denetiminden önce modeli ve IFC'yi hazırlar. İki bölümü vardır. Paletin en üstündeki iki seçenekle bölüm değiştirilir.

1. **IFC dosyasını kontrol et ve düzelt**: Allplan'dan alınan IFC'yi bakanlığın **EPYS_IDS.ids** dosyasına göre denetler (161 kuralın tamamı, dosyadan okunur). Dosyada zaten bulunan bilgilerle eksikleri düzeltip `<ad>_IDS.ifc` yazar ve Excel rapor üretir. Allplan modeli değişmez.
2. **ALLPLAN modeline nitelik yaz**: Seçilen elemanlara IDS'in istediği nitelikleri tek seferde yazar (çoklu nitelik). Bilgi Paletinde eleman eleman girmek gerekmez. İstenirse yalnız ön kontrol raporu verir.

## Kurulum

1. `PythonPartsScripts\ALUPLAN\` içindeki 6 dosyayı kopyalayın (R9'dan itibaren hepsi `ePYS_IDS_` ile başlar):

   | Dosya | Ne için |
   |---|---|
   | `ePYS_IDS.py` | Allplan paleti |
   | `ePYS_IDS_core.py` | IDS denetimi ve düzeltmeler |
   | `ePYS_IDS_Kurallar.ids` | Bakanlığın IDS dosyası (EPYS_IDS.ids) |
   | `ePYS_IDS_Form.xlsx` | Proje Bilgi Formu şablonu |
   | `ePYS_IDS_IfcDuzenle.py` | e-PYS IFC (PP03) çekirdeği |
   | `ePYS_IDS_Eslestirme.txt` | e-PYS IFC eşleme kuralları |

   → `...\Usr\Local\PythonPartsScripts\ALUPLAN\`

   Eski sürümlerden kalan, artık gerekmeyen PP09 dosyaları (silebilirsiniz): `EPYS_IDS.ids`, `ePYS_Proje_Bilgi_Formu.xlsx`, `ePYS_IDS_Varsayilan.txt`, `ePYS_IDS_kurallar.py`. `EPYS_IfcDuzenle_core.py`, `EPYS_IfcDuzenle.py` ve `EPYS_IfcEslestirme.txt` yalnız ayrı e-PYS IFC aracını da kullanıyorsanız kalmalı.

   **Bakanlık yeni IDS gönderdiğinde:** dosyayı `ePYS_IDS_Kurallar.ids` adıyla değiştirin ya da paletteki "IDS dosyası" alanından seçin.
2. `Library\ALUPLAN\` içindeki `e-PYS IDS Kontrol.pyp` ve `e-PYS IDS Kontrol.png` dosyalarını kopyalayın
   → `...\Usr\Local\Library\ALUPLAN\`
3. Allplan'ı yeniden başlatın. Kütüphane → Özel → ALUPLAN → **e-PYS IDS Kontrol**. Palet başlığında sürüm görünür: **e-PYS IDS Kontrol (R21)**.
4. **e-PYS IFC (PP03) artık PP09'un içinde.** Kütüphanede tek araç istiyorsanız `Library\ALUPLAN\e-PYS IFC.pyp` ve `e-PYS IFC.png` dosyalarını silin (PP09 kendi kopyasını, `ePYS_IDS_IfcDuzenle.py`, kullanır).

Dış kütüphane gerekmez. Çekirdek yalnız Python standart kütüphanesini kullanır.

## Önerilen iş akışı

1. **ALLPLAN modeline nitelik yaz → İşlem = Yalnız kontrol et (rapor)**: Projeyi pencereyle seçin. Excel'de eksik nitelikler listelenir.
2. **İşlem = Önce dene (yazmadan rapor ver)**, ardından **Nitelik yaz**: Eksikleri toplu yazın.
3. PP02 e-PYS Nitelik Yaz ile **Kod yazısı** (Tag) verin.
4. IFC'yi Allplan'dan dışa aktarın (IFC 4.3; taban miktarları / Base Quantities açık).
5. **Proje Bilgi Formu → Düzenle/Aç**: projede bir kez doldurun (arsa, müellif, koordinat …). Bkz. aşağısı.
6. **Kontrol et ve düzelt → ▶ Çalıştır**: `<ad>_IDS.ifc` ve `<ad>_IDS_Rapor.xlsx` oluşur.
7. Rapordaki **Yapılacaklar** sayfasında kalanları Allplan'da tamamlayın (2. adım).
8. `<ad>_IDS.ifc` dosyasını e-PYS'e yükleyin. Ayrıca e-PYS IFC (PP03) çalıştırmaya gerek yok: nitelik eşlemesi PP09'dan önce, AllplanAttributes temizliği sonra otomatik yapılır.

## Palet yazıları (R11)

| Eski yazı (R10) | Yeni yazı (R11) |
|---|---|
| Çalışma: IFC Denetim / Düzelt · Nitelik Ata / Ön Kontrol | (başlıksız) IFC dosyasını kontrol et ve düzelt · ALLPLAN modeline nitelik yaz |
| Yalnız denetle (rapor) · Düzelt + denetle | Yalnız kontrol et (rapor) · Kontrol et ve düzelt |
| Çıktı IFC | Kaydedilecek IFC |
| Proje Bilgi Formu'nu aç | Proje Bilgi Formu → **Düzenle/Aç** |
| e-PYS IFC (Allplan nitelikleri) · Eşleme dosyasını düzenle | Allplan nitelikleri · Aktarma kuralları → **Düzenle** |
| Otomatik düzeltmeler | e-PYS Yönetmeliğe göre otomatik düzeltmeler (1–15) |
| IDS nitelikleri · Serbest nitelikler (çoklu) | Yazılacak nitelikler · Diğer nitelikler (listeden seç) |
| Son raporu aç | Son rapor → **Aç** |

## 1. IFC Denetim / Düzelt

| Ayar | Açıklama |
|---|---|
| Allplan IFC dosyası | Denetlenecek IFC (IFC4; IFC2x3 de okunur) |
| İşlem | **Yalnız denetle** (rapor) ya da **Düzelt + denetle** |
| Çıktı IFC | Boş bırakılırsa `<ad>_IDS.ifc`. Yalnız dosya adı yazılırsa IFC'nin klasörüne kaydedilir; uzantı yoksa `.ifc` eklenir. Orijinal dosya hiçbir zaman değişmez |
| IDS dosyası | Boş bırakılırsa paketteki `ePYS_IDS_Kurallar.ids` kullanılır. Bakanlık yeni IDS yayınlarsa yalnız bu dosyayı değiştirin ya da burada seçin; kod değişmez |
| Proje kodu, Bina adı, Bina uzun adı | IfcProject Name (boşsa formdan), IfcBuilding Name / LongName |
| Proje Bilgi Formu'nu aç | IFC klasöründe `ePYS_Proje_Bilgi_Formu.xlsx` oluşturur / açar. Bkz. aşağısı |
| **e-PYS IFC (R7)** – Allplan nitelik eşlemesi | `ePYS_IDS_Eslestirme.txt` kurallarıyla AllplanAttributes'taki nitelikleri IFC alanlarına yazar (İsim → Name, Kod yazısı → Tag, IfcSpace: CSB_Mahal → mahal adı …). PP09 düzeltmesinden **önce** uygulanır |
| **e-PYS IFC (R7)** – AllplanAttributes setlerini sil | Teslim için Allplan'a özel nitelik setlerini çıktıdan siler (PP03 "tamamen sil"). PP09 düzeltmesinden **sonra** uygulanır |
| Eşleme dosyasını düzenle | `ePYS_IDS_Eslestirme.txt` dosyasını açar (PP03 ile aynı biçim) |

**Otomatik düzeltmeler**: Her biri paletten kapatılabilir. Yalnız IFC'de zaten bulunan bilgiler kullanılır.

| Düzeltme | Kaynak |
|---|---|
| Tag ← Kod yazısı | `AllplanAttributes`, `AllplanAttributes (MM-KAP-…)` ve katmanlı (`Object Layer Attributes #n`) setler dahil. Kapı, pencere, kaplama ve çatıda Tag'in boş kalma nedeni buydu |
| Boş PredefinedType → USERDEFINED | ObjectType boşsa "IFC obje kategorisi" ile doldurulur |
| Ek-5 ad biçimi | `MM_KAP-…` → `MM-KAP-…`, `MM_GDC_ALU` → `MM-GDC-ALU`, `Tiriz/Travers` → `MM-ELM-TIRIZ_TRAVERS`, `Kapı Boşluğu` → `MM-ACL-KAPI_BOSLUGU`, boş adlar malzemeden. Adı **ve** malzemesi olmayan elemanlara ad verilmez (ad, onu ek kurallara sokar); Uyarılar'da listelenir |
| Yanlış sınıf | Adında TML olan IfcSlab → IfcFooting; BAC olan IfcWall → IfcChimney (Pset adıyla birlikte). **Allplan'da da düzeltin.** |
| Mahal no | `OAL_OAL_001` → `K01_OAL_001`, `_OAL_001` → `K01_OAL_001`, `Z00_…` → `K00_…` (kat, mahalin bağlı olduğu kattan) |
| Mahal kaplamaları | Pset_SpaceCoveringRequirements: mahalin içindeki IfcCovering'lerin (döşeme/duvar/tavan) katman malzemeleri ve kalınlık toplamı |
| Kat | ElevationOfSSLRelative ← kat kotu; NetFloorArea ← mahal net alanları toplamı |
| Bina | NumberOfStoreys, GrossFloorArea, NetFloorArea; bina / arsa adı Ek-5 biçimi, LongName |
| Adres | Pset_Address ← IFC posta adresi (bina ve arsa) |
| Zon | `D01` → `MM-ZON-D01`, LongName "Daire 01", ObjectType "Daire" |
| Merdiven FireExit ← Acil Çıkış | Allplan bunu Pset_StairCommon'a Türkçe adla yazıyor |
| Kapı/pencere IsExternal | Eksikse yerleştiği boşluğun "Dış Yapı Elemanı" niteliğinden; çatı her zaman dış eleman |
| FireRating F120 → 120 | IDS açıklaması "tam sayı dakika" diyor |
| IfcActorRole Description | IDS rol açıklamasını zorunlu tutuyor: ARCHITECT → "Mimar" vb.; USERDEFINED rolde UserDefinedRole |
| **Bina/arsa bilgileri (R5)** | Ada/parsel ← arsa adı; net alan ← mahal geometrisi; brüt/taban alanı ← döşemeler (yaklaşık); yükseklik, saçak ← en üst eleman/döşeme; yapım tekniği ← taşıyıcı malzeme; kullanım ← mahal/zon adları; yangın bina sınıfı ← yükseklik (21,50 m); geçici BuildingID ← bina adı (IsPermanentID = FALSE); proje açıklaması; rol ← disiplin (MM → ARCHITECT); kurum adresi |
| **Giydirme cephe (R5)** | Tiriz/travers (IfcMember): Dış eleman ← giydirme cephe; Kod yazısı ← giydirme cephe Kod yazısı + `_T01…`; malzeme ← giydirme cephe adı (ALU → Alüminyum_Profil). Giydirme cephenin malzemesi de adından |

## Proje Bilgi Formu (R5)

Allplan modelinde olmayan resmî bilgiler için **Excel formu**. Paletteki **Proje Bilgi Formu'nu aç** düğmesi formu IFC dosyasının klasöründe `ePYS_Proje_Bilgi_Formu.xlsx` adıyla oluşturur (şablon: `ePYS_IDS_Form.xlsx`) ve açar. Doldurduğunuz mevcut formlar aynen kullanılır. Proje başına **bir kez** doldurulur; aynı klasördeki her IFC'de kullanılır.

- Türkçe sorular; her satırda birim, örnek ve **nereden bulunur** (imar durumu, tapu, aplikasyon krokisi …).
- Açılır listeler (meslek, kullanım, yapım tekniği, TM dilimi, yangın dakikası), sayı aralığı kontrolü, proje kodu biçim kontrolü.
- **Durum** sütunu: ✓ Tamam · ✗ Boş (zorunlu) · ⚠ Değer hatalı ya da **örnek değer** (örnek sütunundan kopyalanmış) · ○ Boş (otomatik / isteğe bağlı). **Örnek sütunundaki değerler gerçek değildir.** Üstte "Zorunlu alanlar: x / 27 dolu".
- Yalnız sarı **Değer** sütunu yazılabilir; diğer sütunlar kilitli.
- "Otomatik bulunur" alanları boş bırakılabilir; girilirse girilen değer kullanılır.
- Formdaki değer IFC'deki mevcut değerin **yerine** yazılır (yanlış adres, müellif adı, arsa oranları …). Hatalı değerler yazılmaz; raporun **Uyarılar** sayfasında listelenir.
- Koordinat: TM dilimi + proje 0,0 noktasının Sağa/Yukarı değeri + kuzey açısı → IfcProjectedCRS (TUREF/TM, EPSG:5253–5259), IfcMapConversion, TrueNorth.

## Varsayılan değerler dosyası (eski, isteğe bağlı)

R8'den itibaren pakette yok; Proje Bilgi Formu kullanın. IFC'nin yanında `<ad>_Varsayilan.txt` (`Sınıf ; Hedef ; Değer` satırları) varsa PP09 onu da okur ve yalnız IFC'de boş olan alanlara yazar.

## Rapor (Excel)

| Sayfa | İçerik |
|---|---|
| Özet | Modele uygulanan IDS kuralları: önce / sonra durum, geçen / kısmi / kalan; bakanlık aracının sayımı |
| Yapılacaklar | Kalan her gereksinim: adet, bulunan değerler, IDS beklentisi, **Allplan'da / PP09'da ne yapılacağı** |
| Otomatik Düzeltmeler | Her değişiklik: eleman, alan, eski → yeni, kaynak |
| Kalan Hatalar | Eleman listesi (IFC # ile), filtrelenebilir |
| Uyarılar | Otomatik düzeltilemeyenler (mahal kaplaması yok, mahal no tanınmadı …) |
| Allplan Nitelikleri | Hangi Allplan niteliği hangi IFC alanına gidiyor |

## 2. ALLPLAN modeline nitelik yaz

1. Paletin üstünde **ALLPLAN modeline nitelik yaz** seçin. Seçim hemen başlar (pencereyle toplu seçim olur, ESC: çıkış).
2. **İşlem**:

   | Seçenek | Ne yapar |
   |---|---|
   | **Nitelik yaz** | Nitelikleri elemanlara yazar |
   | **Önce dene (yazmadan rapor ver)** | Hiçbir şey yazmaz; neyin yazılacağını raporlar |
   | **Nitelik sil** | "Yazılacak nitelikler"de işaretli nitelikleri (ve Diğer nitelikler listesindekileri) seçilen elemanlardan siler (PP02 "Nitelik Sil" gibi). Metin nitelikler boşaltılır, sayı/evet-hayır nitelikler kaldırılır |
   | **Yalnız kontrol et (rapor)** | Mevcut nitelikleri IDS'e göre ön kontrol eder |

   **Nitelik doluysa**: **Dokunma, yalnız boşlara yaz** (varsayılan) ya da **Üzerine yaz**. İsim, boşsa ya da Ek-5 biçimine uymuyorsa yazılır.
3. **Elemanlar** (R12, PP02 e-PYS Nitelik Yaz R62'deki gruplar):

   | Grup | Elemanlar |
   |---|---|
   | Statik – Tümü | Temel, Kolon, Kiriş, Döşeme, Merdiven |
   | Mimari – Tümü | Duvar, Çatı Örtüsü, Baca, Çatı Penceresi, Oda, Kapı, Korkuluk, Pencere, Giydirme Cephe |
   | Kaplama (IfcCovering) – Tümü | Duvar Kaplaması, Tavan Kaplaması, Döşeme Kaplaması, Süpürgelik |
   | Tümü | hepsi |

   - Eleman tanıma PP02 R62 ile aynıdır: Allplan tip kimliği (TypeUUID), bulunamazsa tip adı.
   - Katman/parça seçilirse ana elemana yazılır (WallTier → Duvar, DoorTier → Kapı, SubFacade → Giydirme Cephe).
   - Kapı/pencere ParaObje'si seçilirse kapıya/pencereye, çatı penceresi ParaObje'si seçilirse çatı penceresine yazılır.
   - **Oda seçilince içindeki kaplamalar da alınır** (kaplama kutuları açıksa). Kaplamalar Allplan'da odanın alt öğesidir; pencereyle seçimde yalnız oda gelir.
   - Yazı, etiket, ölçü, akıllı sembol, döşeme boşluğu, donatı gibi öğeler atlanır ve raporun **Tanınmayan tipler** sayfasına yazılır.
   - **Kapı / Pencere: nitelik yazılacak yer**: **Boşluk + ParaObje** (varsayılan), **Boşluk** ya da **ParaObje**. ParaObje'si olmayan kapı/pencerede nitelik boşluğa yazılır.
4. **Yazılacak nitelikler**: Yazılacak her satırın kutusunu işaretleyin.

| Satır | Allplan niteliği | IFC |
|---|---|---|
| İsim (Ek-5) | İsim | Name: `DİSİPLİN-KOD-AÇIKLAMA`. Kod eleman türünden gelir (DVR, KLN, KRS, DSM, TML, MRD, KAP, PNC, KRK, GDC, CAT, BAC, KPL; çatı penceresi PNC, dört kaplama türü KPL). Disiplin **Otomatik**: taşıyıcılar ST, diğerleri MM. Kapı/pencere/kaplama yalnız MM/IM, temel ST. Açıklamada `{MALZEME}` ve `{MEVCUT}` kullanılabilir. Odada İsim'e dokunulmaz |
| Yangın dayanımı (dk) | Yangın Dayanım Sınıfı | Pset_*Common.FireRating |
| Dış eleman | Dış Yapı Elemanı | IsExternal |
| Taşıyıcı | Statik_taşıyıcı | LoadBearing (duvar, kolon, kiriş, döşeme, temel, merdiven, baca, çatı) |
| Kaçış yolu / Acil çıkış | Kaçış Yolu (kapı) / Acil Çıkış (merdiven) | FireExit |
| Malzeme | Malzeme | IfcMaterial (`Malzeme_Dayanım`) |
| IFC obje kategorisi | IFC obje kategorisi | ObjectType |

5. **Diğer nitelikler (listeden seç)**: Allplan'ın Nitelik Seçimi penceresinden istediğiniz kadar nitelik ekleyip değer verin; hepsi birlikte yazılır.

**Raporlar nereye yazılır (R20):** IFC denetim raporu IFC dosyasının yanına (`<ad>_IDS_Rapor.xlsx`); nitelik yazma / deneme / silme / ön kontrol raporları **Belgeler\\e-PYS IDS Raporları** klasörüne (`ePYS_IDS_Nitelik_<tarih>.xlsx`, `ePYS_IDS_OnKontrol_<tarih>.xlsx`). Sonuç → **Son rapor → Aç** son raporu açar; rapor yoksa bu klasörü açar.

**Kod yazısı (Tag)** numaralandırması ve plan etiketi PP02 e-PYS Nitelik Yaz'da kalır; PP09 Kod yazısını yalnız ön kontrolde denetler.

**Ön kontrol**, Allplan nitelikleri üzerinden yaklaşık bir denetimdir (İsim deseni, Kod yazısı, yangın, dış eleman, taşıyıcı, kaçış yolu, malzeme, mahal no). Kesin sonuç IFC denetimidir.

**Allplan nitelik adları** (palette kapalı başlar; okla açılır): Nitelikler adıyla bulunur. `A|B` yazılırsa ilk bulunan kullanılır. **Nitelik adlarını doğrula** düğmesi her adın ID'sini ve tipini gösterir. İlk kullanımda bir kez basın. "BULUNAMADI" çıkan bir ad varsa Allplan'daki adı yazın.

**Geri alma**: Nitelik değişikliği Ctrl+Z ile geri alınmaz. Emin değilseniz önce **Önce dene (yazmadan rapor ver)** ile başlayın.

## Allplan dışında kullanım

```
python ePYS_IDS_core.py model.ifc
python ePYS_IDS_core.py model.ifc --duzelt --form ePYS_Proje_Bilgi_Formu.xlsx --bina-adi MM-BNA-A_BLOK
```

## Doğrulama

PP09 denetimi, bakanlığın IDS aracının raporuyla (2026-10-02_ids-check-EPYS_IDS, 02.11.2026 12:10) **eleman bazında** karşılaştırıldı: 83 gereksinim grubunun 82'sinde kalan elemanlar (IFC # listesi) birebir aynı. Tek fark IfcGeometricRepresentationContext: bakanlık aracı bu dosyada bağlamı hiç bulamıyor ("sınıf yok"), PP09 bulup TrueNorth eksik diyor. Her ikisinde de kural kalıyor; rapordaki "bakanlık aracının sayımı" bunu bakanlık gibi sayar.

## Bilinen sınırlar (R21)

- IDS facet'lerinden entity, predefinedType, attribute, property, material, partOf desteklenir (EPYS_IDS'in kullandıklarının tamamı). classification henüz yok (EPYS_IDS'te kullanılmıyor).
- IfcGeometricRepresentationContext kuralı bakanlık aracında bulunamıyor; TrueNorth eklemek tek başına yetmeyebilir.
- IDS şeması IFC4X3_ADD2. IfcAnnotation (PredefinedType = SURVEY) yalnız IFC 4.3'te var; IFC4 dışa aktarımda karşılanamaz.
- Allplan 2026, kapı/pencere ParaObjesi boşluklarının İsim ve Kod yazısı niteliklerini IFC'ye aktarmıyor (ad her zaman "Kapı Boşluğu"/"Pencere Boşluğu"). PP09 adı Ek-5 biçimine getirir.
- Giydirme cephe alt elemanlarına (tiriz/travers) Allplan'da nitelik girilemiyor; PP09 bunları giydirme cepheden tamamlar (R5).
- Geometriden alan/yükseklik hesabı yaklaşıktır (ekstrüzyon profilleri). Brüt alanı formda proje alan hesabından girin. Taban miktarları (Base Quantities) dışa aktarılırsa Allplan değerleri kullanılır.
- Katı olmayan IfcBuilding'lere (vaziyet planı, emsal raporu yapı düzeyleri) otomatik bina bilgisi yazılmaz; Uyarılar'da listelenir. Bunları IFC dışa aktarmaya almayın.
- "Yanlış sınıf" düzeltmesi yalnız IFC'yi değiştirir. Allplan'da da temel/baca olarak modelleyin.
- Mahal kaplaması olmayan mahallerde (Allplan'da yüzey tanımlanmamış) Pset_SpaceCoveringRequirements üretilemez; Uyarılar sayfasında listelenir.
- Allplan tip adları sürüme göre değişebilir. Tanınmayan tipler log'a ve raporun **Tanınmayan tipler** sayfasına yazılır.

## Sorun giderme

Her çalıştırma `%TEMP%\ePYS_IDS.log` dosyasına yazılır (ilk satır: "Script yüklendi R21"). Hata olursa bu dosyayı iletin.

## Sürümler

- **R21** (04.11.2026): Baca katmanları (WallTier) Baca sayılır ama nitelik katmanın **kendisine** yazılır (R19'da bacaya yazılıyordu). Allplan her baca katmanını ayrı IfcChimney olarak aktarıyor (örnek modelde 3 baca → 14 IfcChimney).

- **R20** (04.11.2026): **Son rapor → Aç** çalışmıyordu (palet yenilenmediği için rapor yolu kayboluyordu). Son raporun yolu artık ayrıca saklanır; rapor bulunamazsa rapor klasörü açılır. Nitelik raporları %TEMP% yerine **Belgeler\\e-PYS IDS Raporları** klasörüne yazılır. İşlemden sonra palet yenilenir.

- **R19** (04.11.2026): Allplan boş niteliği "<tanımsız>" yazısıyla veriyor; PP09 bunu dolu sayıyordu ("yalnız boşlara yaz" hiçbir şey yazmıyordu). Artık boş sayılır. Bacanın katmanları (Allplan'da WallTier) Duvar değil **Baca** sayılır ve nitelik bacanın kendisine yazılır.

- **R18** (04.11.2026): Nitelik yaz / Önce dene / Nitelik sil / Yalnız kontrol et sonrasında **özet penceresi** açılır (Sonuç → "İşlemden sonra özet göster", varsayılan açık): seçilen öğe, işlenen eleman türleri, kutusu kapalı olduğu için atlananlar, tanınmayanlar, sonuç ve Excel rapor yolu. Hiç nitelik işaretlenmemişse ya da seçimde işaretli eleman türü yoksa ne yapılacağı yazılır. İlerleme çubuğu yalnız 30 ve üzeri elemanda görünür.

- **R17** (04.11.2026): Asıl çökme nedeni bulundu: paletteki üst seçenek ya da İşlem değişince seçim ikinci kez başlatılıyordu (R11'den beri); ardından eleman seçilince Allplan kapanıyordu. Artık seçim yeniden başlatılmaz (PP02 R62 gibi). IFC bölümü değişmedi.

- **R16** (04.11.2026): "ALLPLAN modeline nitelik yaz" Allplan'ı kapatıyordu (R15). Nitelik yazma ve ilerleme çubuğu PP02 R62'de Allplan'da denenmiş çağrılara çevrildi (`ChangeAttributes(…, False, False)`, her nitelik ayrı; `ProgressBar(n, 0, False)`). Log dosyasına adım adım kayıt eklendi (ADIM 1–4, her yazılan eleman). IFC bölümü değişmedi.

- **R15** (04.11.2026): Proje Bilgi Formu: sayılar yazı olarak girildiğinde ya da yapıştırıldığında (ör. "1436", "0,30", kuzey açısı "0") Durum sütunu yanlışlıkla "⚠ Sayı … olmalı" diyordu. Artık yazı biçimindeki sayılar da kabul edilir (virgül ya da nokta). PP09 bu değerleri zaten doğru okuyordu; değişen yalnız formdaki uyarı. Kod ve IFC bölümü değişmedi.

- **R14** (04.11.2026): "Allplan nitelik adları" bölümü palette kapalı başlar (bir kez ayarlanan bir bölüm; gerektiğinde okla açılır). Başka değişiklik yok.

- **R13** (04.11.2026): R12'de Allplan, satır yazısı boş olan satırları tek satırda birleştirdi (Statik/Mimari/Kaplama kutuları yan yana tek satırda). Satırlara PP02'deki gibi benzersiz (görünmeyen) adlar verildi; kutular iki sütunda. İşlem listesine **Nitelik sil** eklendi. IFC bölümü yine değişmedi.

- **R12** (04.11.2026): **ALLPLAN modeline nitelik yaz** bölümü yenilendi; IFC bölümüne dokunulmadı (`ePYS_IDS_core.py` R11 ile aynı, aynı IFC'de çıktı birebir aynı). PP02 e-PYS Nitelik Yaz R62'nin eleman tanıması aktarıldı: Statik / Mimari / Kaplama grupları ve her grupta Tümü kutusu, 18 eleman türü (çatı penceresi, oda, dört kaplama türü yeni), ParaObje ve katman → ana eleman, odadaki kaplamaların otomatik alınması, "Kapı / Pencere: nitelik yazılacak yer". Allplan'da görünmeyen **İşlem** bölümü düzeltildi: açılır listeler (Nitelik yaz / Önce dene / Yalnız kontrol et; Nitelik doluysa). R11'de "Önizleme" kapatılamadığı için nitelik yazılamıyordu; artık varsayılan **Nitelik yaz**. Satırdaki kutular PP02'deki gibi yan yana.

- **R11** (03.11.2026): Yalnız palet yazıları sadeleştirildi (kod değişmedi). Üstte "Çalışma" yazısı kaldırıldı; seçenekler "IFC dosyasını kontrol et ve düzelt" / "ALLPLAN modeline nitelik yaz". Bölümler: Dosyalar, Proje bilgileri, Allplan nitelikleri, e-PYS Yönetmeliğe göre otomatik düzeltmeler (1–15 numaralı), Yazılacak nitelikler, Diğer nitelikler, Sonuç. Düğmelerde satır yazısı ile düğme yazısı ayrıldı (Düzenle/Aç, Düzenle, ▶ Çalıştır, Doğrula, Aç).

- **R10** (03.11.2026): **Çıktı IFC** alanına yalnız dosya adı yazılınca çıktı Allplan'ın çalışma klasörüne yazılmaya çalışılıyordu (hata). Artık IFC'nin klasörüne kaydedilir; `.ifc` uzantısı yoksa eklenir; alt klasör yoksa oluşturulur.

- **R9** (03.11.2026): `PythonPartsScripts\ALUPLAN` dosya adları düzenlendi; hepsi `ePYS_IDS_` ile başlıyor (`ePYS_IDS_Kurallar.ids`, `ePYS_IDS_Form.xlsx`, `ePYS_IDS_IfcDuzenle.py`, `ePYS_IDS_Eslestirme.txt`). Eski adlı dosyalar bulunursa onlar da okunur. Proje klasörlerindeki doldurulmuş `ePYS_Proje_Bilgi_Formu.xlsx` değişmedi.

- **R8** (03.11.2026): Paket sadeleştirildi: `ePYS_IDS_Varsayilan.txt` şablonu ve paletteki "İleri düzey: varsayılan değerler (.txt)" düğmesi kaldırıldı (yerini Proje Bilgi Formu aldı). IFC'nin yanında eski bir `<ad>_Varsayilan.txt` varsa yine okunur.

- **R7** (03.11.2026): **e-PYS IFC (PP03) birleştirildi.** Tek çalıştırmada: Allplan nitelik eşlemesi (PP03 kuralları) → PP09 düzeltmeleri → AllplanAttributes temizliği. Sıra hatası (PP03'ü önce çalıştırıp Acil Çıkış gibi bilgileri kaybetme) artık olmaz. Örnek model (IFC4, AllplanAttributes'lı): 2.726 → 267 hatalı kontrol, 2.714 nitelik seti silindi, kırık referans yok.

- **R6** (03.11.2026): Palet başlığında sürüm görünür. Formda **örnek değer** uyarısı (sicil no, tapu, TAKS/KAKS, çekmeler, kot, koordinat örnekle aynıysa Durum sütunu ve rapor Uyarılar'ı uyarır). Listeli alanlar elle yazılırsa baştaki koda göre eşlenir (ör. "TM30 …"). TM dilimi örneği listeyle aynı yapıldı.

- **R5** (03.11.2026): **Proje Bilgi Formu** (Excel; açılır listeler, değer kontrolü, durum sütunu) – varsayılan .txt yerine. Modelden **otomatik bina/arsa bilgileri** (ada/parsel, alanlar, yükseklik, yapım tekniği, kullanım, yangın bina sınıfı, rol, kurum adresi). **Giydirme cephe** tiriz/traversleri giydirme cepheden tamamlanır. Koordinat girilmeden 0,0 harita dönüşümü yazılmaz. Örnek model (NNN_02): formsuz 1.677 → 124; formla 1.677 → 107 hatalı kontrol.

- **R4** (03.11.2026): Bakanlığın 03.11.2026 tarihli **EPYS_IDS.ids** dosyası (boşluk ad deseni `[A-Z]{2}-[A-Z]{3}-[^-]+`, proje adı `XX-PRJ-` + 6 karakter, IfcAnnotation artık zorunlu değil). Varsayılan dosyasına **Malzeme** hedefi ve **{#}** sıra numarası eklendi; giydirme cephe tiriz/traversleri (IfcMember) için IsExternal, Malzeme, Tag satırları. Örnek model (NNN_02): 1.677 → 150 hatalı kontrol.

- **R3** (02.11.2026): Kurallar artık doğrudan bakanlığın **EPYS_IDS.ids** dosyasından okunur (161 kural; palette IDS dosyası seçilebilir). Bakanlığın güncel IDS'inde duvar ad deseni düzeltilmiş (`…-DVR-[^-]+`); IDS hatası sayfası/ayarı kaldırıldı. Rol eklenirken IDS’in istediği IfcActorRole Description yazılır. Adı ve malzemesi olmayan elemanlara ad verilmez. Örnek model: 2.762 → 333 hatalı kontrol (bakanlık sayımıyla 2.758 → 329 eleman hatası).

- **R2** (02.11.2026): Bakanlık IDS raporuyla eleman bazında doğrulandı. Rapor Özet sayfasına bakanlık aracının sayımı eklendi (örnek model: 3.280 → 847 eleman hatası; bunun 522'si IDS'teki duvar deseni hatası). Bağlam (TrueNorth) notu.

- **R1** (02.11.2026): İlk sürüm. Örnek modelde (2026_45_MM_XXXX_MD_MMC_NNN_01_ePYS.ifc) IDS hatalı kontrol sayısı **2.762 → 329** (yalnız otomatik düzeltme). Denetim sonuçları R2 IDS raporuyla birebir aynı (32 kural, 3.284 hatalı kontrol).
