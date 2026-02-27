# Emlak Teknoloji Platformu — Proje Plani

**Tarih:** 2026-02-20
**Versiyon:** 1.0
**Hazirlayan:** Stratejik Degerlendirme Heyeti (Claude Stratejik Planlayici + Gemini Urun Yoneticisi + Codex Operasyonel Planlayici)
**Yontem:** Delphi Iteratif Yakinsama — 4 Tur
**Durum:** GO (Kosullu) — Kullanici onayi bekleniyor

---

## 1. Yonetici Ozeti

Emlak Teknoloji Platformu, Turkiye emlak sektorunun **veri + operasyon + tahmin** uclusunu tek catida birlestiren ilk entegre SaaS cozumdur. Istanbul merkezli butik emlak ofislerini hedefleyen platform; AI destekli degerleme, bolge analizi, musteri-portfoy eslestirme, portfoy paylasim agi, ilan asistani ve cift kanalli mesajlasma (Telegram + WhatsApp) sunarak emlakcilari kurumsal duzeyde donanimli hale getirir. Temel farklilasma **freemium ile hacim → hacimden veri → veriden AI → AI'dan deger → degerden gelir** dongusu uzerine kuruludur. Mevcut rakiplerden (Endeksa, Arveya, Fizbot, REIDIN) hicbiri bu ucluyu tek platformda birlestirmemektedir.

**Hedef Pazar:** Turkiye emlak SaaS pazari (~800M-1.2 milyar TL), birincil hedef Istanbul butik ofisler (3-15 danismani)
**Temel Farklilasilma:** Veri + Operasyon + Tahmin birlesiimi, Telegram Mini App ile sektor ilki UX, kademeli portfoy paylasim agi
**Nihai Karar:** **GO** — Iki katmanli MVP (Alpha + Beta), 38 hafta, ₺8.2-9.4M net butce (orkestrator ile)

---

## 2. Vizyon ve Misyon

### Vizyon
Turkiye emlak ekosisteminin **veri omurgasi** olmak. Emlak profesyonellerinin karar sureclerini sezgiden veriye, tahminlerini modelden gercek zamanli sinyal analizlerine donusturen, sektorun **tek entegre zeka platformu** haline gelmek.

### Misyon
Emlak danismanlarina, yatirimcilara ve ofislere; fiyatlama, portfoy yonetimi, musteri eslestirme, ilan optimizasyonu ve yatirim analizi konularinda **AI destekli, gercek zamanli, kullanilabilir araclar** sunarak sektorun dijital donusumunu hizlandirmak. Her olcekteki emlak profesyoneline (bireysel danismandan kurumsal zincire) eriselebilir fiyatla hizmet vermek.

### Stratejik Hedefler

| Vade | Hedef | Olcum |
|------|-------|-------|
| **Kisa Vade (0-12 ay)** | MVP-Alpha + Beta lansmansi, 1.500 ucretli kullanici, Istanbul hakimiyeti | MRR ~973K TL, NPS >40, churn <%10 |
| **Orta Vade (1-3 yil)** | Turkiye geneli yayilim, 5.000+ ucretli ofis, B2B API geliri | ARR >50M TL, 5+ sehir, 1+ kurumsal anlasma |
| **Uzun Vade (3-5 yil)** | Sektor standardi platform, MENA genislemesi, veri urunleri | ARR >200M TL, uluslararasi pazar, veri marketplace |

---

## 3. Pazar Analizi

### 3.1 Turkiye Emlak SaaS Pazari Buyuklugu

| Gosterge | Deger | Kaynak/Tahmin |
|----------|-------|---------------|
| Turkiye yillik konut satisi | ~1.4M adet | TUIK 2025 |
| Tahmini toplam islem hacmi | ~2.5 trilyon TL | Ortalama konut fiyati x satis adedi |
| Kayitli emlak ofisi sayisi | ~40.000+ | TOBB/Meslek odalari |
| Aktif emlak danismani sayisi | ~120.000-150.000 | Sektor tahmini |
| PropTech pazari (yazilim+veri) | ~800M-1.2 milyar TL | Endeksa+REIDIN+CRM+portal gelirleri |
| Dijitallesmis ofis orani (CRM kullanan) | ~%15-20 | Arveya blog verileri referans |
| Yillik buyume potansiyeli | %25-35 | Global PropTech trendleri |

**Kritik gozlem:** 40.000+ emlak ofisinin %80'inden fazlasi hala Excel, WhatsApp ve telefon rehberiyle calisiyor. EIDS zorunlulugu bu dijitallesme dalgasini hizlandiracak.

### 3.2 TAM / SAM / SOM

| Seviye | Tanim | Hesaplama | Deger |
|--------|-------|-----------|-------|
| **TAM** | Tum Turkiye emlak teknoloji harcamalari | 40.000 ofis x ort. 30.000 TL/yil | **~2 milyar TL/yil** |
| **SAM** | CRM + veri analitigi + ilan yonetimi SaaS | ~8.000 dijital ofis x 12.000 TL/yil | **~200M TL/yil** |
| **SOM** | Ilk 3 yilda ulasilabilir pazar payi | 800-1.200 ofis x 9.600 TL/yil | **~10-12M TL/yil** |

### 3.3 Rakip Analizi Tablosu

| Platform | Guclu Yanlari | Zayif Yanlari | Fiyat | Bizim Farkimiz |
|----------|---------------|---------------|-------|----------------|
| **Endeksa** | Kapsamli degerleme motoru, genis veri seti, emsal raporu | Pahali (kurumsal odak), CRM yok, mobil zayif | 2.000-15.000 TL/ay | Freemium + CRM entegrasyonu + AI tahmin |
| **REIDIN** | Profesyonel veri, uluslararasi karsilastirma | Cok pahali, sadece enterprise, karisik UI | 5.000-50.000 TL/ay | Eriselebilir fiyat + operasyonel araclar |
| **Arveya** | Yerli CRM, ilan entegrasyonu, makul fiyat | Veri analitigi yok, AI yok | 500-2.000 TL/ay | Veri katmani + AI tahmin + ag etkisi |
| **Fizbot** | Dijital asistan, cok kanalli ilan dagitimi | Degerleme yok, sinirli analitik | 300-1.500 TL/ay | Veri zekasi + CRM + AI birlesiimi |
| **Sahibinden** | Devasa kullanici tabani, marka bilinirlilig | Profesyonel arac degil, veri analizi yok | Ilan basi 500-3.000 TL | B2B profesyonel araC seti |

### 3.4 Bosluk Analizi

| Bosluk | Mevcut Durum | Bizim Cozumumuz |
|--------|-------------|-----------------|
| **Orta Segment Boslugu** | Endeksa/REIDIN pahali, Arveya/Fizbot sinirli | 399 TL giris bariyeri, premium iceriik |
| **Veri + Is Akisi Entegrasyonu** | Emlaici 5+ farkli arac kullaniyor | Tek platform: degerleme + CRM + ilan + mesajlasma |
| **AI-Native Yaklasim** | Mevcut platformlar AI'yi "eklenti" olarak kullaniyor | AI urunun cekirdeginde: degerleme, ilan, eslestirme, fiyat onerisi |
| **EIDS Uyum** | Hicbir platform EIDS is akisi sunmuyor | Hibrit EIDS dogrulama (manuel + gelecekte oto) |
| **Portfoy Paylasim Agi** | WhatsApp gruplariyla kaotik | Yapilandirilmis, guvenli, komisyon mekanizmali ag |
| **Mobil-Oncelikli** | Cogu cozum masaustu odakli | Telegram Mini App + responsive web |

---

## 4. Hedef Kullanici ve Personalar

### 4.1 Birincil Persona: Emlak Danismani — "Hakan"

| Ozellik | Detay |
|---------|-------|
| **Yas** | 28-45 |
| **Deneyim** | 1-5 yil |
| **Portfoy** | 10-30 aktif ilan |
| **Musteri** | 20-50 aktif alici/kiraci |
| **Gelir** | Aylik 15.000-40.000 TL komisyon |
| **Teknoloji** | Akilli telefon, WhatsApp, Sahibinden |
| **Butce** | Aylik 200-500 TL yazilim harcamasi |
| **Motivasyon** | Daha fazla satis kapatmak, profesyonel gorunmek, zamandan tasarruf |

**Temel Agri Noktalari:**
1. "Bu ev kaca satilir?" sorusuna guvenilir cevap verememe
2. Musteri takibinin kopmasi (Excel/not defteri kayboluyor)
3. Ilan hazirlamak ve guncellemek saatler suruyor
4. Potansiyel musteriye hizli donus yapamama

### 4.2 Ikincil Persona: Ofis Sahibi / Broker — "Elif"

