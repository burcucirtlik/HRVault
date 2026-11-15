# Adaptörler

Her site için: ilanlar nasıl bulunur, nasıl başvurulur, hangi adım kişiye kalır.
Tarama kodu `engine/scanner/sources/<site>.py`; sitede öğrenilen tuhaflıklar
`knowledge/sites/<site>.md`.

| Kaynak | Tür | Kapsam | Tarama | Başvuru | Durum |
|---|---|---|---|---|---|
| greenhouse | ATS | küresel | takip listesi | otomatik (onaylı) | tarama çalışır |
| lever | ATS | küresel | takip listesi | otomatik (onaylı) | tarama çalışır |
| ashby | ATS | küresel | takip listesi | otomatik (onaylı) | tarama çalışır |
| himalayas | akış | küresel | rol araması | kaynağa yönlendirir | tarama çalışır |
| weworkremotely | akış | küresel | RSS | kaynağa yönlendirir | tarama çalışır |
| remotive | akış | küresel | tüm akış | kaynağa yönlendirir | tarama çalışır |
| remoteok | akış | küresel | tüm akış | kaynağa yönlendirir | tarama çalışır |
| linkedin | keşif | küresel | e-posta / elle link | yarı-otomatik | bekliyor |

**Bölgesel** kaynaklar tabloda yok: başlığında `**kapsam:** <ülke kodu>` taşıyan adaptörlerdir. Coach kişinin konumuna
göre önerir; paylaşım paketine varsayılan olarak girmezler (`engine/export/manifest.json → bölgesel_adaptörler`).

**ATS** kaynakları şirket bazlıdır: `me/sources.json → watchlist`'teki şirketleri tarar
(`scan.py detect <url> --add "Şirket"`). **Akış** kaynakları herkese açık genel ilan akışlarıdır;
asıl başvuru genellikle ilanın verdiği şirket sayfasından yapılır — o sayfa bir ATS'ye
gidiyorsa ilgili ATS adaptörü kullanılır.

## Yeni adaptör eklemek
1. `engine/scanner/sources/<ad>.py` — `fetch(ctx) -> list[Job]` (bkz. `common.Job`).
2. Küreselse `engine/scanner/sources/__init__.py` içinde `ATS` ya da `FEEDS`'e ekle.
3. Küresel akışsa `engine/templates/me/sources.json → feeds`'e varsayılanını ekle. **Bölgesel** kaynakta modüle
   `KAPSAM = "<ülke kodu>"` yaz; `__init__.py`'ye, şablona ve varsayılan `kaynaklar` listesine ekleme (modül kendiliğinden
   bulunur, coach `feeds.<ad>.enabled: true` yazınca taranır). Paylaşılan katmanda adını başka dosyada anma.
4. Bu klasöre `<ad>.md`: tarama, başvuru yöntemi, **kapsam** (`küresel` ya da ülke kodu), kurallar.
