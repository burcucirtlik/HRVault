# HRVault

**[Türkçe kılavuz](#turkce) · [English guide](#english)**

Senin için iş arayan, sana uygun ilanları seçen, ilana özel CV hazırlayan ve başvurularını takip eden bir asistan.
Claude uygulamasının içinde çalışır. Kurulumu Claude yapar; sen yalnızca sorularını cevaplarsın.

*An assistant that looks for jobs for you, picks the postings that fit, writes a CV for each one and tracks your
applications. It runs inside the Claude app. Claude does the setup; you just answer its questions.*

---

<a name="turkce"></a>

## Türkçe kılavuz

### Üç adımda başla

**Gereken tek şey:** ücretli bir Claude üyeliği (Pro, Max, Team ya da Enterprise) ve
[Claude masaüstü uygulaması](https://claude.ai/download). Başka bir şey kurman gerekirse Claude sana söyler.

**1. Boş bir klasör aç.**
Masaüstünde yeni bir klasör oluştur, adını `HRVault` koy.

**2. Klasörü Claude'a ver.**
Claude uygulamasını aç → sol üstte **Code** → mesaj kutusunun altındaki klasör düğmesi → **Open folder…** → az önce
açtığın klasörü seç. (Yanındaki ilk düğmede **Local** seçili olsun; "bu bilgisayarda" demektir.)

**3. Claude'a tek bir mesaj gönder.**
Bu sayfanın adresini tarayıcının adres çubuğundan kopyala. Sonra aşağıdaki mesajı Claude'a yapıştır ve sonuna
adresi ekle:

```text
Bu depoyu doğrudan bu klasöre klonla (alt klasör açma). Sonra CLAUDE.md ve .claude/skills/basla/SKILL.md dosyalarını okuyup kuruluma başla. Depo:
```

Claude izin isterse onayla. Gerisini o yapar: HRVault'u indirir, bilgisayarını kontrol eder ve sana soruları
**tek tek** sormaya başlar. Bitince **`/tara` yaz** der. Yazarsın, ilanların gelir.

**Sonraki günler:** Claude uygulamasında aynı klasörü aç. Yarıda bıraktıysan `/başla`, ilanlara bakmak için `/tara` yaz.

---

### Komutlar

Mesaj kutusuna `/` yazınca hepsi listede çıkar.

| Yaz | Ne olur |
|---|---|
| `/başla` | Kurulum ve tanışma. Yarıda bıraktıysan kaldığın yerden devam eder. |
| `/tara` | İlanları tarar, sana uymayanları eler, kalanları puanlar ve listeyi gösterir. |
| `/başvur` | Seçtiğin ilanlar için ilana özel CV hazırlar, senin onayınla başvurur. |
| `/durum` | Başvuruların ne durumda, bugün ne yapman gerekiyor. |
| `/panel` | Her şeyin özetini tarayıcıda açar. |
| `/yardım` | Bu listeyi ve sırada ne olduğunu gösterir. |

Klavyende Türkçe harf yoksa düz harfle yaz: `/basla`, `/basvur`, `/yardim`.

**Komut yazmak zorunda değilsin.** Ne istediğini düz cümleyle de söyleyebilirsin:

- *1 ve 3'e başvur, 2'yi reddet: maaşı düşük* (sebep yazarsan HRVault öğrenir, benzerlerini daha az gösterir)
- *X şirketinden ret geldi* · *Y şirketi mülakata çağırdı*
- *Şimdilik yalnızca freelance işlere bak*
- *Şu şirketi takip et:* ve şirketin kariyer sayfası linki
- *Yedek al*

---

### İlk gün ne olur?

Kurulum kısa bir turdur; ilk ilan listeni aynı oturumda görürsün. Ara verirsen sonra `/başla` yazarsın.

1. **Seni tanıyalım** — LinkedIn linkini ya da CV dosyanı verirsin; ikisi de yoksa anlatırsın. Claude okur ve özetler.
2. **Ne arıyorsun?** — Hayalindeki iş, nasıl çalışmak istediğin, nerede yaşadığın ve nerede çalışma iznin olduğu.
3. **Sana uygun işler** — Claude 3–4 iş türü önerir. **Sen onaylamadan hiçbir şey aranmaz.**
4. **Diller** — Hangi dilde ilanlara bakılacak, CV hangi dilde olacak.
5. **Takip edilecek şirketler** — Çalışmak istediğin şirketlerin adlarını yazarsın; yeni ilanları takip edilir. İstemezsen geçersin.

Taramanın gerektirmediği sorular sonraya kalır: başvuru formlarında sorulanlar (başlama tarihi, ücret beklentisi…)
ilk başvurunda, kırmızı çizgilerin ve önceliklerin ilk listeden sonra sorulur.

### Neyi iyi bulur?

HRVault en çok ilanı **uzaktan (remote) işlerde** ve **takip etmek istediğin şirketlerde** bulur. Kendi şehrinde
ofis işi arıyorsan liste kısa olabilir. İki çözüm var: kurulumda çalışmak istediğin şirketleri ekle, ya da başka bir
sitede beğendiğin ilanın linkini Claude'a yapıştır; ona da bakar, puanlar ve CV hazırlar.

---

### Claude izin istediğinde

Claude bir şey yapmadan önce bazen izin ister; ekranda ne yapmak istediğini gösteren bir kutu çıkar.

- **`python3 engine/…` ile başlayanlar HRVault'un kendi parçalarıdır; onaylamak normaldir.**
- Bir şeyi **silmek**, HRVault klasörünün **dışına** dokunmak ya da **ödeme** yapmak isterse önce "Bu ne işe yarıyor?"
  diye sor.

---

### HRVault neyi yapmaz?

- **Sen onaylamadan hiçbir başvuruyu göndermez.**
- Şifreni girmez, "robot değilim" kutularını geçmez; onları sen yaparsın.
- LinkedIn'de senin yerine başvurmaz: her şeyi hazırlar, son tıklamayı sen yaparsın.
- Senin hakkında bir şey uydurmaz. CV'ne yalnızca gerçekten yaptığın şeyleri yazar.
- CV'n ilanla **%90'dan az** uyuşuyorsa o ilana başvurmaz. Bu kural değişmez. Neyin eksik olduğunu söyler;
  o konuda gerçekten deneyimin varsa anlatırsın, eklenir.

---

### Verin ve gizliliğin

- HRVault'un senin hakkında yazdığı her şey bilgisayarında, HRVault klasörünün içindeki **`me`** klasöründe durur.
  HRVault bu dosyaları başka bir yere göndermez.
- Claude'la konuştukların, Claude'la yaptığın her sohbet gibi Claude tarafından işlenir. Başvuru formlarına yazılanlar da,
  sen onayladığında, o şirkete gider.
- **HRVault klasörünü kimseyle paylaşma.** Bir arkadaşına vermek istersen ona bu sayfanın adresini ver; kendi
  HRVault'unu kursun.
- Ayda bir **"Yedek al"** de. Klasörün yanına tarihli bir yedek koyar.

---

### Takılırsan

| Ne oldu | Ne yap |
|---|---|
| **Code** bölümü açılmıyor ya da "Upgrade" diyor | Hesabın ücretsiz. HRVault ücretli bir Claude planı gerektirir. |
| `/başla` listede yok ya da "Unknown command" diyor | Uygulamada aynı klasörde yeni bir sohbet aç ve tekrar yaz. Ya da düz bir mesaj olarak "kurulumu başlat" yaz. |
| Claude "git bulunamadı" diyor | Claude'a "git'i nasıl kurarım?" diye sor; adım adım anlatır. İstemezsen bu sayfada yeşil **Code → Download ZIP** ile indir, içindekileri klasörüne taşı, sonra "kurulumu başlat" yaz. |
| Claude "Python bulunamadı" diyor | `/başla` sana nasıl kuracağını söyler. Windows'ta kurarken **Add python.exe to PATH** kutusunu işaretle, sonra uygulamayı kapatıp aç. |
| CV PDF'i oluşmuyor | Google Chrome'u kur, sonra "PDF'i yeniden oluştur" de. |
| Çok az ilan çıkıyor | "Neden az ilan çıktı?" diye sor. Hangi kuralın kaç ilan elediğini söyler; gevşetmek istersen söylemen yeter. |
| Bir hata mesajı gördüm | Kopyala, Claude'a yapıştır, "bu ne demek?" diye sor. |

> **Windows hakkında dürüst bir not:** HRVault şimdiye kadar Mac'te kullanıldı. Windows'ta çalışması beklenir ama henüz
> denenmedi.

### Güncellemek

Claude'a **"HRVault'u güncelle"** de. Yeni sürümü indirir; `me` klasörüne (senin bilgilerine) dokunmaz.

---

<a name="english"></a>

## English guide

### Start in three steps

**All you need:** a paid Claude plan (Pro, Max, Team or Enterprise) and the
[Claude desktop app](https://claude.ai/download). If anything else is needed, Claude will tell you.

**1. Create an empty folder.**
Make a new folder on your Desktop and call it `HRVault`.

**2. Give the folder to Claude.**
Open the Claude app → **Code** at the top left → the folder button under the message box → **Open folder…** → pick
the folder you just made. (The first button next to it should say **Local**, which means "on this computer".)

**3. Send Claude one message.**
Copy this page's address from your browser's address bar. Then paste the message below to Claude and add the
address at the end:

```text
Clone this repository directly into this folder (no subfolder). Then read CLAUDE.md and .claude/skills/basla/SKILL.md and start the setup. Repository:
```

Approve when Claude asks for permission. It does the rest: downloads HRVault, checks your computer and starts
asking you questions **one at a time**. When it's finished it tells you to **type `/tara`**. You do, and your job list arrives.

**On later days:** open the same folder in the Claude app. Type `/basla` to pick up where you left off, `/tara` to look at jobs.

> HRVault's own files are written in Turkish, but Claude talks to you in the language you write in.

---

### Commands

Type `/` in the message box and they all appear in the list. The names are Turkish; the plain-letter spellings below
work on any keyboard.

| Type | Meaning | What happens |
|---|---|---|
| `/basla` | start | Setup and getting to know you. If you stopped halfway, it picks up where you left off. |
| `/tara` | scan | Scans job postings, drops the ones that don't fit, scores the rest and shows you the list. |
| `/basvur` | apply | Writes a tailored CV for the jobs you picked and applies with your approval. |
| `/durum` | status | Where your applications stand and what to do today. |
| `/panel` | dashboard | Opens a summary page in your browser. |
| `/yardim` | help | Shows this list and what comes next. |

**You don't have to use commands.** Plain sentences work too:

- *Apply to 1 and 3, reject 2: salary too low* (give a reason and HRVault learns to show fewer like it)
- *I got a rejection from company X* · *Company Y invited me to an interview*
- *Only look at freelance work for now*
- *Follow this company:* plus the link to its careers page
- *Make a backup*

---

### What happens on day one?

Setup is a short tour; you see your first job list in the same sitting. If you take a break, type `/basla` later.

1. **Getting to know you** — You give your LinkedIn link or your CV file; if you have neither, you tell your story. Claude reads it and sums it up.
2. **What you're looking for** — Your dream job, how you want to work, where you live and where you're allowed to work.
3. **Jobs that fit you** — Claude proposes 3–4 kinds of jobs. **Nothing is searched until you approve.**
4. **Languages** — Which languages to search postings in, and which language your CV should be in.
5. **Companies to follow** — You name companies you'd like to work for; their new postings are followed. You can skip this.

Questions the search doesn't need come later: what application forms ask (start date, salary expectation…) at your
first application, your red lines and priorities after your first list.

### What is it good at?

HRVault finds the most postings for **remote jobs** and at **companies you choose to follow**. If you're looking for
an office job in your own city, the list may be short. Two fixes: add the companies you'd like to work for during
setup, or paste a link to a posting you liked on any other site; Claude looks at it, scores it and writes a CV.

---

### When Claude asks for permission

Claude sometimes asks before doing something; a box shows what it wants to do.

- **Anything starting with `python3 engine/…` is part of HRVault itself; approving it is normal.**
- If it wants to **delete** something, touch files **outside** the HRVault folder or make a **payment**, ask
  "What is this for?" first.

---

### What HRVault won't do

- **It never sends an application without your approval.**
- It doesn't type your password or pass "I'm not a robot" checks; those are yours.
- It doesn't apply for you on LinkedIn: it prepares everything and you make the final click.
- It doesn't invent anything about you. Your CV only says things you've really done.
- If your CV matches a posting **less than 90%**, it doesn't apply. This rule is fixed. It tells you what's missing;
  if you really have that experience, you describe it and it's added.

---

### Your data and privacy

- Everything HRVault writes about you stays on your computer, in the **`me`** folder inside the HRVault folder.
  HRVault doesn't send these files anywhere.
- What you say to Claude is processed by Claude, like any conversation with it. What goes into an application form
  goes to that company, once you approve.
- **Don't share your HRVault folder with anyone.** If a friend wants it, give them this page's address so they can
  set up their own.
- Once a month say **"Make a backup"**. It puts a dated backup next to the folder.

---

### If you get stuck

| What happened | What to do |
|---|---|
| The **Code** section won't open or says "Upgrade" | Your account is on the free plan. HRVault needs a paid Claude plan. |
| `/basla` isn't in the list or says "Unknown command" | Open a new chat in the app (same folder) and type it again. Or send "start the setup" as a normal message. |
| Claude says "git not found" | Ask Claude "how do I install git?"; it walks you through it. Or use the green **Code → Download ZIP** button on this page, move the contents into your folder, then send "start the setup". |
| Claude says "Python not found" | `/basla` tells you how to install it. On Windows tick **Add python.exe to PATH** in the installer, then close and reopen the app. |
| The CV PDF isn't created | Install Google Chrome, then say "create the PDF again". |
| Very few jobs show up | Ask "Why so few jobs?". It tells you which rule dropped how many postings; say so if you want one relaxed. |
| I saw an error message | Copy it, paste it to Claude and ask "what does this mean?". |

> **An honest note about Windows:** so far HRVault has been used on Mac. It is expected to work on Windows but hasn't
> been tested there yet.

### Updating

Tell Claude **"Update HRVault"**. It downloads the new version and leaves your `me` folder (your information) alone.

---

Teknik ayrıntılar / technical details: [TEKNIK.md](TEKNIK.md) · [DESIGN.md](DESIGN.md)
