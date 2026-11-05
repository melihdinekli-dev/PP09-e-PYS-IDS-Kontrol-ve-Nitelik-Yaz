const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  AlignmentType, HeadingLevel, LevelFormat, Header, Footer, PageNumber, PageBreak, TableOfContents
} = require('docx');

const NAVY = '1F3864', LIGHT = 'DDEBF7', YEL = 'FFF2CC', RED = 'FCE4D6', GREEN = 'E2F0D9';
const W = 9638; // A4 içerik genişliği (2 cm kenar)
const bd = { style: BorderStyle.SINGLE, size: 4, color: 'BFBFBF' };
const borders = { top: bd, bottom: bd, left: bd, right: bd };

const t = (text, o = {}) => new TextRun({ text, ...o });
const P = (runs, o = {}) => new Paragraph({ children: Array.isArray(runs) ? runs : [t(runs)], spacing: { after: 100 }, ...o });
const H1 = (s) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [t(s)] });
const H2 = (s) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [t(s)] });
const H3 = (s) => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [t(s)] });
const B = (s, lvl = 0) => new Paragraph({ numbering: { reference: 'bul', level: lvl }, children: rich(s), spacing: { after: 60 } });
const N = (s, ref = 'num') => new Paragraph({ numbering: { reference: ref, level: 0 }, children: rich(s), spacing: { after: 60 } });
// **kalın** desteği
function rich(s) {
  const out = [];
  s.split(/(\*\*[^*]+\*\*)/).forEach(part => {
    if (!part) return;
    if (part.startsWith('**')) out.push(t(part.slice(2, -2), { bold: true }));
    else out.push(t(part));
  });
  return out;
}
function table(head, rows, widths, opt = {}) {
  const mk = (cells, isHead, fill) => new TableRow({
    tableHeader: isHead,
    children: cells.map((c, i) => new TableCell({
      borders, width: { size: widths[i], type: WidthType.DXA },
      shading: { fill: isHead ? NAVY : (fill || 'FFFFFF'), type: ShadingType.CLEAR },
      margins: { top: 60, bottom: 60, left: 100, right: 100 },
      children: [new Paragraph({ children: isHead ? [t(c, { bold: true, color: 'FFFFFF' })] : rich(String(c)) })]
    }))
  });
  return new Table({
    width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: widths,
    rows: [mk(head, true), ...rows.map((r, i) => mk(r, false, opt.fills ? opt.fills[i] : (opt.zebra && i % 2 ? 'F7F9FC' : null)))]
  });
}
function note(title, text, fill = YEL) {
  return new Table({
    width: { size: W, type: WidthType.DXA }, columnWidths: [W],
    rows: [new TableRow({ children: [new TableCell({
      borders, width: { size: W, type: WidthType.DXA }, shading: { fill, type: ShadingType.CLEAR },
      margins: { top: 100, bottom: 100, left: 160, right: 160 },
      children: [new Paragraph({ children: [t(title + ' ', { bold: true }), ...rich(text)] })]
    })] })]
  });
}
const sp = () => new Paragraph({ children: [], spacing: { after: 60 } });

const kids = [];
// ---------------- Kapak
kids.push(new Paragraph({ spacing: { before: 2400, after: 200 }, children: [t('e-PYS IDS Kontrol', { bold: true, size: 56, color: NAVY })] }));
kids.push(new Paragraph({ spacing: { after: 200 }, children: [t('Kullanıcı Kılavuzu', { size: 40, color: NAVY })] }));
kids.push(new Paragraph({ border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: NAVY, space: 4 } }, spacing: { after: 400 }, children: [] }));
kids.push(P([t('Allplan 2026 için PythonPart (PP09) · Sürüm R14', { size: 26 })]));
kids.push(P([t('Bakanlık e-PYS IDS kontrolüne hazırlık: IFC kontrolü, otomatik düzeltme ve toplu nitelik yazma', { size: 24, italics: true })]));
kids.push(new Paragraph({ spacing: { before: 3000 }, children: [t('ALUPLAN – Allplan Türkiye Distribütörü', { bold: true, size: 24 })] }));
kids.push(P([t('Kasım 2026', { size: 22 })]));
kids.push(new Paragraph({ children: [new PageBreak()] }));

