# HRVault

**[Türkçe kılavuz](#turkce) · [English guide](#english)**

Senin için iş arayan, sana uygun ilanları seçen, ilana özel CV hazırlayan ve başvurularını takip eden bir asistan.
Claude uygulamasının içinde çalışır; komut yazmana gerek yok.

*An assistant that looks for jobs for you, picks the postings that fit, writes a CV for each one and tracks your
applications. It runs inside the Claude app; you don't need to type any commands.*

---

<a name="turkce"></a>

## Türkçe kılavuz

Bu kılavuz, bilgisayarı e-posta, belge ve internet için rahatça kullanan ama hiç "terminal" açmamış, kod yazmamış biri için.
Hiçbir komut yazmayacaksın. Claude'la sohbet ederek ilerleyeceksin.

---

### HRVault ne yapar?

HRVault senin için iş arayan bir asistandır.

- İnternetteki iş ilanlarını tarar ve sana uymayanları eler.
- Kalanları puanlar ve her gün sana kısa bir liste sunar.
- Senin seçtiğin ilanlar için o ilana özel bir CV hazırlar.
- Başvurunu hazırlar. **Sen "gönder" demeden hiçbir başvuruyu göndermez.**
- Hangi şirkete ne zaman başvurduğunu ve sonucunu takip eder.

#### Ne yapmaz?

- Şifreni girmez. "Ben robot değilim" kutularını geçmez; onları sen yaparsın.
- LinkedIn'de senin yerine başvurmaz. Her şeyi hazırlar, son tıklamayı sen yaparsın.
- Senin hakkında bir şey uydurmaz. CV'ne yalnızca gerçekten yaptığın şeyleri yazar.

---

### Başlamadan önce neye ihtiyacın var?

| Ne | Neden | Ücret |
|---|---|---|
| Bir Mac ya da Windows bilgisayar | — | — |
| **Ücretli bir Claude üyeliği** (Pro, Max, Team ya da Enterprise) | HRVault, Claude uygulamasının "Code" bölümünde çalışır; ücretsiz üyelikte bu bölüm açılmaz | Aylık abonelik |
| Claude masaüstü uygulaması | HRVault'la burada konuşacaksın | Ücretsiz indirilir |
| Python | HRVault'un ilanları taramak için kullandığı program | Ücretsiz |
| Google Chrome | CV'ni PDF'e çevirmek için | Ücretsiz |
| LinkedIn profilin | Koç seni tanımak için okur | — |

> **Windows hakkında dürüst bir not:** HRVault şimdiye kadar Mac'te kullanıldı. Windows'ta çalışması beklenir, ama henüz
> denenmedi. Bir şey takılırsa Claude'a ne gördüğünü yaz; çoğu zaman kendisi çözer.

Kurulum yaklaşık **20–30 dakika** sürer. Kariyer koçuyla ilk sohbet de yaklaşık **1 saat**.

---

### Kurulum: adım adım

#### 1. Claude masaüstü uygulamasını kur

1. **claude.ai/download** adresine git.
2. Bilgisayarına uygun olanı (Mac ya da Windows) indir ve kur.
3. Uygulamayı aç ve Claude hesabınla giriş yap.
4. Sol taraftaki menünün en üstünde **Code** yazan bölüme tıkla. Burası, Claude'un bilgisayarındaki bir klasörle
   çalışabildiği bölümdür; HRVault burada çalışır.
   - **Upgrade** (yükselt) gibi bir uyarı görürsen hesabın ücretsiz demektir. Ücretli bir plana geçmen gerekir.

#### 2. Python'u kur

Python, HRVault'un ilanları taramak için kullandığı ücretsiz bir programdır. Bir kez kurarsın, sonra unutursun.

1. **python.org/downloads** adresine git.
2. Sarı **Download Python** düğmesine bas ve indirdiğin dosyayı aç.
3. Kurulum ekranındaki adımları izle.
   - **Windows'ta önemli:** ilk ekranın en altındaki **"Add python.exe to PATH"** kutusunu işaretle
     (bu, diğer programların Python'u bulabilmesini sağlar), sonra **Install Now**'a bas.
   - **Mac'te:** sonraki ekranlarda **Continue** (Devam), lisans için **Agree** (Kabul ediyorum) ve **Install** (Yükle)'ye bas.
     Mac bilgisayarının giriş şifresini sorar; bu normaldir, kendi şifreni yaz.
4. Kurulum bitince pencereyi kapat. Ekranda başka bir şey olmaz; doğru kurulduğunu 7. adımda Claude kontrol edecek.

> Mac'te bir gün "komut satırı geliştirici araçlarını yüklemek ister misiniz?" diye bir pencere çıkarsa **Yükle**'ye bas.
> Bu da Python için gereken ücretsiz bir parçadır.

#### 3. Google Chrome'u kur (yoksa)

Bilgisayarında Chrome yoksa **google.com/chrome** adresinden kur. HRVault CV'ni PDF'e çevirirken onu kullanır.
Windows'ta Microsoft Edge de iş görür.

#### 4. HRVault'u indir

HRVault'un dosyaları **GitHub**'da duruyor. GitHub, programların dosyalarının saklandığı bir web sitesidir.
İndirmek için hesap açman gerekmez.

1. Sana verilen **HRVault GitHub linkini** aç.
2. Sayfadaki yeşil **`<> Code`** düğmesine tıkla.
3. Açılan menüden **Download ZIP**'i seç. Tek bir dosya iner (ZIP, içinde bir klasör taşıyan sıkıştırılmış bir dosyadır).
4. İndirdiğin ZIP dosyasını aç:
   - **Mac:** dosyaya çift tıkla. Yanında bir klasör belirir.
   - **Windows:** dosyaya sağ tıkla → **Tümünü Ayıkla** (Extract All) → **Ayıkla**.
5. Ortaya çıkan klasörü kolay bulacağın bir yere taşı, örneğin **Belgeler**.
   Klasörün adı `HRVault-main` gibi bir şey olabilir; istersen adını `HRVault` yap.

> **Doğru klasör hangisi?** İçini açtığında `README.md` dosyasını ve `engine` klasörünü gördüğün klasör.
> Windows bazen iç içe iki klasör yapar (`HRVault-main` içinde yine `HRVault-main`). O zaman içteki klasörü kullan.

> Dosyaları tek tek kopyalama; klasörü bütün olarak taşı. İçinde normalde görünmeyen birkaç dosya var; bu normal.

#### 5. HRVault'u Claude'da aç

1. Claude uygulamasında **Code** bölümündesin.
2. Mesaj yazdığın kutunun hemen altında küçük seçim düğmeleri var. İlki, Claude'un nerede çalışacağını seçer:
   ona tıkla ve **Local** başlığının altındaki ilk seçeneği seç ("bu bilgisayarda" demektir).
3. Yanındaki klasör düğmesine tıkla → **Open folder…** → 4. adımda taşıdığın **HRVault** klasörünü seç.
4. Artık Claude bu klasörde çalışıyor.

#### 6. Claude izin istediğinde ne yapacaksın?

Bir sonraki adımdan itibaren Claude bazen bir şey yapmadan önce senden izin ister: bir kontrol çalıştırmak,
bir dosya yazmak, bir web sayfasını açmak gibi. Ekranda ne yapmak istediğini gösteren bir kutu ve onay düğmeleri çıkar.

Örneğin şuna benzer bir şey görürsün:

> `python3 engine/pipeline/profile.py doctor`

Bu karmaşık görünür ama anlamı basit: "HRVault'un kendi programlarından birini çalıştırayım mı?"
**`engine/` ile başlayan komutlar HRVault'un kendi parçalarıdır; onaylamak normaldir.**

Dikkat etmen gereken durumlar:

- Bir şeyi **silmek**, HRVault klasörünün **dışındaki** dosyalara dokunmak ya da **ödeme** yapmak isterse onaylamadan önce
  "Bu ne işe yarıyor?" diye sor. Claude açıklar.
- Mesaj kutusunun altındaki seçim düğmelerinden biri çalışma modudur. **Manual** olarak kalsın: böylece her adımı görür ve onaylarsın.

#### 7. Kurulumu kontrol ettir

Mesaj kutusuna şunu yaz ve Enter'a bas:

> **Kurulumumu kontrol et**

Claude bir kontrol çalıştırır (izin isterse onayla) ve neyin hazır, neyin eksik olduğunu söyler.
Eksik bir şey varsa nasıl düzelteceğini anlatır.

---

### İlk gün: kariyer koçuyla tanış

Mesaj kutusuna **/** yaz. Açılan listeden **coach**'u seç ve Enter'a bas.
(Listeyi göremezsen "Kariyer koçuyla başlayalım" yazman da yeter.)

Koç seninle sohbet eder. Aceleye gerek yok; bölüm bölüm ilerler, ara verirsen kaldığın yerden devam eder.

1. **Tanışma.** Önce LinkedIn profilini ister. En kolay yol şu:
   LinkedIn'de kendi profiline git → profil fotoğrafının altındaki **Daha fazla** (More) ya da **Kaynaklar** (Resources)
   düğmesi → **PDF olarak kaydet** (Save to PDF). İndirdiğin PDF'i Claude'daki mesaj kutusuna sürükleyip bırak.
   Sonra seninle konuşur: neyi iyi yaparsın, nelerden çekinirsin, hayalindeki iş ne, nasıl çalışmak istersin
   (tam zamanlı, yarı zamanlı, serbest; evden ya da ofisten), nerede yaşıyorsun, nerede çalışma iznin var.
2. **Kanıt.** Güçlü yanlarını somut örneklerle eşleştirir. Uydurma yok: yalnızca gerçekten yaptığın şeyler.
3. **Analiz.** Sana dürüst bir kariyer analizi yazar: güçlü yanların, eksiklerin, hangi işlere ulaşabileceğin.
4. **İş tanımları.** 3–6 iş türü önerir. Her birini **onaylar, değiştirir ya da reddedersin.**
   Onaylamadığın hiçbir iş türü aranmaz.
5. **Tamamlama.** Son birkaç soru: hangi dillerde yazılmış ilanlara bakılsın, CV'n hangi dilde olsun,
   başvuru formlarında sık sorulanlar (ne zaman başlayabilirsin, ücret beklentin…).

#### Panelini aç

Kurulum sırasında istediğin zaman şunu yaz:

> **Paneli aç**

Tarayıcında bir sayfa açılır. En üstte kurulumun hangi aşamada olduğunu ve sıradaki adımı görürsün.
Sonra bu sayfa ilanlarınla, başvurularınla ve sonuçlarla dolar. Sayfa yalnızca senin bilgisayarında durur.

---

### Her gün: nasıl kullanılır?

Her şeyi Claude'a normal cümlelerle söylersin. Bazı örnekler:

| Ne istiyorsun | Claude'a ne yazarsın |
|---|---|
| Yeni ilanlara bakmak | **Bugünkü ilanları tara** |
| Listeyi görmek | **Bugünkü listeyi göster** ya da **Paneli aç** |
| Seçim yapmak | **1 ve 3'e başvur, 2'yi reddet: çok kıdemli** |
| Başvurmak | **Onaylananlara başvur** |
| Durumu görmek | **Başvurularım ne durumda?** |
| Sonuç bildirmek | **X şirketinden ret geldi** · **Y şirketi mülakata çağırdı** |
| Aramayı değiştirmek | **Şimdilik yalnızca serbest çalışma (freelance) işlerine bak** |
| Bir şirketi takip etmek | **Şu şirketi takip et:** ve şirketin kariyer sayfası linki |
| Yedek almak | **Yedek al** |

#### Bir ilanı neden reddettiğini söyle

"2'yi reddet" yerine "2'yi reddet: maaşı düşük" dersen HRVault öğrenir ve sana benzer ilanları daha az gösterir.

#### Başvuru nasıl olur?

1. Seçtiğin ilan için Claude o ilana özel bir CV hazırlar ve sana gösterir.
2. CV'nin ilanla ne kadar uyuştuğunu ölçer. Uyum **%90'ın altındaysa başvuru yapılmaz.** Bu kural değişmez.
   Claude sana neyin eksik olduğunu söyler; o konuda gerçekten deneyimin varsa anlatırsın, CV'ye eklenir.
   Deneyimin yoksa eklenmez. Böylece CV'n hiç gerçek dışı bir şey söylemez.
3. Claude formu doldurur ya da sana neyi nereye yazacağını gösterir.
4. **Gönder demeden önce her şeyi sana gösterir.** Sen onaylarsın.
5. LinkedIn'deki başvurularda son "Gönder" tıklamasını sen yaparsın.

---

### Verin ve gizliliğin

- HRVault'un senin hakkında yazdığı her şey (profilin, CV'lerin, başvuru kayıtların) bilgisayarında, HRVault klasörünün
  içindeki **`me`** klasöründe durur. HRVault bu dosyaları başka bir yere göndermez.
- Claude'la konuştukların ve ona verdiğin dosyalar (örneğin LinkedIn PDF'in), Claude'la yaptığın her sohbet gibi
  Claude tarafından işlenir. Başvuru formlarına yazılanlar da, sen onayladığında, o şirkete gider.
- **HRVault klasörünü kimseyle paylaşma**, çünkü içinde kişisel bilgilerin var.
- HRVault'u bir arkadaşına vermek istersen Claude'a **"HRVault'umu paylaşmak istiyorum"** de.
  Senin bilgilerin çıkarılmış temiz bir kopya hazırlar.
- Ayda bir **"Yedek al"** de. HRVault klasörünün yanına tarihli bir yedek koyar.
  İstersen bu yedeği iCloud, Google Drive ya da Dropbox'a da kopyalayabilirsin; o zaman orada da durur.

---

### Takılırsan

**Code bölümü açılmıyor ya da "Upgrade" diyor.**
Claude hesabın ücretsiz. HRVault ücretli bir plan gerektirir.

**Claude "Python bulunamadı" ya da "python3: command not found" diyor.**
Kurulumdaki 2. adımı yap. Windows'ta "Add python.exe to PATH" kutusunu işaretlediğinden emin ol, sonra Claude uygulamasını
kapatıp yeniden aç.

**CV PDF'i oluşmuyor.**
Google Chrome'u kur (3. adım) ve Claude'a "PDF'i yeniden oluştur" de.

**Çok az ilan çıkıyor.**
Bu normal olabilir: HRVault yalnızca sana gerçekten uyan ilanları gösterir. Claude'a **"Neden az ilan çıktı?"** diye sor.
Sana hangi kuralların en çok ilan elediğini söyler (dil, konum, ücret…). Bir kuralı gevşetmek istersen söylemen yeter.

**Claude izin istiyor ve ne olduğunu anlamıyorum.**
6. adıma bak. Emin değilsen onaylama, "Bu ne işe yarıyor?" diye sor.

**Bir hata mesajı gördüm.**
Mesajı kopyala, Claude'a yapıştır ve "bu ne demek?" diye sor.

---

### HRVault'u güncellemek

Yeni bir sürüm çıktığında:

1. Yeni sürümü 4. adımdaki gibi indir ve aç.
2. **Eski** HRVault klasörünün içindeki **`me`** klasörünü, **yeni** HRVault klasörünün içine kopyala.
   Yeni klasörde zaten bir `me` klasörü varsa (boş bir şablondur), bilgisayar sorduğunda **Değiştir** (Replace) seç.
   **"İkisini de sakla"** (Keep both) seçme.
3. Claude'da yeni klasörü aç (5. adım).
4. Her şey düzgün görünüyorsa eski klasörü silebilirsin. Emin değilsen bir süre sakla.

`me` klasörün senin bütün geçmişin; güncellerken onu taşımayı unutma.

---

<a name="english"></a>

## English guide

This guide is for someone who happily uses a computer for email, documents and the web, but has never opened a
"terminal" or written code. You will not type any commands. You will move forward by chatting with Claude.

---

### What does HRVault do?

HRVault is an assistant that looks for jobs for you.

- It scans job postings online and filters out the ones that don't fit you.
- It scores the rest and shows you a short list every day.
- For the jobs you pick, it writes a CV tailored to that posting.
- It prepares your application. **It never sends an application until you say "send".**
- It keeps track of where you applied, when, and what happened.

#### What it doesn't do

- It doesn't type your passwords or solve "I'm not a robot" checks. You do those.
- It doesn't apply for you on LinkedIn. It prepares everything; you make the final click.
- It never makes things up about you. Your CV only says what you have really done.

> **A note on language:** HRVault's built-in instructions are written in Turkish. If Claude answers you in Turkish,
> just write **"Please talk to me in English"**. It will switch, and your CVs will be in the language you choose.

---

### What you need before you start

| What | Why | Cost |
|---|---|---|
| A Mac or Windows computer | — | — |
| **A paid Claude plan** (Pro, Max, Team or Enterprise) | HRVault runs in the Claude app's "Code" section, which isn't available on the free plan | Monthly subscription |
| The Claude desktop app | This is where you'll talk to HRVault | Free download |
| Python | The program HRVault uses to scan job postings | Free |
| Google Chrome | To turn your CV into a PDF | Free |
| Your LinkedIn profile | The coach reads it to get to know you | — |

> **An honest note about Windows:** so far HRVault has been used on a Mac. It should work on Windows, but it hasn't been
> tested there yet. If something gets stuck, tell Claude what you see; it can usually fix it.

Setup takes about **20–30 minutes**. Your first conversation with the career coach takes about **an hour**.

---

### Setup, step by step

#### 1. Install the Claude desktop app

1. Go to **claude.ai/download**.
2. Download the version for your computer (Mac or Windows) and install it.
3. Open the app and sign in with your Claude account.
4. Click **Code** at the top of the menu on the left. This is the part of Claude that can work with a folder on your
   computer; HRVault runs here.
   - If you see an **Upgrade** message, your account is on the free plan. You'll need a paid plan.

#### 2. Install Python

Python is a free program HRVault uses to scan job postings. You install it once and forget about it.

1. Go to **python.org/downloads**.
2. Click the yellow **Download Python** button and open the file you downloaded.
3. Follow the installer.
   - **On Windows, this matters:** on the first screen, tick **"Add python.exe to PATH"** at the bottom
     (this lets other programs find Python), then click **Install Now**.
   - **On a Mac:** click **Continue**, then **Agree** for the license, then **Install**.
     Your Mac asks for its login password; that's normal, type your own password.
4. When it's done, close the window. Nothing else appears on screen; Claude will confirm it worked in step 7.

> If your Mac ever asks "Would you like to install the command line developer tools?", click **Install**.
> It's a free piece that Python needs.

#### 3. Install Google Chrome (if you don't have it)

If you don't have Chrome, install it from **google.com/chrome**. HRVault uses it to turn your CV into a PDF.
On Windows, Microsoft Edge works too.

#### 4. Download HRVault

HRVault's files live on **GitHub**, a website where programs' files are stored. You don't need an account to download.

1. Open the **HRVault GitHub link** you were given.
2. Click the green **`<> Code`** button on the page.
3. Choose **Download ZIP** from the menu. A single file downloads (a ZIP is a compressed file with a folder inside).
4. Open the ZIP file you downloaded:
   - **Mac:** double-click it. A folder appears next to it.
   - **Windows:** right-click it → **Extract All** → **Extract**.
5. Move the folder that appears somewhere easy to find, such as **Documents**.
   It may be called something like `HRVault-main`; you can rename it to `HRVault` if you like.

> **Which folder is the right one?** The one where, when you open it, you see the `README.md` file
> and the `engine` folder. Windows sometimes creates a folder inside a folder (`HRVault-main` inside `HRVault-main`).
> If so, use the inner one.

> Don't copy the files one by one; move the whole folder. It contains a few files that are normally invisible; that's normal.

#### 5. Open HRVault in Claude

1. In the Claude app, you're in the **Code** section.
2. Right under the box where you type messages there are small selector buttons. The first one chooses where Claude works:
   click it and choose the first option under **Local** (it means "on this computer").
3. Click the folder button next to it → **Open folder…** → choose the **HRVault** folder you moved in step 4.
4. Claude is now working in that folder.

#### 6. What to do when Claude asks for permission

From the next step on, Claude sometimes asks before it does something, like running a check, writing a file or
opening a web page. A box appears showing what it wants to do, with buttons to approve or decline.

For example, you might see something like:

> `python3 engine/pipeline/profile.py doctor`

It looks complicated, but it simply means: "May I run one of HRVault's own programs?"
**Commands that start with `engine/` are part of HRVault itself; approving them is normal.**

Be careful in these cases:

- If it wants to **delete** something, touch files **outside** the HRVault folder, or make a **payment**,
  ask "What does this do?" before approving. Claude will explain.
- One of the selector buttons under the message box is the working mode. Keep it on **Manual**: that way you see and
  approve every step.

#### 7. Let Claude check your setup

Type this in the message box and press Enter:

> **Check my setup**

Claude runs a check (approve it if asked) and tells you what's ready and what's missing.
If something is missing, it explains how to fix it.

---

### Day one: meet your career coach

Type **/** in the message box. Pick **coach** from the list and press Enter.
(If you don't see the list, writing "Let's start with the career coach" works too.)

The coach has a conversation with you. There's no rush; it goes section by section, and if you take a break it
picks up where you left off.

1. **Getting to know you.** First it asks for your LinkedIn profile. The easiest way:
   go to your own LinkedIn profile → the **More** or **Resources** button under your photo → **Save to PDF**.
   Drag the PDF you downloaded into the message box in Claude.
   Then it talks with you: what you're good at, what worries you, your dream job, how you want to work
   (full-time, part-time, freelance; from home or in an office), where you live, and where you're allowed to work.
2. **Evidence.** It matches your strengths to concrete examples. Nothing is invented: only things you have really done.
3. **Analysis.** It writes you an honest career analysis: your strengths, your gaps, which jobs are within reach.
4. **Job definitions.** It suggests 3–6 kinds of jobs. You **approve, change or reject** each one.
   Nothing you haven't approved is searched for.
5. **Finishing up.** A few last questions: which languages job postings should be in, which language your CV should be in,
   and the questions application forms often ask (when you can start, your expected pay…).

#### Open your dashboard

At any point during setup, write:

> **Open the dashboard**

A page opens in your browser. At the top you'll see which setup stage you're at and what comes next.
Later this page fills up with your jobs, applications and results. The page stays only on your computer.

---

### Every day: how to use it

You tell Claude everything in normal sentences. Some examples:

| What you want | What you write to Claude |
|---|---|
| Look at new jobs | **Scan today's jobs** |
| See the list | **Show today's list** or **Open the dashboard** |
| Make your picks | **Apply to 1 and 3, reject 2: too senior** |
| Apply | **Apply to the approved ones** |
| Check progress | **How are my applications doing?** |
| Report a result | **Company X rejected me** · **Company Y invited me to an interview** |
| Change the search | **For now, only look at freelance jobs** |
| Follow a company | **Follow this company:** plus a link to its careers page |
| Make a backup | **Make a backup** |

#### Say why you reject a job

Instead of "reject 2", say "reject 2: pay is too low". HRVault learns and shows you fewer jobs like it.

#### How an application works

1. For the job you picked, Claude writes a CV tailored to that posting and shows it to you.
2. It measures how well the CV matches the posting. **If the match is below 90%, it won't apply.** This rule never changes.
   Claude tells you what's missing. If you really have experience with it, tell Claude and it goes into your CV.
   If you don't, it stays out. That way your CV never says anything untrue.
3. Claude fills in the form, or shows you what to put where.
4. **It shows you everything before sending.** You approve.
5. For LinkedIn applications, you make the final "Submit" click yourself.

---

### Your data and privacy

- Everything HRVault writes about you (your profile, CVs, application records) is kept on your computer, in the
  **`me`** folder inside the HRVault folder. HRVault doesn't send these files anywhere else.
- What you discuss with Claude and the files you give it (for example your LinkedIn PDF) are processed by Claude,
  like any chat with Claude. What goes into an application form is sent to that company, once you approve it.
- **Don't share your HRVault folder with anyone**: it contains your personal information.
- If you want to give HRVault to a friend, tell Claude **"I want to share my HRVault"**.
  It prepares a clean copy with your information removed.
- Once a month, say **"Make a backup"**. It puts a dated backup next to your HRVault folder.
  You can also copy that backup to iCloud, Google Drive or Dropbox; then it's stored there too.

---

### If you get stuck

**The Code section won't open, or it says "Upgrade".**
Your Claude account is on the free plan. HRVault needs a paid plan.

**Claude says "Python not found" or "python3: command not found".**
Do step 2 of the setup. On Windows, make sure you ticked "Add python.exe to PATH", then close and reopen the Claude app.

**The CV PDF isn't created.**
Install Google Chrome (step 3) and tell Claude "create the PDF again".

**Very few jobs show up.**
That can be normal: HRVault only shows jobs that really fit you. Ask Claude **"Why did so few jobs show up?"**
It tells you which rules filter out the most jobs (language, location, pay…). If you want to loosen one, just say so.

**Claude is asking for permission and I don't understand what it is.**
See step 6. If you're not sure, don't approve it; ask "What does this do?"

**I saw an error message.**
Copy the message, paste it to Claude and ask "what does this mean?"

---

### Updating HRVault

When a new version comes out:

1. Download and open the new version as in step 4.
2. Copy the **`me`** folder from inside your **old** HRVault folder into your **new** HRVault folder.
   If the new folder already has a `me` folder (it's an empty template), choose **Replace** when your computer asks.
   Don't choose **Keep both**.
3. Open the new folder in Claude (step 5).
4. If everything looks right, you can delete the old folder. If you're not sure, keep it for a while.

Your `me` folder is your whole history. Don't forget to move it when you update.

---

**Teknik ayrıntılar / Technical details:** [TEKNIK.md](TEKNIK.md) · [DESIGN.md](DESIGN.md)
