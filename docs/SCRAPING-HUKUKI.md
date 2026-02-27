# Scraping Hukuki Araştırma Raporu

**Tarih:** 2026-02-21
**Versiyon:** v1.0
**Kapsam:** Emlak Teknoloji Platformu — Web Scraping Hukuki Çerçeve

---

## 1. Türkiye'deki Büyük Emlak Portallerinin ToS Analizi

### 1.1 Sahibinden.com

**Kullanım Koşulları — Scraping Yasağı:**

Sahibinden.com'un Ek-1 Kullanım Koşulları'nda scraping açıkça yasaklanmıştır:

> "Screen scraping" yazılımları veya sistemleri, otomatik aletler ya da manuel süreçler kullanılması, diğer kullanıcılarının verilerine veya yazılımlarına izinsiz olarak ulaşılması, çeşitli kriterlere göre yapılacak tespitler neticesinde bot çalıştırma, DDOS atakları ve sair her türlü sistemlerin bütününü veya bir kısmını bozmaya, değiştirmeye, mevcut performansını azaltmaya veya yok etmeye yönelik kullanımlar SAHİBİNDEN'in takdirine bağlı olarak engellenecektir.

| Özellik | Durum |
|---------|-------|
| ToS'ta scraping yasağı | **Evet, açık** |
| Teknik engelleme | Agresif (CAPTCHA, IP ban — ~10-15 istek sonrası) |
| Kamuya açık API | **Hayır** — Yalnızca kurumsal (EİDS entegrasyonlu, yetki belgeli) |
| Veri lisanslama | Yok (ODTÜ işbirliğiyle kendi analiz raporlarını üretiyor) |
| robots.txt | Var (403 dönüyor, agresif koruma) |

**Rekabet Kurulu Kararı (2023-2025):**
- Sahibinden.com'a **40,1 milyon TL** ceza kesildi (hakim durumun kötüye kullanılması — 4054/md.6).
- Rakiplerine zorunlu API veri paylaşım altyapısı kurma yükümlülüğü getirildi.
- API 21 Mayıs 2025'te aktif hale geldi.
- Bu API yalnızca **kurumsal emlak ve vasıta mağazaları** için, EİDS entegrasyonu ve Ticaret Bakanlığı yetki belgesi şartıyla kullanılabilir.

### 1.2 Hepsiemlak.com

**Kullanım Koşulları — Scraping Yasağı:**

> Hepsiemlak'ın önceden yazılı iznini almaksızın, sitede otomatik program, robot, web crawler, veri madenciliği (data mining), veri taraması (data crawling) ve "screen scraping" yazılımları kullanılması yasaklanmıştır.

| Özellik | Durum |
|---------|-------|
| ToS'ta scraping yasağı | **Evet, açık** |
| Teknik engelleme | Mevcut |
| Kamuya açık API | **Hayır** |
| Veri lisanslama | Yok (Endeksa teknoloji altyapısını kullanıyor) |
| robots.txt | Var (403 dönüyor) |
| Ceza hükmü | İhlal durumunda mahkeme masrafları + avukatlık ücreti dahil tüm zararlar |

### 1.3 Emlakjet.com

