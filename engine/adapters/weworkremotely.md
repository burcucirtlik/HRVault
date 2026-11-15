<!-- durum: tarama çalışır -->
# We Work Remotely

- **tür:** akış · **başvuru_yöntemi:** kaynağa göre (ilanın yönlendirdiği sayfa)
- **kapsam:** küresel

## Tarama
- RSS: `https://weworkremotely.com/remote-jobs.rss` (son ~100 ilan).
- Ayar: `feeds.weworkremotely.categories` → kategori RSS'leri (`/categories/<slug>.rss`); boşsa ana akış.
- Başlık `Şirket: Rol` biçiminde; ayrıştırıcı ikiye böler.

## Başvuru
İlan sayfası genellikle şirketin kendi başvuru sayfasına yönlendirir. O sayfa Greenhouse / Lever /
Ashby ise ilgili adaptörü kullan (`scan.py detect <url>`); değilse yarı-otomatik: belgeleri ve
cevapları hazırla, gönderimi kişi yapar.
