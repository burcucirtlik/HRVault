---
name: başvur
description: Günlük listede onaylanan ilanlar için CV'yi ilana göre hazırlar, başvuru sistemi taramasını ölçer ve başvuruyu kişinin onayıyla yapar. Kişi "/başvur", "başvur", "basvur", "seçtiklerime başvur", "başvuruları hazırla" dediğinde kullan.
---
<!-- durum: çalışır -->
# başvur — onaylananları hazırla ve başvur

`tailor` ve `apply` skill'lerinin işini sırayla yürütür. Kişiye komut yazdırma.

1. **Kapı.** `python3 engine/pipeline/profile.py gate`; hazır değilse `/başla` öner ve dur.
2. **Onaylananlar.** `python3 engine/pipeline/inbox.py decisions`. Onaylanmış ilan yoksa: "Önce `/tara` yazıp
   listeden seçim yapman gerekiyor." Dur. Kişi komutla birlikte numara yazdıysa ("/başvur 1 3") önce onu
   `score` skill'indeki karar adımıyla işle.
3. **Her ilan için, sırayla** (birini bitirmeden diğerine geçme):
   - `.claude/skills/tailor/SKILL.md` oku ve uygula: CV (gerekirse ön yazı) + ölçüm.
   - Sonucu sade dille söyle: "Bu ilanın aradığı kelimelerin %N'i CV'nde var." **%90'ın altındaysa başvuru
     yapılmaz** — bu kural değişmez, kişi istese de aşılmaz. Eksik kelimeleri göster; yalnızca kişinin
     gerçekten sahip olduğu ve kanıt verebildiği olanlar eklenir. Kanıt yoksa o ilan bırakılır; bunu açıkça söyle.
   - `.claude/skills/apply/SKILL.md` oku ve uygula.
4. **Her gönderimden önce** formun dolu halini göster ve açık onay iste. Onay bir ilan içindir, sonrakine taşınmaz.
5. Bittiğinde paneli yenile (`python3 engine/pipeline/dashboard.py`) ve özet ver: hangisi gönderildi,
   hangisi kişinin son adımını bekliyor, hangisi neden bırakıldı. Son cümle: "Durumu görmek için `/durum` yaz."

## Kişiye baştan söylenecek üç şey (ilk kullanımda, birer cümle)
- Hiçbir form onayın olmadan gönderilmez.
- Şifreni ben girmem, "robot değilim" doğrulamasını ben geçmem; o adımlar sende.
- LinkedIn'de son tıklamayı sen yaparsın; ben her şeyi hazırlarım.
