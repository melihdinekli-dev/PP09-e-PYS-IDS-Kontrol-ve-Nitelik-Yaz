# PP09 e-PYS IDS Kontrol ve Nitelik Yaz – Devir Notu (Handoff)

Son güncelleme: 05.11.2026 20:55 · Güncel sürüm: **R21**

## 1. Nerede ne var

| Ne | Yer |
|---|---|
| Kaynak kod (tek doğru kaynak) | GitHub: `melihdinekli-dev/PP09-e-PYS-IDS-Kontrol-ve-Nitelik-Yaz` (şimdilik **public**, ileride private) |
| Son paket | GitHub → Releases → **R21** → `ePYS_IDS_Allplan2026_R21.zip` |
| Allplan kurulumu | `Documents\Nemetschek\Allplan\2026\Usr\Local\PythonPartsScripts\ALUPLAN\` ve `...\Library\ALUPLAN\` |
| Allplan logu | `%TEMP%\ePYS_IDS.log` (ilk satır: "Script yüklendi R…") |
| Nitelik raporları | `Belgeler\e-PYS IDS Raporları\` |
| Kurulum yedekleri (`tools\kur.py`) | `Belgeler\e-PYS IDS Yedekler\` |
| Proje (NNN) favorileri | `C:\Data\Allplan\Allplan 2026\Prj\MM-PRJ-202645.prj\Favoriler - Proje\` |
| Son IDS raporu | `IDS_Hata_Raporu_EPYS_Allplan_R11.xlsx` (NNN_01a, **199 hatalı kontrol**) |
| Yapı strüktürü takip tablosu | `PP09_Yapi_Strukturu_Bina_Nitelikleri_R3.xlsx` (Arsa / Bina IDS zorunlu nitelikleri) |
| Belgeler | `docs/KURULUM.md`, `docs/YEREL_KURULUM.md`, `docs/ALLPLAN_TEST.md`, `docs/DEVOPS_ANALIZ.md`, kullanıcı kılavuzu R14 |

## 2. GitHub / DevOps durumu

- `main`: 10 commit, CI yeşil (Python 3.11 + 3.13: ruff, 24 pytest, paket).
- Release R21 yayınlandı; **R\* etiketiyle** Release iş akışı paketi otomatik ekler.
- `main` **korumalı**: yalnız Pull Request; `test (3.11)` ve `test (3.13)` geçmeden birleşmez. Onay (approval) zorunlu değil. Not: GitHub Free'de koruma yalnız public repoda uygulanır – private'a geçince Pro gerekir.
- Claude oturumundan: dal push **olur**; etiket push ve GitHub API yazma **olmaz** → Release/etiket ve PR birleştirme, Claude uygulamasının yerleşik tarayıcısından (GitHub girişi yapılı) yapılır.
- Yerel geliştirme: `docs/YEREL_KURULUM.md` (Git, Python 3.13, `.venv`, `python -m pytest -q`, `python tools\kur.py`).

## 3. Allplan'daki son durum

- Kullanıcı en son **R18**'i Allplan'da denedi (nitelik yazma çalıştı; 23 elemana yangın 120 yazıldı). R19–R21 teslim edildi; **Allplan'a kurulu sürüm palet başlığından kontrol edilmeli**, R21 değilse `python tools\kur.py` ya da Release zip'i.
- R19: `<tanımsız>` boş sayılır · R20: Son rapor → Aç ve rapor klasörü · R21: baca katmanlarına kendisine yazılır.

## 4. Açık işler (IDS raporu R11, NNN_01a)

| Adım | Konu | Kontrol | Durum |
|---|---|---|---|
| 1–2 | 52 mahalde tavan kaplaması yok (banyo 16, duş 14, Y. odası 14, asansör 5, su deposu, salon K00_D04_006, rüzgarlık) | 104 | **IDS yazarına soruldu – yanıt bekleniyor** |
| 3–4 | 16 kaplama (14 dış cephe sıvası + 2 kristalize yalıtım): yangın + Kod yazısı | 32 | Yangın: PP09 Nitelik yaz; Kod yazısı: PP02 |
| 5 / 9 | K04 çatı: 8 Beton_C25 duvar yangın; 4 "Ytong_Duvar" duvar (hepsi K04_DVR_076) yangın + dış eleman + Kod yazısı ayrımı | 16 | Yapılmadı |
| – | 2 fazla IfcBuilding (Vaziyet Plan, emsal raporu) | 26 | IFC dışa aktarımında yalnız "00" binası seçilecek |
| 23 | K04 asansör süpürgeliği malzemesi (K04_SPG_024) | 1 | **IDS yazarına soruldu** |
| 24–25 | Çatı penceresi MM-PNC-CATI_ALU_40_40_CM: dış eleman + Kod yazısı | 2 | Yapılmadı |
| diğer | mahal döşeme (6×2) / duvar (3×2) kaplaması, adsız 4 döşeme, 2 mahal adı | ~18 | Yapılmadı |

Ek konular:
- **Proje Bilgi Formu:** sicil no, büro adı, tapu no, TAKS, KAKS, çekmeler, kot, koordinat **örnek değerde**. Sicil no (00020418) "büro no" alanına girilmiş. Arsa alanı Allplan'da 1436,80.
- **Kat adları / mahal no kayması:** MM-BNK-K01 (+0,90 zemin) içindeki daire mahalleri K00_…; karar bekliyor (katları K00–K03 yap ya da mahalleri yeniden numarala). IDS yazarına da sorulabilir.
- **Pencereler:** tüm pencerelerde Dış eleman = Hayır (IDS hata saymıyor ama cephe pencereleri Evet olmalı).
- **Bina favorisi** (`Bina Bilgileri-Yapı Strüktürü Nitelikleri.atfanfx`): IFC Entity = **IfcCovering** yazıyor → bina düzeyinde **IfcBuilding** olmalı.
- **Yapı strüktürü nitelikleri:** arsa ve bina IDS zorunlu nitelikleri Allplan'da girilecek; favori Allplan'a kaydettirilecek (takip: Excel R3).

## 5. Dersler (tekrarlanmasın)

- Palette seçimi `modify_element_property` içinde **yeniden başlatma** → Allplan çöker (R17).
- `.pyp`: Row'ların **Text'i benzersiz** olmalı; Expander içinde **RadioButtonGroup yerine StringComboBox**.
- Nitelik yazma: `ChangeAttributes([(id, değer)], liste, False, False)` (PP02 yolu); Allplan boş değeri `<tanımsız>` döndürür.
- **Nitelik favorisi (.atfanfx) elle üretilmez** – Allplan'ı kilitledi; Allplan'a kaydettirilir.
- Her sürüm öncesi `docs/ALLPLAN_TEST.md` (11 adım) Allplan'da uygulanır.

## 6. Yarın başlangıç

1. Allplan'da palet başlığını kontrol et (R21 mi?).
2. IDS yazarının yanıtı geldiyse adım 1–2 ve 23'e karar ver.
3. Yeni IFC'yi dışa aktar (yalnız "00" binası), PP09 ile düzelt, IFC'yi Claude'a gönder → **R12 karşılaştırmalı rapor**.
4. Yeni sohbette aşağıdaki istemi kullan.

### Başlangıç istemi

```
PP09 e-PYS IDS Kontrol ve Nitelik Yaz üzerinde çalışmaya devam ediyoruz.
Önce proje belgesi claude/PP09_HANDOFF.md'yi ve GitHub reposunu
(melihdinekli-dev/PP09-e-PYS-IDS-Kontrol-ve-Nitelik-Yaz, güncel sürüm R21) oku.
Kurallar: kod değişiklikleri repoda bir dalda yapılır, testler eklenir, PR açılır
(main korumalı); sürüm VERSION dosyasından; paketler ePYS_IDS_Allplan2026_Rn.zip,
Excel çıktıları _Rn ekiyle. Allplan'a özgü dersler handoff 5. bölümde.
Bugün: [ör. ekteki yeni IFC ile R11'e göre karşılaştırmalı R12 IDS raporu ver /
IDS yazarının yanıtı şu: … / Nitelik yaz'da şu sorun var: …]
```
