---
name: başla
description: HRVault'un giriş komutu — ortamı kontrol eder, kişisel klasörü kurar ve kişiyi kısa bir turla ilk ilan listesine ulaştırır (soruları tek tek sorar); yarıda kalan kurulumu ve ertelenen soruları kaldığı yerden sürdürür. Kişi "/başla", "başla", "basla", "kurulumu başlat", "devam edelim", "start", "get started" dediğinde, depo yeni klonlandığında, me/ boşken ya da kişi ne yapacağını bilmediğinde kullan.
---
<!-- durum: çalışır -->
# başla — hızlı tur: ilk ilan listesine kadar

Bu komutu yazan kişi teknik olmayabilir. Onun gördüğü tek şey sohbettir: dosya açtırma, komut yazdırma,
terim öğretme. Gereken her şeyi sen yaparsın; ona yalnızca **soru sorar** ve **onay istersin**.

**Hedef:** kişiyi olabildiğince az soruyla taramaya hazır hale getirmek. Taramanın gerektirmediği sorular
**sonraya** bırakılır (bkz. "Ertelenenler"). Dosya biçimleri ve yöntem için `coach` skill'i
(`.claude/skills/coach/SKILL.md`) kaynaktır; **sıra, soru sayısı ve üslup** için bu dosya geçerlidir.

Depo bu oturumda klonlandıysa `CLAUDE.md` bağlamda olmayabilir: başlamadan önce oku.

## 0 — Doğru klasörde miyiz?
Çalışma klasöründe `engine/` ve `CLAUDE.md` olmalı. Bunlar bir alt klasördeyse (depo alt klasöre klonlanmış):
komutlar ve oturum başı kontrolü yüklenmez. Kişiye tek cümleyle söyle ve **o alt klasörü** Claude'da proje
klasörü olarak açıp yeniden `/başla` yazmasını iste. Dosyaları kendiliğinden taşıma.

## 1 — Ortam (kişiye sormadan)
```bash
python3 --version                              # Windows'ta yoksa: python --version ya da py -3 --version
python3 engine/pipeline/profile.py init        # me/ yoksa kurar; varsa dokunmaz, eksik şablonu ekler
python3 engine/pipeline/profile.py doctor
python3 engine/pipeline/profile.py check
```
- **Python yoksa** dur ve sade bir dille kurdur, sonra yeniden dene:
  macOS'ta ekrana gelen "komut satırı geliştirici araçları" penceresinde *Yükle*; Windows'ta python.org'daki
  kurucu, ilk ekranda *Add python.exe to PATH* kutusu işaretli. Kurulum bitince kişi "tamam" yazsın.
  `python3` yerine `python` ya da `py -3` çalışıyorsa bu oturumda onu kullan ve kişiye söyle: oturum başı
  kontrolü `python3` adını bekler; çalışmazsa her oturumda `/başla` yazması yeterlidir.
- `doctor` çıktısını **yapıştırma**. Her `✗` ve `!` satırını bir cümleye çevir: ne eksik, neyi etkiler, ne zaman
  gerekir ("PDF için Chrome ya da Edge gerekiyor; başvuru adımına kadar kurman yeterli"). `✗` varsa önce onu çöz.
- `check` **HAZIR** diyorsa tur bitmiştir → "Zaten kurulu vault".

## 2 — Karşılama (yalnızca ilk kez; me/ yeni kurulduysa)
Beş satırı geçme:
1. Gizlilik sözü: anlattığı ve okunan her şey yalnızca kendi bilgisayarındaki `me/` klasöründe kalır.
2. Ne olacak: kısa bir tanışma, sonra ona uygun iş türleri önerilecek; **onayı olmadan** tarama da başvuru da yok.
3. Süre: ilk ilan listesine bu oturumda ulaşılır; kalan sorular sonra, gerektikleri anda sorulur.
4. Dürüst kapsam: "Şu an en çok ilanı **uzaktan (remote) işlerde** ve **takip etmek istediğin şirketlerde** bulurum.
   Kendi şehrinde ofis işi arıyorsan ilk liste kısa olabilir; beğendiğin bir ilanın linkini yapıştırırsan ona da bakarım."
