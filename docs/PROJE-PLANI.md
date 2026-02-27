# Emlak Teknoloji Platformu — Proje Planı

**Tarih:** 2026-02-20
**Versiyon:** 1.0
**Hazırlayan:** Stratejik Değerlendirme Heyeti (Claude Stratejik Planlayıcı + Gemini Ürün Yöneticisi + Codex Operasyonel Planlayıcı)
**Yöntem:** Delphi İteratif Yakınsama — 4 Tur
**Durum:** GO (Koşullu) — Kullanıcı onayı bekleniyor

---

## 1. Yönetici Özeti

Emlak Teknoloji Platformu, Türkiye emlak sektörünün **veri + operasyon + tahmin** üçlüsünü tek çatıda birleştiren ilk entegre SaaS çözümdür. İstanbul merkezli butik emlak ofislerini hedefleyen platform; AI destekli değerleme, bölge analizi, müşteri-portföy eşleştirme, portföy paylaşım ağı, ilan asistanı ve çift kanallı mesajlaşma (Telegram + WhatsApp) sunarak emlakçıları kurumsal düzeyde donanımlı hale getirir. Temel farklılaşma **freemium ile hacim → hacimden veri → veriden AI → AI'dan değer → değerden gelir** döngüsü üzerine kuruludur. Mevcut rakiplerden (Endeksa, Arveya, Fizbot, REIDIN) hiçbiri bu üçlüyü tek platformda birleştirmemektedir.

**Hedef Pazar:** Türkiye emlak SaaS pazarı (~800M-1.2 milyar TL), birincil hedef İstanbul butik ofisler (3-15 danışmanı)
**Temel Farklılaşma:** Veri + Operasyon + Tahmin birleşimi, Telegram Mini App ile sektör ilki UX, kademeli portföy paylaşım ağı
**Nihai Karar:** **GO** — İki katmanlı MVP (Alpha + Beta), 38 hafta, ₺8.2-9.4M net bütçe (orkestratör ile)

---

## 2. Vizyon ve Misyon

### Vizyon
Türkiye emlak ekosisteminin **veri omurgası** olmak. Emlak profesyonellerinin karar süreçlerini sezgiden veriye, tahminlerini modelden gerçek zamanlı sinyal analizlerine dönüştüren, sektörün **tek entegre zeka platformu** haline gelmek.

### Misyon
Emlak danışmanlarına, yatırımcılara ve ofislere; fiyatlama, portföy yönetimi, müşteri eşleştirme, ilan optimizasyonu ve yatırım analizi konularında **AI destekli, gerçek zamanlı, kullanılabilir araçlar** sunarak sektörün dijital dönüşümünü hızlandırmak. Her ölçekteki emlak profesyoneline (bireysel danışmandan kurumsal zincire) erişelebilir fiyatla hizmet vermek.

### Stratejik Hedefler

| Vade | Hedef | Ölçüm |
|------|-------|-------|
| **Kısa Vade (0-12 ay)** | MVP-Alpha + Beta lansmansı, 1.500 ücretli kullanıcı, İstanbul hakimiyeti | MRR ~973K TL, NPS >40, churn <%10 |
| **Orta Vade (1-3 yıl)** | Türkiye geneli yayılım, 5.000+ ücretli ofis, B2B API geliri | ARR >50M TL, 5+ şehir, 1+ kurumsal anlaşma |
| **Uzun Vade (3-5 yıl)** | Sektör standardı platform, MENA genişlemesi, veri ürünleri | ARR >200M TL, uluslararası pazar, veri marketplace |

---

## 3. Pazar Analizi

### 3.1 Türkiye Emlak SaaS Pazarı Büyüklüğü

| Gösterge | Değer | Kaynak/Tahmin |
|----------|-------|---------------|
| Türkiye yıllık konut satışı | ~1.4M adet | TÜİK 2025 |
| Tahmini toplam işlem hacmi | ~2.5 trilyon TL | Ortalama konut fiyatı x satış adedi |
| Kayıtlı emlak ofisi sayısı | ~40.000+ | TOBB/Meslek odaları |
| Aktif emlak danışmanı sayısı | ~120.000-150.000 | Sektör tahmini |
| PropTech pazarı (yazılım+veri) | ~800M-1.2 milyar TL | Endeksa+REIDIN+CRM+portal gelirleri |
| Dijitalleşmiş ofis oranı (CRM kullanan) | ~%15-20 | Arveya blog verileri referans |
| Yıllık büyüme potansiyeli | %25-35 | Global PropTech trendleri |

**Kritik gözlem:** 40.000+ emlak ofisinin %80'inden fazlası hala Excel, WhatsApp ve telefon rehberiyle çalışıyor. EİDS zorunluluğu bu dijitalleşme dalgasını hızlandıracak.

### 3.2 TAM / SAM / SOM

| Seviye | Tanım | Hesaplama | Değer |
|--------|-------|-----------|-------|
| **TAM** | Tüm Türkiye emlak teknoloji harcamaları | 40.000 ofis x ort. 30.000 TL/yıl | **~2 milyar TL/yıl** |
| **SAM** | CRM + veri analitiği + ilan yönetimi SaaS | ~8.000 dijital ofis x 12.000 TL/yıl | **~200M TL/yıl** |
| **SOM** | İlk 3 yılda ulaşılabilir pazar payı | 800-1.200 ofis x 9.600 TL/yıl | **~10-12M TL/yıl** |

### 3.3 Rakip Analizi Tablosu

| Platform | Güçlü Yanları | Zayıf Yanları | Fiyat | Bizim Farkımız |
|----------|---------------|---------------|-------|----------------|
| **Endeksa** | Kapsamlı değerleme motoru, geniş veri seti, emsal raporu | Pahalı (kurumsal odak), CRM yok, mobil zayıf | 2.000-15.000 TL/ay | Freemium + CRM entegrasyonu + AI tahmin |
| **REIDIN** | Profesyonel veri, uluslararası karşılaştırma | Çok pahalı, sadece enterprise, karışık UI | 5.000-50.000 TL/ay | Erişelebilir fiyat + operasyonel araçlar |
| **Arveya** | Yerli CRM, ilan entegrasyonu, makul fiyat | Veri analitiği yok, AI yok | 500-2.000 TL/ay | Veri katmanı + AI tahmin + ağ etkisi |
| **Fizbot** | Dijital asistan, çok kanallı ilan dağıtımı | Değerleme yok, sınırlı analitik | 300-1.500 TL/ay | Veri zekası + CRM + AI birleşimi |
| **Sahibinden** | Devasa kullanıcı tabanı, marka bilinirliği | Profesyonel araç değil, veri analizi yok | İlan başı 500-3.000 TL | B2B profesyonel araç seti |

### 3.4 Boşluk Analizi

| Boşluk | Mevcut Durum | Bizim Çözümümüz |
|--------|-------------|-----------------|
| **Orta Segment Boşluğu** | Endeksa/REIDIN pahalı, Arveya/Fizbot sınırlı | 399 TL giriş bariyeri, premium içerik |
| **Veri + İş Akışı Entegrasyonu** | Emlakçı 5+ farklı araç kullanıyor | Tek platform: değerleme + CRM + ilan + mesajlaşma |
| **AI-Native Yaklaşım** | Mevcut platformlar AI'yi "eklenti" olarak kullanıyor | AI ürünün çekirdeğinde: değerleme, ilan, eşleştirme, fiyat önerisi |
| **EİDS Uyum** | Hiçbir platform EİDS iş akışı sunmuyor | Hibrit EİDS doğrulama (manuel + gelecekte oto) |
| **Portföy Paylaşım Ağı** | WhatsApp gruplarıyla kaotik | Yapılandırılmış, güvenli, komisyon mekanizmalı ağ |
| **Mobil-Öncelikli** | Çoğu çözüm masaüstü odaklı | Telegram Mini App + responsive web |

---

## 4. Hedef Kullanıcı ve Personalar

### 4.1 Birincil Persona: Emlak Danışmanı — "Hakan"

| Özellik | Detay |
|---------|-------|
| **Yaş** | 28-45 |
| **Deneyim** | 1-5 yıl |
| **Portföy** | 10-30 aktif ilan |
| **Müşteri** | 20-50 aktif alıcı/kiracı |
| **Gelir** | Aylık 15.000-40.000 TL komisyon |
| **Teknoloji** | Akıllı telefon, WhatsApp, Sahibinden |
| **Bütçe** | Aylık 200-500 TL yazılım harcaması |
| **Motivasyon** | Daha fazla satış kapatmak, profesyonel görünmek, zamandan tasarruf |

**Temel Ağrı Noktaları:**
1. "Bu ev kaça satılır?" sorusuna güvenilir cevap verememe
2. Müşteri takibinin kopması (Excel/not defteri kayboluyor)
3. İlan hazırlamak ve güncellemek saatler sürüyor
4. Potansiyel müşteriye hızlı dönüş yapamama

### 4.2 İkincil Persona: Ofis Sahibi / Broker — "Elif"

| Özellik | Detay |
|---------|-------|
| **Yaş** | 35-55 |
| **Deneyim** | 5-15 yıl |
| **Ekip** | 3-10 danışmanı |
| **Portföy** | 50-200 aktif ilan |
| **Müşteri** | 100-500 aktif kayıt |
| **Gelir** | Ofis aylık 80.000-300.000 TL ciro |
| **Teknoloji** | CRM denemiş ama bırakmış, Excel ağırlıklı |
| **Bütçe** | Aylık 500-2.000 TL |
| **Motivasyon** | Ekibi verimli yönetmek, kayıp müşteriyi azaltmak |

