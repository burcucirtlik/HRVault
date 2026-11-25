---
name: apply
description: Onay listesinde işaretlenen ilanlara başvurur — tailor'ı çalıştırır, formu doldurur, gönderimden önce kişiye gösterir ve başvuruyu kaydeder. "onaylananlara başvur", "başvuruları yap" isteklerinde kullan.
---
<!-- durum: çalışır (yarı otomatik: her gönderim kişinin açık onayıyla) -->
# apply

## Adımlar
1. Kararları al: `python3 engine/pipeline/inbox.py decisions --record [--date YYYY-MM-DD]`
   → `onaylanan` listesi başvurulacaklar; `reddedilen` sebepleri learn'e verilir.
2. Günlük limiti kontrol et (`preferences.md → günlük_başvuru_limiti` + worker `günlük_limit`).
3. Her ilan için:
   0. **Önceki başvuru kontrolü:** `track.py list --all`'da aynı şirket + benzer rol var mı bak; şirketin
      kendi kariyer sitesinde kişi oturumluysa Apply sayfasında "önceki başvuru / bekleme süresi" uyarısına bak.
      Varsa hazırlığa geçmeden kişiye söyle.
   1. tailor'ı çalıştır (CV + ön yazı + PDF başvuru klasörüne). Kişi kendi CV'sini verdiyse de PDF'in metnini
      `cv.md` olarak klasöre koy, ATS ölçümü onun üzerinden yapılır.
   2. **ATS kapısı — sabit kural: ATS puanı %90'ın altındaysa başvuru yapılmaz.**
      ```bash
      python3 engine/pipeline/ats.py <klasör> --gate
      ```
      Kapı kayıtlı sayıya güvenmez: `ats-terimler.json`'daki listeyi cv.md üzerinde yeniden ölçer, birincil şarta
      ve PDF'in cv.md'den güncel olduğuna bakar. Liste kayıtlı değilse (eski başvurular) önce tailor §2 ile ölç.
      Eşik ayarla değişmez; kişi "yine de gönder" dese de aşılmaz. `DUR` derse forma geçme:
      1. Sebepleri ve öneri listesini (eksik kelimeler, önce zorunlular) kişiye göster.
      2. Her eksik için "bunu gösteren bir deneyimin var mı?" diye sor. Kanıt gelirse `evidence-bank`'e ekle,
         tailor ile CV'ye ilandaki yazımıyla işle, yeniden ölç (`--record`) ve kapıyı yeniden çalıştır.
      3. Kanıtla %90'a ulaşılamıyorsa başvurma: `track.py set <klasör> iptal --sebep "ATS %<n>, eksik: …"`.
      Puanı yükseltmek için uydurma kelime eklenmez, anahtar kelime listesi de CV'ye göre budanmaz.
   3. `engine/adapters/<site>.md`'deki **başvuru yöntemini** uygula:
      - `otomatik`: tarayıcıda formu doldur. Sorular için `knowledge/forms.md` → `me/profile/answers.md`.
        Doldurmadan önce cevapları `<klasör>/form-cevaplar.md`'ye yaz.
      - `yarı-otomatik` (LinkedIn vb.): her şeyi hazırla, link + doldurulacak alanları
        kişiye ver; son adımı kişi yapar.
      - `manuel`: sadece belgeleri ve cevapları hazırla.
   4. Dosya yükleme alanına **başvuru klasöründeki** PDF'i ver (`application.md → cv_pdf`).
   5. **Gönderimden önce dur ve kişiye göster.** Açık onay olmadan gönderme. Kapının listelediği **eleyici soruları**
      (izin, konum, taşınma, ücret, dil, başlangıç; ⚠ işaretli olumsuz ya da boş cevaplar) kişiyle tek tek gözden geçir:
      ATS puanı yüksek başvurular en çok bu cevaplarla elenir (`knowledge/forms.md`).
   6. Kaydet: `python3 engine/pipeline/track.py set <klasör> başvuruldu --not "onay sayfası görüldü"`
      (başvuru ve takip tarihi otomatik yazılır). track kapıyı yeniden çalıştırır; geçmezse durum değişmez.
      `--harici` yalnızca kişinin vault dışında **kendisi** gönderdiği başvuruyu kayda geçirmek içindir;
      vault'ta hazırlanan bir başvuru için asla kullanılmaz.
4. Kişi bir ilandan vazgeçerse **sebebini sor** (tek soru, "geç" de kabul) ve kaydet:
   `python3 engine/pipeline/track.py set <klasör> iptal --sebep "…"` — sebep learn'in ana girdisidir.
5. Sonunda özet: başvurulan / kişiye bırakılan / atlanan / iptal (+ sebep).
6. **learn'i çalıştır** (zorunlu): bu oturumdaki form tuhaflıkları, iptal ve ret sebepleri, kişinin
   tercih ettiği ton. Sonra `python3 engine/pipeline/backup.py`.

## Durdurma koşulları (o ilanı atla, kişiye sor)
- ATS kapısı `DUR` dedi (yukarıda 3.2) — kanıtla %90'a çıkılamazsa ilan atlanır, kişi onayıyla da gönderilmez.
- Aynı role daha önce başvurulmuş ya da site bekleme süresi gösteriyor.
- Giriş gerekiyor ve oturum yok → kişi giriş yapar. Şifre girme.
- CAPTCHA → kişi tamamlar.
- `answers.md`'de karşılığı olmayan soru → kişiye sor, cevabı `answers.md`'ye ekle,
  soru kalıbını learn ile `knowledge/forms.md`'ye ekle.
- Formda ilan özetiyle çelişen bilgi (ör. remote değil ofis şartı) → kişiye sor.
