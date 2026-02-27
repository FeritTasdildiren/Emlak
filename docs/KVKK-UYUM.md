# KVKK Uyum Dokümanı Taslağı

**Tarih:** 2026-02-21
**Versiyon:** v1.0
**Kapsam:** Emlak Teknoloji Platformu — KVKK 6698 Uyum Çerçevesi

---

## 1. Aydınlatma Metni Taslağı

> Aşağıdaki metin, platform kullanıcılarına (emlak ofisleri, danışmanlar, bireysel kullanıcılar) gösterilecek aydınlatma metni taslağıdır. KVKK md.10 ve "Aydınlatma Yükümlülüğünün Yerine Getirilmesinde Uyulacak Usul ve Esaslar Hakkında Tebliğ" kapsamında hazırlanmıştır.

---

### KİŞİSEL VERİLERİN İŞLENMESİNE İLİŞKİN AYDINLATMA METNİ

**1. Veri Sorumlusu**

[Şirket Unvanı] ("Platform"), 6698 sayılı Kişisel Verilerin Korunması Kanunu ("KVKK") kapsamında veri sorumlusu sıfatıyla aşağıda açıklanan amaçlar doğrultusunda kişisel verilerinizi işlemektedir.

| Bilgi | Değer |
|-------|-------|
| Şirket Unvanı | [Tüzel kişi unvanı] |
| MERSİS No | [MERSİS numarası] |
| Adres | [Açık adres] |
| E-posta | kvkk@[domain].com |
| Telefon | [Telefon numarası] |
| KEP Adresi | [KEP adresi] |

**2. İşlenen Kişisel Veriler**

| Veri Kategorisi | Kişisel Veriler |
|-----------------|----------------|
| Kimlik Bilgileri | Ad-soyad, T.C. kimlik numarası (EİDS doğrulama kapsamında) |
| İletişim Bilgileri | E-posta adresi, telefon numarası, adres |
| Konum Verileri | IP adresi, GPS konum bilgisi (izin verildiğinde) |
| Dijital İz Verileri | Çerez verileri, oturum bilgileri, cihaz bilgileri, tarayıcı bilgileri |
| Finansal Veriler | Ödeme bilgileri (abonelik), fatura bilgileri |
| Mesleki Veriler | Taşınmaz ticareti yetki belgesi numarası, ofis bilgileri |
| İlan Verileri | İlan içerikleri, taşınmaz bilgileri, fotoğraflar |
| Kullanım Verileri | Platform kullanım istatistikleri, arama geçmişi, favori ilanlar |

**3. Kişisel Verilerin İşlenme Amaçları ve Hukuki Sebepleri**

| Amaç | Hukuki Sebep (KVKK md.5) |
|------|--------------------------|
| Üyelik kaydı oluşturma ve kimlik doğrulama | Sözleşmenin ifası (md.5/2-c) |
| EİDS entegrasyonu kapsamında yetki doğrulama | Kanunlarda açıkça öngörülme (md.5/2-a) |
| İlan yayınlama ve yönetimi | Sözleşmenin ifası (md.5/2-c) |
| AI destekli gayrimenkul değerleme | Açık rıza (md.5/1) |
| Bölge analizi ve piyasa istatistikleri | Meşru menfaat (md.5/2-f) |
| Ticari elektronik ileti gönderimi (SMS, e-posta, push) | Açık rıza (md.5/1) + 6563 ETK onayı |
| WhatsApp/Telegram üzerinden iletişim | Açık rıza (md.5/1) |
| Ödeme işlemlerinin gerçekleştirilmesi | Sözleşmenin ifası (md.5/2-c) |
| Yasal yükümlülüklerin yerine getirilmesi | Hukuki yükümlülük (md.5/2-ç) |
| Platform güvenliğinin sağlanması | Meşru menfaat (md.5/2-f) |
| İstatistiksel analiz (anonimleştirilmiş) | KVKK kapsamı dışı (md.28/1) |

**4. Kişisel Verilerin Aktarıldığı Taraflar**

