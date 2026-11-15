<!-- durum: tarama çalışır · başvuru taslak -->
# Ashby

- **tür:** ATS · **başvuru_yöntemi:** otomatik (gönderim öncesi kişi onayı ile)
- **kapsam:** küresel

## Tarama
- `GET https://api.ashbyhq.com/posting-api/job-board/<token>?includeCompensation=true`
- Token: `jobs.ashbyhq.com/<token>`. Ücret `compensation.compensationTierSummary`.
- Başvuru linki: `applyUrl`.

## Başvuru
1. `apply_url` tarayıcıda açılır.
2. Standart alanlar + özel sorular: `knowledge/forms.md` → `me/profile/answers.md`.
3. CV (ve varsa ön yazı) yüklenir.
4. **Gönderimden önce dur, kişiye göster.**

## Durma noktaları
CAPTCHA, giriş gerekmesi, `answers.md`'de karşılığı olmayan soru, ilan özetiyle çelişen form bilgisi.
