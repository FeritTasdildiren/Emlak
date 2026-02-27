# Emlak Teknoloji Platformu - Product Backlog

**Tarih:** 20.02.2026
**Durum:** Taslak (Draft)
**Kapsam:** Alpha (MVP) + Beta Fazları
**Personalar:**
- **Hakan (Danışman):** 28-45 yaş, bireysel çalışır, sahada aktif, teknolojiyle arası orta, bütçe kısıtlı (200-500 TL). Hız ve pratiklik arar.
- **Elif (Broker):** 35-55 yaş, ofis sahibi, 3-10 danışman yönetir, portföyü geniş, bütçesi var (500-2000 TL). Kontrol, raporlama ve kurumsallık arar.

---

## 1. EPIC LİSTESİ VE DETAYLARI

### EPIC-01: AI Değerleme Motoru + Emsal Analiz
**Açıklama:** Kullanıcının girdiği özelliklere ve konuma göre mülkün tahmini kira/satış değerini hesaplayan ve benzer ilanlarla karşılaştıran modül.
**Fiyat Kademesi:** Starter+
**Sprint:** S5
**Bağımlılıklar:** Yok (Veri seti hazır olmalı)

*   **US-01.1:** Bir **Danışman (Hakan)** olarak, bir dairenin konum ve özelliklerini (m², oda sayısı, kat) girerek anında tahmini fiyat aralığı görmek istiyorum, böylece mülk sahibiyle görüşmeye hazırlıklı gidebilirim.
    *   **Kriterler:**
        - Adres, m², oda, bina yaşı, kat bilgisi girilebilmeli.
        - "Hesapla" butonuna basıldıktan sonra <3 saniye içinde sonuç dönmeli.
        - Sonuç; Min, Max ve Ortalama fiyatı içermeli.
    *   **Öncelik:** Must
    *   **Puan:** XL

*   **US-01.2:** Bir **Broker (Elif)** olarak, değerleme sonucunun dayandığı benzer (emsal) ilanları listelenmiş görmek istiyorum, böylece fiyatı müşteriye verilerle savunabilirim.
    *   **Kriterler:**
        - En az 3 adet benzer aktif/pasif ilan listelenmeli.
        - Emsallerin ilana olan uzaklığı ve fiyat farkı gösterilmeli.
    *   **Öncelik:** Must
    *   **Puan:** L

*   **US-01.3:** Bir **Danışman** olarak, değerleme sonucunu şık bir PDF raporu olarak indirmek istiyorum, böylece müşterime sunabilirim.
    *   **Kriterler:**
        - PDF çıktısında firma logosu ve danışman iletişim bilgileri olmalı.
        - Raporda fiyat analizi ve bölge trendi grafiği bulunmalı.
    *   **Öncelik:** Should
    *   **Puan:** M

### EPIC-02: Bölge Analiz Kartları
**Açıklama:** Belirli bir mahalle veya ilçe için demografik, sosyo-ekonomik ve pazar trendlerini gösteren bilgi kartları.
**Fiyat Kademesi:** Starter+
**Sprint:** S6
**Bağımlılıklar:** EPIC-01 (Veri altyapısı ortak)

*   **US-02.1:** Bir **Danışman** olarak, bir mahallenin ortalama kira dönüş süresini ve amortisman süresini görmek istiyorum, böylece yatırımcı müşterilerimi yönlendirebilirim.
    *   **Kriterler:**
        - Seçilen mahalle için "Amortisman Süresi (Yıl)" gösterilmeli.
        - Veri son 30 günlük pazar hareketine dayanmalı.
    *   **Öncelik:** Must
    *   **Puan:** M

*   **US-02.2:** Bir **Broker** olarak, bölgedeki nüfus yoğunluğu ve yaş dağılımını görmek istiyorum, böylece ticari mülk pazarlarken hedef kitleyi belirleyebilirim.
    *   **Kriterler:**
        - TÜİK veya benzeri kaynaktan demografik özet gösterilmeli.
        - Veriler görsel grafiklerle sunulmalı.
    *   **Öncelik:** Should
    *   **Puan:** S

### EPIC-03: Harita Entegrasyonu
**Açıklama:** İlanların, emsallerin ve önemli noktaların harita üzerinde görselleştirilmesi.
**Fiyat Kademesi:** Tüm Kademeler
**Sprint:** S6
**Bağımlılıklar:** Yok

