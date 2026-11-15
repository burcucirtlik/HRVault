<!-- durum: tarama çalışır · başvuru taslak -->
# Lever

- **tür:** ATS · **başvuru_yöntemi:** otomatik (gönderim öncesi kişi onayı ile)
- **kapsam:** küresel

## Tarama
- `GET https://api.lever.co/v0/postings/<token>?mode=json`
- Token: `jobs.lever.co/<token>`. Çalışma tipi `categories.commitment`, yer `workplaceType`.
- Başvuru linki: `applyUrl` (`jobs.lever.co/<token>/<id>/apply`).

## Başvuru
1. `apply_url` tarayıcıda açılır.
2. Standart alanlar + özel sorular: `knowledge/forms.md` → `me/profile/answers.md`.
3. CV (ve varsa ön yazı) yüklenir.
4. **Gönderimden önce dur, kişiye göster.**

## Durma noktaları
CAPTCHA, giriş gerekmesi, `answers.md`'de karşılığı olmayan soru, ilan özetiyle çelişen form bilgisi.
