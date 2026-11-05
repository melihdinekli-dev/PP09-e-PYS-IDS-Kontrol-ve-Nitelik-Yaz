# DevOps Analizi – PP09 e-PYS IDS Kontrol (05.11.2026)

## Başlangıç durumu (R21 öncesi)

| İlke | Durum | Not |
|---|---|---|
| Sürüm kontrolü | ✗ | Sürümler zip adlarıyla (R1…R21) izleniyordu; kod geçmişi yoktu |
| Kaynak kodun güvenli yeri | ✗ | Kaynak ve üreteçler yalnız bir bulut çalışma oturumundaydı; kullanıcıda yalnız derlenmiş paket vardı |
| Tekrarlanabilir derleme | ~ | Elle sıralı komutlar; çekirdeğin komut satırı bölümü önceki derlemeden kopyalanıyordu (kendine bağımlı) |
| Tek sürüm kaynağı | ✗ | Sürüm 3 yerde elle değişiyordu (script, palet başlığı/sürümü, çekirdek) |
| Otomatik test | ~ | Allplan taklidiyle test betikleri vardı ama elle çalışıyor, sonuç gözle okunuyordu |
| CI | ✗ | – |
| Yayın | ~ | Zip sohbette dosya olarak |
| Değişiklik günlüğü | ~ | KURULUM.md içinde elle |
| Hata takibi | ~ | Excel tabloları |
| Veri gizliliği | ~ | Müşteri IFC/formları ile kod aynı klasörde |

### Bu eksiklerin yol açtığı somut sorunlar
- **R12–R17:** Palette seçim ikinci kez başlatılıyordu (R11'den beri). Hiçbir test kapsamadığı için Allplan'da çökme olarak ortaya çıktı. → `tests/test_nitelik.py::test_secim_yeniden_baslatilmaz`
- **R12:** Aynı adlı palet satırları Allplan'da tek satırda birleşti. → `tests/test_paket.py::test_satir_adlari_benzersiz`
- **R12:** Expander içindeki RadioButtonGroup Allplan'da görünmedi. → `test_islem_acilir_liste`
- **R19:** Allplan'ın boş değeri `<tanımsız>` dolu sayıldı. → `test_tanimsiz_bos_sayilir`
- **R10:** "Çıktı IFC" yalnız ad yazılınca hata. → `test_cikti_yolu_yalniz_ad`
- **Nitelik favorisi (.atfanfx):** Elle üretilen dosya Allplan'ı kilitledi. → Bu dosyalar artık üretilmiyor; Allplan'a kaydettiriliyor.

## Yapılanlar (bu repo)

| İlke | Çözüm |
|---|---|
| Sürüm kontrolü | Git + GitHub; R21 etiketi |
| Kaynak düzeni | `src/core`, `src/allplan`, `resources`, `tools`, `tests`, `docs` |
| Tekrarlanabilir derleme | `python build.py` → paket; çıktı R21 teslim paketiyle birebir aynı (çekirdekte yalnız sürüm damgası farklı) |
| Tek sürüm kaynağı | `VERSION` dosyası |
| Otomatik test | 22 pytest testi: sentetik IFC ile çekirdek, Allplan taklidiyle nitelik yazma, paket/palet kontrolleri |
| Kod denetimi | ruff (sözdizimi ve tanımsız ad hataları) |
| CI | GitHub Actions: her push/PR'da lint + test + paket (Python 3.11 ve 3.13) |
| Yayın | `R*` etiketi → paket otomatik GitHub Release'e |
| Değişiklik günlüğü | `CHANGELOG.md` (R1–R21 geçmişi aktarıldı) |
| Hata takibi | GitHub Issues + hata şablonu (log, sürüm, ekran görüntüsü) |
| Veri gizliliği | `.gitignore` müşteri verisini dışarıda tutar; testler sentetik |

## Kalan riskler ve öneriler

1. **Gizlilik.** Proje kapalı kaynaktır (LICENSE: tescilli). Repo **private** olmalı ve yalnız yetkili kişilere erişim verilmelidir (Settings → Collaborators). Kaynak dosyalarda telif bildirimi bulunur.
2. **Gerçek Allplan testi otomatik değil.** Taklit, Allplan'ın davranışını tam yansıtmaz (çökmeler bunu gösterdi). Her sürümden önce [ALLPLAN_TEST.md](ALLPLAN_TEST.md) listesi uygulanmalı; sonucu Release notuna yazılmalı.
3. **Gerçek model regresyon testi yok.** Büyük müşteri IFC'leri repoya konamaz. Öneri: anonimleştirilmiş orta boy bir test modeli (ör. 1 kat, her eleman türünden birkaç tane) hazırlayıp beklenen "hatalı kontrol" sayısını teste bağlamak.
4. **Büyük dosyalar.** `fixer.py` (~1.200 satır) ve `ePYS_IDS.py` (~1.200 satır) bölünebilir; önce testler genişletilmeli.
5. **Diğer araçlar (PP01–PP06).** Aynı düzenle ayrı repolar ya da tek bir monorepo olarak taşınmalı.
6. **Dal koruması.** `main` dalına doğrudan push kapatılıp PR + yeşil CI zorunlu tutulmalı (Settings → Branches).