// ---------------- İçindekiler
kids.push(new Paragraph({ children: [t('İçindekiler', { bold: true, size: 32, color: NAVY })], spacing: { after: 200 } }));
kids.push(new TableOfContents('İçindekiler', { hyperlink: true, headingStyleRange: '1-2' }));
kids.push(new Paragraph({ children: [new PageBreak()] }));

// ---------------- 1
kids.push(H1('1. Bu araç ne yapar?'));
kids.push(P('Bakanlık, e-PYS ruhsat başvurularında IFC dosyasını bir IDS kural dosyasıyla (EPYS_IDS.ids) kontrol ediyor. Her eleman için doğru ad (Ek-5), Kod yazısı (Tag), yangın dayanımı, dış eleman bilgisi, mahal kaplamaları, arsa ve bina bilgileri gibi yüzlerce bilgi isteniyor. Bunları Allplan Bilgi Paleti\'nden eleman eleman girmek büyük projelerde günler sürer.'));
kids.push(P('e-PYS IDS Kontrol bu işi iki yoldan hızlandırır:'));
kids.push(table(['Bölüm', 'Neyin üzerinde çalışır', 'Ne yapar', 'Allplan modeli değişir mi?'], [
  ['**IFC dosyasını kontrol et ve düzelt**', 'Allplan\'dan dışa aktarılmış IFC dosyası', 'IDS kurallarına göre kontrol eder, eksikleri düzeltip yeni bir IFC (…_IDS.ifc) ve Excel rapor üretir', 'Hayır – yalnız çıkan dosya'],
  ['**ALLPLAN modeline nitelik yaz**', 'Allplan modelinde seçtiğiniz elemanlar', 'İsim, yangın dayanımı, dış eleman, taşıyıcı, malzeme … niteliklerini toplu yazar ya da eksikleri listeler', 'Evet – kalıcı'],
], [2400, 2200, 3238, 1800]));
kids.push(sp());
kids.push(P([t('Kısaca: ', { bold: true }), t('biri dosyayı, diğeri modeli düzeltir. Örnek projede IDS hatası, araç tek çalıştırmayla 1.677\'den 199\'a indirdi; kalanlar yalnız Allplan\'da girilmesi gereken bilgilerdi.')]));

// ---------------- 2
kids.push(H1('2. Kurulum'));
kids.push(N('Paketi (ePYS_IDS_Allplan2026_R14.zip) açın.', 'kur'));
kids.push(N('**PythonPartsScripts\\ALUPLAN** klasöründeki 6 dosyayı Allplan\'ın **…\\Usr\\Local\\PythonPartsScripts\\ALUPLAN\\** klasörüne kopyalayın.', 'kur'));
kids.push(N('**Library\\ALUPLAN** klasöründeki 2 dosyayı **…\\Usr\\Local\\Library\\ALUPLAN\\** klasörüne kopyalayın.', 'kur'));
kids.push(N('Allplan\'ı yeniden başlatın. **Kütüphane → Özel → ALUPLAN → e-PYS IDS Kontrol**. Palet başlığında **e-PYS IDS Kontrol (R14)** yazmalıdır.', 'kur'));
kids.push(sp());
kids.push(table(['Dosya', 'Ne için'], [
  ['ePYS_IDS.py', 'Allplan paleti'],
  ['ePYS_IDS_core.py', 'Kontrol ve düzeltme çekirdeği'],
  ['ePYS_IDS_Kurallar.ids', 'Bakanlığın IDS dosyası'],
  ['ePYS_IDS_Form.xlsx', 'Proje Bilgi Formu şablonu'],
  ['ePYS_IDS_IfcDuzenle.py', 'Allplan nitelik aktarımı ve temizliği (eski e-PYS IFC aracı)'],
  ['ePYS_IDS_Eslestirme.txt', 'Allplan niteliği → IFC alanı aktarma kuralları'],
  ['e-PYS IDS Kontrol.pyp / .png', 'Kütüphane simgesi ve palet (Library klasörü)'],
], [3600, 6038], { zebra: true }));
kids.push(sp());
kids.push(note('Bakanlık yeni IDS gönderdiğinde:', 'dosyayı **ePYS_IDS_Kurallar.ids** adıyla değiştirin ya da paletteki **IDS dosyası** alanından seçin. Kod değişmez.', LIGHT));
kids.push(sp());
kids.push(note('Ayrı e-PYS IFC aracı:', 'artık bu aracın içinde. Kütüphanede tek araç görmek için **e-PYS IFC.pyp** ve **e-PYS IFC.png** dosyalarını silebilirsiniz. Dış kütüphane gerekmez; yalnız Python standart kütüphanesi kullanılır.', LIGHT));