| Ozellik | Detay |
|---------|-------|
| **Yas** | 35-55 |
| **Deneyim** | 5-15 yil |
| **Ekip** | 3-10 danismani |
| **Portfoy** | 50-200 aktif ilan |
| **Musteri** | 100-500 aktif kayit |
| **Gelir** | Ofis aylik 80.000-300.000 TL ciro |
| **Teknoloji** | CRM denemis ama birakmis, Excel agirlikli |
| **Butce** | Aylik 500-2.000 TL |
| **Motivasyon** | Ekibi verimli yonetmek, kayip musteriyi azaltmak |

**Temel Agri Noktalari:**
1. Hangi danismani hangi musteriyle ne konustu bilinmiyor
2. Ayni musteriye iki danismani ayni anda ulasiyor (cakisma)
3. Ilan portalllarina tek tek giris yapiliyor
4. Danismani performansini olcemiyor, komisyon hesabi karmasik

### 4.3 Kullanici Agri Noktalari Tablosu

| Agri Noktasi | Hakan (Danismani) | Elif (Broker) | Cozum Ozelligimiz |
|-------------|-------------------|---------------|-------------------|
| Fiyat belirleyememe | "Sahibinden'den bakip tahmin ediyorum" | "Danismanilarim tutarsiz fiyat veriyor" | AI Degerleme + Emsal Analiz |
| Musteri kaybetme | "Not ettim ama kaybettim" | "Kim ne konustu bilmiyorum" | CRM + Otomatik Eslestirme |
| Ilan hazirlama suresi | "Her ilan 1-2 saat" | "10 danismani x 1 saat = gun gidiyor" | AI Ilan Asistani |
| Portfoy paylasimi | "WhatsApp'ta kayboluyor" | "Diger ofislerle koordinasyon yok" | Portfoy Paylasim Agi |
| Mobil erisim | "Sahada bilgiye eriisemiyorum" | "Danismanilarim sahada kopuk" | Telegram Mini App |
| EIDSuyumu | "Sistemi bilmiyorum" | "Her ilana tek tek giriyoruz" | EIDS Hibrit Dogrulama |

---

## 5. Urun Stratejisi — Iki Katmanli MVP

### 5.1 MVP-Alpha (Hafta 11-24)

Calisan, gelir ureten, tek basina yasayabilen urun. 9 temel ozellik.

| # | Ozellik | Aciklama | Fiyat Kademesi |
|---|---------|----------|:--------------:|
| 1 | **AI Degerleme Motoru + Emsal Analiz** | Adres/ada-parsel girisiyle AI tabanli fiyat tahmini, emsal karsilastirma, PDF rapor | Starter+ |
| 2 | **Bolge Analiz Kartlari** | Mahalle/ilce bazinda demografi, ort. m2 fiyati, kira carpani, arz-talep, imar durumu | Starter+ |
| 3 | **Harita Entegrasyonu** | Portfoy ve emsal gorunumu, POI (okul, hastane, metro), isii haritasi | Starter+ |
| 4 | **Deprem Risk Skoru** | AFAD + Kandilli + belediye verileriyle bolge bazli deprem risk degerlendirmesi | Starter+ |
| 5 | **CRM (Musteri-Portfoy Eslestirme)** | Musteri kayit, iletisim takip, not, etiket, otomatik eslestirme bildirimi | Starter+ |
| 6 | **AI Ilan Asistani** | LLM ile SEO uyumlu ilan metni, temel fotograf iyilestirme (aydinlatma, HDR) | Pro+ |
| 7 | **Portfoy Vitrin + Temel Eslestirme** | Pasif portfoy sergileme + temel alici-satici eslestirme motoru | Pro+ |
| 8 | **Kredi Hesaplayici** | Tutar, vade, faiz → aylik taksit tablosu, banka karsilastirma | Starter+ |
| 9 | **Telegram Bot + Mini App** | Bot API ile bildirimler, CRM etkileesiimleri, Mini App ile dashboard | Tum kademeler |

**Alpha Lansmani Hedefi:**
- 30+ seed ofis aktif
- Starter + Pro kademeleri acik
- Telegram uzerinden tam deneyim
- WhatsApp: Click-to-chat (BSP hala beklemede olabilir)

### 5.2 MVP-Beta (Hafta 25-38)

Ekosistem tamamlama, Elite kademe, tam mesajlasma. 6 ek ozellik.

| # | Ozellik | Aciklama | Fiyat Kademesi |
|---|---------|----------|:--------------:|
| 10 | **WhatsApp Business API** | BSP entegrasyon, template mesajlar, cift yonlu iletisim, musteri vitrini | Pro+ |
| 11 | **EIDS Hibrit Dogrulama** | Manuel numara giris + OCR belge tarama + dogrulanmis ilan rozeti | Pro+ |
| 12 | **Portfoy Paylasim Agi (Aktif)** | Gelismis eslestirme + temel komisyon akisi + moderasyon | Pro+ |
| 13 | **Coklu Site Scraping** | Sahibinden, Hepsiemlak, Emlakjet veri toplama (kosullu — ortaklik/hukuki izin) | Elite |
| 14 | **Gelismis AI Fotograf** | Virtual staging, dekorasyon onerisi, genis aci duzeltme, nesne iyilestirme | Elite |
| 15 | **Ofis Yonetim Paneli + Raporlama** | Coklu kullanici, danismani performans KPI, komisyon hesabi, ekip dashboard | Elite |

---

## 6. Ozellik Detaylari

### 6.1 AI Degerleme Motoru + Emsal Analiz

| Alan | Detay |
|------|-------|
| **Ne Yapar** | Bir adres veya ada/parsel girildiginde, yakin cevredeki gerceklesmis satislar, aktif ilanlar ve AI degerleme raporunu tek sayfada gosterir. Ilan fiyati vs. gercek islem fiyati karsilastirmasi yapar. Guven araligi (%80 olasilikla X-Y TL arasi) sunar. |
| **Neden Onemli** | Emlaicinin #1 agri noktasi: "Bu ev kaca satilir?" Guvenilir cevap, profesyonellik algiisi yaratir ve satis kapatma oranini arttirir. |
| **Teknik Gereksinimler** | LightGBM/XGBoost ensemble model, TUIK + TCMB + belediye + kullanici girisi veri pipeline, PostGIS spatial sorgular, PDF rapor uretici |
| **Kademe** | Starter: 10 sorgu/ay, Pro: 100 sorgu/ay, Elite: sinirsiz |

### 6.2 Bolge Analiz Kartlari

| Alan | Detay |
|------|-------|
| **Ne Yapar** | Her mahalle/ilce icin demografik yapi, ortalama m2 fiyati, kira carpani, arz-talep orani, ulasim skoru, okul/hastane yogunlugu, deprem risk skoru, imar durumu bilgilerini gorsel kartlarda sunar. A vs B mahalle karsilastirmasi. |
| **Neden Onemli** | Danismanilar ve yatirimcilar icin bolgeler arasi karsilastirma en sik ihtiyac. Profesyonel sunum araci. |
| **Teknik Gereksinimler** | TUIK demografik veri, TCMB fiyat endeksi, belediye imar bilgisi, OpenStreetMap POI, cache mekanizmasi |
| **Kademe** | Starter: temel kart, Pro: detayli + karsilastirma, Elite: trend tahmin eklentisi |

### 6.3 Harita Entegrasyonu

