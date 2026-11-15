---
name: track
description: Başvuruların durumunu takip eder ve günceller — e-postadan gelen cevapları başvurulara eşler, takip tarihi gelenleri hatırlatır, özet çıkarır. "başvurularım ne durumda", "bu şirketten ret geldi", "mülakata çağrıldım", "haftalık özet" isteklerinde kullan.
---
<!-- durum: çalışır (e-posta entegrasyonu yok) -->
# track

Komutlar vault kökünden: `python3 engine/pipeline/track.py <komut>`

## Görünümler
```bash
python3 engine/pipeline/track.py list [--all]   # tablo: tarih · durum · gün · puan · şirket — rol · worker
python3 engine/pipeline/track.py due            # takip tarihi gelenler + hazırlanıp gönderilmeyenler
python3 engine/pipeline/track.py stats          # dönüşüm: genel, worker'a ve puan bandına göre
```

## Durum güncelleme
Kaynak: kişinin söylediği ("X'ten mülakat daveti geldi") ya da kişinin paylaştığı e-posta.
```bash
python3 engine/pipeline/track.py set <klasör-adı-parçası> mülakat --not "ilk görüşme 20 Kasım"
python3 engine/pipeline/track.py set <…> ret --not "otomatik ret e-postası"
python3 engine/pipeline/track.py set <…> iptal --sebep "…"      # sebep zorunlu
```
Durumlar: `hazırlandı → başvuruldu → görüldü → mülakat → teklif | ret | sessiz | iptal`.
Betik frontmatter'ı ve "Durum geçmişi"ni günceller; elle düzenleme gerekmez.

## Kurallar
- `due` takip tarihi gelen başvuru gösterirse: kısa takip mesajı taslağı öner (göndermek kişinin işi),
  kişi istemezse `sessiz` yap.
- Mülakat / teklif / ret → learn'e ver (worker, puan, ATS eşleşmesi, CV vurgusu).
- `stats` en az ~20 gönderilmiş başvurudan sonra anlamlıdır; puan eşiği (`min_uygunluk_puanı`) önerisini
  ancak o zaman yap ve kişiye sor.

## TODO
- E-posta entegrasyonu (bağlayıcı seçilince).