**Temel Ağrı Noktaları:**
1. Hangi danışmanı hangi müşteriyle ne konuştu bilinmiyor
2. Aynı müşteriye iki danışmanı aynı anda ulaşıyor (çakışma)
3. İlan portallarına tek tek giriş yapılıyor
4. Danışmanı performansını ölçemiyor, komisyon hesabı karmaşık

### 4.3 Kullanıcı Ağrı Noktaları Tablosu

| Ağrı Noktası | Hakan (Danışmanı) | Elif (Broker) | Çözüm Özelliğimiz |
|-------------|-------------------|---------------|-------------------|
| Fiyat belirleyememe | "Sahibinden'den bakıp tahmin ediyorum" | "Danışmanılarım tutarsız fiyat veriyor" | AI Değerleme + Emsal Analiz |
| Müşteri kaybetme | "Not ettim ama kaybettim" | "Kim ne konuştu bilmiyorum" | CRM + Otomatik Eşleştirme |
| İlan hazırlama süresi | "Her ilan 1-2 saat" | "10 danışmanı x 1 saat = gün gidiyor" | AI İlan Asistanı |
| Portföy paylaşımı | "WhatsApp'ta kayboluyor" | "Diğer ofislerle koordinasyon yok" | Portföy Paylaşım Ağı |
| Mobil erişim | "Sahada bilgiye eriisemiyorum" | "Danışmanılarım sahada kopuk" | Telegram Mini App |
| EİDSuyumu | "Sistemi bilmiyorum" | "Her ilana tek tek giriyoruz" | EİDS Hibrit Doğrulama |

---

## 5. Ürün Stratejisi — İki Katmanlı MVP

### 5.1 MVP-Alpha (Hafta 11-24)

Çalışan, gelir üreten, tek başına yaşayabilen ürün. 9 temel özellik.

| # | Özellik | Açıklama | Fiyat Kademesi |
|---|---------|----------|:--------------:|
| 1 | **AI Değerleme Motoru + Emsal Analiz** | Adres/ada-parsel girişiyle AI tabanlı fiyat tahmini, emsal karşılaştırma, PDF rapor | Starter+ |
| 2 | **Bölge Analiz Kartları** | Mahalle/ilçe bazında demografi, ort. m2 fiyatı, kira çarpanı, arz-talep, imar durumu | Starter+ |
| 3 | **Harita Entegrasyonu** | Portföy ve emsal görünümü, POİ (okul, hastane, metro), isii haritası | Starter+ |
| 4 | **Deprem Risk Skoru** | AFAD + Kandıllı + belediye verileriyle bölge bazlı deprem risk değerlendirmesi | Starter+ |
| 5 | **CRM (Müşteri-Portföy Eşleştirme)** | Müşteri kayıt, iletişim takip, not, etiket, otomatik eşleştirme bildirimi | Starter+ |
| 6 | **AI İlan Asistanı** | LLM ile SEO uyumlu ilan metni, temel fotoğraf iyileştirme (aydınlatma, HDR) | Pro+ |
| 7 | **Portföy Vitrin + Temel Eşleştirme** | Pasif portföy sergileme + temel alıcı-satıcı eşleştirme motoru | Pro+ |
| 8 | **Kredi Hesaplayıcı** | Tutar, vade, faiz → aylık taksit tablosu, banka karşılaştırma | Starter+ |
| 9 | **Telegram Bot + Mini App** | Bot API ile bildirimler, CRM etkileesiimleri, Mini App ile dashboard | Tüm kademeler |

**Alpha Lansmanı Hedefi:**
- 30+ seed ofis aktif
- Starter + Pro kademeleri açık
- Telegram üzerinden tam deneyim
- WhatsApp: Click-to-chat / manuel link (BSP gerektirmez, Starter/Pro kapsamı)

### 5.2 MVP-Beta (Hafta 25-38)

Ekosistem tamamlama, Elite kademe, tam mesajlaşma. 6 ek özellik.

| # | Özellik | Açıklama | Fiyat Kademesi |
|---|---------|----------|:--------------:|
| 10 | **WhatsApp Cloud API (Elite)** | BSP entegrasyon (360dialog), template mesajlar, çift yönlü iletişim, müşteri vitrini. *Starter/Pro: click-to-chat (manuel link) Alpha'da mevcut — BSP gerektirmez.* | Elite |
| 11 | **EİDS Hibrit Doğrulama** | Manuel numara giriş + OCR belge tarama + doğrulanmış ilan rozeti | Pro+ |
| 12 | **Portföy Paylaşım Ağı (Aktif)** | Gelişmiş eşleştirme + temel komisyon akışı + moderasyon | Pro+ |
| 13 | **Çoklu Site Scraping** | Sahibinden, Hepsiemlak, Emlakjet veri toplama (koşullu — ortaklık/hukuki izin) | Elite |
| 14 | **Gelişmiş AI Fotoğraf** | Virtual staging, dekorasyon önerisi, geniş açı düzeltme, nesne iyileştirme | Elite |
| 15 | **Ofis Yönetim Paneli + Raporlama** | Çoklu kullanıcı, danışmanı performans KPI, komisyon hesabı, ekip dashboard | Elite |

---

## 6. Özellik Detayları

### 6.1 AI Değerleme Motoru + Emsal Analiz

| Alan | Detay |
|------|-------|
| **Ne Yapar** | Bir adres veya ada/parsel girildiğinde, yakın çevredeki gerçekleşmiş satışlar, aktif ilanlar ve AI değerleme raporunu tek sayfada gösterir. İlan fiyatı vs. gerçek işlem fiyatı karşılaştırması yapar. Güven aralığı (%80 olasılıkla X-Y TL arası) sunar. |
| **Neden Önemli** | Emlakçınin #1 ağrı noktası: "Bu ev kaça satılır?" Güvenilir cevap, profesyonellik algıisi yaratır ve satış kapatma oranını arttırır. |
| **Teknik Gereksinimler** | LightGBM/XGBoost ensemble model, TÜİK + TCMB + belediye + kullanıcı girişi veri pipeline, PostGIS spatial sorgular, PDF rapor üretici |
| **Kademe** | Starter: 10 sorgu/ay, Pro: 100 sorgu/ay, Elite: sınırsız |

### 6.2 Bölge Analiz Kartları

| Alan | Detay |
|------|-------|
| **Ne Yapar** | Her mahalle/ilçe için demografik yapı, ortalama m2 fiyatı, kira çarpanı, arz-talep oranı, ulaşım skoru, okul/hastane yoğunluğu, deprem risk skoru, imar durumu bilgilerini görsel kartlarda sunar. A vs B mahalle karşılaştırması. |
| **Neden Önemli** | Danışmanılar ve yatırımcılar için bölgeler arası karşılaştırma en sık ihtiyaç. Profesyonel sunum aracı. |
| **Teknik Gereksinimler** | TÜİK demografik veri, TCMB fiyat endeksi, belediye imar bilgisi, OpenStreetMap POİ, cache mekanizması |
| **Kademe** | Starter: temel kart, Pro: detaylı + karşılaştırma, Elite: trend tahmin eklentisi |

### 6.3 Harita Entegrasyonu

