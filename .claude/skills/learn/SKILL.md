---
name: learn
description: Akış sırasında öğrenilenleri sınıflandırıp doğru yere yazar — genel öğrenimler knowledge/'a, kişiye dair öğrenimler me/learnings.md'ye. Bir site/form tuhaflığı, ret sebebi, mülakat sonucu veya kişi tercihi ortaya çıktığında; "bunu öğren", "bunu hatırla" isteklerinde kullan.
---
<!-- durum: çalışır -->
# learn

## Tek soru: "Bu, vault'u kullanan herkes için doğru mu?"

| Cevap | Nereye |
|---|---|
| Evet | `knowledge/<ilgili dosya>` — sites/, forms.md, ats.md, classification.md, scam-signals.md, writing.md |
| Hayır | `me/learnings.md` |
| Karışık | İkiye böl: genel kural → `knowledge/`, kişisel detay → `me/` |

## knowledge/'a yazmadan önce kontrol
Madde şunlardan birini içeriyorsa **genelleştir veya me/'ye taşı**:
isim, e-posta, telefon, adres, ücret/maaş rakamı, başvurulan şirket adı,
kişinin CV'sinden cümle, kişinin tercihi.

Örnek: "Acme'nin Greenhouse formu maaşı sadece rakam kabul ediyor"
→ `knowledge/sites/greenhouse.md`: "Bazı Greenhouse formlarında maaş alanı yalnızca rakam
kabul ediyor; para birimi ayrı seçiliyor."

Örneklerde yer tutucu kullan (`<Ülke>`, `<Şirket>`, `<rol>`). Kişinin ülkesi, aradığı rol, worker adı ve oturum
sayımları ("N aramada M ilan") tek tek zararsız görünür ama birlikte kişiyi tarif eder; kuralı taşıyan kısmı yaz, sayımı at.

## Yazdıktan hemen sonra: kapı
```bash
python3 engine/pipeline/export.py lint <yazdığın dosya>
```
- `engel` → maddeyi geri al; genel kısmı yeniden yaz, kişisel kısmı `me/learnings.md`'ye taşı.
- `gözden_geçir` → genelleştir. Genelleştirince kural anlamını yitiriyorsa kişiye sor; onaylarsa
  `export.py allow <dosya> <satır> --gerekce "…"`.
- Genel mi kişisel mi emin değilsen `knowledge/`'a yazma: `me/learnings.md → Genel adayı` başlığına yaz;
  export sırasında gözden geçirilir.
- `TARAMA YAPILAMADI` (profil henüz boş) → genel kurallar yine de uygulanır: `export.py lint --hook`.

## Format
`knowledge/README.md`'deki madde formatı: tarih, başlık, kalıcı kimlik (`k:` — `export.py ids` eksik olanları ekler),
`dayanak`, `güven`, gerekirse `kapsam` (yalnızca bir ülkede geçerliyse ülke kodu).

Var olan bir maddeyi destekleyen yeni veri gelirse yeni madde yazma; `dayanak` sayısını ve `güven`i güncelle.
**Devralınan madde** (`knowledge/.baseline.json`'da kimliği olan): devralınan dayanağa dokunma, kendi gözlemini
yanına ekle — `_dayanak: devralındı (1 form) + 2 form · güven: …_`. Güveni yalnızca kendi verin yükseltir.
Devralınan madde senin deneyiminle çelişiyorsa silme; altına yenisini yaz.
Maddenin `kapsam`ı kişinin durumuna uymuyorsa (başka ülke) o maddeyi uygulama.

## Ne zaman
apply her oturumun sonunda learn'i çalıştırır; ayrıca kişi "bunu öğren" dediğinde ve her tarama + puanlama
döngüsünden sonra (en az haftada bir) rapor için.

## Döngü: rapor → öneri → kişinin onayı → değişiklik
```bash
python3 engine/pipeline/learn.py rapor            # son 30 gün; --gün 0 = hepsi
```
Betik okur, hiçbir şey yazmaz; üç bölüm verir:
- **Verim:** rol kelimesi / kaynak / worker başına huni (betik → kaldı → listede → onay → başvuru → cevap).
  *Gürültü adayı* (çok ilan getiren, listeye hiç ilan sokmayan kelime) ve *hiç ilan getirmeyen rol*.
- **Tekrar eden eleme sebepleri** (3+), her birinin hangi kelimeden geldiği ve öneri.
- **Bekleyenler:** sebepsiz ret/iptal, öğrenime işlenmemiş sonuç (ret, mülakat, teklif), 30+ gündür cevapsız başvuru.

Ne yapılır:
1. Bekleyenler: sebepleri kişiye **tek soruda** sor ("geç" de kabul); sonuçları `me/learnings.md`'ye işle;
   sessiz adaylarını kişiye söyleyip `track.py set <klasör> sessiz`.
2. Gürültü, ölü rol, tekrar eden sebep: **öneri olarak** sun, en fazla 3 tane, her biri sayısıyla
   ("'<rol>' 42 ilan getirdi, hiçbiri listeye girmedi; 20'si alan uzmanlığı"). Rol çıkarma / ekleme / hariç_başlık /
   kara liste değişikliği kişi onaylarsa `mode` (worker) ya da `coach` (iş tanımı) ile yapılır; learn worker'a kendi yazmaz.
   Onaylanan ya da reddedilen her öneri `me/learnings.md → Tanım değişiklikleri`'ne tarihle yazılır: aynı öneri
   gerekçesiz tekrar sunulmaz.
3. Rapor başında "az tarama" uyarısı varsa rol çıkarma önerme; yalnızca gözlem olarak söyle.
4. Kalıp birden çok kişide geçerliyse (ör. bir başlık tipinin sistematik olarak başka bir iş türü çıkması) genel kuralı
   `knowledge/classification.md`'ye yaz; sayımları ve kişinin rollerini değil.

`track.py stats` başvuru sonrası tarafı verir: worker, uygunluk puanı bandı, ATS bandı ve kaynağa göre cevap oranı.

## Kaynaklar
- Onay listesinde `ret:` sebepleri → `python3 engine/pipeline/inbox.py log` (her ilanın geçerli kararı;
  `decisions.jsonl` yalnızca eklenir, aynı ilanın son satırı geçerlidir) → genelde `me/learnings.md`.
- İptal edilen başvurular: `application.md → iptal_sebebi`. `belirtilmedi` ise bir kez kişiye sor.
- `python3 engine/pipeline/track.py stats` → hangi worker / puan bandı / ATS bandı / kaynak cevap alıyor (yeterli veri olunca).
  Aynı sebep 3+ kez tekrar ederse (`learn.py elemeler` sayar) worker filtresine ya da kara listeye eklemeyi kişiye öner.
  Bir iş tanımının ilanları sürekli elenir ya da reddedilirse coach'a "tanımları gözden geçir" öner.
- apply'da form tuhaflıkları → `knowledge/sites/`, `knowledge/forms.md`.
- track'ten mülakat/ret sonuçları → kişiye özel olanlar `me/`, birden çok kişide tekrar
  edebilecek kalıplar `knowledge/writing.md`.
