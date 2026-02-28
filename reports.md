# Emlak Teknoloji Platformu - Calisma Raporlari

---

## [RAPOR-006] Harita Sayfasi Mock → Real API + Mock Dosya Temizligi (TASK-181)
| Alan | Deger |
|------|-------|
| **Durum** | TAMAMLANDI |
| **Baslangic** | 2026-02-28 |
| **Bitis** | 2026-02-28 |
| **Etkilenen Dosyalar** | app/(dashboard)/maps/page.tsx |

### Hedef
Maps sayfasindaki mock property verilerini gercek backend GeoJSON API'ye baglamak ve kullanilmayan mock dosyalarini temizlemek.

### Yapilanlar
- [x] `maps/page.tsx`: mockProperties import + generateMapProperties() fonksiyonu kaldirildi
- [x] React Query ile `GET /maps/properties?bbox=28.5,40.7,29.5,41.3&limit=200` endpoint'ine baglandi
- [x] GeoJSON FeatureCollection → PropertyMarkerLayer Property donusumu yapildi (coordinates[1]=lat, coordinates[0]=lon)
- [x] GeoJSON tip interface'leri tanimlandi (GeoJSONResponse, GeoJSONFeature, GeoJSONFeatureProperties)
- [x] Loading overlay (spinner + "Ilanlar yukleniyor...") ve error overlay (AlertCircle + "Ilanlar yuklenemedi") eklendi
- [x] staleTime: 2dk, gcTime: 5dk (gcTime >= staleTime kurali)
- [x] DISTRICT_COORDINATES sabiti korundu (gelecekteki bbox filtreleme icin)
- [x] Mock dosya temizligi: shared-showcases.ts zaten onceki TASK'ta silinmis. properties.ts hala showcase-form.tsx ve lib/api/showcases.ts tarafindan kullaniliyor — silinemez
- [x] pnpm build 0 hata ile tamamlandi

### Kararlar ve Notlar
- PropertyMarkerLayer Property interface'ine dokunulmadi (gorev kisitlamasi)
- GeoJSON coordinates [lon, lat] → Property {lat, lon} donusumu dikkatli yapildi
- `useMemo(() => generateMapProperties(), [])` yerine React Query `data` kullanildi — cache + stale management ucretsiz geldi

### Sonuc
9/10 frontend hook gercek API'ye baglandi. Kalan mock: showcase-form.tsx (properties.ts), lib/api/showcases.ts (properties.ts + showcases mock kullaniyor — ayri TASK olarak planlandi).

---

## [RAPOR-005] Showcases Mock → Gercek API Entegrasyonu (TASK-180)
| Alan | Deger |
|------|-------|
| **Durum** | TAMAMLANDI |
| **Baslangic** | 2026-02-28 |
| **Bitis** | 2026-02-28 |
| **Etkilenen Dosyalar** | lib/api/showcases.ts, components/network/showcase-form.tsx, app/(dashboard)/network/[id]/edit/page.tsx, lib/mock/showcases.ts (SILINDI), lib/mock/shared-showcases.ts (SILINDI) |

### Hedef
Showcases public API (fetchShowcaseBySlug, incrementShowcaseViews) ve showcase-form property listesini mock veriden gercek backend API'ye baglamak. Edit sayfasini da useShowcaseDetail hook ile entegre etmek.

### Yapilanlar
- [x] `lib/api/showcases.ts` tamamen yeniden yazildi:
  - fetchShowcaseBySlug → api.get('/showcases/public/{slug}') (PUBLIC, JWT gereksiz)
  - incrementShowcaseViews → api.post('/showcases/public/{slug}/view', {})
  - Backend ShowcasePublicResponse → frontend ShowcaseWithProperties mapping (PropertySummary → Property, theme string → ShowcaseTheme, duz agent_* alanlari → ShowcaseAgent nesnesi)
  - 404 → null donusu, view increment hatasi sessizce loglanir
- [x] `components/network/showcase-form.tsx` yeniden yazildi:
  - mockProperties import'u kaldirildi
  - useQuery ile api.get('/properties/search?limit=100&per_page=100') — ofis ilanlari gercek API'den
  - Loading state: 6 skeleton card animasyonu
  - Empty state: "Henuz ilan bulunamadi" mesaji
  - handleSubmit: mock delay → gercek api.post/api.put showcases CRUD
  - Error handling eklendi (toast mesaji)
- [x] `network/[id]/edit/page.tsx`: Server Component → Client Component'e donusturuldu
  - mockShowcases import'u → useShowcaseDetail(params.id) hook'u
  - Loading spinner, error/notFound yonetimi eklendi
  - React 19 use() ile async params cozumu
