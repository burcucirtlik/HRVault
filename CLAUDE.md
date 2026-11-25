# HRVault — Claude için çalışma kuralları

Bu vault bir iş arama ve başvuru motorudur. Tam tasarım: `DESIGN.md`.

## Oturum başı kapısı

Her oturumun başında `python3 engine/pipeline/profile.py gate` çıktısına bak (SessionStart hook'u bağlama ekler;
yoksa kendin çalıştır). `me/` yoksa ya da profil `HAZIR DEĞİL` ise kişi ne isterse istesin önce durumu söyle ve
`/coach` ile kaldığı yerden devam etmeyi öner. Profil hazır değilken `scan`, `score`, `apply` çalışmaz.

## Katman sınırı (en önemli kural)

- `engine/`, `.claude/`, `knowledge/` → **paylaşılır.** Buraya asla kişisel veri yazma:
  isim, e-posta, telefon, adres, maaş/ücret rakamı, başvurulan şirket adı,
  CV'den cümle, kişinin tercihleri.
- `me/` → **kişiye ait, asla paylaşılmaz.** Profil, worker'lar, kişisel öğrenimler,
  başvuru kayıtları burada.
- Emin değilsen `me/` içine yaz.
- Paylaşılan katmanda örnek gerekiyorsa yer tutucu kullan (`<Ülke>`, `<Şirket>`, `<rol>`); kişinin ülkesini,
  aradığı rolü, worker adını ya da oturum sayımlarını ("N aramada M ilan") örnek olarak yazma.
- `knowledge/` ya da `engine/` içine yazdıktan sonra: `python3 engine/pipeline/export.py lint <dosya>`.

## Öğrenirken

Bir şey öğrendiğinde sor: "Bu, vault'u kullanan herkes için doğru mu?"
- Evet → `knowledge/` altındaki ilgili dosyaya, `DESIGN.md` §4 formatında.
- Hayır → `me/learnings.md`.
- Karışık → ikiye böl: genel kural `knowledge/`'a, kişisel detay `me/`'ye.

## Akış sırasında

- Kişinin profili: `me/profile/`. Aktif worker'lar: `me/workers/` içinde `durum: aktif` olanlar.
- Tarama: `python3 engine/scanner/scan.py run | brief | show | annotate | detect` (ayrıntı: scan skill'i).
- Profil: `python3 engine/pipeline/profile.py init | check | doctor | gate` (ayrıntı: coach skill'i).
- Tarama yalnızca **onaylanmış iş tanımına** (`me/profile/job-definitions.md`) bağlı aktif worker'larla çalışır.
- Onay listesi: `python3 engine/pipeline/inbox.py filter | rate | render | mark | decisions | log` (ayrıntı: score skill'i).
- Başvuru: `engine/pipeline/ats.py` (ATS ölçümü), `render_pdf.py` (CV/ön yazı PDF), `track.py list | due | stats | set`,
  `backup.py` (me/ yedeği). Ayrıntı: tailor, apply, track skill'leri.
- Öğrenme raporu: `python3 engine/pipeline/learn.py rapor | verim | elemeler | bekleyen` (yalnızca okur; öneriler
  kişinin onayıyla uygulanır — ayrıntı: learn skill'i).
- Panel: `python3 engine/pipeline/dashboard.py [--open]` → `me/dashboard.html` (yerel, kişisel; yayımlanmaz). Tarama, puanlama
  ya da başvuru durumu değişince yeniden üret.
- **Her hazırlanan CV ve ön yazı (md + PDF) başvurunun klasöründe saklanır**; gönderilmiş başvurunun PDF'i yeniden üretilmez.
- Paylaşım: `python3 engine/pipeline/export.py lint | allow | ids | build | verify | merge | install-hook` (ayrıntı: export skill'i).
- Arayüz dili Türkçedir; **aranan ilanların dili ayrı bir ayardır** (`preferences.md → worker_varsayılanları.ilan_dilleri`,
  CV için `cv_dili`). Varsayma, coach sorar.
- Motoru değiştirdikten sonra: `python3 -m unittest discover engine/tests`.
- `me/profile/preferences.md` ayarları dosyanın başındaki `---` bloğunda; betikler oradan okur.
- Bir siteyle çalışmadan önce `engine/adapters/<site>.md` ve `knowledge/sites/<site>.md` oku.
- Form sorusu: önce `knowledge/forms.md`'de kalıbı bul, cevabı `me/profile/answers.md`'den al.
  Cevap yoksa tahmin etme, kişiye sor ve cevabı `answers.md`'ye ekle.
- CV / ön yazıda yalnızca `me/profile/` içinde dayanağı olan bilgiyi kullan. Uydurma yok.
- Hiçbir formu kişinin açık onayı olmadan gönderme. Şifre girme, CAPTCHA geçme.
- **ATS puanı %90'ın altındaysa başvuru yok** (`ats.py <klasör> --gate`). Sabit kural: ayarla değişmez,
  kişi onayıyla da aşılmaz. Puan yalnızca kanıta dayalı kelimelerle yükseltilir; öneriler kişiye sunulur.
- LinkedIn'de otomatik başvuru yapma; her şeyi hazırla, son adımı kişi yapsın.

## Skill'ler

`.claude/skills/` altında: `coach` (kariyer koçu, giriş noktası), `mode`, `scan`, `score`, `tailor`, `apply`,
`track`, `learn`, `export`. Durumları için her SKILL.md'nin başına bak.
