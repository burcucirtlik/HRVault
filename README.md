# HRVault

İş ilanlarını tarayan, sana uygun olanları her gün onayına sunan ve onayladıkların
için özel CV / ön yazı hazırlayıp başvuran bir motor. Claude Code ile çalışır.

## Verin nerede durur

Anlattığın ve profilinden okunan her şey yalnızca **senin bilgisayarındaki `me/` klasörüne** yazılır.
Bu klasör git'e girmez ve vault başkasına verilirken pakete girmez. Yedeğini sen alırsın:
`python3 engine/pipeline/backup.py`.

## Ne gerekir

| Gerekli | Ne için | Yoksa |
|---|---|---|
| Claude Code | Her şey | — |
| Python 3.9+ | Tarama, onay listesi, kayıtlar | Hiçbir betik çalışmaz |
| Chrome ya da Chromium | CV / ön yazı PDF'i | Başvuru adımına kadar kurman yeterli |
| Claude in Chrome eklentisi | LinkedIn profilini okumak, form doldurmak | LinkedIn "Save to PDF" çıktısı kullanılır; formu sen doldurursun |

Kontrol: `python3 engine/pipeline/profile.py doctor`

## İlk 30 dakika

1. Bu klasörü Claude Code'da aç ve `/coach` yaz. (Başka bir şey yazsan da Claude seni buraya yönlendirir.)
   İlerlemeni panelde izle: `python3 engine/pipeline/dashboard.py --open`. Panel tarayıcında açılır; en üstteki kurulum
   kartı hangi aşamada olduğunu ve sıradaki adımı gösterir, her adımla dolar.
2. **Tanışma** — koç LinkedIn profil linkini ister ve profilini ayrıntılı okur (CV gerekmez). Sonra konuşursunuz:
   güçlü gördüğün yanlar, çekincelerin, hayalindeki iş ve sektör, nasıl çalışmak istediğin, nerede yaşadığın
   ve çalışma iznin.
3. **Kanıt ve analiz** — koç yetkinliklerini kanıtlarıyla eşler ve bir kariyer analizi yapar.
4. **İş tanımları** — koç 3–6 tanım önerir; onaylar, düzenler ya da reddedersin. Onaylamadığın hiçbir şey taranmaz.
5. **Tamamlama** — koç sorar: hangi dillerde yazılmış ilanlara bakılsın, CV hangi dillerde hazırlansın,
   yaşadığın yere göre hangi kaynaklar açılsın. Bu vault'un arayüzü Türkçe; ilan dili senin kararın.
6. `/scan` ile ilk taramayı başlat. Sonuçlar `me/pipeline/inbox/` altına gelir.

## Günlük kullanım

- **Panel** (`me/dashboard.html`): son tarama, elenenler ve sebepleri, başvurular ve ATS uyumu (eksik kelimelerle),
  retler, kaynakların en son ne zaman tarandığı ve tarama kriterleri. Yalnızca senin bilgisayarında durur, hiçbir yere gönderilmez.
- Onay listesini aç, istediğin ilanları `[x]` ile işaretle.
- "Onaylananlara başvur" de. Her başvuru için CV hazırlanır, gönderimden önce sana gösterilir.
- İş tanımlarını gözden geçir: "tanımlarımı gözden geçirelim".
- Mod değiştir: "bu ara sadece freelance'e başvur", "part-time remote'ları da aç".

## Ne çalışıyor, ne çalışmıyor

Çalışır: kariyer koçu, tarama (Greenhouse, Lever, Ashby, Himalayas, We Work Remotely, Remotive, Remote OK ve
bölgesel kaynaklar), puanlama ve günlük onay listesi, ilana özel CV / ön yazı, yarı otomatik başvuru
(gönderimden önce hep sana sorar), başvuru takibi, paylaşım paketi.

Henüz yok: LinkedIn alarm e-postalarını otomatik okuma, e-postadan durum güncelleme, zamanlanmış günlük tarama.
Motor şifre girmez, CAPTCHA geçmez, LinkedIn'de senin yerine başvurmaz.

## Klasörler

| Klasör | Ne var | Paylaşılır mı |
|---|---|---|
| `engine/` | Motor: betikler, adaptörler, şablonlar | Evet |
| `knowledge/` | Süreçte öğrenilen genel bilgi | Evet |
| `me/` | Senin profilin, worker'ların, başvuruların | **Hayır** |

`knowledge/` sana başka birinin deneyimiyle gelir (`knowledge/.baseline.json`); senin öğrendiklerin ayrı sayılır.

## Paylaşmak

Vault'u başkasına vermek için `/export` kullan: kişisel veri taramasından geçmiş, `me/` yerine boş şablon içeren
yeni bir klasör üretir. **Kendi vault klasörünü doğrudan kopyalayarak ya da kendi deposunu paylaşma**; yalnızca bu
paketi paylaş. Paket ayrı bir git deposu olarak yayımlanabilir: sonraki sürümleri aynı depoya
`export.py build --reviewed --update <depo-klasörü>` ile yazarsın. Yalnızca öğrendiklerini geri
göndermek için: "öğrendiklerimi paketle".

Ayrıntılar: `DESIGN.md`.
