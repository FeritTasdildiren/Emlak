# TASK-152: Responsive / Browser Statik Analiz Test Raporu

**Tarih:** 2026-02-26
**Yontem:** Kaynak kodu statik analizi (Tailwind class, JSX yapisi, link href, runtime guvenlik)
**Kapsam:** `apps/web/src/app/` altindaki (dashboard)/*, tg/*, (auth)/* + paylasilan bilesenler
**Toplam Analiz Edilen Dosya:** 53 dosya (24 dashboard, 16 tg, 13 auth+root+layout+shared)

---

## Ozet Skor Tablosu

| Bolum | Dosya Sayisi | CRITICAL | WARNING | INFO | Responsive Puani |
|-------|-------------|----------|---------|------|-----------------|
| (auth)/* | 3 | 4 | 2 | 3 | 3/10 |
| (dashboard)/* | 24 | 12 | 22 | 15+ | 6/10 |
| tg/* | 16 | 1 | 14 | 14 | 8/10 |
| Layout/Shared | 10 | 5 | 12 | 8 | 5/10 |
| **TOPLAM** | **53** | **22** | **50** | **40+** | **5.5/10** |

> **Responsive Puani:** 10 = mukemmel mobil uyum, 0 = hic responsive degil

---

## Kritik Sorunlar Ozeti (CRITICAL - 22 adet)

### C1. Sistematik Kirik Link Sorunu — `/dashboard/` Prefix Hatasi
**Etki:** 11+ link, 8 dosya
**Aciklama:** `(dashboard)` bir Next.js route group'tur ve URL'de gorunmez. Ancak pek cok sayfada linkler `/dashboard/areas`, `/dashboard/network`, `/dashboard/properties` olarak yazilmis. Dogru path'ler `/areas`, `/network`, `/properties` olmali.

| Dosya | Satir | Yanlis Path | Dogru Path |
|-------|-------|-------------|------------|
| `areas/page.tsx` | 49 | `/dashboard/areas?...` | `/areas?...` |
| `areas/page.tsx` | 128 | `/dashboard/areas/compare?...` | `/areas/compare?...` |
| `areas/compare/page.tsx` | 65, 122 | `/dashboard/areas/compare?...`, `/dashboard/areas` | `/areas/compare?...`, `/areas` |
| `maps/page.tsx` | 199, 248 | `/dashboard/areas?...` | `/areas?...` |
| `network/page.tsx` | 97, 137, 356 | `/dashboard/network/.../edit`, `/dashboard/network/create` | `/network/.../edit`, `/network/create` |
| `network/create/page.tsx` | 18 | `/dashboard/network` | `/network` |
| `network/[id]/edit/page.tsx` | 27 | `/dashboard/network` | `/network` |
| `properties/page.tsx` | 201, 498 | `/dashboard/properties/new` | `/properties/new` |
| `properties/new/page.tsx` | 13 | `/dashboard/properties` | `/properties` |

> **Not:** `(dashboard)/dashboard/customers/` alt dizini ozel bir durumdur — burada `/dashboard/customers` path'i DOGRUDIR cunku `dashboard/` klasoru route group'un icinde fiziksel olarak vardir.

### C2. Eksik Route — `/dashboard/customers/new` (404)
**Dosya:** `dashboard/customers/page.tsx` satir 61
**Aciklama:** "Yeni Musteri" butonu `/dashboard/customers/new` adresine yonlendirir ancak bu route mevcut degil.

### C3. Eksik Route — `/tg/settings` (404)
**Dosya:** `tg/components/tg-bottom-nav.tsx` satir 26
**Aciklama:** Bottom navigation'da "Ayarlar" sekme linki `/tg/settings`'e gider ancak bu route mevcut degil.

### C4. Login/Register Formlari Calismaz
**Dosyalar:** `login/page.tsx` satir 18, `register/page.tsx` satir 18
**Aciklama:** Her iki form da `action="#" method="POST"` kullaniyor, `onSubmit` handler yok. Form submit edildiginde sayfa `#`'a navigate eder — formlar tamamen non-functional.

### C5. Register Sayfasi — Mobil Grid Kirilmasi
**Dosya:** `register/page.tsx` satir 19
**Aciklama:** Ad/Soyad alanlari `grid grid-cols-2` ile yan yana. 375px ekranda her sutun ~131px genisliginde — input alanlari icin cok dar. `grid-cols-1 sm:grid-cols-2` olmali.

### C6. Landing Page — CTA Butonlari Overflow
**Dosya:** `page.tsx` (root) satir 32-39
**Aciklama:** Iki buyuk buton (`size="lg" className="px-8"`) `flex gap-4` icerisinde yan yana. 375px ekranda tasma garanti. `flex-col sm:flex-row` olmali.

### C7. Mobile Nav — 7 Sayfa Erisilemez
**Dosya:** `mobile-nav.tsx` satir 25-30
**Aciklama:** Sidebar'da 11 navigasyon ogesi var, mobile nav'da sadece 4 (Dashboard, Mulkler, Ilan Asistani, Musteriler). Degerleme, Bolge Analizi, Mesajlar, Harita, Ag, Kredi, Ayarlar sayfalarina mobilde erisilemez.

### C8. Harita Sayfasi — Sidebar/Bottom Sheet Cakismasi
**Dosya:** `maps/page.tsx` satir 131-135, 218-254
**Aciklama:** Mobilde sidebar `w-full` acilirken, ayni anda `md:hidden` bottom sheet de render ediliyor. Iki panel ust uste biner.

### C9. Dashboard Ana Sayfa — `col-span-4` Grid Overflow
**Dosya:** `(dashboard)/page.tsx` satir 64-71
**Aciklama:** `md:grid-cols-2` grid'de `col-span-4` kullanilmis. 4 sutunluk span, 2 sutunluk grid'den tasar.

### C10. Runtime Error — `toast()` Import Eksik (2 dosya)
**Dosyalar:**
- `properties/property-form.tsx` satir 197
- `valuation/ValuationResult.tsx` satir 144
**Aciklama:** `toast()` fonksiyonu cagirilmis ama import edilmemis. Runtime'da `ReferenceError` verir.

### C11. Runtime Error — `customer.desired_districts.slice()` Guard Eksik
**Dosya:** `customers/customer-table.tsx` satir 162
**Aciklama:** `desired_districts` undefined olabilir, optional chaining veya fallback yok. Runtime crash.

### C12. Tailwind Dynamic Class — Compile'da Kaybolur
**Dosya:** `valuation/ValuationResult.tsx` satir 276
**Aciklama:** `guven.text.split(' ')[0].replace('text-', 'bg-')` ile runtime'da Tailwind class olusturuluyor. JIT compiler bu class'i goremez, CSS'te bulunmaz. Renk gosterilmez.

### C13. ValuationHistory — Kirik Link
**Dosya:** `valuation/ValuationHistory.tsx` satir 99
**Aciklama:** Link href `/valuations/${item.id}` — route group nedeniyle bu 404 verir. Route yapisina gore dogru path belirlenmeli.

---

## Sayfa Bazli Detayli Analiz

### (AUTH) Sayfalari

#### `(auth)/layout.tsx`
- **Responsive:** `sm:px-6`, `lg:px-8` — minimal ama mevcut
- **WARNING:** `p-10` padding mobilde cok genis. 375px'te kullanilabilir alan sadece ~263px. `p-4 sm:p-6 lg:p-10` olmali.

#### `(auth)/login/page.tsx`
- **Responsive:** `sm:mx-auto sm:w-full sm:max-w-sm`
- **CRITICAL:** Form non-functional (action="#")
- **WARNING:** "Sifremi unuttum?" `<a href="#">` — dead link, `<Link>` veya `<button>` olmali
- Link `/register` — DOGRU

#### `(auth)/register/page.tsx`
- **Responsive:** `sm:mx-auto sm:w-full sm:max-w-sm`
- **CRITICAL:** Form non-functional (action="#")
- **CRITICAL:** `grid-cols-2` mobilde kirilir
- Link `/login` — DOGRU

---

### (DASHBOARD) Sayfalari

#### `(dashboard)/layout.tsx`
- **Responsive:** `md:p-6`, `lg:p-8` — iyi kademeli padding
- Sorun yok, temiz layout

#### `(dashboard)/page.tsx` (Ana Dashboard)
- **Responsive:** `md:grid-cols-2`, `lg:grid-cols-4`, `lg:grid-cols-7` — 4 breakpoint kullanimi
- **CRITICAL:** `col-span-4` ve `col-span-3` — `md:grid-cols-2` grid'de overflow
- **WARNING:** Baslik + timestamp satiri `flex justify-between` — 375px'te tasar

#### `(dashboard)/areas/page.tsx`
- **Responsive:** `sm:flex-row`, `sm:items-center`, `lg:grid-cols-3` — 5 breakpoint kullanimi
- **CRITICAL:** `/dashboard/areas?...` kirik link (x2)
- **WARNING:** `w-[180px]` sabit genislik Select, mobilde sorun potansiyeli
- **WARNING:** `trendData.trends.map()` — null check eksik

#### `(dashboard)/areas/compare/page.tsx`
- **Responsive:** `md:flex-row`, `md:grid-cols-3` — 3 breakpoint kullanimi
- **CRITICAL:** `/dashboard/areas/compare?...` kirik link (x2)
- **WARNING:** `area.rental_yield_annual_pct.toFixed(2)` — null/undefined crash potansiyeli

#### `(dashboard)/calculator/page.tsx`
- **Responsive:** `sm:grid-cols-2`, `lg:grid-cols-3`, `lg:grid-cols-12`, `lg:sticky` — 8 breakpoint kullanimi (en iyi)
- **WARNING:** `grid-cols-3` icindeki para degerleri mobilde tasar ("12.500.000,00 TL")
- **WARNING:** `result.bankComparisons` ve `result.amortization` — undefined guard eksik

#### `(dashboard)/customers/page.tsx`
- **Responsive:** 0 breakpoint kullanimi (placeholder sayfa)
- Sorun yok

#### `(dashboard)/dashboard/customers/page.tsx`
- **Responsive:** `sm:flex-row`, `sm:hidden`, `sm:flex` — 8+ breakpoint kullanimi (iyi)
- **CRITICAL:** `/dashboard/customers/new` route mevcut degil
- **WARNING:** Pagination tum butonlari render eder — cap/ellipsis yok

#### `(dashboard)/dashboard/customers/[id]/page.tsx`
- **Responsive:** `sm:px-6`, `lg:px-8`, `sm:flex`, `sm:flex-row` — 11+ breakpoint kullanimi (cok iyi)
- **WARNING:** `customer.tags.length` — optional chaining eksik
- **WARNING:** Tab container `space-x-8 px-6` — 375px'te 3 tab + icon overflow potansiyeli

#### `(dashboard)/listings/page.tsx`
- **Responsive:** `sm:px-6`, `lg:grid-cols-2` — 7 breakpoint kullanimi
- **WARNING:** Cift header (`sticky top-0` + layout header cakismasi)

#### `(dashboard)/listings/components/listing-text-form.tsx`
- **Responsive:** `sm:grid-cols-4`, `sm:grid-cols-2`, `sm:p-4` — 5 breakpoint kullanimi
- Sorun yok, iyi tasarim

#### `(dashboard)/listings/components/listing-text-result.tsx`
- **Responsive:** `sm:px-6`, `sm:text-xl`, `sm:inline`, `sm:hidden` — 9 breakpoint kullanimi
- **WARNING:** `max-h-[calc(100vh-300px)]` — cift header ile yanlis hesaplama

#### `(dashboard)/listings/components/portal-export-tab.tsx`
- **Responsive:** `sm:p-6`, `lg:grid-cols-12` — 6 breakpoint kullanimi
- Sorun yok

#### `(dashboard)/listings/components/virtual-staging-tab.tsx`
- **Responsive:** `sm:p-6`, `sm:flex-row`, `lg:grid-cols-12` — 12 breakpoint kullanimi (cok iyi)
- **WARNING:** `<img>` yerine Next.js `<Image>` kullanilmali (3 adet)
- **WARNING:** `sliderPosition` 0 oldugunda bolme hatasi (division by zero)
- Alt text: Tum `<img>` etiketlerinde `alt` MEVCUT

#### `(dashboard)/maps/page.tsx`
- **Responsive:** `md:w-96`, `md:w-[400px]`, `md:hidden` — 3 breakpoint kullanimi
- **CRITICAL:** Sidebar + bottom sheet mobilde ust uste biner
- **CRITICAL:** `/dashboard/areas?...` kirik link (x2)
- **WARNING:** `h-[calc(100vh-64px)]` — hardcoded header yuksekligi

#### `(dashboard)/messages/page.tsx`
- **Responsive:** 0 breakpoint kullanimi (placeholder)
- Sorun yok

#### `(dashboard)/network/page.tsx`
- **Responsive:** `md:grid-cols-2`, `lg:grid-cols-3` — 4 breakpoint kullanimi
- **CRITICAL:** `/dashboard/network/...` kirik linkler (x3)
- **WARNING:** `showcase.selected_properties.length` — optional chaining eksik

#### `(dashboard)/network/create/page.tsx`
- **Responsive:** 0 breakpoint kullanimi
- **CRITICAL:** `/dashboard/network` kirik link
- **WARNING:** `pl-10` mobilde fazla padding (viewport'un %10.7'si bos)

#### `(dashboard)/network/[id]/edit/page.tsx`
- **Responsive:** 0 breakpoint kullanimi
- **CRITICAL:** `/dashboard/network` kirik link
- **WARNING:** Uzun baslik truncate edilmiyor

#### `(dashboard)/properties/page.tsx`
- **Responsive:** `sm:flex-row`, `sm:grid-cols-2`, `lg:grid-cols-3`, `sm:table-cell`, `md:table-cell`, `lg:table-cell` — 15+ breakpoint kullanimi (en iyi)
- **CRITICAL:** `/dashboard/properties/new` kirik link
- Progressive column disclosure patterni — tablo sutunlari breakpoint'lere gore gizleniyor (MUKEMMEL)

#### `(dashboard)/properties/new/page.tsx`
- **Responsive:** 0 (PropertyForm'a devreder)
- **CRITICAL:** `/dashboard/properties` kirik link

#### `(dashboard)/settings/page.tsx`
- **Responsive:** 0 (placeholder)
- Sorun yok

#### `(dashboard)/valuations/page.tsx`
- **Responsive:** `sm:px-6`, `lg:px-8` — 2 breakpoint kullanimi
- **WARNING:** Baslik + TabsList `flex justify-between` — 375px'te overflow
- **WARNING:** Cift padding (layout + sayfa)

#### `(dashboard)/valuations/[id]/page.tsx`
- **Responsive:** `sm:px-6`, `lg:px-8`, `lg:grid-cols-3` — 5 breakpoint kullanimi
- **WARNING:** `valuation.comparables` null check eksik
- **WARNING:** Cift padding

---

### TG (Telegram Mini App) Sayfalari

> **Genel Degerlendirme:** tg/ tamamen mobil-first. Hicbir `sm:`, `md:`, `lg:`, `xl:` breakpoint kullanilmamis — bu bir Telegram Mini App icin DOGRU yaklasim.

#### `tg/layout.tsx` + `tg/layout-client.tsx`
- **WARNING:** `minWidth: 375` pixel hardcoded — split screen'de overflow
- **INFO:** `pb-20` bottom nav spacing — safe area ile yetersiz kalabilir

#### `tg/page.tsx` (Dashboard)
- Linkler: `/tg/crm` DOGRU, `/tg/valuation` DOGRU
- **WARNING:** Bos `full_name` icin `??` fallback calismaz (`""` nullish degil)
- **WARNING:** Ping badge 3+ haneli sayilarda overflow (`h-5 w-5` = 20x20px)
- **WARNING:** Kota toplami `30` hardcoded — backend degisirse yanlis gosterir

#### `tg/crm/page.tsx`
- **WARNING:** Sinirsiz tag render — cok tag olan kartlar asiri uzun olur
- **WARNING:** Budget input `type="text"` — sayisal klavye acilmaz, NaN risk
- **WARNING:** Bottom sheet safe-area padding eksik — iPhone'da buton gizlenebilir

#### `tg/valuation/page.tsx`
- **WARNING:** 28/38 ilce icin mahalle verisi yok — bos dropdown
- **WARNING:** Buyuk fiyat metni `text-3xl font-mono` — 375px'te overflow potansiyeli
- **WARNING:** PDF/Paylas butonlari non-functional — onClick handler yok, disabled gorunumu yok

#### `tg/components/tg-bottom-nav.tsx`
- **CRITICAL:** `/tg/settings` route mevcut degil — 404
- **WARNING:** Bottom nav yuksekligi + safe-area > layout `pb-20` — icerik gizlenebilir

#### `tg/components/tg-provider.tsx`
- **WARNING:** Error state'de retry butonu yok — kullanici takili kalir

#### `tg/hooks/use-tg-dashboard.ts`
- **WARNING:** `Promise.all` — tek API hatasi tum dashboard'u durdurur. `Promise.allSettled` olmali.

#### Diger tg/ dosyalari
- `segmented-control.tsx` — Temiz, `min-h-[44px]` touch target (iyi)
- `tg-auth-guard.tsx` — `max-w-sm` 375px'ten genis (mintor)
- `tg-card.tsx` — Temiz, sorun yok
- `tg-skeleton.tsx` — Temiz, sorun yok
- `use-tg-auth.ts` — JWT parse try/catch icinde (guvenli)
- `use-tg-customers.ts` — Sorun yok
- `use-tg-valuation.ts` — Sorun yok
- `tg-api.ts` — Sorun yok

---

### Paylasilan Bilesenler

#### `components/layout/sidebar.tsx`
- **Responsive:** `hidden lg:flex` — lg altinda tamamen gizli
- **WARNING:** Tablet (md-lg arasi) icin collapsed/icon-only mod yok
- **WARNING:** Hardcoded kullanici bilgisi ("John Doe", "Broker")

#### `components/layout/header.tsx`
- **Responsive:** `hidden md:block` (arama cubugu)
- **WARNING:** Mobilde arama alternatifi yok
- **WARNING:** Bildirim butonu `aria-label` eksik

#### `components/layout/mobile-nav.tsx`
- **Responsive:** `lg:hidden`
- **CRITICAL:** 7/11 navigasyon ogesi eksik
- **WARNING:** Focus trap yok, "x" butonu `aria-label` eksik

#### `components/ui/table.tsx`
- `overflow-auto` wrapper — mobilde yatay scroll icin DOGRU yaklasim

#### `components/customers/customer-table.tsx`
- **Responsive:** `hidden sm:block` — mobilde gizlenir, kart gorunumune gecer
- **CRITICAL:** `desired_districts.slice()` guard eksik
- **WARNING:** `getRelativeTime(undefined)` → "NaN yil once"

#### `components/customers/customer-form.tsx`
- **Responsive:** `sm:grid-cols-2`, `p-4 sm:p-6` — IYI responsive form
- `SegmentedControl` `flex-wrap` ile overflow handle — DOGRU

#### `components/properties/property-form.tsx`
- **Responsive:** `sm:grid-cols-2`, `sm:grid-cols-3` — IYI
- **CRITICAL:** `toast()` import eksik — ReferenceError

#### `components/properties/search-filters.tsx`
- **Responsive:** `sm:grid-cols-3`, `sm:flex-row` — IYI
- **WARNING:** SegmentedControl `inline-flex` — 5 buton mobilde overflow

#### `components/valuation/ValuationForm.tsx`
- **Responsive:** `sm:grid-cols-2`, `lg:flex`, `lg:sticky` — MUKEMMEL
- **WARNING:** `/pricing` route dogrulanmali

#### `components/valuation/ValuationResult.tsx`
- **CRITICAL:** `toast()` import eksik
- **CRITICAL:** Dynamic Tailwind class — compile'da kaybolur
- **WARNING:** Fiyat araligi etiketleri dar ekranda cakisir

#### `components/valuation/ValuationHistory.tsx`
- **CRITICAL:** `/valuations/${id}` kirik link
- **WARNING:** 5 sutunlu tablo mobilde sadece scroll ile gorunur

#### `components/valuation/ComparablesList.tsx`
- **Responsive:** `sm:flex-row sm:items-center` — IYI
- Sorun yok

#### `components/map/MapContainer.tsx`
- **WARNING:** `min-h-[400px]` tum ekranlarda — mobilde cok yuksek
- `w-full h-full` — parent'a uyum saglar

#### `components/map/AreaAnalysisCard.tsx`
- **Responsive:** `md:grid-cols-2` — IYI
- **WARNING:** `investment.roi` icin `&&` falsy check — `0` degeri gizlenir
- **WARNING:** `font-inter` class Tailwind config ile eslesmeyebilir

---

## Gorsel/Alt Text Denetimi

| Bolum | `<img>` Sayisi | Alt Text Durumu |
|-------|---------------|-----------------|
| Dashboard | 3 (virtual-staging-tab) | TUMU MEVCUT ("Preview", "Before", "After") |
| TG | 0 | Gorsel yok (sadece SVG ikonlar) |
| Auth | 0 | Gorsel yok |
| Shared | 0 | Gorsel yok |

> **Sonuc:** Alt text sorunu yok. Ancak `virtual-staging-tab.tsx`'teki `<img>` etiketleri Next.js `<Image>` ile degistirilmeli (optimizasyon icin).

---

## Responsive Kalip Analizi

### Iyi Kaliplar (Ornekler Icin)
1. **Progressive Column Disclosure:** `properties/page.tsx` — tablo sutunlari `hidden sm:table-cell`, `hidden md:table-cell`, `hidden lg:table-cell` ile kademeli gosteriliyor
2. **Mobil/Desktop Ayirimi:** `customer-table.tsx` `hidden sm:block` + `customer-card.tsx` `block sm:hidden`
3. **Pagination Ayirimi:** `dashboard/customers/page.tsx` — mobilde basitlestirilmis, desktopda tam pagination
4. **Responsive Button Text:** `listing-text-result.tsx` — `hidden sm:inline` / `sm:hidden` ile buton etiketleri adapte oluyor
5. **TG Mobil-First:** Tum tg/ modulu sifir breakpoint ile tamamen mobil tasarim

### Kotu Kaliplar (Duzeltilmeli)
1. **Hardcoded `/dashboard/` prefix:** 11+ link yanlis path kullaniyor
2. **`grid-cols-N` without responsive:** Register sayfasi, dashboard `col-span-4`
3. **`flex` without `flex-wrap`:** Landing page CTA, valuations header
4. **Fixed widths on mobile:** `w-[180px]`, `pl-10`, `min-h-[400px]`
5. **Double padding:** Layout padding + sayfa padding = fazla bosluk

---

## Oncelikli Aksiyon Plani

### Oncelik 1 — Hemen Duzelt (CRITICAL)
1. [ ] Tum `/dashboard/X` linklerini `/X` olarak duzelt (areas, network, properties, maps)
2. [ ] Login/Register form `onSubmit` handler ekle
3. [ ] Register `grid-cols-2` → `grid-cols-1 sm:grid-cols-2`
4. [ ] Landing page CTA `flex` → `flex flex-col sm:flex-row`
5. [ ] Mobile nav'a eksik 7 navigasyon ogesini ekle
6. [ ] `toast()` import'larini ekle (property-form, ValuationResult)
7. [ ] `customer.desired_districts` optional chaining ekle
8. [ ] Maps sidebar'a `hidden md:block` ekle
9. [ ] `/tg/settings` route'unu olustur veya bottom nav'dan kaldir
10. [ ] `/dashboard/customers/new` route'unu olustur
11. [ ] ValuationResult dynamic Tailwind class'i safelist'e ekle veya statik yap
12. [ ] ValuationHistory link path'ini duzelt

### Oncelik 2 — Sprint Icinde Duzelt (WARNING)
1. [ ] Auth layout `p-10` → `p-4 sm:p-6 lg:p-10`
2. [ ] Dashboard page `col-span` → responsive col-span ekle
3. [ ] Valuations header `flex-wrap` ekle
4. [ ] Calculator para degerleri mobilde font kucultme
5. [ ] Sidebar tablet collapsed mode ekle
6. [ ] Header bell `aria-label` ekle
7. [ ] Mobile nav focus trap ekle
8. [ ] Maps `h-[calc(100vh-64px)]` → dinamik yap
9. [ ] TG bottom sheet safe-area padding ekle
10. [ ] TG PDF/Share butonlarina `disabled` state ekle
11. [ ] `Promise.all` → `Promise.allSettled` (tg dashboard hook)
12. [ ] Network edit title `truncate` ekle
13. [ ] Pagination ellipsis/cap ekle
14. [ ] Cift padding sorunlarini temizle (4 sayfa)

### Oncelik 3 — Iyilestirme (INFO)
1. [ ] `<img>` → `<Image>` (virtual staging)
2. [ ] `inputMode="numeric"` / `inputMode="tel"` ekle (tg formlari)
3. [ ] SVG ikonlara `aria-hidden="true"` ekle
4. [ ] Budget `formatBudget(!n)` → `formatBudget(n === null || n === undefined)`
5. [ ] MapContainer `min-h` responsive yap
6. [ ] AreaAnalysisCard `font-inter` class dogrula

---

## Istatistikler

| Metrik | Deger |
|--------|-------|
| Toplam analiz edilen dosya | 53 |
| Responsive breakpoint kullanan dosya | 28/53 (%53) |
| Hicbir breakpoint kullanmayan sayfa dosyasi | 12 (7'si placeholder/layout, 5'i sorunlu) |
| Kirik link (CRITICAL) | 15+ |
| Runtime error potansiyeli | 6 |
| Mobilde overflow riski | 8 |
| Accessibility sorunu | 5 |
| En iyi responsive: | `properties/page.tsx` (15+ breakpoint, progressive disclosure) |
| En kotu responsive: | `register/page.tsx` (grid kirilmasi + non-functional form) |
