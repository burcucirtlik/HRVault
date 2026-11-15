---
id: YYYY-MM-DD-sirket-rol
ilan_id:                      # tarama dosyasındaki id (kaynak:id); karar günlüğüyle eşleşir
şirket:
rol:
worker:                       # virgülle, ör. fulltime-remote, freelance
kaynak:
ilan_linki:
başvuru_linki:
başvuru_yöntemi: otomatik | yarı-otomatik | manuel
uygunluk_puanı:               # score'un verdiği puan (0–100)
ats_eşleşme:                  # ats.py'nin ölçtüğü yüzde; ölçülmediyse boş
cv: cv.md                     # bu başvuru için hazırlanan CV, bu klasörde
cv_pdf:                       # render_pdf.py çıktısı, bu klasörde
ön_yazı:                      # cover-letter.md | yok
ön_yazı_pdf:
durum: hazırlandı             # hazırlandı | başvuruldu | görüldü | mülakat | teklif | ret | sessiz | iptal
iptal_sebebi:                 # durum iptal ise: kişinin sebebi (learn bunu kullanır)
başvuru_tarihi:
son_güncelleme:
takip_tarihi:                 # bu tarihte ses yoksa hatırlat
---
---
# <Rol> — <Şirket>

## Durum geçmişi
- YYYY-MM-DD · hazırlandı

## İlan özeti
- çalışma tipi / yer / saat:
- ücret:
- istenen yetkinlikler:
- tercih edilen yetkinlikler:

## ATS simülasyonu
- eşleşen anahtar kelimeler:
- eksik anahtar kelimeler:
- kanıtı olmadığı için eklenmeyenler:

## Gönderilen
- CV: `cv.md` + PDF (bu klasörde; ana CV'den farklı her sürüm burada saklanır)
- Ön yazı: `cover-letter.md` | yok
- Form cevapları: aşağıda

## Form cevapları
| Soru | Cevap | Kaynak |
|---|---|---|

## Notlar
<!-- mülakat notları, iletişim kişisi, takip -->

---
<!-- ilan.md: ilanın tam metni ayrı dosyada saklanır (ilan kaldırılabilir). -->