// ---------------- 3
kids.push(H1('3. Hızlı başlangıç'));
kids.push(P('Her teslimde izlenecek sıra:'));
kids.push(table(['Adım', 'Nerede', 'Ne yapılır'], [
  ['1', 'Allplan', 'Modeli IFC 4.3 olarak dışa aktarın (taban miktarları / Base Quantities açık). Vaziyet planı ve emsal raporu yapı düzeylerini dışa aktarmaya almayın.'],
  ['2', 'e-PYS IDS Kontrol', '**IFC dosyasını kontrol et ve düzelt** seçin, **IFC dosyası** alanından dosyayı seçin.'],
  ['3', 'Proje Bilgi Formu', 'Projede ilk kez: **Proje Bilgi Formu → Düzenle/Aç**. Arsa, müellif ve koordinat bilgilerini girin, kaydedin (bkz. Bölüm 5).'],
  ['4', 'e-PYS IDS Kontrol', '**Kontrol et ve düzelt** seçili iken **IFC kontrolünü başlat → ▶ Çalıştır**. …_IDS.ifc ve …_IDS_Rapor.xlsx oluşur.'],
  ['5', 'Excel rapor', '**Yapılacaklar** sayfasındaki kalan maddeleri Allplan\'da düzeltin (gerekirse **ALLPLAN modeline nitelik yaz** ile toplu).'],
  ['6', 'e-PYS', 'Son **…_IDS.ifc** dosyasını e-PYS\'e yükleyin.'],
], [900, 2200, 6538]));
kids.push(sp());
kids.push(note('Önemli:', 'Düzeltmeler yalnız çıkan IFC dosyasında yapılır. Allplan\'dan her yeni dışa aktarmadan sonra aracı yeniden çalıştırın. Proje Bilgi Formu bir kez doldurulur, her çalıştırmada kullanılır.'));