| Alan | Detay |
|------|-------|
| **Ne Yapar** | Tüm portföy ve emsalleri harita üzerinde gösterir. POİ katmanları (okul, hastane, metro, market), isii haritası (fiyat yoğunluk), bölge poligonları. |
| **Neden Önemli** | Sahada çalışan emlakçı için konum bazlı görselleştirme vazgeçilmez. Müşteriye gösterim sırasında profesyonel sunum. |
| **Teknik Gereksinimler** | MapLibre GL JS + OpenStreetMap, PostGIS spatial queries, Google Maps Places API |
| **Kademe** | Tüm kademeler (Starter'da sınırlı katman) |

### 6.4 Deprem Risk Skoru

| Alan | Detay |
|------|-------|
| **Ne Yapar** | AFAD deprem tehlike haritası, Kandıllı verisi, belediye zemin etüdü bilgileri birleştirilerek bölge bazlı deprem risk skoru üretir (0-100). Bina yaşı ve kat sayısıyla birleşik "Güvenlik Skoru" sunar. |
| **Neden Önemli** | 2023 deprem sonrası Türkiye'de deprem hassasiyeti çok yüksek. Hiçbir Türk emlak platformu bunu sunmuyor — güçlü diferansiyatör. |
| **Teknik Gereksinimler** | AFAD WMS/REST API, Kandıllı verileri, belediye zemin etüdü (varsa), PGA hesaplama, cache |
| **Kademe** | Starter+ (tüm kademeler) |

### 6.5 CRM (Müşteri-Portföy Eşleştirme)

| Alan | Detay |
|------|-------|
| **Ne Yapar** | Müşteri kayıt, iletişim takip, not, etiket, arama kriterleri (bütçe, oda, konum, metro). Yeni portföy eklendiğinde otomatik bildirim. Müşteri isii haritası (sıcak/soğuk lead). |
| **Neden Önemli** | Emlakçınin günlük operasyonel ihtiyacı. Müşteri kaybını azaltır, eşleştirme önerisi ile satış kapatma oranını arttırır. |
| **Teknik Gereksinimler** | CRUD + bildirim sistemi + eşleştirme algoritması (kural tabanlı MVP'de, ML ile gelişecek), Telegram entegrasyonu |
| **Kademe** | Starter: 50 müşteri, Pro: 500 müşteri, Elite: sınırsız + ekip CRM |

### 6.6 AI İlan Asistanı (Metin + Temel Fotoğraf İyileştirme)

| Alan | Detay |
|------|-------|
| **Ne Yapar** | Mülk özelliklerini girip LLM ile SEO uyumlu, çekici ilan metni üretme. Çoklu portal formatında export. Temel fotoğraf iyileştirme: aydınlatma düzeltme, perspektif düzeltme, HDR efekti. |
| **Neden Önemli** | Emlakçınin en büyük zaman kaybı: ilan hazırlama. AI ile 1-2 saatlik iş 5 dakikaya düşer. Hemen hissedilen somut değer. |
| **Teknik Gereksinimler** | LLM API (Claude/GPT) metin için, görüntü işleme modeli (hafif CNN) fotoğraf için, multi-format export |
| **Kademe** | Pro: 20 ilan/ay + 50 foto/ay, Elite: sınırsız |

### 6.7 Portföy Paylaşım Ağı (Vitrin → Eşleştirme → Komisyon)

| Alan | Detay |
|------|-------|
| **Ne Yapar** | 3 katmanlı aktivasyon: (1) Pasif Vitrin — emlakçı portföyünü sergiler, aranabilir; (2) Eşleştirme Motoru — "müşterim var, ilan arıyorum" alıcı-satıcı eşleştirme; (3) Komisyon Akışı — komisyon anlaşma, çapraz satış. |
| **Neden Önemli** | WhatsApp gruplarındaki kaotik paylaşımı yapılandırır. Ağ etkisi = en güçlü moat. Her yeni ofis ağın değerini arttırır. |
| **Teknik Gereksinimler** | Eşleştirme algoritması, bildirim sistemi, gizlilik/görünürlük ayarları, Telegram grup entegrasyonu, moderasyon paneli |
| **Kademe** | Pro: ilan paylaşma + eşleştirme, Elite: öncelikli eşleştirme + "Süper-Agent" rozeti |

### 6.8 Kredi Hesaplayıcı

| Alan | Detay |
|------|-------|
| **Ne Yapar** | Tutar, vade, faiz oranı girerek aylık taksit tablosu oluşturma. Banka faiz karşılaştırması. Amortisman tablosu. |
| **Neden Önemli** | Sahada müşteriye anında kredi hesabı göstermek, alım kararını kolaylaştırır. Quick win — düşük efor, yüksek kullanım. |
| **Teknik Gereksinimler** | Basit matematik formülleri, banka faiz verisi (TCMB örtalama + scraping), responsive UI |
| **Kademe** | Starter+ (tüm kademeler) |

### 6.9 Telegram Bot + Mini App

| Alan | Detay |
|------|-------|
| **Ne Yapar** | Telegram Bot API ile bildirimler (yeni eşleştirme, fiyat değişikliıği, lead), inline keyboard ile hızlı CRM eylemleri, Mini App ile dashboard görünümü, dosya/konum paylaşımı. |
| **Neden Önemli** | Ücretsiz, anında deploy, sıfır dış bağımlılık. Rate limit pratiikte yok. Mini App ile uygulama benzeri deneyim Telegram içinden. Türkiye emlak SaaS'ta ilk. |
| **Teknik Gereksinimler** | grammy/python-telegram-bot, webhook altyapısı, Mini App (responsive HTML5), auth token köprüsü |
| **Kademe** | Starter: temel (sorgu), Pro: tam (veri girişi + rapor), Elite: yönetici modu |

### 6.10 WhatsApp Entegrasyonu (Kademeli)

| Alan | Detay |
|------|-------|
| **Ne Yapar** | **Starter/Pro (Alpha):** Portföy kartından click-to-chat butonu → native WhatsApp açılır, manuel link oluşturucu (BSP gerektirmez, maliyet = 0). **Elite (Beta):** BSP (360dialog) Cloud API entegrasyonu → template mesajlar, çift yönlü iletişim, randevu hatırlatma, webhook ile delivery/read takibi. |
| **Neden Önemli** | Türkiye'de son kullanıcıda %85+ WhatsApp penetrasyonu. Müşteriye ulaşmanın en doğal kanalı. Click-to-chat tüm planlara sıfır maliyetle WhatsApp erişimi sağlar; Cloud API ise Elite'te otomasyon ve mesaj takibi getirir. |
| **Teknik Gereksinimler** | **Starter/Pro:** `https://wa.me/?text=...` link oluşturucu, portföy kartı paylaşım butonu. **Elite:** BSP entegrasyonu (360dialog), template mesaj yönetimi, webhook, opt-in/opt-out, mesaj kuyruğu, kota kontrolü |
| **Kademe** | Starter/Pro: click-to-chat / manuel link (0 TL), Elite: Cloud API (BSP) tam entegrasyon (aylık 50 msg dahil) |

### 6.11 EİDS Hibrit Doğrulama

| Alan | Detay |
|------|-------|
| **Ne Yapar** | Manuel EİDS belge numarası girişi + OCR ile belge tarama doğrulama + "Doğrulanmış İlan" rozeti. Resmi API açıldığında otomatik geçiş için hazır mimari. |
| **Neden Önemli** | EİDS yasal zorunluluk. Kolaylaştıran platform, uyum aracı olarak konumlanır. "Ceza yemek istemiyorsan bizi kullan" güçlü satış argümanı. |
| **Teknik Gereksinimler** | OCR motor (Tesseract/Cloud Vision), form doğrulama, rozet sistemi, audit log, EİDS uyumlu veri yapısı |
| **Kademe** | Pro: manuel giriş + OCR, Elite: öncelikli doğrulama + bulk işlem |

### 6.12 Çoklu Site Scraping (Koşullu)

| Alan | Detay |
|------|-------|
| **Ne Yapar** | Sahibinden, Hepsiemlak, Emlakjet'ten aggregate piyasa verisi toplama. Fiyat trendi, mahalle bazlı istatistik, ilan izleme. |
| **Neden Önemli** | Kapsamlı pazar görünümü. Değerleme modeli ve bölge analizleri güçlendirir. Hiçbir Türk emlak SaaS'ı çoklu site aggregasyonu sunmuyor. |
| **Teknik Gereksinimler** | Scrapy/Playwright parserları, anti-scraping önlemleri (proxy pool, İP rotasyonu), veri normalizasyon, deduplication |
| **Kademe** | Elite (tam scraping), Pro (sınırlı istatistik) |
| **Koşul** | Hukuki araştırma + ortaklık görüşmesi sonucuna bağlı. Ortaklık sağlanırsa resmi API, sağlanmazsa sınırlı istatistik modu |

### 6.13 Gelişmiş AI Fotoğraf

| Alan | Detay |
|------|-------|
| **Ne Yapar** | Virtual staging (boş odaya mobilya ekleme), dekorasyon önerisi, geniş açı simülasyonu, nesne silme/ekleme, profesyonel portfolio oluşturma. |
| **Neden Önemli** | İlan fotoğrafları satış hızını %20-30 etkiler. Profesyonel fotoğrafçı tutamayan emlaiciye büyük avantaj. |
| **Teknik Gereksinimler** | Stable Diffusion/DALL-E API veya self-hosted model, GPU compute, görüntü islleme pipeline |
| **Kademe** | Elite (sınırsız), Pro (20 foto/ay) |

### 6.14 Akıllı Fiyat Önerisi

| Alan | Detay |
|------|-------|
| **Ne Yapar** | Değerleme motorunun uzantısı: "En hızlı satılacak fiyat" vs "Maksimum getiri fiyatı" arasındaki optimal noktayı gösterir. Satış süresi tahmini (survival analysis). |
| **Neden Önemli** | Değerlemenin ötesinde strateji önerisi. Satıcıyı ikna etme aracı. Hiçbir rakip bunu yapmıyor. |
| **Teknik Gereksinimler** | Survival Analysis + LightGBM, bölge arz/talep verisi, sezonalite, ilan kalitesi skoru |
| **Kademe** | Pro+ |

### 6.15 Ofis Yönetim Paneli + Raporlama

| Alan | Detay |
|------|-------|
| **Ne Yapar** | Çoklu kullanıcı yönetimi, danışmanı performans KPI'ları (satış hunisi, gösteriminler, kapatmalar), komisyon hesabı, ekip dashboard, otomatik haftalık rapor. |
| **Neden Önemli** | Ofis sahibinin "ofisin nabzını tek ekrandan görmesi". Franchise ofislere karşı rekabet avantajı. |
| **Teknik Gereksinimler** | Multi-tenant mimari, RBAC (rol bazlı erişim), rapor üretici, KPI hesaplama motoru |
| **Kademe** | Elite |

---

## 7. İletişim Stratejisi — Telegram + WhatsApp

### 7.1 Kanal Stratejisi

| Kanal | Rol | Kullanım Alanı | Zamanlama |
|-------|-----|----------------|-----------|
| **Telegram** | Birincil (Operasyonel Merkez, B2B) | Danışmanı sisteme veri girerken, rapor alırken, portföy ararken, diğer emlakçılarla paylaşım | Alpha'da TAM |
| **WhatsApp** | İkincil (Müşteri Vitrini, B2C) | Müşteriye ilan paylaşımı, yer gösterme konumu, randevu hatırlatma, lead yakalama | Beta'da TAM |
| **SMS** | Fallback | Kritik bildirimler (randevu, ödeme) | Her iki fazda |
| **E-posta** | Raporlama | Haftalık rapor, fatura, kampanya | Her iki fazda |

### 7.2 Kanal Karşılaştırma Tablosu

| Boyut | Telegram | WhatsApp | Stratejik Sonuç |
|-------|----------|----------|-----------------|
| **API Maliyeti** | ÜCRETSİZ — Bot API tamamen bedava | Meta BSP: mesaj başı ~0.05-0.15 TL | Telegram COGS'u dramatik düşürür |
| **Onay Süreci** | YOK — Bot anında oluşturulur | 4-12 hafta Meta BSP onayı | Telegram'da dış bağımlılık sıfır |
| **Rate Limit** | Pratikte yok (30 mesaj/sn) | Ciddi — 1000 mesaj/gün, template zorunlu | Yüksek hacimli bildirimler Telegram'dan |
| **Mini App** | TAM HTML5 uygulama çalıştırma | Yok | Dashboard Telegram içinden açılabilir |
| **Bot Ekosistemi** | Zengin — inline keyboard, callback, dosya, konum | Sınırlı — template mesajlar | CRM etkileşimleri Telegram'da esnek |
| **Penetrasyon (Türkiye)** | ~%35-40 aktif | ~%85+ aktif | WhatsApp mutlaka olmalı ama Telegram'ı bilenler sever |
| **Emlakçı Alışkanlığı** | Daha az yaygın | Zaten iş için kullanıyor | Tüm planlar: click-to-chat; Elite: Cloud API otomasyon |

### 7.3 Unified Messaging Gateway Mimarisi

```
┌─────────────────────────────────────────────────┐
│              MESAJLAŞMA GATEWAY                  │
│         (Unified Messaging Service)              │
├─────────────┬───────────────────────┬────────────┤
│  TELEGRAM   │     WHATSAPP          │  SMS/EMAIL │
│  Bot API    │     Cloud API (Elite) │  (Fallback)│
│  (Ücretsiz) │     Click-to-chat     │            │
│  Mini App   │     (Starter/Pro: 0TL)│            │
├─────────────┴───────────────────────┴────────────┤
│              KANAL YÖNETİCİSİ                     │
│  • Kullanıcı tercih yönetimi                     │
│  • Maliyet optimizasyonu (Telegram öncelikli)    │
│  • Fallback zinciri: Telegram→WhatsApp→SMS→Email │
│  • Kanal-agnostik mesaj formatı                  │
└─────────────────────────────────────────────────┘
```

**Mimarı Prensip:** Mesajlaşma servisini **kanal-agnostik** tasarla. Mesajın içeriği tek yerde üretilir, kanal adaptörleri sadece format dönüşümü yapar. Bugün 2 kanal, yarın 5 kanal olabilir.

### 7.4 Faz Bazlı Kanal Aktivasyonu

| Faz | Telegram | WhatsApp | Neden |
|-----|----------|----------|-------|
| **MVP-Alpha** | TAM — Bot + Mini App + Bildirimler | Click-to-chat / manuel link (Starter/Pro, BSP gerektirmez) | Telegram'da dış bağımlılık yok. WhatsApp click-to-chat sıfır maliyet. BSP paralel başvuru |
| **MVP-Beta** | Gelişmiş — Grup entegrasyonu, gelişmiş Mini App | Cloud API TAM — BSP onaylı, template mesajlar, çift yönlü (Elite) | BSP bu zamana kadar onaylı olacak. Cloud API sadece Elite. |
| **Faz 2+** | Kanal marketplace, 3. parti bot | Flows, katalog entegrasyonu | Ekosistem genişletme |

### 7.5 Fallback Zinciri

```
Telegram (birincil) → WhatsApp (ikincil) → SMS (acil) → E-posta (raporlama)
```

Her kullanıcının tercih ettiği kanal seçimi vardır. Teslimat başarısız olursa bir sonraki kanala otomatik geçiş yapılır.

---

## 8. Fiyatlandırma Stratejisi

### 8.1 Paket Detayları

| Özellik / Paket | **STARTER (399 TL/ay)** | **PRO (799 TL/ay)** | **ELİTE (1.499 TL/ay)** |
|:---|:---:|:---:|:---:|
| **Kullanıcı** | 1 Danışmanı | 3 Danışmanı | 10 Danışmanı (Ofis) |
| **Portföy Limiti** | 20 | 100 | Sınırsız |
| **AI Değerleme** | 10 sorgu/ay | 100 sorgu/ay | Sınırsız |
| **Bölge Analiz** | Temel kart | Detaylı + karşılaştırma | Trend tahmin eklentisi |
| **AI İlan Asistanı** | — | 20 ilan/ay + 50 foto/ay | Sınırsız |
| **CRM** | 50 müşteri | 500 müşteri | Sınırsız + ekip CRM |
| **Portföy Ağı Erişimi** | Sadece görüntüleme | İlan paylaşma + eşleştirme | Öncelikli eşleştirme + Süper-Agent rozeti |
| **EİDS** | — | Manuel giriş + OCR | Öncelikli doğrulama + bulk |
| **Telegram Bot** | Temel (sorgu) | Tam (veri girişi + rapor) | Yönetici modu (ekip takibi) |
| **WhatsApp** | Click-to-chat (native link) | Click-to-chat + manuel link oluşturucu | Cloud API (BSP) — tam otomasyon (aylık 50 msg dahil) |
| **Scraping** | — | Sınırlı istatistik | Tam erişim |
| **AI Fotoğraf** | — | 20 foto/ay | Sınırsız |
| **Ofis Yönetim Paneli** | — | — | Tam erişim |
| **Deprem Risk Skoru** | Temel | Detaylı | Detaylı + tarihçe |
| **Kredi Hesaplayıcı** | Temel | Gelişmiş | Gelişmiş |

### 8.2 COGS Analizi (Kullanıcı Başı Aylık)

| Maliyet Kalemi | Starter (399) | Pro (799) | Elite (1.499) | Açıklama |
|----------------|:---:|:---:|:---:|----------|
| Sunucu/altyapı | 15 TL | 25 TL | 40 TL | Ölçeklenen kullanıcı başı compute |
| AI Değerleme API | 20 TL | 35 TL | 50 TL | GPT/Claude API — sınırlı vs sınırsız |
| AI İlan + Fotoğraf | — | 30 TL | 60 TL | Fotoğraf GPU yoğun, Pro'da limitli |
| Telegram Bot | 0 TL | 0 TL | 0 TL | **Tamamen ücretsiz** |
| WhatsApp API | 0 TL | 0 TL | 45 TL | Starter/Pro: click-to-chat (BSP yok, maliyet 0). Elite: Cloud API template mesajlar + BSP ücreti |
| Scraping proxy | — | 15 TL | 30 TL | Residential proxy pool payı |
| EİDS doğrulama | 5 TL | 5 TL | 5 TL | OCR/işlem maliyeti |
| Veri depolama | 5 TL | 10 TL | 15 TL | Fotoğraf, doküman, rapor |
| Destek maliyeti | 5 TL | 10 TL | 20 TL | Otomatik + insan destek oranı |
| **TOPLAM COGS** | **50 TL** | **130 TL** | **240 TL** | |
| **Brüt Kar** | **349 TL** | **669 TL** | **1.259 TL** | |
| **Brüt Marj** | **%87.5** | **%83.7** | **%84.0** | |

**Telegram + Click-to-chat Etkisi:** Starter/Pro'da WhatsApp Cloud API yerine click-to-chat kullanılması BSP maliyetini sıfırlar. Elite'te bile Telegram-first stratejisi WhatsApp mesaj maliyetini düşürür (Telegram varsayılan kanal, WhatsApp sadece kullanıcı tercihi veya Telegram erişilemezse). 1.000 Elite kullanıcıda Telegram-first = yıllık ~300.000 TL WhatsApp API tasarrufu.

### 8.3 Ünit Economics

| Metrik | Değer | Sağlık Durumu |
|--------|:-----:|:---:|
| **ARPU** | 649 TL/ay | Sağlıklı |
| **Ağırlıklı COGS** | ~120 TL/ay | Düşük (Telegram etkisi) |
| **Brüt Kar/Kullanıcı** | ~529 TL/ay | Güçlü |
| **Brüt Marj** | ~%81.5 | SaaS ortalamasının üstünde |
| **CAC** | 3.000-3.500 TL | Orta — Seed stratejisi ile düşürülebilir |
| **LTV (24 ay, %85 retention)** | ~12.700 TL | Güçlü |
| **LTV/CAC** | **3.6-4.2x** | Sağlıklı (3x+ hedef) |
| **Payback Periyodu** | 5.5-6.5 ay | Makul |
| **MRR (Yıl 1 sonu)** | ~973K TL | Yıllık ~11.7M TL ARR |

---

## 9. Gelir Projeksiyonu

### 9.1 Yıl 1 Hedef Senaryo: 1.500 Ücretli Kullanıcı

| Kademe | Dağılım | Kullanıcı | Aylık Gelir | Yıllık Gelir |
|--------|:---:|:---:|:---:|:---:|
| Starter (399 TL) | %55 | 825 | 329.175 TL | 3.950.100 TL |
| Pro (799 TL) | %35 | 525 | 419.475 TL | 5.033.700 TL |
| Elite (1.499 TL) | %10 | 150 | 224.850 TL | 2.698.200 TL |
| **TOPLAM** | **%100** | **1.500** | **973.500 TL** | **11.682.000 TL** |

### 9.2 Konservatif Senaryo: 800 Kullanıcı

| Kademe | Dağılım | Kullanıcı | Aylık Gelir | Yıllık Gelir |
|--------|:---:|:---:|:---:|:---:|
| Starter (399 TL) | %60 | 480 | 191.520 TL | 2.298.240 TL |
| Pro (799 TL) | %30 | 240 | 191.760 TL | 2.301.120 TL |
| Elite (1.499 TL) | %10 | 80 | 119.920 TL | 1.439.040 TL |
| **TOPLAM** | **%100** | **800** | **503.200 TL** | **6.038.400 TL** |

**Konservatif ARPU:** 629 TL/ay

### 9.3 MRR / ARR Projeksiyonu

| Ay | Hedef Senaryo MRR | Konservatif MRR |
|:---:|:---:|:---:|
| 6 (Alpha lansmanı) | ~50K TL (50 ücretli) | ~30K TL (30 ücretli) |
| 9 | ~200K TL (300 ücretli) | ~100K TL (150 ücretli) |
| 12 (Yıl 1 sonu) | ~973K TL (1.500 ücretli) | ~503K TL (800 ücretli) |

### 9.4 Break-even Analizi

| Metrik | Değer |
|--------|-------|
| Aylık OPEX (post-MVP) | ~1.1-1.3M TL |
| ARPU | 649 TL |
| Katkı marjı | ~%85 |
| **Break-even noktası** | **~1.900 ofis** |
| Hedef senaryo break-even | ~14. ay |
| Konservatif break-even | ~18. ay |

---

## 10. Sprint Planı

### 10.1 Faz 0 — Temel Hazırlık (Hafta 1-10)

| Sprint | Hafta | İçerik | Kritik Çıktı |
|--------|:---:|--------|-------------|
| **S0** | 1-2 | Mimarı tasarım, tech stack kesinleştirme, veri modeli, auth altyapısı, CI/CD pipeline | Çalışan iskelet, repo, Docker |
| **S1** | 3-4 | Unified Messaging Gateway mimarisi, Telegram Bot temel altyapısı | Çalışan Telegram bot (echo level) |
| **S2** | 5-6 | Veri toplama altyapısı (TÜİK, TCMB, AFAD, belediye), WhatsApp BSP başvurusu | Veri pipeline çalışıır, BSP süreci başlatılmış |
| **S3** | 7-8 | AI değerleme model v0 (TKGM + TÜİK verisi), temel UI bileşenleri | Prototip değerleme çıktısı, MAPE <%22 |
| **S4** | 9-10 | Seed ofis iletişimi, alpha kullanıcı anlaşmaları, hukuki çerçeve (scraping, KVKK, EİDS) | 30 ofis LOİ, KVKK uyum dokümanı |

**Faz 0 Bütçe:** ~₺1.8-2.0M
**Faz 0 Kritik Çıktı:** Çalışan iskelet + Telegram bot + AI model v0 + 30 seed ofis + BSP başvurusu yapılmış + Hukuki çerçeve

### 10.2 MVP-Alpha (Hafta 11-24)

| Sprint | Hafta | İçerik | Bağımlılık |
|--------|:---:|--------|:---:|
| **S5** | 11-12 | AI Değerleme Motoru v1 (emsal karşılaştırma, bölge analizi) | S3 model v0 |
| **S6** | 13-14 | Bölge Kartları + Harita Entegrasyonu + Deprem Risk Skoru | S2 veri pipeline |
| **S7** | 15-16 | CRM Temel (müşteri kayıt, iletişim takip, not, etiket) | — |
| **S8** | 17-18 | AI İlan Asistanı (metin oluşturma + temel fotoğraf iyileştirme) | — |
| **S9** | 19-20 | Portföy Vitrin + Temel Eşleştirme Motoru + Kredi Hesaplayıcı | S7 CRM |
| **S10** | 21-22 | Telegram Tam Entegrasyon (bildirimler, inline CRM, Mini App dashboard) | S1 gateway, S7 CRM |
| **S11** | 23-24 | QA, performans optimizasyonu, güvenlik taraması, Alpha lansmanı | Tümü |

**Alpha Gö/No-Go Kriterleri (Hafta 24):**
- [ ] 100+ aktif kullanıcı
- [ ] 50+ ücretli abone
- [ ] NPS > 40
- [ ] Aylık churn < %10
- [ ] AI değerleme MAPE < %18
- [ ] Telegram bot stabil, mesajlaşma başarı oranı %95+
- [ ] 50+ portföy yüklenmiis

### 10.3 MVP-Beta (Hafta 25-38)

| Sprint | Hafta | İçerik | Bağımlılık |
|--------|:---:|--------|:---:|
| **S12** | 25-26 | WhatsApp Cloud API tam entegrasyon (Elite) | BSP onayı |
| **S13** | 27-28 | EİDS Hibrit Akış (manuel numara giriş + OCR doğrulama + rozet) | — |
| **S14** | 29-30 | Portföy Paylaşım Ağı aktif (gelişmiş eşleştirme + temel komisyon akışı) | S9 vitrin verisi |
| **S15** | 31-32 | Çoklu Site Scraping (koşullu — ortaklık varsa tam, yoksa sınırlı istatistik) | Hukuki çerçeve |
| **S16** | 33-34 | Gelişmiş AI Fotoğraf (staging, virtual styling), Akıllı Fiyat Önerisi | — |
| **S17** | 35-36 | Elite kademe özellikleri (ofis yönetim paneli, çoklu kullanıcı, raporlama) | — |
| **S18** | 37-38 | Tam QA döngüsü, penetrasyon testi, performans testi, genel lansman | Tümü |

**Beta Gö/No-Go Kriterleri (Hafta 38):**
- [ ] 500+ aktif kullanıcı
- [ ] Ünit economics pozitif
- [ ] ARPU >= 600 TL
- [ ] Churn < %8
- [ ] Güvenlik taraması temiz
- [ ] Portföy ağında 80+ ofis, 50+ eşleştirme

### 10.4 Görsel Sprint Timeline (ASCII)

```
Hafta:  1────5────10────15────20────24────30────35────38
        |─── FAZ 0 ───|──── MVP-ALPHA ────|──── MVP-BETA ────|

Faz 0:  [Mimarı][Gateway][Veri ][AI v0][Seed ]
Alpha:  ─────────────[Değer.][Bölge+Harita][CRM ][AI İlan][Portföy][Telegram][QA→🚀Alpha]
Beta:   ─────────────────────────────────[WhatsApp][EİDS][Portföy Aktif][Scraping][AI Foto+][Elite][QA→🚀Beta]

Paralel: BSP başvurusu ────────────────────────────────→ (onay bekleniyor)
         Seed ofis     ─────────→ Alpha lansmanı → organik büyüme ──────────→
         Hukuki çerçeve ──────────────────→ Scraping kararı ──────→
```

---

## 11. Bütçe

### 11.1 Geliştirme Bütçesi (Tek Seferlik)

| Kalem | Faz 0 | Alpha | Beta | Toplam |
|-------|:---:|:---:|:---:|:---:|
| **Backend geliştirme** | 0.6M | 1.8M | 1.5M | 3.9M |
| **Frontend geliştirme** | 0.3M | 1.2M | 1.0M | 2.5M |
| **AI/ML geliştirme** | 0.3M | 0.8M | 0.6M | 1.7M |
| **Telegram + Messaging Gateway** | 0.2M | 0.3M | 0.2M | 0.7M |
| **WhatsApp entegrasyon** | — | 0.1M | 0.4M | 0.5M |
| **Scraping altyapısı** | 0.1M | — | 0.5M | 0.6M |
| **DevOps/altyapı** | 0.15M | 0.2M | 0.3M | 0.65M |
| **QA/Test** | 0.05M | 0.2M | 0.3M | 0.55M |
| **UI/UX tasarım** | 0.1M | 0.15M | 0.1M | 0.35M |
| **Hukuki danışmanlık** | 0.05M | 0.05M | 0.1M | 0.2M |
| **TOPLAM** | **1.9M** | **4.8M** | **5.0M** | **₺11.7M** |

### 11.2 Yıllık Operasyonel Maliyet (Geliştirme Sonrası)

| Kalem | Aylık | Yıllık | Not |
|-------|:---:|:---:|-----|
| Sunucu/cloud | 15-25K | 180-300K | Ölçeklenen — kullanıcı başı |
| AI API (GPT/Claude) | 30-50K | 360-600K | Değerleme + İlan asistanı |
| Telegram | 0 | 0 | **Ücretsiz** |
| WhatsApp BSP | 10-30K | 120-360K | Mesaj hacmine bağlı |
| Scraping proxy | 5-15K | 60-180K | Koşullu — ortaklık varsa düşer |
| Veri kaynakları | 5-10K | 60-120K | TKGM, belediye API |
| Destek ekibi | 20-40K | 240-480K | Ölçeklenen |
| **TOPLAM** | **85-170K** | **₺1.0-2.0M** | |

### 11.3 Toplam ve Net Bütçe

| Kalem | Tutar |
|-------|:---:|
| Geliştirme bütçesi (brüt) | ₺11.7M |
| Orkestratör tasarrufu (%20-30) | -₺2.3M ~ -₺3.5M |
| **Net geliştirme bütçesi** | **₺8.2-9.4M** |
| Yıllık operasyonel (post-MVP) | ₺1.0-2.0M |
| **İlk 12 ay toplam (net)** | **₺9.2-11.4M** |

**Orkestratör Tasarruf Karşılaştırması:**

| Kalem | Klasik Geliştirme | Orkestratör ile | Tasarruf |
|-------|:---:|:---:|:---:|
| Geliştirme bütçesi | ₺11.7M | ₺8.2-9.4M | %20-30 |
| Geliştirme süresi | 38 hafta | 34-36 hafta | %5-10 |
| Hata oranı | Sektör ortalaması | -%30-40 (AI code review) | Dolaylı tasarruf |

---

## 12. Gö-to-Market (GTM) Stratejisi

### 12.1 Seed the Network: 30-50 Anchor Ofis

| Adım | Zamanlama | Hedef |
|------|:---:|-------|
| 1. Hedef ofis belirleme | Faz 0 (Hafta 1-4) | İstanbul Anadolu Yakası'ndan 30 "anchor" ofis seçimi |
| 2. Ücretsiz onboarding | Alpha Hafta 1-4 | 30 ofis = ~300 ilan portföy yükleme |
| 3. Organik büyüme | Alpha Hafta 5-16 | Çapraz referanslarla +50 ofis |
| 4. Eşleştirme aktivasyonu | Alpha Hafta 12 | Minimum 50 ofis = anlamlı eşleştirme havuzu |
| **Hedef: Alpha sonunda** | | **80+ ofis, 800+ ilan, 50+ eşleştirme** |

**Neden İstanbul Anadolu Yakası:**
- Türkiye emlak işlemlerinin ~%25'i İstanbul'da
- Anadolu yakası yoğun ofis konsantrasyonu
- Hem lüks hem orta segment mevcut
- Kentsel dönüşüm devam ediyor (veri zenginliği)
- Saha ekibi lojistik olarak yönetilebilir

### 12.2 Telegram Viral Loop

1. **Değerleme Raporu Paylaşımı:** Emlakçı museterisine PDF rapor gönderir. Raporda platform logosu + "Siz de gayrimenkulünüzü değerletin" CTA'si
2. **Bot Paylaşım:** Emlakçı meslektaşına "Bu botu dene, sorgunun cevabını 3 saniyede alıyon" der
3. **Portföy Paylaşım Daveti:** "Bu portföyü görmek için platformumuza kayıt olun" → B2B viral

### 12.3 Freemium → Pro Dönüşüm Akışı

```
Ücretsiz Kayıt → 10 Değerleme/ay → Sınıra Ulaşır → "Pro'ya Geç: Sınırsız Değerleme + AI İlan + Portföy Ağı"
     ↓                                                        ↓
 Telegram Bot                                            799 TL/ay
 (anında değer)                                      (30 gün ücretsiz deneme)
```

### 12.4 WhatsApp Viral Loop (Beta'da)

- Her üretilen ilan PDF'inde platform logosu
- "Bu ilan [Platform] ile hazırlanmıştır" watermark
- Müşteriye atılan her link = potansiyel lead
- "WhatsApp ile Sor" butonu web sitesinde

### 12.5 Müşteri Edinme Kanalları

| Kanal | Strateji | Tahmini CAC | Öncelik |
|-------|----------|:---:|:---:|
| Saha Satış | 2-3 kişilik ekip, ofis ofis demo | 3.000 TL | YÜKSEK (ilk 100) |
| Dijital Reklam | Google Ads + Meta Ads | 1.500 TL | ORTA |
| İçerik Pazarlama | Blog, YouTube eğitim | 500 TL | DÜŞÜK (uzun vadeli) |
| Sektör Etkinlikleri | GYÖDER, RE/MAX konvansiyonu | 2.000 TL | ORTA |
| Referral Programı | Mevcut müşteri tavsiyesi = 1 ay ücretsiz | 800 TL | YÜKSEK (Faz 2+) |
| Telegram Bot Viral | Organik paylaşım | ~0 TL | YÜKSEK |

---

## 13. Kullanıcı Yolculuk Haritası

### Tam Akis: Telegram + WhatsApp + Web Platform

```
1. KEŞFETME
   ├─ Instagram/Google rekllamı: "Bölgenizdeki fiyat değişimini biliyor musunuz?"
   ├─ Meslektaş tavsiyesi (viral loop)
   └─ Telegram Bot keşfedme: "Kadıköy 3+1 fiyatları" sorusuna anında cevap

2. DENEME (Aha! Momenti)
   ├─ Telegram Bot'a adres/konum gönderir → 3 saniyede değerleme çıktısı
   ├─ Mini App'te bölge analiz kaartini görür → "Vay, bunu bilmiyordum"
   └─ Ücretsiz 10 değerleme ile platforma alışır

3. SATIN ALMA
   ├─ Starter (399 TL) veya Pro (799 TL) abone olur
   ├─ 30 gün ücretsiz deneme (Pro)
   └─ Portföyünü sisteme yükler → AI ilan metni oluşturur

4. KULLANIM (Stickiness)
   ├─ Her sabah Telegram'dan "Piyasa Raporu" alır
   ├─ CRM'e müşteri kayıt → otomatik eşleştirme bildirimi gelir
   ├─ AI ile ilan hazırlar → zamandan tasarruf hisseder
   └─ Portföy vitrininde görülür → diğer ofislerden iletişim gelir

5. BAĞIMLILIK
   ├─ Haftalık bölge raporu → vazgeçilmez
   ├─ Müşteri-portföy eşleştirme → kayıp azalır
   ├─ Veri birikimi → ayrılmanın maliyeti artar (data lock-ın)
   └─ WhatsApp ile müşteriye profesyonel PDF atar → "bu olmadan yapamam"

6. YAYILIM
   ├─ "Bu yazılımı kullanmayan ofise şaşırırım" sözü
   ├─ Portföy paylaşım daveti → zorunlu viral büyüme
   ├─ Değerleme raporu paylaşımı → logo ile organik reklam
   └─ "İş arkadaşıma sistemden paslıyorum, oradan kabul et" → ağ buyur
```

---

## 14. Portföy Paylaşım Ağı Stratejisi

### 14.1 Üç Katmanlı Aktivasyon

| Katman | Ne Yapar | Zamanlama | Değer | Risk |
|--------|---------|:---------:|:---:|:---:|
| **1. Pasif Vitrin** | Emlakçı portföyünü gösterir, aranabilir | Alpha (Hafta 12-16) | Düşük-Orta | Düşük |
| **2. Eşleştirme Motoru** | "Müşterim var, ilan arıyorum" alıcı-satıcı eşleştirme | Alpha (Hafta 16-20) | Yüksek | Orta |
| **3. Aktif Paylaşım + Komisyon** | Komisyon anlaşması, çapraz satış, kontrat yönetimi | Beta (Hafta 25-30) | Çok Yüksek | Çok Yüksek |

### 14.2 Seed Stratejisi

| Adım | Zamanlama | Hedef |
|------|:---------:|-------|
| 1. Hedef ofis belirleme | Faz 0 (Hafta 1-4) | İstanbul'dan 30 "anchor" ofis |
| 2. Ücretsiz onboarding | Alpha Hafta 1-4 | 30 ofis = ~300 ilan yüklemesi |
| 3. Organik büyüme | Alpha Hafta 5-16 | Çapraz referansla +50 ofis |
| 4. Eşleştirme aktivasyonu | Alpha Hafta 12 | Min. 50 ofis = anlamlı havuz |
| **Alpha sonunda hedef** | | **80+ ofis, 800+ ilan, 50+ eşleştirme** |

### 14.3 Kritik Kütle Metrikleri

| Metrik | Eşik | Neden |
|--------|:---:|-------|
| Aktif ofis sayısı | 50+ | Eşleştirme algoritması anlamlı sonuç üretebilir |
| Portföy (ilan) sayısı | 500+ | Yeterli çeşitlilik |
| Haftalık eşleştirme | 20+ | Kullanıcılar değer görür |
| Aktif paylaşım oranı | %30+ | Ağ "çalışıyor" hissi |

### 14.4 Moderasyon Planı

- Alpha'da 1 moderatör + 1 topluluk yöneticisi (pilot için)
- Moderasyon SLO: 24 saat içinde dönüş
- "Raporla/Engelle" mekanizması
- Güven skoru sistemi (Beta'da)
- Platform Etik Kuralları — kabul edenler sisteme alınır

---

## 15. Risk Matrisi

### 15.1 Risk Tablosu

| # | Risk | Etki (1-10) | Olasılık (1-10) | Risk Skoru | Mitigasyon |
|---|------|:---:|:---:|:---:|----------|
| **R1** | Çoklu scraping hukuki riski (ToS + KVKK) | 9 | 7 | **63** | Ortaklık öncelikli, yoksa sadece istatistik. Scraping kritik yol DIŞINDA |
| **R2** | Kapsam şişmesi (feature creep) — 15 özellik | 8 | 7 | **56** | İki katmanlı MVP (Alpha = 9 özellik, sınırlı ve odaklı) |
| **R3** | WhatsApp BSP onay gecikmesi (>12 hafta) | 7 | 5 | **35** | Telegram varsayılan kanal, WhatsApp Beta'da. Fallback SMS |
| **R4** | Portföy ağı kritik kütle sağlanamaması | 8 | 4 | **32** | Seed strategy (30 ofis), Alpha'da ölçüm, karar noktası Alpha sonunda |
| **R5** | AI API maliyet patlaması (fotoğraf) | 6 | 5 | **30** | Fotoğraf Alpha'da "basit", Beta'da "gelişmiş". Hard limit/kullanıcı |
| **R6** | EİDS resmi API'nin hiç gelmemesi | 6 | 4 | **24** | Hibrit çözüm yeterli, manuel giriş kabul edildi |
| **R7** | Rakip kopyalama (Arveya, Fizbot, Endeksa) | 5 | 4 | **20** | Veri moat + ağ etkisi + Telegram Mini App diferansiyeli |
| **R8** | Telegram penetrasyonunun düşük kalması | 4 | 4 | **16** | WhatsApp yedek kanal, çift kanal mimarisi nötralize eder |
| **R9** | Deprem/afet veri kaynağı erişim sorunu | 5 | 3 | **15** | Birden fazla kaynak (AFAD, Kandıllı, belediye), cache mekanizması |
| **R10** | Ekip tükenmişliği (38 hafta maraton) | 6 | 3 | **18** | İki katmanlı yapı moral verir — Alpha lansmanı ara hedef |

### 15.2 Risk Isı Haritası (ASCII)

```
        Olasılık →   1-2    3-4    5-6    7-8    9-10
Etki ↓
9-10                                      [R1]
7-8                  [R4]          [R3]   [R2]
5-6                  [R9]  [R6]   [R5]
3-4                  [R8]  [R10]  [R7]
1-2
```

### 15.3 Top 3 Risk ve Detaylı Mitigasyon

**R1 — Scraping Hukuki (Skor: 63)**
- Faz 0'da hukuki araştırma: ToS analizi, scraping hukuku, emsal kararlar
- Paralel: İş ortaklığı görüşmeleri (Hepsiemlak, Zingat)
- Ortaklık sağlanırsa → resmi API
- Ortaklık sağlanmazsa → sınırlı aggregate istatistik (bireysel ilan değil)
- Scraping'i core özellik yerine "veri zenginleştirme katmanı" olarak konumlandır

**R2 — Kapsam Şişmesi (Skor: 56)**
- İki katmanlı MVP bunu doğrudan adresliyor
- Alpha = 9 odaklı özellik → erken gelir, erken feedbaçk
- Beta başarısız olursa Alpha tek başına yaşayabilir bir üründür
- Her sprint sonunda kapsam review

**R3 — WhatsApp BSP (Skor: 35)**
- Telegram Alpha'da tam — WhatsApp Beta'da
- BSP başvurusu Faz 0'da başlatılır (paralel)
- Click-to-chat ile geçici çözüm
- Bu risk Tur 4'te dramatik düştü (Telegram sayesinde)

### 15.4 Kullanıcı Kararlarının Risk Etkisi

| Karar | Azalttığı Riskler | Arttırdığı Riskler |
|-------|-------------------|-------------------|
| İki katmanlı MVP | R2 (kapsam şişmesi) ⬇ | — |
| 399/799/1499 fiyat | R5 (AI maliyet) ⬇ COGS karşılanır | — |
| Telegram eklenmesi | R3 (WhatsApp bağımlılığı) ⬇⬇ | R8 (Telegram penetrasyonu) ⬆ ama düşük |
| EİDS hibrit | R6 (API yokluğu) ⬇⬇ | — |
| Portföy kesinlikle MVP | R4 (kritik kütle) ⬆ | — (seed stratejisi mitigate eder) |

---

## 16. Kritik Karar Noktaları (Gate'ler)

| Gate | Zamanlama | Karar | Geçiş Kriteri |
|------|:---:|-------|-------------|
| **G0** | Hafta 10 (Faz 0 sonu) | Alpha'ya devam mı? | AI model v0 çalışıyor + 20+ seed ofis LOİ + BSP başvurusu yapılmış + KVKK uyum dokümanı |
| **G1** | Hafta 16 (Alpha ortası) | Portföy eşleştirme açılsın mı? | 50+ portföy yüklenmiş + eşleştirme algoritması doğrulanmış |
| **G2** | Hafta 24 (Alpha sonu) | Beta'ya geçiş mi? | 100+ aktif kullanıcı + 50+ ücretli + NPS 40+ + aylık churn <%10 |
| **G3** | Hafta 30 (Beta ortası) | Scraping açılsın mı? | Hukuki çerçeve tamam (ortaklık veya hukuki görüş) + altyapı hazır |
| **G4** | Hafta 38 (Beta sonu) | Genel lansman mı? | 500+ aktif + ünit economics pozitif + güvenlik taraması temiz |

**Önemli:** Her gate'te "hayır" cevabı mümkün. G2'de Alpha yeterli traction göstermezse Beta kapsamı daraltılabilir veya pivot edilebilir. Bu esneklik iki katmanlı MVP'nin en büyük avantajı.

---

## 17. Kaynak Planı

### 17.1 Çekirdek Ekip (Orkestratör AI Agent'lar)

| # | Agent | Rol | Birincil Faz |
|---|-------|-----|-------------|
| 1 | claude-teknik-lider | Mimarı kararlar, tech stack | Faz 0 |
| 2 | gemini-uiux-tasarımcı | UI/UX tasarım stratejisi | Faz 0 + Alpha |
| 3 | claude-web-arastirmaci | Veri kaynakları, teknoloji karşılaştırma | Faz 0 |
| 4 | gemini-kodlayıcı | Standart sayfa/bileşen geliştirme | Alpha + Beta |
| 5 | claude-kıdemli-geliştirici | Karmaşık kod, refaçtoring, mesajlaşma | Alpha + Beta |
| 6 | codex-junior-geliştirici | Basit/tekrarlayan görevler | Alpha + Beta |
| 7 | claude-qa-senaryo | QA test senaryosu, test planı | Alpha sonu + Beta |
| 8 | gemini-test-mühendisi | Fonksiyonel test çalıştırma | Alpha sonu + Beta |
| 9 | claude-devops | CI/CD, deployment, altyapı | Tüm fazlar |
| 10 | claude-güvenlik-analisti | Güvenlik analizi, penetrasyon | Beta |
| 11 | claude-üx-mikrokopi | UX mikro-kopya, CTA metinleri | Alpha + Beta |
| 12 | claude-misafir-tester | Browser testi, responsive | Beta |

### 17.2 Faz Bazlı Agent Atama Planı

| Faz | Öncelikli Agent'lar | İkincil Agent'lar |
|-----|---------------------|-------------------|
| **Faz 0** | claude-teknik-lider, gemini-uiux-tasarımcı, claude-web-arastirmaci | claude-devops, claude-güvenlik-analisti |
| **Alpha S5-S8** | gemini-kodlayıcı, claude-kıdemli-geliştirici, codex-junior-geliştirici | claude-qa-senaryo, gemini-test-mühendisi |
| **Alpha S9-S11** | gemini-kodlayıcı, claude-kıdemli-geliştirici | claude-üx-mikrokopi, claude-misafir-tester |
| **Beta S12-S15** | claude-kıdemli-geliştirici, gemini-kodlayıcı | claude-güvenlik-analisti, claude-devops |
| **Beta S16-S18** | claude-qa-senaryo, gemini-test-mühendisi, claude-devops | codex-teknik-yazar |

### 17.3 Ek İnsan Kaynağı Gereksinimleri

| Rol | Ne Zaman | Neden |
|-----|----------|-------|
| Hukuk Danışmanı | Faz 0 (part-time) | KVKK, scraping, EİDS hukuki çerçeve |
| Saha Satış (2-3 kişi) | Alpha lansman öncesi | Seed ofis ilişkileri, onboarding |
| Moderatör (1 kişi) | Alpha Hafta 12+ | Portföy paylaşım ağı moderasyonu |
| Topluluk Yöneticisi (1 kişi) | Beta | Pilot ops, büyüme yönetimi |

---

## 18. Teknik Altyapı Özeti

### 18.1 Önerilen Tech Staçk

| Katman | Teknoloji | Gerekçe |
|--------|-----------|---------|
| **Frontend (Web)** | Next.js 15 (React 19) | SSR + SEO kritik, App Router, İSR |
| **Frontend (Mobil)** | Telegram Mini App + PWA | Alpha'da yeterli, Native Faz 2+ |
| **Backend API** | FastAPI (Python 3.12) | ML ekosistemiyle doğal uyum, asynç İ/O |
| **Veritabanı** | PostgreSQL 16 + PostGIS | Spatial sorgular, JSONB, olgunluk |
| **Arama** | Elasticsearch / Meilisearch | Full-text, filtreleme, geo-distance |
| **Onbellek** | Rediş 7 | Session, cache, rate limiting, Çelery broker |
| **Görev Kuyruğu** | Çelery + Rediş | Veri toplama, ML eğitim, toplu bildirim |
| **Mesajlaşma** | Unified Messaging Gateway (özel) | Kanal-agnostik, Telegram + WhatsApp + SMS |
| **ML Framework** | LightGBM + scikit-learn + HuggingFace | Tablo verisi, NLP, görüntü |
| **Harita** | MapLibre GL JS + OpenStreetMap | Açık kaynak, isii haritaları, özel stil |
| **Dosya Depolama** | MinİO (self-hosted S3) | Fotoğraf, doküman, rapor |
| **CI/CD** | GitHub Actions + Docker Compose | Otomatik test, build, deploy |
| **Monitoring** | Sentry + Grafana + Prometheus | Hata takibi, performans metrikleri |

### 18.2 Veri Kaynakları ve Erişim Stratejisi

| Kaynak | Veri Tıpı | Erişim | Risk |
|--------|----------|--------|:---:|
| **TÜİK MEDAŞ** | Konut satış istatistikleri, nüfus | REST API (SDMX) | DÜŞÜK |
| **TCMB EVDS** | Konut fiyat endeksi, faiz, döviz | REST API | DÜŞÜK |
| **AFAD TDTH** | Deprem tehlike haritası, PGA | WMS REST | DÜŞÜK |
| **TKGM Parsel** | Ada/parsel, koordinat | WMS/WFS | ORTA |
| **İBB Açık Veri** | İmar planı, nüfus, ulaşım | API | ORTA |
| **Sahibinden/Hepsiemlak** | İlan verileri, fiyatlar | Ortaklık (öncelik) / koşullu scraping | YÜKSEK |
| **Google Maps/OSM** | POİ, geoçoding | API | DÜŞÜK |
| **Bankalar** | Kredi faiz oranları | Scraping + ortaklık | ORTA |

**Katmanlı Veri Toplama Prensibi:** Önce kolay kaynaklar (TÜİK, TCMB, AFAD) → sonra orta zorlukta (TKGM, belediye) → en son riskli (ilan siteleri).

### 18.3 AI Model Stratejisi

| Model | Girdi | Çıktı | Faz |
|-------|-------|-------|:---:|
| **Otomatik Değerleme (AVM)** | m2, oda, kat, yaş, konum, emsaller | Tahmini fiyat + güven aralığı | Alpha |
| **İlan Metni Üretimi** | Mülk özellikleri, fotoğraf etiketleri | SEO uyumlu ilan metni | Alpha |
| **Müşteri-Portföy Eşleştirme** | Müşteri kriterleri, portföy özellikleri | Eşleştirme skoru + sıralı liste | Alpha (kural tabanlı) → Beta (ML) |
| **Fotoğraf İyileştirme** | Ham fotoğraf | Işık/perspektif düzeltilmiş fotoğraf | Alpha (temel) → Beta (gelişmiş) |
| **Akıllı Fiyat Önerisi** | Fiyat, bölge, arz/talep, sezonalite | "Hızlı satış" vs "max getiri" fiyatı | Beta |
| **Fiyat Anomalı Tespiti** | İlan fiyatı vs bölge ortalaması | Sapma uyarısı | Alpha |

### 18.4 Altyapı Gereksinimleri

| Bileşen | MVP (Faz 0-Alpha) | Faz 2+ |
|---------|:---:|:---:|
| Sunucu | 8 vCPU, 32 GB RAM, 500 GB NVMe | Horizontal scaling, Kubernetes |
| Veritabanı | PostgreSQL + PostGIS + TimescaleDB | Read replica, sharding |
| Nesne Depolama | 500 GB (fotoğraflar) | 2+ TB büyüme planı |
| CDN | CloudFlare | CloudFront |
| ML Eğitim | CPU yeterli (LightGBM) | GPU sadece görüntü modelleri |

---

## 19. Hukuki ve Uyum Gereksinimleri

### 19.1 KVKK Uyum

| Gereksinim | Uygulama |
|-----------|----------|
| Kişisel veri işleme rızası | Kayıt anında açık rıza, aydınlatma metni |
| Veri minimizasyonu | Sadece gerekli kişisel veri toplanacak. Scraping katmanında kişisel veri (ad, telefon) **kesinlikle toplanmaz** — yalnızca anonim pazar verisi. CRM PII'ı kullanıcı girişlidir ve rıza ile işlenir |
| Veri silme hakkı | "Hesabımı sil" butonu, 30 gün içinde tam silme |
| Çerez politikası | OneTrust/CookieBot entegrasyonu |
| VERBİS kaydı | Veri sorumlusu olarak VERBİS'e kayıt zorunlu |
| Veri ihlali bildirimi | KVKK Kurulu'na 72 saat içinde bildirim prosedürü |
| Privacy by Design | Sistem mimarisinde kişisel veri ayrımı (PII vs anonim) |

### 19.2 EİDS Yasal Çerçeve

| Konu | Durum | Yaklaşım |
|------|-------|----------|
| Resmi API | Şu an mevcut değil | Manuel giriş + OCR, resmi API takibi |
| e-Devlet erişimi | 3. taraf erişimi için protokol yok | Kullanıcının kendi EİDS numarasını girmesi |
| e-Devlet scraping | TCK 243-244 riski (bilişim sistemine girme) | **KESİNLİKLE YAPILMAYACAK** |
| Uyum stratejisi | Hibrit çözüm | Manuel giriş + belge OCR + "Doğrulanmış İlan" rozeti |

### 19.3 Scraping Hukuki Risk ve ToS Analizi

| Site | ToS Durumu | Risk | Yaklaşım |
|------|-----------|:---:|----------|
| Sahibinden.com | Otomatik veri çekmeyi açıkça yasaklıyor | YÜKSEK | Ortaklık görüşmesi öncelikli, yoksa sadece aggregate istatistik |
| Hepsiemlak | Sınırlı ortaklık programı | ORTA | İş ortaklığı görüşmesi |
| Emlakjet | API bilgisi kamuya açık değil | ORTA | Doğrudan iş geliştirme |
| Zingat | REIDIN ortaklığı var | DÜŞÜK-ORTA | REIDIN üzerinden veri ortaklığı |

**Hukuki İlkeler:**
- **Scraping katmanında kişisel veri toplanmaz:** 3. parti ilan sitelerinden kişisel veri (telefon, isim, e-posta vb.) toplanmayacak; yalnızca ilan bazlı anonim pazar verisi ve aggregate istatistik (ortalama m² fiyatı, arz-talep oranı vb.)
- **CRM'deki PII ayrımı:** CRM modülündeki müşteri verileri (isim, telefon, talep bilgisi) kullanıcı tarafından girilen kişisel verilerdir ve KVKK kapsamında **açık rıza + aydınlatma metni** ile işlenir. Bu veriler scraping ile değil, doğrudan kullanıcı etkileşimiyle toplanır
- Düşük frekans, sınırlı hacim
- Ortaklık her zaman scraping'e tercih edilir
- Faz 0'da hukuki görüş alınacak

### 19.4 Veri Saklama ve Güvenlik Politikası

| Alan | Politika |
|------|---------|
| Veri sınıflandırma | PII (kişisel) vs anonim veri ayrılmış depolama |
| Şifreleme | AES-256 at-rest, TLS 1.3 in-transit |
| Erişim kontrolü | RBAC + audit log |
| Yedekleme | Günlük otomatik, 30 gün saklama |
| Penetrasyon testi | Beta lansmanından önce zorunlu |
| Olay müdahale | 72 saat KVKK bildirim, incident response planı |

---

## 20. Sonraki Adımlar

### Kullanıcı Onayı Sonrası Yapılacaklar

| # | Adım | Sorumlu Ağent | Süre | Öncelik |
|---|------|:---:|:---:|:---:|
| 1 | **Product Backlog oluşturma** — 15 özellik → user story'lere ayırma | gemini-urun-yoneticisi | 2-3 gün | KRİTİK |
| 2 | **Teknik mimari doküman** — Tech stack, veri modeli, API tasarımı, mesajlaşma gateway | claude-teknik-lider | 2-3 gün | KRİTİK |
| 3 | **UI/UX tasarım stratejisi** — Wireframe + Stitch prototipleri | gemini-uiux-tasarımcı | 3-5 gün | KRİTİK |
| 4 | **Operasyonel sprint planı detaylandırma** — Görev kırılımı, bağımlılık haritası | codex-operasyonel-planlayici | 1-2 gün | YÜKSEK |
| 5 | **Hukuki çerçeve başlangıç** — KVKK danışmanlığı, scraping hukuki araştırma | Hukuk danışmanı (dış) | Hemen | YÜKSEK |
| 6 | **Seed ofis aday listesi** — İstanbul Anadolu Yakası 30 hedef ofis | claude-web-arastirmaci | 2-3 gün | ORTA |
| 7 | **WhatsApp BSP başvurusu** — 360dialog veya Twilio üzerinden | claude-devops | 1 gün | ORTA (paralel) |
| 8 | **Faz 0 Sprint S0 başlatma** — Mimarı tasarım, repo, CI/CD | Orkestra şefi koordinasyonu | — | BAŞLA |

### Kritik Yol

```
Kullanıcı onayı → [1. Backlog + 2. Mimarı (paralel)] → [3. UI/UX] → [4. Sprint planı] → Faz 0 S0 Başla
                   ↕ (paralel)
                   [5. Hukuki] + [6. Seed ofis] + [7. BSP başvurusu]
```

---

*Bu doküman, 4 türlü Delphi İteratif Yakınsama süreci sonucunda 3 bağımsız AI agent'in (Claude Stratejik Planlayıcı, Gemini Ürün Yöneticisi, Codex Operasyonel Planlayıcı) uzlaşısıyla oluşturulmuştur. Toplam ~350K+ karakter analiz çıktısı tek bir birleşik plan olarak derlenmiştir.*

*Son güncelleme: 2026-02-20*
