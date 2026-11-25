<!-- durum: tarama çalışır · başvuru taslak -->
# Greenhouse

- **tür:** ATS · **başvuru_yöntemi:** otomatik (gönderim öncesi kişi onayı ile)
- **kapsam:** küresel

## Tarama
- `GET https://boards-api.greenhouse.io/v1/boards/<token>/jobs?content=true`
- Token: `boards.greenhouse.io/<token>`, `job-boards.greenhouse.io/<token>` veya kariyer sayfasındaki
  embed (`job_board?for=<token>`). `scan.py detect` bunları bulur.
- Yer bilgisi: `metadata` içindeki "Location Type" (her şirkette yok).

## Başvuru
1. `apply_url` tarayıcıda açılır.
2. Standart alanlar + özel sorular: `knowledge/forms.md` → `me/profile/answers.md`.
3. CV (ve varsa ön yazı) yüklenir.
4. **Gönderimden önce dur, kişiye göster.**

## Durma noktaları
CAPTCHA, giriş gerekmesi, `answers.md`'de karşılığı olmayan soru, ilan özetiyle çelişen form bilgisi.
- Tarih: `first_published` → yayın, `updated_at` → son güncelleme/yeniden yayım. Yaş filtresi ikisinden yenisine bakar
  (`me/sources.json → max_age_kapsam: hepsi` ise kariyer sayfalarına da uygulanır).
