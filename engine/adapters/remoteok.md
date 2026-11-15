<!-- durum: tarama çalışır -->
# Remote OK

- **tür:** akış · **başvuru_yöntemi:** kaynağa göre (ilanın yönlendirdiği sayfa)
- **kapsam:** küresel

## Tarama
- `GET https://remoteok.com/api` — son ~100 ilan; ilk eleman yasal nottur.
- **Koşul:** Remote OK'u kaynak olarak belirt ve ilan linkini koru.

## Başvuru
İlan sayfası genellikle şirketin kendi başvuru sayfasına yönlendirir. O sayfa Greenhouse / Lever /
Ashby ise ilgili adaptörü kullan (`scan.py detect <url>`); değilse yarı-otomatik: belgeleri ve
cevapları hazırla, gönderimi kişi yapar.
