# Web Platform Kullanim Kilavuzu

Emlak Teknoloji Platformu'nun web paneli, gayrimenkul ofislerinizin tum is sureclerini tek bir arayuzden yonetmenizi saglar. Bu kilavuz, platformdaki her modulu detayli olarak aciklamaktadir.

---

## Genel Bakis

Platforma giris yaptiginizda sol taraftaki gezinti cubugu (sidebar) uzerinden tum modullere erisebilirsiniz:

| Modul | Simge | Aciklama |
|-------|-------|----------|
| Dashboard | LayoutDashboard | Ana sayfa ve genel ozet |
| Mulkler | Building2 | Portfoy yonetimi |
| Ilan Asistani | FileText | AI destekli ilan olusturma |
| Musteriler | Users | CRM — musteri iliskileri yonetimi |
| Degerleme | Calculator | AI konut degerleme |
| Bolge Analizi | BarChart3 | Ilce bazli pazar analizi |
| Mesajlar | MessageSquare | Bildirim ve mesaj yonetimi |
| Harita | Map | Interaktif emlak haritasi |
| Ag (Vitrin) | Network | Portfolyo agi ve vitrin yonetimi |
| Kredi | Coins | Konut kredisi hesaplayici |
| Ayarlar | Settings | Hesap ve platform ayarlari |

---

## 1. Dashboard

**Yol:** `/dashboard`

Dashboard, platformdaki tum aktivitelerinizin ozetini sunar. Giris yaptiginizda ilk goreceg iniz ekran burasid ir.

### Ozet Kartlari

Ekranin ust kisminda dort ana metrik karti yer alir:

- **Toplam Portfolyo:** Ofisinizdeki toplam ilan sayisi ve bu ayki degisim.
- **Aktif Musteriler:** Kayitli musteri sayisi ve aylik artis.
- **Tahmini Deger:** Portfoyunuzdeki toplam tahmini gayrimenkul degeri.
- **Bekleyen Isler:** Tamamlanmayi bekleyen gorevler ve acil olanlar.

### Son Aktiviteler

Dashboard'un alt kisminda iki bolum bulunur:

- **Aktivite Grafigi:** Son donem islemlerinizin gorsel ozeti.
- **Yaklasan Randevular:** Planlanan musteri gorusmeleri ve randevular.

---

## 2. Degerleme

**Yol:** `/dashboard/valuations`

Yapay zeka destekli konut degerleme modulu. Istanbul genelinde 39 ilce icin anlik fiyat tahmini yapabilirsiniz.

### Yeni Degerleme

**"Yeni Degerleme"** sekmesinde degerleme formunu doldurun:

1. **Ilce** secin (Istanbul ilcelerinden biri).
2. **Net metrekare**, **oda sayisi**, **kat** ve **bina yasi** bilgilerini girin.
3. **Degerle** butonuna tiklayin.
4. Sonuc ekraninda tahmini fiyat araligi, ortalama deger ve guven orani goruntulenir.

### Gecmis Degerlemeler

**"Gecmis Degerlemeler"** sekmesinde daha once yaptiginiz tum degerleme sonuclarina ulasabilirsiniz. Her degerlemenin detay sayfasina giderek raporu PDF olarak indirebilirsiniz.

> **Not:** Degerleme modeli ~%90 dogruluk oranina sahiptir (MAPE: ~%10). Sonuclar bilgilendirme amaclidir.

---

## 3. Ilanlarim (Ilan Asistani)

**Yol:** `/dashboard/listings`

Ilan Asistani, yapay zeka destekli uc ana ozellik sunar:

### Metin Olustur

AI ile profesyonel ilan metni uretir:

1. Sol paneldeki formu doldurun (emlak bilgileri, konum, ozellikler).
2. **Olustur** butonuna tiklayin.
3. Sag panelde uretilen ilan metni goruntulenir.
4. **Yeniden Olustur** ile farkli bir versiyon alin veya **Ton Degistir** ile uslup ayarlayin.

### Virtual Staging

Bos oda fotograflarini yapay zeka ile mobilyali hale getirin:

1. **Virtual Staging** sekmesine gecin.
2. Bos oda fotografinizi yukleyin.
3. Mobilya tarzini secin (Modern, Klasik, Minimalist, Skandinav, Bohem, Endustriyel).
4. Islenmis fotografi indirin veya ilana ekleyin.

### Portal Export

Olusturdugunuz ilan metinlerini emlak portallerina aktarin:

1. **Portal Export** sekmesine gecin.
2. Daha once uretilmis ilan metnini secin.
3. Hedef portali belirleyin ve disa aktarin.

> **Kredi Sistemi:** Ilan Asistani kredi bazli calisir. Mevcut kredi bakiyeniz sag ust kosede goruntulenir.

---

## 4. Musteriler (CRM)

**Yol:** `/dashboard/customers`

Musteri iliskileri yonetim modulu. Tum musterilerinizi ve taleplerini tek bir yerden takip edin.

### Temel Ozellikler