// ---------------- 4
kids.push(H1('4. IFC dosyasını kontrol et ve düzelt'));
kids.push(H2('4.1 Dosyalar'));
kids.push(table(['Palette', 'Açıklama'], [
  ['IFC dosyası', 'Allplan\'dan dışa aktardığınız IFC. Orijinal dosya hiçbir zaman değiştirilmez.'],
  ['İşlem', '**Yalnız kontrol et (rapor):** yalnız Excel rapor. **Kontrol et ve düzelt:** düzeltilmiş IFC + rapor.'],
  ['Kaydedilecek IFC', 'Boşsa …_IDS.ifc. Yalnız dosya adı yazılırsa IFC\'nin klasörüne kaydedilir; .ifc eklenir.'],
  ['IDS dosyası', 'Boşsa paketteki Bakanlık IDS\'i kullanılır.'],
  ['Raporu Excel\'de aç', 'İşlem bitince rapor otomatik açılır.'],
], [2600, 7038], { zebra: true }));
kids.push(H2('4.2 Proje bilgileri'));
kids.push(table(['Palette', 'Açıklama'], [
  ['Proje kodu', 'MM-PRJ- + 6 karakter. Boşsa Proje Bilgi Formu\'ndan alınır.'],
  ['Bina adı', 'IFC\'deki resmi bina kodu (ör. MM-BNA-A_BLOK). Boşsa Allplan\'daki bina adından üretilir.'],
  ['Bina görünen adı', 'Okunur ad (ör. A Blok).'],
  ['Disiplin (MM = Mimari)', 'Ek-5 adlarının başı: MM, ST, IM, PY …'],
  ['Proje Bilgi Formu → Düzenle/Aç', 'Formu IFC\'nin klasöründe oluşturur / açar (Bölüm 5).'],
], [2600, 7038], { zebra: true }));
kids.push(H2('4.3 Allplan nitelikleri'));
kids.push(table(['Palette', 'Açıklama'], [
  ['İsim, Açıklama, Kod yazısı → Tag, CSB_Mahal → Mahal adı aktar', 'Allplan\'ın kendi nitelik grubundaki bilgileri IFC\'nin standart alanlarına yazar. Düzeltmeden **önce** çalışır.'],
  ['AllplanAttributes setlerini sil', 'Bakanlığın görmek istemediği Allplan nitelik gruplarını çıkan dosyadan siler. Düzeltmeden **sonra** çalışır.'],
  ['Aktarma kuralları → Düzenle', 'Hangi niteliğin hangi IFC alanına gideceğini yazan dosyayı açar (ePYS_IDS_Eslestirme.txt). Yeni kural eklenebilir.'],
], [3600, 6038], { zebra: true }));
kids.push(H2('4.4 e-PYS Yönetmeliğe göre otomatik düzeltmeler'));
kids.push(P('Her biri ayrı açılıp kapatılabilir. Varsayılan olarak hepsi açıktır. Yalnız IFC\'de boş ya da yanlış olan bilgiler düzeltilir; dolu ve doğru bilgilere dokunulmaz.'));
kids.push(table(['No', 'Palette', 'Ne yapar'], [
  ['1', 'Kod yazısını Tag alanına yaz', 'Boş Tag\'e Allplan Kod yazısını yazar (kapı, pencere, kaplama, çatı dahil).'],
  ['2', 'Formda boş kalan bina/arsa bilgilerini modelden hesapla', 'Ada/parsel, alanlar, yükseklik, yapım tekniği, kullanım, yangın bina sınıfı …'],
  ['3', 'Giydirme cephe tiriz/travers ← giydirme cephe', 'Allplan\'da nitelik girilemeyen tiriz/traverslere dış eleman, Kod yazısı (_T01, _T02 …) ve malzeme verir.'],
  ['4', 'Boş eleman tipini doldur', 'Boş PredefinedType → USERDEFINED; ObjectType ← IFC obje kategorisi.'],
  ['5', 'Eleman isimlerini Ek-5 biçimine değiştir', 'MM_KAP- → MM-KAP-, "Kapı Boşluğu" → MM-ACL-KAPI_BOSLUGU, Türkçe karakter düzeltme.'],
  ['6', 'Yanlış IFC sınıfını düzelt', 'Adında TML olan döşeme → temel; BAC olan duvar → baca.'],
  ['7', 'Mahal numarasına eksik kat önekini ekle', 'OAL_OAL_001 → K01_OAL_001; Z00 → K00.'],
  ['8', 'Mahal kaplamaları', 'Mahalin döşeme/duvar/tavan kaplama malzemesi ve kalınlığı, içindeki kaplamalardan.'],
  ['9', 'Kat kotu ve kat net alanını otomatik hesapla', 'Kat kotu ve mahallerin net alan toplamı.'],
  ['10', 'Bina ve arsa adını, kat sayısını ve alanlarını otomatik hesapla', 'MM-BNA-…, MM-SAH-…, kat sayısı, brüt/net alan.'],
  ['11', 'Bina ve arsa adresini doldur', 'Formdaki adres; yoksa Allplan proje adresi.'],
  ['12', 'Daire (zon) bilgilerini doldur', 'D01 → MM-ZON-D01, "Daire 01", tip "Daire".'],
  ['13', 'Merdiven FireExit ← Acil Çıkış', 'Allplan\'ın Türkçe "Acil Çıkış" niteliğini IDS\'in beklediği alana taşır.'],
  ['14', 'Kapı, pencere ve çatıya dış eleman bilgisi ver', 'Kapı/pencere: boşluğun Dış Yapı Elemanı niteliği; çatı: her zaman dış.'],
  ['15', 'Yangın dayanımını dakikaya çevir', 'F120 / REI 120 → 120.'],
], [700, 3800, 5138], { zebra: true }));
kids.push(H2('4.5 Çalıştırma ve sonuç'));
kids.push(P('**IFC kontrolünü başlat → ▶ Çalıştır** düğmesine basın. Büyük modellerde işlem 10–30 saniye sürer. Bittiğinde bir mesaj kutusu sonucu gösterir (ör. "1677 → 199 hata · 12 sn"). **Sonuç** bölümünde **Son IFC sonucu** ve **Rapor dosyası** yazılır; **Son rapor → Aç** ile raporu yeniden açabilirsiniz.'.replace(/\*\*/g, '')));

