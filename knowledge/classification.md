# İlan sınıflandırma

> scan ilan etiketine güvenmez; metni okuyup bu kurallarla çalışma tipi, yer ve saati çıkarır.
> Emin olamazsa ilanı "belirsiz" işaretler.

## Çalışma tipi
- **"Contract-to-hire" full-time adayıdır** `k:classification-contract-to-hire-full-time-adayidir`
  Deneme süreli contract, sonunda kadro hedefleniyor. Freelance worker'ına değil,
  full-time worker'ına (veya ikisine birden, belirsiz işaretle) eşle.
  _dayanak: genel bilgi · güven: orta_
- **Saat sayısı tipi belirler** `k:classification-saat-sayisi-tipi-belirler`
  "Full-time" etiketli ama metinde "20 hours/week" geçiyorsa part-time say.
  _dayanak: genel bilgi · güven: orta_

## Yer
- **"Remote" ≠ her yerden** `k:classification-remote-her-yerden`
  "Remote (US only)", "Remote within EU", "must be based in…" ifadeleri ülke kısıtıdır;
  worker'ın `ülkeler` alanıyla karşılaştır.
  _dayanak: genel bilgi · güven: yüksek_
- **Gizli hibrit** `k:classification-gizli-hibrit`
  "Remote" etiketli ilanlarda "X days in office", "occasional travel to HQ" geçebilir;
  hibrit say ve uyarıya yaz.
  _dayanak: genel bilgi · güven: yüksek_

## Zaman dilimi
- **Çakışma şartı** `k:classification-cakisma-sarti`
  "Must overlap with EST hours" gibi şartlar varsa kişinin `timezone` ve
  `overlap_hours` alanıyla kontrol et.
  _dayanak: genel bilgi · güven: yüksek_

## Öğrenimler
- **Etiket "Full-Time", metin part-time** `k:classification-etiket-full-time-metin-part-time`
  Akış sitelerinde (ör. WWR `type` alanı) etiket varsayılan "Full-Time" kalabiliyor; "10-20 hours per week"
  gibi saat ifadesi varsa part-time say.
  _dayanak: ilk tarama · güven: orta_
- **"Independent contractor" = freelance** `k:classification-independent-contractor-freelance`
  Görev/saat başı ödemeli, "independent contractor basis" ifadeli ilanlar freelance/contract sayılır.
  _dayanak: ilk tarama · güven: orta_
- **Saatlik "part-time non-exempt" çalışan freelance değildir** `k:classification-saatlik-part-time-non-exempt-calisan`
  "Part-time, non-exempt, hourly employee" ifadeli ilanlar bordrolu çalışandır; freelance/contract worker'ına eşleme.
  İşverenin ülkesinde çalışma izni şartı da genellikle beraberinde gelir.
  _dayanak: ilk tarama (birkaç ilan) · güven: orta_
- **"Contractor" etiketi ülke kısıtını kaldırmaz** `k:classification-contractor-etiketi-ulke-kisitini-kaldirmaz`
  Contractor ilanlarının çoğu yine tek ülke/bölgeye kısıtlı ("North America only", "must be based in Canada").
  Ülke kısıtını her zaman metinden ve kaynağın konum alanından kontrol et.
  _dayanak: ilk tarama (birkaç ilan) · güven: orta_
- **Aday konumu: başlık değil, kaynağın konum alanı** `k:classification-aday-konumu-baslik-degil-kaynagin-konum`
  Akış kaynaklarında konum alanı adayın nerede olması gerektiğini söyler. Başlıktaki "Worldwide/Anywhere"
  ile çelişirse kısıtlayıcı olanı esas al; emin değilsen `belirsiz` işaretle, uygun sayma.
  _dayanak: tek hatalı öneri · güven: orta_
- **Hariç başlıklar tam kelime eşleşmeli** `k:classification-haric-basliklar-tam-kelime-eslesmeli`
  Başlık hariç listesi önek olarak eşleşirse "intern" → "Internal", "International" ilanlarını da eler (uygun bir ilan bu
  yüzden kaçtı). scan.py artık hariç listesini tam kelime (+ çoğul) olarak eşliyor; dahil listesi önek eşleşmeye devam ediyor.
  _dayanak: tek kaçan ilan · güven: orta_
