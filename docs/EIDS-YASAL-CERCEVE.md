# EİDS (Elektronik İlan Doğrulama Sistemi) Yasal Çerçeve

**Tarih:** 2026-02-21
**Versiyon:** v1.0
**Kapsam:** Emlak Teknoloji Platformu — EİDS Entegrasyon Gereksinimleri

---

## 1. EİDS Nedir?

### 1.1 Tanım ve Amaç

**EİDS (Elektronik İlan Doğrulama Sistemi)**, T.C. Ticaret Bakanlığı tarafından geliştirilen, internet ortamında yayınlanan emlak ve ikinci el motorlu araç ilanlarının doğruluğunu ve güvenilirliğini artırmayı amaçlayan bir doğrulama sistemidir.

**Portal:** https://eids.ticaret.gov.tr/

**Temel amaçlar:**
- Sahte ilanların önlenmesi
- İlan kirliliğinin azaltılması
- Tüketici mağduriyetlerinin önlenmesi
- Yetki belgesiz ve kayıt dışı emlakçılık faaliyetlerinin engellenmesi
- Spekülatif fiyat artışlarının önüne geçilmesi

### 1.2 Yasal Dayanak

- **Taşınmaz Ticareti Hakkında Yönetmelik** — 31 Ağustos 2023 değişikliği
- **6563 sayılı Elektronik Ticaretin Düzenlenmesi Hakkında Kanun**
- **7416 sayılı Kanun** (6563'te değişiklik — 1 Temmuz 2022)

### 1.3 Uygulama Takvimi

| Faz | Kapsam | Tarih | Durum |
|-----|--------|-------|-------|
| **Faz 1** | Kimlik Doğrulama (Taşınmaz) | 1 Kasım 2023 | Aktif |
| **Faz 2 — Kiralik** | Yetki Doğrulama (Kiralık Taşınmaz) | Pilot: 15 Eylül 2024, Zorunlu: 1 Ocak 2025 | Aktif |
| **Faz 2 — Satılık İşyeri** | Satılık İşyeri İlanları | 7 Nisan 2025 | Aktif |
| **Faz 2 — Araç** | İkinci El Motorlu Araç | Pilot: 3 Şubat 2025, Zorunlu: 1 Nisan 2025 | Aktif |
| **Faz 3 — Tüm Satılık** | Konut, arsa, işyeri dahil tüm satılık taşınmaz | Pilot (İst/Ank/İzm): 1 Şubat 2026, **Ülke geneli: 15 Şubat 2026** | **AKTİF** |

> **Güncel durum (21 Şubat 2026):** EİDS yetki doğrulaması **tüm taşınmaz ilanlarında** (kiralık + satılık) ve **tüm ikinci el motorlu araç ilanlarında** ülke genelinde zorunlu olarak uygulanmaktadır.

### 1.4 Kapsam Dahilindeki İlan Türleri

**Taşınmaz ilanları** (kiralık + satılık):
- Konutlar (daire, villa, müstakil ev)
- Arsalar
- İşyerleri
- Ticari gayrimenkuller

**İkinci el motorlu kara taşıtları:**
- Otomobiller
- Ticari araçlar
- Motosikletler

### 1.5 Taşınmaz Numarası

Her gayrimenkule Tapu ve Kadastro Genel Müdürlüğü (TKGM) tarafından verilen benzersiz tanımlama numarasıdır.

| Bilgi | Açıklama |
|-------|----------|
| Eski tapu senetlerinde | "Zemin Sistem No" adı altında |
| Yeni tip tapu senetlerinde | "Taşınmaz No" alanı altında |
| e-Devlet'te | "Tapu Bilgileri Sorgulama" hizmetinden öğrenilebilir |
| Format | Sayısal kod (genellikle 6-8 haneli) |

---

## 2. Platform Sorumlulukları

### 2.1 Kimler İlan Verebilir?

**Bireysel ilanlar için:**

| Yetkilendirilmiş Kişi | Koşul |
|-----------------------|-------|
| Taşınmaz/araç sahibi (malik) | Doğrudan |
| Sahibin eşi | Aile bağı doğrulaması |
| Birinci derece kan hısımları | Ebeveynler, çocuklar |
| İkinci derece kan hısımları | Kardeşler, büyük ebeveynler, torunlar |

> **Önemli:** Hısımlar ilan verebilir ancak **malik adına emlak firmasını yetkilendiremez** — yetkilendirme yalnızca malik tarafından yapılabilir.

**Kurumsal ilanlar için:**
- Yalnızca **taşınmaz ticareti yetki belgesine sahip** emlak işletmeleri
- Malik tarafından **e-Devlet üzerinden yetkilendirilmiş** olması şart
- Yetki süresi **minimum 3 ay**

### 2.2 Aracı Hizmet Sağlayıcı (Platform) Yükümlülükleri

#### a) Kimlik Doğrulama (Faz 1)
- Kullanıcı kimlik doğrulaması **e-Devlet SSO** entegrasyonu ile yapılmalı
- Kimlik doğrulanmadan ilan girişi **engellenmeli**

#### b) Yetki Doğrulama (Faz 2+)
- Bireysel ilan girişinde **taşınmaz numarasının girilmesi** zorunlu
- Sistem EİDS API üzerinden **otomatik yetki kontrolü** yapar
- Yetki yoksa ilan **yayınlanamaz**
- Kurumsal ilanlarda emlak işletmesinin yalnızca **yetkilendirilmiş taşınmazlar** için ilan girmesi sağlanmalı

#### c) EİDS Logosu
- Doğrulama yapılarak yayımlanan ilanlarda **"EİDS'den yetki doğrulamasının yapıldığı"** yönünde logo/ibare gösterilmeli

#### d) Bildirim Yükümlülükleri
- Yetki süresi dolduğunda veya iptal edildiğinde ilanın durumu güncellenmeli
- Yetki bitiş tarihi ilan bitiş tarihinden önce ise, sistem yetki bitişinde yeniden doğrulama yapar
- Doğrulama başarısız olursa **ilan kaldırılır**

#### e) İstisnai Durumlar
- **Tapusu olmayan taşınmazlar:** "Tapum Yok" seçeneği ile doğrulama dışında ilan verilebilir (tamamlanmamış konut projeleri, hazine arazileri)
- **e-Devlet erişimi olmayan yabancı vatandaşlar:** Doğrulama sistemine dahil edilmez
- Bu istisnai ilanlar **Bakanlık tarafından yakından takip edilmektedir**

#### f) Kayıt ve Saklama
- 6563 sayılı Kanun kapsamında tüm bilgi, belge, defter ve elektronik kayıtlar **10 yıl süreyle** saklanmalı

### 2.3 Cezalar

| İhlal | Yaptırım |
|-------|----------|
| Yanıltıcı bilgi ile ilan girişi | Yetki belgesinin iptali + **684.214 TL** idari para cezası |
| EİDS entegrasyonu yapmama | Platformun faaliyetinin durdurulması riski |
| Bildirim yükümlülüğüne aykırılık | İdari para cezası |

### 2.4 Beklenen Etki

- Mevcut yaklaşık 1,2 milyon emlak ilanının **~%20'si** (240.000 civarında) sistemden düşeceği tahmin edilmektedir
- "Ayakçı" denilen yetkisiz emlakçıların elenmesi
- Tapu harçlarında 400 milyar TL'ye kadar gelir artışı öngörülmektedir

---

## 3. Entegrasyon Gereksinimleri

### 3.1 EİDS API Bilgileri

| Bilgi | Değer |
|-------|-------|
| **Taşınmaz API** | EİDS üzerinden e-Devlet SSO entegrasyonu |
| **Araç API Endpoint** | `https://ws.gtb.gov.tr:8443/EidsAracApi` |
| **Health Check** | `https://ws.gtb.gov.tr:8443/EidsApi/health` |
| **Kimlik Doğrulama** | Basic Authentication (kurum tarafından firma bazında sağlanan kimlik bilgileri) |
| **IP Yetkilendirme** | IP bazlı whitelist (servis tüketecek IP adresleri kuruma bildirilmeli) |
| **İletişim** | `eids@ticaret.gov.tr` |

**Health Check yanıtı:**
- Tüm servisler çalışıyorsa: `"Healthy"`
- Herhangi bir servis çalışmıyorsa: `"Unhealthy"`
- Alt servisler: Mersis ve Esbis servisleri kontrol edilir

**API yanıt formatı:**
- Başarılı: HTTP **200**, `errors: null`, `data` alanında sonuç
- Hata: `data: null`, `errors` alanında `List<string>` formatında hata mesajları

### 3.2 Kimlik Doğrulama Entegrasyonu (SSO)

```
Kullanıcı Akışı:
1. Kullanıcı platformda "İlan Ver" butonuna tıklar
2. e-Devlet SSO sayfasına yönlendirilir
3. e-Devlet kimlik bilgileriyle giriş yapar
4. Başarılı doğrulama sonrası returnUrl'e yönlendirilir
5. EİDS, kullanıcı için benzersiz GUID kullanıcı kodu üretir
```

**API Metodu:** `GetKullaniciKodu` — e-Devlet üzerinden doğrulanan kullanıcıya ilan platformu için kullanıcı kodu sağlar.

### 3.3 Yetki Doğrulama Akışları

#### Bireysel İlan Akışı

```
1. Kullanıcı platforma giriş yapar (e-Devlet SSO)
2. Taşınmaz numarasını girer
3. Platform → EİDS API: yetki sorgulama
4. EİDS otomatik malik/hısımlık kontrolü yapar
5a. Yetki VAR → İlan girişi tamamlanır
5b. Yetki YOK → İlan girişi engellenir
```

#### Kurumsal İlan Akışı

```
1. Emlak işletmesi platformda oturum açar
2. Taşınmaz numarası girilir
3. Platform → EİDS API: yetkilendirme durumu sorgulanır
4a. Malik e-Devlet'te yetkilendirme yapmışsa → İlan girilebilir
4b. Yetkilendirme yoksa → İlan girişi engellenir
```

### 3.4 Erişim Başvuru Süreci

```
Adım 1: Ticaret Bakanlığı ile iletişime geçin
Adım 2: Bakanlık tarafından Firma Kodu tahsis edilir
Adım 3: Firma Kodu + şirket e-posta → eids@ticaret.gov.tr
Adım 4: Basic Authentication kimlik bilgileri alınır
Adım 5: Servis tüketecek IP adresleri kuruma bildirilir
Adım 6: Entegrasyon dokümanlarına uygun teknik altyapı hazırlanır
Adım 7: Test ve doğrulama süreci tamamlanır
Adım 8: Canlı ortama geçiş
```

### 3.5 Entegrasyon Dokümanları

Ticaret Bakanlığı tarafından sağlanan resmi dokümanlar:

| Doküman | İçerik |
|---------|--------|
| Faz 1 Entegrasyon Dokümanı | Kimlik doğrulama teknik detayları |
| Faz 2 Entegrasyon Dokümanı | Yetki doğrulama teknik detayları |

**Temin yolları:**
- Ticaret Odaları aracılığıyla
- Doğrudan Bakanlık'tan (`eids@ticaret.gov.tr`)

**Referans dokümanlar (ticaret odalarından):**
- Kayseri TO: `kayserito.tr/dokuman/eids-yetki-dogrulama-uygulama-esaslari-ve-faz1-faz2-dokumanlar.pdf`
- ITSO: `itso.org.tr/upload/files/eids1_-sayfalar-4.pdf`
- ITO: `ito.org.tr/documents/eidsdogrulama_docx.pdf`

### 3.6 İlan Numarası Validasyonu

Platformda uygulanması gereken validasyon adımları:

| Adım | Açıklama |
|------|----------|
| 1. Format kontrolü | Taşınmaz numarasının sayısal formatta ve beklenen uzunlukta olduğunu kontrol et |
| 2. EİDS API sorgusu | `GetKullaniciKodu` ile kullanıcı doğrulama, ardından taşınmaz numarası ile yetki sorgulama |
| 3. Yetki durumu kontrolü | API yanıtındaki yetki durumunu değerlendir |
| 4. Hata yönetimi | API erişilemez durumda uygun hata mesajı göster, ilanı beklemeye al |
| 5. Yetki süresi takibi | Yetki bitiş tarihini kaydet, süre dolunca otomatik yeniden doğrulama |

---

## 4. Platform Geliştirme Aksiyonları

### 4.1 Teknik Entegrasyon Yol Haritası

```
AŞAMA 1: Bakanlık Başvurusu (Hafta 1-2)
├── eids@ticaret.gov.tr ile iletişim
├── Firma Kodu talebi
├── IP adresleri bildirimi
└── Entegrasyon dokümanlarının temini

AŞAMA 2: e-Devlet SSO Entegrasyonu (Hafta 3-5)
├── SSO redirect akışı geliştirme
├── returnUrl callback handler
├── Kullanıcı GUID yönetimi
└── Oturum yönetimi

AŞAMA 3: Yetki Doğrulama Entegrasyonu (Hafta 5-8)
├── Taşınmaz numarası giriş formu
├── EİDS API sorgulama servisi
├── Bireysel/kurumsal akış ayrımı
├── Hata yönetimi ve retry mekanizması
└── Health check monitoring

AŞAMA 4: İlan Yönetimi (Hafta 8-10)
├── EİDS logosu gösterim mekanizması
├── Yetki süresi takip sistemi
├── Otomatik ilan kaldırma/askıya alma
├── "Tapum Yok" istisnai akış
└── Yabancı vatandaş istisna akışı

AŞAMA 5: Test ve Canlıya Geçiş (Hafta 10-12)
├── Bakanlık ile test ortamı doğrulaması
├── Edge case testleri
├── Canlı ortama geçiş
└── Monitoring ve alerting
```

### 4.2 6563 Sayılı ETK ve 7416 Sayılı Kanun Gereksinimleri

**6563 sayılı Kanun — platform yükümlülükleri:**
- Ticari iletişimlerin açıkça tanımlanabilir olması
- Tanıtım malzemelerinin niteliğinin açıkça belirtilmesi
- Kolay erişilebilir şartların sunulması
- Tüm kayıtların **10 yıl** saklanması

**7416 sayılı Kanun değişiklikleri (1 Temmuz 2022):**
- Elektronik ticaret aracı hizmet sağlayıcıları için yeni yükümlülükler
- Yıllık net işlem hacmi **10 milyar TL**'yi aşan platformlar için ek yükümlülükler
- Veri kullanımı, veri taşınabilirliği düzenlemeleri
- Stok güncelleme sorumluluğu ile ilgili teknik altyapı sağlama yükümlülüğü

---

## Kaynaklar

- [EİDS Portal — Ticaret Bakanlığı](https://eids.ticaret.gov.tr/)
- [EİDS Yetki Doğrulama Uygulaması — Ticaret Bakanlığı](https://ticaret.gov.tr/kurumsal-haberler/elektronik-ilan-dogrulama-sistemi-eids-yetki-dogrulama-uygulamasi-hayata-gecirildi)
- [EİDS Nedir, Nasıl Kullanılır? — Afyon Ticaret](https://afyon.ticaret.gov.tr/haberler/elektronik-ilan-dogrulama-sistemi-eids-nedir-nasil-kullanilir)
- [10 Soruda EİDS — Anadolu Ajansı](https://www.aa.com.tr/tr/ekonomi/10-soruda-emlak-sektorunde-uygulanan-elektronik-ilan-dogrulama-sisteminin-ayrintilari/3373964)
- [EİDS Hepsiemlak Rehberi](https://www.hepsiemlak.com/emlak-yasam/genel/elektronik-ilan-dogrulama-sistemi)
- [EİDS 1 Şubat 2026 Zorunluluk — Emlak Haberi](https://www.emlakhaberi.com/elektronik-ilan-dogrulama-sistemi-1-subat-2026dan-itibaren-zorunlu-oluyor/amp)
- [Sahibinden Taşınmaz Numarası Rehberi](https://yardim.sahibinden.com/hc/tr/articles/15014853223324)
- [e-Devlet EİDS Yetkilendirme İşlemleri](https://www.turkiye.gov.tr/ticaret-eids-tasinmaz-ilani-yetkilendirme-islemleri)
- [6563 Sayılı Kanun — Mevzuat](https://www.mevzuat.gov.tr/mevzuatmetin/1.5.6563.pdf)
- [7416 Sayılı Kanun — Lexpera](https://www.lexpera.com.tr/resmi-gazete/metin/7416-elektronik-ticaretin-duzenlenmesi-hakkinda-kanunda-degisiklik-yapilmasina-dair-kanun-31889-7416)
- [Sahibinden Kurumsal EİDS Yetkilendirme](https://yardim.sahibinden.com/hc/tr/articles/15852522141340)
- [EİDS Entegrasyon Dokümanları — Kayseri TO](https://www.kayserito.tr/dokuman/eids-yetki-dogrulama-uygulama-esaslari-ve-faz1-faz2-dokumanlar.pdf)
