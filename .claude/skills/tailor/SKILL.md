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
     **`--required` listesinin ilk terimi ilanın birincil şartıdır** (genelde ilk sıradaki "must-have";
     bir araç ya da teknoloji adıysa onun adı). ats.py bunu ayrıca izler ve apply'ın kapısı ona bakar.
   - **Listeyi CV'yi yazmadan önce kilitle** (`ilan.md` klasörde olmalı; cv.md henüz yokken yalnızca liste kaydedilir):
     ```bash
     python3 engine/pipeline/ats.py <klasör> --required "SQL; stakeholder management; Tableau" --preferred "Python" --record
     ```
     Liste `<klasör>/ats-terimler.json`'a yazılır. Her terimin en az bir yazımı `ilan.md`'de geçmeli; geçmeyen
     reddedilir. `a|b` aynı şartın yazım farkıdır (kısaltma, İngiliz/Amerikan yazımı); ilanda geçmeyen eş anlamlılar
     ayrıca listelenir; gevşek eşleme kurma. Tekil/çoğul farkı kendiliğinden eşleşir (3 harfli terimlerde değil: `API|APIs`).
   - CV'yi yazdıktan ve her düzenlemeden sonra kayıtlı listeyle ölç: `ats.py <klasör> --record`.
     Eksik zorunlu kelimenin kanıtı varsa CV'ye ekle ve yeniden ölç; kanıtı yoksa "eklenmeyenler"e yaz.
     Yüzde `application.md → ats_eşleşme`'ye yazılır.
   - Kayıtlı listeden terim çıkarmak, zorunludan tercihe indirmek ya da birincil şartı değiştirmek betik tarafından
     reddedilir. İlandan gerçekten yanlış çıkarıldıysa `--cikar-gerekce "…"` ile yapılır, gerekçe dosyada kalır
     ve kişiye söylenir; puanı yükseltmek gerekçe değildir.
   - **Hedef: ATS puanı en az %90 (sabit kural, apply kapısı bunun altını göndermez).** Altındaysa
     `ats.py <klasör> --gate` öneri listesini verir (önce zorunlu kelimeler, +2; sonra tercih, +1).
     Sırayla: (a) kanıtı profilde olan ama CV'de geçmeyen kelimeleri ilandaki yazımıyla işle;
     (b) kanıt bankasında olmayanları kişiye sor, gelen kanıtı `evidence-bank`'e yazıp işle; (c) yeniden ölç.
     Kanıtla %90'a çıkılamıyorsa bunu açıkça söyle — uydurma yok.
   - Anahtar kelime listesi ilandan **CV'yi yazmadan önce** çıkarılır ve sonradan CV'ye uysun diye budanmaz
     ya da gevşetilmez; aynı kavramın ilandaki yazım farkları `a|b` ile verilebilir.
   - Ön yazıda eksik bir şartı kendiliğinden itiraf etme; o boşluğa en yakın gerçek kanıtı öne çıkar.
     Uydurma yok, ama "henüz X'te deneyimim yok" cümlesini de kişi istemedikçe yazma.
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
   PDF'i CV'nin **son** hâlinden üret: kapı, cv.md PDF'ten yeniyse durur (ölçülen CV ile yüklenen CV aynı olmalı).
6. Kişiye göster: ATS sonucu, CV farkları (ana CV'ye göre ne öne çıktı), eklenmeyenler, ön yazı.
