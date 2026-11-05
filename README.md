# PP09 – e-PYS IDS Kontrol ve Nitelik Yaz (Allplan 2026)

ALUPLAN'ın Allplan 2026 PythonPart'ı. Bakanlığın **e-PYS IDS** kontrolüne hazırlık için iki iş yapar:

1. **IFC dosyasını kontrol et ve düzelt** – Allplan'dan alınan IFC'yi bakanlığın `EPYS_IDS.ids` dosyasına (161 kural) göre denetler, dosyadaki bilgilerle ve Proje Bilgi Formu'yla düzeltip `<ad>_IDS.ifc` ve Excel rapor üretir. e-PYS IFC (PP03) eşlemesi de içindedir.
2. **ALLPLAN modeline nitelik yaz** – Seçilen elemanlara IDS niteliklerini (İsim, yangın dayanımı, dış eleman, taşıyıcı, kaçış yolu, malzeme …) toplu yazar, siler, dener ya da ön kontrol eder. Eleman tanıma PP02 e-PYS Nitelik Yaz R62 ile aynıdır.

Kullanım ve kurulum: [docs/KURULUM.md](docs/KURULUM.md) · Kullanıcı kılavuzu: [docs/](docs/) · Sürüm notları: [CHANGELOG.md](CHANGELOG.md)

## Depo düzeni

```
src/core/        IFC okuma (ifc_step, ifc_model), IDS okuma ve denetim (ids_reader, checker),
                 düzeltme (fixer), rapor (report), akış ve Proje Bilgi Formu (engine), komut satırı (cli)
src/allplan/     Allplan sarmalayıcı (ePYS_IDS.py) ve e-PYS IFC çekirdeği (ePYS_IDS_IfcDuzenle.py)
resources/       Bakanlık IDS dosyası, eşleme kuralları, kütüphane simgesi
tools/           Paket parçalarını üretenler: merge.py (çekirdeği tek dosyaya birleştirir),
                 gen_pyp.py (palet), gen_form.py (Proje Bilgi Formu şablonu), kur.py (Allplan'a kurulum), icon.py
tests/           pytest: çekirdek (sentetik IFC), nitelik yazma (Allplan taklidi), paket/palet kontrolleri
docs/            Kurulum, kullanıcı kılavuzu, DevOps analizi, Allplan test listesi
build.py         Paket üretimi -> dist/ePYS_IDS_Allplan2026_<VERSION>.zip
VERSION          Tek sürüm kaynağı (ör. R21) – palet başlığı, script ve çekirdek buradan damgalanır
```

## Geliştirme

```bash
pip install -r requirements-dev.txt
python -m pytest -q                 # tüm testler
python build.py --kontrol           # paket + içerik kontrolü
python dist/ePYS_IDS_Allplan2026_R21/PythonPartsScripts/ALUPLAN/ePYS_IDS_core.py model.ifc --duzelt   # Allplan dışında
```

Allplan'a kurmak / geri almak (yedekli):

```bash
python tools/kur.py           # derle + yedekle + Usr\Local'e kopyala
python tools/kur.py --geri-al # son yedeğe dön
```

Windows'ta adım adım kurulum ve günlük akış: [docs/YEREL_KURULUM.md](docs/YEREL_KURULUM.md).

Çekirdek yalnız Python standart kütüphanesini kullanır; `openpyxl` yalnız form şablonu üretimi ve testler için gerekir.

## Sürüm yayınlama

1. Değişikliği bir dalda (`feature/...`, `fix/...`) yapın, Pull Request açın; CI yeşil olmalı.
2. `VERSION` dosyasını artırın (`R22`), `CHANGELOG.md` ve `docs/KURULUM.md` "Sürümler" bölümüne not ekleyin.
3. Paketi Allplan'da [docs/ALLPLAN_TEST.md](docs/ALLPLAN_TEST.md) listesiyle deneyin.
4. `main`'e birleştirip etiketleyin: `git tag R22 && git push origin R22` – GitHub Actions paketi üretir ve **Releases** sayfasına koyar.

## Veri gizliliği

Müşteri IFC'leri, Proje Bilgi Formları, IDS raporları ve nitelik favorileri (`*.atfanfx`) repoya **eklenmez** (`.gitignore`). Bunlar sicil no, adres, tapu bilgisi gibi kişisel/resmî veriler içerir. Testler yalnız `tests/fixtures/` içindeki sentetik dosyaları kullanır.

## Lisans

Tescilli – bkz. [LICENSE](LICENSE). © ALUPLAN, Allplan Türkiye Distribütörü.
