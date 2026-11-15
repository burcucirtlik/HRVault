<!-- durum: tarama çalışır -->
# Himalayas

- **tür:** akış · **başvuru_yöntemi:** kaynağa göre (ilanın yönlendirdiği sayfa)
- **kapsam:** küresel

## Tarama
- `GET https://himalayas.app/jobs/api/search?q=<rol>&page=<n>` — sayfa başı 20 ilan; worker rolleriyle aranır.
- Ayar: `feeds.himalayas.pages` (rol başına kaç sayfa).
- Tüm ilanlar remote; ülke kısıtı `locationRestrictions`, saat dilimi `timezoneRestrictions`.

## Başvuru
İlan sayfası genellikle şirketin kendi başvuru sayfasına yönlendirir. O sayfa Greenhouse / Lever /
Ashby ise ilgili adaptörü kullan (`scan.py detect <url>`); değilse yarı-otomatik: belgeleri ve
cevapları hazırla, gönderimi kişi yapar.