- [x] lib/mock/showcases.ts SILINDI (artik hicbir import yok)
- [x] lib/mock/shared-showcases.ts SILINDI (artik hicbir import yok)
- [x] lib/mock/properties.ts KORUNDU (paralel TASK-181 bagimliligi)
- [x] tsc --noEmit 0 hata, pnpm build derleme/lint/static page generation basarili

### Kararlar ve Notlar
- Backend ShowcasePublicResponse'da agent name yok (sadece phone/email/whatsapp/photo_url). Frontend agent.name bos string olarak set edildi.
- Backend theme string ("modern", "classic", "minimal") → Frontend ShowcaseTheme objesi donusumu mapTheme fonksiyonu ile yapildi.
- Backend PropertySummary listing_type "sale"/"rent" → Frontend "satilik"/"kiralik" donusumu her yerde tutarli.
- Edit sayfasi Server Component'ten Client Component'e donmek zorunda kaldi — useShowcaseDetail React hook kullaniyor, Server Component'te hook cagrilamaz.
- View increment try/catch ile sarildi — hata kullanici deneyimini bozmasin diye sessiz fail.

### Sonuc
Showcase public API, form property listesi ve edit sayfasi gercek API'ye bagli. 2 mock dosya silindi. Kalan mock: maps/page.tsx, lib/mock/properties.ts (TASK-181 bagimlisi).

---

## [RAPOR-004] Frontend 3 Hook Mock → Gercek API Entegrasyonu (TASK-178)
| Alan | Deger |
|------|-------|
| **Durum** | TAMAMLANDI |
| **Baslangic** | 2026-02-28 |
| **Bitis** | 2026-02-28 |
| **Etkilenen Dosyalar** | hooks/use-calculator.ts, hooks/use-customer-detail.ts, hooks/use-search.ts, lib/mock/bank-rates.ts (SILINDI), lib/mock/customers.ts (SILINDI), lib/mock/matches.ts (SILINDI), CLAUDE.md |

### Hedef
3 frontend hook'u mock veriden gercek backend API'ye baglamak: calculator, customer-detail, search.

### Yapilanlar
- [x] `hooks/use-calculator.ts`: mockBankRates → React Query + GET /calculator/rates. Backend annual_rate/12 → monthly_rate. staleTime 30dk.
- [x] `hooks/use-customer-detail.ts`: 3 paralel React Query (detail, notes, matches). note_type "note"→"general" mapping. useAddNote mutation eklendi.
- [x] `hooks/use-search.ts`: mockSearch/mockSuggestions/mockProperties ve API_URL fallback bloklari silindi. Her zaman API kullaniliyor.
- [x] 3 mock dosyasi silindi: bank-rates.ts, customers.ts, matches.ts
- [x] pnpm build 0 hata ile tamamlandi

### Kararlar ve Notlar
- Consumer dosyalarina dokunulmadi (zero-change consumer)
- Backend MatchResponse'da property nested objesi yok → UI optional chaining ile handle ediyor

### Sonuc
7/10 frontend hook gercek API'ye baglandi. Kalan mock: maps, showcase-form, network/edit.

---

## [RAPOR-003] Listings API Mock → Gercek Backend Entegrasyonu (TASK-179)
| Alan | Deger |
|------|-------|
| **Durum** | TAMAMLANDI |
| **Baslangic** | 2026-02-28 |
| **Bitis** | 2026-02-28 |
| **Etkilenen Dosyalar** | lib/api-client.ts, lib/api/listings.ts, hooks/use-listing-assistant.ts, hooks/use-virtual-staging.ts, mock/listings.ts (SILINDI) |

### Hedef
`lib/api/listings.ts` dosyasindaki tum mock metotlari gercek backend API endpoint'lerine cevirmek.

