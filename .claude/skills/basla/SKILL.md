---
name: başla
description: HRVault'un tek giriş komutu — ortamı kontrol eder, kişisel klasörü kurar ve kariyer koçunu soruları tek tek sorarak yürütür; yarıda kalan kurulumu kaldığı yerden sürdürür. Kişi "/başla", "başla", "basla", "kurulumu başlat", "devam edelim", "start", "get started" dediğinde, depo yeni klonlandığında, me/ boşken ya da kişi ne yapacağını bilmediğinde kullan.
---
<!-- durum: çalışır -->
# başla — kurulum ve tanışma, tek komut

Bu komutu yazan kişi teknik olmayabilir. Onun gördüğü tek şey sohbettir: dosya açtırma, komut yazdırma,
terim öğretme. Gereken her şeyi sen yaparsın; ona yalnızca **soru sorar** ve **onay istersin**.

Akışın kendisi `coach` skill'idir (`.claude/skills/coach/SKILL.md`); bu dosya ona nasıl girileceğini ve
yeni başlayan biriyle nasıl yürütüleceğini söyler. Çelişki olursa içerikte coach, **üslupta bu dosya** geçerlidir.

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
- `check` sonucu **HAZIR + aşama tamam** ise kurulum bitmiştir → §4.

## 2 — Karşılama (yalnızca ilk kez; me/ yeni kurulduysa)
Dört satırı geçme:
1. Gizlilik sözü: anlattığı ve okunan her şey yalnızca kendi bilgisayarındaki `me/` klasöründe kalır.
2. Ne olacak: altı kısa adımda onu tanıyacaksın, ona uygun iş tanımları önereceksin; **onayı olmadan** tarama da
   başvuru da yapılmaz.
3. Ne kadar sürer: tek oturumda bitmek zorunda değil; istediği an bırakır, sonra yine `/başla` yazar.
4. İlk soru.

## 3 — Koçu yürüt (yeni başlayan kuralları)
`coach` skill'ini oku ve `check`'in gösterdiği aşamadan devam et. Şu kurallarla:

- **Her mesajda tek soru.** Seçenekli olabilen her soruyu AskUserQuestion ile sor; açık uçlu soruya bir örnek
  cevap ekle ("örneğin: …"). coach'taki "bir mesajda ~5 soru" sınırı burada **1**'dir.
- **Her mesajın başında nerede olduğunu göster:** `Adım 2/6 · Kanıt`. Adımlar: 1 Tanışma · 2 Kanıt · 3 Analiz ·
  4 İş tanımları · 5 Aramalar · 6 Son ayarlar.
- **Terim yok.** worker → "arama", evidence-bank → "kanıt listesi", ATS → "başvuru sistemlerinin CV taraması",
  inbox → "günlük liste". Dosya adlarını ancak kişi sorarsa söyle.
- **İlk bilgi kaynağını kişi seçer** (AskUserQuestion, tek soru):
  - *LinkedIn profilim var* (önerilen) → linki iste; tarayıcıda kişinin kendi oturumuyla oku
    (`engine/adapters/linkedin.md` → "Profil okuma"). Giriş gerekiyorsa kişi kendisi girer; şifre girme.
  - *CV dosyam var* → dosyayı sohbete sürüklemesini ya da vault klasörüne koymasını iste; oku.
  - *İkisi de yok* → deneyimlerini sondan başa doğru, her seferinde tek iş için sor.
  Tarayıcı kullanılamıyorsa takılma: LinkedIn'in "PDF olarak kaydet" çıktısını ya da CV'yi iste.
- **Bilinen şeyi yeniden sorma.** Bir soruyu sormadan önce `me/profile/` içinde cevabı var mı bak; varsa
  "şunu anladım, doğru mu?" diye teyit al.
- **Her adımın sonunda:** iki satırlık "senden öğrendiklerim" özeti → dosyalara yaz → paneli yenile
  (`python3 engine/pipeline/dashboard.py`; ilk seferde `--open`) → "devam edelim mi, ara mı verelim?".
- İş tanımları (Adım 4) kişinin **açık onayı** olmadan onaylanmış sayılmaz; "tamam", "olur" yeterli, sessizlik değil.
- Kişi bir soruyu geçmek isterse geç, `me/learnings.md → bekleyen konular`a yaz, kurulumu bu yüzden durdurma;
  ancak `check`'in zorunlu saydığı bir alan ise neden gerektiğini bir cümleyle söyle.

## 4 — Bitiş
`python3 engine/pipeline/profile.py check` → **HAZIR** olunca:
- Paneli aç: `python3 engine/pipeline/dashboard.py --open`.
- Üç satırlık özet: kaç iş tanımı onaylandı, hangi aramalar açık, hangi dillerde ilan aranacak.
- Son cümle, aynen: **"Kurulum tamam. İlanları görmek için `/tara` yaz."**
  Taramayı kendiliğinden başlatma; kişi yazsın (komutu öğrenmesi için).

Zaten hazır bir vault'ta `/başla` yazıldıysa hiçbir şeyi yeniden sorma: durumu bir cümleyle söyle ve
`yardim` skill'indeki komut tablosunu göster.

## Kişi yarıda bırakırsa
Bir şey kaybolmaz; yazılanlar `me/` içindedir. Kapanışta tek cümle: "Kaldığımız yer: Adım N. Devam etmek için
`/başla` yaz."