// ---------------- 5
kids.push(H1('5. Proje Bilgi Formu'));
kids.push(P('Allplan modelinde olmayan resmî bilgiler (arsa, imar, müellif, koordinat) için Excel formudur. Proje başına bir kez doldurulur; IFC dosyalarının bulunduğu klasörde **ePYS_Proje_Bilgi_Formu.xlsx** adıyla durur ve o klasördeki her IFC\'de kullanılır.'.replace(/\*\*/g, '')));
kids.push(H2('5.1 Nasıl doldurulur'));
kids.push(B('Palette **Proje Bilgi Formu → Düzenle/Aç** düğmesine basın. Form yoksa oluşturulur ve Excel\'de açılır.'));
kids.push(B('Yalnız sarı **Değer** sütununa yazın. Diğer sütunlar kilitlidir.'));
kids.push(B('Listeli alanlarda (meslek, kullanım, TM dilimi, yangın dakikası) hücreye tıklayıp açılır listeden seçin.'));
kids.push(B('Sayılarda ondalık için virgül kullanın (0,30). Birim yazmayın (m, m²).'));
kids.push(B('Kaydedip kapatın, sonra aracı çalıştırın.'));
kids.push(H2('5.2 Durum sütunu'));
kids.push(table(['İşaret', 'Anlamı'], [
  ['✓ Tamam', 'Değer geçerli.'],
  ['✗ Boş', 'Zorunlu alan boş – doldurun.'],
  ['⚠ Değer hatalı', 'Aralık dışı ya da listede yok. IFC\'ye yazılmaz.'],
  ['⚠ Örnek değer', 'Formun "Örnek" sütunundaki değerle aynı. Örnekler gerçek değildir – gerçeğini yazın.'],
  ['○ Boş', 'Otomatik bulunur ya da isteğe bağlı.'],
], [2400, 7238], { fills: [GREEN, RED, YEL, YEL, null] }));
kids.push(sp());
kids.push(note('Dikkat:', 'Örnek sütunundaki değerleri kopyalamayın. IDS bu değerleri "geçerli" sayar ama Bakanlığa gerçek olmayan bilgi gider. Araç örnek değerleri yakalar ve raporun Uyarılar sayfasında listeler.', RED));
kids.push(H2('5.3 Bilgiler nereden bulunur'));
kids.push(table(['Bilgi', 'Kaynak belge'], [
  ['TAKS, KAKS, ön/yan/arka bahçe mesafesi', 'İmar durumu belgesi'],
  ['Ada, parsel, tapu (taşınmaz) no, arsa alanı', 'Tapu / TKGM parsel sorgu'],
  ['±0.00 kotunun deniz seviyesine göre değeri', 'Kot kesit / aplikasyon krokisi'],
  ['TM dilimi, proje 0,0 noktasının Sağa/Yukarı koordinatı', 'Aplikasyon krokisi (harita mühendisi)'],
  ['Kuzey açısı', 'Vaziyet planı kuzey oku (plan yukarısı kuzeyse 0)'],
  ['Oda sicil no, büro tescil / vergi no', 'Meslek odası üye belgesi, büro tescil belgesi'],
  ['Çatı ve giydirme cephe yangın dayanımı', 'Yangın yönetmeliği / proje müellifi'],
], [4400, 5238], { zebra: true }));

