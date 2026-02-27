# Emlak Teknoloji Platformu - UI/UX Tasarım Stratejisi

**Tarih:** 2026-02-20
**Versiyon:** 1.0
**Durum:** Hazır
**Kapsam:** Web Dashboard + Telegram Mini App + PWA

---

## 1. Tasarım Vizyonu ve İlkeleri

Platformun tasarım dili, emlak profesyonellerine (Danışman ve Broker) yönelik **güvenilir, veri odaklı ve operasyonel hızı artıran** bir araç seti sunmayı hedefler. "Süsleme" değil, "işlevsellik" ön plandadır.

### Temel Tasarım İlkeleri

1.  **Veri Odaklı Netlik (Data First):** Kullanıcılar karmaşık verilerle (fiyatlar, m², oranlar) çalışır. Tasarım, veriyi okunabilir, karşılaştırılabilir ve taranabilir (scannable) kılmalıdır. Sayısal veriler (fiyat, m²) monospaced font ile ayrıştırılmalıdır.
2.  **Operasyonel Hız (Speed over Glamour):** Emlak danışmanı sahadadır. Butonlar büyük, formlar kısa, akışlar kesintisiz olmalıdır. Gereksiz animasyonlardan kaçınılmalı, "tek tıkla sonuç" hedeflenmelidir.
3.  **Mobil Öncelikli & TMA Uyumlu:** Telegram Mini App (TMA) birincil temas noktalarından biridir. Tüm arayüzler önce mobil dar ekran (375px) için tasarlanır, sonra masaüstüne genişler (Progressive Enhancement).
4.  **Güven Veren Kurumsallık:** Turuncu (enerji/hareket) ve Gri/Zinc (profesyonellik/teknoloji) dengesiyle, kullanıcının müşterisine sunum yaparken gurur duyacağı modern bir arayüz.
5.  **Hatasız Yönlendirme:** Kullanıcı hata yapmaktan korkmamalıdır. Destructive işlemler (silme vb.) öncesi net onaylar, formlarda anlık validasyonlar ve açıklayıcı hata mesajları esastır.

### Persona Bazlı Yaklaşım

*   **Hakan (Danışman):** Hız arar. Sahada tek elle kullanım, hızlı veri girişi, müşteriye anlık sunum (PDF/Ekran görüntüsü) odaklıdır. -> *Büyük butonlar, kontrastlı metinler, mobil uyum.*
*   **Elif (Broker):** Kontrol arar. Dashboard üzerinden ekibini izler, raporlara bakar. -> *Yoğun veri tabloları, filtreleme araçları, masaüstü dashboard yerleşimi.*

---

## 2. Design System

### 2.1 Renk Paleti (WCAG 2.1 AA Uyumlu)

Marka rengi olarak **Turuncu** seçilmiştir. Enerjik, dikkat çekici ve sektörde ayrıştırıcıdır.

| Renk Rolü | Tailwind Class | HEX | Kullanım Alanı | Kontrast (Beyaz üzeri) |
| :--- | :--- | :--- | :--- | :--- |
| **Primary** | `orange-600` | `#EA580C` | Ana butonlar, aktif tablar, linkler | **AA (3.0+) Large Text** / *Dikkat: Beyaz metinle AA* |
| **Primary Hover** | `orange-700` | `#C2410C` | Hover durumları | AAA |
| **Secondary** | `zinc-900` | `#18181B` | Başlıklar, ikincil butonlar | AAA |
| **Background** | `white` / `zinc-50` | `#FFFFFF` / `#FAFAFA` | Sayfa zemini | - |
| **Surface** | `white` | `#FFFFFF` | Kartlar, modallar | - |
| **Border** | `zinc-200` | `#E4E4E7` | Çizgiler, input sınırları | - |
| **Success** | `emerald-600` | `#059669` | Pozitif trend, onay | AA |
| **Warning** | `amber-500` | `#F59E0B` | Bekleyen işlem, uyarı | (Siyah metinle kullanılmalı) |
| **Error** | `red-600` | `#DC2626` | Hata, silme, negatif trend | AA |
| **Info** | `blue-600` | `#2563EB` | Bilgilendirme, linkler | AA |

*Not: Dark mode için `zinc-950` zemin ve `zinc-800` surface renkleri tersine çevrilerek kullanılır.*

### 2.2 Tipografi

Okunabilirlik ve hiyerarşi esastır.

*   **Font Ailesi:**
    *   **Başlıklar:** `Poppins` (Google Fonts). Geometrik, modern, güvenilir. (Weight: 500, 600, 700)
    *   **Gövde Metni:** `Inter` (Google Fonts). UI için optimize edilmiş, yüksek okunabilirlik. (Weight: 400, 500)
    *   **Veriler / Sayılar:** `Roboto Mono` (Google Fonts). Fiyatlar, m², koordinatlar, ID'ler için. (Weight: 400, 500)

