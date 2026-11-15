# HRVault — Tasarım

İş ilanlarını tarayan, kişiye uygun olanları günlük onaya sunan, onaylananlar için
özel CV / ön yazı hazırlayıp başvuran ve her başvuruyu kayıt altında tutan bir motor.

Vault **kişiden bağımsız bir motor** olarak kurulur. Kişiye ait her şey tek bir
klasörde (`me/`) durur; vault başkasına verilirken o klasör hiç gitmez.

---

## 1. Üç katman

```
HRVault/
├── .claude/skills/   ┐
├── engine/           ┘ PAYLAŞILIR — mekanizma
├── knowledge/          PAYLAŞILIR — süreçte öğrenilen genel bilgi
└── me/                 ASLA PAYLAŞILMAZ — kişi
```

| Katman | İçerik | Kim yazar |
|---|---|---|
| `.claude/skills/` | Akışın adımları (coach, scan, score, tailor, apply, track, learn, export, mode) | Geliştirici |
| `engine/adapters/` | Site bazlı tarama/başvuru talimatları | Geliştirici + `learn` |
| `engine/scanner/` | Tarama betiği ve kaynak modülleri (Python, standart kütüphane) | Geliştirici |
| `engine/export/` | Export manifesti (beyaz liste), ülke takma adları, commit öncesi hook, izinler | Geliştirici |
| `engine/pipeline/` | Profil kontrolü; export ve sızıntı taraması; onay listesi (filtre, puan, render, kararlar); başvuru kaydı, PDF, ATS ölçümü, takip, yedek | Geliştirici |
| `engine/tests/` | Eleme ve ayrıştırma kuralları için testler (`python3 -m unittest discover engine/tests`) | Geliştirici |
| `engine/templates/` | Boş profil şablonu, örnek worker'lar, CV/ön yazı şablonları | Geliştirici |
| `knowledge/` | Herkes için geçerli öğrenimler | `learn` |
| `me/` | Profil, worker'lar, kişisel öğrenimler, başvuru kayıtları | `coach`, `learn`, akış |

**Sınır kuralı:** `me/` dışına kişisel veri yazılmaz. İsim, iletişim bilgisi, maaş
rakamı, başvurulan şirket adı, CV'den cümle — hiçbiri `engine/` veya `knowledge/`
içine girmez.

---

## 2. Kişisel katmanın kuruluşu: kariyer koçu

Vault'u alan kişi `/coach` ile bir kariyer koçuyla konuşarak başlar. Tarama ve başvuru,
kişinin **onayladığı iş tanımlarına** göre çalışır; onaylı tanım yoksa tarama başlamaz.

```
Tanışma → Kanıt → Analiz → İş tanımları → [kişi onaylar] → Worker'lar → Tamamlama → scan
```

| Aşama | Ne olur | Yazılan dosya (`me/profile/`) |
|---|---|---|
| 1 Tanışma | Önce LinkedIn profili ayrıntılı okunur (CV gerekmez), sonra kişinin anlatımı: güçlü yanlar, çekinceler, hayalindeki iş ve sektör, çalışma biçimi (sabit/kontratlı/freelance/part-time, remote/hibrit/ofis), konum ve çalışma izni | `linkedin-notes.md`, `cv-master.md`, `goals.md`, `answers.md` |
| 2 Kanıt | Yetkinlik → kanıt; yalnızca analiz için önemli belirsizlikler sorulur | `evidence-bank.md` |
| 3 Analiz | Kanıtlı güç / kanıtlanması gereken / fark edilmeyen güç; çekincelere yanıt; hayal ile bugün arasındaki mesafe; konuma göre erişilebilir pazar | `career-analysis.md` |
| 4 İş tanımları | 3–6 tanım (ana · köprü · esnetme), her biri ilan başlıkları, filtreler, neden sen, açıklar; kişi onaylar / düzenler / reddeder | `job-definitions.md` |
| 5 Worker'lar | Her onaylı tanım → bir worker (`tanım: T<n>`) | `me/workers/*.md` |
| 6 Tamamlama | İlan ve CV dilleri (sorulur, varsayılmaz), konuma göre kaynaklar, form cevapları, kara liste, takip edilecek şirketler | `answers.md`, `preferences.md`, `me/sources.json` |

`profile.py check` hangi aşamada olunduğunu söyler. Koç uydurmaz: piyasa iddiası yalnızca
veriye (tarama sonuçları, kişinin bilgisi) dayanıyorsa yapılır. Tanımlar zamanla gözden geçirilir:
learn bir tanımda tekrarlayan ret/eleme kalıbı görürse koç değişiklik önerir, yine kişinin onayıyla.

---

## 3. Tek akış

```
scan → score → [günlük onay] → tailor → apply → track
                                                  ↓
                                                learn
```