5. İlk soru (Adım 1).

## 3 — Tur (her mesajda tek soru)
Her mesajın başında yerini göster: `Adım 2/5 · Ne arıyorsun?`. Adımlar:
1 Seni tanıyalım · 2 Ne arıyorsun? · 3 Sana uygun işler · 4 Diller · 5 Takip edilecek şirketler.

Genel kurallar:
- **Tek soru.** Seçenekli olabilen her soru AskUserQuestion ile; açık uçlu soruya bir örnek cevap ekle.
- **Terim yok.** worker → "arama", evidence-bank → "kanıt listesi", ATS → "başvuru sistemlerinin CV taraması",
  inbox → "günlük liste". Dosya adlarını ancak kişi sorarsa söyle.
- **Bilinen şeyi yeniden sorma.** Sormadan önce `me/profile/` içinde cevabı var mı bak; varsa teyit al.
- **Uydurma yok.** Yalnızca kişinin verdiği kaynakta ya da söylediğinde dayanağı olanı yaz.
- Her adımın sonunda: dosyalara yaz → paneli yenile (`python3 engine/pipeline/dashboard.py`; ilk seferde `--open`).
- Kişi ara vermek isterse: "Kaldığımız yer: Adım N. Devam etmek için `/başla` yaz."

### Adım 1 · Seni tanıyalım
AskUserQuestion: **"Seni nereden tanıyayım?"** → *LinkedIn profilim* (önerilen) · *CV dosyam* · *İkisi de yok, anlatırım*.
- LinkedIn → linki iste; tarayıcıda kişinin kendi oturumuyla oku (`engine/adapters/linkedin.md` → "Profil okuma").
  Giriş gerekiyorsa kişi kendisi girer; şifre girme. Tarayıcı kullanılamıyorsa LinkedIn'in "PDF olarak kaydet"
  çıktısını ya da CV'yi iste.
- CV → sohbete sürüklemesini ya da vault klasörüne koymasını iste; oku.
- Anlatım → deneyimlerini sondan başa doğru, her seferinde tek iş için sor (unvan, şirket, yıllar, 2–3 somut iş).

Yaz (biçimler coach §1a ve §2):
- `cv-master.md` — deneyimler, özet, eğitim, diller. LinkedIn'den geldiyse ayrıca `linkedin-notes.md`.
- `evidence-bank.md` — deneyim maddelerinden **en az 5 yetkinlik**, her biri kaynaktaki bir cümleye bağlı
  (`_kaynak: LinkedIn_` / `_kaynak: CV_` / `_kaynak: kişi anlattı_`). Kanıtı olmayan yetkinliği yazma.
- `answers.md` → kaynakta açıkça yazanlar (ad, e-posta, LinkedIn linki). Gerisini sorma; ertelenir.

Sonra 5 maddelik "senden öğrendiklerim" özeti ve tek soru: "Yanlış ya da eksik bir şey var mı?"

### Adım 2 · Ne arıyorsun?
Üç soru, ayrı mesajlarda:
1. **Hayalindeki iş ve sektör** (açık uçlu; örnek: "fintech'te ürün analisti").
2. **Nasıl çalışmak istiyorsun?** AskUserQuestion, çoklu seçim: *Tam zamanlı* · *Freelance / proje* · *Part-time*;
   ardından ikinci kart: *Remote* · *Hibrit* · *Ofis*.
