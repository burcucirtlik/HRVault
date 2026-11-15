<!-- durum: bekliyor — e-posta kaynağı seçilmedi -->
# LinkedIn

- **başvuru_yöntemi:** yarı-otomatik
- **kapsam:** küresel

## Kurallar
LinkedIn kullanıcı sözleşmesi bot ile veri çekmeyi ve otomatik başvuruyu yasaklıyor;
ihlalde hesap kısıtlanabiliyor. Bu yüzden:
- Sayfaları otomatik gezip toplu veri çekme yok.
- "Easy Apply" otomatik gönderilmez; son adımı kişi yapar.

## Profil okuma (coach §1a)
Kişinin **kendi** profili, kişinin isteğiyle ve kendi oturumuyla, tek tek sayfa açılarak okunur.
Bu toplu veri çekme değildir; yine de sayfaları sırayla ve makul hızda aç.

1. Tarayıcıda profil linkini aç (`linkedin.com/in/<slug>/`). Giriş sayfası gelirse kişiden tarayıcıda
   kendisinin giriş yapmasını iste; şifre girme, CAPTCHA geçme.
2. Ana sayfadan: ad, headline, konum, "About", öne çıkanlar (Featured), bölüm başlıkları.
3. Her bölümün tam listesi için detay sayfaları (kısaltılmış listede kalma):
   `/in/<slug>/details/experience/` · `education/` · `skills/` · `certifications/` · `projects/` ·
   `recommendations/` · `languages/` · `honors/` · `volunteering-experiences/` · `courses/` · `publications/`
   Sayfa yoksa (404 ya da ana profile yönlenme) o bölüm boştur; atla.
4. Deneyimde aynı şirketteki birden çok rol ayrı ayrı alınır; "…see more" ile kısaltılmış açıklamaları aç.
5. Öneriler: yazan kişinin unvanı, ilişki (yönetici, ekip arkadaşı, müşteri) ve övdüğü yetkinlikler.
6. Son paylaşımlar: `/in/<slug>/recent-activity/all/` — yalnızca konu ve ton için ilk ~10 içerik.
7. Okuma için sayfa metni yeterli (`get_page_text` / `read_page`); ekran görüntüsü gerekmez.

**Yedek yollar** (tarayıcıda okunamazsa):
- Profilde "More → Save to PDF" çıktısı → kişi dosyayı verir → Read.
- LinkedIn veri arşivi (Settings → Data privacy → Get a copy of your data): Profile, Positions,
  Education, Skills, Certifications, Recommendations, Endorsements CSV'leri. En eksiksiz kaynak; birkaç
  dakika ile bir gün arasında hazırlanır.

Okunan her şey yalnızca `me/` içine yazılır.

## Tarama
- Birincil: kişinin LinkedIn'de kurduğu **iş alarmı e-postaları** (worker başına bir alarm önerilir:
  çalışma tipi + yer + rol filtreli). E-postadan ilan linkleri ve başlıklar alınır.
- İlan "Apply on company website" ise asıl ATS'yi (Greenhouse, Lever…) bul ve o adaptöre devret.

## Başvuru
1. tailor çıktısı + form cevapları hazırlanır.
2. Kişiye: ilan linki, yüklenecek CV, alan alan cevaplar.
3. Kişi gönderdiğini söyleyince `application.md` → `başvuruldu`.

## Şu an
- Kişi ilan linki veya alarm e-postası metnini verir → scan skill'i §5 ile tarama dosyasına ekler.

## TODO
- E-posta kaynağı (Gmail bağlayıcısı vb.) netleşince alarm e-postalarını otomatik oku.