| Özellik | Durum |
|---------|-------|
| ToS'ta scraping yasağı | **Evet** (ToS + robots.txt kuralları) |
| Teknik engelleme | Mevcut — belirli botlar kara listede (Scrappy, dotbot, yacybot vb.) |
| Kamuya açık API | **Hayır** |
| Veri lisanslama | Endeksa ile birleşmiş (iLab çatısı) — "Veri, API ve Widget" hizmetleri mevcut olabilir |
| robots.txt | Detaylı kurallar: /listings/*, /listing/* genel botlara kapalı |

### 1.4 Karşılaştırma Özeti

| | Sahibinden | Hepsiemlak | Emlakjet |
|-|-----------|------------|---------|
| ToS scraping yasağı | Evet, açık | Evet, açık | Evet |
| Teknik engelleme | Agresif | Mevcut | Mevcut |
| API | Kurumsal (zorunlu) | Yok | Yok |
| Veri lisanslama | Yok | Yok | Endeksa üzerinden olabilir |
| Hukuki tehdit | Yüksek | Yüksek | Orta-Yüksek |

---

## 2. Emsal Kararlar

### 2.1 Uluslararası Emsal Kararlar

#### hiQ Labs vs LinkedIn (ABD, 2017-2022)

**Süreç:**
1. hiQ, LinkedIn'in kamuya açık profil verilerini topluyordu.
2. LinkedIn engelleyince hiQ dava açtı.
3. 2019: 9. Daire Temyiz Mahkemesi hiQ lehine — kamuya açık verilerin scraping'i CFAA ihlali değil.
4. 2021: ABD Yüksek Mahkemesi, Van Buren kararını referans göstererek yeniden inceleme istedi.
5. Nisan 2022: 9. Daire önceki kararını teyit etti — "kamuya açık web sitesini tarayan botun yetkisiz erişim kavramına girmediği" hükmü.
6. Aralık 2022: LinkedIn **sözleşme hukuku** üzerinden kazandı. hiQ'nun Kullanıcı Sözleşmesi ihlali tespit edildi; tüm veri/algoritmaların silinmesi kararlaştırıldı.

**Ders:** CFAA (ceza hukuku) kapsamında kamuya açık veri scraping'i suç olmayabilir, ama **sözleşme ihlali** üzerinden hukuki sorumluluk doğar.

#### Ryanair vs PR Aviation (AB, 2015)

**Karar (CJEU, C-30/14):**
- PR Aviation, Ryanair uçuş verilerini scraping ile toplayıp fiyat karşılaştırma sitesinde kullanıyordu.
- CJEU: Veri Tabanı Direktifi'nin ne telif ne de sui generis koruma altında olmayan veri tabanlarına uygulanamayacağına hükmetti.
- **Ancak:** Ryanair'ın ToS'undaki scraping yasağı **sözleşmesel olarak geçerli** bulundu.

**Ders:** AB hukukunda veri tabanı koruması sınırlı olsa bile, **kullanım koşulları sözleşmesel bağlayıcılık taşır**.

#### Meta vs BrandTotal (ABD, 2022)

**Karar:**
- BrandTotal, Chrome eklentisi ile Facebook kullanıcı verilerini topluyordu.
- Meta lehine karar: ToS ihlali (md.3.2.3: "Otomatik yollarla veri toplayamazsınız") + sahte hesaplarla erişim CFAA ihlali.
- Ekim 2022'de gizli uzlaşma; BrandTotal kalıcı olarak men edildi.

**Ders:** Şifre korumalı içeriğe erişim kesinlikle suç. ToS ihlali bağımsız hukuki sorumluluk doğurur.

### 2.2 Türkiye'deki Emsal Kararlar

#### Yargıtay 11. HD, E. 2016/6829, K. 2018/768 (05.02.2018)

- İnternet sitelerinin veri tabanı olarak FSEK kapsamında korunması yönünde eğilim.
- Web sitelerindeki verilerin toplu olarak alınması, veri tabanı hakkının ihlali olarak değerlendirilebilir.

#### Rekabet Kurulu — Sahibinden.com (2023-2025)

- Sahibinden'in veri paylaşımını engellemesi **hakim durumun kötüye kullanılması** olarak değerlendirildi.
- Zorunlu API paylaşım altyapısı kararı — Türkiye'de ilk.
- **Çift yönlü etki:** Hem veriyi kısıtlayan (hakim platform) hem de haksız kullanan (scraper) sorumluluk taşıyabilir.

#### Rekabet Kurulu — Online İkinci El Kitap Platformu (22-16/273122, 07.04.2022)

- Kullanıcılar tarafından girilen veriler "gönüllü ve erişime açık veriler" olarak nitelendirildi.
- Veri portabilitesinin kısıtlanması hakim durumun kötüye kullanılması teşkil edebilir.

### 2.3 Türkiye'de Uygulanabilirlik Değerlendirmesi

| Emsal | Türkiye'de Uygulanabilirlik | Açıklama |
|-------|---------------------------|----------|
| hiQ vs LinkedIn (CFAA) | Kısmen — TCK 243 paraleli | Kamuya açık veriye erişim tek başına TCK 243 ihlali olmayabilir, ancak kesin içtihat yok |
| hiQ vs LinkedIn (Sözleşme) | **Yüksek** | Türk Borçlar Kanunu kapsamında ToS ihlali sözleşme ihlali teşkil eder |
| Ryanair vs PR Aviation | **Yüksek** | ToS'un sözleşmesel bağlayıcılığı Türk hukukunda da geçerli |
| Meta vs BrandTotal | **Doğrudan** | TCK 243 + TCK 135/136 kapsamında cezai sorumluluk |

---

## 3. Türk Hukukunda Scraping'in Yasal Çerçevesi

### 3.1 İlgili Mevzuat

| Kanun | İlgili Maddeler | Kapsam |
|-------|-----------------|--------|
| **TCK 243** | Bilişim sistemine girme | Hukuka aykırı sisteme giriş (1 yıl hapis) |
| **TCK 244** | Sistemi engelleme, bozma | Yoğun trafikle sistem performansı düşürme (1-5 yıl hapis) |
| **TCK 135-136** | Kişisel veri kaydetme/ele geçirme | İletişim bilgisi toplama (2-4 yıl hapis) |
| **KVKK 6698** | md.5, md.9, md.10, md.11 | Kişisel veri işleme, aktarım, aydınlatma |
| **FSEK 5846** | md.6/I-11, Ek md.8 | Veri tabanı koruması (telif + sui generis) |
| **TTK 6102** | md.54-55 | Haksız rekabet — başkasının iş ürününden yetkisiz yararlanma |
| **6563 ETK** | Ticari elektronik ileti | Scraping ile elde edilen iletişim bilgisiyle pazarlama |

### 3.2 TCK 243 — Bilişim Sistemine Girme

- **Temel suç:** 1 yıla kadar hapis veya adli para cezası
- **Zarar varsa:** 6 aydan 2 yıla kadar hapis
- **Kamu kurumu:** Ceza yarı oranında artar

**Scraping bağlamı:**
- Kamuya açık sayfalara normal HTTP istekleriyle erişim → TCK 243 kapsamına girip girmeyeceği **tartışmalı**
- ToS ile yasaklanan erişim + teknik engellerin aşılması (CAPTCHA bypass) → TCK 243 **gündeme gelebilir**
- Şifre korumalı alanlara yetkisiz erişim → **Kesinlikle kapsam dahilinde**

### 3.3 FSEK — Veri Tabanı Koruması

**İkili koruma rejimi:**

1. **Telif hakkı (md.6/I-11):** Verilerin seçimi ve düzenlenmesi özgün nitelik taşıyorsa
2. **Sui generis (Ek md.8):** Özgün olmasa bile, "esaslı yatırım" yapılmış veri tabanları

> **Not:** "Satılık ev ilanlarından derlenen semtlere göre metrekare fiyatları gibi istatistik bilgiler eser olarak nitelendirilemez." Ancak bu verilerin **derlenme biçimi** (veri tabanı yapısı) korunabilir.

---

## 4. Risk Değerlendirmesi ve Öneriler

### 4.1 Risk Matrisi

| Yaklaşım | KVKK | TCK | FSEK | ToS | TTK | Genel Risk |
|----------|------|-----|------|-----|-----|------------|
| **Fiyat istatistikleri** (kişisel veri yok, agregatif) | Düşük | Düşük | Orta | Yüksek | Orta | **ORTA** |
| **İlan detayları** (anonim, bireysel ilan) | Düşük | Düşük-Orta | Yüksek | Yüksek | Yüksek | **YÜKSEK** |
| **İletişim bilgileri** (ad, telefon, e-posta) | Çok Yüksek | Çok Yüksek | Yüksek | Yüksek | Yüksek | **ÇOK YÜKSEK** |

### 4.2 Düşük Riskli Yaklaşım: Sadece Fiyat İstatistikleri

**Ne:** Kişisel veri içermeyen, ilçe/mahalle bazlı ortalama m² fiyatları, fiyat trendleri.

| Risk Faktörü | Değerlendirme |
|--------------|--------------|
| KVKK | **Düşük** — kişisel veri yok, anonim istatistik |
| TCK 243 | **Düşük** — kamuya açık sayfalara normal erişim |
| FSEK | **Orta** — agregatif istatistik eser değil ama kaynak veri tabanı korunuyor |
| ToS ihlali | **Yüksek** — veri toplama yöntemi scraping ise hâlâ ToS ihlali |

**Azaltıcı tedbirler:**
- robots.txt'ye uyum
- Düşük frekanslı erişim (saniyede 1 istek altı)
- Sonuçları agregatif/anonimleştirilmiş olarak sunma
- Kaynak platformu referans gösterme

### 4.3 Orta Riskli Yaklaşım: İlan Detayları (Anonim)

**Ne:** Bireysel ilan detayları (fiyat, m², oda, kat, mahalle) — ilan sahibi bilgisi olmadan.

**Ek riskler:**
- FSEK sui generis ihlali (veri tabanının esaslı kısmının kopyalanması)
- TTK haksız rekabet (başkasının iş ürününden yetkisiz yararlanma)
- ToS ihlali → sözleşme hukuku davaları

### 4.4 Yüksek Riskli Yaklaşım: İletişim Bilgileri

**Ne:** İlan sahibi ad-soyad, telefon, e-posta bilgileri.

**Riskler:**
- KVKK cezası: **85.437 TL — 17.092.242 TL**
- TCK 135: **1-3 yıl hapis**
- TCK 136: **2-4 yıl hapis**
- KVKK Kurul Kararı 2017/61: Kişisel verilerin toplu toplanması açıkça yasaklanmış

> **Kesin öneri: Bu yaklaşımdan kaçınılmalıdır.**

### 4.5 Önerilen Strateji

```
ÖNCELİK SIRASI (güvenlikten riskli olana doğru):

1. YASAL ALTERNATİFLER (Risk: Çok Düşük)
   ├── TCMB Konut Fiyat Endeksi (resmi, açık kaynak)
   ├── TÜİK gayrimenkul verileri
   ├── Tapuda satış istatistikleri (resmi kaynaklar)
   └── Belediye imar verileri

2. LİSANSLI VERİ ERİŞİMİ (Risk: Düşük)
   ├── Endeksa API/Widget hizmetleri (Emlakjet ekosistemi)
   ├── Sahibinden Kurumsal API (yetki belgesi gerekli)
   └── Portallerle doğrudan veri lisanslama anlaşması

3. KULLANICI GİRİŞLİ VERİ (Risk: Çok Düşük)
   ├── Platformumuza doğrudan girilen ilan verileri
   ├── EİDS entegrasyonu ile doğrulanmış veriler
   └── Kullanıcı onayı ile CRM verisi

4. ANONİM İSTATİSTİK SCRAPING (Risk: Orta — son çare)
   ├── Yalnızca fiyat/m²/oda istatistikleri
   ├── robots.txt uyumu
   ├── Düşük frekanslı erişim
   └── Sonuçları mutlaka anonimleştirme
```

### 4.6 Risk Azaltma Stratejileri (Scraping Yapılması Durumunda)

| Strateji | Açıklama |
|----------|----------|
| **robots.txt uyumu** | Site sahibinin iradesine saygı gösterir, iyi niyet kanıtı |
| **Rate limiting** | Saniyede 1 istekten az, sunucu yükünü artırmama |
| **Kişisel veri filtreleme** | Toplanan veride kişisel veri varsa anında silme |
| **Anonimleştirme** | Mümkün olan en erken aşamada agregatif hale getirme |
| **Kaynak gösterme** | Verilerin kaynağını belirtme (ancak ToS ihlalini ortadan kaldırmaz) |
| **Hukuki danışmanlık** | Operasyona başlamadan uzman avukat görüşü alma |
| **Yazılı izin** | Portallerle yazılı anlaşma yapma (en güvenli yol) |

---

## Kaynaklar

### Portal Kullanım Koşulları
- [Sahibinden.com Ek-1 Kullanım Koşulları](https://www.sahibinden.com/sozlesmeler/ek-1-kullanim-kosullari-37)
- [Hepsiemlak Kullanım Koşulları](https://www.hepsiemlak.com/kullanim-kosullari)
- [Sahibinden API Kullanımı ile Veri Transferi](https://yardim.sahibinden.com/hc/tr/articles/19780244786460-API-Kullan%C4%B1m%C4%B1-ile-Veri-Transferi)

### Emsal Kararlar
- [hiQ Labs v. LinkedIn — Wikipedia](https://en.wikipedia.org/wiki/HiQ_Labs_v._LinkedIn)
- [9th Circuit Ruling — Justia](https://law.justia.com/cases/federal/appellate-courts/ca9/17-16783/17-16783-2022-04-18.html)
- [Ryanair v. PR Aviation — CJEU](https://curia.europa.eu/juris/document/document.jsf?docid=161388&doclang=EN)
- [Meta v. BrandTotal — Courthouse News](https://www.courthousenews.com/judge-rules-brandtotals-data-harvesting-violates-metas-terms-of-use-and-anti-hacking-laws/)

### Türkiye Mevzuat ve Kararlar
- [Rekabet Kurulu Sahibinden API Kararı](https://mfylegal.av.tr/haberler/sahibinden-api-veri-tasima-karari-26-06-2025/)
- [Web Scraping ve Haksız Rekabet — Göksu Safi Işık](https://www.goksusafiisik.av.tr/tr/publications/2025-summer-issue/web-scraping-eyleminin-haksiz-rekabet-acisindan-degerlendirilmesi?id=510)
- [Veri Kazıma ve KVKK — KP Veri](https://kpveri.com/veri-kazima-data-scraping-faaliyeti-sirasinda-kvkk-kapsaminda-nelere-dikkat-edilmelidir/)
- [KVKK Kurul Kararı 2017/61](https://www.kvkk.gov.tr/Icerik/4113/2017-61)
- [TCK 243 Analizi](https://ayboga.av.tr/tck-243-bilisim-sistemine-girme-sucu/)
- [KVKK İşlenme Şartları](https://www.kvkk.gov.tr/Icerik/4190/Kisisel-Verilerin-Islenme-Sartlari)

### Yasal Veri Alternatifleri
- [TCMB Konut Fiyat Endeksi](https://www.tcmb.gov.tr/wps/wcm/connect/tr/tcmb+tr/main+menu/istatistikler/reel+sektor+istatistikleri/konut+fiyat+endeksi/)
- [TÜİK Veri Portalı](https://data.tuik.gov.tr/)
- [Endeksa Ürünler](https://www.endeksa.com/tr/urunler/)