| Aktarım Yapılan Taraf | Amaç | Hukuki Sebep |
|------------------------|------|-------------|
| Barındırma/bulut hizmet sağlayıcı (AWS/GCP) | Platform altyapısı | Sözleşmenin ifası + Standart Sözleşme |
| Ödeme sistemi sağlayıcısı (iyzico/Stripe) | Ödeme işlemleri | Sözleşmenin ifası |
| WhatsApp Business API (Meta) | Mesajlaşma hizmeti | Açık rıza + Standart Sözleşme |
| E-posta hizmet sağlayıcısı | İletişim | Sözleşmenin ifası |
| Ticaret Bakanlığı (EİDS) | Yasal yükümlülük | Kanunlarda açıkça öngörülme |
| Analitik hizmet sağlayıcıları | Platform iyileştirme | Açık rıza |
| Hukuki danışmanlar, denetçiler | Yasal süreçler | Hukuki yükümlülük / hak tesisi |

**5. Yurt Dışı Aktarım**

KVKK md.9 kapsamında, kişisel verileriniz aşağıdaki yurt dışı taraflara aktarılabilir:

| Hizmet Sağlayıcı | Ülke | Aktarım Mekanizması |
|-------------------|------|---------------------|
| AWS / Google Cloud | ABD/AB | Standart Sözleşme (KVKK md.9/4) |
| Meta (WhatsApp Business) | ABD | Açık Rıza + Standart Sözleşme |
| Stripe | ABD/AB | Standart Sözleşme |
| Google Analytics / Firebase | ABD | Açık Rıza |

> **Not:** Şubat 2026 itibarıyla KVKK Kurulu tarafından henüz hiçbir ülke/sektör için yeterlilik kararı verilmemiştir. Tüm yurt dışı aktarımlar Standart Sözleşme veya açık rıza mekanizması ile gerçekleştirilmektedir.

**6. Saklama Süreleri**

| Veri Kategorisi | Saklama Süresi | Dayanak |
|----------------|----------------|---------|
| Üyelik ve kimlik verileri | Üyelik süresince + 10 yıl | TTK md.82 |
| Ödeme/fatura bilgileri | İşlem tarihi + 10 yıl | VUK md.253 |
| Ticari elektronik ileti onay kayıtları | Onay geri çekilme + 3 yıl | 6563 ETK Yönetmelik |
| İlan verileri | İlan süresi + 5 yıl | TTK md.82 |
| Çerez/analitik verileri | Maksimum 2 yıl | Meşru menfaat |
| Platform erişim logları | 2 yıl | 5651 sayılı Kanun |
| EİDS doğrulama kayıtları | 10 yıl | 6563 ETK md.11 |

Saklama süresi dolan veriler, 6 ayı geçmeyen periyodik imha dönemlerinde silinir, yok edilir veya anonim hale getirilir.

**7. İlgili Kişi Hakları (KVKK md.11)**

KVKK'nın 11. maddesi kapsamında aşağıdaki haklara sahipsiniz:

- a) Kişisel verilerinizin işlenip işlenmediğini öğrenme
- b) Kişisel verileriniz işlenmişse buna ilişkin bilgi talep etme
- c) Kişisel verilerinizin işlenme amacını ve bunların amacına uygun kullanılıp kullanılmadığını öğrenme
- d) Yurt içinde veya yurt dışında kişisel verilerinizin aktarıldığı üçüncü kişileri bilme
- e) Kişisel verilerinizin eksik veya yanlış işlenmiş olması hâlinde bunların düzeltilmesini isteme
- f) KVKK md.7 kapsamında kişisel verilerinizin silinmesini veya yok edilmesini isteme
- g) (e) ve (f) bentleri uyarınca yapılan işlemlerin, kişisel verilerinizin aktarıldığı üçüncü kişilere bildirilmesini isteme
- h) İşlenen verilerinizin münhasıran otomatik sistemler vasıtasıyla analiz edilmesi suretiyle aleyhinize bir sonucun ortaya çıkmasına itiraz etme
- ı) Kişisel verilerinizin kanuna aykırı olarak işlenmesi sebebiyle zarara uğramanız hâlinde zararın giderilmesini talep etme

