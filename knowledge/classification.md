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
- **Rol kalıbı ne çok özel ne çok genel olmalı** `k:classification-rol-kalibi-ne-cok-ozel-ne-cok-genel`
  Başlık eşleşmesi kalıbın tüm kelimelerini sırasız arar. Üç kelimelik çok özel kalıplar ("<sıfat> <alan> <unvan>") gerçek başlıklarla
  nadiren birebir tutar ve uygun ilanlar görünmez; iki kelimelik çekirdek ("<alan> <unvan>") aynı ilanların hepsini yakalar. Öte yandan
  genel bir çift ("<teknoloji> specialist") kelimeleri ayrı yerlerde geçen ilgisiz başlıkları da getirir ("<konu> Specialist – <teknoloji> … Project");
  bunlar hariç başlıkla kapatılır. Kalıpları değiştirmeden önce geniş bir örneklemde ölç: ne eklenir, ne düşer.
  _dayanak: tek örneklem karşılaştırması · güven: orta_
- **İlan dili ve kara liste betikte elenir** `k:classification-ilan-dili-ve-kara-liste-betikte-elenir`
  scan.py, rolle eşleşen ilanın yazıldığı dili metinden çıkarır; worker'ın `ilan_dilleri` listesinde yoksa ilanı düşürür (özette `dil_dışı`),
  kara listedeki şirketleri de eşleşmeden önce atar (`kara_liste`). Kısa özetlerde ve iki dilli ilanlarda tahmin etmez; onlar sınıflandırmaya gelir.
  İlanın *istediği* dil (ör. İngilizce ilanda başka bir dilde akıcılık şartı) hâlâ metinden okunarak elenir.
  _dayanak: tek örneklem · güven: orta_
- **Kariyer sayfası konumu: izinli yer yoksa ele** `k:classification-kariyer-sayfasi-konumu-izinli-yer-yoksa-ele`
  ATS konum alanı çoğunlukla ofis şehridir ve ülke adı yazmayabilir ("San Francisco, California", "Seattle; Remote"). Kısıtlayıcı
  ülke listesi bu şehirleri yakalamaz. Güvenilir kural tersidir: konum worker'ın izinli yerlerinden birini (ya da onu kapsayan bölgeyi)
  anıyorsa ya da yalnızca açık bir ifadeyse ("Remote", "Home based – Worldwide") geç; başka bir yer adı varsa ele. "Remote – <şehir>"
  o şehre/ülkeye bağlı remote demektir. scan.py bu kuralı uygular.
  _dayanak: tek tarama, çok sayıda ilan · güven: orta_
- **Yer yazmayan freelance ilanı elenmez** `k:classification-yer-yazmayan-freelance-ilani-elenmez`
  Proje bazlı freelance ilanlar çoğu zaman çalışma yerini yazmaz. Ofis ya da hibrit şartı yalnızca metinde açıkça varsa ele;
  yoksa `yer: belirsiz` işaretle, sınıflandırmadan geçir ve uyarıya "yer belirtilmemiş, teyit et" yaz. Freelance platformlarındaki
  "%<n> remote" ifadesi kısmi yerinde çalışma demektir: worker yalnızca remote istiyorsa hibrit say. Worker'da `kısmi_remote`
  istisnası varsa (tip, en düşük remote oranı, şehir) üç koşul birden sağlanınca geçir. Kabaca: %80 remote ≈ haftada 1 gün,
  %85 ≈ ayda 3 gün yerinde (tam zamanlı proje varsayımıyla).
  _dayanak: tek tarama · güven: orta_

