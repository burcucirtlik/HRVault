---
name: yardım
description: HRVault komutlarını ve kişinin şu an hangi adımda olduğunu gösterir. Kişi "/yardım", "yardim", "yardım", "ne yazabilirim", "komutlar neler", "help", "sırada ne var" dediğinde kullan.
---
<!-- durum: çalışır -->
# yardım

1. `python3 engine/pipeline/profile.py gate` → kişinin nerede olduğunu **bir cümleyle** söyle ve sıradaki komutu öner.
2. Tabloyu göster:

| Yaz | Ne olur |
|---|---|
| `/başla` | Kurulum ve tanışma. Yarıda kaldıysa kaldığı yerden devam eder. |
| `/tara` | İlanları tarar, puanlar, günlük listeyi gösterir. |
| `/başvur` | Seçtiğin ilanlar için CV hazırlar, onayınla başvurur. |
| `/durum` | Başvuruların ne durumda, bugün ne yapılacak. |
| `/panel` | Özet sayfayı tarayıcıda açar. |
| `/yardım` | Bu liste. |

3. Ekle: "Komut yazmak zorunda değilsin; ne istediğini düz cümleyle de söyleyebilirsin
   (örneğin: *part-time işlere de bak*, *şu şirketten ret geldi*, *yedek al*)."

Klavyesinde Türkçe harf olmayan biri komutları düz harfle yazabilir: `/basla`, `/basvur`, `/yardim`.
İleri düzey komutlar `TEKNIK.md` içinde anlatılır (`/coach`, `/mode`, `/scan`, `/score`,
`/tailor`, `/apply`, `/track`, `/learn`, `/export`); kişi sormadıkça sayma.
