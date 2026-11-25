---
name: durum
description: Başvuruların ve kurulumun durumunu tek bakışta özetler; gelen cevapları (ret, mülakat daveti) kayda geçirir. Kişi "/durum", "durum", "başvurularım ne oldu", "neredeyiz", "şu şirketten cevap geldi" dediğinde kullan.
---
<!-- durum: çalışır -->
# durum — neredeyiz?

1. `python3 engine/pipeline/profile.py gate`. Kurulum bitmediyse hangi adımda kaldığını söyle, `/başla` öner.
2. `.claude/skills/track/SKILL.md` oku. Çalıştır: `python3 engine/pipeline/track.py list`, `track.py due`.
3. Sohbette kısa özet (dosyaya yönlendirme):
   - Gönderilen · cevap bekleyen · mülakat · ret sayıları.
   - **Bugün yapılacaklar:** takip tarihi gelenler ve kişinin son adımını bekleyen başvurular.
   - Günlük listede karar bekleyen ilan varsa sayısı.
4. Kişi bir gelişme söylediyse ("X'ten ret geldi", "mülakata çağrıldım") `track` skill'iyle kaydet; ret ya da
   mülakat sonucu ise `learn` skill'ine de haber ver.
5. Paneli yenile: `python3 engine/pipeline/dashboard.py`. Ayrıntı isteyene: "`/panel` yaz, tarayıcıda açayım."
