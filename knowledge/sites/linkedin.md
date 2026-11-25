# linkedin — öğrenimler

> Bu sitede çalışırken öğrenilen genel bilgiler. Kişisel veri yok.

## Öğrenimler
- **Profil bölümlerinin tam listesi detay sayfalarında** `k:linkedin-profil-bolumlerinin-tam-listesi-detay-sayfalarinda`
  Ana profil her bölümü kısaltılmış gösterir; tam liste `/in/<slug>/details/<bölüm>/` sayfalarında
  (experience, education, skills, certifications, projects, recommendations, languages, honors,
  volunteering-experiences, courses, publications). Paylaşımlar: `/in/<slug>/recent-activity/all/`.
  _dayanak: genel bilgi · güven: orta (LinkedIn yolları değişebilir; ilk kullanımda doğrula)_
- **Detay sayfaları tembel yükleniyor; sonuna kadar kaydırmadan liste eksik kalır** `k:linkedin-detay-sayfalari-tembel-yukleniyor-sonuna-kadar`
  `details/skills/` gibi uzun listeler kaydırdıkça parça parça yükleniyor (altta dönen bir yükleme simgesi çıkıyor).
  Sayfa metnini okumadan önce, simge kaybolup footer görünene kadar birkaç kez kaydır ve bekle. Ana profil
  sayfasında da About, Experience ve Activity bölümleri kaydırmadan metne girmiyor.
  Boş bölümlerde "When you add new … they'll show up here." ya da "You haven't received a recommendation yet" yazıyor.
  _dayanak: tek profil okuması · güven: orta_
- **Uygulama içi tarayıcıda LinkedIn oturumu yok; kişinin kendi Chrome'u kullanılmalı** `k:linkedin-uygulama-ici-tarayicida-linkedin-oturumu-yok`
  Claude'un yerleşik tarayıcı paneli kişinin Chrome oturumunu paylaşmıyor, profil linki authwall'a düşüyor.
  Kişi Chrome'da zaten giriş yapmışsa Claude in Chrome eklentisiyle okumak, ayrıca giriş yaptırmaktan daha hızlı.
  _dayanak: tek oturum · güven: orta_
- **Girişsiz iş araması: sayılar şişkin, filtreler güvenilmez** `k:linkedin-girissiz-is-aramasi-sayilar-siskin-filtreler`
  Girişsiz `linkedin.com/jobs/search` sayfası arama başına yalnızca ilk ~60 ilanı gösteriyor. `OR`'lu sorgularda başlıktaki "1.000+ / 5.000+"
  sayısı gevşek eşleşmeden geliyor; `AND` ve parantez yok sayılabiliyor. Remote filtresi (`f_WT=2`) uygulanmış görünse de sonuçların çoğu
  şehir konumlu (muhtemelen ofis/hibrit) ilanlar; konumu yalnızca ülke adı olanlar remote olmaya en yakın aday. Tekil ilanların küçük bir kısmı
  başlık ve konum süzgecinden geçiyor. Keşif için kullan; ilan metnini şirketin kendi ATS'sinden oku.
  _dayanak: tek oturum, birkaç arama · güven: orta_
- **Oturumlu arama girişsizden çok daha isabetli** `k:linkedin-oturumlu-arama-girissizden-cok-daha-isabetli`
  Kişinin kendi oturumuyla aynı aramalar gerçek, çok daha küçük sayıları veriyor ve Remote filtresi gerçekten uygulanıyor
  (kartlarda "<Ülke> (Remote)" / "(Hybrid)"). `/jobs/search/?…&f_WT=2` isteği yeni arayüze (`/jobs/search-results/`) yönleniyor; kişinin
  kayıtlı filtreleri (ör. maaş) URL'ye eklenebiliyor. Sayfa başına 25 kart; kartlar `[componentkey^="job-card-component-ref-<id>"]`.
  Sonuçlar alaka sırasında, anahtar kelimeye uymayan çok ilan da geliyor: worker başlık kurallarıyla yine elenmeli.
  Sayfa localStorage'ı ve window.name'i sayfa geçişinde siliyor; ara sonuç tarayıcıda tutulamıyor. Araç çıktısı ~1.000 karakterde
  kesildiği için kart listesi parça parça okunmalı. Düşük hacim: arama başına tek sayfa, aramalar arası birkaç saniye.
  _dayanak: tek oturum, birkaç arama · güven: orta_
- **Tek ilan girişsiz okunabiliyor** `k:linkedin-tek-ilan-girissiz-okunabiliyor`
  Oturum yokken `linkedin.com/jobs/view/<id>` giriş sayfasına yönleniyor (bazen 429). Aynı ilanın metni
  `linkedin.com/jobs-guest/jobs/api/jobPosting/<id>` adresinde girişsiz açılıyor: başlık, şirket, tam açıklama, kıdem ve istihdam türü.
  Yalnızca kişinin verdiği tekil ilan linki için kullan; arama sayfalarını bu yolla gezme. Linkteki izleme parametrelerini at, yalnızca id'yi kullan.
  _dayanak: tek ilan · güven: orta_
