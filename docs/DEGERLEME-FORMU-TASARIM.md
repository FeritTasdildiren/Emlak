# AI Degerleme Formu - Tasarim Spesifikasyonu

**Tarih:** 2026-02-21
**Versiyon:** 1.0
**Durum:** Hazir
**Referans:** docs/UI-UX-TASARIM.md

---

## 1. Layout Kararlari

### Genel Yaklasim

Tek sayfa form yaklasimi kullanilir. Kullanici scroll ederek tum alanlari doldurur ve sonucu ayni sayfada gorur. Adim bazli (wizard) yaklasim yerine tek sayfa tercih edilmistir; cunku alan sayisi makul seviyededir ve kullanici formu hizla tarayabilir.

### Responsive Layout

| Breakpoint | Layout | Aciklama |
| :--- | :--- | :--- |
| **Mobile** (<768px) | Tek kolon | Tum form alanlari alt alta, sonuc karti formun altinda |
| **Tablet** (768px-1023px) | 2 kolon grid | Kisa alanlar (m2, kat, banyo) yan yana, sonuc karti formun altinda |
| **Desktop** (1024px+) | Sol form + Sag sonuc karti | Form sol tarafta (~60%), sonuc karti sagda sticky (~40%) |

### Desktop 2 Panel Layout

```
+------------------------------------------+---------------------+
| Form (sol panel)                         | Sonuc Karti (sag)   |
|                                          |                     |
| [Konum Bilgileri]                        | sticky top-24       |
| Il / Ilce / Mahalle                      |                     |
|                                          | Tahmini Deger       |
| [Mulk Ozellikleri]                       | Min - Ort - Max     |
| Mulk Tipi / m2 / Oda / Kat / Yas        | m2 birim fiyat      |
|                                          | Guven Skoru         |
| [Ek Ozellikler]                          | Emsal Mulkler       |
| Banyo / Balkon / Otopark / Asansor       |                     |
| Isitma / Cephe                           | [PDF Indir]         |
|                                          | [Yeni Degerleme]    |
| [ Degerleme Yap ]                        |                     |
+------------------------------------------+---------------------+
```

---

## 2. Renk Paleti

Mevcut tasarim sistemiyle (UI-UX-TASARIM.md) uyumlu. Marka rengi **Turuncu**.

| Rol | Tailwind Class | HEX | Kullanim |
| :--- | :--- | :--- | :--- |
| Primary | `orange-600` | `#EA580C` | Submit butonu, aktif segmented, focus ring |
| Primary Hover | `orange-700` | `#C2410C` | Buton hover |
| Secondary | `zinc-900` | `#18181B` | Basliklar, section label |
| Background | `zinc-50` | `#FAFAFA` | Sayfa zemini |
| Surface | `white` | `#FFFFFF` | Form karti, sonuc karti |
| Border | `zinc-200` | `#E4E4E7` | Input border, kart border |
| Success | `emerald-600` | `#059669` | Guven skoru (yuksek) |
| Warning | `amber-500` | `#F59E0B` | Guven skoru (orta) |
| Danger | `red-600` | `#DC2626` | Hata, validasyon |
| Info | `blue-600` | `#2563EB` | Bilgilendirme |

### Dark Mode Renkleri

| Rol | Dark Tailwind Class |
| :--- | :--- |
| Background | `dark:bg-zinc-950` |
| Surface | `dark:bg-zinc-900` |
| Border | `dark:border-zinc-700` |
| Text Primary | `dark:text-zinc-100` |
| Text Secondary | `dark:text-zinc-400` |

---

## 3. Tipografi

| Element | Font | Size | Weight | Tailwind Class |
| :--- | :--- | :--- | :--- | :--- |
| Sayfa Basligi (H1) | Poppins | 24px | Bold (700) | `text-2xl font-bold` |
| Section Basligi (H2) | Poppins | 18px | SemiBold (600) | `text-lg font-semibold` |
| Form Label | Inter | 14px | Medium (500) | `text-sm font-medium` |
| Body Text | Inter | 16px | Regular (400) | `text-base` |
| Helper Text | Inter | 12px | Regular (400) | `text-xs text-zinc-500` |
| Fiyat (Buyuk) | Roboto Mono | 32px | Bold (700) | `text-3xl font-bold font-mono` |
| Fiyat (Normal) | Roboto Mono | 16px | Medium (500) | `text-base font-medium font-mono` |
| Badge / Chip | Inter | 12px | SemiBold (600) | `text-xs font-semibold` |

---

## 4. Spacing Sistemi

4px grid tabanli. Tailwind standart spacing scale kullanilir.

