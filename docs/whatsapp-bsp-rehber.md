# WhatsApp BSP Basvuru Rehberi - 360dialog

> **Tarih:** 2026-02-20
> **Sprint:** S2.17
> **Durum:** Rehber Dokumani (Basvuru YAPILMADI)
> **Proje:** Emlak Teknoloji Platformu

---

## Ozet

Bu rehber, emlak teknoloji platformumuz icin WhatsApp Business API erisimi saglamak amaciyla **360dialog** BSP (Business Solution Provider) uzerinden basvuru surecini kapsamli sekilde dokumante eder. 360dialog, Meta'nin resmi WhatsApp Business Solution Provider'larindan biridir ve Almanya merkezli bir messaging iPaaS cozumudur.

**Neden WhatsApp Business API?**
- Turkiye'de 60+ milyon WhatsApp kullanicisi
- Emlak sektorunde musteri iletisiminin %70+'i WhatsApp uzerinden
- Otomatik ilan bildirimleri, randevu onaylari, odeme hatirlatalari
- 7/24 chatbot entegrasyonu imkani

**Neden 360dialog?**
- Meta'nin resmi BSP'si (tier-1 partner)
- Dusuk maliyet: Aylik $49'dan baslayan lisans + Meta mesaj ucretleri (markup yok)
- Hizli onboarding: 10-15 dakikada kayit
- Sandbox/test ortami mevcut
- Kapsamli API dokumantasyonu
- Turkce destek mevcut

---

## 1. 360dialog Nedir?

### 1.1 Genel Bakis

360dialog, isletmelerin WhatsApp Business API'ye erisimini saglayan Meta onayali bir **Business Solution Provider (BSP)**'dir. Almanya, Berlin merkezlidir ve 2018'den beri WhatsApp ekosisteminde faaliyet gostermektedir.

**Temel Ozellikler:**
- WhatsApp Cloud API uzerinden mesajlasma altyapisi
- Partner API ile coklu isletme yonetimi
- Client Hub ile self-servis WABA yonetimi
- Embedded Signup ile hizli onboarding
- Template mesaj yonetimi ve onay sureci
- Webhook tabanli gercek zamanli bildirimler

### 1.2 WhatsApp Business API vs Cloud API

| Ozellik | On-Premise API (Eski) | Cloud API (Guncel) |
|---------|----------------------|-------------------|
| **Hosting** | Kendi sunucunuzda | Meta'nin sunucularinda |
| **Maliyet** | Yuksek (sunucu + bakim) | Dusuk (sadece mesaj ucreti) |
| **Guncelleme** | Manuel | Otomatik |
| **Olceklendirme** | Karmasik | Otomatik |
| **Kurulum Suresi** | Haftalar | Dakikalar |
| **Onerilen** | Hayir (kullanimdan kalkiyor) | **Evet** |

> **Not:** Meta, On-Premise API'yi asamali olarak kulanimdan kaldirmaktadir. Tum yeni entegrasyonlar Cloud API uzerinden yapilmalidir.

### 1.3 360dialog Fiyatlandirma Planlari

| Plan | Aylik Ucret | Ozellikler |
|------|-------------|------------|
| **Starter** | $49/ay | 1 telefon numarasi, temel API erisimi, Client Hub |
| **Professional** | $99/ay | Oncelikli destek, gelismis analitik, SLA garantisi |
| **Enterprise** | Ozel fiyat | Coklu numara, ozel entegrasyon, dedicated destek |

> **Onemli:** 360dialog, Meta'nin mesaj ucretleri uzerine **ek markup EKLEMEZ**. Sadece aylik platform ucreti alinir.

---

## 2. Basvuru Gereksinimleri

### 2.1 Sirket Bilgileri

- [x] Turkiye'de kayitli bir sirket (Ltd. Sti., A.S., vb.)
- [x] Aktif vergi levhasi
- [x] Sirket web sitesi (SSL sertifikali, aktif)
- [x] Web sitesinde sirket adi, adresi ve telefon numarasi
- [x] Sirketin yasal temsilcisinin bilgileri

### 2.2 Meta Business Manager Hesabi

- [x] Meta Business Manager hesabi (business.facebook.com)
- [x] Business Manager'da admin yetkili kullanici
- [x] Sirket bilgileri Business Manager'da tanimli
- [x] **Business Verification** tamamlanmis (onemli!)

> **Business Verification Neden Onemli?**
> - Mesaj gonderim limitlerini artirmak icin zorunlu
> - 2'den fazla telefon numarasi kullanmak icin gerekli
> - Gununuzluk suresini kisaltir
> - Meta'nin guvenlik gereksinimlerini karsilar

### 2.3 Telefon Numarasi

- [x] WhatsApp Business API icin ayrilmis bir telefon numarasi
- [x] Numara uluslararasi arama veya SMS alabilmeli (dogrulama icin)
- [x] Numara baska bir WhatsApp hesabinda kayitli olmamali

> **Subat 2025 Guncellemesi:** Artik mevcut WhatsApp uygulamasinda (Android/iPhone/WhatsApp Business App) kullanilan bir numara, silinmeden API'ye tasinabilmektedir (Coexistence ozelligi).