**Başvuru Yöntemi:** kvkk@[domain].com adresine veya [açık adres]'e yazılı olarak başvurabilirsiniz. Başvurular en geç 30 gün içinde ücretsiz olarak yanıtlanır. İşlemin ayrıca bir maliyet gerektirmesi hâlinde, Kurul tarafından belirlenen tarifedeki ücret alınabilir.

---

## 2. Açık Rıza Formu Taslağı

> Aşağıdaki form, aydınlatma metninden **ayrı** olarak sunulmalıdır. Her kategori için **ayrı onay kutusu** bulunmalı ve varsayılan olarak **işaretlenmemiş** gelmelidir.

---

### KİŞİSEL VERİLERİN İŞLENMESİNE İLİŞKİN AÇIK RIZA FORMU

Yukarıdaki Aydınlatma Metni'ni okudum ve anladım. Aşağıdaki konularda **ayrı ayrı** özgür irademle rıza veriyorum:

---

**[ ] 1. Ticari Elektronik İleti Gönderimi**

Platform tarafından sunulan hizmetler, kampanyalar, yenilikler ve sektörel gelişmeler hakkında **e-posta, SMS, push bildirim, WhatsApp ve Telegram** kanalları üzerinden ticari elektronik ileti gönderilmesine rıza veriyorum.

> *Bu rızayı vermemeniz halinde platformun temel hizmetlerinden yararlanmaya devam edebilirsiniz. Rızanızı dilediğiniz zaman geri çekebilirsiniz.*

---

**[ ] 2. Konum Verisi Kullanımı**

Bölge bazlı emlak analizleri, yakınımdaki ilanlar, deprem riski değerlendirmesi ve piyasa karşılaştırmaları gibi hizmetler kapsamında **GPS konum verimin** işlenmesine rıza veriyorum.

> *Konum izni vermemeniz halinde bu hizmetleri manuel adres girişi ile kullanabilirsiniz.*

---

**[ ] 3. AI ile Otomatik Değerleme (Profilleme)**

Taşınmaz ilanlarıma ilişkin verilerin (fiyat, metrekare, konum, kat, oda sayısı vb.) yapay zeka modelleri tarafından analiz edilerek **otomatik fiyat tahmini ve değerleme** yapılmasına rıza veriyorum.

Bu işlem kapsamında:
- Makine öğrenimi modelleri ilanlarımı analiz edecektir
- Sonuçlar tavsiye niteliğindedir, bağlayıcı değildir
- KVKK md.11/1(h) kapsamında otomatik kararlara **itiraz hakkım** saklıdır

> *Bu rızayı vermemeniz halinde AI değerleme özelliğini kullanamazsınız, ancak diğer platform hizmetlerinden yararlanmaya devam edebilirsiniz.*

---

**[ ] 4. Kişisel Verilerin Yurt Dışına Aktarılması**

Platformun teknik altyapısı gereği kişisel verilerimin aşağıdaki yurt dışı hizmet sağlayıcılara aktarılmasına rıza veriyorum:

| Hizmet | Sağlayıcı | Sunucu Lokasyonu |
|--------|-----------|-----------------|
| Mesajlaşma | Meta (WhatsApp Business) | ABD |
| Analitik | Google Analytics / Firebase | ABD |
| Bulut altyapı | AWS / Google Cloud | AB/ABD |

> *Yurt dışı aktarımına rıza vermemeniz halinde WhatsApp üzerinden iletişim hizmeti sunulamayacak, alternatif iletişim kanalları kullanılacaktır.*

---

**Ad Soyad:** _______________
**Tarih:** _______________
**İmza / Elektronik Onay:** _______________

---

### Rıza Geri Çekme Mekanizması

Verdiğiniz rızayı dilediğiniz zaman, rıza vermek kadar kolay bir yöntemle geri çekebilirsiniz:
- Platform ayarları → Gizlilik → Rıza Yönetimi
- kvkk@[domain].com adresine e-posta göndererek
- Ticari elektronik ileti için: iletideki "abonelikten çık" bağlantısı

