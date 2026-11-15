# Form soru kalıpları

> Soru kalıbı → `me/profile/answers.md` alanı. Cevaplar burada değil.
> Yeni kalıp öğrenildikçe eklenir.

| Soru kalıbı (örnek ifadeler) | Alan | Not |
|---|---|---|
| "Are you legally authorized to work in…", "Work permit" | `work_authorization` | Ülkeye göre evet/hayır |
| "Will you now or in the future require sponsorship" | `requires_sponsorship` | |
| "Desired salary", "Salary expectations", "Compensation expectations" | `salary_expectation_annual` veya `hourly_rate` | Worker'a göre seçilir |
| "Hourly rate", "Rate" | `hourly_rate` | |
| "When can you start", "Earliest start date", "Notice period" | `earliest_start_date` / `notice_period` | |
| "How many hours per week are you available" | `availability_hours_per_week` | |
| "What time zone are you in" | `timezone` | |
| "Are you willing to relocate" | `willing_to_relocate` | |
| "LinkedIn profile", "LinkedIn URL" | `linkedin_url` | |
| "Portfolio", "Website", "GitHub" | `portfolio_url` | |
| "Why do you want to work here", "Why this role" | `why_this_role_template` | tailor ilana göre yazar |
| "Tell us about yourself" | `about_me` | tailor ilana göre kısaltır |
| "How did you hear about us" | — | Kaynak siteyi yaz (ör. "LinkedIn") |
| "If you are based in the United States, confirm your state" (ABD dışı seçenek var) | `work_authorization` / konum | ABD dışındaysa "not located in the United States" seçeneği |
| "Select all the languages you are proficient in" | `answers.md → Diller` | Liste dil-varyantı olabilir (ör. yalnızca "American English") |
| "Skills category that best describes your core strengths" (tek seçim, akademik alan listesi) | — | Kişiye sor; ilanla ve kanıtla en uyumlu alanı öner |
| Eğitim "Discipline" (sabit liste) | `cv-master.md → Eğitim` | Tam karşılık yoksa en yakın seçeneği kişiye sor |
| Demografik / EEO soruları (gender, race, veteran, disability) | — | Kişi aksini söylemedikçe "Decline to self-identify" |

## Öğrenimler
- **Greenhouse formlarında telefon çoğu zaman zorunlu** `k:forms-greenhouse-formlarinda-telefon-cogu-zaman-zorunlu`
  Ülke kodu + numara alanı yıldızlı geliyor. `answers.md → phone` boşsa forma başlamadan sor.
  _dayanak: tek form · güven: orta_
- **Claude in Chrome: form doldururken sekme kapatma** `k:forms-claude-in-chrome-form-doldururken-sekme`
  Doldurulmuş formların olduğu oturumda bir sekme kapatılınca eklentinin sekme grubu dağılabiliyor ve açık formlara erişim
  kayboluyor. Gönderim bitene kadar sekme kapatma; vazgeçilen ilanın sekmesini olduğu gibi bırak.
  Doldurmadan önce her formun cevaplarını başvuru klasörüne (`form-cevaplar.md`) yaz ki yeniden doldurmak hızlı olsun.
  _dayanak: tek oturum · güven: orta_
- **Uzun metin cevapları için tuş vuruşuyla yazma** `k:forms-uzun-metin-cevaplari-icin-tus-vurusuyla`
  Greenhouse (react-select), Ashby ve Dover'da alanı JS ile odakla, metni klavye ile yaz; açılır listelerde yaz + Enter.
  Ashby radyo/checkbox gruplarında `fieldset` içindeki input'a doğrudan tıkla (etikete tıklamak seçimi kaydetmeyebiliyor).
  _dayanak: çok sayıda form · güven: orta_
- **"Yalnızca kendi sözlerim" / AI içerik yasağı taahhüdü** `k:forms-yalnizca-kendi-sozlerim-ai-icerik-yasagi`
  Bazı formlarda zorunlu bir soru var: "I agree to use only my own words ... the use of AI or other generated content will disqualify".
  Bu formlarda açık uçlu cevaplar ve ilana özel CV Claude tarafından yazılmaz; taahhüt kişi adına "Yes" işaretlenmez. Formu açmadan önce
  ATS API'sindeki soru listesini (`?questions=true`) kontrol et ve kişiye baştan söyle: ya kendisi yazar ya başvuru atlanır.
  Aynı formlar lise başarı dilimi, lisans ortalaması gibi cevap bankasında olmayan sorular da sorabiliyor.
  _dayanak: birkaç form · güven: orta_
