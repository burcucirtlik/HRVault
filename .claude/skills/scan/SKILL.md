---
name: scan
description: Aktif worker'ların kaynaklarından iş ilanlarını toplar, ilan metninden çalışma tipi/yer/saat çıkarır, uymayanları eler ve score'a hazırlar. "ilanları tara", "bugünkü ilanlar", "yeni ilan var mı", "şu şirketi takip et", "bu linke bak" ya da günlük zamanlanmış çalışmada kullan.
---
<!-- durum: çalışır (tarayıcı + sınıflandırma); LinkedIn e-posta kaynağı bekliyor -->
# scan

İki katman: **betik** ilanları çeker ve rol anahtar kelimesiyle ön eler (hızlı, deterministik);
**sen** kalanları okuyup sınıflandırırsın (etikete güvenmeden).

Tüm komutlar vault kökünden: `python3 engine/scanner/scan.py <komut>`

## 1. Tara
```bash
python3 engine/scanner/scan.py run
```
- Aktif worker'ları (`me/workers/`, `durum: aktif`) ve `me/sources.json`'u okur.
- Çıktı: `me/pipeline/scans/YYYY-MM-DD.json`. Daha önce görülen ilanlar (`me/pipeline/seen.json`) atlanır.
- `me/sources.json` yoksa `engine/templates/me/sources.json`'dan kopyala.
- Kaynak hata verirse tarama durmaz; özetteki `hata` satırını kişiye bildir.
- Özetteki `not:` satırlarını ele al:
  - *"takip listesinde … şirket yok"* → kişiye hangi şirketleri takip etmek istediğini sor (§4).
  - *linkedin* → §5.

## 2. Sınıflandır
```bash
python3 engine/scanner/scan.py brief
```
Her ilan için beyan edilen alanlar + açıklamadan sinyal cümleleri gelir. `knowledge/classification.md`
kurallarıyla çıkar: **tip** (full-time | part-time | contract | freelance | internship),
**yer** (remote | hybrid | onsite), **ülke_kısıtı**, **saat**/hafta, **ücret**, **dil**, **kıdem**.

- Brief yetmiyorsa: `scan.py show <sıra>` (gerekirse `--full`).
- Etiket ile metin çelişirse metne güven (ör. "Full-Time" etiketli ama "10-20 hours per week" → part-time).
- Emin olamadığın alanı `belirsiz` listesine yaz; tahmin etme.

Kişinin paylaşmamayı seçtiği sınıflandırma kuralları `me/learnings.md → Paylaşılmayan öğrenimler` başlığındadır;
onları da `knowledge/` maddesi gibi uygula.

**İlan dili:** `dil` alanına ilanın *istediği* dilleri yaz; ilanın *yazıldığı* dil worker'ın `ilan_dilleri`
listesinde (yoksa `preferences.md → worker_varsayılanları.ilan_dilleri`) değilse ilanı ele
(`--drop "ilan dili: de; aranan: en"`). Liste boşsa tarama yapma, coach'a yönlendir.

Sonra worker filtreleriyle karşılaştır (`çalışma_tipi`, `yer`, `ülkeler`, `diller`, `ilan_dilleri`, `kıdem`, `min_ücret`)
ve her ilan için **tek** komut çalıştır:
```bash
# uyuyorsa
python3 engine/scanner/scan.py annotate <sıra> --json '{"tip":"part-time","yer":"remote","ülke_kısıtı":["US"],"saat":20,"ücret":"<ilandaki ücret>","dil":["en"],"kıdem":"mid","belirsiz":[]}'
# uymuyorsa
python3 engine/scanner/scan.py annotate <sıra> --drop "onsite; worker remote istiyor"
# başka worker'a uyuyorsa
python3 engine/scanner/scan.py annotate <sıra> --json '{…}' --workers parttime-remote
```
Eleme sebebi kısa ve somut olsun; score ve learn bunu kullanır.

Yeni bir sınıflandırma kuralı keşfettiysen (sık tekrar eden bir etiket yanılgısı gibi) learn ile
`knowledge/classification.md`'ye ekle.

## 3. Devret
Sınıflandırma bitince kısa özet ver (taranan / sınıflandırılan / elenen ve en sık eleme sebepleri)
ve score'u çalıştır.

## 4. Şirket takibi (Greenhouse / Lever / Ashby)
Kişi "X şirketini takip et" derse ya da bir kariyer sayfası/ilan linki verirse:
```bash
python3 engine/scanner/scan.py detect "<kariyer-sayfası-veya-ilan-url>" --add "Şirket Adı"
```
- `me/sources.json → watchlist`'e eklenir. Takip listesi kişiseldir, `me/` içinde kalır.
- ATS bulunamazsa (Workable, SmartRecruiters…) kişiye adaptörün henüz olmadığını söyle.

## 5. LinkedIn ve elle verilen linkler
LinkedIn otomatik taranmaz (`engine/adapters/linkedin.md`).
- Kişi bir LinkedIn ilan linki veya iş alarmı e-postası verirse: ilanı oku; başvuru şirket sitesine
  gidiyorsa `detect` ile ATS'yi bul (bulunursa şirketi takip listesine eklemeyi öner).
- İlanı bugünün tarama dosyasına elle ekle (aynı şema, `source: "linkedin"`) ve §2 ile sınıflandır.

## Kurallar
- Kaynaklara günde bir tarama yeterli; aynı gün tekrar `run` yalnızca yeni ilanları ekler.
- Remotive ve Remote OK ilanlarında kaynak linkini koru (API koşulları).
