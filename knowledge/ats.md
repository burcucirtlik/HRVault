# ATS kuralları

> tailor'ın ATS simülasyonu bu kurallara göre çalışır.

## Başlangıç kuralları
- **Tek sütun, standart başlıklar** `k:ats-tek-sutun-standart-basliklar`
  ATS'ler çok sütunlu düzeni, tabloları, metin kutularını ve ikonları sıklıkla yanlış
  ayrıştırır. CV tek sütun; başlıklar "Experience", "Education", "Skills" gibi standart.
  _dayanak: genel bilgi · güven: yüksek_
- **Anahtar kelime ilandaki haliyle** `k:ats-anahtar-kelime-ilandaki-haliyle`
  İlan "PostgreSQL" diyorsa CV'de "Postgres" yerine "PostgreSQL" kullan; kısaltmayı
  bir kez açık haliyle yaz. Yalnızca kanıt bankasında dayanağı olan kelimeler.
  _dayanak: genel bilgi · güven: yüksek_
- **Bilgi header/footer'da olmasın** `k:ats-bilgi-header-footer-da-olmasin`
  İletişim bilgisi sayfa başlığına/altlığına konursa bazı ATS'ler okumaz; gövdeye yaz.
  _dayanak: genel bilgi · güven: orta_
- **Metin tabanlı PDF** `k:ats-metin-tabanli-pdf`
  Taranmış / görsel PDF ayrıştırılamaz. Metin seçilebilir PDF veya DOCX kullan.
  _dayanak: genel bilgi · güven: yüksek_

## Site / ATS bazlı istisnalar

## Öğrenimler
- **Uygunluk puanı ATS ölçümünün yerini tutmaz** `k:ats-uygunluk-puani-ats-olcumunun-yerini-tutmaz`
  Rolün kişiye uyması, CV'nin ilanda bunu gösterdiği anlamına gelmez: yüksek uygunluk puanlı bir başvuru, ölçülmeden
  gönderilmiş ve sonradan ölçüldüğünde zorunlu kelimelerin yarısı CV'de çıkmamıştı. Her gönderimden önce
  `ats.py --gate` çalışır; ölçüm yoksa ya da puan %90'ın altındaysa gönderim yapılmaz (sabit kural).
  _dayanak: tek ret · güven: orta_
- **İlanın birincil şartı CV'de adıyla geçmeli** `k:ats-ilanin-birincil-sarti-cv-de-adiyla-gecmeli`
  İlanın ilk zorunlu şartı bir araç ya da teknoloji adıysa (ör. "practitioner-level <araç> fluency") ve kişide kanıtı
  varsa, o ad CV'de aynen geçmeli; ATS de insan okuyucu da önce ona bakar. Kanıt bankasında yoksa CV'yi bitirmeden
  kişiye sor. ats.py'ye `--required` listesinin ilk terimi olarak verilir.
  _dayanak: tek ret · güven: orta_