- **Musteri Listesi:** Tum kayitli musterilerinizi goruntuleyin.
- **Musteri Tipleri:** Alici, Satici, Kiraci, Ev Sahibi olarak kategorize edin.
- **Talep Takibi:** Musteri taleplerini (butce, konum, ozellik) kaydedin.
- **Detay Sayfasi:** Her musterinin detay sayfasinda gecmis islemler ve iletisim gecmisi yer alir.

### Musteri Ekleme

1. **Yeni Musteri** butonuna tiklayin.
2. Ad, telefon, e-posta ve musteri tipini girin.
3. Opsiyonel olarak butce araligi ve tercih ettigi bolgeler ekleyin.
4. **Kaydet** ile islemi tamamlayin.

> **Telegram Entegrasyonu:** Telegram bot uzerinden `/musteri` komutuyla da hizli musteri kaydi olusturabilirsiniz.

---

## 5. Bolge Analizi

**Yol:** `/dashboard/areas`

Ilce bazli detayli pazar verileri, demografik yapi ve risk analizleri.

### Ilce Secimi

1. Acilis ekraninda **"Bir Bolge Secin"** mesaji gorursunuz.
2. Dropdown'dan Istanbul'un 39 ilcesinden birini secin.
3. Ilce seciminden sonra detayli analiz raporu yuklenir.

### Rapor Icerigi

Secilen ilce icin sunulan veriler:

- **Genel Bakis Karti:**
  - Nufus ve yogunluk
  - Ortalama satis fiyati (m² bazinda)
  - Ortalama kira fiyati
  - Son 6 aylik fiyat trendi
  - Yatirim skoru ve amortisman suresi

- **Fiyat Trend Grafigi:** Son 12 aylik m² fiyat degisim grafigi.

- **Deprem Risk Raporu:**
  - Risk skoru (1-10 arasi)
  - Risk seviyesi (dusuk / orta / yuksek)
  - Fay hatti mesafesi
  - Zemin sinifi
  - PGA (en yuksek yer ivmesi) degeri

### Karsilastirma

Birden fazla ilceyi kiyaslamak icin **"Karsilastir"** butonuna tiklayin. Karsilastirma sayfasinda sectiginiz ilcelerin verilerini yan yana gorebilirsiniz.

---

## 6. Harita

**Yol:** `/dashboard/maps`

Interaktif harita uzerinde tum emlak envanterinizi goruntuleyin.

### Harita Kullanimi

- Harita Istanbul merkezli olarak yuklenir (MapLibre GL tabanli).
- Emlak ilanlari harita uzerinde pin olarak gosterilir.
- Bir pine tikladiginizda sag tarafta yan panel acilir.

### Yan Panel

Secilen bolge veya mulk icin:

- **Deprem Riski Badge:** Bolgenim risk durumunu hizla gorun.
- **Bolge Analizi:** Nufus, fiyat ortalamalari, yatirim skoru.
- **Detayli Rapor Linki:** "Detayli Raporu Gor" butonuyla Bolge Analizi sayfasina yonlendirilirsiniz.

### Arama

Ust taraftaki arama cubuguna bolge veya ilan adi yazarak filtreleme yapabilirsiniz.

> **Mobil Uyumluluk:** Mobil cihazlarda yan panel yerine ekranin altindan kayan bir bilgi karti (bottom sheet) goruntulenir.

---

## 7. Ilan Asistani (Detayli)

**Yol:** `/dashboard/listings`

Ilan Asistani modulu uc sekmeden olusur:

| Sekme | Islem |
|-------|-------|
| **Metin Olustur** | AI ile ilan metni uretimi |
| **Virtual Staging** | Yapay zeka ile sanal mobilyalama |
| **Portal Export** | Ilan metinlerini portallere aktarma |

Her sekme bagimsiz calisir. Virtual Staging sekmesi **"YENI"** etiketi ile isaretlenmistir.

---

## 8. Kredi Hesaplayici

**Yol:** `/dashboard/calculator`

Emlak kredisi hesaplama, amortisman tablosu ve banka faiz oranlari karsilastirmasi.

### Hesaplama Formu

Sol paneldeki formu doldurun:

1. **Emlak Fiyati:** Minimum 100.000 TL (adim: 100.000 TL).
2. **Pesinat Orani:** %10 ile %90 arasi kayar cubukla ayarlayin. Pesinat tutari ve kredi tutari otomatik hesaplanir.
3. **Vade:** Asagidaki seceneklerden birini secin:
   - 60 Ay (5 Yil)
   - 120 Ay (10 Yil)
   - 180 Ay (15 Yil)
   - 240 Ay (20 Yil)
   - 360 Ay (30 Yil)
4. **Hesapla** butonuna tiklayin.

### Sonuc Ekrani

Hesaplama tamamlandiginda sag panelde sunlar goruntulenir:

- **Ozet Karti:**
  - Aylik taksit tutari (buyuk punto)
  - Kredi tutari, toplam odeme, toplam faiz
  - Anapara/faiz dagilim grafigi (donut chart)

- **Banka Karsilastirmasi:** Farkli bankalarin guncel faiz oranlariyla aylik taksit ve toplam odeme karsilastirmasi. En uygun oran **"En Uygun"** etiketi ile isaretlenir.