Rızanın geri çekilmesi, geri çekilmeden önce yapılan işlemlerin hukuka uygunluğunu etkilemez.

---

## 3. VERBİS Kaydı Gereklilikleri

### 3.1 Kayıt Zorunluluğu Eşikleri (Güncel — 2026)

| Kriter | Eşik | Kayıt Zorunlu mu? |
|--------|------|-------------------|
| Yıllık çalışan sayısı ≥ 50 | Bilançodan bağımsız | **EVET** |
| Yıllık mali bilanço ≥ 100 milyon TL | Çalışan sayısından bağımsız | **EVET** |
| Çalışan < 50 VE bilanço < 100M TL | Ana faaliyet özel nitelikli veri değilse | **HAYIR (muaf)** |
| Ana faaliyet özel nitelikli veri işleme | Çalışan ≥ 10 VEYA bilanço ≥ 10M TL | **EVET** |
| Ana faaliyet özel nitelikli veri işleme | Çalışan < 10 VE bilanço < 10M TL | **HAYIR (2025/1572 muafiyeti)** |

### 3.2 Platform İçin Değerlendirme

- **Startup/erken aşama** (çalışan < 50, bilanço < 100M TL): VERBİS kaydından **muaf** olabilir.
- **Büyüme aşaması** (çalışan ≥ 50 veya bilanço ≥ 100M TL): Kayıt **zorunlu**.
- Platform ana faaliyet konusu gayrimenkul teknolojisi olduğundan, özel nitelikli kişisel veri (sağlık, biyometrik, ırk vb.) işleme ana faaliyet kapsamında **değildir**.

> **Önemli:** VERBİS muafiyeti, KVKK yükümlülüklerinin tamamından muaf olmak anlamına **gelmez**. Aydınlatma, açık rıza, veri güvenliği, saklama/imha politikası gibi yükümlülükler muafiyet durumunda da geçerlidir.

### 3.3 VERBİS'e Kaydedilmesi Gereken Bilgiler

Kayıt zorunluluğu doğduğunda:
- Veri sorumlusu ve irtibat kişi bilgileri
- Kişisel veri işleme amaçları
- Veri konusu kişi grupları ve gruplara ait veri kategorileri
- Alıcı veya alıcı grupları
- Yabancı ülkelere aktarım yapılıp yapılmadığı
- Veri güvenliğine ilişkin alınan tedbirler
- Azami muhafaza (saklama) süresi

### 3.4 Cezalar (2026 Güncel)

| İhlal | Alt Sınır | Üst Sınır |
|-------|----------|----------|
| VERBİS kayıt/bildirim yükümlülüğüne aykırılık | 341.809 TL | 17.092.242 TL |
| Aydınlatma yükümlülüğünü yerine getirmeme | 85.437 TL | 1.709.200 TL |
| Veri güvenliği yükümlülüğü ihlali | 256.000 TL | 17.092.242 TL |
| Kurul kararına uymama | 427.263 TL | 17.092.242 TL |

---

## 4. Scraping/CRM Ayrımı

### 4.1 Kamuya Açık Veri vs. Kişisel Veri

| Kavram | Tanım | KVKK Durumu |
|--------|-------|-------------|
| **Kamuya açık (alenileşmiş) veri** | İlgili kişinin kendisi tarafından alenileştirdiği veriler (md.5/2-d) | Alenileştirme amacı dahilinde açık rıza aranmadan işlenebilir |
| **Kişisel veri** | Kimliği belirli/belirlenebilir gerçek kişiye ilişkin her türlü bilgi (md.3) | KVKK kapsamında, hukuki sebep gerekli |
| **Anonim veri** | Hiçbir şekilde gerçek kişiyle ilişkilendirilemeyen veri (md.3/1-b) | KVKK kapsamı **dışında** (md.28/1) |

### 4.2 Scraping Senaryoları ve KVKK Durumu