*   **Ölçek (Mobile Base / Desktop Base):**
    *   H1: 24px/32px (Bold)
    *   H2: 20px/24px (SemiBold)
    *   H3: 18px/20px (Medium)
    *   Body: 16px (Regular) - *Minimum okunabilir boyut*
    *   Small: 14px (Regular) - *İkincil metinler*
    *   Tiny: 12px (Medium) - *Etiketler, meta veriler*

### 2.3 Spacing & Grid

*   **Base Unit:** 4px (`0.25rem`). Tailwind standart spacing scale kullanılır.
*   **Layout Grid:**
    *   Desktop: 12 kolon, 24px gutter.
    *   Tablet: 8 kolon, 16px gutter.
    *   Mobile: 4 kolon, 16px gutter.
*   **Radius:**
    *   `rounded-md` (0.375rem / 6px) - Standart input ve butonlar.
    *   `rounded-xl` (0.75rem / 12px) - Kartlar ve modallar.
*   **Shadows:**
    *   `shadow-sm` - Kartlar (default).
    *   `shadow-md` - Hover durumu ve dropdownlar.
    *   `shadow-lg` - Modallar ve floating action buttons (FAB).

---

## 3. Component Kütüphanesi

Proje **shadcn/ui** (Radix UI + Tailwind CSS) üzerine kurulacaktır.

### Temel Bileşenler (Özelleştirilmiş)

1.  **Button:**
    *   `default`: bg-orange-600 text-white hover:bg-orange-700
    *   `secondary`: bg-zinc-100 text-zinc-900 hover:bg-zinc-200
    *   `outline`: border-zinc-200 text-zinc-900 hover:bg-zinc-50
    *   `ghost`: text-zinc-600 hover:bg-zinc-100 (Tablo içi aksiyonlar)
    *   *Mobile:* Min height 44px (touch target).

2.  **Input / Select:**
    *   Height: 40px (Desktop), 44px (Mobile).
    *   Focus ring: `ring-2 ring-orange-600/20 border-orange-600`.
    *   Error state: `border-red-500 ring-red-500/20`.

3.  **DataCard (Dashboard Widget):**
    *   `bg-white rounded-xl border border-zinc-200 p-4`.
    *   Başlık (Inter 14px text-zinc-500) + Değer (Roboto Mono 24px text-zinc-900) + Trend İndikatörü (Badge).

4.  **PropertyCard (İlan Kartı):**
    *   Görsel (Cover image) + Başlık (Poppins) + Fiyat (Roboto Mono, Orange) + Özellikler (Pill row: 3+1, 120m²).
    *   Aksiyonlar: Düzenle, Paylaş, PDF İndir.

5.  **Status Badge:**
    *   `bg-emerald-100 text-emerald-700` (Aktif/Satıldı).
    *   `bg-zinc-100 text-zinc-700` (Pasif/Taslak).
    *   `bg-amber-100 text-amber-700` (Bekliyor).

6.  **Skeleton Loader:**
    *   Veri yüklenirken layout kaymasını (CLS) önlemek için gri kutucuklar animasyonu.

---

## 4. Layout Sistemi

### 4.1 Desktop Dashboard (1024px+)

*   **Sol Sidebar (260px):**
    *   Logo alanı.
    *   Navigasyon (Dashboard, Portföy, Değerleme, CRM, Harita, Mesajlar).
    *   Alt kısım: Kullanıcı profili, Ayarlar, Çıkış.
    *   *Collapsible:* Daraltılabilir (sadece ikonlar).
*   **Üst Header (64px):**
    *   Global Arama (Command Palette `Cmd+K`).
    *   Bildirim Zili.
    *   Breadcrumb navigasyon.
*   **Main Content:**
    *   Maksimum genişlik ve ortalama (`max-w-7xl mx-auto`).
    *   Padding: `p-6` veya `p-8`.

### 4.2 Mobile & Telegram Mini App (<768px)

*   **Üst Header:**
    *   Sayfa Başlığı (Ortalı).
    *   Geri Butonu (Varsa).
    *   Aksiyon butonu (Sağ üst: "Kaydet", "Filtrele").
*   **Bottom Navigation Bar (56-64px):**
    *   4-5 Ana sekme: Ana Sayfa, Portföy, Ekle (+), CRM, Profil.
    *   Aktif ikon `orange-600`, pasif `zinc-400`.
*   **Telegram Entegrasyonu:**
    *   `Telegram WebApp` header rengi ile uyumlu status bar.
    *   Telegram `MainButton` (ekranın en altındaki büyük buton) form submit işlemleri için kullanılır.

### 4.3 Responsive Breakpoints