3. **Nerede yaşıyorsun ve hangi ülkelerde çalışma iznin var?** (örnek: "İzmir'de yaşıyorum; Türkiye'de iznim var,
   AB'de yok"). Taşınmaya açıklığını da bu cevapta yakala; ayrıca sorma.
Son olarak, CV'de güncel bir işveren varsa tek kart: **"Şu an çalıştığın şirketin ilanlarını gizleyeyim mi?"** → kara liste.

→ `goals.md`: *Hayalimdeki iş ve sektör*, *Nasıl çalışmak istiyorum*, *Konum ve çalışma izni* (kişinin kelimeleriyle).
→ `answers.md`: `location`, `work_authorization`. → `preferences.md`: kara liste.

### Adım 3 · Sana uygun işler
- `career-analysis.md` → yalnızca **Profil özeti** ve **Önerilen iş tanımları** (coach §3). Diğer bölümler
  ertelenen sorular cevaplanınca tamamlanır.
- `job-definitions.md` → **3–4 tanım** (coach §4 biçimi; ülkeler çalışma izniyle tutarlı). Her birini kısa bir
  kartla göster (ad · bir cümle · neden sen · açıklar) ve AskUserQuestion ile tek tek sor: *Onayla* · *Değiştir* · *İstemiyorum*.
  Açık onay olmadan tanım onaylanmış sayılmaz.
- Onaylanan her tanım için aramayı kur (coach §5) — kişiye sormadan, sonunda tek cümleyle söyle
  ("3 arama kuruldu: …").

### Adım 4 · Diller
AskUserQuestion, çoklu seçim: **"Hangi dillerde yazılmış ilanlara bakalım?"** (CV'deki dillerden öner; arayüz Türkçe
diye Türkçeyi varsayma). Ardından **"CV'ni hangi dillerde hazırlayabilirim?"**
→ `preferences.md → worker_varsayılanları.ilan_dilleri`, `cv_dili`.
Kişinin ülkesine uyan bölgesel kaynak varsa (`engine/adapters/*.md` → `kapsam:`) tek kartla aç/kapalı sor (coach §6).

### Adım 5 · Takip edilecek şirketler
Soru: **"Çalışmak istediğin şirketler var mı? 5–10 isim yazabilirsin; aklında yoksa geçebiliriz."**
Her şirket için:
1. Resmi kariyer sayfasını bul (şirketin kendi sitesi). Bulamıyorsan ya da emin değilsen kişiye linki sor; tahmin etme.
2. `python3 engine/scanner/scan.py detect "<kariyer-sayfası>" --add "<Şirket>"`
3. Sonucu topla. Sonda tek mesaj: eklenenler (açık ilan sayısıyla) ve eklenemeyenler — "bu şirketlerin ilan
   sistemi henüz desteklenmiyor; ilanlarının linkini bana yapıştırırsan tek tek değerlendiririm."
Kişi geçerse sorun değil; tarama yine çalışır.

## 4 — Bitiş
`python3 engine/pipeline/profile.py check` → **HAZIR** değilse eksik olanı (yalnızca hazır olmayı engelleyeni)
bir soruyla tamamla. HAZIR olunca:
- Paneli aç: `python3 engine/pipeline/dashboard.py --open`.
- Üç satırlık özet: onaylanan iş türleri, kurulan aramalar, takip edilen şirketler.
- Son cümle, aynen: **"Hazırız. İlanları görmek için `/tara` yaz."**
  Taramayı kendiliğinden başlatma; kişi yazsın (komutu öğrenmesi için).

## Ertelenenler (turda sorulmaz)
| Ne | Ne zaman sorulur |
|---|---|
| Form cevapları (telefon, başlama tarihi, saat dilimi, para birimi, vize sponsorluğu, ücret, ihbar süresi / haftalık saat) | İlk `/başvur`'da, başvurudan önce (başvur skill'i) |
| Güçlü yanlar, çekinceler, öncelikler, artık istemediklerin, kırmızı çizgiler | İlk `/tara`'dan sonra (tara skill'i) ya da kişi `/başla`'yı yeniden yazınca |
| Kariyer analizinin kalan bölümleri | Güçlü yanlar ve çekinceler cevaplanınca |

## Zaten kurulu vault
`/başla` hazır bir vault'ta yazıldıysa hiçbir şeyi yeniden sorma. Durumu bir cümleyle söyle.
`check` eksik listesinde ertelenen bir şey varsa: "Listeni iyileştirecek birkaç kısa soru kaldı; şimdi sorayım mı?"
Evet derse yukarıdaki tablodaki soruları tek tek sor (form cevapları hariç; onlar başvuruda). Hayır derse
`yardim` skill'indeki komut tablosunu göster.
