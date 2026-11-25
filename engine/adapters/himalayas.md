<!-- durum: tarama çalışır -->
# Himalayas

- **tür:** akış · **başvuru_yöntemi:** kaynağa göre (ilanın yönlendirdiği sayfa)
- **kapsam:** küresel

## Tarama
- `GET https://himalayas.app/jobs/api/search?q=<rol>&page=<n>&country=<ülke>` — sayfa başı 20 ilan; worker rolleriyle aranır.
- **Ülke filtresi:** `country` adayın başvurabileceği ilanları (kısıtsız ilanlar dahil) getirir; tek ülke alır,
  geçersizse 400 döner. Ülke `feeds.himalayas.country` (metin ya da liste) ile verilir; yoksa worker `ülkeler`
  listesindeki ülke adlarından türetilir (bölge adları ve "Worldwide" atlanır). Geçersiz ülke özette uyarı olur;
  hiçbiri geçerli değilse filtresiz aranır.
- **Sayfa:** `feeds.himalayas.pages` üst sınırdır. Alaka sırası başlık eşleşmelerini öne topladığı için başlığı sorguya
  uyan ilan içermeyen ilk sayfada durulur; çoğu sorgu tek istekle biter.
- **Hız sınırı:** 429 → 15 sn bekleyip bir kez tekrar; yine 429 ise kalan sorgular okunmaz ve özette `uyarı` olarak
  listelenir. Başlangıç sorgusu güne göre döner.
- Tüm ilanlar remote; ülke kısıtı `locationRestrictions`, saat dilimi `timezoneRestrictions`.

## Başvuru
İlan sayfası genellikle şirketin kendi başvuru sayfasına yönlendirir. O sayfa Greenhouse / Lever /
Ashby ise ilgili adaptörü kullan (`scan.py detect <url>`); değilse yarı-otomatik: belgeleri ve
cevapları hazırla, gönderimi kişi yapar.
