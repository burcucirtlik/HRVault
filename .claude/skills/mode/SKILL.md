---
name: mode
description: Worker'ları aktif/duraklatıldı yapar ve yeni worker ekler. "bu ara sadece freelance'e başvur", "part-time'ları da aç", "hepsini durdur", "yeni bir arama ekle", "hangi modlar açık" gibi isteklerde kullan.
---
<!-- durum: çalışır -->
# mode

## Amaç
Kişinin doğal dille söylediği iş tercihini `me/workers/*.md` dosyalarının `durum` alanına yansıtmak.

## Adımlar
1. `me/workers/` altındaki tüm worker'ları oku (frontmatter: ad, durum, çalışma_tipi, yer, roller).
2. İsteği yorumla:
   - "sadece X" → X'e uyanlar `aktif`, diğerleri `duraklatıldı`.
   - "X'i de aç" → X `aktif`, diğerlerine dokunma.
   - "N gün/hafta durdur" → `duraklatıldı` + `duraklatma_bitişi`.
   - Uyan worker yoksa → yeni bir arama, yeni bir iş tanımı demektir: coach §4 ile tanımı öner,
     kişi onaylayınca worker'ı kur. Onaysız worker taranmaz.
3. Değişiklikten önce ne yapacağını tek satırda söyle, sonra uygula.
4. Sonuç tablosu: worker · durum · çalışma tipi · yer.

## Kurallar
- Tüm worker'lar için ortak alanlar (yer, ülkeler, kaynaklar, günlük limit, saat, ortak hariç başlıklar)
  `me/profile/preferences.md → worker_varsayılanları`'nda. "Hepsinde X'i değiştir" isteği oraya yazılır;
  tek worker'a özel fark worker dosyasına yazılır (worker'daki değer varsayılanı ezer).
- `duraklatma_bitişi` geçmişse scan o worker'ı otomatik `aktif` sayar ve dosyayı günceller.