*   **US-03.1:** Bir **Kullanıcı** olarak, portföyümdeki ilanları harita üzerinde pinlenmiş olarak görmek istiyorum, böylece birbirine yakın ilanları bir arada planlayabilirim.
    *   **Kriterler:**
        - Google Maps veya OpenStreetMap tabanlı harita yüklenmeli.
        - Pinlere tıklayınca ilan özeti açılmalı.
    *   **Öncelik:** Should
    *   **Puan:** M

*   **US-03.2:** Bir **Danışman** olarak, harita üzerinde "Okul", "Metro", "Hastane" gibi önemli noktaları (POI) görmek istiyorum, böylece ilanın konum avantajlarını anlatabilirim.
    *   **Kriterler:**
        - POI katmanları açılıp kapatılabilmeli.
        - İlana yürüme mesafesi hesaplanabilmeli.
    *   **Öncelik:** Could
    *   **Puan:** M

### EPIC-04: Deprem Risk Skoru
**Açıklama:** Binanın yaşı, zemin durumu ve bölge riskine dayalı tahmini risk bilgilendirmesi.
**Fiyat Kademesi:** Starter+
**Sprint:** S6
**Bağımlılıklar:** EPIC-03 (Konum verisi)

*   **US-04.1:** Bir **Danışman** olarak, binanın yapım yılı ve konumuna göre temel bir "Deprem Yönetmeliği Uyumu" bilgisi görmek istiyorum, böylece müşterimin güvenlik endişesini adresleyebilirim.
    *   **Kriterler:**
        - Bina yaşına göre (1999 öncesi/sonrası, 2018 sonrası) renk kodu (Kırmızı/Sarı/Yeşil) verilmeli.
        - "Resmi rapor değildir, bilgilendirme amaçlıdır" uyarısı net olmalı.
    *   **Öncelik:** Must
    *   **Puan:** S

### EPIC-05: CRM Müşteri-Portföy Eşleştirme (Temel)
**Açıklama:** Müşteri taleplerini kaydedip, uygun portföylerle otomatik eşleştiren sistem.
**Fiyat Kademesi:** Starter+
**Sprint:** S7
**Bağımlılıklar:** Yok

*   **US-05.1:** Bir **Danışman** olarak, yeni bir alıcı talebi (Örn: 2+1, Kadıköy, Max 5M TL) kaydetmek istiyorum, böylece müşteri veritabanımı oluşturabilirim.
    *   **Kriterler:**
        - İsim, Telefon, Talep Kriterleri formu olmalı.
        - Hızlı kayıt (Quick Add) özelliği olmalı.
    *   **Öncelik:** Must
    *   **Puan:** M

*   **US-05.2:** Bir **Danışman** olarak, kaydettiğim bir talebe uygun portföy sisteme girdiğinde bildirim almak istiyorum, böylece müşteriye hemen dönebilirim.
    *   **Kriterler:**
        - Kriterler (Fiyat, Oda, Konum) %80+ uyuştuğunda eşleşme sayılmalı.
        - Sistem içi bildirim düşmeli.
    *   **Öncelik:** Should
    *   **Puan:** L

### EPIC-06: AI İlan Asistanı
**Açıklama:** İlan fotoğraflarından ve temel bilgilerden otomatik, dikkat çekici ilan açıklaması ve başlığı üreten AI modülü.
**Fiyat Kademesi:** Pro+
**Sprint:** S8
**Bağımlılıklar:** Yok

*   **US-06.1:** Bir **Danışman** olarak, dairenin özelliklerini maddeler halinde girip "Açıklama Yaz" dediğimde pazarlama diliyle yazılmış metin almak istiyorum, böylece ilan girişinde zaman kaybetmem.
    *   **Kriterler:**
        - LLM (GPT/Claude) tabanlı üretim yapılmalı.
        - "Kurumsal", "Samimi", "Acil" gibi ton seçenekleri olmalı.
    *   **Öncelik:** Must
    *   **Puan:** L

### EPIC-07: Portföy Vitrin + Temel Eşleştirme
**Açıklama:** Danışmanın portföyünü sergileyebileceği dijital vitrin ve diğer danışmanlarla pasif eşleşme.
**Fiyat Kademesi:** Pro+
**Sprint:** S9
**Bağımlılıklar:** EPIC-05 (CRM verisi)

