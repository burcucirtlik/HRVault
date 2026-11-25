---
# Limitler
günlük_başvuru_limiti: 10          # tüm worker'lar toplamı (apply uygular)
min_uygunluk_puanı: 60             # altındakiler onay listesine gelmez
onay_listesi_üst_sınır: 20         # günlük listede en fazla kaç ilan

# Kara liste
kara_liste:
  şirketler: []                    # mevcut işveren dahil
  sektörler: []                    # score skill'i ilan metninden değerlendirir
  anahtar_kelimeler: []            # başlıkta veya metinde geçerse elenir

# Worker varsayılanları — worker dosyasında olmayan alan buradan alınır; worker'daki değer kazanır.
# `ortak_hariç_başlık` worker'ın kendi hariç listesine eklenir (birleşim).
worker_varsayılanları:
  yer: []
  ülkeler: []
  kaynaklar: [remotive, remoteok, weworkremotely, himalayas, greenhouse, lever, ashby, linkedin]   # küresel kaynaklar; bölgeye özgü olanları coach konumuna göre ekler
  ilan_dilleri: []                 # hangi dillerde yazılmış ilanlar aransın, ör. [en, tr]; coach sorar, boşken tarama başlamaz
  günlük_limit: 5
  ortak_hariç_başlık: []
  kısmi_remote:                 # isteğe bağlı istisna: yer [remote] iken kısmen yerinde çalışmayı kabul et
    tipler: []                  # ör. [freelance]
    min_remote_yüzde:           # ör. 80
    şehirler: []                # yerinde kısmın kabul edildiği şehirler

# Onay ve bildirim
onay_kanalı: markdown              # markdown | slack | notion | email
tarama_saati: "09:00"

# Belgeler
cv_dili: []                        # CV hangi dillerde hazırlanabilir, ör. [en, tr]; ilanın diline göre seçilir (coach sorar)
cv_formatı: pdf                    # pdf | docx (site istisnaları knowledge/ats.md'de)
ön_yazı: gerekirse                 # her_zaman | gerekirse | asla
---
# Tercihler

Tüm worker'lar için geçerli genel kurallar. Değerler yukarıdaki bloğun içinde;
worker'a özel filtreler `me/workers/` dosyalarında.

Bu dosyayı elle düzenleyebilir ya da Claude'a söyleyebilirsin
("Acme'yi kara listeye ekle", "minimum puanı 70 yap").
