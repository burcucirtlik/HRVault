<!-- durum: tarama çalışır -->
# Remotive

- **tür:** akış · **başvuru_yöntemi:** kaynağa göre (ilanın yönlendirdiği sayfa)
- **kapsam:** küresel

## Tarama
- `GET https://remotive.com/api/remote-jobs` (opsiyonel `category`).
- **Koşul:** Remotive'i kaynak olarak belirt, linki koru, ilanları yeniden yayınlama. Kişisel kullanım uygundur.

## Başvuru
İlan sayfası genellikle şirketin kendi başvuru sayfasına yönlendirir. O sayfa Greenhouse / Lever /
Ashby ise ilgili adaptörü kullan (`scan.py detect <url>`); değilse yarı-otomatik: belgeleri ve
cevapları hazırla, gönderimi kişi yapar.
