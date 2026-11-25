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
- Yaş filtresi `me/sources.json → max_age_days`; yayın ya da yeniden yayım/güncellemeden yeni olanına bakar. `max_age_kapsam:
  akışlar` (varsayılan) yalnızca akış sitelerine, `hepsi` kariyer sayfalarına da uygular. Özette `eski` sayacı elenenleri gösterir.
- `me/sources.json` yoksa `engine/templates/me/sources.json`'dan kopyala.
- Kaynak hata verirse tarama durmaz; özetteki `hata` satırını kişiye bildir.
- `kara_liste` ve `dil_dışı` sayaçları betiğin kendiliğinden elediklerini gösterir (kara listedeki şirket; `ilan_dilleri`
  dışında yazılmış ilan). Bunlar tarama dosyasına girmez; yalnızca sayı olarak görünür.
- `uyarı` satırı kaynağın **kısmen** okunduğunu söyler (ör. Himalayas hız sınırı: okunmayan sorgular listelenir;
  geçersiz ülke). Az ilanı "piyasada ilan yok" diye yorumlama; kişiye söyle ve biraz sonra yalnızca o kaynağı yeniden tara:
  `scan.py run --kaynak himalayas` (görülenler atlanır, yeni ilanlar bugünün dosyasına eklenir).
- Özetteki `not:` satırlarını ele al:
  - *"takip listesinde … şirket yok"* → kişiye hangi şirketleri takip etmek istediğini sor (§4).
  - *linkedin* ya da *"taranmaz; yalnızca iş alarmı…"* → §5.
  - *"tarayıcıyla okunur"* → notun gösterdiği adaptörü oku, kurallarına uyarak yalnızca kişi isterse arama sayfalarını oku;
    sonuçları bugünün tarama dosyasına elle ekle ve §2 ile sınıflandır.
    Her okumadan sonra, ilan çıkmasa bile kaydet: `scan.py kaydet <kaynak> --yontem tarayıcı --ilan <n> [--not "…"]`
    (panel kaynağın en son ne zaman tarandığını buradan gösterir).

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

**Kısmi remote istisnası:** worker `yer: [remote]` iken `kısmi_remote` tanımlıysa (ör. `tipler`, `min_remote_yüzde`, `şehirler`),
hibrit bir ilanı ancak üç koşul birden sağlanıyorsa geçir: tip listede, metindeki remote oranı en az `min_remote_yüzde`, yerinde
çalışılacak yer `şehirler`den biri. Geçen ilanda `yer: "hibrit (%<n> remote, <şehir>)"` yaz ve `belirsiz`e değil uyarıya yerinde gün
tahminini ekle. Koşullardan biri eksikse hibrit sebebiyle ele; oran yazmıyorsa `belirsiz` işaretle.

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
LinkedIn otomatik taranmaz (`engine/adapters/linkedin.md`). Taranmayan bir sitedeki ilan da aynı yolla girer:
kişi beğendiği ilanın linkini sohbete yapıştırır.
- Kişi bir ilan linki (LinkedIn ya da başka bir site) veya iş alarmı e-postası verirse: ilanı oku; başvuru şirket
  sitesine gidiyorsa `detect` ile ATS'yi bul (bulunursa şirketi takip listesine eklemeyi öner).
- İlanı bugünün tarama dosyasına elle ekle (aynı şema, `source`: sitenin kısa adı, ör. `"linkedin"`) ve §2 ile sınıflandır.
- Sonra kaydet: `scan.py kaydet <site> --yontem "kişinin linki" --ilan 1` (oturumlu aramada `--yontem "oturumlu arama"`).
- Ardından score skill'iyle puanla ve sonucu kişiye sohbette göster (puan, neden uygun, eksikler).

## Kurallar
- Kaynaklara günde bir tarama yeterli; aynı gün tekrar `run` yalnızca yeni ilanları ekler.
- Remotive ve Remote OK ilanlarında kaynak linkini koru (API koşulları).
