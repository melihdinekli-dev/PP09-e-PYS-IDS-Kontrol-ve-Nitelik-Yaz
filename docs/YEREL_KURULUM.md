# Yerel geliştirme ortamı (Windows)

## 1. Bir kez kurulacaklar

| Araç | Neden | Not |
|---|---|---|
| Git for Windows | Repo, commit, push | "Git Credential Manager" seçili kalsın; ilk push'ta GitHub girişi tarayıcıdan yapılır |
| Python 3.13 | Test ve paket (Allplan 2026 da 3.13) | "Add Python to PATH" işaretli |
| VS Code | Düzenleme | Python ve GitLens eklentileri |

```
git config --global core.autocrlf false
git config --global user.name "Melih Dinekli"
git config --global user.email "melih@aluplan.com.tr"
```

## 2. Repoyu al

```
cd %USERPROFILE%\source
git clone https://github.com/melihdinekli-dev/PP09-e-PYS-IDS-Kontrol-ve-Nitelik-Yaz.git PP09-e-PYS-IDS
cd PP09-e-PYS-IDS
```
(İlk kez bundle'dan: `git clone PP09_repo_R21.bundle PP09-e-PYS-IDS`, ardından
`git remote set-url origin https://github.com/melihdinekli-dev/PP09-e-PYS-IDS-Kontrol-ve-Nitelik-Yaz.git` ve
`git push -u origin main --tags`.)

## 3. Python ortamı

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
python -m pytest -q
python build.py --kontrol
```

## 4. Allplan'a kurma

```
python tools\kur.py               derler, mevcut PP09 dosyalarını yedekler, yenilerini Allplan'a kopyalar
python tools\kur.py --geri-al     son yedeği geri yükler
```
- Hedef: `Documents\Nemetschek\Allplan\2026\Usr\Local` (farklıysa `--hedef` ya da `ALLPLAN_USR_LOCAL` ortam değişkeni).
- Yedekler: `Documents\e-PYS IDS Yedekler\<tarih>_<sürüm>\` – Allplan kütüphanesinin dışında.
- Yalnız PP09 dosyaları değişir; ALUPLAN klasöründeki diğer araçlara dokunulmaz.
- Allplan'ı yeniden başlatın; palet başlığında sürüm görünür.

`Usr\Local\PythonPartsScripts\ALUPLAN` içindeki PP09 dosyalarını **elle düzenlemeyin**; her kurulumda yeniden üretilir. Kod `src/`, palet `tools/gen_pyp.py`, form `tools/gen_form.py` içindedir.

## 5. Günlük akış

1. Dal: `git switch -c fix/...` ya da `feature/...`
2. Değiştir → `python -m pytest -q` (yeni hata için önce test)
3. `python tools\kur.py` → Allplan'da dene
4. `git add -A` → `git commit -m "..."` → `git push -u origin <dal>` → GitHub'da Pull Request (CI yeşil olmalı)
5. Sürüm: `VERSION` artır, `CHANGELOG.md` ve `docs/KURULUM.md` "Sürümler", `docs/ALLPLAN_TEST.md` listesini uygula,
   `git tag R22 && git push origin R22` → paket Releases'e gelir.

## 6. Klasör düzeni

```
%USERPROFILE%\source\PP09-e-PYS-IDS\     kod (git)
   dist\                                  derlenmiş paketler (git'e girmez)
Allplan 2026\Usr\Local\...\ALUPLAN\       yalnız tools\kur.py ile güncellenir
Belgeler\e-PYS IDS Raporları\             nitelik raporları (git'e girmez)
Belgeler\e-PYS IDS Yedekler\              kurulum yedekleri
Proje klasörleri (IFC, Proje Bilgi Formu) müşteri verisi – repoya asla girmez
```