| Alan | Detay |
|------|-------|
| **Ne Yapar** | Tum portfoy ve emsalleri harita uzerinde gosterir. POI katmanlari (okul, hastane, metro, market), isii haritasi (fiyat yogunluk), bolge poligonlari. |
| **Neden Onemli** | Sahada calisan emlaici icin konum bazli gorsellestirme vazgecilmez. Musteriye gosterim sirasinda profesyonel sunum. |
| **Teknik Gereksinimler** | MapLibre GL JS + OpenStreetMap, PostGIS spatial queries, Google Maps Places API |
| **Kademe** | Tum kademeler (Starter'da sinirli katman) |

### 6.4 Deprem Risk Skoru

| Alan | Detay |
|------|-------|
| **Ne Yapar** | AFAD deprem tehlike haritasi, Kandilli verisi, belediye zemin etudu bilgileri birlestirilerek bolge bazli deprem risk skoru uretir (0-100). Bina yasi ve kat sayisiyla birlesik "Guvenlik Skoru" sunar. |
| **Neden Onemli** | 2023 deprem sonrasi Turkiye'de deprem hassasiyeti cok yuksek. Hicbir Turk emlak platformu bunu sunmuyor — guclu diferansiyator. |
| **Teknik Gereksinimler** | AFAD WMS/REST API, Kandilli verileri, belediye zemin etudu (varsa), PGA hesaplama, cache |
| **Kademe** | Starter+ (tum kademeler) |

### 6.5 CRM (Musteri-Portfoy Eslestirme)

| Alan | Detay |
|------|-------|
| **Ne Yapar** | Musteri kayit, iletisim takip, not, etiket, arama kriterleri (butce, oda, konum, metro). Yeni portfoy eklendiginde otomatik bildirim. Musteri isii haritasi (sicak/soguk lead). |
| **Neden Onemli** | Emlaicinin gunluk operasyonel ihtiyaci. Musteri kaybini azaltir, eslestirme onerisi ile satis kapatma oranini arttirir. |
| **Teknik Gereksinimler** | CRUD + bildirim sistemi + eslestirme algoritmasi (kural tabanli MVP'de, ML ile gelisecek), Telegram entegrasyonu |
| **Kademe** | Starter: 50 musteri, Pro: 500 musteri, Elite: sinirsiz + ekip CRM |

### 6.6 AI Ilan Asistani (Metin + Temel Fotograf Iyilestirme)

| Alan | Detay |
|------|-------|
| **Ne Yapar** | Mulk ozelliklerini girip LLM ile SEO uyumlu, cekici ilan metni uretme. Coklu portal formatinda export. Temel fotograf iyilestirme: aydinlatma duzeltme, perspektif duzeltme, HDR efekti. |
| **Neden Onemli** | Emlaicinin en buyuk zaman kaybi: ilan hazirlama. AI ile 1-2 saatlik is 5 dakikaya duser. Hemen hissedilen somut deger. |
| **Teknik Gereksinimler** | LLM API (Claude/GPT) metin icin, goruntu isleme modeli (hafif CNN) fotograf icin, multi-format export |
| **Kademe** | Pro: 20 ilan/ay + 50 foto/ay, Elite: sinirsiz |

### 6.7 Portfoy Paylasim Agi (Vitrin → Eslestirme → Komisyon)

| Alan | Detay |
|------|-------|
| **Ne Yapar** | 3 katmanli aktivasyon: (1) Pasif Vitrin — emlaici portfoyunu sergiler, aranabilir; (2) Eslestirme Motoru — "musterim var, ilan ariyorum" alici-satici eslestirme; (3) Komisyon Akisi — komisyon anlasma, capraz satis. |
| **Neden Onemli** | WhatsApp gruplarindaki kaotik paylasimi yapilandirir. Ag etkisi = en guclu moat. Her yeni ofis agin degerini arttirir. |
| **Teknik Gereksinimler** | Eslestirme algoritmasi, bildirim sistemi, gizlilik/gorunurluk ayarlari, Telegram grup entegrasyonu, moderasyon paneli |
| **Kademe** | Pro: ilan paylasma + eslestirme, Elite: oncelikli eslestirme + "Super-Agent" rozeti |

### 6.8 Kredi Hesaplayici

| Alan | Detay |
|------|-------|
| **Ne Yapar** | Tutar, vade, faiz orani girerek aylik taksit tablosu olusturma. Banka faiz karsilastirmasi. Amortisman tablosu. |
| **Neden Onemli** | Sahada musteriye aninda kredi hesabi gostermek, alim kararini kolaylastirir. Quick win — dusuk efor, yuksek kullanim. |
| **Teknik Gereksinimler** | Basit matematik formulleri, banka faiz verisi (TCMB ortalama + scraping), responsive UI |
| **Kademe** | Starter+ (tum kademeler) |

### 6.9 Telegram Bot + Mini App

| Alan | Detay |
|------|-------|
| **Ne Yapar** | Telegram Bot API ile bildirimler (yeni eslestirme, fiyat degisikliigi, lead), inline keyboard ile hizli CRM eylemleri, Mini App ile dashboard gorunumu, dosya/konum paylasimi. |
| **Neden Onemli** | Ucretsiz, aninda deploy, sifir dis bagimlilik. Rate limit pratiikte yok. Mini App ile uygulama benzeri deneyim Telegram icinden. Turkiye emlak SaaS'ta ilk. |
| **Teknik Gereksinimler** | grammy/python-telegram-bot, webhook altyapisi, Mini App (responsive HTML5), auth token koprusu |
| **Kademe** | Starter: temel (sorgu), Pro: tam (veri girisi + rapor), Elite: yonetici modu |

### 6.10 WhatsApp Business API

| Alan | Detay |
|------|-------|
| **Ne Yapar** | BSP entegrasyonuyla musteri ilan paylasimi, randevu hatirlatma, template mesajlar, cift yonlu iletisim. Click-to-chat butonu, lead yakalama. |
| **Neden Onemli** | Turkiye'de son kullanicida %99 penetrasyon. Musteriye ulasmanin en dogal kanali. B2C vitrini. |
| **Teknik Gereksinimler** | BSP entegrasyonu (360dialog veya Twilio), template mesaj yonetimi, webhook, opt-in/opt-out, mesaj kuyrugu |
| **Kademe** | Pro: manuel link olusturucu, Elite: tam API entegrasyonu (aylik 50 msg dahil) |

### 6.11 EIDS Hibrit Dogrulama

| Alan | Detay |
|------|-------|
| **Ne Yapar** | Manuel EIDS belge numarasi girisi + OCR ile belge tarama dogrulama + "Dogrulanmis Ilan" rozeti. Resmi API acildiginda otomatik gecis icin hazir mimari. |
| **Neden Onemli** | EIDS yasal zorunluluk. Kolaylastiran platform, uyum araci olarak konumlanir. "Ceza yemek istemiyorsan bizi kullan" guclu satis argumani. |
| **Teknik Gereksinimler** | OCR motor (Tesseract/Cloud Vision), form dogrulama, rozet sistemi, audit log, EIDS uyumlu veri yapisi |
| **Kademe** | Pro: manuel giris + OCR, Elite: oncelikli dogrulama + bulk islem |

### 6.12 Coklu Site Scraping (Kosullu)

| Alan | Detay |
|------|-------|
| **Ne Yapar** | Sahibinden, Hepsiemlak, Emlakjet'ten aggregate piyasa verisi toplama. Fiyat trendi, mahalle bazli istatistik, ilan izleme. |
| **Neden Onemli** | Kapsamli pazar gorunumu. Degerleme modeli ve bolge analizleri guclendirir. Hicbir Turk emlak SaaS'i coklu site aggregasyonu sunmuyor. |
| **Teknik Gereksinimler** | Scrapy/Playwright parserlari, anti-scraping onlemleri (proxy pool, IP rotasyonu), veri normalizasyon, deduplication |
| **Kademe** | Elite (tam scraping), Pro (sinirli istatistik) |
| **Kosul** | Hukuki arastirma + ortaklik gorusmesi sonucuna bagli. Ortaklik saglanirsa resmi API, saglanmazsa sinirli istatistik modu |

### 6.13 Gelismis AI Fotograf

| Alan | Detay |
|------|-------|
| **Ne Yapar** | Virtual staging (bos odaya mobilya ekleme), dekorasyon onerisi, genis aci simulasyonu, nesne silme/ekleme, profesyonel portfolio olusturma. |
| **Neden Onemli** | Ilan fotograflari satis hizini %20-30 etkiler. Profesyonel fotografci tutamayan emlaiciye buyuk avantaj. |
| **Teknik Gereksinimler** | Stable Diffusion/DALL-E API veya self-hosted model, GPU compute, goruntu islleme pipeline |
| **Kademe** | Elite (sinirsiz), Pro (20 foto/ay) |

### 6.14 Akilli Fiyat Onerisi

| Alan | Detay |
|------|-------|
| **Ne Yapar** | Degerleme motorunun uzantisi: "En hizli satilacak fiyat" vs "Maksimum getiri fiyati" arasindaki optimal noktayi gosterir. Satis suresi tahmini (survival analysis). |
| **Neden Onemli** | Degerlemenin otesinde strateji onerisi. Saticiyi ikna etme araci. Hicbir rakip bunu yapmiyor. |
| **Teknik Gereksinimler** | Survival Analysis + LightGBM, bolge arz/talep verisi, sezonalite, ilan kalitesi skoru |
| **Kademe** | Pro+ |

### 6.15 Ofis Yonetim Paneli + Raporlama

| Alan | Detay |
|------|-------|
| **Ne Yapar** | Coklu kullanici yonetimi, danismani performans KPI'lari (satis hunisi, gosteriminler, kapatmalar), komisyon hesabi, ekip dashboard, otomatik haftalik rapor. |
| **Neden Onemli** | Ofis sahibinin "ofisin nabzini tek ekrandan gormesi". Franchise ofislere karsi rekabet avantaji. |
| **Teknik Gereksinimler** | Multi-tenant mimari, RBAC (rol bazli erisim), rapor uretici, KPI hesaplama motoru |
| **Kademe** | Elite |

---

## 7. Iletisim Stratejisi — Telegram + WhatsApp

### 7.1 Kanal Stratejisi

| Kanal | Rol | Kullanim Alani | Zamanlama |
|-------|-----|----------------|-----------|
| **Telegram** | Birincil (Operasyonel Merkez, B2B) | Danismani sisteme veri girerken, rapor alirken, portfoy ararken, diger emlaicilarla paylasim | Alpha'da TAM |
| **WhatsApp** | Ikincil (Musteri Vitrini, B2C) | Musteriye ilan paylasimi, yer gosterme konumu, randevu hatirlatma, lead yakalama | Beta'da TAM |
| **SMS** | Fallback | Kritik bildirimler (randevu, odeme) | Her iki fazda |
| **E-posta** | Raporlama | Haftalik rapor, fatura, kampanya | Her iki fazda |

### 7.2 Kanal Karsilastirma Tablosu

| Boyut | Telegram | WhatsApp | Stratejik Sonuc |
|-------|----------|----------|-----------------|
| **API Maliyeti** | UCRETSIZ — Bot API tamamen bedava | Meta BSP: mesaj basi ~0.05-0.15 TL | Telegram COGS'u dramatik dusurur |
| **Onay Sureci** | YOK — Bot aninda olusturulur | 4-12 hafta Meta BSP onayi | Telegram'da dis bagimlilik sifir |
| **Rate Limit** | Pratikte yok (30 mesaj/sn) | Ciddi — 1000 mesaj/gun, template zorunlu | Yuksek hacimli bildirimler Telegram'dan |
| **Mini App** | TAM HTML5 uygulama calistirma | Yok | Dashboard Telegram icinden acilabilir |
| **Bot Ekosistemi** | Zengin — inline keyboard, callback, dosya, konum | Sinirli — template mesajlar | CRM etkilesimleri Telegram'da esnek |
| **Penetrasyon (Turkiye)** | ~%35-40 aktif | ~%85+ aktif | WhatsApp mutlaka olmali ama Telegram'i bilenler sever |
| **Emlaici Aliskanligi** | Daha az yaygin | Zaten is icin kullaniyor | Starter: WhatsApp / Pro+Elite: Telegram + WhatsApp |

### 7.3 Unified Messaging Gateway Mimarisi

```
┌─────────────────────────────────────────────────┐
│              MESAJLASMA GATEWAY                  │
│         (Unified Messaging Service)              │
├─────────────┬───────────────────────┬────────────┤
│  TELEGRAM   │     WHATSAPP          │  SMS/EMAIL │
│  Bot API    │     Business API      │  (Fallback)│
│  (Ucretsiz) │     (Ucretli)         │            │
│  Mini App   │     Template Mesaj    │            │
├─────────────┴───────────────────────┴────────────┤
│              KANAL YONETICISI                     │
│  • Kullanici tercih yonetimi                     │
│  • Maliyet optimizasyonu (Telegram oncelikli)    │
│  • Fallback zinciri: Telegram→WhatsApp→SMS→Email │
│  • Kanal-agnostik mesaj formati                  │
└─────────────────────────────────────────────────┘
```

**Mimari Prensip:** Mesajlasma servisini **kanal-agnostik** tasarla. Mesajin icerigi tek yerde uretilir, kanal adaptorleri sadece format donusumu yapar. Bugun 2 kanal, yarin 5 kanal olabilir.

### 7.4 Faz Bazli Kanal Aktivasyonu

| Faz | Telegram | WhatsApp | Neden |
|-----|----------|----------|-------|
| **MVP-Alpha** | TAM — Bot + Mini App + Bildirimler | SINIRLI — Click-to-chat link | Telegram'da dis bagimlilik yok. WhatsApp BSP paralel basvuru |
| **MVP-Beta** | Gelismis — Grup entegrasyonu, gelismis Mini App | TAM — BSP onayli, template mesajlar, cift yonlu | BSP bu zamana kadar onayli olacak |
| **Faz 2+** | Kanal marketplace, 3. parti bot | Flows, katalog entegrasyonu | Ekosistem genisletme |

### 7.5 Fallback Zinciri

```
Telegram (birincil) → WhatsApp (ikincil) → SMS (acil) → E-posta (raporlama)
```

Her kullanicinin tercih ettigi kanal secimi vardir. Teslimat basarisiz olursa bir sonraki kanala otomatik gecis yapilir.

---

## 8. Fiyatlandirma Stratejisi

### 8.1 Paket Detaylari

| Ozellik / Paket | **STARTER (399 TL/ay)** | **PRO (799 TL/ay)** | **ELITE (1.499 TL/ay)** |
|:---|:---:|:---:|:---:|
| **Kullanici** | 1 Danismani | 3 Danismani | 10 Danismani (Ofis) |
| **Portfoy Limiti** | 20 | 100 | Sinirsiz |
| **AI Degerleme** | 10 sorgu/ay | 100 sorgu/ay | Sinirsiz |
| **Bolge Analiz** | Temel kart | Detayli + karsilastirma | Trend tahmin eklentisi |
| **AI Ilan Asistani** | — | 20 ilan/ay + 50 foto/ay | Sinirsiz |
| **CRM** | 50 musteri | 500 musteri | Sinirsiz + ekip CRM |
| **Portfoy Agi Erisimi** | Sadece goruntuleme | Ilan paylasma + eslestirme | Oncelikli eslestirme + Super-Agent rozeti |
| **EIDS** | — | Manuel giris + OCR | Oncelikli dogrulama + bulk |
| **Telegram Bot** | Temel (sorgu) | Tam (veri girisi + rapor) | Yonetici modu (ekip takibi) |
| **WhatsApp** | — | Manuel link olusturucu | Tam API (aylik 50 msg dahil) |
| **Scraping** | — | Sinirli istatistik | Tam erisim |
| **AI Fotograf** | — | 20 foto/ay | Sinirsiz |
| **Ofis Yonetim Paneli** | — | — | Tam erisim |
| **Deprem Risk Skoru** | Temel | Detayli | Detayli + tarihce |
| **Kredi Hesaplayici** | Temel | Gelismis | Gelismis |

### 8.2 COGS Analizi (Kullanici Basi Aylik)

| Maliyet Kalemi | Starter (399) | Pro (799) | Elite (1.499) | Aciklama |
|----------------|:---:|:---:|:---:|----------|
| Sunucu/altyapi | 15 TL | 25 TL | 40 TL | Olceklenen kullanici basi compute |
| AI Degerleme API | 20 TL | 35 TL | 50 TL | GPT/Claude API — sinirli vs sinirsiz |
| AI Ilan + Fotograf | — | 30 TL | 60 TL | Fotograf GPU yogun, Pro'da limitli |
| Telegram Bot | 0 TL | 0 TL | 0 TL | **Tamamen ucretsiz** |
| WhatsApp API | — | 25 TL | 45 TL | Template mesajlar, BSP ucreti |
| Scraping proxy | — | 15 TL | 30 TL | Residential proxy pool payi |
| EIDS dogrulama | 5 TL | 5 TL | 5 TL | OCR/islem maliyeti |
| Veri depolama | 5 TL | 10 TL | 15 TL | Fotograf, dokuman, rapor |
| Destek maliyeti | 5 TL | 10 TL | 20 TL | Otomatik + insan destek orani |
| **TOPLAM COGS** | **50 TL** | **155 TL** | **265 TL** | |
| **Brut Kar** | **349 TL** | **644 TL** | **1.234 TL** | |
| **Brut Marj** | **%87.5** | **%80.6** | **%82.3** | |

**Telegram Etkisi:** WhatsApp yerine Telegram'in varsayilan kanal olmasi, Pro segmentte COGS'u ~25 TL/kullanici/ay dusurur. 1.000 Pro kullanicida = yillik 300.000 TL tasarruf.

### 8.3 Unit Economics

| Metrik | Deger | Saglik Durumu |
|--------|:-----:|:---:|
| **ARPU** | 649 TL/ay | Saglikli |
| **Agirlikli COGS** | ~120 TL/ay | Dusuk (Telegram etkisi) |
| **Brut Kar/Kullanici** | ~529 TL/ay | Guclu |
| **Brut Marj** | ~%81.5 | SaaS ortalamasinin ustunde |
| **CAC** | 3.000-3.500 TL | Orta — Seed stratejisi ile dusurulebilir |
| **LTV (24 ay, %85 retention)** | ~12.700 TL | Guclu |
| **LTV/CAC** | **3.6-4.2x** | Saglikli (3x+ hedef) |
| **Payback Periyodu** | 5.5-6.5 ay | Makul |
| **MRR (Yil 1 sonu)** | ~973K TL | Yillik ~11.7M TL ARR |

---

## 9. Gelir Projeksiyonu

### 9.1 Yil 1 Hedef Senaryo: 1.500 Ucretli Kullanici

| Kademe | Dagilim | Kullanici | Aylik Gelir | Yillik Gelir |
|--------|:---:|:---:|:---:|:---:|
| Starter (399 TL) | %55 | 825 | 329.175 TL | 3.950.100 TL |
| Pro (799 TL) | %35 | 525 | 419.475 TL | 5.033.700 TL |
| Elite (1.499 TL) | %10 | 150 | 224.850 TL | 2.698.200 TL |
| **TOPLAM** | **%100** | **1.500** | **973.500 TL** | **11.682.000 TL** |

### 9.2 Konservatif Senaryo: 800 Kullanici

| Kademe | Dagilim | Kullanici | Aylik Gelir | Yillik Gelir |
|--------|:---:|:---:|:---:|:---:|
| Starter (399 TL) | %60 | 480 | 191.520 TL | 2.298.240 TL |
| Pro (799 TL) | %30 | 240 | 191.760 TL | 2.301.120 TL |
| Elite (1.499 TL) | %10 | 80 | 119.920 TL | 1.439.040 TL |
| **TOPLAM** | **%100** | **800** | **503.200 TL** | **6.038.400 TL** |

**Konservatif ARPU:** 629 TL/ay

### 9.3 MRR / ARR Projeksiyonu

| Ay | Hedef Senaryo MRR | Konservatif MRR |
|:---:|:---:|:---:|
| 6 (Alpha lansmani) | ~50K TL (50 ucretli) | ~30K TL (30 ucretli) |
| 9 | ~200K TL (300 ucretli) | ~100K TL (150 ucretli) |
| 12 (Yil 1 sonu) | ~973K TL (1.500 ucretli) | ~503K TL (800 ucretli) |

### 9.4 Break-even Analizi

| Metrik | Deger |
|--------|-------|
| Aylik OPEX (post-MVP) | ~1.1-1.3M TL |
| ARPU | 649 TL |
| Katki marji | ~%85 |
| **Break-even noktasi** | **~1.900 ofis** |
| Hedef senaryo break-even | ~14. ay |
| Konservatif break-even | ~18. ay |

---

## 10. Sprint Plani

### 10.1 Faz 0 — Temel Hazirlik (Hafta 1-10)

| Sprint | Hafta | Icerik | Kritik Cikti |
|--------|:---:|--------|-------------|
| **S0** | 1-2 | Mimari tasarim, tech stack kesinlestirme, veri modeli, auth altyapisi, CI/CD pipeline | Calisan iskelet, repo, Docker |
| **S1** | 3-4 | Unified Messaging Gateway mimarisi, Telegram Bot temel altyapisi | Calisan Telegram bot (echo level) |
| **S2** | 5-6 | Veri toplama altyapisi (TUIK, TCMB, AFAD, belediye), WhatsApp BSP basvurusu | Veri pipeline calisiir, BSP sureci baslatilmis |
| **S3** | 7-8 | AI degerleme model v0 (TKGM + TUIK verisi), temel UI bilesenleri | Prototip degerleme ciktisi, MAPE <%22 |
| **S4** | 9-10 | Seed ofis iletisimi, alpha kullanici anlasmalari, hukuki cerceve (scraping, KVKK, EIDS) | 30 ofis LOI, KVKK uyum dokumani |

**Faz 0 Butce:** ~₺1.8-2.0M
**Faz 0 Kritik Cikti:** Calisan iskelet + Telegram bot + AI model v0 + 30 seed ofis + BSP basvurusu yapilmis + Hukuki cerceve

### 10.2 MVP-Alpha (Hafta 11-24)

| Sprint | Hafta | Icerik | Bagimlilik |
|--------|:---:|--------|:---:|
| **S5** | 11-12 | AI Degerleme Motoru v1 (emsal karsilastirma, bolge analizi) | S3 model v0 |
| **S6** | 13-14 | Bolge Kartlari + Harita Entegrasyonu + Deprem Risk Skoru | S2 veri pipeline |
| **S7** | 15-16 | CRM Temel (musteri kayit, iletisim takip, not, etiket) | — |
| **S8** | 17-18 | AI Ilan Asistani (metin olusturma + temel fotograf iyilestirme) | — |
| **S9** | 19-20 | Portfoy Vitrin + Temel Eslestirme Motoru + Kredi Hesaplayici | S7 CRM |
| **S10** | 21-22 | Telegram Tam Entegrasyon (bildirimler, inline CRM, Mini App dashboard) | S1 gateway, S7 CRM |
| **S11** | 23-24 | QA, performans optimizasyonu, guvenlik taramasi, Alpha lansmani | Tumu |

**Alpha Go/No-Go Kriterleri (Hafta 24):**
- [ ] 100+ aktif kullanici
- [ ] 50+ ucretli abone
- [ ] NPS > 40
- [ ] Aylik churn < %10
- [ ] AI degerleme MAPE < %18
- [ ] Telegram bot stabil, mesajlasma basari orani %95+
- [ ] 50+ portfoy yuklenmiis

### 10.3 MVP-Beta (Hafta 25-38)

| Sprint | Hafta | Icerik | Bagimlilik |
|--------|:---:|--------|:---:|
| **S12** | 25-26 | WhatsApp Business API tam entegrasyon | BSP onayi |
| **S13** | 27-28 | EIDS Hibrit Akis (manuel numara giris + OCR dogrulama + rozet) | — |
| **S14** | 29-30 | Portfoy Paylasim Agi aktif (gelismis eslestirme + temel komisyon akisi) | S9 vitrin verisi |
| **S15** | 31-32 | Coklu Site Scraping (kosullu — ortaklik varsa tam, yoksa sinirli istatistik) | Hukuki cerceve |
| **S16** | 33-34 | Gelismis AI Fotograf (staging, virtual styling), Akilli Fiyat Onerisi | — |
| **S17** | 35-36 | Elite kademe ozellikleri (ofis yonetim paneli, coklu kullanici, raporlama) | — |
| **S18** | 37-38 | Tam QA dongusu, penetrasyon testi, performans testi, genel lansman | Tumu |

**Beta Go/No-Go Kriterleri (Hafta 38):**
- [ ] 500+ aktif kullanici
- [ ] Unit economics pozitif
- [ ] ARPU >= 600 TL
- [ ] Churn < %8
- [ ] Guvenlik taramasi temiz
- [ ] Portfoy aginda 80+ ofis, 50+ eslestirme

### 10.4 Gorsel Sprint Timeline (ASCII)

```
Hafta:  1────5────10────15────20────24────30────35────38
        |─── FAZ 0 ───|──── MVP-ALPHA ────|──── MVP-BETA ────|

Faz 0:  [Mimari][Gateway][Veri ][AI v0][Seed ]
Alpha:  ─────────────[Deger.][Bolge+Harita][CRM ][AI Ilan][Portfoy][Telegram][QA→🚀Alpha]
Beta:   ─────────────────────────────────[WhatsApp][EIDS][Portfoy Aktif][Scraping][AI Foto+][Elite][QA→🚀Beta]

Paralel: BSP basvurusu ────────────────────────────────→ (onay bekleniyor)
         Seed ofis     ─────────→ Alpha lansmani → organik buyume ──────────→
         Hukuki cerceve ──────────────────→ Scraping karari ──────→
```

---

## 11. Butce

### 11.1 Gelistirme Butcesi (Tek Seferlik)

| Kalem | Faz 0 | Alpha | Beta | Toplam |
|-------|:---:|:---:|:---:|:---:|
| **Backend gelistirme** | 0.6M | 1.8M | 1.5M | 3.9M |
| **Frontend gelistirme** | 0.3M | 1.2M | 1.0M | 2.5M |
| **AI/ML gelistirme** | 0.3M | 0.8M | 0.6M | 1.7M |
| **Telegram + Messaging Gateway** | 0.2M | 0.3M | 0.2M | 0.7M |
| **WhatsApp entegrasyon** | — | 0.1M | 0.4M | 0.5M |
| **Scraping altyapisi** | 0.1M | — | 0.5M | 0.6M |
| **DevOps/altyapi** | 0.15M | 0.2M | 0.3M | 0.65M |
| **QA/Test** | 0.05M | 0.2M | 0.3M | 0.55M |
| **UI/UX tasarim** | 0.1M | 0.15M | 0.1M | 0.35M |
| **Hukuki danismanlik** | 0.05M | 0.05M | 0.1M | 0.2M |
| **TOPLAM** | **1.9M** | **4.8M** | **5.0M** | **₺11.7M** |

### 11.2 Yillik Operasyonel Maliyet (Gelistirme Sonrasi)

| Kalem | Aylik | Yillik | Not |
|-------|:---:|:---:|-----|
| Sunucu/cloud | 15-25K | 180-300K | Olceklenen — kullanici basi |
| AI API (GPT/Claude) | 30-50K | 360-600K | Degerleme + Ilan asistani |
| Telegram | 0 | 0 | **Ucretsiz** |
| WhatsApp BSP | 10-30K | 120-360K | Mesaj hacmine bagli |
| Scraping proxy | 5-15K | 60-180K | Kosullu — ortaklik varsa duser |
| Veri kaynaklari | 5-10K | 60-120K | TKGM, belediye API |
| Destek ekibi | 20-40K | 240-480K | Olceklenen |
| **TOPLAM** | **85-170K** | **₺1.0-2.0M** | |

### 11.3 Toplam ve Net Butce

| Kalem | Tutar |
|-------|:---:|
| Gelistirme butcesi (brut) | ₺11.7M |
| Orkestrator tasarrufu (%20-30) | -₺2.3M ~ -₺3.5M |
| **Net gelistirme butcesi** | **₺8.2-9.4M** |
| Yillik operasyonel (post-MVP) | ₺1.0-2.0M |
| **Ilk 12 ay toplam (net)** | **₺9.2-11.4M** |

**Orkestrator Tasarruf Karsilastirmasi:**

| Kalem | Klasik Gelistirme | Orkestrator ile | Tasarruf |
|-------|:---:|:---:|:---:|
| Gelistirme butcesi | ₺11.7M | ₺8.2-9.4M | %20-30 |
| Gelistirme suresi | 38 hafta | 34-36 hafta | %5-10 |
| Hata orani | Sektor ortalamasi | -%30-40 (AI code review) | Dolayli tasarruf |

---

## 12. Go-to-Market (GTM) Stratejisi

### 12.1 Seed the Network: 30-50 Anchor Ofis

| Adim | Zamanlama | Hedef |
|------|:---:|-------|
| 1. Hedef ofis belirleme | Faz 0 (Hafta 1-4) | Istanbul Anadolu Yakasi'ndan 30 "anchor" ofis secimi |
| 2. Ucretsiz onboarding | Alpha Hafta 1-4 | 30 ofis = ~300 ilan portfoy yukleme |
| 3. Organik buyume | Alpha Hafta 5-16 | Capraz referanslarla +50 ofis |
| 4. Eslestirme aktivasyonu | Alpha Hafta 12 | Minimum 50 ofis = anlamli eslestirme havuzu |
| **Hedef: Alpha sonunda** | | **80+ ofis, 800+ ilan, 50+ eslestirme** |

**Neden Istanbul Anadolu Yakasi:**
- Turkiye emlak islemlerinin ~%25'i Istanbul'da
- Anadolu yakasi yogun ofis konsantrasyonu
- Hem luks hem orta segment mevcut
- Kentsel donusum devam ediyor (veri zenginligi)
- Saha ekibi lojistik olarak yonetilebilir

### 12.2 Telegram Viral Loop

1. **Degerleme Raporu Paylasimi:** Emlaici museterisine PDF rapor gonderir. Raporda platform logosu + "Siz de gayrimenkulunuzu degerletin" CTA'si
2. **Bot Paylasim:** Emlaici meslektasina "Bu botu dene, sorgunun cevabini 3 saniyede aliyon" der
3. **Portfoy Paylasim Daveti:** "Bu portfoyu gormek icin platformumuza kayit olun" → B2B viral

### 12.3 Freemium → Pro Donusum Akisi

```
Ucretsiz Kayit → 10 Degerleme/ay → Sinira Ulasir → "Pro'ya Gec: Sinirsiz Degerleme + AI Ilan + Portfoy Agi"
     ↓                                                        ↓
 Telegram Bot                                            799 TL/ay
 (aninda deger)                                      (30 gun ucretsiz deneme)
```

### 12.4 WhatsApp Viral Loop (Beta'da)

- Her uretilen ilan PDF'inde platform logosu
- "Bu ilan [Platform] ile hazirlanmistir" watermark
- Musteriye atilan her link = potansiyel lead
- "WhatsApp ile Sor" butonu web sitesinde

### 12.5 Musteri Edinme Kanallari

| Kanal | Strateji | Tahmini CAC | Oncelik |
|-------|----------|:---:|:---:|
| Saha Satis | 2-3 kisilik ekip, ofis ofis demo | 3.000 TL | YUKSEK (ilk 100) |
| Dijital Reklam | Google Ads + Meta Ads | 1.500 TL | ORTA |
| Icerik Pazarlama | Blog, YouTube egitim | 500 TL | DUSUK (uzun vadeli) |
| Sektor Etkinlikleri | GYODER, RE/MAX konvansiyonu | 2.000 TL | ORTA |
| Referral Programi | Mevcut musteri tavsiyesi = 1 ay ucretsiz | 800 TL | YUKSEK (Faz 2+) |
| Telegram Bot Viral | Organik paylasim | ~0 TL | YUKSEK |

---

## 13. Kullanici Yolculuk Haritasi

### Tam Akis: Telegram + WhatsApp + Web Platform

```
1. KESFETME
   ├─ Instagram/Google rekllami: "Bolgenizdeki fiyat degisimini biliyor musunuz?"
   ├─ Meslektas tavsiyesi (viral loop)
   └─ Telegram Bot kesfedme: "Kadikoy 3+1 fiyatlari" sorusuna aninda cevap

2. DENEME (Aha! Momenti)
   ├─ Telegram Bot'a adres/konum gonderir → 3 saniyede degerleme ciktisi
   ├─ Mini App'te bolge analiz kaartini gorur → "Vay, bunu bilmiyordum"
   └─ Ucretsiz 10 degerleme ile platforma alisir

3. SATIN ALMA
   ├─ Starter (399 TL) veya Pro (799 TL) abone olur
   ├─ 30 gun ucretsiz deneme (Pro)
   └─ Portfoyunu sisteme yukler → AI ilan metni olusturur

4. KULLANIM (Stickiness)
   ├─ Her sabah Telegram'dan "Piyasa Raporu" alir
   ├─ CRM'e musteri kayit → otomatik eslestirme bildirimi gelir
   ├─ AI ile ilan hazirlar → zamandan tasarruf hisseder
   └─ Portfoy vitrininde gorulur → diger ofislerden iletisim gelir

5. BAGIMLILIK
   ├─ Haftalik bolge raporu → vazgecilmez
   ├─ Musteri-portfoy eslestirme → kayip azalir
   ├─ Veri birikimi → ayrilmanin maliyeti artar (data lock-in)
   └─ WhatsApp ile musteriye profesyonel PDF atar → "bu olmadan yapamam"

6. YAYILIM
   ├─ "Bu yazilimi kullanmayan ofise sasiririm" sozu
   ├─ Portfoy paylasim daveti → zorunlu viral buyume
   ├─ Degerleme raporu paylasimi → logo ile organik reklam
   └─ "Is arkadasima sistemden pasliyorum, oradan kabul et" → ag buyur
```

---

## 14. Portfoy Paylasim Agi Stratejisi

### 14.1 Uc Katmanli Aktivasyon

| Katman | Ne Yapar | Zamanlama | Deger | Risk |
|--------|---------|:---------:|:---:|:---:|
| **1. Pasif Vitrin** | Emlaici portfoyunu gosterir, aranabilir | Alpha (Hafta 12-16) | Dusuk-Orta | Dusuk |
| **2. Eslestirme Motoru** | "Musterim var, ilan ariyorum" alici-satici eslestirme | Alpha (Hafta 16-20) | Yuksek | Orta |
| **3. Aktif Paylasim + Komisyon** | Komisyon anlasmasi, capraz satis, kontrat yonetimi | Beta (Hafta 25-30) | Cok Yuksek | Cok Yuksek |

### 14.2 Seed Stratejisi

| Adim | Zamanlama | Hedef |
|------|:---------:|-------|
| 1. Hedef ofis belirleme | Faz 0 (Hafta 1-4) | Istanbul'dan 30 "anchor" ofis |
| 2. Ucretsiz onboarding | Alpha Hafta 1-4 | 30 ofis = ~300 ilan yuklemesi |
| 3. Organik buyume | Alpha Hafta 5-16 | Capraz referansla +50 ofis |
| 4. Eslestirme aktivasyonu | Alpha Hafta 12 | Min. 50 ofis = anlamli havuz |
| **Alpha sonunda hedef** | | **80+ ofis, 800+ ilan, 50+ eslestirme** |

### 14.3 Kritik Kutle Metrikleri

| Metrik | Esik | Neden |
|--------|:---:|-------|
| Aktif ofis sayisi | 50+ | Eslestirme algoritmasi anlamli sonuc uretebilir |
| Portfoy (ilan) sayisi | 500+ | Yeterli cesiitlilik |
| Haftalik eslestirme | 20+ | Kullanicilar deger gorur |
| Aktif paylasim orani | %30+ | Ag "calisiyor" hissi |

### 14.4 Moderasyon Plani

- Alpha'da 1 moderator + 1 topluluk yoneticisi (pilot icin)
- Moderasyon SLO: 24 saat icinde donus
- "Raporla/Engelle" mekanizmasi
- Guven skoru sistemi (Beta'da)
- Platform Etik Kurallari — kabul edenler sisteme alinir

---

## 15. Risk Matrisi

### 15.1 Risk Tablosu

| # | Risk | Etki (1-10) | Olasilik (1-10) | Risk Skoru | Mitigasyon |
|---|------|:---:|:---:|:---:|----------|
| **R1** | Coklu scraping hukuki riski (ToS + KVKK) | 9 | 7 | **63** | Ortaklik oncelikli, yoksa sadece istatistik. Scraping kritik yol DISINDA |
| **R2** | Kapsam sissmesi (feature creep) — 15 ozellik | 8 | 7 | **56** | Iki katmanli MVP (Alpha = 9 ozellik, sinirli ve odakli) |
| **R3** | WhatsApp BSP onay gecikmesi (>12 hafta) | 7 | 5 | **35** | Telegram varsayilan kanal, WhatsApp Beta'da. Fallback SMS |
| **R4** | Portfoy agi kritik kutle sagllanamama | 8 | 4 | **32** | Seed strategy (30 ofis), Alpha'da olcum, karar noktasi Alpha sonunda |
| **R5** | AI API maliyet patlamasi (fotograf) | 6 | 5 | **30** | Fotograf Alpha'da "basit", Beta'da "gelismis". Hard limit/kullanici |
| **R6** | EIDS resmi API'nin hic gelmemesi | 6 | 4 | **24** | Hibrit cozum yeterli, manuel giris kabul edildi |
| **R7** | Rakip kopyalama (Arveya, Fizbot, Endeksa) | 5 | 4 | **20** | Veri moat + ag etkisi + Telegram Mini App diferansiyeli |
| **R8** | Telegram penetrasyonunun dusuk kalmasi | 4 | 4 | **16** | WhatsApp yedek kanal, cift kanal mimarisi notralize eder |
| **R9** | Deprem/afet veri kaynagi erisim sorunu | 5 | 3 | **15** | Birden fazla kaynak (AFAD, Kandilli, belediye), cache mekanizmasi |
| **R10** | Ekip tukenmisiligi (38 hafta maraton) | 6 | 3 | **18** | Iki katmanli yapi moral verir — Alpha lansmani ara hedef |

### 15.2 Risk Isi Haritasi (ASCII)

```
        Olasilik →   1-2    3-4    5-6    7-8    9-10
Etki ↓
9-10                                      [R1]
7-8                  [R4]          [R3]   [R2]
5-6                  [R9]  [R6]   [R5]
3-4                  [R8]  [R10]  [R7]
1-2
```

### 15.3 Top 3 Risk ve Detayli Mitigasyon

**R1 — Scraping Hukuki (Skor: 63)**
- Faz 0'da hukuki arastirma: ToS analizi, scraping hukuku, emsal kararlar
- Paralel: Is ortakligi gorusmeleri (Hepsiemlak, Zingat)
- Ortaklik saglanirsa → resmi API
- Ortaklik saglanmazsa → sinirli aggregate istatistik (bireysel ilan degil)
- Scraping'i core ozellik yerine "veri zenginlestirme katmani" olarak konumlandir

**R2 — Kapsam Sismesi (Skor: 56)**
- Iki katmanli MVP bunu dogrudan adresliyor
- Alpha = 9 odakli ozellik → erken gelir, erken feedback
- Beta basarisiz olursa Alpha tek basina yasayabilir bir urundur
- Her sprint sonunda kapsam review

**R3 — WhatsApp BSP (Skor: 35)**
- Telegram Alpha'da tam — WhatsApp Beta'da
- BSP basvurusu Faz 0'da baslatilir (paralel)
- Click-to-chat ile gecici cozum
- Bu risk Tur 4'te dramatik dustu (Telegram sayesinde)

### 15.4 Kullanici Kararlarinin Risk Etkisi

| Karar | Azalttigi Riskler | Arttirdigi Riskler |
|-------|-------------------|-------------------|
| Iki katmanli MVP | R2 (kapsam sismesi) ⬇ | — |
| 399/799/1499 fiyat | R5 (AI maliyet) ⬇ COGS karsilanir | — |
| Telegram eklenmesi | R3 (WhatsApp bagimliligi) ⬇⬇ | R8 (Telegram penetrasyonu) ⬆ ama dusuk |
| EIDS hibrit | R6 (API yoklugu) ⬇⬇ | — |
| Portfoy kesinlikle MVP | R4 (kritik kutle) ⬆ | — (seed stratejisi mitigate eder) |

---

## 16. Kritik Karar Noktalari (Gate'ler)

| Gate | Zamanlama | Karar | Gecis Kriteri |
|------|:---:|-------|-------------|
| **G0** | Hafta 10 (Faz 0 sonu) | Alpha'ya devam mi? | AI model v0 calisiyor + 20+ seed ofis LOI + BSP basvurusu yapilmis + KVKK uyum dokumani |
| **G1** | Hafta 16 (Alpha ortasi) | Portfoy eslestirme acilsin mi? | 50+ portfoy yuklenmis + eslestirme algoritmasi dogrulanmis |
| **G2** | Hafta 24 (Alpha sonu) | Beta'ya gecis mi? | 100+ aktif kullanici + 50+ ucretli + NPS 40+ + aylik churn <%10 |
| **G3** | Hafta 30 (Beta ortasi) | Scraping acilsin mi? | Hukuki cerceve tamam (ortaklik veya hukuki gorus) + altyapi hazir |
| **G4** | Hafta 38 (Beta sonu) | Genel lansman mi? | 500+ aktif + unit economics pozitif + guvenlik taramasi temiz |

**Onemli:** Her gate'te "hayir" cevabi mumkun. G2'de Alpha yeterli traction gostermezse Beta kapsami daraltilabilir veya pivot edilebilir. Bu esneklik iki katmanli MVP'nin en buyuk avantaji.

---

## 17. Kaynak Plani

### 17.1 Cekirdek Ekip (Orkestrator AI Agent'lar)

| # | Agent | Rol | Birincil Faz |
|---|-------|-----|-------------|
| 1 | claude-teknik-lider | Mimari kararlar, tech stack | Faz 0 |
| 2 | gemini-uiux-tasarimci | UI/UX tasarim stratejisi | Faz 0 + Alpha |
| 3 | claude-web-arastirmaci | Veri kaynaklari, teknoloji karsilastirma | Faz 0 |
| 4 | gemini-kodlayici | Standart sayfa/bilesen gelistirme | Alpha + Beta |
| 5 | claude-kidemli-gelistirici | Karmasik kod, refactoring, mesajlasma | Alpha + Beta |
| 6 | codex-junior-gelistirici | Basit/tekrarlayan gorevler | Alpha + Beta |
| 7 | claude-qa-senaryo | QA test senaryosu, test plani | Alpha sonu + Beta |
| 8 | gemini-test-muhendisi | Fonksiyonel test calistirma | Alpha sonu + Beta |
| 9 | claude-devops | CI/CD, deployment, altyapi | Tum fazlar |
| 10 | claude-guvenlik-analisti | Guvenlik analizi, penetrasyon | Beta |
| 11 | claude-ux-mikrokopi | UX mikro-kopya, CTA metinleri | Alpha + Beta |
| 12 | claude-misafir-tester | Browser testi, responsive | Beta |

### 17.2 Faz Bazli Agent Atama Plani

| Faz | Oncelikli Agent'lar | Ikincil Agent'lar |
|-----|---------------------|-------------------|
| **Faz 0** | claude-teknik-lider, gemini-uiux-tasarimci, claude-web-arastirmaci | claude-devops, claude-guvenlik-analisti |
| **Alpha S5-S8** | gemini-kodlayici, claude-kidemli-gelistirici, codex-junior-gelistirici | claude-qa-senaryo, gemini-test-muhendisi |
| **Alpha S9-S11** | gemini-kodlayici, claude-kidemli-gelistirici | claude-ux-mikrokopi, claude-misafir-tester |
| **Beta S12-S15** | claude-kidemli-gelistirici, gemini-kodlayici | claude-guvenlik-analisti, claude-devops |
| **Beta S16-S18** | claude-qa-senaryo, gemini-test-muhendisi, claude-devops | codex-teknik-yazar |

### 17.3 Ek Insan Kaynagi Gereksinimleri

| Rol | Ne Zaman | Neden |
|-----|----------|-------|
| Hukuk Danismani | Faz 0 (part-time) | KVKK, scraping, EIDS hukuki cerceve |
| Saha Satis (2-3 kisi) | Alpha lansman oncesi | Seed ofis iliskileri, onboarding |
| Moderator (1 kisi) | Alpha Hafta 12+ | Portfoy paylasim agi moderasyonu |
| Topluluk Yoneticisi (1 kisi) | Beta | Pilot ops, buyume yonetimi |

---

## 18. Teknik Altyapi Ozeti

### 18.1 Onerilen Tech Stack

| Katman | Teknoloji | Gerekce |
|--------|-----------|---------|
| **Frontend (Web)** | Next.js 15 (React 19) | SSR + SEO kritik, App Router, ISR |
| **Frontend (Mobil)** | Telegram Mini App + PWA | Alpha'da yeterli, native Faz 2+ |
| **Backend API** | FastAPI (Python 3.12) | ML ekosistemiyle dogal uyum, async I/O |
| **Veritabani** | PostgreSQL 16 + PostGIS | Spatial sorgular, JSONB, olgunluk |
| **Arama** | Elasticsearch / Meilisearch | Full-text, filtreleme, geo-distance |
| **Onbellek** | Redis 7 | Session, cache, rate limiting, Celery broker |
| **Gorev Kuyrugu** | Celery + Redis | Veri toplama, ML egitim, toplu bildirim |
| **Mesajlasma** | Unified Messaging Gateway (ozel) | Kanal-agnostik, Telegram + WhatsApp + SMS |
| **ML Framework** | LightGBM + scikit-learn + HuggingFace | Tablo verisi, NLP, goruntu |
| **Harita** | MapLibre GL JS + OpenStreetMap | Acik kaynak, isii haritalari, ozel stil |
| **Dosya Depolama** | MinIO (self-hosted S3) | Fotograf, dokuman, rapor |
| **CI/CD** | GitHub Actions + Docker Compose | Otomatik test, build, deploy |
| **Monitoring** | Sentry + Grafana + Prometheus | Hata takibi, performans metrikleri |

### 18.2 Veri Kaynaklari ve Erisim Stratejisi

| Kaynak | Veri Tipi | Erisim | Risk |
|--------|----------|--------|:---:|
| **TUIK MEDAS** | Konut satis istatistikleri, nufus | REST API (SDMX) | DUSUK |
| **TCMB EVDS** | Konut fiyat endeksi, faiz, doviz | REST API | DUSUK |
| **AFAD TDTH** | Deprem tehlike haritasi, PGA | WMS REST | DUSUK |
| **TKGM Parsel** | Ada/parsel, koordinat | WMS/WFS | ORTA |
| **IBB Acik Veri** | Imar plani, nufus, ulasim | API | ORTA |
| **Sahibinden/Hepsiemlak** | Ilan verileri, fiyatlar | Ortaklik (oncelik) / kosullu scraping | YUKSEK |
| **Google Maps/OSM** | POI, geocoding | API | DUSUK |
| **Bankalar** | Kredi faiz oranlari | Scraping + ortaklik | ORTA |

**Katmanli Veri Toplama Prensibi:** Once kolay kaynaklar (TUIK, TCMB, AFAD) → sonra orta zorlukta (TKGM, belediye) → en son riskli (ilan siteleri).

### 18.3 AI Model Stratejisi

| Model | Girdi | Cikti | Faz |
|-------|-------|-------|:---:|
| **Otomatik Degerleme (AVM)** | m2, oda, kat, yas, konum, emsaller | Tahmini fiyat + guven araligi | Alpha |
| **Ilan Metni Uretimi** | Mulk ozellikleri, fotograf etiketleri | SEO uyumlu ilan metni | Alpha |
| **Musteri-Portfoy Eslestirme** | Musteri kriterleri, portfoy ozellikleri | Eslestirme skoru + sirali liste | Alpha (kural tabanli) → Beta (ML) |
| **Fotograf Iyilestirme** | Ham fotograf | Isik/perspektif duzeltilmis fotograf | Alpha (temel) → Beta (gelismis) |
| **Akilli Fiyat Onerisi** | Fiyat, bolge, arz/talep, sezonalite | "Hizli satis" vs "max getiri" fiyati | Beta |
| **Fiyat Anomali Tespiti** | Ilan fiyati vs bolge ortalamasi | Sapma uyarisi | Alpha |

### 18.4 Altyapi Gereksinimleri

| Bilesen | MVP (Faz 0-Alpha) | Faz 2+ |
|---------|:---:|:---:|
| Sunucu | 8 vCPU, 32 GB RAM, 500 GB NVMe | Horizontal scaling, Kubernetes |
| Veritabani | PostgreSQL + PostGIS + TimescaleDB | Read replica, sharding |
| Nesne Depolama | 500 GB (fotograflar) | 2+ TB buyume plani |
| CDN | CloudFlare | CloudFront |
| ML Egitim | CPU yeterli (LightGBM) | GPU sadece goruntu modelleri |

---

## 19. Hukuki ve Uyum Gereksinimleri

### 19.1 KVKK Uyum

| Gereksinim | Uygulama |
|-----------|----------|
| Kisisel veri isleme rizasi | Kayit aninda acik riza, aydinlatma metni |
| Veri minimizasyonu | Sadece gerekli kisisel veri toplanacak |
| Veri silme hakki | "Hesabimi sil" butonu, 30 gun icinde tam silme |
| Cerez politikasi | OneTrust/CookieBot entegrasyonu |
| VERBIS kaydi | Veri sorumlusu olarak VERBIS'e kayit zorunlu |
| Veri ihlali bildirimi | KVKK Kurulu'na 72 saat icinde bildirim proseduru |
| Privacy by Design | Sistem mimarisinde kisisel veri ayrimi (PII vs anonim) |

### 19.2 EIDS Yasal Cerceve

| Konu | Durum | Yaklasim |
|------|-------|----------|
| Resmi API | Su an mevcut degil | Manuel giris + OCR, resmi API takibi |
| e-Devlet erisimi | 3. taraf erisimi icin protokol yok | Kullanicinin kendi EIDS numarasini girmesi |
| e-Devlet scraping | TCK 243-244 riski (bilisim sistemine girme) | **KESINLIKLE YAPILMAYACAK** |
| Uyum stratejisi | Hibrit cozum | Manuel giris + belge OCR + "Dogrulanmis Ilan" rozeti |

### 19.3 Scraping Hukuki Risk ve ToS Analizi

| Site | ToS Durumu | Risk | Yaklasim |
|------|-----------|:---:|----------|
| Sahibinden.com | Otomatik veri cekmeyi acikca yasakliyor | YUKSEK | Ortaklik gorusmesi oncelikli, yoksa sadece aggregate istatistik |
| Hepsiemlak | Sinirli ortaklik programi | ORTA | Is ortakligi gorusssmesi |
| Emlakjet | API bilgisi kamuya acik degil | ORTA | Dogrudan is gelistirme |
| Zingat | REIDIN ortakligi var | DUSUK-ORTA | REIDIN uzerinden veri ortakligi |

**Hukuki Ilkeler:**
- Kisisel veri (ad, telefon) TOPLANMAYACAK
- Sadece aggregate fiyat/ozellik verileri
- Dusuk frekans, sinirli hacim
- Ortaklik her zaman scraping'e tercih edilir
- Faz 0'da hukuki gorus alinacak

### 19.4 Veri Saklama ve Guvenlik Politikasi

| Alan | Politika |
|------|---------|
| Veri siiniflandirma | PII (kisisel) vs anonim veri ayrilmis depolama |
| Sifreleme | AES-256 at-rest, TLS 1.3 in-transit |
| Erisim kontrolu | RBAC + audit log |
| Yedekleme | Gunluk otomatik, 30 gun saklama |
| Penetrasyon testi | Beta lansmansindan once zorunlu |
| Olay mudahale | 72 saat KVKK bildirim, incident response plani |

---

## 20. Sonraki Adimlar

### Kullanici Onayi Sonrasi Yapilacaklar

| # | Adim | Sorumlu Agent | Sure | Oncelik |
|---|------|:---:|:---:|:---:|
| 1 | **Product Backlog olusturma** — 15 ozellik → user story'lere ayirma | gemini-urun-yoneticisi | 2-3 gun | KRITIK |
| 2 | **Teknik mimari dokuman** — Tech stack, veri modeli, API tasarimi, mesajlasma gateway | claude-teknik-lider | 2-3 gun | KRITIK |
| 3 | **UI/UX tasarim stratejisi** — Wireframe + Stitch prototipleri | gemini-uiux-tasarimci | 3-5 gun | KRITIK |
| 4 | **Operasyonel sprint plani detaylandirma** — Gorev kirilimi, bagimlilik haritasi | codex-operasyonel-planlayici | 1-2 gun | YUKSEK |
| 5 | **Hukuki cerceve baslangic** — KVKK danismanligi, scraping hukuki arastirma | Hukuk danismani (dis) | Hemen | YUKSEK |
| 6 | **Seed ofis aday listesi** — Istanbul Anadolu Yakasi 30 hedef ofis | claude-web-arastirmaci | 2-3 gun | ORTA |
| 7 | **WhatsApp BSP basvurusu** — 360dialog veya Twilio uzerinden | claude-devops | 1 gun | ORTA (paralel) |
| 8 | **Faz 0 Sprint S0 baslatma** — Mimari tasarim, repo, CI/CD | Orkestra sefi koordinasyonu | — | BASLA |

### Kritik Yol

```
Kullanici onayi → [1. Backlog + 2. Mimari (paralel)] → [3. UI/UX] → [4. Sprint plani] → Faz 0 S0 Basla
                   ↕ (paralel)
                   [5. Hukuki] + [6. Seed ofis] + [7. BSP basvurusu]
```

---

*Son guncelleme: 2026-02-20*