*   **US-07.1:** Bir **Danışman** olarak, seçtiğim ilanlardan oluşan kişisel bir web sayfası linki (Vitrin) oluşturmak istiyorum, böylece sosyal medyada paylaşabilirim.
    *   **Kriterler:**
        - Mobil uyumlu (responsive) tasarım olmalı.
        - Danışman iletişim bilgileri sabit (sticky) olmalı.
    *   **Öncelik:** Must
    *   **Puan:** M

*   **US-07.2:** Bir **Danışman** olarak, portföy kartından "WhatsApp'a Paylaş" butonuna basarak müşterime ilan bilgisini click-to-chat linkiyle göndermek istiyorum, böylece BSP onayı beklemeden WhatsApp üzerinden hızlıca paylaşım yapabilirim.
    *   **Kriterler:**
        - Buton `https://wa.me/?text=...` formatında link oluşturmalı (ilan başlığı + fiyat + vitrin linki).
        - Native WhatsApp uygulaması açılmalı (web/mobil).
        - BSP veya Cloud API **gerektirmemeli** (tüm planlarda kullanılabilir).
    *   **Öncelik:** Should
    *   **Puan:** S

*   **US-07.3 (Opsiyonel):** Bir **Danışman** olarak, seçtiğim ilanlar için toplu WhatsApp paylaşım linki oluşturmak istiyorum, böylece birden fazla ilanı tek mesajda paylaşabilirim.
    *   **Kriterler:**
        - Manuel link oluşturucu: seçili ilanlar → tek paylaşım linki.
        - Kopyala butonu ile panoya alınabilmeli.
    *   **Öncelik:** Could
    *   **Puan:** S

### EPIC-08: Kredi Hesaplayıcı
**Açıklama:** Güncel banka faiz oranlarıyla konut kredisi ödeme planı çıkaran araç.
**Fiyat Kademesi:** Starter+
**Sprint:** S9 (MVP-Alpha sonu)
**Bağımlılıklar:** Yok

*   **US-08.1:** Bir **Alıcı Adayı** olarak, ilandaki daire için ne kadar kredi çekebileceğimi ve aylık taksidimi hesaplamak istiyorum.
    *   **Kriterler:**
        - Güncel ortalama faiz oranları default gelmeli ama değiştirilebilmeli.
        - Toplam geri ödeme tutarı gösterilmeli.
    *   **Öncelik:** Could
    *   **Puan:** S

### EPIC-09: Telegram Bot + Mini App
**Açıklama:** Sistemin ana fonksiyonlarının Telegram üzerinden kullanımı.
**Fiyat Kademesi:** Tüm Kademeler
**Sprint:** S10 (Entegrasyon)
**Bağımlılıklar:** Tüm Alpha Epikleri

*   **US-09.1:** Bir **Danışman** olarak, Telegram botuna fotoğraf ve konum atarak hızlıca ilan taslağı oluşturmak istiyorum, böylece sahadayken veri girişi yapabilirim.
    *   **Kriterler:**
        - Bot conversation flow (diyalog akışı) kesintisiz olmalı.
        - Gönderilen fotolar geçici belleğe alınmalı.
    *   **Öncelik:** Must
    *   **Puan:** XL

*   **US-09.2:** Bir **Broker** olarak, gün sonu ofis raporunu (girilen ilan, alınan talep) Telegram mesajı olarak almak istiyorum.
    *   **Kriterler:**
        - Her akşam 20:00'de otomatik özet mesaj gelmeli.
    *   **Öncelik:** Should
    *   **Puan:** M

### EPIC-10: WhatsApp Cloud API (Elite) (BETA)
**Açıklama:** Resmi WhatsApp Cloud API (BSP: 360dialog) üzerinden şablon mesajlar, çift yönlü iletişim ve otomasyon. *Not: Starter/Pro click-to-chat (manuel link) ayrıca EPIC-07 portföy paylaşım kapsamında Alpha'da mevcuttur.*
**Fiyat Kademesi:** Elite
**Sprint:** S12
**Bağımlılıklar:** BSP Onayı (360dialog)