// ---------------- 6
kids.push(H1('6. ALLPLAN modeline nitelik yaz'));
kids.push(P('Bu bölüm Allplan modelindeki elemanlara nitelikleri toplu ve kalıcı yazar. IFC raporunda Allplan\'da girilmesi gereken bilgiler (ör. 16 kaplamanın ya da 12 duvarın yangın dayanımı) burada dakikalar içinde girilir.'));
kids.push(H2('6.1 Kullanım'));
kids.push(N('Palette **ALLPLAN modeline nitelik yaz** seçin. Seçim hemen başlar.', 'ata'));
kids.push(N('**İşlem** listesinden ne yapılacağını seçin (bkz. 6.2). İlk kullanımda **Önce dene (yazmadan rapor ver)** önerilir.', 'ata'));
kids.push(N('**Elemanlar** bölümünde yazılacak eleman türlerini işaretleyin (bkz. 6.3). Pencereyle her şeyi seçebilirsiniz; yalnız işaretli türlere yazılır.', 'ata'));
kids.push(N('**Yazılacak nitelikler** bölümünde yazılacak her satırın kutusunu işaretleyin ve değerini seçin.', 'ata'));
kids.push(N('Gerekirse **Diğer nitelikler (listeden seç)** ile listede olmayan nitelikleri ekleyin.', 'ata'));
kids.push(N('Elemanları pencereyle seçin. Excel rapor neyin yazıldığını gösterir.', 'ata'));
kids.push(H2('6.2 İşlem'));
kids.push(table(['İşlem', 'Ne yapar'], [
  ['**Nitelik yaz** (varsayılan)', 'İşaretli nitelikleri seçilen elemanlara yazar.'],
  ['**Önce dene (yazmadan rapor ver)**', 'Hiçbir şey yazmaz; neyin yazılacağını Excel raporda gösterir.'],
  ['**Nitelik sil**', '"Yazılacak nitelikler"de işaretli nitelikleri seçilen elemanlardan siler (PP02 "Nitelik Sil" gibi).'],
  ['**Yalnız kontrol et (rapor)**', 'Mevcut nitelikleri IDS\'e göre ön kontrol eder; eksikleri listeler.'],
], [3600, 6038], { zebra: true }));
kids.push(sp());
kids.push(P('**Nitelik doluysa**: **Dokunma, yalnız boşlara yaz** (varsayılan) dolu nitelikleri değiştirmez; **Üzerine yaz** hepsini yeni değerle değiştirir.'.replace(/\*\*/g, '')));
kids.push(H2('6.3 Elemanlar'));
kids.push(P('Eleman türleri PP02 e-PYS Nitelik Yaz ile aynı gruplardadır. Her grubun **Tümü** kutusu o gruptaki bütün kutuları açar/kapatır; en alttaki **Tümü** hepsini.'.replace(/\*\*/g, '')));
kids.push(table(['Grup', 'Eleman türleri'], [
  ['Statik', 'Temel, Kolon, Kiriş, Döşeme, Merdiven'],
  ['Mimari', 'Duvar, Çatı Örtüsü, Baca, Çatı Penceresi, Oda, Kapı, Korkuluk, Pencere, Giydirme Cephe'],
  ['Kaplama (IfcCovering)', 'Duvar Kaplaması, Tavan Kaplaması, Döşeme Kaplaması, Süpürgelik'],
], [2800, 6838], { zebra: true }));
kids.push(sp());
kids.push(B('Duvar katmanı, kapı parçası ya da cephe alt elemanı seçilirse nitelik ana elemana (duvar, kapı, giydirme cephe) yazılır.'));
kids.push(B('Kapı/pencere ParaObje\'si seçilirse kapıya/pencereye; çatı penceresi ParaObje\'si seçilirse çatı penceresine yazılır.'));
kids.push(B('**Oda seçilince içindeki kaplamalar da alınır** (kaplama kutuları açıksa). Allplan\'da pencereyle seçimde yalnız oda gelir; kaplamalar odanın içindedir.'));
kids.push(B('**Kapı / Pencere: nitelik yazılacak yer**: Boşluk + ParaObje (varsayılan), yalnız Boşluk ya da yalnız ParaObje. ParaObje\'si olmayan kapı/pencerede boşluğa yazılır.'));
kids.push(B('Yazı, etiket, ölçü, akıllı sembol, donatı gibi öğeler atlanır; raporun **Tanınmayan tipler** sayfasında listelenir.'));
kids.push(H2('6.4 Yazılacak nitelikler'));
kids.push(table(['Palette', 'Allplan niteliği', 'IFC\'de'], [
  ['İsim (Ek-5 biçiminde)', 'İsim', 'Name – DİSİPLİN-KOD-AÇIKLAMA (ör. MM-DVR-BETON_C30)'],
  ['Yangın dayanımı (dk)', 'Yangın Dayanım Sınıfı', 'FireRating'],
  ['Dış eleman', 'Dış Yapı Elemanı', 'IsExternal'],
  ['Taşıyıcı', 'Statik_taşıyıcı', 'LoadBearing'],
  ['Kaçış yolu / Acil çıkış', 'Kaçış Yolu / Acil Çıkış', 'FireExit'],
  ['Malzeme (ör. Beton_C30)', 'Malzeme', 'Malzeme (Malzeme_Özellik biçimi)'],
  ['IFC obje kategorisi', 'IFC obje kategorisi', 'ObjectType'],
], [2800, 2600, 4238], { zebra: true }));
kids.push(sp());
kids.push(P('**İsim** işaretlenince alt seçenekler açılır: Disiplin (Otomatik: taşıyıcılar ST, diğerleri MM), Açıklama ({MALZEME} = malzeme, {MEVCUT} = mevcut ad), Türkçe harfleri çevir, Büyük harf.'.replace(/\*\*/g, '')));
kids.push(note('Neden gerekli?', 'IFC düzeltmesi yalnız dosyada zaten bulunan bilgiyi düzeltebilir (ör. F120 → 120). Modelde hiç girilmemiş yangın dayanımı, dış eleman, malzeme gibi değerleri ancak bu bölüm yazar. Son IDS raporunda kalan duvar/kaplama yangın dayanımı, duvar/pencere dış eleman ve kaplama malzemesi hataları buradan giderilir.', GREEN));
kids.push(H2('6.5 Allplan nitelik adları'));
kids.push(P('Bu bölüm palette kapalı başlar; gerektiğinde okla açılır. Aracın Allplan\'da hangi niteliği arayacağını söyler. Normalde değiştirmeyin. **Nitelik adlarını doğrula → Doğrula** ile her adın bulunup bulunmadığını görün; "BULUNAMADI" çıkarsa Allplan\'daki gerçek adı yazın. A|B yazılırsa önce A, yoksa B aranır.'.replace(/\*\*/g, '')));
kids.push(sp());
kids.push(note('Geri alma yok:', 'Nitelik değişikliği Allplan\'da Ctrl+Z ile geri alınmaz. İlk kullanımda küçük bir seçimle **Önce dene** ile başlayın ve raporu kontrol edin. Yanlış yazılan bir niteliği **Nitelik sil** ile kaldırabilirsiniz.', RED));

