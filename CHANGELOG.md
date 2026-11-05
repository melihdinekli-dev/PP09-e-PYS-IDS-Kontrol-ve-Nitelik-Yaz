# Değişiklik Günlüğü (CHANGELOG)

Biçim: her sürüm `R<n>` etiketiyle yayınlanır (paket: `ePYS_IDS_Allplan2026_R<n>.zip`). En yeni sürüm üstte.

## [Yayınlanmamış]

- Repo ve DevOps altyapısı: kaynak düzeni (`src/`), tekrarlanabilir paket (`build.py`), otomatik testler (`tests/`), GitHub Actions (CI + Release). Paket içeriği R21 ile aynı.

## [R21] – 04.11.2026

Baca katmanları (WallTier) Baca sayılır ama nitelik katmanın **kendisine** yazılır (R19'da bacaya yazılıyordu). Allplan her baca katmanını ayrı IfcChimney olarak aktarıyor (örnek modelde 3 baca → 14 IfcChimney).

## [R20] – 04.11.2026

**Son rapor → Aç** çalışmıyordu (palet yenilenmediği için rapor yolu kayboluyordu). Son raporun yolu artık ayrıca saklanır; rapor bulunamazsa rapor klasörü açılır. Nitelik raporları %TEMP% yerine **Belgeler\\e-PYS IDS Raporları** klasörüne yazılır. İşlemden sonra palet yenilenir.

## [R19] – 04.11.2026

Allplan boş niteliği "<tanımsız>" yazısıyla veriyor; PP09 bunu dolu sayıyordu ("yalnız boşlara yaz" hiçbir şey yazmıyordu). Artık boş sayılır. Bacanın katmanları (Allplan'da WallTier) Duvar değil **Baca** sayılır ve nitelik bacanın kendisine yazılır.

## [R18] – 04.11.2026

Nitelik yaz / Önce dene / Nitelik sil / Yalnız kontrol et sonrasında **özet penceresi** açılır (Sonuç → "İşlemden sonra özet göster", varsayılan açık): seçilen öğe, işlenen eleman türleri, kutusu kapalı olduğu için atlananlar, tanınmayanlar, sonuç ve Excel rapor yolu. Hiç nitelik işaretlenmemişse ya da seçimde işaretli eleman türü yoksa ne yapılacağı yazılır. İlerleme çubuğu yalnız 30 ve üzeri elemanda görünür.

## [R17] – 04.11.2026

Asıl çökme nedeni bulundu: paletteki üst seçenek ya da İşlem değişince seçim ikinci kez başlatılıyordu (R11'den beri); ardından eleman seçilince Allplan kapanıyordu. Artık seçim yeniden başlatılmaz (PP02 R62 gibi). IFC bölümü değişmedi.

## [R16] – 04.11.2026

"ALLPLAN modeline nitelik yaz" Allplan'ı kapatıyordu (R15). Nitelik yazma ve ilerleme çubuğu PP02 R62'de Allplan'da denenmiş çağrılara çevrildi (`ChangeAttributes(…, False, False)`, her nitelik ayrı; `ProgressBar(n, 0, False)`). Log dosyasına adım adım kayıt eklendi (ADIM 1–4, her yazılan eleman). IFC bölümü değişmedi.

## [R15] – 04.11.2026

Proje Bilgi Formu: sayılar yazı olarak girildiğinde ya da yapıştırıldığında (ör. "1436", "0,30", kuzey açısı "0") Durum sütunu yanlışlıkla "⚠ Sayı … olmalı" diyordu. Artık yazı biçimindeki sayılar da kabul edilir (virgül ya da nokta). PP09 bu değerleri zaten doğru okuyordu; değişen yalnız formdaki uyarı. Kod ve IFC bölümü değişmedi.

## [R14] – 04.11.2026

"Allplan nitelik adları" bölümü palette kapalı başlar (bir kez ayarlanan bir bölüm; gerektiğinde okla açılır). Başka değişiklik yok.

## [R13] – 04.11.2026

R12'de Allplan, satır yazısı boş olan satırları tek satırda birleştirdi (Statik/Mimari/Kaplama kutuları yan yana tek satırda). Satırlara PP02'deki gibi benzersiz (görünmeyen) adlar verildi; kutular iki sütunda. İşlem listesine **Nitelik sil** eklendi. IFC bölümü yine değişmedi.

## [R12] – 04.11.2026

**ALLPLAN modeline nitelik yaz** bölümü yenilendi; IFC bölümüne dokunulmadı (`ePYS_IDS_core.py` R11 ile aynı, aynı IFC'de çıktı birebir aynı). PP02 e-PYS Nitelik Yaz R62'nin eleman tanıması aktarıldı: Statik / Mimari / Kaplama grupları ve her grupta Tümü kutusu, 18 eleman türü (çatı penceresi, oda, dört kaplama türü yeni), ParaObje ve katman → ana eleman, odadaki kaplamaların otomatik alınması, "Kapı / Pencere: nitelik yazılacak yer". Allplan'da görünmeyen **İşlem** bölümü düzeltildi: açılır listeler (Nitelik yaz / Önce dene / Yalnız kontrol et; Nitelik doluysa). R11'de "Önizleme" kapatılamadığı için nitelik yazılamıyordu; artık varsayılan **Nitelik yaz**. Satırdaki kutular PP02'deki gibi yan yana.

## [R11] – 03.11.2026

Yalnız palet yazıları sadeleştirildi (kod değişmedi). Üstte "Çalışma" yazısı kaldırıldı; seçenekler "IFC dosyasını kontrol et ve düzelt" / "ALLPLAN modeline nitelik yaz". Bölümler: Dosyalar, Proje bilgileri, Allplan nitelikleri, e-PYS Yönetmeliğe göre otomatik düzeltmeler (1–15 numaralı), Yazılacak nitelikler, Diğer nitelikler, Sonuç. Düğmelerde satır yazısı ile düğme yazısı ayrıldı (Düzenle/Aç, Düzenle, ▶ Çalıştır, Doğrula, Aç).

## [R10] – 03.11.2026

**Çıktı IFC** alanına yalnız dosya adı yazılınca çıktı Allplan'ın çalışma klasörüne yazılmaya çalışılıyordu (hata). Artık IFC'nin klasörüne kaydedilir; `.ifc` uzantısı yoksa eklenir; alt klasör yoksa oluşturulur.

## [R9] – 03.11.2026

`PythonPartsScripts\ALUPLAN` dosya adları düzenlendi; hepsi `ePYS_IDS_` ile başlıyor (`ePYS_IDS_Kurallar.ids`, `ePYS_IDS_Form.xlsx`, `ePYS_IDS_IfcDuzenle.py`, `ePYS_IDS_Eslestirme.txt`). Eski adlı dosyalar bulunursa onlar da okunur. Proje klasörlerindeki doldurulmuş `ePYS_Proje_Bilgi_Formu.xlsx` değişmedi.

## [R8] – 03.11.2026

Paket sadeleştirildi: `ePYS_IDS_Varsayilan.txt` şablonu ve paletteki "İleri düzey: varsayılan değerler (.txt)" düğmesi kaldırıldı (yerini Proje Bilgi Formu aldı). IFC'nin yanında eski bir `<ad>_Varsayilan.txt` varsa yine okunur.

## [R7] – 03.11.2026

**e-PYS IFC (PP03) birleştirildi.** Tek çalıştırmada: Allplan nitelik eşlemesi (PP03 kuralları) → PP09 düzeltmeleri → AllplanAttributes temizliği. Sıra hatası (PP03'ü önce çalıştırıp Acil Çıkış gibi bilgileri kaybetme) artık olmaz. Örnek model (IFC4, AllplanAttributes'lı): 2.726 → 267 hatalı kontrol, 2.714 nitelik seti silindi, kırık referans yok.

## [R6] – 03.11.2026

Palet başlığında sürüm görünür. Formda **örnek değer** uyarısı (sicil no, tapu, TAKS/KAKS, çekmeler, kot, koordinat örnekle aynıysa Durum sütunu ve rapor Uyarılar'ı uyarır). Listeli alanlar elle yazılırsa baştaki koda göre eşlenir (ör. "TM30 …"). TM dilimi örneği listeyle aynı yapıldı.

## [R5] – 03.11.2026

**Proje Bilgi Formu** (Excel; açılır listeler, değer kontrolü, durum sütunu) – varsayılan .txt yerine. Modelden **otomatik bina/arsa bilgileri** (ada/parsel, alanlar, yükseklik, yapım tekniği, kullanım, yangın bina sınıfı, rol, kurum adresi). **Giydirme cephe** tiriz/traversleri giydirme cepheden tamamlanır. Koordinat girilmeden 0,0 harita dönüşümü yazılmaz. Örnek model (NNN_02): formsuz 1.677 → 124; formla 1.677 → 107 hatalı kontrol.

## [R4] – 03.11.2026

Bakanlığın 03.11.2026 tarihli **EPYS_IDS.ids** dosyası (boşluk ad deseni `[A-Z]{2}-[A-Z]{3}-[^-]+`, proje adı `XX-PRJ-` + 6 karakter, IfcAnnotation artık zorunlu değil). Varsayılan dosyasına **Malzeme** hedefi ve **{#}** sıra numarası eklendi; giydirme cephe tiriz/traversleri (IfcMember) için IsExternal, Malzeme, Tag satırları. Örnek model (NNN_02): 1.677 → 150 hatalı kontrol.

## [R3] – 02.11.2026

Kurallar artık doğrudan bakanlığın **EPYS_IDS.ids** dosyasından okunur (161 kural; palette IDS dosyası seçilebilir). Bakanlığın güncel IDS'inde duvar ad deseni düzeltilmiş (`…-DVR-[^-]+`); IDS hatası sayfası/ayarı kaldırıldı. Rol eklenirken IDS’in istediği IfcActorRole Description yazılır. Adı ve malzemesi olmayan elemanlara ad verilmez. Örnek model: 2.762 → 333 hatalı kontrol (bakanlık sayımıyla 2.758 → 329 eleman hatası).

## [R2] – 02.11.2026

Bakanlık IDS raporuyla eleman bazında doğrulandı. Rapor Özet sayfasına bakanlık aracının sayımı eklendi (örnek model: 3.280 → 847 eleman hatası; bunun 522'si IDS'teki duvar deseni hatası). Bağlam (TrueNorth) notu.

## [R1] – 02.11.2026

İlk sürüm. Örnek modelde (2026_45_MM_XXXX_MD_MMC_NNN_01_ePYS.ifc) IDS hatalı kontrol sayısı **2.762 → 329** (yalnız otomatik düzeltme). Denetim sonuçları R2 IDS raporuyla birebir aynı (32 kural, 3.284 hatalı kontrol).
