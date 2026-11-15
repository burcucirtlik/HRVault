---
name: tailor
description: Onaylanan bir ilan için ATS simülasyonu yapar ve kanıt bankasından ilana özel CV ile (gerekirse) ön yazı üretir. "CV hazırla", "bu ilana göre CV", "ön yazı yaz" veya apply'dan önce kullan.
---
<!-- durum: çalışır -->
# tailor

## Doğruluk kuralı (değişmez)
Yalnızca `me/profile/` içinde dayanağı olan bilgi kullanılır. Mevcut deneyim yeniden
sıralanır ve ifade edilir; olmayan yetkinlik, rakam, unvan veya deneyim **asla** eklenmez.
İlanın istediği ama kanıtı olmayan anahtar kelimeler "eklenmeyenler" listesine yazılır.
`me/learnings.md → Profil gerçekleri` maddeleri (kullanılmayacak roller, unvan düzeltmeleri) her CV'de uygulanır.

## Saklama kuralı (değişmez)
**Her hazırlanan CV ve ön yazı, başvurunun kendi klasöründe saklanır** — md kaynağı ve PDF birlikte.
Başka yere (masaüstü, scratchpad, indirilenler) CV yazılmaz; forma yüklenen dosya da bu klasördeki PDF'tir.
Gönderilmiş bir başvurunun PDF'i yeniden üretilmez: işverenin elindeki sürümle aynı kalmalı.
Aynı ilana ikinci bir sürüm gerekirse `cv-v2.md` olarak yanına yazılır, eskisi silinmez.

## Adımlar
1. Başvuru klasörü: `me/pipeline/applications/<YYYY-MM-DD>-<şirket>-<rol>/`
   - `ilan.md` (tam metin; ilan kaldırılabilir),
   - `application.md` (`engine/templates/documents/application.md`): `ilan_id` (tarama dosyasındaki id),
     `worker`, `uygunluk_puanı` (score'dan) **mutlaka** dolu.
2. **ATS simülasyonu** (`knowledge/ats.md`):
   - İlandan zorunlu ve tercih edilen anahtar kelimeleri çıkar (ilandaki yazımıyla).
   - CV'yi yazdıktan sonra ölç ve kaydet:
     ```bash
     python3 engine/pipeline/ats.py <klasör> --required "SQL; stakeholder management|stakeholders; Tableau" --preferred "Python" --record
     ```
     `a|b` eş anlamlıdır. Eksik zorunlu kelimenin kanıtı varsa CV'ye ekle ve yeniden ölç;
     kanıtı yoksa "eklenmeyenler"e yaz. Yüzde `application.md → ats_eşleşme`'ye yazılır.
3. **CV** → `<klasör>/cv.md` (`engine/templates/documents/cv.md`, `knowledge/writing.md`):
   - İlk satır `# Ad Soyad` (PDF adı buradan türetilir), altında iletişim satırı — başlık/altlıkta değil.
   - Dil: ilanın dili. Uzunluk ve vurgu: worker dosyasındaki "CV vurgusu".
   - İlanla en alakalı maddeler ve yetkinlikler önce; anahtar kelimeler ilandaki haliyle.
4. **Ön yazı** (`preferences.md: ön_yazı` ve ilan istiyorsa) → `<klasör>/cover-letter.md`,
   `engine/templates/documents/cover-letter.md`, worker'daki ton.
5. **PDF:**
   ```bash
   python3 engine/pipeline/render_pdf.py <klasör>          # cv.md (+ cover-letter.md) → PDF, aynı klasöre
   ```
   `application.md`'ye `cv_pdf` / `ön_yazı_pdf` yazılır. PDF'i bir kez aç ve kontrol et (sayfa sayısı, taşma).
6. Kişiye göster: ATS sonucu, CV farkları (ana CV'ye göre ne öne çıktı), eklenmeyenler, ön yazı.