| Senaryo | Kişisel Veri? | KVKK Durumu | Risk |
|---------|---------------|-------------|------|
| Fiyat, m², oda sayısı, kat bilgisi toplama | Hayır | KVKK kapsamında değil | Düşük (KVKK) |
| İlan sahibi ad-soyad, telefon toplama | Evet | Kişisel veri işleme; hukuki sebep gerekli | **Çok yüksek** |
| Scraping → CRM'e aktarma → pazarlama | Evet | Açık rıza zorunlu + 6563 ETK onayı | **Çok yüksek** |
| Scraping → anonimleştirilmiş istatistik | Geçiş sürecinde evet | Anonimize edilene kadar KVKK kapsamında | Orta |
| Resmi kaynak (TCMB, TÜİK) verileri | Hayır | Kanunlarda açıkça öngörülme | Çok düşük |

### 4.3 Önemli Ayrımlar

**Alenileştirme ≠ Genel Kullanım İzni:**
- Bir kişinin emlak ilanına telefon numarasını koyması, o numaranın **ilan amacıyla** alenileştirilmesidir.
- Aynı numaranın toplu olarak CRM'e aktarılıp farklı amaçlarla (pazarlama, profilleme) kullanılması **alenileştirme amacını aşar**.

**CRM Verisi İçin Gereklilikler:**
- Doğrudan ilgili kişiden toplanan veri → Aydınlatma + hukuki sebep yeterli
- Scraping ile elde edilen kişisel veri → Aydınlatma + çoğu durumda açık rıza gerekli
- Ticari elektronik ileti göndermek için → Her iki durumda da 6563 ETK ayrı onayı zorunlu

### 4.4 Anonimleştirme Önerileri

KVKK'nın anonimleştirme rehberine göre:

| Yöntem | Açıklama | Uygunluk |
|--------|----------|----------|
| **Gruplama/kümeleme** | Bireysel veriyi bölge/ilçe bazlı ortalama haline getirme | Yüksek |
| **Veri maskeleme** | İlan sahibi bilgilerini kaldırma | Yüksek |
| **Genelleme** | Kesin konum yerine ilçe/mahalle seviyesi kullanma | Yüksek |
| **Gürültü ekleme** | Fiyatlara küçük sapmalar ekleme | Orta |
| **Pseudonimleştirme** | Kişisel veriyi takma adla değiştirme | **Yeterli değil** — veri hâlâ kişisel veri kapsamında |

> **Önemli:** Verilerin anonim hale getirilmesine kadar geçen süreçteki tüm işleme faaliyetleri KVKK'ya tabidir. Anonimleştirme işlemi **geri dönüşümsüz** olmalıdır.

### 4.5 Önerilen Yaklaşım

1. **Scraping ile yalnızca kişisel veri içermeyen verileri toplayın** (fiyat, m², oda sayısı, konum — ilçe/mahalle düzeyinde)
2. **İlan sahibi iletişim bilgilerini kesinlikle toplamayın** (TCK 135-136 ceza riski)
3. Toplanan verileri **mümkün olan en erken aşamada anonimleştirin**
4. CRM verisi için **doğrudan ilgili kişiden, aydınlatma yaparak ve hukuki sebebe dayanarak** toplayın
5. Pazarlama amaçlı kullanım için **6563 ETK ayrı onayı** alın

---

## 5. Yapay Zeka ve KVKK (Kasım 2025 Rehberi)

KVKK'nın 24.11.2025 tarihli "Üretken Yapay Zeka ve Kişisel Verilerin Korunması Rehberi" kapsamında platform yükümlülükleri:

| Yükümlülük | Açıklama |
|------------|----------|
| Anonimleştirilmiş veri ile eğitim | ML modeli yalnızca anonim veri ile eğitilirse KVKK kapsamı dışındadır |
| Otomatik karar verme itiraz hakkı | Kullanıcılara AI değerleme sonuçlarına itiraz mekanizması sunulmalı |
| Şeffaflık | Kararın nasıl alındığı açıklanabilir olmalı |
| Az veri prensibi | Minimum gerekli veri ile maksimum performans |
| Ayrımcı örüntü kontrolü | Belirli mahallelere/gruplara karşı önyargı denetimi |

