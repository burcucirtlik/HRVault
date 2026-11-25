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
| "Are you willing to relocate", "Relocationbereitschaft nach <Ülke>?" | `willing_to_relocate` | Hedef ülke kişinin zaten yaşadığı ülkeyse "hayır" yazma (bkz. Öğrenimler) |
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
- **Hazırlıktan önce önceki başvuruyu kontrol et** `k:forms-hazirliktan-once-onceki-basvuruyu-kontrol-et`
  Kişi vault dışında da başvurmuş olabilir; aynı rol bir iş ilanı sitesinde yeni bir ilan numarasıyla yeniden
  yayınlanabilir. Bazı kariyer siteleri aynı role belli bir süre (ör. 90 gün) yeniden başvuruyu kabul etmez.
  CV hazırlamadan önce başvuru kayıtlarına ve, kişi oturumluysa, sitenin Apply sayfasına bak.
  _dayanak: tek başvuru · güven: orta_
- **Profil değişince kariyer sitesi profillerini de gözden geçir** `k:forms-profil-degisince-kariyer-sitesi-profillerini`
  Bazı kariyer siteleri önceki başvurudan kalan kariyer profilini (deneyim, tarih, dil listesi) saklar ve yeni
  başvuruya otomatik ekler. Kişinin profili ya da ana CV'si değiştiğinde bu kayıtlı profiller eski kalır ve yeni
  CV ile çelişebilir. Bir sitede ikinci kez başvurmadan önce kayıtlı profili CV ile karşılaştır, farkları kişiye göster.
  _dayanak: tek başvuru · güven: orta_
- **Şirketin kendi kariyer formunda dosya yüklemek için Claude in Chrome kullan** `k:forms-sirketin-kendi-kariyer-formunda-dosya-yuklemek`
  Uygulama içi tarayıcı dosya seçemez; kendi kariyer sitesi formlarında (LinkedIn'den yönlendirilen şirket linkleri
  dahil) CV'yi Claude in Chrome'un dosya yükleme aracıyla ver. LinkedIn yönlendirme linkini açma; asıl şirket
  adresini çöz ve doğrudan onu aç. Tarih alanları tarih seçici kullanabilir: yazılan metin geçersiz sayılırsa
  seçiciden tarihi tıkla ve alanda gösterilen biçimi kontrol et. Tek rakamlık maaş alanı cevap bankasındaki aralıktan
  yanıtlanamaz; kişiye sor.
  _dayanak: tek başvuru · güven: orta_
- **Taşınma sorusu kişinin zaten yaşadığı ülkeyi soruyorsa "hayır" deme** `k:forms-tasinma-sorusu-kisinin-zaten-yasadigi-ulke`
  "Willing to relocate to <Ülke>?" sorusuna cevap bankasındaki genel "taşınmam, yalnızca remote" cevabını körü körüne verme.
  Kişi zaten o ülkedeyse "hayır", işe alım uzmanına "ülke dışında yaşıyor ve gelmeyecek" diye okunabilir; yalnızca
  o ülke içinden remote çalışmaya izin veren ilanlarda bu bir eleme sebebi olur. Yabancı ülke kodlu telefon bu izlenimi
  güçlendirir. Soru hangi yeri soruyor, kişi nerede yaşıyor: ikisini karşılaştır; belirsizse kişiye sor, açıklama alanı
  varsa konumu yaz.
  _dayanak: tek başvuru (hızlı ret, sebep doğrulanmadı) · güven: düşük_
- **Ashby'de "otomatik değerlendirme" rızası kişiye bırakılır; açık uçlu kanıt soruları sonradan çıkabilir** `k:forms-ashby-otomatik-degerlendirme-rizasi-kisiye-birakilir`
  Bazı Ashby formlarında zorunlu bir "başvurumun otomatik araçlarla değerlendirilmesini kabul ediyorum" Evet/Hayır sorusu var; bu bir rıza,
  doldurma. Yerleşik tarayıcıda dosya yüklenemez: CV'yi kişi yükler (ya da Claude in Chrome kullan). reCAPTCHA'yı kişi geçer.
  Form CV'den sonra "kamuya açık bir parça (profil değil, tek içerik) linkle ve kaç kişi gördü", "sıfırdan başlattığın topluluk" gibi
  açık uçlu sorular ekleyebilir: kanıt bankasında link ya da sayı yoksa uydurma, kişiden iste.
  _dayanak: tek başvuru · güven: orta_

