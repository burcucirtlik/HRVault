---
name: tara
description: Günlük turun tek komutu — ilanları tarar, eler, puanlar ve günlük listeyi sohbette gösterir; sonra hangilerine başvurulacağını sorar. Kişi "/tara", "tara", "bugün ne var", "yeni ilanlara bak", "günlük tur" dediğinde kullan. (Yalnızca toplama adımı için scan, yalnızca puanlama için score.)
---
<!-- durum: çalışır -->
# tara — tara, puanla, listeyi göster

Kişi tek komut yazar; `scan` ve `score` skill'lerinin işini sırayla sen yaparsın. Kişiye komut yazdırma, dosya açtırma.

1. **Kapı.** `python3 engine/pipeline/profile.py gate`. Profil hazır değilse tarama yok: eksik olanı tek cümleyle
   söyle ve `/başla` yazmasını öner. Dur.
2. **Tara.** `.claude/skills/scan/SKILL.md` dosyasını oku ve uygula (toplama + ilan metninden sınıflandırma).
   Uzun sürerse arada tek satırlık ilerleme ver ("3 kaynaktan 2'si bitti").
3. **Puanla.** `.claude/skills/score/SKILL.md` dosyasını oku ve uygula (kesin kurallar → puan → günlük liste).
4. **Paneli yenile.** `python3 engine/pipeline/dashboard.py`.
5. **Sohbette göster** — dosyaya yönlendirme, listeyi buraya yaz:
   - Tek satır özet: kaç ilan bulundu, kaçı elendi, kaçı listede. Tarama uyarılarını sade dille aktar
     ("bir kaynak bugün cevap vermedi; yarın yeniden denenecek").
   - En çok 10 satırlık tablo: `No · Rol · Şirket · Tip / yer · Puan · Neden uygun (bir cümle)`; ilan linkiyle.
     Daha fazlası varsa "kalan N ilan panelde" de.
   - Puanı düşüren açık bir eksik varsa o satırda söyle; gizleme.
6. **Sor:** "Hangilerine başvurmak istersin? Numaralarını yaz (örneğin: 1 ve 3). İstemediklerini de söyleyebilirsin."
   Cevabı `score` skill'indeki karar adımıyla listeye işle. En az bir ilan onaylandıysa son cümle:
   **"Başvuruları hazırlamak için `/başvur` yaz."**

## Liste boş ya da çok kısaysa
Geçiştirme. Taramanın eleme sayaçlarına bak ve **en çok ilan düşüren iki sebebi** sayılarıyla söyle
(dil, konum, ilan yaşı, başlık eşleşmesi…). Bir tane somut ayar öner; ayarı kişinin onayı olmadan değiştirme.
Sebep bir kaynağın cevap vermemesiyse bunu söyle, kriterleri suçlama.
