# Knowledge — genel öğrenimler

> **Paylaşılır.** Burada kişisel veri olmaz: isim, iletişim, ücret rakamı,
> başvurulan şirket adı, CV cümlesi yok. Şüphedeysen `me/learnings.md`'ye yaz.

| Dosya | Ne öğrenilir |
|---|---|
| `sites/<site>.md` | Site bazlı: form yapısı, tuzaklar, hangi adım manuel kalmalı |
| `forms.md` | Form soru kalıbı → cevabın alındığı profil alanı |
| `ats.md` | ATS ayrıştırma kuralları, format tercihleri |
| `classification.md` | İlan okuma: çalışma tipi, yer, saat nasıl çıkarılır |
| `scam-signals.md` | Sahte / riskli ilan sinyalleri |
| `writing.md` | CV ve ön yazıda genel olarak işe yarayan / yaramayan |

## Madde formatı

```markdown
- **[YYYY-MM-DD] Kısa başlık** `k:dosya-kisa-baslik`
  Ne öğrenildi, tek cümle. Nasıl uygulanır.
  _dayanak: <genel bilgi | N başvuru | N ilan> · güven: düşük | orta | yüksek · kapsam: genel_
```

- **`k:`** kalıcı kimlik. Başlık değişse de aynı kalır; vault'lar arası birleştirmenin anahtarıdır.
  `python3 engine/pipeline/export.py ids` kimliği olmayan maddelere ekler.
- **`kapsam`** yazılmazsa `genel`. Yalnızca bir ülkede geçerli maddede ülke kodu (`DE`, `TR`…); `sites/<site>.md`
  maddeleri zaten o siteyle sınırlıdır. Kapsamı kişinin durumuna uymayan madde uygulanmaz.
- **`dayanak`** sayım olsun ("2 form", "1 tarama"), anlatı olmasın. Devralınan maddede:
  `devralındı (1 form) + 2 form` — parantez içi paketle gelen, sonrası bu vault'ta görülen.
- Pakete girerken tarih silinir, dayanak sayıları yuvarlanır ("10 form" → "çok sayıda form") ve tek kişinin gözlemine
  dayanan maddenin güveni en fazla `orta` olur. Başlığında `**kapsam:** <ülke>` olan site notu pakete girmez.

## Örnek yazma kuralı

Örneklerde yer tutucu: `<Ülke>`, `<Şirket>`, `<rol>`. Kişinin ülkesi, aradığı rol, worker adı, başvurduğu şirket
ve oturum sayımları yazılmaz. Yazdıktan sonra: `python3 engine/pipeline/export.py lint <dosya>`.

## Devralınan bilgi

Paketle gelen maddelerin kimliği ve o andaki hali `knowledge/.baseline.json`'da durur. Bunlar başka birinin
gözlemidir: doğrulanana kadar varsayım say. Kendi öğrendiklerini kaynağa geri vermek için:
`python3 engine/pipeline/export.py build --knowledge-only`.

Çelişen bir öğrenim gelirse eskisini silme; altına yenisini yaz ve güveni güncelle.
