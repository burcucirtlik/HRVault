# himalayas — öğrenimler

> Bu sitede çalışırken öğrenilen genel bilgiler. Kişisel veri yok.

## Öğrenimler
- **Arama sayfalı, akış imleçli** `k:himalayas-arama-sayfali-akis-imlecli`
  `/jobs/api/search` sayfa başı 20 ilan döner (`page=`); `/jobs/api` tüm akıştır (100k+) ve taramaya uygun değil.
  _dayanak: API notu · güven: yüksek_
- **employmentType güvenilir değil** `k:himalayas-employmenttype-guvenilir-degil`
  Saatlik part-time ilanlar "Full Time" etiketiyle gelebiliyor; çalışma tipini metinden çıkar.
  _dayanak: ilk tarama · güven: orta_
- **Başvuru e-postası metinden silinmiş olabilir** `k:himalayas-basvuru-e-postasi-metinden-silinmis-olabilir`
  Bazı ilanlarda "submit … to ." gibi boş e-posta adresi kalıyor; başvuru için `apply_url` (Himalayas sayfası) kullanılır.
  _dayanak: ilk tarama · güven: orta_
- **locationRestrictions başlığı geçersiz kılar** `k:himalayas-locationrestrictions-basligi-gecersiz-kilar`
  Başlık "Remote/Worldwide" dese bile `locationRestrictions` tek ülke ("Portugal") olabilir; aday konumu için
  bu alan esas alınır. scan.py artık worker `ülkeler` listesiyle kesişmeyen ilanları eler.
  _dayanak: tek hatalı öneri · güven: orta_
- **Ülke filtresi olmadan uygun ilanlar okunmuyor** `k:himalayas-ulke-filtresi-olmadan-uygun-ilanlar-okunmuyor`
  Filtresiz aramada ilk sayfalar çoğunlukla başka ülkelere kısıtlı ilanlarla doluyor; sorgu başına birkaç sayfa okunduğunda
  adayın ülkesine açık ilanların büyük kısmı hiç görülmüyor. `country=<ülke>` (tam ad ya da ISO kodu, tek ülke) kısıtsız
  ilanları da içererek sonucu adaya uygun kümeye indiriyor. Virgüllü liste ve bilinmeyen ülke 400 döndürür.
  _dayanak: birkaç sorgu karşılaştırması · güven: orta_
- **Alaka sırası başlık eşleşmelerini ilk sayfaya topluyor** `k:himalayas-alaka-sirasi-baslik-eslesmelerini-ilk-sayfaya`
  Varsayılan sırada başlığı sorguya uyan ilanlar ilk sayfada toplanıyor, sonraki sayfalar metinde geçen eşleşmeler;
  `sort=recent` aynı ilanları sayfalara dağıtıyor. Tam sayfalama yerine alaka sırası + "başlık eşleşmesi kalmayınca dur".
  _dayanak: birkaç sorgu, tüm sayfalar · güven: orta_
- **"Apply now" oturum açmamış kullanıcıyı kayıt sayfasına gönderiyor** `k:himalayas-apply-now-oturum-acmamis-kullaniciyi-kayit`
  Oturum yokken ilan sayfasındaki "Apply now" linki `/signup/talent?redirect=…showModal=true` adresine gidiyor.
  Asıl başvuru adresi kayıt ya da giriş sonrasında açılan pencerede görünüyor. Hesabı kişi açar ya da giriş yapar;
  Claude şifre girmez.
  _dayanak: tek başvuru denemesi · güven: orta_
