---
name: score
description: Sınıflandırılmış ilanlara kesin kuralları uygular, kalanları kişinin profiline göre 0-100 puanlar ve günlük onay listesini me/pipeline/inbox/ altına yazar; sohbetten gelen onay/ret kararlarını da listeye işler. scan'den sonra, "ilanları puanla", "onay listesini hazırla", "bugünkü liste", "1 ve 3'e başvur, 2'yi reddet" isteklerinde kullan.
---
<!-- durum: çalışır -->
# score

Komutlar vault kökünden: `python3 engine/pipeline/inbox.py <komut>`

## 0. Ön koşul
Bugünün tarama dosyasında (`me/pipeline/scans/YYYY-MM-DD.json`) ilanlar scan skill'iyle
sınıflandırılmış olmalı. `filter` sınıflandırılmamış ilan bildirirse önce scan §2'yi bitir.

## 1. Kesin kurallar
```bash
python3 engine/pipeline/inbox.py filter
```
Betik eler: şirket / anahtar kelime kara listesi, zaten başvurulan ilan (puanlanmış ilanlara
dokunmaz; tekrar çalıştırmak güvenli). Aynı şirkete birden çok başvuru serbesttir. Dolandırıcılık kalıbı geçen ilanları **eleme değil
işaret** olarak (⚠) listeler; kararı sen verirsin (§2). Çıktı: puanlanacak ilanlar.

## 2. Puanla
Önce **bir kez** oku: `me/profile/job-definitions.md` (worker'ın bağlı olduğu tanım: neden sen, açıklar, CV vurgusu), `me/profile/goals.md`, `me/profile/evidence-bank.md`, `me/profile/cv-master.md`,
`me/learnings.md`, ilgili `me/workers/*.md`, `me/profile/preferences.md` (sektör kara listesi).
Sonra her ilan için `python3 engine/scanner/scan.py show <sıra>` ile metni oku.

### Önce eleme kontrolleri (puan vermeden `--drop`)
- `scam_sinyal` işaretliyse `knowledge/scam-signals.md` ile değerlendir; güçlü sinyal → ele.
  Masum bağlam (ör. "WhatsApp ürün ekibi") → puanla, uyarıya yaz.
- `preferences.md → kara_liste.sektörler` ile eşleşen sektör ya da `goals.md → Kırmızı çizgiler` → ele.
- İlanın **aday konumu** kısıtı (başlık değil, kaynağın konum alanı) worker `ülkeler` ile uyuşmuyorsa → ele.
- Worker'ın kesin bir şartı karşılanmıyor ve scan bunu kaçırmış (ör. ülke kısıtı, `min_ücret`) → ele.

### Puan ölçütü (toplam 100)
| Bileşen | Ağırlık | Nasıl |
|---|---|---|
| Zorunlu yetkinlikler | 45 | İlanın "requirements / must have" maddelerinden kaçının kanıt bankasında **dayanağı** var. Dayanaksız iddia sayılmaz. |
| Tercih edilen yetkinlikler | 15 | "nice to have / preferred" maddeleri, aynı kural. |
| Kıdem ve deneyim yılı | 15 | İstenen yıl/seviye ile CV'deki ilgili deneyim. 2+ yıl açık ya da çok kıdemli rol → düşük. |
| Worker uyumu | 15 | Ücret, saat, zaman dilimi, dil — worker ve `answers.md` ile. Belirsiz alan → yarı puan. |
| Kişisel tercih | 10 | `goals.md` (ne yapmak istiyor, güçlü alanlar, istemedikleri, öncelikler) ve `me/learnings.md`'deki kalıplar (sevdiği/reddettiği alanlar, şirket tipi, ton). Veri yoksa 5. |

**Kalibrasyon:** 85+ güçlü aday, neredeyse tüm zorunlu maddeler kanıtlı · 70–84 iyi, 1–2 açık var ·
60–69 sınırda, başvurmaya değebilir · <60 listede gösterilmez. Puanı şişirme: kişi listeye güvenmeli.

### Yaz
```bash
python3 engine/pipeline/inbox.py rate <sıra> --json '{"puan":78,"gerekçe":"SQL ve dashboard deneyimi zorunlu maddelerin 4/5ini karşılıyor; remote ve saat uyumlu.","eksikler":["dbt"],"uyarılar":["ücret belirtilmemiş"]}'
python3 engine/pipeline/inbox.py rate <sıra> --drop "kripto sektörü kara listede"
```
- **gerekçe:** 1–2 cümle, somut: hangi kanıt hangi şartı karşılıyor.
- **eksikler:** ilanın istediği ama kanıt bankasında dayanağı olmayanlar. tailor bunları CV'ye
  eklemeyecek; kişi burada görüp karar verir.
- **uyarılar:** belirsizlik, zayıf scam sinyali, gizli hibrit, kısa süreli sözleşme vb.

Eksik bir yetkinliğin aslında kişide olduğundan şüpheleniyorsan puanı düşük tut ve uyarıya
"kanıt bankasında yok, varsa ekle: X" yaz — kanıt uydurma.

## 3. Onay listesini yaz
```bash
python3 engine/pipeline/inbox.py render
```
`me/pipeline/inbox/YYYY-MM-DD.md` oluşur (eşik: `min_uygunluk_puanı`, üst sınır:
`onay_listesi_üst_sınır`). Tekrar çalıştırmak güvenlidir: kişinin işaretleri korunur.

Kişiye kısa özet ver: kaç ilan sunuldu, ilk 3'ü (puan · rol · şirket · tek cümle neden),
en sık eleme sebepleri, varsa dikkat isteyen uyarılar. Listenin yolunu ver.

## 4. Kararlar
Kişi dosyada işaretleyebilir ya da sohbette söyleyebilir:
```bash
python3 engine/pipeline/inbox.py mark --approve 1,3 --reject '2=çok kıdemli' --reject '5=sektör ilgimi çekmiyor'
python3 engine/pipeline/inbox.py decisions --record
python3 engine/pipeline/inbox.py log          # her ilan için geçerli (son) karar
```
`decisions` onaylananları apply'a, ret sebeplerini learn'e verir (`me/pipeline/decisions.jsonl`).
Ret sebepleri kişiye özeldir → learn bunları `me/learnings.md`'ye yazar; birden çok kişide
geçerli olabilecek bir kalıp görürsen (ör. bir ilan tipinin sistematik yanlış puanlanması) genel
kuralı `knowledge/`'a ekle.

## Kurallar
- Puan yalnızca `me/profile/` içindeki dayanağa göre. Başlamadan `python3 engine/pipeline/profile.py check`;
  `HAZIR DEĞİL` ise puanlama yapma, coach öner.
- Bir günün listesi başka günün tarama dosyasıyla karıştırılmaz (`--scan`/`--date` aynı gün).
