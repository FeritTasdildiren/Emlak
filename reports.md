# Emlak Teknoloji Platformu - Calisma Raporlari

---

## [RAPOR-011] Vitrin Seed Genisleme + Ankara/Izmir Degerleme Verisi (TASK-194)
| Alan | Deger |
|------|-------|
| **Durum** | TAMAMLANDI |
| **Baslangic** | 2026-03-01 |
| **Bitis** | 2026-03-01 |
| **Etkilenen Dosyalar** | scripts/seed_showcases_expand.py (YENI), data/training/ankara_districts.json (YENI), data/training/izmir_districts.json (YENI), data/training/prepare_ankara_data.py (YENI), data/training/prepare_izmir_data.py (YENI), data/training/ankara_training_data.csv (YENI), data/training/izmir_training_data.csv (YENI) |

### Hedef
A) Mevcut 2 demo vitrini 8 yeni vitrinle genisletmek (toplam 10). B) Ankara (25 ilce) ve Izmir (29 ilce) icin LightGBM egitim verisi hazirlamak.

### Yapilanlar
- [x] seed_showcases_expand.py scripti olusturuldu — 8 yeni vitrin (farkli temalar: modern, classic, minimalist; farkli layout: grid, carousel)
- [x] Deterministik showcase UUID'leri (bb000001-...-000000000003 ile 010) ile idempotent ON CONFLICT (slug) DO UPDATE
- [x] seed_demo.py'deki OFFICE_ID ve USER_ID sabitleri kullanildi
- [x] ankara_districts.json olusturuldu — 25 ilce, gercekci fiyat/koordinat/deprem verisi
- [x] izmir_districts.json olusturuldu — 29 ilce (gorevde Konak tekrari vardi, 1'e dusuruldu)
- [x] prepare_ankara_data.py olusturuldu — Seed 43, Istanbul formati ile birebir ayni
- [x] prepare_izmir_data.py olusturuldu — Seed 44, Istanbul formati ile birebir ayni
- [x] ankara_training_data.csv uretildi — 2525 kayit, 25 ilce, Ort 2.38M TL
- [x] izmir_training_data.csv uretildi — 2967 kayit, 29 ilce, Ort 4.07M TL

### Kararlar ve Notlar
- Ankara fiyatlari Istanbul'un ~%60-70'i seviyesinde (Cankaya 78K vs Kadikoy 116K TL/m2)
- Izmir fiyatlari Istanbul'un ~%50-65'i (Cesme 85K en yuksek, turistik bolge primi)
- Ankara deprem riski tum ilceler "low" (PGA 0.05-0.13), Izmir "medium"/"high" (PGA 0.20-0.35)
- Isitma dagilimi sehre ozel: Ankara soguk iklim→dogalgaz %45, Izmir Ege→klima %12
- Konak gorevde 2 kez listelenmisti, tekrar cikarildi (29 benzersiz ilce)

### Sonuc
7 yeni dosya olusturuldu. Istanbul (3749) + Ankara (2525) + Izmir (2967) = toplam ~9241 egitim kaydı. Vitrin sayisi 2'den 10'a yukseltildi.

---

## [RAPOR-010] Banka Faiz Toplama Sistemi (TASK-193)
| Alan | Deger |
|------|-------|
| **Durum** | TAMAMLANDI |
| **Baslangic** | 2026-03-01 |
| **Bitis** | 2026-03-01 |
| **Etkilenen Dosyalar** | models/bank_rate.py (YENİ), models/__init__.py, migrations/versions/024_bank_rates_table.py (YENİ), modules/calculator/bank_rates.py, modules/calculator/calculator_router.py, modules/calculator/calculator_schemas.py, tasks/update_bank_rates.py (YENİ), modules/admin/bank_rates_router.py (YENİ), celery_app.py, main.py |

### Hedef
Kredi hesaplayicidaki hardcoded banka faiz oranlarini DB tablosuna tasimak, Celery freshness check task eklemek, GET /rates endpoint'ini DB'den okuyacak sekilde guncellemek, admin guncelleme endpoint'leri olusturmak.

### Yapilanlar
- [x] BankRate SQLAlchemy modeli olusturuldu (BigInteger PK, unique bank_name, Numeric oranlar, is_active, update_source, updated_at)
- [x] Alembic migration 024 olusturuldu (tablo CREATE + idx_bank_rates_active_updated indeks + GRANT app_user + 6 banka seed INSERT)
- [x] bank_rates.py yeniden yazildi: get_bank_rates_from_db(async) + get_bank_rates() fallback (DEFAULT_BANK_RATES korundu)
- [x] calculator_router.py guncellendi: GET /rates ve POST /compare artik DB session alarak DB'den okuyor
- [x] calculator_schemas.py guncellendi: BankRate'e is_active/update_source/from_attributes, BankRateUpdateRequest, BankRateUpdateItem, BankRateBulkUpdateRequest eklendi
- [x] Celery task olusturuldu: check_bank_rates_freshness (7 gun esik, WARNING log)
- [x] celery_app.py'ye 9. beat task eklendi (gunluk 09:00 TST = 06:00 UTC)
- [x] Admin router olusturuldu: GET /admin/bank-rates (tumu), PUT /admin/bank-rates/{bank_name} (tek), PUT /admin/bank-rates (toplu UPSERT)
- [x] models/__init__.py ve main.py guncellendi (import + include_router)
- [x] ruff check temiz (TC003 noqa — bilinen Pydantic+annotations kisitlamasi)

### Kararlar ve Notlar
- bank_rates tablosu RLS-SIZ — tenant-bagimsiz global referans verisi, tum ofisler ayni oranlari gorur
- BaseModel (UUID PK) kullanilMADI — BigInteger autoincrement PK (referans verisi icin basit yeterli)
- DEFAULT_BANK_RATES fallback olarak korundu (graceful degradation: DB erisilemezse)
- GRANT SELECT app_user eklendi — RLS session'larindan SELECT erisimi icin gerekli
- Admin endpoint'ler platform_admin rolu gerektiriyor (require_role dependency)
- Celery task sync psycopg2 kullanir (get_sync_session) — async event loop cakmasi onlendi

### Sonuc
Banka faiz oranlari DB'ye tasiindi, API DB'den okuyor, admin guncelleme endpoint'leri hazir, freshness check periyodik calisiyor. ruff check temiz.

---

## [RAPOR-009] Property Form Standardizasyon (TASK-189)
| Alan | Deger |
|------|-------|
| **Durum** | TAMAMLANDI |
| **Baslangic** | 2026-03-01 |
| **Bitis** | 2026-03-01 |
| **Etkilenen Dosyalar** | property.py, 022_property_form_standardization.py, properties/schemas.py, property.ts, property-form-schema.ts, property-form.tsx, showcases.ts |

### Hedef
Property formunu standardize etmek: 4 yeni DB kolonu (bathroom_count, furniture_status, building_type, facade), genisletilmis room_count secenekleri (15), yeni heating_type secenekleri (7), brut/net alan ayristirmasi, Arsa tipi icin alan gizleme.

### Yapilanlar
- [x] Backend: property.py modeline 4 yeni kolon eklendi (bathroom_count Integer, furniture_status String(20), building_type String(20), facade String(20))
- [x] Backend: Alembic migration 022 olusturuldu (ADD COLUMN x4, RLS dokunulmadi)
- [x] Backend: PropertyCreate + PropertyUpdate Pydantic schemalari olusturuldu
- [x] Frontend: property.ts'ye HeatingType, FurnitureStatus, BuildingType, Facade type'lari eklendi
- [x] Frontend: property-form-schema.ts yeniden yazildi (15 room, 5 bathroom, 7 heating, 3 furniture, 6 building, 8 facade secenegi)
- [x] Frontend: property-form.tsx yeniden yazildi (Select'ler, grid-cols-2 alan, Arsa gizleme)
- [x] ruff check 0 hata, tsc --noEmit 0 hata

### Kararlar ve Notlar
- area_sqm → gross_area (optional) + net_area (required) ayristirmasi
- room_count ve heating_type SegmentedControl → Select (cok fazla secenek)
- is_furnished checkbox → furniture_status Select (3 secenek)
- Arsa: bathroom/heating/furniture/building_type/facade GİZLİ

### Sonuc
Tum degisiklikler basariyla tamamlandi. Build ve lint temiz.

---

## [RAPOR-008] Musteri Model Genisletme — Demografik Bilgiler (TASK-191)
| Alan | Deger |
|------|-------|
| **Durum** | TAMAMLANDI |
| **Baslangic** | 2026-03-01 |
| **Bitis** | 2026-03-01 |
| **Etkilenen Dosyalar** | customer.py, 022_customer_demographics.py, schemas.py, customer.ts, customer-form.tsx, listing-text-form.tsx, showcase-form.tsx, use-properties.ts |

### Hedef
Musteri modeline 4 demografik alan eklemek: cinsiyet (gender), yas araligi (age_range), meslek (profession), aile buyuklugu (family_size). Frontend formda yeni "Demografik Bilgiler" bolumu olusturmak.

### Yapilanlar
- [x] Customer SQLAlchemy modeline 4 yeni kolon eklendi (gender, age_range, profession, family_size)
- [x] Alembic migration 022_customer_demographics olusturuldu (ADD COLUMN, RLS'e dokunulmadi)
- [x] CustomerCreate, CustomerUpdate, CustomerResponse Pydantic schema'larina Optional alanlar eklendi
- [x] Frontend customer.ts type'larina Gender, AgeRange type alias'lari + Customer interface'ine yeni alanlar eklendi
- [x] customer-form.tsx'e "Demografik Bilgiler" bolumu eklendi (Cinsiyet Select, Yas Araligi Select, Meslek Input, Aile Buyuklugu NumberInput — grid-cols-2)
- [x] Zod schema'ya yeni 4 optional alan eklendi, defaultValues guncellendi
- [x] QuickAddCustomer modal'a demografik alan EKLENMEDI (gorev geregi basit kalmali)
- [x] Mevcut build hatalari duzeltildi: listing-text-form.tsx bathroomCount enum type, showcase-form.tsx ve use-properties.ts mapApiToProperty eksik alanlar

### Kararlar ve Notlar
- Value=ASCII (erkek, kadin, belirtilmemis), Label=Turkce — backend'de ASCII string tutulur, frontend'de Turkce gosterilir
- RLS policy'lerine dokunulmadi — mevcut satir bazli policy tum kolonlari kapsar
- Mevcut build'de 3 onceden var olan TypeScript hatasi tespit ve duzeltildi (Property type'ina eklenen alanlar mapApiToProperty fonksiyonlarinda eksikti)
- Turbopack nft.json trace hatasi bilinen Next.js 15.5.12 sorunu — type checking ve derleme basarili

### Sonuc
Musteri modeli demografik bilgiler ile genisletildi. Backend (model + migration + schema) ve frontend (type + form) tamamlandi. Build type-check basarili.

---

## [RAPOR-007] Ilan Asistani Fiyat Alani + Token Refresh + PUT /auth/me (TASK-186)
| Alan | Deger |
|------|-------|
| **Durum** | TAMAMLANDI |
| **Baslangic** | 2026-03-01 |
| **Bitis** | 2026-03-01 |
| **Etkilenen Dosyalar** | listing-text-form.tsx, listings.ts, listings/page.tsx, use-listing-assistant.ts, types/listing.ts, api-client.ts, auth/router.py, auth/schemas.py, profile-form.tsx |

### Hedef
1. Ilan Asistani "Ilan metni olustur" butonunun 422 hatasi vermesini cozmek (eksik price alani)
2. Token refresh mekanizmasi eklemek (401 interceptor)
3. PUT /auth/me endpoint'i ile profil guncelleme

### Yapilanlar
- [x] ListingFormData tipine `price: number` alani eklendi
- [x] listing-text-form.tsx Zod schema'sina `price: z.coerce.number().min(1)` eklendi
- [x] listing-text-form.tsx formuna "Fiyat (TL)" input alani eklendi
- [x] listings.ts mapFormDataToBackend'te `price: 0` → `price: data.price` duzeltildi
- [x] listings/page.tsx'de hook'tan error/regenerateText destructure edildi
- [x] listings/page.tsx'de hata gosterimi (AlertCircle banner), onRegenerate/onChangeTone gercek fonksiyonlara baglandi
- [x] use-listing-assistant.ts'de HTTP durum koduna gore Turkce hata mesajlari eklendi (422, 401, 403, 429, 500+)
- [x] auth/schemas.py'ye UpdateProfileRequest schema eklendi
- [x] auth/router.py'ye PUT /me endpoint eklendi (partial update: full_name, phone)
- [x] api-client.ts'ye 401 interceptor eklendi: otomatik refresh token → yeni access token → retry
- [x] Refresh promise singleton pattern ile concurrent 401'ler tek refresh'e konsolide edildi
- [x] Auth endpoint'leri interceptor'dan haric tutuldu (sonsuz dongu onleme)
- [x] profile-form.tsx mock toast → gercek PUT /auth/me API cagrisina baglandi
- [x] pnpm build 0 hata, ruff check temiz

### Kararlar ve Notlar
- price defaultValues'a 0 olarak eklendi (Zod default degil — zodResolver uyumsuzlugu)
- refreshPromise singleton ile birden fazla 401 ayni anda geldiginde tek bir refresh istegi yapilir
- AUTH_EXCLUDED_ENDPOINTS listesi ile /auth/refresh, /auth/login, /auth/register interceptor'dan haric tutuldu
- PUT /me endpoint'i partial update: sadece gonderilen alanlar guncellenir (null check)

### Sonuc
Her iki sorun basariyla cozuldu. Build ve lint temiz.

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