### Yapilanlar
- [x] Backend router/schema dosyalari okundu (listing_assistant_router.py, staging_router.py, portal_export_router.py + schemas)
- [x] `api-client.ts`'e `postFormData<T>()` metodu eklendi — multipart/form-data destegi (Content-Type header gonderilmez, browser boundary otomatik ekler)
- [x] `lib/api/listings.ts` tamamen yeniden yazildi:
  - `getAvailableTones()` → GET /api/v1/listings/tones (backend ToneInfo {name_tr, example_phrase} → frontend {label, iconName} mapping)
  - `generateListingText()` → POST /api/v1/listings/generate-text (backend snake_case response → frontend camelCase mapping)
  - `regenerateText()` → POST /api/v1/listings/regenerate-text (kota tuketmez, ton degisikligi icin)
  - `getStagingStyles()` → GET /api/v1/listings/staging-styles (backend {name_tr} → frontend {label, imageUrl} mapping, imageUrl frontend'te STYLE_IMAGE_MAP ile)
  - `virtualStage()` → POST /api/v1/listings/virtual-stage (multipart/form-data, base64 PNG → data URL donusumu)
  - `analyzeRoom()` → POST /api/v1/listings/analyze-room (multipart/form-data, oda analizi)
  - `exportToPortal()` → POST /api/v1/listings/export (portal format donusumu)
- [x] `hooks/use-listing-assistant.ts` guncellendi:
  - mockTones import'u kaldirildi
  - useState<ToneInfo[]>([]) + useEffect ile API'den yukleme
  - `regenerateText()` metodu eklendi (kota tuketmeyen yeniden uretim)
  - Hata yonetimi: kota asimi, OpenAI hatasi icin kullanici-dostu mesajlar
- [x] `hooks/use-virtual-staging.ts` guncellendi:
  - mockStyles import'u kaldirildi
  - useState<StyleInfo[]>([]) + useEffect ile API'den yukleme
  - `analyzeRoom()` metodu eklendi (sahneleme oncesi on-kontrol)
  - isAnalyzing, isLoadingStyles, roomAnalysis state'leri eklendi
  - Hata yonetimi: kota, bos olmayan oda, genel hata mesajlari
- [x] `mock/listings.ts` dosyasi SILINDI (artik hicbir dosyadan import edilmiyor)
- [x] pnpm build basarili: 0 TypeScript hatasi, 0 lint hatasi, 29 route uretildi

### Kararlar ve Notlar
- Backend ToneInfo'da `imageUrl`/`iconName` yok → Frontend'te TONE_ICON_MAP static mapping kullanildi
- Backend StyleInfo'da `imageUrl` yok → Frontend'te STYLE_IMAGE_MAP (Unsplash gorsellerle) static mapping kullanildi
- Backend StagingResponse base64 PNG listesi donduruyor → Frontend `data:image/png;base64,...` data URL'e ceviriyor
- ListingFormData'da `price` alani yok ama backend zorunlu → 0 fallback (backend prompt'ta fiyat bos kalacak)
- Backend kota/kredi sistemi kendi icinde yonetiyor → Frontend'te creditsUsed/creditsRemaining sadece UI uyumluluk icin

### Sonuc
6 mock metot gercek API'ye baglandi, 2 yeni metot eklendi (regenerateText, analyzeRoom). Mock dosyasi temizlendi. Build basarili.

---

## [RAPOR-002] Frontend 4 Ana Hook Mock → Gercek API Entegrasyonu
| Alan | Deger |
|------|-------|
| **Durum** | TAMAMLANDI |
| **Baslangic** | 2026-02-28 |
| **Bitis** | 2026-02-28 |
| **Etkilenen Dosyalar** | hooks/use-customers.ts, hooks/use-properties.ts, lib/api/valuations.ts, hooks/use-showcases.ts, hooks/use-shared-showcases.ts, app/(dashboard)/network/page.tsx, CLAUDE.md |

### Hedef
Web dashboard'daki 4 ana hook'u mock datadan gercek backend API endpoint'lerine baglamak.

### Yapilanlar
- [x] Mevcut hook dosyalari, API client, backend schema/router dosyalari ve referans (tg-api.ts) okundu
- [x] `hooks/use-customers.ts` yeniden yazildi:
  - useCustomers: React Query + api.get('/customers') — staleTime 2dk, gcTime 5dk
  - pipelineCounts: Her LeadStatus icin paralel count sorgusu (5 adet per_page=1)
  - useCustomerDetail, useCustomerNotes, useCreateCustomer, useUpdateCustomer, useUpdateLeadStatus, useAddCustomerNote mutation hook'lari eklendi
- [x] `hooks/use-properties.ts` yeniden yazildi:
  - Backend'de GET /properties endpoint'i yok, search endpoint kullanildi: GET /properties/search
  - ApiPropertyItem → Property mapping fonksiyonu (listing_type: sale→satilik, net_area→area_sqm)
  - useCreateProperty, useUpdateProperty, useDeleteProperty mutation'lari eklendi
- [x] `lib/api/valuations.ts` yeniden yazildi:
  - submitValuation: Form degerlerini backend request formatina donusturme (room_count "3+1"→3+1, floor string→int, building_age range→ortadeger, property_type→PascalCase)
  - Backend confidence 0-1 → frontend 0-100 donusumu
  - getValuations: offset-based pagination ile degerleme gecmisi
  - getValuationById: 404 → null donusu
  - getQuotaStatus: Backend'de dedicated endpoint yok, fallback mantigi
