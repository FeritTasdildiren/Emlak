# Destek Akışı ve Eskalasyon Süreci — Emlak Teknoloji Platformu

**Versiyon:** v1.0 | **Tarih:** 2026-02-26
**Kapsam:** Seed Ofis Destek Operasyonları — Alpha Dönemi

---

## 1. Destek Felsefesi

Emlak ofisleri teknolojiye farklı mesafelerde. Bazıları dijitale çok açık, bazıları Excel bile kullanmıyor. Destek yaklaşımımız:

- **Sabırlı ve basit dil:** Teknik jargon kullanma, adım adım anlat
- **Proaktif:** Sorunu beklemeden çözüme yönlendir
- **Kişisel:** Her ofisi ismiyle tanı, not tut, ilişki kur
- **Hızlı:** İlk yanıt sürelerini asla aşma

---

## 2. Destek Kanalları

| Kanal | Erişim | Çalışma Saati | Hedef Kitle |
|-------|--------|--------------|-------------|
| **E-posta** | destek@emlakteknoloji.com | 7/24 (yanıt iş saati) | Tüm planlar |
| **Telegram** | @emlakteknoloji_destek | 09:00-18:00 (haftaiçi) | Tüm planlar |
| **Telefon** | 0216 XXX XX XX | 09:00-18:00 (haftaiçi) | Elite + Seed ofisler |
| **Platform içi chat** | Sağ alt köşe sohbet balonu | 09:00-18:00 (haftaiçi) | Tüm planlar |
| **Bilgi merkezi** | platform.com/yardim | 7/24 (self-servis) | Tüm planlar |
| **Bire bir görüşme** | Randevu ile | Randevuya göre | Seed ofisler (ilk 30 gün) |

---

## 3. Yanıt Süresi Taahhütleri (SLA)

### Planlara Göre Yanıt Süreleri

| Öncelik | Starter | Pro | Elite | Seed Ofis (İlk 30 gün) |
|---------|---------|-----|-------|------------------------|
| **Kritik** (platform erişilemiyor) | 24 saat | 4 saat | 1 saat | 1 saat |
| **Yüksek** (özellik çalışmıyor) | 48 saat | 12 saat | 4 saat | 4 saat |
| **Normal** (soru/yardım) | 48 saat | 24 saat | 12 saat | 12 saat |
| **Düşük** (öneri/istek) | 72 saat | 48 saat | 24 saat | 24 saat |

### Öncelik Tanımları

| Seviye | Tanım | Örnekler |
|--------|--------|----------|
| **Kritik (P1)** | Platform tamamen erişilemiyor veya veri kaybı riski var | Giriş yapılamıyor, tüm veriler kaybolmuş görünüyor, ödeme sistemi çalışmıyor |
| **Yüksek (P2)** | Temel bir özellik çalışmıyor ama platform erişilebilir | AI değerleme hata veriyor, PDF rapor indirilemiyor, Telegram bot yanıt vermiyor |
| **Normal (P3)** | Kullanım sorusu veya küçük sorun | "Toplu yükleme nasıl yapılır?", "Vitrin URL'mi değiştirebilir miyim?" |
| **Düşük (P4)** | Özellik isteği, öneri veya kozmetik sorun | "Raporda renk değişikliği olabilir mi?", "Yeni bir filtre eklenebilir mi?" |

---

## 4. Destek Talebi Akış Şeması

```
KULLANICI SORUNU YAŞIYOR
         │
         ▼
┌─────────────────────┐
│ 1. Self-Servis       │
│    Bilgi Merkezi     │───── Çözüldü ──→ Kapandı
│    platform.com/     │
│    yardim            │
└────────┬────────────┘
         │ Çözülmedi
         ▼
┌─────────────────────┐
│ 2. Platform İçi Chat │
│    veya Telegram     │───── Çözüldü ──→ Kapandı
│    Destek            │
└────────┬────────────┘
         │ Çözülmedi
         ▼
┌─────────────────────┐
│ 3. E-posta Talebi    │
│    destek@           │───── Çözüldü ──→ Kapandı
│    emlakteknoloji.   │
│    com               │
└────────┬────────────┘
         │ Çözülmedi / Kritik
         ▼
┌─────────────────────┐
│ 4. Telefon Desteği   │
│    (Elite + Seed)    │───── Çözüldü ──→ Kapandı
│                      │
└────────┬────────────┘
         │ Çözülmedi / Teknik
         ▼
┌─────────────────────┐
│ 5. Eskalasyon        │
│    Teknik Ekibe      │───── Çözüldü ──→ Kapandı
│    Aktarım           │
└────────┬────────────┘
         │ Çözülmedi / Acil
         ▼
┌─────────────────────┐
│ 6. Üst Yönetim       │
│    Eskalasyon         │───── Çözüldü ──→ Kapandı
└─────────────────────┘
```