### 2.4 Teknik Gereksinimler

- [x] HTTPS destekli webhook endpoint (SSL zorunlu)
- [x] Sunucu/hosting altyapisi (webhook icin)
- [x] Gelistirici kaynaklari (API entegrasyonu icin)
- [x] Test ortami (ngrok veya benzeri tunnel araci)

---

## 3. Basvuru Adimlari (Adim Adim)

### Adim 1: 360dialog Client Hub Hesabi Olusturma (5 dk)

1. [360dialog.com](https://360dialog.com) adresine git
2. "Get Started" veya "Sign Up" butonuna tikla
3. Sirket e-posta adresi ile kayit ol (**ucretsiz e-posta domainleri kabul edilmez** - gmail, hotmail vb. OLMAZ)
4. E-posta dogrulama linkine tikla
5. Client Hub'a giris yap

```
Kabul Edilen: info@emlakplatformu.com, api@sirketadi.com.tr
Reddedilen: sirketadi@gmail.com, isim@hotmail.com
```

### Adim 2: Meta Business Manager Baglantisi (10 dk)

1. Client Hub'da "Connect Business Manager" secenegine tikla
2. Meta Business Manager hesabiniza giris yapin
3. 360dialog'un WABA yonetim izinlerini onaylayin
4. Embedded Signup akisini tamamlayin:
   - Business Manager seciminizi yapin
   - WhatsApp Business Account (WABA) olusturun
   - Telefon numaranizi kaydedin

### Adim 3: Telefon Numarasi Dogrulama (5 dk)

1. API'ye kaydetmek istediginiz telefon numarasini girin
2. Dogrulama yontemi secin: **SMS** veya **Telefon Aramasi**
3. Gelen 6 haneli dogrulama kodunu girin
4. Dogrulama tamamlandiginda numara WABA'niza baglanir

### Adim 4: Business Verification (1-14 gun)

1. Meta Business Manager'da "Security Center" > "Start Verification" yolunu izleyin
2. Gerekli belgeleri yukleyin:
   - Sirket tescil belgesi / Ticaret sicil gazetesi
   - Vergi levhasi
   - Faaliyet belgesi
3. Meta'nin dogrulama surecini bekleyin (genellikle 1-3 is gunu)
4. Onay sonrasi mesaj limitleri otomatik artar

### Adim 5: API Anahtari Edinme (Aninda)

1. Client Hub'da WABA'nizi secin
2. "API Key" bolumune gidin
3. API anahtarinizi kopyalayin
4. Guvenli bir sekilde saklayin (environment variable olarak)

```bash
# Ornek: .env dosyasina ekleyin
WHATSAPP_360_API_KEY=your_api_key_here
WHATSAPP_360_BASE_URL=https://waba.360dialog.io
```

### Adim 6: Webhook Yapilandirmasi (15 dk)

1. HTTPS destekli webhook endpoint'inizi hazirlayin
2. Client Hub'dan veya API uzerinden webhook URL'nizi kaydedin:

```bash
# Webhook yapilandirma API cagrisi
curl -X POST https://waba.360dialog.io/v1/configs/webhook \
  -H "D360-API-KEY: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://api.emlakplatformu.com/webhooks/whatsapp"
  }'
```

### Adim 7: Business Profile Olusturma (10 dk)

1. Sirket bilgilerinizi tanimlayin:
   - Sirket adi
   - Sirket aciklamasi
   - Adres
   - E-posta
   - Web sitesi
   - Profil resmi

```json
{
  "messaging_product": "whatsapp",
  "address": "Istanbul, Turkiye",
  "description": "Emlak Teknoloji Platformu - Guvenilir emlak cozumleri",
  "email": "info@emlakplatformu.com",
  "websites": ["https://emlakplatformu.com"],
  "profile_picture_url": "https://emlakplatformu.com/logo.png"
}
```

### Adim 8: Uretim Ortamina Gecis

1. Sandbox testlerini tamamlayin (Bolum 7'ye bakiniz)
2. Template mesajlarinizi onaylatin (Bolum 6'ya bakiniz)
3. Webhook endpoint'inizi uretim sunucusuna tasiyin
4. API anahtarinizi uretim ortaminda yapilandirin
5. Ilk uretim mesajinizi gonderin ve dogrulayin

---

## 4. Fiyatlandirma

### 4.1 Meta WhatsApp Mesaj Ucretleri (Turkiye - 2025/2026)

> **Onemli:** 1 Temmuz 2025 itibariyle Meta, conversation-based (konusma bazli) fiyatlandirmayi kaldirmis ve **per-message (mesaj bazli)** fiyatlandirmaya gecmistir.

| Mesaj Kategorisi | Birim Fiyat (USD) | Aciklama |
|-----------------|-------------------|----------|
| **Marketing** | $0.0109 | Promosyon, urun tanitim, kampanya mesajlari |
| **Utility** | $0.0053 | Siparis onay, teslimat bildirimi, randevu hatirlatma |
| **Authentication** | $0.0053 | OTP, dogrulama kodlari, guvenlik mesajlari |
| **Service** | **Ucretsiz** | Musterinin baslattigi mesajlasma (24 saat icerisinde) |

> **Not:** Turkiye, utility ve authentication kategorilerinde dunyanin en uygun fiyatli pazarlarindan biridir ($0.0053).

### 4.2 Mesaj Kategorisi Detaylari

**Marketing Mesajlari ($0.0109/mesaj):**
- Yeni ilan bildirimleri
- Kampanya ve firsatlar
- Urun/hizmet tanitimi
- Cross-selling ve upselling

**Utility Mesajlari ($0.0053/mesaj):**
- Randevu onaylari ve hatirlatalari
- Odeme bildirimleri
- Sozlesme guncelemeleri
- Siparis/basvuru durumu

**Authentication Mesajlari ($0.0053/mesaj):**
- Tek kullanimlik sifreler (OTP)
- Giris dogrulama kodlari
- Hesap dogrulama

**Service Mesajlari (Ucretsiz):**
- Musteri sorusuna yanit (24 saat icinde)
- Canli destek mesajlari
- Musteri sikayet yonetimi

### 4.3 360dialog Platform Ucretleri

| Kalem | Ucret |
|-------|-------|
| Starter Plan (aylik) | $49/ay |
| Professional Plan (aylik) | $99/ay |
| Meta mesaj ucreti markup'i | **$0 (SIFIR)** |
| Template olusturma ucreti | **$0 (SIFIR)** |
| Kurulum ucreti | **$0 (SIFIR)** |

### 4.4 Toplam Maliyet Ozeti

```
Toplam Aylik Maliyet = 360dialog Platform Ucreti + (Mesaj Sayisi x Meta Birim Fiyat)
```

**Ornek Senaryo (Starter Plan):**
```
Platform:     $49/ay
1.000 Marketing mesaji:  1.000 x $0.0109 = $10.90
5.000 Utility mesaji:    5.000 x $0.0053 = $26.50
500 Auth mesaji:          500 x $0.0053 =  $2.65
Service mesajlari:        UCRETSIZ
-------------------------------------------
TOPLAM:       $89.05/ay (~2.850 TL/ay @ 32 TL/USD)
```

---

## 5. Teknik Entegrasyon

### 5.1 API Mimarisi

360dialog, Meta WhatsApp Cloud API'nin uzerine ince bir katman ekler. Tum mesajlasma Meta'nin altyapisi uzerinden gerceklesir.

```
[Emlak Platformu Backend]
        |
        v
[360dialog API Gateway]  <-- https://waba.360dialog.io
        |
        v
[Meta WhatsApp Cloud API]
        |
        v
[WhatsApp Kullanicisi]
```

### 5.2 Authentication (Kimlik Dogrulama)

**Client API (Mesaj Gonderme/Alma):**
```
Header: D360-API-KEY: <your_api_key>
```

**Partner API (Hesap Yonetimi):**
```
# Yontem 1: API Key (Onerilen)
Header: x-api-key: <partner_api_key>

# Yontem 2: Bearer Token
POST https://hub.360dialog.io/api/v2/token
Body: { "username": "email", "password": "pass" }
Response: { "access_token": "...", "token_type": "Bearer", "expires_in": 86400 }
```

### 5.3 Temel API Endpoint'leri

| Islem | Method | Endpoint |
|-------|--------|----------|
| Mesaj Gonder | POST | `/v1/messages` |
| Template Gonder | POST | `/v1/messages` |
| Medya Yukle | POST | `/v1/media` |
| Medya Indir | GET | `/v1/media/{media_id}` |
| Webhook Ayarla | POST | `/v1/configs/webhook` |
| Profil Guncelle | PATCH | `/v1/settings/business/profile` |
| Template Listele | GET | `/v1/configs/templates` |

**Base URL:** `https://waba.360dialog.io`

### 5.4 Mesaj Gonderme Ornegi

```bash
# Basit metin mesaji gonderme
curl -X POST https://waba.360dialog.io/v1/messages \
  -H "D360-API-KEY: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "messaging_product": "whatsapp",
    "to": "905551234567",
    "type": "text",
    "text": {
      "body": "Merhaba! Emlak Platformu'na hosgeldiniz."
    }
  }'
```

```bash
# Template mesaj gonderme
curl -X POST https://waba.360dialog.io/v1/messages \
  -H "D360-API-KEY: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "messaging_product": "whatsapp",
    "to": "905551234567",
    "type": "template",
    "template": {
      "name": "yeni_ilan_bildirimi",
      "language": { "code": "tr" },
      "components": [
        {
          "type": "body",
          "parameters": [
            { "type": "text", "text": "Ahmet" },
            { "type": "text", "text": "Kadikoy, Istanbul" },
            { "type": "text", "text": "3+1" },
            { "type": "text", "text": "1.250.000 TL" }
          ]
        }
      ]
    }
  }'
```

### 5.5 Webhook Yapilandirmasi

**Webhook Kurulumu:**
```bash
curl -X POST https://waba.360dialog.io/v1/configs/webhook \
  -H "D360-API-KEY: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://api.emlakplatformu.com/webhooks/whatsapp"
  }'
```

**Webhook Payload Ornegi (Gelen Mesaj):**
```json
{
  "object": "whatsapp_business_account",
  "entry": [{
    "id": "WABA_ID",
    "changes": [{
      "value": {
        "messaging_product": "whatsapp",
        "metadata": {
          "display_phone_number": "905551234567",
          "phone_number_id": "PHONE_ID"
        },
        "messages": [{
          "from": "905559876543",
          "id": "wamid.xxx",
          "timestamp": "1708444800",
          "type": "text",
          "text": { "body": "Kadikoy'deki 3+1 ilan hakkinda bilgi almak istiyorum" }
        }]
      },
      "field": "messages"
    }]
  }]
}
```

**Webhook Payload Ornegi (Mesaj Durumu):**
```json
{
  "object": "whatsapp_business_account",
  "entry": [{
    "changes": [{
      "value": {
        "statuses": [{
          "id": "wamid.xxx",
          "status": "delivered",
          "timestamp": "1708444810",
          "recipient_id": "905559876543"
        }]
      },
      "field": "messages"
    }]
  }]
}
```

**Mesaj Durumlari:**
- `sent` - Mesaj Meta'ya iletildi
- `delivered` - Mesaj aliciya ulasti
- `read` - Mesaj okundu (mavi tik)
- `failed` - Mesaj gonderilemedi

### 5.6 Rate Limit ve Quotalar

**Mesaj Gonderim Tier Sistemi:**

| Tier | Gunluk Benzersiz Alici | Gereksinim |
|------|----------------------|------------|
| **Tier 1** (Baslangic) | 1.000 | Yeni kayitli numaralar |
| **Tier 2** | 10.000 | Yuksek kalite puani + istikrarli kullanim |
| **Tier 3** | 100.000 | Yuksek kalite puani + istikrarli kullanim |
| **Sinirsiz** | Sinirsiz | Dogrulanmis buyuk isletmeler |

**Tier Yukseltme Kosullari:**
- Orta veya yuksek kalite puani (Yesil/Sari)
- 7 gunluk surede mevcut limitin yakininda istikrarli kullanim
- Otomatik yukseltme (manuel basvuru gerekmez)

**Kalite Puani Sistemi:**
- **Yesil (Yuksek):** Sorunsuz mesajlasma, dusuk engelleme orani
- **Sari (Orta):** Uyari seviyesi, iyilestirme gerekebilir
- **Kirmizi (Dusuk):** Limit dusurulme riski, acil aksiyon gerekli

**Kalite Puanini Etkileyen Faktorler:**
- Kullanici engelleme/raporlama oranlari
- Mesaj etkilesim oranlari
- Son 7 gunluk performans verileri

> **Ekim 2025 Degisikligi:** WhatsApp, mesaj limitlerini artik telefon numarasi bazinda degil, WABA hesabi bazinda tek bir limit olarak hesaplamaktadir.

---

## 6. Template Mesaj Yonetimi

### 6.1 Template Nedir?

Template mesajlar, 24 saatlik mesajlasma penceresi disinda musterilere mesaj gondermek icin kullanilan **onceden onaylanmis** mesaj sablonlaridir. Her template, Meta tarafindan incelenir ve onaylanir.

### 6.2 Template Kategorileri

| Kategori | Kullanim Alani | Ornek |
|----------|---------------|-------|
| **Marketing** | Promosyon, tanitim | Yeni ilan bildirimi, kampanya |
| **Utility** | Islemsel bildirimler | Randevu onay, odeme hatirlatma |
| **Authentication** | Guvenlik | OTP, dogrulama kodu |

### 6.3 Template Onay Sureci

1. **Olusturma:** Client Hub veya API uzerinden template tasarlayin
2. **Gonderme:** Meta'ya onay icin gonderin
3. **Inceleme:** Meta ML destekli otomatik inceleme yapar (1 dk - 48 saat)
4. **Sonuc:** Onaylandi / Reddedildi

**Reddedilme Nedenleri:**
- Yanlis format (hatali placeholder kullanimi)
- WhatsApp Kullanim Kosullari veya Ticaret Politikasi ihlali
- Cok genel icerik (spam potansiyeli)
- Yaniltici veya aldatici icerik
- Yasakli kategoriler (alkol, silah, yetiskin icerigi vb.)

### 6.4 Emlak Sektoru Icin Template Ornekleri

#### Template 1: Yeni Ilan Bildirimi (Marketing)

```
Isim: yeni_ilan_bildirimi
Kategori: Marketing
Dil: tr (Turkce)

Icerik:
Merhaba {{1}}! 🏠

Arama kriterlerinize uygun yeni bir ilan bulundu:

📍 Konum: {{2}}
🏢 Tip: {{3}}
💰 Fiyat: {{4}}

Detaylar icin tiklayin: {{5}}

Bu ilani goruntulemek ister misiniz?

Butonlar:
[Ilani Gor] -> URL
[Randevu Al] -> Quick Reply
```

#### Template 2: Randevu Onay (Utility)

```
Isim: randevu_onay
Kategori: Utility
Dil: tr (Turkce)

Icerik:
Merhaba {{1}},

Emlak gosterim randevunuz onaylandi! ✅

📅 Tarih: {{2}}
⏰ Saat: {{3}}
📍 Adres: {{4}}
👤 Danisman: {{5}}

Randevuya gelemeyecekseniz lutfen en az 2 saat once bize bildirin.

Butonlar:
[Onayla] -> Quick Reply
[Iptal Et] -> Quick Reply
```

#### Template 3: Fiyat Degisikligi Bildirimi (Utility)

```
Isim: fiyat_guncelleme
Kategori: Utility
Dil: tr (Turkce)

Icerik:
Merhaba {{1}},

Takip listenizdeki bir ilanda fiyat degisikligi var:

🏠 {{2}}
📍 {{3}}
💰 Eski Fiyat: {{4}}
💰 Yeni Fiyat: {{5}}

Detaylar: {{6}}
```

#### Template 4: Hosgeldiniz Mesaji (Marketing)

```
Isim: hosgeldiniz
Kategori: Marketing
Dil: tr (Turkce)

Icerik:
Merhaba {{1}}! 👋

Emlak Platformu'na hosgeldiniz!

Size en uygun emlak firsatlarini WhatsApp uzerinden paylasacagiz.

Lutfen bize aradiginiz emlak ozelliklerini bildirin:
- Bolge tercihiniz?
- Butceniz?
- Oda sayisi tercihiniz?

Butonlar:
[Arama Baslat] -> Quick Reply
[Daha Sonra] -> Quick Reply
```

#### Template 5: OTP Dogrulama (Authentication)

```
Isim: otp_dogrulama
Kategori: Authentication
Dil: tr (Turkce)

Icerik:
{{1}} dogrulama kodunuzdur. Bu kodu kimseyle paylasmayiniz.

Not: Authentication template'lerinde Meta icerik metnini belirler,
degistirilemez.
```

#### Template 6: Gosterim Sonrasi Takip (Marketing)

```
Isim: gosterim_takip
Kategori: Marketing
Dil: tr (Turkce)

Icerik:
Merhaba {{1}},

{{2}} adresindeki emlak gosterimine katildiginiz icin tesekkurler! 🙏

Bu mulk hakkinda ne dusunuyorsunuz?

Butonlar:
[Teklif Vermek Istiyorum] -> Quick Reply
[Baska Secenekler Gor] -> Quick Reply
[Ilgilenmedim] -> Quick Reply
```

### 6.5 Template Tasarim En Iyi Uygulamalari

1. **Net ve ozel olun:** Genel mesajlar reddedilir
2. **Placeholder'lari dogru kullanin:** `{{1}}`, `{{2}}` formatinda, sirali
3. **Spam gibi gorunmeyin:** Asiri buyuk harfler, cok fazla emoji kacinilmali
4. **Opt-out secenegi:** Marketing mesajlarinda "Abonelikten cik" butonu ekleyin
5. **Turkce karakter:** Template icerigi Turkce ise dil kodunu `tr` olarak secin
6. **Kisa tutun:** WhatsApp'ta uzun mesajlar dusuk etkilesim alir

---

## 7. Sandbox / Test Ortami

### 7.1 Sandbox Nedir?

360dialog, uretim ortamina gecmeden once API'yi test edebileceginiz bir sandbox (kumhavuzu) ortami sunar. Bu ortam ucretsizdir ve kayit gerektirmez.

### 7.2 Sandbox Kurulumu

**Adim 1: Test API Anahtari Edinme**

WhatsApp uygulamanizdan asagidaki numaraya `START` mesaji gonderin:

```
Numara: +55 11 4673-3492
Mesaj: START
```

Yanit olarak benzersiz bir **Test API Key** alacaksiniz.

**Adim 2: Sandbox API'yi Test Etme**

```bash
# Sandbox Base URL
BASE_URL=https://waba-sandbox.360dialog.io

# Test mesaji gonderme (yalnizca kendi numaraniza)
curl -X POST ${BASE_URL}/v1/messages \
  -H "D360-API-KEY: YOUR_SANDBOX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "messaging_product": "whatsapp",
    "to": "YOUR_PHONE_NUMBER",
    "type": "text",
    "text": {
      "body": "Sandbox test mesaji - Emlak Platformu"
    }
  }'
```

**Adim 3: Webhook Kurulumu**

```bash
# Webhook URL yapilandirma
curl -X POST ${BASE_URL}/v1/configs/webhook \
  -H "D360-API-KEY: YOUR_SANDBOX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-webhook-url.ngrok.io/webhook"
  }'
```

> **Ipucu:** Yerel gelistirme icin [ngrok](https://ngrok.com) veya [webhook.site](https://webhook.site) kullanabilirsiniz.

### 7.3 Sandbox Sinirliliklari

| Ozellik | Sandbox | Uretim |
|---------|---------|--------|
| Mesaj limiti | 200 mesaj | Tier'a gore |
| Alici | Yalnizca kayitli numara | Tum WhatsApp kullanicilari |
| Template | 3 on tanimli | Sinirsiz (onay gerekli) |
| Medya dosyasi | Desteklenmiyor | Tam destek |
| API yanit bilgisi | Sinirli | Tam |

### 7.4 On Tanimli Sandbox Template'leri

1. `disclaimer` - Genel bilgilendirme template'i
2. `first_welcome_messsage` - Karsilama mesaji
3. `interactive_template_sandbox` - Interaktif butonlu template

### 7.5 Test Senaryolari Kontrol Listesi

- [ ] Sandbox API anahtari edinme
- [ ] Basit metin mesaji gonderme
- [ ] Template mesaj gonderme
- [ ] Webhook kurulumu ve gelen mesaj alma
- [ ] Mesaj durumu webhook'unu dogrulama (sent/delivered/read)
- [ ] Hata senaryolarini test etme (gecersiz numara, vb.)

---

## 8. Alternatif BSP'ler Karsilastirma

### 8.1 Detayli Karsilastirma Tablosu

| Kriter | 360dialog | Twilio | Meta Dogrudan (Cloud API) |
|--------|-----------|--------|--------------------------|
| **Tur** | BSP (Almanya) | BSP (ABD) | Dogrudan erisim |
| **Aylik Platform Ucreti** | $49-99/ay | $0 (kullanim bazli) | $0 |
| **Mesaj Markup'i** | $0 (Meta fiyati) | $0.005/mesaj (gelen+giden) | $0 (Meta fiyati) |
| **Kurulum Suresi** | 10-15 dakika | 2-4 hafta | Dakikalar |
| **Teknik Karmasiklik** | Dusuk-Orta | Orta | Yuksek |
| **Dashboard/UI** | Client Hub | Twilio Console | Yok (sadece API) |
| **Sandbox** | Evet (ucretsiz) | Evet (ucretsiz) | Evet (sinirli) |
| **Template Ucreti** | Ucretsiz | Ucretsiz | Ucretsiz |
| **Webhook Destegi** | Tam | Tam | Tam |
| **Coklu Numara** | Enterprise plan | Var | Var |
| **SLA Garantisi** | Professional+ | Var (ucretli) | Yok |
| **Turkce Destek** | Sinirli | Yok | Yok |
| **Dokumanstasyon** | Iyi | Cok iyi | Iyi |
| **SDK Destegi** | REST API | Python, Node, PHP, Java, vb. | REST API |

### 8.2 Senaryo Bazli Oneri

**Kucuk Isletme (< 5.000 mesaj/ay):**
- **Oneri: 360dialog Starter ($49/ay)**
- Neden: Dusuk sabit maliyet, markup yok, kolay kurulum

**Orta Olcekli (5.000-50.000 mesaj/ay):**
- **Oneri: 360dialog Professional ($99/ay)**
- Neden: SLA garantisi, oncelikli destek, maliyet avantaji

**Buyuk Olcekli (50.000+ mesaj/ay):**
- **Oneri: Twilio veya Meta Dogrudan**
- Neden: Olceklenebilirlik, coklu kanal destegi, gelismis SDK'lar

**Gelistirici Odakli Takim:**
- **Oneri: Meta Dogrudan (Cloud API)**
- Neden: Aracisiz, tam kontrol, sifir ekstra maliyet

### 8.3 Maliyet Karsilastirmasi (10.000 mesaj/ay senaryosu)

**Varsayim:** 5.000 Marketing + 3.000 Utility + 1.000 Auth + 1.000 Service (TR fiyatlari)

| Kalem | 360dialog | Twilio | Meta Dogrudan |
|-------|-----------|--------|---------------|
| Platform ucreti | $49 | $0 | $0 |
| Marketing (5.000) | $54.50 | $54.50 + $25* | $54.50 |
| Utility (3.000) | $15.90 | $15.90 + $15* | $15.90 |
| Auth (1.000) | $5.30 | $5.30 + $5* | $5.30 |
| Service (1.000) | $0 | $0 + $5* | $0 |
| **TOPLAM** | **$124.70** | **$120.70** | **$75.70** |

> *Twilio markup: $0.005/mesaj (gelen+giden her mesaj icin)

**Yorum:**
- Meta Dogrudan en ucuz ancak teknik bilgi gerektirir
- 360dialog, orta duzeyde bir maliyetle kolay yonetim saglar
- Twilio, yuksek hacimde markup nedeniyle daha pahali olabilir

---

## 9. Tahmini Maliyet Analizi

### 9.1 Emlak Platformu Icin Senaryo Modelleri

#### Senaryo A: Baslangic Fazisi (Ay 1-3)

```
Kullanici sayisi:     500
Aylik mesaj dagitimi:
  Marketing:     1.000 mesaj (yeni ilan bildirimleri)
  Utility:       2.000 mesaj (randevu onay, hatirlatma)
  Auth:            500 mesaj (OTP dogrulama)
  Service:       1.500 mesaj (musteri destek - ucretsiz)

Maliyet Hesabi:
  360dialog Starter:          $49.00
  Marketing: 1.000 x $0.0109 = $10.90
  Utility:   2.000 x $0.0053 = $10.60
  Auth:        500 x $0.0053 =  $2.65
  Service:   1.500 x $0.00   =  $0.00
  ─────────────────────────────────────
  TOPLAM:                      $73.15/ay (~2.340 TL)
```

#### Senaryo B: Buyume Fazisi (Ay 4-12)

```
Kullanici sayisi:     2.500
Aylik mesaj dagitimi:
  Marketing:     5.000 mesaj
  Utility:       8.000 mesaj
  Auth:          2.000 mesaj
  Service:       5.000 mesaj (ucretsiz)

Maliyet Hesabi:
  360dialog Starter:           $49.00
  Marketing: 5.000 x $0.0109 =  $54.50
  Utility:   8.000 x $0.0053 =  $42.40
  Auth:      2.000 x $0.0053 =  $10.60
  Service:   5.000 x $0.00   =   $0.00
  ─────────────────────────────────────
  TOPLAM:                       $156.50/ay (~5.010 TL)
```

#### Senaryo C: Olgun Faz (Ay 12+)

```
Kullanici sayisi:     10.000
Aylik mesaj dagitimi:
  Marketing:    20.000 mesaj
  Utility:      30.000 mesaj
  Auth:          5.000 mesaj
  Service:      15.000 mesaj (ucretsiz)

Maliyet Hesabi:
  360dialog Professional:         $99.00
  Marketing: 20.000 x $0.0109 = $218.00
  Utility:   30.000 x $0.0053 = $159.00
  Auth:       5.000 x $0.0053 =  $26.50
  Service:   15.000 x $0.00   =   $0.00
  ─────────────────────────────────────
  TOPLAM:                        $502.50/ay (~16.080 TL)
```

### 9.2 Yillik Maliyet Projeksiyon Tablosu

| Donem | Aylik Maliyet (USD) | Aylik Maliyet (TRY*) | Yillik Toplam (USD) |
|-------|--------------------|-----------------------|--------------------|
| Baslangic (3 ay) | ~$73 | ~2.340 TL | $219 |
| Buyume (9 ay) | ~$157 | ~5.010 TL | $1.413 |
| **Ilk Yil Toplam** | - | - | **~$1.632** |
| Olgun Faz (yillik) | ~$503 | ~16.080 TL | **~$6.030** |

> *TRY hesaplari yaklasik 32 TL/USD kuru ile yapilmistir. Guncel kuru kontrol ediniz.

### 9.3 Maliyet Optimizasyon Onerileri

1. **Service mesajlarini maksimize edin:** Musterinin ilk mesaj gondermesini tesvik edin (ucretsiz pencere)
2. **Utility vs Marketing:** Mumkun oldugunca mesajlari Utility kategorisinde tasarlayin (%50 daha ucuz)
3. **Toplu bildirimlerden kaciniin:** Hedefli, segmentli mesajlar gonderin (daha dusuk engelleme orani = daha iyi kalite puani)
4. **Template optimizasyonu:** Az sayida iyi tasarlanmis template kullanin, cok sayida template acmayin
5. **Chatbot ile Service mesajlari:** Musteri sorularini chatbot ile yanitlayarak ucretsiz mesaj penceresinden faydalanin

---

## 10. Eylem Plani

### 10.1 Basvuru Timeline'i

```
Hafta 1: Hazirlik
├── [1.1] Meta Business Manager hesabi olustur/kontrol et
├── [1.2] Business Verification icin belgeleri hazirla
├── [1.3] WhatsApp icin ayrilmis telefon numarasi edin
└── [1.4] Webhook endpoint altyapisini hazirla (HTTPS)

Hafta 2: Kayit ve Sandbox
├── [2.1] 360dialog Client Hub'a kayit ol
├── [2.2] Sandbox ortaminda API testleri yap
├── [2.3] Webhook entegrasyonunu test et
└── [2.4] Template mesajlarini tasarla

Hafta 3: Uretim Hazirlik
├── [3.1] Meta Business Manager'i 360dialog'a bagla
├── [3.2] WABA olustur ve telefon numarasini dogrula
├── [3.3] Business Verification basvurusu yap
├── [3.4] Template mesajlarini onaya gonder
└── [3.5] Business Profile'i tamamla

Hafta 4: Go-Live
├── [4.1] Business Verification onayini bekle (1-14 gun)
├── [4.2] Template onaylarini kontrol et
├── [4.3] Uretim webhook endpoint'ini yapilandir
├── [4.4] Ilk uretim mesajlarini gonder ve dogrula
├── [4.5] Monitoring ve alerting kur
└── [4.6] Takim egitimini tamamla
```

### 10.2 Sorumluluklar (RACI)

| Gorev | Gelistirici | DevOps | Urun Yoneticisi | Hukuk |
|-------|-------------|--------|-----------------|-------|
| Meta BM Kurulumu | I | C | **R** | I |
| Business Verification | I | I | **R** | **A** |
| 360dialog Kayit | **R** | C | I | I |
| API Entegrasyonu | **R** | C | I | - |
| Webhook Altyapisi | C | **R** | I | - |
| Template Tasarimi | C | I | **R** | A |
| KVKK Uyumluluk | I | I | C | **R** |
| Test & QA | **R** | A | C | - |
| Go-Live | C | **R** | A | I |

> R: Responsible (Sorumlu), A: Accountable (Hesap verebilir), C: Consulted (Danisilan), I: Informed (Bilgilendirilen)

### 10.3 Risk ve Azaltma Stratejileri

| Risk | Olasilik | Etki | Azaltma |
|------|----------|------|---------|
| Business Verification gecikmesi | Orta | Yuksek | Belgeleri onceden hazirla, web sitesini guncelle |
| Template reddedilmesi | Orta | Dusuk | Ornekleri incele, rehbere uy, alternatifler hazirla |
| Telefon numarasi sorunu | Dusuk | Yuksek | Yedek numara hazirla, mevcut numara tasima |
| Webhook downtime | Dusuk | Yuksek | Yuksek erisilebilirlik, retry mekanizmasi, monitoring |
| Kalite puani dususu | Orta | Orta | Segmentli gonderim, opt-out secenegi, icerik kalitesi |
| KVKK uyumluluk sorunu | Dusuk | Cok Yuksek | Hukuki danismanlik, acik riza metni, veri isleme sozlesmesi |

### 10.4 KVKK ve Veri Koruma Notlari

> **Onemli:** WhatsApp verileri yurt disinda (Meta sunuculari - ABD/AB) islenir. KVKK kapsaminda dikkat edilmesi gerekenler:

1. **Acik Riza:** Musterilerden WhatsApp uzerinden iletisim icin acik riza alinmali
2. **Aydinlatma Metni:** WhatsApp iletisim kanali icin aydinlatma metni hazirlanmali
3. **Veri Isleme Sozlesmesi:** 360dialog ve Meta ile veri isleme sozlesmesi (DPA) incelenmeli
4. **Yurt Disi Aktarim:** KVKK m.9 kapsaminda yurt disi veri aktarimi icin gerekli onlemler alinmali
5. **Veri Minimizasyonu:** Sadece gerekli kisisel verilerin islenmesi saglanmali
6. **Silme Hakki:** Musteri talep ettiginde WhatsApp verilerinin silinebilmesi saglanmali

---

## Kaynaklar

### Resmi Kaynaklar

- [360dialog Pricing](https://360dialog.com/pricing) - 360dialog fiyatlandirma sayfasi
- [360dialog Documentation](https://docs.360dialog.com) - 360dialog resmi dokumantasyonu
- [360dialog Sandbox Guide](https://docs.360dialog.com/docs/get-started/sandbox) - Sandbox kurulum rehberi
- [360dialog Webhook Docs](https://docs.360dialog.com/docs/waba-messaging/webhook) - Webhook yapilandirma
- [360dialog Partner Program](https://360dialog.com/partners) - Partner programi
- [Meta WhatsApp Business Platform Pricing](https://business.whatsapp.com/products/platform-pricing) - Meta resmi fiyatlandirma
- [Meta Business Manager](https://business.facebook.com) - Meta Business Manager

### Karsilastirma ve Inceleme

- [Twilio vs 360dialog Comparison](https://www.kommunicate.io/blog/twilio-vs-360dialog-a-comparison/) - Twilio vs 360dialog karsilastirmasi
- [Top WhatsApp BSPs 2026](https://prelude.so/blog/best-whatsapp-business-solution-providers) - En iyi BSP'ler karsilastirmasi
- [WhatsApp API Providers 2026](https://zixflow.com/blog/whatsapp-api-providers/) - API saglayicilari listesi

### Fiyatlandirma Rehberleri

- [WhatsApp API Pricing 2026 Guide](https://flowcall.co/blog/whatsapp-business-api-pricing-2026) - Ulke bazli fiyat rehberi
- [WhatsApp Pricing Update 2026](https://authkey.io/blogs/whatsapp-pricing-update-2026/) - 2026 fiyat guncellemesi
- [Respond.io Pricing Guide](https://respond.io/blog/whatsapp-business-api-pricing) - Fiyatlandirma analizi

### Template ve Best Practices

- [Real Estate WhatsApp Templates](https://www.delightchat.io/whatsapp-templates/real-estate-agents) - Emlak template ornekleri
- [WhatsApp Template Categories Guide](https://sanuker.com/guideline-to-whatsapp-template-message-categories/) - Template kategori rehberi
- [WhatsApp Template Compliance](https://www.messageblink.com/whatsapp-template-compliance-waba-approvals/) - Template uyumluluk rehberi

### Rate Limit ve Kalite

- [WhatsApp Messaging Limits](https://docs.360dialog.com/docs/waba-management/capacity-quality-rating-and-messaging-limits) - 360dialog limit dokumantasyonu
- [WhatsApp Rate Limits Guide](https://www.chatarchitect.com/news/whatsapp-api-rate-limits-what-you-need-to-know-before-you-scale) - Rate limit detaylari

---

> **Bu rehber 2026-02-20 tarihinde hazirlanmistir.**
> Fiyatlandirma ve politikalar degisebilir. Basvuru oncesinde resmi kaynaklardan guncel bilgileri dogrulayin.
> **Gercek basvuru yapilmamistir** - bu dokuman yalnizca yol haritasi niteligindedir.