*   `sm`: 640px (Büyük telefonlar)
*   `md`: 768px (Tablet - Sidebar gizlenir, hamburger menu gelir)
*   `lg`: 1024px (Laptop - Sidebar görünür)
*   `xl`: 1280px (Desktop)
*   `2xl`: 1536px (Geniş Ekran)

---

## 5. Sayfa Bazlı UX Akışları

### 5.1 Onboarding & Login
1.  **Giriş Ekranı:** Telefon/Email + Şifre veya "Telegram ile Giriş".
2.  **Rol Seçimi (İlk kayıt):** "Ofis Sahibiyim" / "Danışmanım".
3.  **Hoşgeldin Turu:** Kritik özellikleri gösteren 3 adımlı modal (Değerleme yap, İlan ekle, CRM'e bak).

### 5.2 AI Değerleme (Core Feature)
1.  **Adres Girişi:** Google Places Autocomplete entegre input.
2.  **Detaylandırma:** Bina yaşı, kat, m² (Slider ve butonlarla hızlı seçim).
3.  **Analiz (Loading):** "Bölge taranıyor...", "Emsaller karşılaştırılıyor..." mesajlarıyla işlem hissi.
4.  **Sonuç Ekranı:**
    *   Tahmini Fiyat Aralığı (Büyük, Roboto Mono).
    *   Güven Skoru (Gauge chart).
    *   Harita üzerinde emsaller.
    *   CTA: "PDF İndir", "Portföye Ekle".

### 5.3 Portföy Yönetimi
1.  **Liste Görünümü:** Filtrelenebilir liste (Kart veya Tablo modu).
2.  **İlan Ekleme (Sihirbaz):** Adım adım form (Step 1: Temel, Step 2: Konum, Step 3: Foto, Step 4: AI Metin).
3.  **Detay Sayfası:** İlanın tüm verileri, istatistikleri (görüntülenme), eşleşen müşteriler listesi.

### 5.4 CRM & Eşleştirme
1.  **Müşteri Ekle:** İsim, İletişim, Talep (Konum, Bütçe, Tip).
2.  **Otomatik Eşleştirme:** Müşteri detayına girince "Bu müşteriye uygun 3 portföy bulundu" uyarısı.
3.  **Aksiyon:** Portföyü WhatsApp/Telegram ile gönder butonu.
    *   **WhatsApp buton davranışı (plan bazlı degrade):**
        - **Starter/Pro:** "WhatsApp'a Paylaş" → native WhatsApp / click-to-chat açar (`wa.me` linki). Uygulama içi delivery/read takibi **beklenmez** (capability yok).
        - **Elite:** "WhatsApp'tan Gönder" → uygulama içinden Cloud API ile template mesaj gönderir. Delivery/read statüsü webhook ile takip edilir (capability destekliyorsa gösterilir).
    *   **Mesaj statü gösterimi (capability-aware):**
        - UI'da `delivered` / `read` ikonları **sadece ilgili kanalın capability'si destekliyorsa** gösterilir.
        - Desteklenmiyorsa (Telegram, click-to-chat vb.) → statü alanı gizlenir, sadece `sent ✓` gösterilir.
        - "Read rate" KPI'ı sadece `supports_read=true` olan kanallarda hesaplanır; diğerlerinde N/A.

---

## 6. Wireframe Tanımları (Metin Bazlı)

### Ekran: Dashboard (Ana Sayfa)
```text
[Header: Arama | Bildirimler | Profil]
[Selamlama: "Merhaba Hakan, bugün piyasa hareketli!"]

[Grid: 2x2 Mobile, 4x1 Desktop]
- [Kart: Aktif İlanlar (12) ↗]
- [Kart: Potansiyel Müşteri (45) ↘]
- [Kart: Bu Ayki Satış (2) =]
- [Kart: Hedef Kalan (%80) ]

[Bölüm: Hızlı İşlemler]
( + Değerleme Yap ) ( + İlan Ekle ) ( + Müşteri Ekle ) ( Hesaplayıcı )

[Bölüm: Son Aktiviteler]
- [Avatar] Ahmet Bey ile görüşüldü (2s önce)
- [Ev İkonu] Kadıköy 3+1 ilanı yayına alındı (1g önce)
- [Rozet] EİDS doğrulaması tamamlandı (2g önce)
```

### Ekran: AI Değerleme Sonuç
```text
[Header: < Geri | Değerleme Raporu | Paylaş]

[Büyük Kart: Tahmini Değer]
   8.500.000 ₺ - 9.200.000 ₺
   [Ortalama: 8.850.000 ₺]
   (Güven Skoru: %88 - Yüksek)

[Grafik: Bölge Fiyat Trendi (Son 1 Yıl)]
   [Line Chart: Yukarı yönlü]

[Harita Preview]
   [Pin: Hedef Mülk]
   [Pin: Emsal 1 (8.4M)]
   [Pin: Emsal 2 (9.0M)]

[Liste: Benzer Emsaller]
1. Kadıköy, Caferağa, 3+1, 110m² - 8.4M ₺ (Satıldı)
2. Kadıköy, Moda, 3+1, 105m² - 9.5M ₺ (İlanda)

[Sticky Footer Button (Mobile)]
[ PDF Rapor Oluştur ]
```

### Ekran: İlan Detay & AI Asistan
```text
[Header: < Geri | İlan #12345 | Düzenle]

[Fotoğraf Galerisi (Swipeable / Grid)]

[Başlık: Kadıköy Merkezde Yenilenmiş 3+1 Fırsat Daire]
[Fiyat: 12.500.000 ₺] [Konum: Osmanağa Mah.]

[Özellikler Grid]
[3+1] [120 m²] [3. Kat] [Kombi]

[AI Asistanı Kutusu ✨]
"Bu ilan için açıklama metni önerisi:"
(Metin alanı: "Kadıköy'ün kalbinde, metroya 5dk mesafede...")
[ Buton: Metni Kopyala ] [ Buton: Yeniden Yaz (Kurumsal/Samimi) ]

[Tab: Eşleşen Müşteriler (3)]
- Ayşe Yılmaz (%95 Uyum) [Whatsapp] [Ara]
- Mehmet Demir (%80 Uyum) [Whatsapp] [Ara]
```

---

## 7. Interaction Patterns

*   **Form Validation:** Kullanıcı yazarken (onBlur veya onChange) Zod şeması ile kontrol. Hatalar input altında kırmızı metinle: "Geçerli bir telefon numarası giriniz."
*   **Toast Notifications:** İşlem sonuçları için sağ alt (desktop) veya üst orta (mobile) bildirimler.
    *   Başarılı: "İlan kaydedildi." (Yeşil ikon)
    *   Hata: "Bağlantı hatası, tekrar deneyin." (Kırmızı ikon)
*   **Modals vs Drawers:**
    *   Desktop: Ortalanmış Modallar (Dialog).
    *   Mobile: Alttan açılan paneller (Drawer / Bottom Sheet). Bu parmak erişimi için daha ergonomiktir.
*   **Empty States:** Boş listeler (İlan yok, Müşteri yok) için illüstrasyon + açıklama + CTA butonu ("Henüz ilanınız yok, ilk ilanınızı ekleyin").

---

## 8. Accessibility (Erişilebilirlik)

*   **Kontrast:** Tüm metinler WCAG AA (4.5:1) standardını sağlamalıdır. `orange-500` beyaz üzerinde yetersiz kalabilir, bu yüzden metinlerde `orange-600` veya daha koyusu kullanılacaktır.
*   **Klavye Navigasyonu:** Tüm interaktif elemanlar (buton, input, link) `Tab` ile gezilebilir olmalıdır. Focus durumunda `ring` efekti belirgin olmalıdır.
*   **Screen Readers:** İkon butonlarında mutlaka `aria-label` bulunmalıdır (örn: `<button aria-label="Düzenle"><EditIcon /></button>`).
*   **Türkçe Karakter:** Input alanlarında ve aramalarda Türkçe karakter (ı/i, ğ/g, ş/s) duyarlılığı ve normalizasyonu sağlanmalıdır.
*   **Touch Targets:** Mobilde tıklanabilir alanlar minimum 44x44px olmalıdır.

---

## 9. Mobile ve Telegram Mini App Stratejisi

### PWA (Progressive Web App)
*   `manifest.json` ile "Ana Ekrana Ekle" özelliği.
*   Offline destek: Statik assetler ve son gezilen sayfalar cache'lenir.
*   Kamera erişimi: İlan fotoğrafı çekmek için native input entegrasyonu.

### Telegram Mini App (TMA) Özel UX
*   **Telegram Theme Params:** Uygulama renkleri, Telegram kullanıcısının temasına (Dark/Light) otomatik uyum sağlar.
    *   `bg-color` -> `var(--tg-theme-bg-color)`
    *   `text-color` -> `var(--tg-theme-text-color)`
    *   `button-color` -> `var(--tg-theme-button-color)`
*   **MainButton:** Formların "Kaydet" veya "Gönder" aksiyonları için Telegram'ın native `MainButton` bileşeni kullanılır. Bu klavyenin üzerinde sabit kalır ve native hissettirir.
*   **BackButton:** Alt sayfalarda Telegram'ın sol üst köşedeki native geri butonu aktifleştirilir.
*   **Haptic Feedback:** Başarılı işlemlerde veya seçimlerde titreşim geri bildirimi verilir.

---
**Onay:** UI/UX Strateji Tasarımcısı (Gemini)