---

## 5. Eskalasyon Matrisi

### Seviye 1 — Destek Temsilcisi (L1)

**Kim:** Müşteri destek ekibi
**Ne yapar:**
- Genel kullanım sorularını yanıtlar
- Bilgi merkezi makalelerine yönlendirir
- Hesap ve plan sorularını çözer
- Basit teknik sorunları giderir (tarayıcı önbellek temizleme, tekrar giriş vb.)
- Onboarding sürecinde bire bir destek verir

**Çözemezse:** Seviye 2'ye aktarır (maks. 30 dakika içinde)

### Seviye 2 — Teknik Destek (L2)

**Kim:** Teknik ekip (backend/frontend geliştirici)
**Ne yapar:**
- Platform hatalarını inceler ve düzeltir
- API ve entegrasyon sorunlarını çözer
- Veri tutarsızlıklarını araştırır
- Telegram bot bağlantı sorunlarını giderir
- AI değerleme sonuç anormalliklerini inceler

**Çözemezse:** Seviye 3'e aktarır (maks. 2 saat içinde)

### Seviye 3 — Mühendislik ve Ürün (L3)

**Kim:** Kıdemli mühendis + Ürün yöneticisi
**Ne yapar:**
- Kritik sistem hatalarını düzeltir
- Veri kaybı durumunda kurtarma işlemi yapar
- ML model sorunlarını inceler
- Güvenlik açıklarını kapatır
- Mimari düzeyde kararlar alır

**Çözemezse:** Üst yönetime bilgi verilir

### Seviye 4 — Üst Yönetim (L4)

**Kim:** Kurucu / CTO
**Ne zaman:** Müşteri kaybı riski, veri ihlali, hukuki durum, basın ilgisi
**Ne yapar:**
- Müşteriyle doğrudan iletişim
- Tazminat veya telafi kararları
- Kamuoyu açıklamaları
- Stratejik kararlar

---

## 6. Seed Ofis Özel Destek Protokolü

İlk 30 seed ofis için standart desteğin üzerinde özel süreç uygulanır:

### Atanmış Destek Sorumlusu

- Her seed ofise bir **Onboarding Sorumlusu** atanır
- Sorumlunun adı, telefonu ve Telegram'ı ofise bildirilir
- İlk 30 gün boyunca doğrudan bu kişiye ulaşabilirler

### Proaktif İletişim Takvimi

| Gün | Aksiyon | Kanal |
|-----|---------|-------|
| 0 | Hoş geldin araması, kampanya kodu iletimi | Telefon |
| 1 | Kayıt kontrolü, ilk ilan ekleme yardımı | Telefon/Telegram |
| 3 | İlan aktarımı durumu kontrolü | Telegram |
| 7 | Bot kurulum kontrolü, ilk hafta özeti | Telefon |
| 14 | Değerleme ve CRM kullanım kontrolü | Telefon |
| 21 | İleri özellikler tanıtımı | Telegram |
| 30 | Onboarding sonu değerlendirme görüşmesi | Telefon |

### Proaktif İletişim Şablonu (Gün 7 Örneği)

> "Merhaba [Yetkili Adı], [Ofis Adı] ekibinden [İsim]. Platformla ilk haftanız nasıl geçti? Bot kurulumunu tamamladınız mı? Herhangi bir takıldığınız yer varsa birlikte çözelim. Kısa bir görüşme yapmamız uygun mu?"

### Geri Bildirim Toplama

| Zaman | Yöntem | Soru Sayısı |
|-------|--------|-------------|
| 7. gün | Telegram anketi | 3 soru (puan + yorum) |
| 14. gün | Platform içi popup | 5 soru (NPS + detay) |
| 30. gün | Telefon görüşmesi | 10 soru (kapsamlı) |
| 60. gün | E-posta anketi | 5 soru (memnuniyet + plan kararı) |

---

## 7. Yaygın Sorun Kategorileri ve Standart Çözümler

### Kategori 1: Hesap ve Giriş Sorunları

| Sorun | Standart Çözüm | Seviye |
|-------|----------------|--------|
| Şifremi unuttum | "Şifremi Unuttum" linki → e-posta ile sıfırlama | L1 |
| Doğrulama e-postası gelmedi | Spam kontrol → tekrar gönder → 5 dk bekle | L1 |
| Kampanya kodu çalışmıyor | Kod doğrulama → manuel aktivasyon | L1 |
| Hesabım kilitlendi | 5 hatalı giriş → 15 dk bekleme → admin açma | L1-L2 |

### Kategori 2: Portföy ve İlan Sorunları