- **Amortisman Tablosu:** Ay bazinda taksit, anapara, faiz ve kalan borc detayi. Ilk 12 ay varsayilan olarak gosterilir; **"Tumunu Goster"** butonu ile tamamina ulasabilirsiniz.

---

## 9. Vitrin (Portfolyo Agi)

**Yol:** `/dashboard/network`

Musterilerinize ozel vitrin sayfalari olusturun ve digerof islerle ilan paylasin.

### Vitrin Yonetimi

**"Vitrin Yonetimi"** sekmesinde:

1. **Yeni Vitrin Olustur** butonuna tiklayin.
2. Vitrin basligini, aciklamasini ve temasini belirleyin.
3. Portfoyunuzden ilanlari secin.
4. Kaydedin — benzersiz bir vitrin linki olusturulur (`/vitrin/<slug>`).

Her vitrin karti uzerinde:
- **Ilan sayisi**, **goruntuleme sayisi** ve **olusturulma tarihi** istatistikleri.
- **Duzenle**, **Goruntule** ve **Linki Kopyala** butonlari.
- Yayinda/Taslak durumu badge ile gosterilir.

### Vitrin Sayfasi (Public)

Olusturdugunuz vitrin linki (`/vitrin/<slug>`) herkese acik bir sayfadir:

- Danismaninizin adi, ofisi, telefon ve e-posta bilgileri header'da goruntulenir.
- Sectiginiz ilanlar kart gorunumunde (grid veya list layout) listelenir.
- Her ilan kartinda: fotograf, fiyat, konum, metrekare ve oda sayisi.
- Sayfanin altinda **WhatsApp ile Iletisime Gec** butonu sabitlenir.
- Acik veya koyu tema destegi mevcuttur.

### Paylasim Agi

**"Paylasim Agi"** sekmesinde diger ofislerin paylasima actigi vitrinleri gorebilirsiniz. Her paylasimdaki danismanin adi, ofisi, ilan sayisi ve goruntuleme sayisi listelenir.

---

## 10. Telegram Baglantisi

**Yol:** `Ayarlar → Telegram Bagla`

Web platform hesabinizi Telegram botuna baglamak icin:

1. **Ayarlar** sayfasina gidin.
2. **Telegram Bagla** butonuna tiklayin.
3. Olusturulan baglanti linkine tiklayin — Telegram acilir.
4. Bot otomatik olarak hesabinizi eslestirir.
5. Basarili baglanti sonrasi platform bildirimlerini Telegram uzerinden almaya baslars iniz.

### Baglantinin Sagladiklari

Hesap baglandiktan sonra Telegram bot uzerinden:
- `/musteri` ile hizli musteri kaydi
- `/portfoy` ile ilan listesi
- `/rapor` ile PDF degerleme raporu
- `/fotograf` ile virtual staging
- `/ilan` ile ilan olusturma wizard'i

kullanabilirsiniz.

> **Not:** Baglanti tokeni belirli bir sure gecerlidir. Suresi dolmussa Ayarlar sayfasindan yeni token olusturabilirsiniz.

---

## 11. Mesajlar

**Yol:** `/dashboard/messages`

Bildirim ve mesaj yonetimi modulu. Platform uzerindeki bildirimlerinizi, musteri mesajlarinizi ve sistem uyarilarini bu ekrandan takip edebilirsiniz.

---

## Genel Ipuclari

- **Aktif Sayfa Vurgusu:** Sol sidebar'da bulundugunuz sayfanin linki mavi arka plan ile vurgulanir.
- **Responsive Tasarim:** Platform masaustu, tablet ve mobil cihazlarda uyumlu calisir. Mobil gorunumde sidebar gizlenir.
- **Kisa Yollar:** Dashboard kartlarina tiklayarak dogrudan ilgili modullere gecis yapabilirsiniz.
- **Kredi Bakiyesi:** Ilan Asistani sayfasinda sag ust kosedeki yesil badge ile mevcut kredinizi gorebilirsiniz.

---

## Hizli Erisim Tablosu

| Modul | Yol | Temel Islev |
|-------|-----|-------------|
| Dashboard | `/dashboard` | Genel ozet ve metrikler |
| Mulkler | `/dashboard/properties` | Portfoy yonetimi |
| Ilan Asistani | `/dashboard/listings` | AI ilan metni + virtual staging |
| Musteriler | `/dashboard/customers` | CRM ve musteri takibi |
| Degerleme | `/dashboard/valuations` | AI konut fiyat tahmini |
| Bolge Analizi | `/dashboard/areas` | Ilce bazli pazar raporu |
| Mesajlar | `/dashboard/messages` | Bildirim yonetimi |
| Harita | `/dashboard/maps` | Interaktif emlak haritasi |
| Ag (Vitrin) | `/dashboard/network` | Vitrin olusturma ve paylasim |
| Kredi | `/dashboard/calculator` | Kredi hesaplama ve banka karsilastirmasi |
| Ayarlar | `/dashboard/settings` | Hesap, Telegram baglama, plan |

---

> Daha fazla yardim icin destek ekibimizle iletisime gecebilirsiniz.