- [x] `hooks/use-showcases.ts` yeniden yazildi:
  - ShowcaseListItem → Showcase mapping (liste endpoint ozet dondurur)
  - useCreateShowcase, useUpdateShowcase, useDeleteShowcase mutation'lari
- [x] `hooks/use-shared-showcases.ts` yeniden yazildi:
  - SharedShowcase tipi hook dosyasina tasinarak export edildi (mock dosyasindan bagimsiz)
  - React Query ile api.get('/showcases/shared')
- [x] `network/page.tsx`: SharedShowcase import'u mock → hook dosyasina yonlendirildi
- [x] pnpm build BASARILI (0 hata, sadece onceden mevcut uyarilar)

### Kararlar ve Notlar
- **Properties endpoint:** Backend'de ayri bir GET /properties listesi yok, sadece /properties/search var. Search endpoint kullanildi, `q` parametresi ile arama yapiliyor.
- **Pipeline counts:** Tek sorguda tum status'lerin sayisini alacak endpoint yok. 5 paralel count sorgusu ile cozuldu (per_page=1, sadece total alinir).
- **Valuation field mapping:** Backend `confidence` 0-1 araligi, frontend 0-100 bekliyor. `prediction_id` → `id`, `predicted_price` → `estimated_price` gibi donusumler yapildi.
- **Kota durumu:** Backend'de dedicated quota endpoint yok. Degerleme sayisindan fallback hesaplama yapildi.
- **Mock dosyalari silinmedi** — diger hook'lar (use-customer-detail, use-search, maps, calculator) hala kullandigi icin referans olarak kaldi.
- **SharedShowcase tipi** `use-shared-showcases.ts` icine tasinarak mock dosya bagimliligi kesildi.

### Sonuc
4 ana hook gercek API'ye bagli. Build basarili. Kalan mock hook'lar: use-customer-detail.ts, use-search.ts, maps/page.tsx, showcase-form.tsx, network/[id]/edit/page.tsx.

---

## [RAPOR-001] Demo Hesap + Seed Data Script Olusturma
| Alan | Deger |
|------|-------|
| **Durum** | TAMAMLANDI |
| **Baslangic** | 2026-02-28 |
| **Bitis** | 2026-02-28 |
| **Etkilenen Dosyalar** | apps/api/scripts/__init__.py, apps/api/scripts/seed_demo.py |

### Hedef
Sunucu veritabaninda demo hesap, Elite plan abonelik ve seed data (musteri, ilan, vitrin, kota) olusturacak idempotent Python script yazmak.

### Yapilanlar
- [x] Model dosyalari okundu (office, user, subscription, property, customer, showcase, usage_quota)
- [x] apps/api/scripts/ klasoru olusturuldu
- [x] scripts/__init__.py eklendi
- [x] scripts/seed_demo.py yazildi — 7 adimli seed:
  - Ofis (PetQas Demo Emlak, Kadikoy)
  - Kullanici (demo@petqas.com / Demo2026!, office_admin)
  - Elite abonelik (active, 2027 sonuna kadar)
  - 10 musteri (gercekci Turk isimleri, farkli tipler ve durumlar)
  - 15 ilan (5 daire + 4 villa + 3 ofis + 2 arsa + 1 dukkan)
  - 2 vitrin (her biri 3-5 property ile)
  - Kullanim kotasi (Elite: 9999 degerleme/ay)
- [x] UUID format dogrulamasi yapildi (31 UUID)
- [x] Syntax ve import kontrolu gecti
- [x] Idempotentlik analizi: ON CONFLICT (id) DO UPDATE ile tekrar calistirmaya uygun

### Kararlar ve Notlar
- psycopg2 direkt kullanildi (lightweight, SQLAlchemy gereksiz)
- Bcrypt hash runtime'da uretiliyor (her calistirmada yeni hash ama ayni sifre)
- RLS bypass icin SET LOCAL app.current_user_role = 'platform_admin' kullanildi
- UUID'ler deterministik (sabit) secildi — idempotent calisma icin
- Property location PostGIS EWKT formati kullanildi: SRID=4326;POINT(lon lat)

### Sonuc
Script hazir. Sunucuya rsync ile gonderilip calistirilabilir:
```bash
cd /var/www/petqas/apps/api
source .venv/bin/activate
python3 -m scripts.seed_demo
```