---

## 6. Yurt Dışı Veri Aktarımı Mekanizmaları (md.9 — Güncel)

### Mart 2024 Kanun Değişikliği (7499 sayılı Kanun)

1 Haziran 2024'te yürürlüğe giren değişiklikle GDPR uyumlu yeni sistem:

| Mekanizma | Açıklama | Durum (Şubat 2026) |
|-----------|----------|---------------------|
| **Yeterlilik kararı** | Kurul'un ülke/sektör bazında karar vermesi | Henüz hiçbir karar verilmemiş |
| **Standart Sözleşme** | Kurul'un matbu sözleşmesi (4 Haziran 2024'te kabul edildi) | **Aktif — kullanılabilir** |
| **Bağlayıcı Şirket Kuralları** | Çok uluslu şirket grupları için | Mevcutama çoğu startup için uygunsuz |
| **Taahhütname** | Yazılı taahhütle Kurul izni | Mevcut |
| **Açık rıza** | İlgili kişinin açık rızası | İstisnai durumlar için |

**Standart Sözleşme yükümlülüğü:** İmzalanmasını takip eden **5 iş günü** içinde Kurum'a bildirilmeli. Bildirim yapılmamasının cezası: **50.000 TL — 1.000.000 TL**

---

## Kaynaklar

- [KVKK Aydınlatma Yükümlülüğü](https://www.kvkk.gov.tr/Icerik/2033/Aydinlatma-Yukumlulugu-)
- [Aydınlatma Tebliğ Metni](https://kvkk.gov.tr/Icerik/5443/AYDINLATMA-YUKUMLULUGUNUN-YERINE-GETIRILMESINDE-UYULACAK-USUL-VE-ESASLAR-HAKKINDA-TEBLIG)
- [KVKK Açık Rıza Rehberi (PDF)](https://www.kvkk.gov.tr/yayinlar/A%C3%87IK%20RIZA.pdf)
- [KVKK 2025/1072 Sayılı Karar (SMS Doğrulama)](https://www.kvkk.gov.tr/Icerik/8338/2025-1072)
- [VERBİS 2025/1572 Sayılı Karar](https://www.kvkk.gov.tr/Icerik/8388/KAMUOYU-DUYURUSU)
- [Yurt Dışı Aktarım Rehberi (Ocak 2025)](https://www.kvkk.gov.tr/Icerik/8142/Kisisel-Verilerin-Yurt-Disina-Aktarilmasi-Rehberi)
- [Standart Sözleşme Dokümanları](https://www.kvkk.gov.tr/Icerik/7938/Standart-Sozlesmeler-ve-Baglayici-Sirket-Kurallarina-Iliskin-Dokumanlar-Hakkinda-Kamuoyu-Duyurusu)
- [WhatsApp KVKK Kararı (2021/891)](https://www.kvkk.gov.tr/Icerik/7045/WHATSAPP-UYGULAMASI-HAKKINDA-YURUTULEN-RESEN-INCELEMEYE-ILISKIN-KAMUOYU-DUYURUSU)
- [Gayrimenkul Şirketi SMS Kararı (2020/67)](https://www.kvkk.gov.tr/Icerik/6718/2020-67)
- [Üretken Yapay Zeka KVKK Rehberi (Kasım 2025)](https://www.kvkk.gov.tr/Icerik/8547/uretken-yapay-zeka-ve-kisisel-verilerin-korunmasi-rehberi-15-soruda)
- [2026 İdari Para Cezaları — Mondaq](https://www.mondaq.com/turkey/data-protection/1729106/2026-y%C4%B1l%C4%B1nda-kvkk-kapsam%C4%B1ndaki-%C4%B0dari-para-cezas%C4%B1-tutarlar%C4%B1-g%C3%BCncellendi)
- [6698 Sayılı Kanun Tam Metni](https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=6698&MevzuatTur=1&MevzuatTertip=5)
