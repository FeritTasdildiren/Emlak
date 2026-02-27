# UX Mikro-Kopya Audit Raporu — TASK-146 / S11-D2

**Tarih:** 2026-02-26
**Kapsam:** Web Dashboard + Telegram Mini App + Telegram Bot + Backend API + Vitrin
**Toplam Taranan Dosya:** 85+ (.tsx, .ts, .py, .txt)
**Toplam Tespit Edilen Metin:** 500+ adet

---

## İçindekiler

1. [Yönetici Özeti](#1-yönetici-özeti)
2. [Kritik Bulgular](#2-kritik-bulgular)
3. [Sayfa Bazlı Audit Tablosu](#3-sayfa-bazlı-audit-tablosu)
4. [Hata Mesajları Sözlüğü](#4-hata-mesajları-sözlüğü)
5. [Boş Durum Metinleri Kataloğu](#5-boş-durum-metinleri-kataloğu)
6. [Telegram Bot Mesajları Revizyonu](#6-telegram-bot-mesajları-revizyonu)
7. [Genel Öneriler ve Sonraki Adımlar](#7-genel-öneriler-ve-sonraki-adımlar)

---

## 1. Yönetici Özeti

### Genel Skor: 6.5 / 10

| Kriter | Skor | Açıklama |
|--------|------|----------|
| Türkçe Karakter Tutarlılığı | ⚠️ 4/10 | Ciddi tutarsızlık: Bazı dosyalarda `ş/ö/ü/ç/ğ/ı` var, bazılarında ASCII |
| Ton Tutarlılığı (Sen dili) | ✅ 7/10 | Çoğunlukla samimi, ama bazı yerlerde resmi ("Lütfen") |
| CTA Netliği | ✅ 8/10 | Butonlar genelde aksiyon odaklı, birkaç istisna var |
| Hata Mesajı Kalitesi | ⚠️ 5/10 | Çoğu tek katmanlı; 3-katman yapısı eksik |
| Boş Durum Kalitesi | ✅ 7/10 | Çoğunda CTA var, bazıları sadece placeholder |
| Accessibility | ⚠️ 5/10 | aria-label çok az; sr-only metinler yetersiz |
| Placeholder Kalitesi | ✅ 7/10 | Çoğunda örnek değer var, birkaçı jenerik |

### En Kritik 5 Sorun

1. **Türkçe karakter tutarsızlığı** — Aynı bileşen içinde bile `ş` vs `s` karışıyor
2. **Hata mesajları tek katmanlı** — "Bir hata oluştu" gibi jenerik mesajlar çok fazla
3. **`alert()` kullanımı** — Native browser alert UX'i bozuyor (ValuationResult, showcase-form)
4. **`confirm()` kullanımı** — Native confirm dialog (delete-showcase-button)
5. **Hardcoded mock veriler** — "John Doe", "JD", "Grafik Placeholder" gibi placeholder'lar

---

## 2. Kritik Bulgular

### 2.1 Türkçe Karakter Tutarsızlığı (P0 — Acil)

Aynı platform içinde iki farklı yazım standardı kullanılıyor:

| Dosya | Mevcut | Olması Gereken |
|-------|--------|----------------|
| ValuationForm.tsx (kota banner) | "Aylık değerleme limitinize ulaştınız." | ✅ Doğru |
| ValuationForm.tsx (açıklama) | "Bu ay icin belirlenen degerleme hakkiniz dolmustur" | ❌ → "Bu ay için belirlenen değerleme hakkınız dolmuştur" |
| ComparablesList.tsx | "Emsal Mülk Karşılaştırması" | ✅ Doğru |
| ValuationResult.tsx | "Degerleme Sonucu" | ❌ → "Değerleme Sonucu" |
| ValuationHistory.tsx | "Gecmis degerlemeler yuklenemedi" | ❌ → "Geçmiş değerlemeler yüklenemedi" |

**Öneri:** Tüm metin sabitleri tek bir `constants/copy.ts` dosyasında toplanmalı ve Türkçe karakter standardı zorunlu kılınmalı.

### 2.2 Native Browser Dialog Kullanımı (P0 — Acil)

| Dosya | Satır | Mevcut | Önerilen |
|-------|-------|--------|----------|
| ValuationResult.tsx | 144 | `alert("PDF indirilemedi...")` | Toast: "PDF indirilemedi. Tekrar deneyin." |
| property-form.tsx | 197 | `alert("İlan başarıyla kaydedildi! (Mock)")` | Toast: "İlan kaydedildi ✓" |
| showcase-form.tsx | 57 | `alert("Vitrin başarıyla oluşturuldu!")` | Toast: "Vitrin oluşturuldu ✓" |
| delete-showcase-button.tsx | 17 | `confirm("Bu vitrini silmek...")` | Modal dialog bileşeni |
| properties/page.tsx | 184 | `alert("Detay sayfası yakında eklenecek.")` | Toast veya kaldır |

### 2.3 Hardcoded / Placeholder Veriler (P1)

| Dosya | Metin | Durum |
|-------|-------|-------|
| sidebar.tsx | "John Doe", "Broker", "JD" | Mock — dinamik olmalı |
| dashboard/page.tsx | "Hoş Geldiniz, John" | Mock — `{user.firstName}` olmalı |
| dashboard/page.tsx | "Grafik Placeholder" | Placeholder — kaldırılmalı |
| messages/page.tsx | "Mesajlaşma Arayüzü Placeholder" | Placeholder — implement edilmeli |
| settings/page.tsx | "Ayarlar Formu Placeholder" | Placeholder — implement edilmeli |
| customers/page.tsx | "Müşteri Listesi Placeholder" | Placeholder — redirect veya implement |

---

## 3. Sayfa Bazlı Audit Tablosu

### 3.1 Auth — Giriş Sayfası
`apps/web/src/app/(auth)/login/page.tsx`

| # | Eleman | Mevcut | Önerilen | Gerekçe | Öncelik |
|---|--------|--------|----------|---------|---------|
| 1 | Sayfa başlığı | "Hesabınıza giriş yapın" | "Tekrar hoş geldin! 👋" | Samimi ton, kişisel hissettir | P2 |
| 2 | E-posta placeholder | "ornek@sirket.com" | "ornek@ofis.com" | Emlak sektörüne özel | P3 |
| 3 | Şifre alanı | Placeholder yok | "Şifreni gir" | Boş input karışıklık yaratır | P2 |
| 4 | Buton | "Giriş Yap" | ✅ İyi | Aksiyon odaklı | — |
| 5 | Alt link | "Ücretsiz kayıt olun" | ✅ İyi | CTA net | — |
| 6 | Hata durumu | Yok (görünmüyor) | "E-posta veya şifre hatalı. Tekrar dene ya da şifreni sıfırla." | 3 katman eksik | P1 |

### 3.2 Auth — Kayıt Sayfası
`apps/web/src/app/(auth)/register/page.tsx`

| # | Eleman | Mevcut | Önerilen | Gerekçe | Öncelik |
|---|--------|--------|----------|---------|---------|
| 1 | Başlık | "Yeni hesap oluşturun" | "Hemen başla — ücretsiz!" | Daha davet edici | P2 |
| 2 | Ofis placeholder | "Örn: Emlak Ofisi A.Ş." | "Örn: Kadıköy Emlak" | Daha gerçekçi örnek | P3 |
| 3 | Şifre alanı | Placeholder yok | "En az 8 karakter" | Beklentiyi belirle | P1 |
| 4 | Buton | "Kayıt Ol" | "Hesabımı Oluştur" | Daha spesifik aksiyon | P2 |

### 3.3 Dashboard Ana Sayfa
`apps/web/src/app/(dashboard)/page.tsx`

| # | Eleman | Mevcut | Önerilen | Gerekçe | Öncelik |
|---|--------|--------|----------|---------|---------|
| 1 | Hoşgeldin | "Hoş Geldiniz, John" | "Günaydın, {user.firstName}! ☀️" | Dinamik + saat bazlı selamlama | P1 |
| 2 | Grafik alanı | "Grafik Placeholder" | Skeleton loader veya kaldır | UX kötü | P0 |
| 3 | KPI "Bekleyen İşler" | "3 acil" | "3 acil görev" | Daha açıklayıcı | P3 |

### 3.4 Portföy Yönetimi
`apps/web/src/app/(dashboard)/properties/page.tsx`

| # | Eleman | Mevcut | Önerilen | Gerekçe | Öncelik |
|---|--------|--------|----------|---------|---------|
| 1 | Sayfa açıklaması | "Portfolyonuzdeki mülkleri buradan yönetebilirsiniz." | "Tüm ilanlarını tek yerden yönet." | Sen dili, kısa | P2 |
| 2 | Boş durum (filtre) | "Aramanızla eşleşen ilan bulunamadı" | "Bu filtrelere uygun ilan yok. Filtreleri değiştirmeyi dene." | CTA içermeli | P2 |
| 3 | Boş durum (ilk) | "Henüz ilan eklenmemiş" | "İlk ilanını ekleyerek başla! 🏠" | Davet edici | P2 |
| 4 | Sayfalama | "Önceki" / "Sonraki" | ✅ İyi | Standart | — |

### 3.5 Yeni İlan Formu
`apps/web/src/components/properties/property-form.tsx`

| # | Eleman | Mevcut | Önerilen | Gerekçe | Öncelik |
|---|--------|--------|----------|---------|---------|
| 1 | Submit (oluştur) | "İlan Oluştur" | "İlanı Yayınla" | Daha güçlü CTA | P2 |
| 2 | Submit (loading) | "Kaydediliyor..." | "İlan oluşturuluyor..." | Spesifik durum | P3 |
| 3 | Mock alert | `alert("İlan başarıyla kaydedildi! (Mock)")` | Toast: "İlan kaydedildi ✓" | Native alert kaldır | P0 |
| 4 | Mahalle placeholder | "Mahalle adı (opsiyonel)" | "Örn: Caferağa, Moda" | Örnek değer ekle | P3 |
| 5 | Açıklama placeholder | "Mülk hakkında detaylı bilgi yazın (opsiyonel)" | "Mülkün öne çıkan özelliklerini yaz..." | Daha yönlendirici | P3 |

### 3.6 Değerleme Formu
`apps/web/src/components/valuation/ValuationForm.tsx`

| # | Eleman | Mevcut | Önerilen | Gerekçe | Öncelik |
|---|--------|--------|----------|---------|---------|
| 1 | Başlık | "AI Değerleme" | "AI Değerleme 🤖" | Görsel ipucu | P3 |
| 2 | Açıklama | "Mülk bilgilerini girerek yapay zeka destekli fiyat tahmini alın." | "Mülk bilgilerini gir, saniyeler içinde piyasa değerini öğren." | Daha aksiyon odaklı, sen dili | P2 |
| 3 | Kota hata | "Bu ay için belirlenen değerleme hakkınız dolmuştur..." | "Bu ayki değerleme hakkın doldu. Planını yükselterek sınırsız kullanabilirsin." | Sen dili + çözüm | P1 |
| 4 | Submit | "Değerleme Yap" | "Değerlemeyi Başlat" | Daha güçlü CTA | P2 |
| 5 | Submit (loading) | "Değerleme yapılıyor..." | "Hesaplanıyor..." | Kısa | P3 |
| 6 | Hata (catch) | "Değerleme sırasında bir hata oluştu. Lütfen tekrar deneyiniz." | "Değerleme şu an yapılamadı. Birkaç dakika sonra tekrar dene." | Sen dili + 3 katman | P1 |

### 3.7 Değerleme Sonucu
`apps/web/src/components/valuation/ValuationResult.tsx`

| # | Eleman | Mevcut | Önerilen | Gerekçe | Öncelik |
|---|--------|--------|----------|---------|---------|
| 1 | Boş durum | "Henüz Değerleme Yapılmadı" | "Henüz değerleme yapılmadı" | Küçük harf tutarlılığı | P3 |
| 2 | PDF hata | `alert("PDF indirilemedi...")` | Toast: "PDF şu an indirilemedi. Tekrar dene." | Native alert kaldır | P0 |
| 3 | Paylaş butonu | "Paylaş" (disabled, tooltip: "Yakında") | "Paylaş (Yakında)" | Tooltip yerine inline bilgi | P3 |
| 4 | PDF butonu | "Detaylı Rapor İndir (PDF)" | "Raporu İndir (PDF)" | Kısa | P3 |

### 3.8 Değerleme Geçmişi
`apps/web/src/components/valuation/ValuationHistory.tsx`

| # | Eleman | Mevcut | Önerilen | Gerekçe | Öncelik |
|---|--------|--------|----------|---------|---------|
| 1 | Boş durum | "Henüz geçmiş bir değerleme bulunmuyor." | "Henüz değerleme yapılmadı. İlk değerlemeni başlat!" | CTA ekle | P2 |
| 2 | Detay linki | "Detay" | "Görüntüle" | Daha aksiyon odaklı | P3 |

### 3.9 Kota Bilgisi
`apps/web/src/components/valuation/QuotaInfo.tsx`

| # | Eleman | Mevcut | Önerilen | Gerekçe | Öncelik |
|---|--------|--------|----------|---------|---------|
| 1 | Başlık | "Değerleme Hakkı" | "Kalan Hakkın" | Sen dili | P2 |
| 2 | CTA | "Plan Yükselt" | "Planı Yükselt" | Türkçe gramer | P2 |

### 3.10 Bölge Analizi
`apps/web/src/app/(dashboard)/areas/page.tsx`

| # | Eleman | Mevcut | Önerilen | Gerekçe | Öncelik |
|---|--------|--------|----------|---------|---------|
| 1 | Boş durum | "Bir Bölge Seçin" | "Analiz için bir ilçe seç 📍" | Sen dili, emoji | P2 |
| 2 | Hata mesajı | "Bölge verileri yüklenirken bir sorun oluştu. Lütfen daha sonra tekrar deneyiniz." | "Bölge verileri şu an yüklenemiyor. Birkaç dakika sonra tekrar dene." | Sen dili | P2 |

### 3.11 Bölge Karşılaştırma
`apps/web/src/app/(dashboard)/areas/compare/page.tsx`

| # | Eleman | Mevcut | Önerilen | Gerekçe | Öncelik |
|---|--------|--------|----------|---------|---------|
| 1 | Hata mesajı | "Veriler yüklenemedi." | "Veriler şu an yüklenemiyor. Tekrar dene." | 3 katman: ne + neden + çözüm | P2 |
| 2 | Boş durum | "Karşılaştırma için ilçe seçin" | "İlçe ekleyerek karşılaştırmaya başla" | Aksiyon odaklı | P2 |

### 3.12 Harita
`apps/web/src/app/(dashboard)/maps/page.tsx`

| # | Eleman | Mevcut | Önerilen | Gerekçe | Öncelik |
|---|--------|--------|----------|---------|---------|
| 1 | Yükleniyor | "Harita yükleniyor..." | "Harita hazırlanıyor..." | Daha doğal | P3 |
| 2 | Boş seçim | "Harita üzerinden bir mülk veya bölge seçerek detayları görüntüleyebilirsiniz." | "Haritadan bir bölge veya ilan seç, detayları burada gör." | Sen dili, kısa | P2 |

### 3.13 Müşteri CRM
`apps/web/src/app/(dashboard)/dashboard/customers/page.tsx` ve bileşenler

| # | Eleman | Mevcut | Önerilen | Gerekçe | Öncelik |
|---|--------|--------|----------|---------|---------|
| 1 | Boş tablo | "Müşteri bulunamadı." | "Müşteri bulunamadı. Yeni müşteri ekleyerek başla." | CTA | P2 |
| 2 | 404 başlık | "Müşteri Bulunamadı" | "Bu müşteri kaydı bulunamadı" | Daha açıklayıcı | P3 |
| 3 | 404 açıklama | "Aradığınız müşteri kaydı mevcut değil veya silinmiş olabilir." | "Bu müşteri kaydı silinmiş veya taşınmış olabilir." | Kısa | P3 |
| 4 | Hızlı ekle başlık | "Hızlı Müşteri Ekle" | ✅ İyi | Net | — |
| 5 | Kaydet butonu | "Kaydet" | "Müşteriyi Kaydet" | Spesifik | P2 |

### 3.14 Müşteri Notları
`apps/web/src/components/customers/customer-notes.tsx`

| # | Eleman | Mevcut | Önerilen | Gerekçe | Öncelik |
|---|--------|--------|----------|---------|---------|
| 1 | Boş durum | "Henüz not eklenmemiş." | "Henüz not yok. İlk notu ekleyerek iletişim geçmişini başlat." | CTA | P2 |
| 2 | Placeholder | "Yeni bir not ekle..." | "Müşteri hakkında not yaz... (ör: görüşme özeti)" | Örnek ekle | P3 |

### 3.15 Eşleştirmeler
`apps/web/src/components/customers/match-list.tsx`

| # | Eleman | Mevcut | Önerilen | Gerekçe | Öncelik |
|---|--------|--------|----------|---------|---------|
| 1 | Boş durum başlık | "Henüz eşleşme bulunamadı." | "Henüz eşleşme yok" | Kısa, olumlu | P3 |
| 2 | Boş durum açıklama | "Müşteri tercihleri ile uyumlu ilanlar otomatik eşleştirilecek." | "Müşteri tercihleriyle eşleşen ilanlar otomatik olarak burada görünecek." | Daha açık | P3 |

### 3.16 İlan Asistanı
`apps/web/src/app/(dashboard)/listings/` bileşenleri

| # | Eleman | Mevcut | Önerilen | Gerekçe | Öncelik |
|---|--------|--------|----------|---------|---------|
| 1 | Boş sonuç | "Henüz ilan metni oluşturulmadı" | "İlan metni henüz oluşturulmadı" | Doğal sıra | P3 |
| 2 | Boş sonuç CTA | 'Sol paneldeki formu doldurup "İlan Metni Oluştur" butonuna tıklayın.' | "Formu doldur ve 'İlan Metni Oluştur'a tıkla." | Sen dili, kısa | P2 |
| 3 | Kopyala butonu | "Metni Kopyala" → "Kopyalandı" | ✅ İyi | Durum değişimi var | — |
| 4 | Kredi bilgisi | "1 kredi kullanılır" | "1 kredi kullanılır 💎" | Görsel ipucu | P3 |

### 3.17 Virtual Staging
`apps/web/src/app/(dashboard)/listings/components/virtual-staging-tab.tsx`

| # | Eleman | Mevcut | Önerilen | Gerekçe | Öncelik |
|---|--------|--------|----------|---------|---------|
| 1 | Upload alanı | "Tıkla veya sürükle" | "Fotoğraf yüklemek için tıkla veya sürükle" | Daha açık | P2 |
| 2 | Alt text | "Preview", "Before", "After" | "Yüklenen fotoğraf", "Öncesi", "Sonrası" | Türkçe + erişilebilirlik | P1 |
| 3 | Loading | "AI mobilya yerleştirmesi yapılıyor" | "Yapay zeka mobilya yerleştiriyor..." | Daha doğal | P3 |

### 3.18 Vitrin (Network)
`apps/web/src/app/(dashboard)/network/page.tsx` ve bileşenler

| # | Eleman | Mevcut | Önerilen | Gerekçe | Öncelik |
|---|--------|--------|----------|---------|---------|
| 1 | Boş vitrin | "Henüz vitrin oluşturmadınız" | "Henüz vitrinin yok" | Sen dili | P2 |
| 2 | Boş vitrin CTA | "Müşterilerinize özel bir vitrin sayfası oluşturun ve seçtiğiniz ilanları tek bir bağlantı ile paylaşın." | "Müşterilerin için özel bir vitrin oluştur, ilanlarını tek linkle paylaş." | Sen dili, kısa | P2 |
| 3 | Silme onayı | `confirm("Bu vitrini silmek istediğinize emin misiniz?")` | Modal: "Bu vitrini silmek istediğinden emin misin? Bu işlem geri alınamaz." | Native confirm kaldır, modal kullan | P0 |
| 4 | Kaydet butonu | "Kaydet" (düzenleme) | "Değişiklikleri Kaydet" | Spesifik | P2 |

### 3.19 Kredi Hesaplayıcı
`apps/web/src/app/(dashboard)/calculator/page.tsx`

| # | Eleman | Mevcut | Önerilen | Gerekçe | Öncelik |
|---|--------|--------|----------|---------|---------|
| 1 | Boş durum | "Kredi Hesaplaması Yapın" | "Kredi hesaplaması yap" | Sen dili | P2 |
| 2 | Boş durum CTA | 'Soldaki formu doldurup "Hesapla" butonuna tıklayarak...' | 'Formu doldur ve "Hesapla"ya tıkla.' | Kısa, sen dili | P2 |
| 3 | Submit | "Hesapla" | ✅ İyi | Kısa ve net | — |

### 3.20 Telegram Mini App — Ana Sayfa
`apps/web/src/app/tg/page.tsx`

| # | Eleman | Mevcut | Önerilen | Gerekçe | Öncelik |
|---|--------|--------|----------|---------|---------|
| 1 | Metrik label | "Portfoly" | "Portföy" | Yazım hatası! | P0 |
| 2 | Hata fallback | "Bilinmeyen bir hata oluştu." | "Bir sorun oluştu. Tekrar dene." | Daha samimi | P2 |
| 3 | Boş durum | "Henüz veri yok" | "Henüz hiçbir şey eklenmedi" | Daha insan | P3 |
| 4 | Boş CTA | "Başlayın" | "Hemen Başla" | Daha güçlü | P2 |

### 3.21 Telegram Mini App — Değerleme
`apps/web/src/app/tg/valuation/page.tsx`

| # | Eleman | Mevcut | Önerilen | Gerekçe | Öncelik |
|---|--------|--------|----------|---------|---------|
| 1 | Submit | "Değerleme Hesapla" | "Değerle" | Mobilde kısa olmalı | P2 |
| 2 | MAPE bilgi | "Ortalama MAPE: %9.94" | "Tahmin doğruluğu: %90" | Kullanıcı dostu | P1 |
| 3 | Kota hata başlık | "Kota Aşıldı" | "Değerleme hakkın doldu" | Sen dili, samimi | P1 |

### 3.22 Telegram Mini App — CRM
`apps/web/src/app/tg/crm/page.tsx`

| # | Eleman | Mevcut | Önerilen | Gerekçe | Öncelik |
|---|--------|--------|----------|---------|---------|
| 1 | Boş durum | "Henüz müşteri yok" | ✅ İyi | Kısa, net | — |
| 2 | Boş CTA | "İlk Müşteriyi Ekle" | "İlk Müşterini Ekle" | Sen dili | P2 |
| 3 | Hata mesajı | "Kayıt sırasında bir hata oluştu." | "Kayıt yapılamadı. Bilgileri kontrol edip tekrar dene." | 3 katman | P1 |

### 3.23 Vitrin Sayfası (Public)
`apps/web/src/app/vitrin/[slug]/page.tsx`

| # | Eleman | Mevcut | Önerilen | Gerekçe | Öncelik |
|---|--------|--------|----------|---------|---------|
| 1 | Görsel placeholder | "Görsel Yok" | "Fotoğraf yakında eklenecek" | Olumlu ton | P2 |
| 2 | CTA metin | "Bu ilanlarla ilgileniyor musunuz?" | "Bu ilanlar ilgini çekti mi?" | Sen dili | P2 |
| 3 | CTA alt metin | "Hemen iletişime geçin, detayları görüşelim." | "Detaylar için hemen yaz!" | Kısa, aksiyon | P2 |
| 4 | WhatsApp butonu | "WhatsApp ile İletişime Geç" | "WhatsApp'tan Yaz" | Kısa | P2 |

### 3.24 Hata Sayfaları

| Sayfa | Mevcut | Önerilen | Öncelik |
|-------|--------|----------|---------|
| error.tsx | "Bir şeyler ters gitti" | "Hay aksi, bir sorun oluştu!" | P2 |
| dashboard/error.tsx | "Yükleme Hatası" | "Sayfa yüklenemedi" | P2 |
| not-found.tsx başlık | "Sayfa Bulunamadı" | "Aradığın sayfa bulunamadı" | P2 |
| not-found.tsx açıklama | "Aradığınız sayfaya ulaşılamıyor..." | "Bu sayfa kaldırılmış veya taşınmış olabilir." | P2 |
| not-found.tsx CTA | "Ana Sayfaya Dön" | "Ana Sayfaya Git" | P3 |

### 3.25 Navigasyon

| Eleman | Mevcut | Önerilen | Gerekçe | Öncelik |
|--------|--------|----------|---------|---------|
| sidebar "Degerleme" | "Degerleme" | "Değerleme" | Türkçe karakter eksik | P0 |
| sidebar "Ağ" | "Ağ" | "Vitrin" | Kullanıcı "ağ"ı anlamaz | P1 |
| sidebar "Mülkler" | "Mülkler" | "İlanlarım" | Sektör dili — emlakçılar "ilan" der | P1 |

### 3.26 Deprem Risk Kartları

| Eleman | Mevcut | Önerilen | Gerekçe | Öncelik |
|--------|--------|----------|---------|---------|
| Uyarı metni | "Bu skor tahmini bir değerdir ve kesin mühendislik değerlendirmesi yerine geçmez. Detaylı analiz için uzman görüşü alınız." | "Bu skor tahminidir, kesin değerlendirme yerine geçmez. Detaylı analiz için uzman görüşü al." | Sen dili + kısa | P2 |

---

## 4. Hata Mesajları Sözlüğü

Her hata mesajı 3 katmanlı yapıda olmalı: **Ne oldu** → **Neden** → **Ne yapmalı**

### 4.1 Authentication Hataları

| ID | HTTP | Mevcut | Önerilen (3 Katman) |
|----|------|--------|---------------------|
| auth.invalid_credentials | 401 | "E-posta veya şifre hatalı." | "Giriş yapılamadı. E-posta veya şifre hatalı. Şifreni sıfırlamak için 'Şifremi Unuttum'a tıkla." |
| auth.token_expired | 401 | "Token geçersiz veya süresi dolmuş." | "Oturum süren doldu. Güvenliğin için tekrar giriş yap." |
| auth.email_exists | 409 | "Bu e-posta adresi zaten kayıtlı: {email}" | "Bu e-posta zaten kayıtlı. Giriş yapmayı dene veya farklı bir e-posta kullan." |
| auth.account_disabled | 401 | "Hesap deaktif edilmiş." | "Hesabın deaktif edilmiş. Destek ekibiyle iletişime geç." |
| auth.invalid_token_type | 401 | "Geçersiz token tipi. Refresh token gerekli." | "Oturum doğrulanamadı. Lütfen tekrar giriş yap." |
| auth.user_not_found | 401 | "Kullanıcı bulunamadı." | "Bu hesap bulunamadı. Kayıt olmayı dene." |
| auth.office_id_required | 401 | "Kayıt için office_id gereklidir." | "Kayıt için ofis bilgisi gerekli. Ofis yöneticinden davet linki iste." |

### 4.2 Değerleme Hataları

| ID | HTTP | Mevcut | Önerilen (3 Katman) |
|----|------|--------|---------------------|
| valuation.quota_exceeded | 429 | "Aylık değerleme kotanız doldu." | "Bu ayki değerleme hakkın doldu. Planını yükselterek sınırsız değerleme yapabilirsin." |
| valuation.not_found | 404 | "Değerleme (id={id}) bulunamadı." | "Bu değerleme kaydı bulunamadı. Silinmiş veya taşınmış olabilir." |
| valuation.model_not_ready | 500 | "Model yüklenmedi. Inference servisi hazır değil." | "Değerleme sistemi şu an hazırlanıyor. Birkaç dakika sonra tekrar dene." |
| valuation.inference_error | 500 | "Değerleme sırasında bir hata oluştu." | "Değerleme şu an yapılamadı. Bilgileri kontrol edip tekrar dene." |
| valuation.insufficient_credits | 400 | "Yetersiz kredi bakiyesi." | "Kredi bakiyen yetersiz. Kredi satın alarak devam edebilirsin." |

### 4.3 İlan / Mülk Hataları

| ID | HTTP | Mevcut | Önerilen (3 Katman) |
|----|------|--------|---------------------|
| property.not_found | 404 | "İlan (id={id}) bulunamadı." | "Bu ilan bulunamadı. Kaldırılmış veya yayından çekilmiş olabilir." |
| property.title_too_short | 422 | "Başlık en az 5 karakter olmalıdır" | "İlan başlığı çok kısa. En az 5 karakter gir." |
| property.area_invalid | 422 | "Alan en az 10 m² olmalıdır" | "Geçersiz alan bilgisi. Alan 10-50.000 m² arasında olmalı." |

### 4.4 Bölge Hataları

| ID | HTTP | Mevcut | Önerilen (3 Katman) |
|----|------|--------|---------------------|
| area.not_found | 404 | "Bölge (id={district}) bulunamadı." | "Bu bölgenin verileri henüz mevcut değil. Farklı bir ilçe dene." |
| area.min_districts | 422 | "En az bir ilçe adı belirtmelisiniz." | "Karşılaştırma için en az bir ilçe seç." |
| area.max_districts | 422 | "En fazla 3 ilçe karşılaştırabilirsiniz." | "En fazla 3 ilçe karşılaştırabilirsin. Birini kaldırıp tekrar dene." |
| area.trend_not_found | 404 | "Fiyat trendi (id={district}) bulunamadı." | "Bu ilçe için fiyat trendi verisi henüz yok." |

### 4.5 Müşteri / CRM Hataları

| ID | HTTP | Mevcut | Önerilen (3 Katman) |
|----|------|--------|---------------------|
| customer.not_found | 404 | "Müşteri (id={id}) bulunamadı." | "Bu müşteri kaydı bulunamadı. Silinmiş olabilir." |
| customer.quota_exceeded | 403 | "Müşteri kotanız doldu. Mevcut: {count}/{quota}." | "Müşteri limitine ulaştın ({count}/{quota}). Planını yükselterek daha fazla müşteri ekleyebilirsin." |
| customer.invalid_status_transition | 422 | "Geçersiz lead status geçişi: '{current}' → '{new}'." | "Bu durum değişikliği yapılamaz. '{current}' durumundan '{new}' durumuna geçiş mümkün değil." |
| match.not_found | 404 | "Eşleştirme (id={id}) bulunamadı." | "Bu eşleştirme kaydı bulunamadı." |

### 4.6 Harita Hataları

| ID | HTTP | Mevcut | Önerilen (3 Katman) |
|----|------|--------|---------------------|
| map.bbox_format | 422 | "bbox formatı hatalı. Beklenen: minLon,minLat,maxLon,maxLat" | "Harita koordinatları hatalı. Sayfayı yenileyip tekrar dene." |
| map.bbox_invalid | 422 | "bbox değerleri geçersiz" | "Harita alanı geçersiz. Farklı bir bölge seç." |
| earthquake.not_found | 404 | "Deprem riski (id={district}) bulunamadı." | "Bu ilçe için deprem risk verisi henüz mevcut değil." |

### 4.7 Mesajlaşma / Telegram Hataları

| ID | HTTP | Mevcut | Önerilen (3 Katman) |
|----|------|--------|---------------------|
| telegram.already_linked | 409 | "Telegram hesabınız zaten bağlı. Önce mevcut bağlantıyı kaldırın." | "Telegram hesabın zaten bağlı. Önce Ayarlar'dan mevcut bağlantıyı kaldır." |
| telegram.link_not_found | 404 | "Telegram bağlantısı bulunamadı." | "Telegram bağlantısı bulunamadı. Henüz hesabını bağlamamış olabilirsin." |
| telegram.bot_not_configured | 401 | "Telegram bot yapılandırması eksik. Lütfen yönetici ile iletişime geçin." | "Telegram botu henüz yapılandırılmamış. Yöneticinle iletişime geç." |
| telegram.verification_failed | 401 | "Telegram doğrulama başarısız: {exc}" | "Telegram doğrulaması başarısız oldu. Uygulamayı kapatıp tekrar aç." |

### 4.8 Ödeme Hataları

| ID | HTTP | Mevcut | Önerilen (3 Katman) |
|----|------|--------|---------------------|
| payment.invalid_payload | 400 | "Invalid payload format" | "Ödeme verisi geçersiz. Tekrar dene." |
| payment.signature_failed | 403 | "Webhook imza doğrulaması başarısız." | "Ödeme doğrulanamadı. İşlem reddedildi." |
| calculator.invalid_amount | 400 | "Kredi tutarı sıfır veya negatif olamaz. Peşinat yüzdesini kontrol edin." | "Kredi tutarı geçersiz. Peşinat oranını kontrol edip tutarın pozitif olduğundan emin ol." |

### 4.9 Vitrin / Showcase Hataları

| ID | HTTP | Mevcut | Önerilen (3 Katman) |
|----|------|--------|---------------------|
| showcase.not_found | 404 | "Vitrin (id={id}) bulunamadı." | "Bu vitrin bulunamadı. Silinmiş veya yayından kaldırılmış olabilir." |
| showcase.no_whatsapp | 404 | "Bu vitrin için WhatsApp numarası tanımlanmamış." | "Bu vitrinde WhatsApp numarası yok. Vitrin ayarlarından numara ekle." |
| showcase.invalid_phone | 400 | "Geçersiz telefon numarası." | "Telefon numarası geçersiz. Doğru formatta (05XX XXX XX XX) gir." |

### 4.10 Bildirim Hataları

| ID | HTTP | Mevcut | Önerilen (3 Katman) |
|----|------|--------|---------------------|
| notification.not_found | 404 | "Bildirim (id={id}) bulunamadı." | "Bu bildirim bulunamadı. Zaten okunmuş veya silinmiş olabilir." |

---

## 5. Boş Durum Metinleri Kataloğu

Her boş durum şu yapıda olmalı: **İkon** + **Başlık** + **Açıklama** + **CTA Butonu**

### 5.1 Dashboard

```
🏠
Hoş geldin!
İlk ilanını ekleyerek platformu keşfetmeye başla.
[İlk İlanı Ekle]
```

### 5.2 Portföy / İlanlar

```
📋
Henüz ilan eklenmedi
İlk ilanını ekleyerek portföyünü oluşturmaya başla.
[Yeni İlan Ekle]
```

**Filtreli boş durum:**
```
🔍
Bu filtrelere uygun ilan yok
Filtreleri değiştirmeyi veya temizlemeyi dene.
[Filtreleri Temizle]
```

### 5.3 Değerleme Sonucu

```
📊
Henüz değerleme yapılmadı
Mülk bilgilerini gir ve "Değerlemeyi Başlat" butonuna tıkla.
```

### 5.4 Değerleme Geçmişi

```
📈
Geçmiş değerleme yok
İlk değerlemeni yaparak burada geçmişini takip et.
[Değerleme Yap]
```

### 5.5 Bölge Analizi (İlçe Seçilmedi)

```
📍
Analiz için bir ilçe seç
Listeden ilçe seçerek detaylı pazar analizi, fiyat trendi ve risk raporlarını görüntüle.
```

### 5.6 Bölge Karşılaştırma

```
⚖️
Karşılaştırmaya başla
En fazla 3 ilçe seçerek fiyat, kira verimi ve yatırım skorlarını karşılaştır.
```

### 5.7 Harita (Seçim Yok)

```
🗺️
Haritadan bir bölge veya ilan seç
Detaylı bilgileri burada görüntüle.
```

### 5.8 Müşteri Listesi (Boş)

```
👥
Henüz müşteri eklenmedi
İlk müşterini ekleyerek CRM'i kullanmaya başla.
[Yeni Müşteri Ekle]
```

### 5.9 Müşteri Notları (Boş)

```
📝
Henüz not yok
İlk notu ekleyerek iletişim geçmişini başlat.
[Not Ekle]
```

### 5.10 Eşleştirmeler (Boş)

```
🔗
Henüz eşleşme yok
Müşteri tercihleriyle uyumlu ilanlar otomatik olarak burada görünecek.
```

### 5.11 İlan Asistanı — Metin Sonucu

```
✍️
İlan metni henüz oluşturulmadı
Formu doldur ve "İlan Metni Oluştur"a tıkla.
```

### 5.12 Virtual Staging (Fotoğraf Yok)

```
📸
Fotoğraf yüklenmedi
Boş bir oda fotoğrafı yükleyip tarz seçerek başla.
```

### 5.13 Portal Export (İlan Metni Yok)

```
🔄
Önce ilan metni oluştur
Portal entegrasyonu için "Metin Oluştur" sekmesinden bir ilan oluştur.
```

### 5.14 Vitrin Yönetimi (Boş)

```
🏪
Henüz vitrinin yok
Müşterilerin için özel vitrin oluştur, ilanlarını tek linkle paylaş.
[Yeni Vitrin Oluştur]
```

### 5.15 Paylaşım Ağı (Boş)

```
🌐
Paylaşıma açılmış vitrin yok
Diğer ofisler vitrinlerini paylaştığında burada listelenecek.
```

### 5.16 Kredi Hesaplayıcı (Boş)

```
💰
Kredi hesaplaması yap
Formu doldur ve "Hesapla"ya tıkla. Amortisman tablosu ve banka karşılaştırması burada görünecek.
```

### 5.17 Fiyat Trendi (Veri Yok)

```
📉
Fiyat trendi verisi henüz mevcut değil
Bu bölge için yeterli veri toplandığında trend grafiği burada görünecek.
```

### 5.18 Telegram Mini App — Ana Sayfa (Boş)

```
🚀
Henüz hiçbir şey eklenmedi
İlk müşterini ekleyerek veya değerleme yaparak başla!
[Hemen Başla]
```

### 5.19 Telegram Mini App — CRM (Boş)

```
👤
Henüz müşteri yok
Sağ alttaki + butonuyla ilk müşterini ekle.
[İlk Müşteriyi Ekle]
```

### 5.20 Telegram Bot — Portföy (Boş)

```
📋 Portföyünde henüz ilan bulunmuyor.
Web panelden yeni ilan ekleyebilirsin.
```

### 5.21 Telegram Bot — Rapor (Değerleme Yok)

```
📊 Henüz değerleme yapmadın.
/degerleme komutuyla başlayabilirsin.
Örnek: /degerleme Kadıköy, 120, 3+1, 5, 10
```

---

## 6. Telegram Bot Mesajları Revizyonu

### 6.1 Karşılama Mesajı

**Mevcut:**
```
Merhaba! 👋 Emlak Teknoloji Platformu botuna hoş geldiniz.
Kullanılabilir komutlar: ...
Hesabınızı bağlamak için web panelden 'Telegram Bağla' butonunu kullanın.
```

**Önerilen:**
```
Merhaba! 👋 EmlakTech botuna hoş geldin!

Yapabileceklerin:
/degerleme  — AI konut değerleme
/musteri    — Hızlı müşteri kayıt
/fotograf   — Sanal mobilyalama
/kredi      — Konut kredisi hesapla
/portfoy    — Portföy listesi
/rapor      — Son değerleme raporu (PDF)
/ilan       — İlan metni oluştur
/help       — Tüm komutlar

Hesabını bağlamak için: Web Panel → Ayarlar → Telegram Bağla
```

### 6.2 Bağlantı Hataları (Tekrarlayan Mesaj Sorunu)

5 farklı komut için aynı "Hesabınız bağlanmamış" mesajı tekrarlanıyor. Tek bir sabit kullanılmalı:

**Önerilen Standart:**
```
❌ Hesabın bağlı değil

Bu komutu kullanmak için Telegram hesabını platforma bağla.
📱 Web Panel → Ayarlar → Telegram Bağla
```

### 6.3 Hata Mesajları — Standart Şablonlar

**Mevcut `_ERROR_MESSAGES` dict'i iyi yapılandırılmış ama dili güncellenebilir:**

| Anahtar | Mevcut | Önerilen |
|---------|--------|----------|
| general | "❌ Bir hata oluştu. Lütfen tekrar deneyin." | "❌ Bir sorun oluştu. Tekrar dene." |
| quota | "⚠️ Kota limitinize ulaştınız. Plan yükseltmek için /help yazın." | "⚠️ Limitine ulaştın. Planını yükseltmek için /help yaz." |
| not_found | "🔍 İstenen kayıt bulunamadı." | "🔍 Aradığın kayıt bulunamadı." |
| permission | "🔒 Bu işlem için yetkiniz yok." | "🔒 Bu işlem için yetkin yok." |
| timeout | "⏳ İşlem zaman aşımına uğradı. Lütfen tekrar deneyin." | "⏳ İşlem zaman aşımına uğradı. Tekrar dene." |
| invalid_input | "📝 Girdi formatı hatalı. Lütfen doğru formatı kullanın." | "📝 Girdi formatı hatalı. Doğru formatı kullan." |

### 6.4 İlan Wizard — Hata Mesajı İyileştirmesi

**Mevcut:**
```
❌ Girdi formatı hatalı.
Doğru format: <m2> <oda> <bina_yası> <kat>
Örnek: 120 3+1 5 3
```

**Önerilen:**
```
❌ Girdi formatı hatalı

Doğru format: alan oda bina_yaşı kat
Örnek: 120 3+1 5 3

📏 Alan: 10-1000 m²
🚪 Oda: 1+0 — 10+2
🏗️ Bina yaşı: 0-100
🏢 Kat: 0-50
```

### 6.5 Inline Butonlar

| Mevcut | Önerilen | Gerekçe |
|--------|----------|---------|
| "✅ Evet" | "✅ Onayla" | Daha spesifik |
| "❌ İptal" | ✅ İyi | — |
| "🔄 Yeniden Üret" | ✅ İyi | — |

---

## 7. Genel Öneriler ve Sonraki Adımlar

### 7.1 Teknik Altyapı Önerileri

1. **Merkezi Metin Yönetimi:** Tüm UI metinlerini `apps/web/src/constants/copy.ts` dosyasında topla. i18n-ready yapı için `sayfa.bolum.eleman` formatında ID kullan.

```typescript
// Örnek yapı
export const COPY = {
  auth: {
    login: {
      title: "Tekrar hoş geldin! 👋",
      submit: "Giriş Yap",
      placeholder: { email: "ornek@ofis.com", password: "Şifreni gir" }
    }
  },
  valuation: {
    form: {
      title: "AI Değerleme 🤖",
      submit: "Değerlemeyi Başlat",
      submitLoading: "Hesaplanıyor..."
    }
  }
} as const;
```

2. **Toast Sistemi:** `alert()` ve `confirm()` çağrılarını kaldır, react-hot-toast veya sonner gibi bir toast kütüphanesi kullan.

3. **Hata Sınıfları:** Backend'de her hata sınıfının `user_message` alanı olsun (kullanıcıya gösterilecek) + `detail` alanı (geliştirici için).

### 7.2 Dil Standartları

| Kural | Örnek |
|-------|-------|
| **Sen dili kullan** | "Değerleme hakkınız" → "Değerleme hakkın" |
| **"Lütfen" kullanma** | "Lütfen tekrar deneyiniz" → "Tekrar dene" |
| **"-iniz/-ınız" kullanma** | "Bilgilerinizi girin" → "Bilgileri gir" |
| **Kısa tut** | "Portfolyonuzdeki mülkleri buradan yönetebilirsiniz" → "İlanlarını tek yerden yönet" |
| **Olumlu ton** | "Bulunamadı" → "Henüz eklenmedi" |
| **Aksiyon fiili** | "Kaydet" → "Müşteriyi Kaydet" |
| **Toast: 2-3 kelime** | "İlan başarıyla kaydedildi!" → "İlan kaydedildi ✓" |

### 7.3 Accessibility Tavsiyeleri

1. Tüm ikonlu butonlara `aria-label` ekle
2. Tüm form alanlarına `aria-describedby` ile hata mesajı bağla
3. Loading durumları için `aria-live="polite"` kullan
4. Renk bağımlı bilgilerde (badge'ler) metin alternatifi sağla
5. `sr-only` class ile ekran okuyucu metinleri ekle (özellikle sayfalama butonları)
6. Virtual staging "Before"/"After" → "Öncesi"/"Sonrası" (Türkçe alt metin)

### 7.4 Öncelik Matrisi

| Öncelik | Sayı | Açıklama |
|---------|------|----------|
| **P0 — Acil** | 8 | Yazım hataları, native alert/confirm, hardcoded mock |
| **P1 — Yüksek** | 14 | Hata mesajları 3 katman, nav isimleri, erişilebilirlik |
| **P2 — Orta** | 35+ | Sen dili dönüşümü, CTA iyileştirme, boş durum |
| **P3 — Düşük** | 20+ | Placeholder örnekleri, emoji, küçük iyileştirmeler |

### 7.5 Uygulama Sırası Önerisi

1. **Sprint 1:** P0 düzeltmeleri (alert→toast, yazım hataları, mock veriler)
2. **Sprint 2:** P1 düzeltmeleri (hata mesajları, navigasyon, erişilebilirlik)
3. **Sprint 3:** P2 dönüşümler (sen dili, CTA, boş durumlar)
4. **Sprint 4:** P3 iyileştirmeler (placeholder, emoji, detay)

---

## Ekler

### Ek A: Taranan Dosya Listesi

**Frontend (60+ dosya):**
- Auth: login, register
- Dashboard: page, properties, valuations, areas, maps, customers, messages, settings, listings, network, calculator
- Components: property-form, property-card, search-bar, search-filters, ValuationForm, ValuationResult, ValuationHistory, ComparablesList, AreaComparison, QuotaInfo, customer-form, customer-table, customer-card, customer-pipeline, customer-filters, quick-add-customer, customer-info, customer-notes, match-card, match-list, showcase-form, delete-showcase-button, listing-text-form, listing-text-result, portal-export-tab, virtual-staging-tab
- Layout: header, sidebar, mobile-nav
- UI: error-display, data-freshness-badge, data-freshness-tooltip
- Map: AreaAnalysisCard, PropertyPopup, PoiPopup, LayerControl
- Telegram Mini App: page, valuation, crm, tg-bottom-nav
- Vitrin: [slug]/page
- Schema/Validation: valuation/schema.ts, property-form-schema.ts

**Backend (30+ dosya):**
- Auth: router, service
- Valuations: router, inference_service, comparable_service, anomaly_service, quota_service
- Properties: router, search, search_router
- Areas: router
- Maps: router
- Earthquake: router, service
- Customers: router, service
- Matches: router, service, matching_service
- Messaging: router, gateway, service, bot/router, bot/conversation_state, bot/handlers
- Notifications: router, service
- Payments: router, webhook
- Showcases: router, service
- Calculator: calculator_router, calculator_service

**Telegram Bot:** handlers.py (30+ sabit mesaj, 6 hata şablonu, 10+ dinamik mesaj, 10 buton, 8 callback)

**Mesaj Şablonları (5 dosya):** welcome, payment_success, payment_failed, new_match, subscription_expiring

### Ek B: Validasyon Mesajları Özeti

| Kaynak | Mevcut | Önerilen |
|--------|--------|----------|
| property-form-schema.ts: title | "Başlık en az 5 karakter olmalıdır" | "İlan başlığı en az 5 karakter olmalı" |
| property-form-schema.ts: price | "Fiyat giriniz" | "Fiyat gir" |
| property-form-schema.ts: area | "Alan en az 10 m² olmalıdır" | "Alan en az 10 m² olmalı" |
| property-form-schema.ts: city | "Şehir seçimi zorunludur" | "Şehir seç" |
| property-form-schema.ts: district | "İlçe seçimi zorunludur" | "İlçe seç" |
| valuation/schema.ts: district | "İlçe seçimi zorunlu" | "İlçe seç" |
| valuation/schema.ts: gross_sqm | "Geçerli bir sayı giriniz" | "Geçerli bir sayı gir" |
| valuation/schema.ts: gross_sqm min | "En az 20 m2 olmalıdır" | "En az 20 m² olmalı" |
| valuation/schema.ts: room_count | "Oda sayısı seçimi zorunlu" | "Oda sayısı seç" |
| valuation/schema.ts: heating_type | "Isıtma tipi seçimi zorunlu" | "Isıtma tipi seç" |
| customer-form.tsx: name | "Ad soyad en az 2 karakter olmalıdır" | "Ad soyad en az 2 karakter olmalı" |
| customer-form.tsx: email | "Geçerli bir e-posta adresi giriniz" | "Geçerli bir e-posta gir" |
| listing-text-form.tsx: sqm | "Metrekare giriniz" | "Metrekare gir" |
| listing-text-form.tsx: district | "İlçe seçiniz" | "İlçe seç" |

---

*Bu doküman TASK-146 kapsamında 2026-02-26 tarihinde oluşturulmuştur.*
*Toplam: 500+ metin denetlendi, 80+ iyileştirme önerisi sunuldu.*