1. **scan** — İki katman:
   - *Betik* (`engine/scanner/scan.py`, yalnızca standart kütüphane): aktif worker'ların
     kaynaklarından ilanları çeker, rol anahtar kelimesiyle başlıktan ön eler, kaynağın açıkça
     beyan ettiği uyumsuz yeri (ör. onsite) eler, başlıkta ya da ATS konum alanında worker'ın
     `ülkeler`iyle kesişmeyen bölge kısıtını ve worker'ın konuşmadığı dilde dil uzmanlığı ilanlarını eler,
     tekrarları birleştirir, son `seen_süresi_gün` (varsayılan 90) içinde görülenleri atlar
     → `me/pipeline/scans/YYYY-MM-DD.json`.
   - *Skill*: ilan metnini okuyup çalışma tipini, yeri ve saati **kendisi çıkarır** (etikete
     güvenmez), worker filtreleriyle karşılaştırır, `annotate` ile sonucu yazar.
   - Kaynaklar: ATS'ler (Greenhouse, Lever, Ashby — `me/sources.json` takip listesindeki şirketler)
     ve akışlar (Himalayas, We Work Remotely, Remotive, Remote OK). LinkedIn: elle link / alarm e-postası.
2. **score** — İki aşama:
   - *Kesin eleme:* worker filtresi (çalışma tipi, yer, ücret alt sınırı, dil,
     kıdem) + kara liste + aynı ilana mevcut başvuru + dolandırıcılık sinyali. Aynı şirkete
     birden çok başvuru serbesttir (sürekli açık havuz ilanları için kasıtlı).
   - *Uygunluk puanı:* 0–100, kısa gerekçe, eksik yetkinlikler.
3. **Günlük onay** — `engine/pipeline/inbox.py`: `filter` (kara liste,
   mevcut başvuru; dolandırıcılık kalıbı → uyarı) → score skill'i `rate` ile puanlar →
   `render` `me/pipeline/inbox/YYYY-MM-DD.md` yazar. Her ilan: worker, puan, gerekçe,
   eksikler, uyarılar, link. Kişi dosyada `[x]` / `ret:` ile ya da sohbette ("1 ve 3'e başvur")
   karar verir (`mark`); yeniden render işaretleri korur. `decisions --record` onaylananları
   apply'a, ret sebeplerini `me/pipeline/decisions.jsonl` üzerinden learn'e verir. Günlük yalnızca
   eklenir; anahtar ilan id'sidir ve aynı ilan için son satır geçerlidir (`inbox.py log`).