*   **US-10.1:** Bir **Danışman (Elite)** olarak, müşterime ilanı "WhatsApp'tan Gönder" dediğimde uygulama içinden profesyonel bir template kart formatında gitmesini ve delivery/read durumunu takip edebilmek istiyorum.
    *   **Kriterler:**
        - Template mesaj Meta onayı alınmış olmalı.
        - Gönderim loglanmalı (Message tablosu).
        - Delivery/read statü webhook ile takip edilmeli.
    *   **Öncelik:** Should
    *   **Puan:** L

### EPIC-11: EİDS Hibrit Doğrulama (BETA)
**Açıklama:** Elektronik İlan Doğrulama Sistemi uyumu için manuel + OCR süreci.
**Fiyat Kademesi:** Pro+
**Sprint:** S13
**Bağımlılıklar:** Yok

*   **US-11.1:** Bir **Danışman** olarak, yetki belgesinin fotoğrafını yükleyerek "Doğrulanmış İlan" rozeti almak istiyorum.
    *   **Kriterler:**
        - OCR ile belge numarası okunmalı.
        - Admin onayına düşmeli veya desen kontrolü yapılmalı.
    *   **Öncelik:** Must (Beta için)
    *   **Puan:** M

### EPIC-12: Portföy Paylaşım Ağı Aktif (BETA)
**Açıklama:** Danışmanlar arası komisyon paylaşımlı ortak çalışma ağı.
**Fiyat Kademesi:** Pro+
**Sprint:** S14
**Bağımlılıklar:** EPIC-07

*   **US-12.1:** Bir **Broker** olarak, "Paylaşıma Aç" işaretlediğim ilanın diğer ofislerin eşleşen müşterilerine (anonim olarak) bildirim gitmesini istiyorum.
    *   **Kriterler:**
        - Sadece Pro+ kullanıcılara bildirim gitmeli.
        - Müşteri verisi gizli kalmalı, sadece "Eşleşme var" denilmeli.
    *   **Öncelik:** Must (Beta için)
    *   **Puan:** XL

### EPIC-13: Çoklu Site Scraping (BETA)
**Açıklama:** Diğer ilan sitelerinden piyasa verisi toplama.
**Fiyat Kademesi:** Elite
**Sprint:** S15
**Bağımlılıklar:** Hukuki Onay

*   **US-13.1:** Bir **Broker** olarak, bölgemdeki tüm "Satılık 2+1" ilanların ortalama m² fiyatını (tüm sitelerden toplanmış) görmek istiyorum.
    *   **Kriterler:**
        - Veriler anonimleştirilmiş istatistik olarak sunulmalı (KVKK/Telif uyumu).
    *   **Öncelik:** Should
    *   **Puan:** XL

### EPIC-14: Gelişmiş AI Fotoğraf (BETA)
**Açıklama:** Boş odaları sanal mobilya ile döşeme (Virtual Staging) veya görüntü iyileştirme.
**Fiyat Kademesi:** Elite
**Sprint:** S16
**Bağımlılıklar:** GPU Maliyet Kontrolü

*   **US-14.1:** Bir **Danışman** olarak, kaba inşaat veya boş bir odanın fotoğrafına "Modern Mobilya Ekle" diyerek dolu halini oluşturmak istiyorum.
    *   **Kriterler:**
        - Orijinal ve işlenmiş foto yan yana sunulmalı.
        - Fotoğraf üzerine "Sanal Düzenleme" filigranı eklenmeli.
    *   **Öncelik:** Could
    *   **Puan:** L

### EPIC-15: Ofis Yönetim Paneli + Raporlama (BETA)
**Açıklama:** Ofis sahibi için personel performans ve finansal takip ekranları.
**Fiyat Kademesi:** Elite
**Sprint:** S17
**Bağımlılıklar:** Yok

*   **US-15.1:** Bir **Broker (Elif)** olarak, hangi danışmanımın kaç görüşme yaptığını ve kaç portföy aldığını tek ekranda görmek istiyorum.
    *   **Kriterler:**
        - Danışman bazlı performans tablosu.
        - Tarih aralığına göre filtreleme.
    *   **Öncelik:** Should
    *   **Puan:** M

---

## 2. ÖNCELİK MATRİSİ (MoSCoW & Kademeler)