| Token | Deger | Tailwind | Kullanim |
| :--- | :--- | :--- | :--- |
| space-1 | 4px | `p-1`, `gap-1` | Ikon ile metin arasi |
| space-2 | 8px | `p-2`, `gap-2` | Input ic padding, chip arasi |
| space-3 | 12px | `p-3`, `gap-3` | Kart ic padding (mobile) |
| space-4 | 16px | `p-4`, `gap-4` | Section arasi, form grup arasi |
| space-6 | 24px | `p-6`, `gap-6` | Kart ic padding (desktop), section arasi |
| space-8 | 32px | `p-8`, `gap-8` | Sayfa padding, buyuk bosluklar |

---

## 5. Form Section Gruplama

Form 3 ana section icinde gruplanir. Her section gorunur baslik ve ayirici ile belirtilir.

### Section 1: Konum Bilgileri
- Il (select)
- Ilce (select)
- Mahalle (select)

### Section 2: Mulk Ozellikleri
- Mulk Tipi (segmented button group)
- Brut m2 (number input + suffix)
- Net m2 (number input + suffix)
- Oda+Salon (segmented button group)
- Kat (select)
- Bina Yasi (segmented button group)

### Section 3: Ek Ozellikler
- Banyo Sayisi (segmented button group)
- Balkon (toggle switch)
- Otopark (radio group)
- Asansor (toggle switch)
- Isitma Tipi (select)
- Cephe Yonu (multi-select chips)

---

## 6. Sonuc Karti Layout

```
+-----------------------------------+
| Degerleme Sonucu                  |
+-----------------------------------+
|                                   |
|  Tahmini Deger                    |
|  [------|========|------]         |
|  2.1M      2.45M      2.8M       |
|                                   |
|      2.450.000 TL                 |
|      (buyuk, vurgulu)             |
|                                   |
|  m2 Birim Fiyat: 45.370 TL/m2    |
|                                   |
|  Guven Skoru  [ %78 ]            |
|               (yesil badge)       |
|                                   |
+-----------------------------------+
|  Emsal Mulkler                    |
|  1. Kadikoy 120m2 2.38M %92      |
|  2. Besiktas 115m2 2.52M %88     |
|  3. Uskudar 125m2 2.31M %85      |
+-----------------------------------+
|  [Detayli Rapor Indir (PDF)]      |
|  [Yeni Degerleme]                 |
+-----------------------------------+
```

---

## 7. Responsive Breakpoints

| Breakpoint | Piksel | Tailwind Prefix | Aciklama |
| :--- | :--- | :--- | :--- |
| Base | 0-639px | (default) | Kucuk telefon, TMA |
| sm | 640px | `sm:` | Buyuk telefon |
| md | 768px | `md:` | Tablet - 2 kolon grid baslar |
| lg | 1024px | `lg:` | Laptop - 2 panel layout (form + sonuc) |
| xl | 1440px | `xl:` | Genis ekran |

---

## 8. Interaction States

### Input / Select
| State | Gorunum |
| :--- | :--- |
| Default | `border-zinc-200 bg-white` |
| Hover | `border-zinc-300` |
| Focus | `border-orange-600 ring-2 ring-orange-600/20` |
| Error | `border-red-500 ring-2 ring-red-500/20` |
| Disabled | `bg-zinc-100 opacity-50 cursor-not-allowed` |

### Segmented Button
| State | Gorunum |
| :--- | :--- |
| Default | `bg-zinc-100 text-zinc-700` |
| Hover | `bg-zinc-200` |
| Selected | `bg-orange-600 text-white shadow-sm` |
| Focus | `ring-2 ring-orange-600/20` |

### Toggle Switch
| State | Gorunum |
| :--- | :--- |
| Off | `bg-zinc-300` (track), `bg-white` (thumb) |
| On | `bg-orange-600` (track), `bg-white` (thumb) |
| Disabled | `opacity-50` |

### Submit Button
| State | Gorunum |
| :--- | :--- |
| Default | `bg-orange-600 text-white` |
| Hover | `bg-orange-700` |
| Loading | `bg-orange-600 opacity-75` + spinner |
| Disabled | `bg-orange-600 opacity-50 cursor-not-allowed` |

### Multi-Select Chips (Cephe)
| State | Gorunum |
| :--- | :--- |
| Default | `border border-zinc-200 bg-white text-zinc-700` |
| Hover | `border-zinc-300 bg-zinc-50` |
| Selected | `border-orange-600 bg-orange-50 text-orange-700` |

---

## 9. Bilesen Listesi

| Bilesen | Dosya | Aciklama |
| :--- | :--- | :--- |
| `ValuationForm` | `components/valuation/ValuationForm.tsx` | Ana form bileseni |
| `ValuationResult` | `components/valuation/ValuationResult.tsx` | Sonuc karti bileseni |

Mevcut UI bilesenlerinden `Button`, `Select`, `NumberInput`, `Card` kullanilir.
Ek olarak `SegmentedControl`, `Toggle`, `ChipSelect` gibi form kontrolleri form icinde tanimlanir.

---

**Onay:** AI Tasarim Spesifikasyonu
