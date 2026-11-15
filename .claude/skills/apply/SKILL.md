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
   1. tailor'ı çalıştır (CV + ön yazı + PDF başvuru klasörüne).
   2. `engine/adapters/<site>.md`'deki **başvuru yöntemini** uygula:
      - `otomatik`: tarayıcıda formu doldur. Sorular için `knowledge/forms.md` → `me/profile/answers.md`.
        Doldurmadan önce cevapları `<klasör>/form-cevaplar.md`'ye yaz.
      - `yarı-otomatik` (LinkedIn vb.): her şeyi hazırla, link + doldurulacak alanları
        kişiye ver; son adımı kişi yapar.
      - `manuel`: sadece belgeleri ve cevapları hazırla.
   3. Dosya yükleme alanına **başvuru klasöründeki** PDF'i ver (`application.md → cv_pdf`).
   4. **Gönderimden önce dur ve kişiye göster.** Açık onay olmadan gönderme.
   5. Kaydet: `python3 engine/pipeline/track.py set <klasör> başvuruldu --not "onay sayfası görüldü"`
      (başvuru ve takip tarihi otomatik yazılır).
4. Kişi bir ilandan vazgeçerse **sebebini sor** (tek soru, "geç" de kabul) ve kaydet:
   `python3 engine/pipeline/track.py set <klasör> iptal --sebep "…"` — sebep learn'in ana girdisidir.
5. Sonunda özet: başvurulan / kişiye bırakılan / atlanan / iptal (+ sebep).
6. **learn'i çalıştır** (zorunlu): bu oturumdaki form tuhaflıkları, iptal ve ret sebepleri, kişinin
   tercih ettiği ton. Sonra `python3 engine/pipeline/backup.py`.

## Durdurma koşulları (o ilanı atla, kişiye sor)
- Giriş gerekiyor ve oturum yok → kişi giriş yapar. Şifre girme.
- CAPTCHA → kişi tamamlar.
- `answers.md`'de karşılığı olmayan soru → kişiye sor, cevabı `answers.md`'ye ekle,
  soru kalıbını learn ile `knowledge/forms.md`'ye ekle.
- Formda ilan özetiyle çelişen bilgi (ör. remote değil ofis şartı) → kişiye sor.
