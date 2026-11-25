---
name: export
description: Vault'un paylaşılabilir kopyasını üretir — motoru ve genel bilgiyi alır, me/ yerine boş şablon koyar, kişisel veri sızıntısı taraması yapıp rapor verir. Yalnızca öğrenimleri içeren küçük bir paket de üretebilir ve başka bir vault'tan gelen öğrenimleri birleştirir. "vault'u paylaş", "başkasına ver", "export", "temiz kopya", "öğrendiklerimi geri gönder", "bu bilgi paketini birleştir" isteklerinde kullan.
---
<!-- durum: çalışır -->
# export

Betik: `engine/pipeline/export.py`. Neyin pakete girdiği: `engine/export/manifest.json` (beyaz liste).
Betik karar verir, sen yorumlarsın: betiğin "temiz" demediği hiçbir şeye "hazır" deme.

## İlkeler
- **Düzeltme kaynakta.** Bulguyu `knowledge/` ya da `engine/` içinde düzelt, sonra yeniden çalıştır. Kopyaya dokunma.
- **`engel`** (isim, e-posta, telefon, şirket, kullanıcı yolu, tanınmayan dosya): istisnası yok.
- **`gözden_geçir`** (ülke/şehir, aranan rol, worker adı, ücret rakamı, profilden cümle): önce genelleştir
  (`<Ülke>`, `<rol>`). Kural genelleşince anlamını yitiriyorsa kişiye **tek tek** sor; onaylarsa
  `export.py allow <dosya> <satır> --gerekce "…"`. Kişi adına izin verme.
- **`TARAMA YAPILAMADI`** (çıkış kodu 2) "temiz" değildir. Sebebini çöz; atlama.
- Raporları dosyaya yazma (bulgu satırları kişisel olabilir); sohbette göster.

Pakette tarih yoktur, dayanak sayıları yuvarlanır, **bölgesel adaptörler** (başlığında `**kapsam:** <ülke>`)
kodu ve site notuyla birlikte dışarıda kalır. Raporun sonundaki `[bilgi]` satırı hangilerinin kaldığını söyler; kişi
bölgesel adaptörleri de paylaşmak isterse manifestte `bölgesel_adaptörler: true`.

## Adımlar
1. `python3 engine/pipeline/export.py lint`
   Bulgu varsa: dosya · satır · tür · öneri (sil / genelleştir / me'ye taşı) olarak göster, kaynakta düzelt, tekrarla.
   Tanınmayan dosya: gerekliyse manifeste eklemeyi, değilse dışarıda bırakmayı (`asla`) kişiye sor.
2. `python3 engine/pipeline/export.py build` — prova. Paket oluşmaz; geçici klasörde kurulur, yeniden taranır
   ve anlam okuması bekleyen `knowledge/` dosyalarını listeler.
3. **Anlam okuması** — listelenen dosyalarda ve `me/learnings.md → Genel adayı` başlığında, madde madde:
   - Bu madde bir **kişinin deneyimini** mi anlatıyor, yoksa bir **sitenin/formun davranışını** mı?
   - Örnek, kuralı anlatmak için gerekli mi? Değilse yer tutucuya çevir.
   - Sayılar kişinin etkinliğini mi ölçüyor ("N aramada M ilan")? Kuralı bırak, sayımı at.
   - Birden çok maddeden birlikte çıkan bir profil var mı (yer + rol + tarih)?
   Karar: `tut` / `genelleştir` / `me'ye taşı`. Değişiklik kaynakta → 1. adıma dön.
4. Kişiye özet ver: kaç dosya, hangi izinler (gerekçeleriyle), neleri genelleştirdin. **Onay iste.**
5. `python3 engine/pipeline/export.py build --reviewed [--dest <klasör>] [--zip]`
   Hedef varsayılanı `../HRVault-share-YYYY-MM-DD/`. Klasör varsa betik durur; üzerine yazmadan önce kişiye sor.
   Betik paketi yazar, `EXPORT.json` ekler ve `verify` çalıştırır.
6. Kişiye söyle: paket yeni bir klasördür, git geçmişi taşımaz; **kendi vault'unu ya da onun deposunu paylaşma**.
   Paket ayrı bir depoda yayımlanacaksa (GitHub): depo klasörü paketin kendisidir. Sonraki sürümler
   `export.py build --reviewed --update <depo-klasörü>` ile yazılır (`.git` korunur, diğer her şey yeni paketle değişir),
   commit'ten önce `git diff --stat` kişiye gösterilir. Commit kimliği olarak kişinin iş e-postası değil GitHub'ın
   no-reply adresi önerilir (`git config user.email` yalnızca o depoda). Depoyu herkese açmak kişinin açık kararıdır.
   Alıcı `README.md`'yi okur ve `/başla` ile başlar.

## Yalnızca öğrenimler (kaynağa geri dönüş)
`python3 engine/pipeline/export.py build --knowledge-only` (prova), sonra `--reviewed`.
Paket yalnızca `knowledge/.baseline.json`'dan beri eklenen ya da dayanağı değişen maddeleri içerir; aynı
tarama, anlam okuması ve onaydan geçer.

## Gelen öğrenimleri birleştirme
`python3 engine/pipeline/export.py merge <paket>` — önce paketi doğrular. Aynı kimlik ve aynı içerik: dayanağa
`+1 kullanıcı` eklenir, güven bir basamak artar. Yeni kimlik: eklenir. Aynı kimlik, farklı içerik: ikisi de kalır
(`k:<kimlik>-gelen`); kişiye göster, birini seçsin ya da birleştirin. Sonra `export.py lint`.

## Kural
`EXPORT.json`'ı olmayan ya da `export.py verify`'dan geçmeyen klasöre "paket" denmez.