| Sorun | Standart Çözüm | Seviye |
|-------|----------------|--------|
| İlan eklenemiyor | Zorunlu alanları kontrol → tekrar dene | L1 |
| Toplu yükleme hatası | Şablon formatı kontrol → sütun adları → karakter | L1 |
| İlan bilgileri yanlış | Düzenleme ekranından güncelleme | L1 |
| İlan silinemiyor | Aktif eşleştirme var mı kontrol → silme onayı | L1 |

### Kategori 3: AI Değerleme Sorunları

| Sorun | Standart Çözüm | Seviye |
|-------|----------------|--------|
| Değerleme hata veriyor | Girdi bilgileri kontrol → ilçe/mahalle doğru mu | L1 |
| Sonuç çok yüksek/düşük | Bilgileri tekrar kontrol → m², bina yaşı, kat | L1-L2 |
| Değerleme çok uzun sürüyor | Sunucu durumu kontrol → yeniden dene | L2 |
| "Desteklenmeyen bölge" hatası | İlçe listesi kontrol → henüz açılmamış olabilir | L1 |

### Kategori 4: Telegram Bot Sorunları

| Sorun | Standart Çözüm | Seviye |
|-------|----------------|--------|
| Bot yanıt vermiyor | Bağlantı yenile → /start tekrar gönder | L1 |
| Komutlar çalışmıyor | Doğru format kontrol → /yardim gönder | L1 |
| Bot bağlanamıyor | Telegram güncel mi → platform ayarları kontrol | L1-L2 |
| Mini App açılmıyor | Telegram sürümü kontrol → güncelle | L1 |

### Kategori 5: Ödeme Sorunları

| Sorun | Standart Çözüm | Seviye |
|-------|----------------|--------|
| Ödeme reddedildi | Kart limiti/geçerlilik → farklı kart dene | L1 |
| Fatura görünmüyor | Faturalandırma sekmesi → 24 saat bekleme | L1 |
| Yanlış plan ücretlendirildi | Fatura kontrolü → düzeltme/iade | L2 |
| İade talebi | İade politikası → L2'ye aktar | L2 |

---

## 8. İç İletişim ve Bilet Yönetimi

### Bilet Durumları

```
Yeni → Atandı → İnceleniyor → Çözüm Önerildi → Çözüldü → Kapatıldı
                                       │
                                       ├── Müşteri Onaylamadı → Tekrar İnceleme
                                       │
                                       └── Eskalasyon Gerekli → Üst Seviye
```

### Bilet Önceliklendirme Kuralları

1. **Seed ofis biletleri** her zaman +1 öncelik seviyesi alır (Normal → Yüksek olur)
2. **Elite plan** biletleri normal süreçte işlenir ama SLA daha kısadır
3. **Aynı sorundan 3+ ofis etkileniyorsa** otomatik P1'e yükselir
4. **Veri kaybı riski** olan her bilet otomatik P1

### Haftalık Destek Raporu

Her pazartesi üretilecek rapor:

| Metrik | Hedef |
|--------|-------|
| Ortalama ilk yanıt süresi | < SLA'nın %80'i |
| Çözüm oranı (L1'de) | > %70 |
| Müşteri memnuniyet skoru (CSAT) | > 4.0/5.0 |
| Açık bilet sayısı | < 15 |
| Eskalasyon oranı (L2+) | < %30 |
| Tekrar açılan bilet oranı | < %10 |

---

## 9. Kriz Yönetimi

### Kriz Seviyesi Tanımları

| Seviye | Tanım | Örnek | Aksiyonlar |
|--------|--------|-------|-----------|
| **SEV-1** | Platform tamamen çöktü | Sunucu hatası, tüm kullanıcılar etkileniyor | Tüm ekip alarm, 15 dk içinde durum güncellemesi, her 30 dk güncelleme |
| **SEV-2** | Kritik özellik çalışmıyor | AI değerleme tüm kullanıcılarda hata, ödeme sistemi durdu | Teknik ekip alarm, 30 dk içinde durum güncellemesi |
| **SEV-3** | Kısmi sorun | Belirli ilçelerde değerleme hatası, bir bankanın kredi oranları yanlış | Normal eskalasyon, 2 saat içinde çözüm |

### Kriz İletişim Şablonu

**SEV-1 / SEV-2 durumunda ofislere gönderilecek mesaj:**

> "Değerli [Ofis Adı] ekibi,
>
> Platformumuzda teknik bir sorun yaşanmaktadır. Ekibimiz sorunu tespit etmiş olup çözüm üzerinde çalışmaktadır.
>
> **Etkilenen:** [Etkilenen özellik]
> **Tahmini çözüm:** [Süre tahmini]
>
> Sorun çözüldüğünde sizi bilgilendireceğiz. Anlayışınız için teşekkür ederiz.
>
> Emlak Teknoloji Platformu Destek Ekibi"

### Post-Mortem (Kriz Sonrası Analiz)

Her SEV-1 ve SEV-2 sonrasında 48 saat içinde:

1. **Ne oldu:** Sorunun teknik açıklaması
2. **Zaman çizelgesi:** Tespit → çözüm süreci
3. **Etki:** Kaç kullanıcı etkilendi, ne kadar sürdü
4. **Kök neden:** Asıl sorun neydi
5. **Önleyici aksiyonlar:** Tekrar yaşanmaması için ne yapılacak

---

## 10. Bilgi Merkezi İçerik Planı

Self-servis destek için platform.com/yardim altında şu içerikler bulunur:

### Video Rehberler (Her biri 2-3 dakika)

| # | Başlık | Konu |
|---|--------|------|
| 1 | İlk Adımlar | Kayıt, giriş, profil |
| 2 | İlan Ekleme | Tek ilan ve toplu yükleme |
| 3 | AI Değerleme | Değerleme yapma ve PDF rapor |
| 4 | Müşteri Yönetimi | CRM kullanımı |
| 5 | Eşleştirme | Müşteri-ilan eşleştirme |
| 6 | Telegram Bot | Bot kurulumu ve kullanımı |
| 7 | Mini App | Aktivasyon ve özelleştirme |
| 8 | İlan Asistanı | Metin oluşturma ve virtual staging |
| 9 | Vitrin | Vitrin oluşturma ve yayınlama |
| 10 | Kredi Hesaplayıcı | Kullanım ve müşteriye sunum |

### Yazılı Rehberler

- Hızlı Başlangıç (1 sayfa)
- Onboarding Rehberi v2 (kapsamlı)
- FAQ (40 soru-cevap)
- Toplu Yükleme Şablon Kılavuzu
- Telegram Bot Komut Referansı

### Sorun Giderme Makaleleri

- "Giriş yapamıyorum" — Adım adım çözüm
- "Toplu yükleme dosyam kabul edilmiyor" — Şablon düzeltme
- "AI değerleme farklı sonuç veriyor" — Bilgi doğrulama
- "Telegram bot yanıt vermiyor" — Bağlantı yenileme
- "PDF rapor indirilemiyor" — Tarayıcı ayarları

---

## 11. Destek Ekibi Eğitim Konuları

Destek temsilcileri için zorunlu eğitimler:

| Konu | Süre | Sıklık |
|------|------|--------|
| Platform özellikleri (tümü) | 2 saat | İlk katılım |
| AI değerleme nasıl çalışır | 1 saat | İlk katılım |
| Telegram bot teknik detay | 1 saat | İlk katılım |
| Emlak sektörü terminolojisi | 1 saat | İlk katılım |
| Müşteri iletişim becerileri | 1 saat | Aylık |
| Yeni özellik eğitimi | 30 dk | Her yeni özellikte |
| Kriz iletişim protokolü | 30 dk | Çeyreklik |

### Emlak Sektörü Temel Terimler (Destek Ekibi İçin)

| Terim | Anlamı |
|-------|--------|
| Brüt m² | Duvarlar dahil toplam alan |
| Net m² | Kullanılabilir alan (duvarlar hariç) |
| 3+1 | 3 oda + 1 salon |
| Kat irtifakı | İnşaat halindeki bağımsız bölüm tapusu |
| Kat mülkiyeti | Tamamlanmış bina tapusu |
| Emsal (KAKS) | İnşaat alanı katsayısı |
| Tapu harcı | Alım-satımda ödenen vergi (%4) |
| Yetki belgesi | Taşınmaz Ticareti Yetki Belgesi |
| Portföy | Ofisteki aktif ilan listesi |
| CRM | Müşteri İlişkileri Yönetimi sistemi |

---

## 12. Metrik Takip Panosu

### Günlük İzlenen Metrikler

- Açık bilet sayısı (toplam ve seviyeye göre)
- Bugün açılan / kapatılan bilet sayısı
- SLA ihlali olan bilet sayısı
- Seed ofis bilet sayısı

### Haftalık İzlenen Metrikler

- Ortalama ilk yanıt süresi
- Ortalama çözüm süresi
- L1 çözüm oranı
- CSAT skoru
- En sık sorulan 5 soru
- Eskalasyon oranı

### Aylık İzlenen Metrikler

- Toplam bilet hacmi ve trend
- Kategori bazlı dağılım
- Seed ofis memnuniyet trendi
- NPS (Net Promoter Score)
- Churn riski olan ofisler (düşük kullanım + destek talebi)

---

*Emlak Teknoloji Platformu — Destek Akışı ve Eskalasyon Süreci v1.0*
*Son güncelleme: 2026-02-26*