4. **tailor** — Onaylanan ilan için ATS simülasyonu (`engine/pipeline/ats.py`: zorunlu/tercih
   anahtar kelimelerinin CV'de ölçülen eşleşmesi) + kanıt bankasından özel CV, gerekiyorsa ön yazı.
   **Her hazırlanan CV ve ön yazı (md + PDF) başvurunun klasöründe saklanır**; PDF'i
   `engine/pipeline/render_pdf.py` üretir ve gönderilmiş başvurunun PDF'inin üzerine yazmaz.
   **Doğruluk kuralı:** mevcut deneyim yeniden sıralanır ve ifade edilir, olmayan
   yetkinlik asla eklenmez.
5. **apply** — Siteye göre:
   - Otomasyona açık siteler (Greenhouse, Lever vb.): form doldurulur, gönderimden
     önce kişi onaylar.
   - LinkedIn ve otomasyonu yasaklayan siteler: her şey hazırlanır, son adımı kişi yapar.
   - CAPTCHA / şifre / bilinmeyen form sorusu → başvuru durur, kişiye sorulur.
6. **track** — Her başvuru `me/pipeline/applications/<tarih>-<şirket>-<rol>/`
   klasöründe: ilan metni, gönderilen CV, ön yazı, form cevapları, durum geçmişi.
   Durumlar: `hazırlandı → başvuruldu → görüldü → mülakat → teklif | ret | sessiz`, ayrıca `iptal`
   (gönderilmeden vazgeçildi; `iptal_sebebi` zorunlu). `engine/pipeline/track.py`: tablo, vadesi gelen
   takipler, worker ve puan bandına göre dönüşüm.
7. **learn** — Her adımdan sonra öğrenilenleri ayırır (bkz. §4).

---

## 4. Worker = filtre profili

Ayrı süreç yoktur. Worker, onaylı bir iş tanımından türetilen ve tek akışa takılan
kayıtlı bir arama profilidir (`tanım: T<n>`; bağsız worker taranmaz):
çalışma tipi, yer, roller, ücret, saat, kaynaklar, CV vurgusu.

- `me/workers/*.md`, her birinde `durum: aktif | duraklatıldı`.
- Tüm worker'larda aynı olan alanlar (yer, ülkeler, kaynaklar, günlük limit, saat) `preferences.md →
  worker_varsayılanları`'nda durur; worker yalnızca farkı yazar. `ortak_hariç_başlık` her worker'ın
  hariç listesine eklenir.
- Kişi doğal dille yönetir: "bu ara sadece freelance'e başvur" → `mode` skill'i
  ilgili worker'ları aktif / duraklatıldı yapar.
- Worker'a göre değişenler: filtre, CV vurgusu, form cevapları (saatlik ücret vs.
  yıllık maaş, müsait saat), ön yazı tonu.
- Bir ilan birden fazla worker'a uyarsa tek sefer gösterilir.

---

## 5. Öğrenme kuralı

`learn` her öğrenim için sorar: **"Bu herkes için doğru mu?"**

| Öğrenim | Nereye |
|---|---|
| Lever formunda "Additional info" zorunlu değil | `knowledge/sites/lever.md` |
| Workable DOCX'i PDF'ten iyi ayrıştırıyor | `knowledge/ats.md` |
| "Contract-to-hire" freelance değil, full-time sayılmalı | `knowledge/classification.md` |
| Kişi fintech ilanlarını reddediyor | `me/learnings.md` |
| Kişi samimi ön yazı tonunu seviyor | `me/learnings.md` |

**Karışık öğrenim ikiye bölünür.** "Bu sitede maaş alanı sadece rakam kabul ediyor"
→ `knowledge/`. Rakamın kendisi → `me/`.

**Soru kalıbı genel, cevap kişisel.** `knowledge/forms.md` "bu soru gelince
profildeki `availability` alanından cevapla" der; cevap yalnızca `me/profile/`'da durur.

### Öğrenim formatı (knowledge/)

Her öğrenim ayrı bir madde; ileride başka kullanıcıların bilgisiyle birleştirmeyi
kolaylaştırmak için tarih ve dayanakla:

```markdown
- **[YYYY-MM-DD] Kısa başlık** `k:dosya-kisa-baslik`
  Ne öğrenildi, tek cümle. Nasıl uygulanır.
  _dayanak: 3 başvuru · güven: orta · kapsam: genel_
```

`k:` kalıcı kimliktir (birleştirmenin anahtarı); `kapsam` yazılmazsa `genel`, bölgeye özgü maddede ülke kodu.
Örneklerde yer tutucu kullanılır (`<Ülke>`, `<Şirket>`, `<rol>`); kişinin ülkesi, aradığı rol ve oturum sayımları yazılmaz.

---

## 6. Export

`export` skill'i ve `engine/pipeline/export.py` paylaşılabilir paket üretir. Altı ilke:

1. **Beyaz liste.** Pakete yalnızca `engine/export/manifest.json → kopyala` ile eşleşen dosyalar girer.
   Eşleşmeyen ve `asla`'da da olmayan dosya bulgudur ("tanınmayan dosya").
2. **Kapalı başarısızlık.** Profilden isim ve e-posta deseni üretilemiyorsa, bir dosya okunamıyorsa ya da
   manifest yoksa sonuç "temiz" değil "tarama yapılamadı"dır (çıkış kodu 2).
3. **Önce kaynağı düzelt.** Bulgu `knowledge/` ya da `engine/` içinde düzeltilir; kopyada yama yapılmaz.
4. **Erken yakala.** Aynı tarama üç yerde çalışır: `learn` yazarken, commit öncesi (`install-hook`), export'ta.
5. **İki seviye.** `engel` (isim, e-posta, telefon, profil adresi, işveren/okul, takip edilen ve başvurulan
   şirket, kullanıcı yolu, şablonda dolu alan): istisnası yok. `gözden_geçir` (ülke/şehir, aranan rol, worker ve
   tanım adı, ücret rakamı, profilden 6 kelimelik cümle parçası): varsayılan genelleştir; tutmak için kişinin
   onayıyla `export.py allow` (`engine/export/allow.json`; satır değişirse izin düşer, dosya pakete girmez).
6. **Betik belirler, Claude yorumlar.** Betik temiz dedikten sonra Claude `knowledge/` maddelerini anlam olarak okur:
   kişinin deneyimi mi, sitenin davranışı mı?

Desenler `me/` içinden (cevap bankası, ana CV, kanıt bankası, takip listesi, kara liste, başvurular, kararlar,
worker'lar, iş tanımları) belleğe okunur; hiçbir yere yazılmaz. Herkese açık platform adları ve motorun kendi
kelimeleri manifestte `platform_adları` / `genel_kelimeler` olarak beyan edilir.

```
lint → build (prova: geçici klasör, yeniden tarama) → anlam okuması → kişi onaylar → build --reviewed → verify
```

Paket: dosyalar içerik olarak yazılır (öznitelik ve tarih taşınmaz, tek sabit tarih), `me/` boş şablondur,
`knowledge/` ve adaptörlerdeki tarihler silinir, dayanak sayıları yuvarlanır ("10 form" → "çok sayıda form"),
**bölgesel adaptörler** (başlığında `kapsam: <ülke>` olanlar; kod, adaptör ve site notu birlikte) varsayılan olarak
girmez, git geçmişi yoktur. `EXPORT.json` motor sürümünü, dosya özetlerini ve
madde kimliklerini taşır; kişi, makine ya da yol bilgisi taşımaz. `verify` paketi `me/` olmadan doğrular.
**`EXPORT.json`'ı olmayan ya da `verify`'dan geçmeyen klasör paket değildir.**

### Paketi alan kişi

- Oturum başında `profile.py gate` (SessionStart hook'u) durumu bağlama ekler; profil hazır değilken Claude
  kişiyi `/coach`'a yönlendirir ve `scan` / `score` / `apply` çalışmaz.
- `profile.py doctor` ortamı denetler ve eksik olanın hangi adımı etkilediğini söyler.
- Varsayılanlar nötrdür: şablonda yalnızca küresel kaynaklar açık, `ülkeler`, `ilan_dilleri`, `cv_dili` boş.
  Her adaptör `kapsam:` taşır; coach bölgesel kaynakları kişinin konumuna göre önerir.
- **Arayüz dili Türkçedir; aranan ilanların dili ayrı bir karardır.** Coach "hangi dillerde yazılmış ilanlara
  bakalım" diye sorar (`ilan_dilleri`); boşken profil hazır sayılmaz.

### Bilginin taşınması

- Her `knowledge/` maddesi kalıcı bir kimlik (`k:`) ve gerekirse `kapsam` taşır (§5).
- Paket `knowledge/.baseline.json` ile gelir: devralınan maddelerin kimliği, içerik özeti ve dayanağı.
  Alıcının `learn`'ü kendi gözlemini ayrı sayar: `devralındı (1 form) + 2 form`.
- Pakette tek kişinin gözlemine dayanan maddenin güveni en fazla `orta`dır.
- Geri dönüş: `export.py build --knowledge-only` yalnızca baseline'dan beri yeni ya da değişen maddeleri
  paketler; kaynak vault `export.py merge <paket>` ile kimliğe göre birleştirir (aynı içerik → `+1 kullanıcı`,
  güven bir basamak artar; farklı içerik → ikisi de kalır, kişi karar verir).

---

## 7. Sabit kurallar

- **Platform kuralları:** LinkedIn ve otomasyonu yasaklayan siteler yalnızca keşif
  için kullanılır; başvurunun son adımını kişi yapar. Hesap riski alınmaz.
- **Şifre ve CAPTCHA:** motor şifre girmez, CAPTCHA geçmez. Girişi kişi yapar.
- **Gönderim onayı:** hiçbir form kişinin onayı olmadan gönderilmez.
- **Doğruluk:** CV ve ön yazıda uydurma yetkinlik, rakam veya deneyim yok.
- **Bilinmeyen soru:** form cevap bankasında olmayan soruda tahmin yapılmaz, sorulur.
- **Günlük limit:** worker başına günlük başvuru üst sınırı (`me/profile/preferences.md`).
- **Gönderilen belge değişmez:** gönderilmiş başvurunun CV/ön yazı PDF'i yeniden üretilmez.
- **Yedek:** `me/` git'e girmez; `engine/pipeline/backup.py` tarihli zip yedeğini vault dışına alır.

---

## 8. Yol haritası

- [x] Tasarım ve iskelet
- [x] `coach` — kariyer koçu: tanışma, kanıt, analiz, iş tanımları ve onay, tanımlardan worker (`profile.py init | check`)
- [x] `scan` + adaptörler: Greenhouse, Lever, Ashby, Himalayas, WWR, Remotive, Remote OK
- [ ] LinkedIn alarm e-postalarını otomatik okuma (e-posta kaynağı seçilecek)
- [ ] Ek ATS adaptörleri: Workable, SmartRecruiters, Personio
- [x] `score` + günlük onay dosyası
- [x] `tailor` — ATS ölçümü (`ats.py`), CV/ön yazı, PDF (`render_pdf.py`)
- [x] `track` — başvuru kaydı, durum güncelleme, takip ve dönüşüm (`track.py`)
- [x] `apply` — yarı otomatik (gönderim öncesi kişi onayı); tam otomatik yok
- [x] `learn` — apply sonrası zorunlu adım
- [x] `export` — beyaz liste, sızıntı taraması, paket ve doğrulama, bilgi paketi ve birleştirme (`export.py`)
- [x] Yeni kurulum: oturum kapısı, `profile.py doctor`, nötr varsayılanlar, ilan dili sorusu
- [ ] E-postadan durum güncelleme (track)
- [ ] Zamanlama (günlük tarama) ve bildirim kanalı