// ---------------- 7
kids.push(H1('7. Raporu okumak'));
kids.push(table(['Sayfa', 'İçerik'], [
  ['Özet', 'Uygulanan IDS kuralları; önce/sonra durum, geçen/kalan eleman; Bakanlık aracının sayımıyla hata sayısı.'],
  ['Yapılacaklar', 'Kalan her eksik: kaç eleman, bulunan değer, IDS beklentisi ve Allplan\'da ne yapılacağı. Buradan başlayın.'],
  ['Otomatik Düzeltmeler', 'Araç ne değiştirdi: eleman, alan, eski → yeni değer, kaynak.'],
  ['Kalan Hatalar', 'Eleman listesi (IFC # ile), filtrelenebilir.'],
  ['Uyarılar', 'Otomatik düzeltilemeyenler, Proje Bilgi Formu\'ndaki boş/hatalı/örnek değerler.'],
], [2600, 7038], { zebra: true }));

// ---------------- 8
kids.push(H1('8. Allplan\'da dikkat edilecekler'));
kids.push(table(['Durum', 'Ne yapmalı'], [
  ['Kapı/pencere boşluklarına girilen İsim IFC\'ye gelmiyor (Allplan 2026)', 'Araç adları otomatik düzeltir (5. düzeltme). Allplan\'da uğraşmayın.'],
  ['Giydirme cephe tiriz/traverslerine nitelik girilemiyor', 'Araç giydirme cepheden tamamlar (3. düzeltme).'],
  ['Dosyada birden fazla IfcBuilding var', 'Vaziyet planı ve emsal raporu yapı düzeylerini IFC dışa aktarmaya almayın.'],
  ['Kat/bina alanları ve yükseklikleri eksik', 'IFC dışa aktarma ayarında taban miktarlarını (Base Quantities) açın. Brüt alanı formda proje alan hesabından girin.'],
  ['Mahalde kaplama bilgisi eksik', 'Mahale döşeme/duvar/tavan yüzeyi (kaplama) tanımlayın; malzeme adında "_" olsun (ör. Kireç_Boya), kalınlık > 0.'],
  ['Mahal adı 001, 002 gibi geliyor', 'Allplan\'da mahal no\'yu K##_XXX_### biçiminde girin (ör. K01_D02_007, bodrumda B01_…).'],
  ['Yeni eklenen elemanlarda Kod yazısı / yangın boş', 'PP02 e-PYS Nitelik Yaz ile Kod yazısı; bu aracın 6. bölümü ile yangın dayanımı.'],
], [4200, 5438], { zebra: true }));