| Epic | Özellik Adı | Faz | Öncelik (Kendi Fazında) | Kademe | Puan |
|:---:|:---|:---:|:---:|:---:|:---:|
| 01 | AI Değerleme | Alpha | **MUST** | Starter+ | XL |
| 09 | Telegram Bot | Alpha | **MUST** | Tümü | XL |
| 05 | CRM Temel | Alpha | **MUST** | Starter+ | M |
| 02 | Bölge Analiz | Alpha | **MUST** | Starter+ | M |
| 07 | Portföy Vitrin | Alpha | **MUST** | Pro+ | M |
| 04 | Deprem Skoru | Alpha | **MUST** | Starter+ | S |
| 06 | AI İlan Asistanı | Alpha | SHOULD | Pro+ | L |
| 03 | Harita Entegre | Alpha | SHOULD | Tümü | M |
| 08 | Kredi Hesap | Alpha | COULD | Starter+ | S |
| 12 | Portföy Ağı | Beta | **MUST** | Pro+ | XL |
| 11 | EİDS Hibrit | Beta | **MUST** | Pro+ | M |
| 10 | WhatsApp Cloud API (Elite) | Beta | SHOULD | Elite | L |
| 15 | Ofis Yönetim | Beta | SHOULD | Elite | M |
| 13 | Scraping | Beta | COULD | Elite | XL |
| 14 | AI Fotoğraf | Beta | COULD | Elite | L |

---

## 3. SPRINT BACKLOG GÖRÜNÜMÜ

### FAZ 0 (Hazırlık) - S0-S4
- **S0:** Mimari, DB Tasarımı, Repo Kurulumu
- **S1:** Messaging Gateway (Telegram API)
- **S2:** Veri Toplama Pipeline'ı (TKGM, Belediye)
- **S3:** AI Değerleme Modeli v0 (Back-end)
- **S4:** Hukuki Altyapı & Seed Kullanıcı Anlaşmaları

### MVP-ALPHA (S5-S11)
- **S5:** EPIC-01 (AI Değerleme)
- **S6:** EPIC-02 (Bölge), EPIC-03 (Harita), EPIC-04 (Deprem)
- **S7:** EPIC-05 (CRM - Müşteri Kayıt)
- **S8:** EPIC-06 (AI İlan Asistanı)
- **S9:** EPIC-07 (Vitrin), EPIC-08 (Kredi Hesap)
- **S10:** EPIC-09 (Telegram Entegrasyonu - Tüm özelliklerin bota bağlanması)
- **S11:** **ALPHA RELEASE** (Bug fix, Stabilizasyon, Seed Kullanıcı Açılışı)

### MVP-BETA (S12-S18)
- **S12:** EPIC-10 (WhatsApp Cloud API — Elite)
- **S13:** EPIC-11 (EİDS Hibrit)
- **S14:** EPIC-12 (Portföy Ağı Aktif - Eşleşme)
- **S15:** EPIC-13 (Scraping - İstatistik Modu)
- **S16:** EPIC-14 (AI Fotoğraf)
- **S17:** EPIC-15 (Ofis Yönetim Paneli)
- **S18:** **BETA RELEASE** (Yük Testi, Güvenlik Taraması, Genel Lansman)

---

---TECRÜBE BAŞLANGIÇ---
## Emlak Teknoloji Platformu - 2026-02-20
### Görev: Product Backlog Oluşturma
- [KARAR] Alpha özelliklerinden 6 tanesini "Must" olarak belirledim → "Must ≤ 6" kuralına uyuldu, diğerleri Should/Could yapıldı.
- [KARAR] Telegram Bot entegrasyonunu S10'a (Alpha sonuna) koydum → Önce web/backend fonksiyonlarının (Değerleme, CRM) bitmesi gerekiyordu, bot bu servisleri tüketecek.
- [PATTERN] Epic 13 (Scraping) ve 14 (AI Fotoğraf) yüksek riskli ve yüksek maliyetli → Beta'nın sonlarına ve "Elite" paketine itilerek risk ötelendi.
- [UYARI] EPIC-01 (Değerleme) XL puan aldı → Bu Epic çok büyük, Sprint 5 tek başına yetmeyebilir. Dev ekibiyle alt task'lara bölünmeli.
---TECRÜBE BİTİŞ---
