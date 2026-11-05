# Allplan'da sürüm öncesi test listesi

Otomatik testler Allplan taklidiyle çalışır; gerçek Allplan davranışını tam yansıtmaz. Her sürümden (R etiketi) önce bu liste Allplan 2026'da uygulanır ve sonucu Release notuna yazılır.

Hazırlık: Projeyi kaydedin. Paketi kurun (`ePYS_IDS.py`, `ePYS_IDS_core.py`, `.pyp` …), Allplan'ı yeniden başlatın.

| # | Adım | Beklenen | Sonuç |
|---|---|---|---|
| 1 | Kütüphane → ALUPLAN → e-PYS IDS Kontrol | Palet başlığı "e-PYS IDS Kontrol (R…)" | |
| 2 | `%TEMP%\ePYS_IDS.log` ilk satır | "Script yüklendi R…" | |
| 3 | IFC dosyasını kontrol et ve düzelt → küçük bir IFC → ▶ Çalıştır | Mesaj kutusu, `<ad>_IDS.ifc` ve rapor oluşur | |
| 4 | ALLPLAN modeline nitelik yaz: Elemanlar paleti | Statik/Mimari/Kaplama satırları iki sütun; Tümü kutuları çalışır | |
| 5 | İşlem = Önce dene, Yangın dayanımı işaretli, 2 duvar seç | Özet penceresi; "Deneme: … (yazılmadı)"; Allplan kapanmaz | |
| 6 | İşlem = Nitelik yaz, aynı 2 duvar | Özet "2 elemana … yazıldı"; Bilgi Paleti'nde değer görünür | |
| 7 | Bir oda seç (kaplama kutuları açık) | Özette tavan/döşeme/duvar kaplaması ve süpürgelik sayılır | |
| 8 | Bir kapının ParaObje'sini seç | Nitelik kapıya (ve ParaObje'ye) yazılır | |
| 9 | İşlem = Nitelik sil, aynı 2 duvar | Değer silinir | |
| 10 | Sonuç → Son rapor → Aç | Excel raporu açılır (Belgeler\e-PYS IDS Raporları) | |
| 11 | Palette üst seçeneği ve İşlem'i değiştirip yeniden seç | Allplan kapanmaz (R17) | |

Sorun çıkarsa: `%TEMP%\ePYS_IDS.log` dosyasını ve ekran görüntüsünü GitHub Issue'ya ekleyin.