// ---------------- 9
kids.push(H1('9. Sorun giderme'));
kids.push(table(['Sorun', 'Çözüm'], [
  ['Palet başlığında sürüm (R14) görünmüyor', 'Library\\ALUPLAN klasöründeki .pyp dosyasını güncelleyip Allplan\'ı yeniden başlatın.'],
  ['"Proje Bilgi Formu bulunamadı" uyarısı', 'Formu Proje Bilgi Formu → Düzenle/Aç ile oluşturun; IFC ile aynı klasörde olmalı.'],
  ['TM dilimi / liste alanı "listede yok"', 'Hücrede açılır listeden seçin.'],
  ['Hata mesajı', '%TEMP%\\ePYS_IDS.log dosyasını ALUPLAN\'a iletin (ilk satırda sürüm yazar).'],
], [4000, 5638], { zebra: true }));
kids.push(sp());
kids.push(P('Allplan dışında da çalışır (komut satırı): python ePYS_IDS_core.py model.ifc --duzelt --form ePYS_Proje_Bilgi_Formu.xlsx'));

const doc = new Document({
  features: { updateFields: true }, creator: 'ALUPLAN', title: 'e-PYS IDS Kontrol – Kullanıcı Kılavuzu',
  styles: {
    default: { document: { run: { font: 'Arial', size: 21 } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { font: 'Arial', size: 32, bold: true, color: NAVY }, paragraph: { spacing: { before: 360, after: 160 }, keepNext: true, outlineLevel: 0 } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { font: 'Arial', size: 25, bold: true, color: NAVY }, paragraph: { spacing: { before: 240, after: 120 }, keepNext: true, outlineLevel: 1 } },
      { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { font: 'Arial', size: 22, bold: true }, paragraph: { spacing: { before: 200, after: 80 }, keepNext: true, outlineLevel: 2 } },
    ]
  },
  numbering: { config: [
    { reference: 'bul', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ...['num', 'kur', 'ata'].map(r => ({ reference: r, levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] })),
  ] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [t('e-PYS IDS Kontrol (R14) – Kullanıcı Kılavuzu', { size: 16, color: '808080' })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [t('ALUPLAN · Sayfa ', { size: 16, color: '808080' }), new TextRun({ children: [PageNumber.CURRENT], size: 16, color: '808080' })] })] }) },
    children: kids
  }]
});
Packer.toBuffer(doc).then(b => { fs.writeFileSync(require('path').join(__dirname, '..', 'ePYS_IDS_Kontrol_Kullanici_Kilavuzu_R14.docx'), b); console.log('ok'); });
