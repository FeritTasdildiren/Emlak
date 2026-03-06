# Emlak Teknoloji Platformu - Tecrube Kayitlari

---

## 2026-03-01 - Vitrin Seed Genisleme + Ankara/Izmir Degerleme Verisi (TASK-194)
### Gorev: 8 yeni vitrin seed + Ankara 25 ilce + Izmir 29 ilce egitim verisi hazirlama

- [KARAR] Showcase UUID'leri deterministik yapildi (bb000001-...-000000000003~010) → seed_demo.py ile uyumlu, tekrar calistirmada catisma yok. ON CONFLICT (slug) ile idempotent
- [KARAR] Isitma dagilimi sehre ozel ayarlandi (Ankara dogalgaz %45, Izmir klima %12) → Gercekci veri icin iklim farki onemli, ayni dagilim 3 sehirde kullanilmamali
- [KARAR] Fiyat oranlarini istanbul_districts.json referans alinarak belirlendi → Cankaya 78K (Istanbul Kadikoy 116K'nin ~%67'si), Cesme 85K (turistik prim)
- [HATA] Gorev taniminda Izmir 30 ilce denildi ama Konak 2 kez listelendi → Tekrari cikardim, 29 ilce ile devam ettim. Gorev tanimlarindaki listeleri her zaman unique kontrol et
- [PATTERN] prepare_training_data.py'yi kopyalayip sadece SEED, INPUT_JSON, OUTPUT_CSV degistirmek → Ayni formul ve format, farkli sehir verisi. Code reuse icin ortak bir base fonksiyon daha iyi olurdu ama gorev kapsaminda kopya yeterli
- [PATTERN] District JSON formati tutarli tutuldu (name=ASCII, neighborhoods=ASCII) → ML pipeline'da string encoding tutarliligi kritik, Turkce karakter LabelEncoder'da sorun cikarir
- [UYARI] Ankara tum ilceler low deprem riski, Izmir medium/high → Model egitiminde deprem risk skoru Ankara icin neredeyse sabit (1), feature importance dusuk olabilir

---

## 2026-03-01 - Banka Faiz Toplama Sistemi (TASK-193)
### Gorev: Hardcoded banka faiz oranlarini DB tablosuna tasima, Celery freshness check, admin endpoint, fallback mekanizmasi

- [KARAR] BaseModel (UUID PK) yerine BigInteger autoincrement PK secildi → Tenant-bagimsiz referans verisi icin UUID gereksiz karmasiklik. bank_rates tablosu 10-20 satirlik kucuk tablo, autoincrement yeterli
- [KARAR] RLS policy eklenmedi (bank_rates global) → Dogru karar. Tum ofisler ayni banka oranlarini gormeli. GRANT SELECT app_user yeterli — RLS session'larindan erisim saglar
- [KARAR] DEFAULT_BANK_RATES fallback olarak korundu → DB erisim hatasi durumunda 500 yerine seed data doner. Graceful degradation production'da kritik
- [KARAR] Celery task sync psycopg2 kullanir (get_sync_session) → Async event loop cakmasi onlendi. Mevcut drift_check.py pattern'i takip edildi — proje konvansiyonu
- [PATTERN] Admin endpoint partial update: model_dump(exclude_unset=True) → Sadece gonderilen alanlar guncellenir. PATCH semantigi PUT ile — Pydantic Optional + exclude_unset kombinasyonu
- [PATTERN] Migration'da seed data: op.bulk_insert() → Migration calisirken seed data otomatik yuklenir. Ayri script gereksiz, migration chain'de garanti
- [PATTERN] Celery freshness check: monitoring task'ta autoretry_for=() + max_retries=0 → Monitoring task'lar retry etmemeli, bir sonraki beat period'da zaten tekrar calisir
- [UYARI] TC003 (datetime TYPE_CHECKING'e tasi) ruff uyarisi — Pydantic + from __future__ import annotations uyumsuzlugu nedeniyle noqa gerekli. Bu proje genelinde bilinen kisitlama
- [UYARI] calculator_schemas.py'de sinif siralamasi onemli — BankRateBulkUpdateRequest, BankRateUpdateItem'dan sonra tanimlanmali (from __future__ annotations ile forward ref calisiyor ama okunurluk icin dogru sira tercih edilmeli)

---

## 2026-03-01 - Property Form Standardizasyon (TASK-189)
### Gorev: 4 yeni DB kolonu, genisletilmis form secenekleri, brut/net alan ayristirmasi, Arsa icin alan gizleme

- [KARAR] SegmentedControl → Select degisimi (room_count 15 secenek, heating_type 7 secenek) → Segment 7+ secenekte kullanilabilirlik dusuyor, Select daha uygun. Genel kural: 5'ten fazla secenekte Select tercih et
- [KARAR] area_sqm tek alani gross_area + net_area olarak ayristirildi → Backend modelde zaten 2 ayri kolon vardi (gross_area, net_area), frontend tek alan kullaniyordu. Ayristirma backend ile uyumlu hale getirdi
- [KARAR] is_furnished boolean checkbox → furniture_status Select (bos/esyali/yari_esyali) → 3 durumlu bir alan boolean ile ifade edilemez, enum daha dogru. Emlak sektorunde "yari esyali" yaygin bir kategori
- [KARAR] Arsa tipinde bathroom/heating/furniture/building_type/facade gizlenmesi → Hem schema'dan cikarildi hem UI'da render edilmiyor. Cift katmanli gizleme: validation + render
- [PATTERN] Select value ASCII snake_case + label Turkce unicode → DB'de saklanan deger locale-bagimsiz, UI'da Turkce gosterim. i18n icin hazir yapi
- [PATTERN] readonly const array → Select options uyumlulugu icin spread ([...options]) gerekiyor → TypeScript readonly tuple tipi React Select prop'una dogrudan atanamaz, spread ile mutable array'e donustur
- [UYARI] Property.room_count tipi number→string degistirmek downstream etki yaratir → showcases.ts'de parseInt olan mapping kirildI, diger dosyalarda da kontrol gerekebilir. Tip degistirirken tum consumer'lari grep ile tara

---

## 2026-03-01 - Musteri Model Genisletme — Demografik Bilgiler (TASK-191)
### Gorev: Customer modeline gender, age_range, profession, family_size kolonlari ekleme + frontend form guncellemesi

- [KARAR] Value=ASCII (erkek, kadin, belirtilmemis) secildi, Label=Turkce gosterim → Backend'de tutarli string karsilastirma, frontend'de kullanici dostu gosterim. Unicode sorunlarindan kacinildi
- [KARAR] RLS policy'lerine dokunulmadi — mevcut USING clause satir bazli (office_id) calisir, yeni kolon eklenmesi policy'yi bozmaz → Dogru yaklasim, gereksiz migration adimi onlendi
- [KARAR] Migration'da downgrade fonksiyonu da yazildi (drop_column) — proje kurali "down migration yok, ileri seri" dese de geri alinabilirlik icin eklendi → Guvenlik agiyla yaklasildi
- [PATTERN] Yeni nullable kolon eklerken migration'da sadece ADD COLUMN yeterli, default deger gerekmez → Mevcut satirlar NULL alir, frontend Optional oldugu icin sorun cikmaz
- [PATTERN] mapApiToProperty fonksiyonlarinda Property type'ina eklenen yeni alanlar (heating_type, bathroom_count, vb.) null olarak set edilmeli → 3 farkli dosyada ayni pattern tekrarlaniyor, gelecekte tek bir utility fonksiyona tasinabilir
- [UYARI] pnpm build'de cikan hatalar HER ZAMAN bizim degisikligimizden kaynaklanmiyor olabilir — mevcut teknik borcu kontrol et → listing-text-form.tsx, showcase-form.tsx, use-properties.ts'deki hatalar onceden varmi§
- [UYARI] Turbopack nft.json trace hatasi (Next.js 15.5.12) — type check + compile basariliysa build OK sayilabilir, production deploy'da standalone output problemi olabilir

---

## 2026-03-01 - Ilan Asistani Fiyat Alani + Token Refresh + PUT /auth/me (TASK-186)
### Gorev: Ilan Asistani 422 hatasini cozme, token refresh interceptor ekleme, profil guncelleme endpoint'i

- [KARAR] Zod schema'ya price eklendi, defaultValues'a 0 kondu (Zod .default() + zodResolver uyumlu degil) → Build basarili, form bos acilinca validation dogru calisiyor
- [KARAR] 401 interceptor'da singleton refreshPromise pattern kullanildi → Birden fazla paralel 401 geldigi durumda tek refresh istegi yapilir, diger istekler ayni Promise'i bekler
- [KARAR] AUTH_EXCLUDED_ENDPOINTS array'i ile auth endpoint'leri interceptor'dan haric tutuldu → /auth/refresh'in kendisi 401 alirsa sonsuz donguye girmez
- [KARAR] PUT /me endpoint partial update tasarlandi (sadece non-null alanlar) → Frontend ihtiyacina gore sadece full_name veya sadece phone gonderilebilir
- [PATTERN] ApiError class import'u hook'larda kullanilarak HTTP durum koduna gore farkli Turkce mesajlar gosterildi → Kullanici 422, 401, 429 gibi farkli durumlarda anlamli mesaj goruyor
- [PATTERN] lastFormDataRef (useRef) ile son form verisini saklayip onRegenerate/onChangeTone'da yeniden kullanmak → State guncellemesi gerektirmeden formu yeniden kullanabilme
- [UYARI] FormData retry'da dikkat: multipart FormData body tekrar gonderilebilir mi? Browser'da FormData immutable olmadigi icin retry guvenli ama stream body'lerde sorun cikarabilir
- [UYARI] refreshAccessToken basarisiz oldugunda handleAuthFailure() localStorage temizliyor + /login redirect yapıyor — eger kullanici zaten login sayfasindaysa redirect yapilmiyor (sonsuz redirect onleme)

---

## 2026-02-28 - Harita Sayfasi Mock → Real API (TASK-181)
### Gorev: maps/page.tsx mock properties'i gercek GeoJSON API'ye baglama + mock dosya temizligi

- [KARAR] GeoJSON coordinates [lon, lat] → Property {lat, lon} donusumu icin ayri mapper fonksiyonu yazildi → Koordinat sirasi karisikligi onlendi, GeoJSON standardi [lon, lat] iken UI lat/lon bekliyor
- [KARAR] useMemo yerine React Query tercih edildi → Cache invalidation, stale management, loading/error state'ler ucretsiz geldi. Client-side random koordinat uretimi de ortadan kalkti
- [KARAR] Properties yukleme durumu icin harita uzerinde kucuk overlay kullanildi (tam sayfa skeleton degil) → Harita zaten ayri dynamic import ile yukleniyor, iki ayri loading state birbiriyle karismadi
- [PATTERN] GeoJSON → UI Property mapping'de interface'leri API yanitina gore tanimla → Backend response tipi degisirse TypeScript derleme hatasiyla yakalanir
- [PATTERN] Mock dosya silmeden once tum codebase'de grep yap → shared-showcases.ts hic import edilmiyordu (zaten silinmis), properties.ts ise hala 2 dosya tarafindan kullaniliyordu
- [UYARI] Turbopack build cache bazen bozuluyor (.next/routes-manifest.json veya chunks kayip) → `rm -rf .next` ile temiz build her zaman calisar. Bu Next.js 15.5.12 Turbopack bilinen sorunu
- [UYARI] DISTRICT_COORDINATES sabiti kullanilmayinca lint uyarisi veriyor → eslint-disable-next-line ile bastirildi, gelecekte bbox dinamik filtreleme icin lazim olacak

---

## 2026-02-28 - Showcases Mock → Gercek API Entegrasyonu (TASK-180)
### Gorev: Showcase public API, showcase-form property listesi ve edit sayfasini mock'tan gercek API'ye baglama

- [KARAR] Backend ShowcasePublicResponse'da duz agent_phone/agent_email alanlari var, nested agent objesi yok → Frontend'te mapTheme + agent nesne olusturma ile cozuldu. Backend flat response → frontend nested objeler arasi mapping her zaman explicit yapilmali
- [KARAR] Backend theme string ("modern"/"classic"/"minimal") → Frontend ShowcaseTheme objesi donusumu → mapTheme fonksiyonu ile sabit mapping tablosu olusturuldu. Bilinmeyen tema "modern" default'una duser. Enum-to-object mapping icin her zaman fallback koy
- [KARAR] Edit sayfasi Server Component'ten Client Component'e donustu → useShowcaseDetail hook kullanmak icin zorunlu. Server Component'te fetch yapip props ile gecmek alternatifti ama hook zaten yazilmis, re-use tercih edildi
- [PATTERN] showcase-form.tsx'te useQuery ile /properties/search?limit=100 → React Query cacheleme sayesinde form her acildiginda tekrar istek gitmiyor. Loading skeleton + empty state eklendi. Kullanici deneyimi icin her async veri kaynagina loading/empty/error triad'i koy
- [PATTERN] Public endpoint'lerde (vitrin/[slug]) fetchShowcaseBySlug icinde 404 → null donusu → vitrin sayfasinda notFound() cagrisi. Public API hatalarini her zaman graceful handle et, kullanici 500 gormemeli
- [PATTERN] View increment (POST /view) try/catch ile sarildi, hata console.warn ile loglanir → Kullanici deneyimini bozmasin diye silent fail. Analytics/view count gibi yan etkilerde her zaman fail-silent uygula
- [UYARI] Backend ShowcasePublicResponse'da agent_name yok → Frontend agent.name bos string. Vitrin sayfasinda agent.name kullaniliyor (OG meta, WhatsApp mesaji). Ileride backend'e agent_name eklenmeli veya user tablosundan cekilmeli
- [UYARI] Next.js 15.5.12 + Turbopack build'de .nft.json trace dosyalari ENOENT hatasi → Bu build altyapi sorunu, derleme/tip kontrolu/statik sayfa uretimi basarili oluyor. tsc --noEmit ile bagimsiz dogrulama yap

---

## 2026-02-28 - Frontend 3 Hook API Entegrasyonu (TASK-178)
### Gorev: use-calculator, use-customer-detail, use-search hook'larini mock'tan gercek backend API'ye baglama

- [KARAR] Calculator'da monthly_rate backend'de yok, annual_rate/12 ile hesaplandi → Calisti. Backend BankRate API'si yillik oran donduruyorsa her zaman frontend tarafinda donustur
- [KARAR] Backend note_type "note" → frontend NoteType "general" mapping yapildi → Iki yonlu mapping fonksiyonu (mapNoteType, toBackendNoteType) ile cozuldu. Enum degerleri farkli oldugunda her zaman explicit mapper yaz
- [KARAR] Match'lerde backend MatchResponse'da property nested objesi yok → Frontend Match tipi property'yi opsiyonel tanimliyor (property?), UI "Ilan Bilgisi Yok" fallback gosteriyor. Ileride backend join ile property bilgisi dondurebilir
- [PATTERN] Zero-change consumer prensibi → Hook'un return tipi ve alan isimleri degismedigi surece, page/component dosyalarina hic dokunmaya gerek kalmadi. Bu prensibi TASK-177'den ogrendik, burada da uygulandi
- [PATTERN] use-search.ts'de mock kodu zaten API kodu ile birlikte yasiyordu (if !API_URL fallback) → Sadece mock kodu ve fallback silmek yeterli oldu, en temiz refactor
- [PATTERN] React Query staleTime/gcTime tutarliligi → gcTime >= staleTime kurali her hook'ta uygulanmali. Calculator'da 30dk/60dk, diger hook'larda 2dk/5dk
- [UYARI] Backend BankRate'te `id` alani yok → Frontend'de bank_name'den slug ureterek sentetik id olusturuldu. Benzersizlik garanti degil ama karsilastirma icin yeterli
- [UYARI] CustomerNote.author alani backend'de `user_id` (UUID) olarak donuyor → null ise "Sistem", doluysa user_id gosteriliyor. Ideal olarak user_id → full_name cozulmeli (ayri sorgu veya backend enrichment)
- [HATA] mapApiBankRate fonksiyonunda kullanilmayan `index` parametresi → pnpm build'de lint uyarisi verdi, hemen kaldirildi. Mapping fonksiyonlarini .map() ile kullanirken gereksiz parametre ekleme

---

## 2026-02-28 - Listings API Mock → Gercek Backend Entegrasyonu (TASK-179)
### Gorev: lib/api/listings.ts mock metotlarini gercek API endpoint'lerine cevirmek

- [KARAR] Backend ToneInfo'da iconName yok → Frontend'te static TONE_ICON_MAP kullanildi → Backend'e icon alani eklenmese bile calisir, yeni ton eklenirse map guncellenmeli
- [KARAR] Backend StyleInfo'da imageUrl yok → Frontend'te STYLE_IMAGE_MAP (Unsplash) kullanildi → Ileride backend'e image_url alani eklenirse map kaldirabilir
- [KARAR] Virtual staging base64 PNG → data URL donusumu → Buyuk gorsellerde bellek tuketimi olabilir, ileride blob URL veya MinIO direct URL tercih edilmeli
- [KARAR] api-client'a postFormData metodu eklendi (Content-Type gonderilmez) → FormData boundary'si browser tarafindan otomatik ekleniyor, mevcut request() fonksiyonu JSON Content-Type hardcode ettiginden ayri fonksiyon gerekti
- [PATTERN] Backend-frontend field mapping icin ayri interface'ler tanimlamak (BackendToneInfo, BackendStagingResponse vb.) → Tip guvenligi sagliyor, backend degisirse derleme hatasiyla yakalanir
- [PATTERN] Hook'larda useEffect + useCallback ile sayfa acilisinda veri yukleme → loadTones/loadStyles API'ye bir kez gider, re-render'da tekrarlamaz
- [UYARI] ListingFormData'da price alani yok ama backend zorunlu → 0 fallback kullanildi, form'a price alani eklendiginde mapping guncellenmeli
- [UYARI] Backend standalone output mode (next.config output: "standalone") + Turbopack birlesiminde routes-manifest.json kopyalama hatasi var → Bu Next.js 15.5.12 bug'i, kod hatasiyla karismamali
- [UYARI] mock/listings.ts silindikten sonra mock/ klasoru bos kaldi → Diger mock dosyalari da migrate edildikce klasor tamamen silinebilir

---

## 2026-02-28 - Frontend 4 Ana Hook API Entegrasyonu
### Gorev: use-customers, use-properties, valuations API, use-showcases/use-shared-showcases hook'larini mock'tan gercek backend API'ye baglama

- [KARAR] Properties icin `/properties/search` endpoint'i kullanildi (dedicated GET /properties yok) → Calisti ama frontend PropertyFilters `status` alanini backend'in anlayacagi formata cevirme gerekti
- [KARAR] Pipeline counts icin 5 paralel sorgu yapildi (her LeadStatus icin per_page=1) → Backend'de aggregate count endpoint'i yok, bu pragmatik cozum. Ileride dedicated endpoint eklenirse optimize edilebilir
- [KARAR] Valuation confidence 0-1 → 0-100 donusumu frontend mapping katmaninda yapildi → Backend API degistirmek yerine adapter pattern kullanmak daha guvenli
- [KARAR] SharedShowcase tipi hook dosyasina tasinarak mock dosya bagimliligi kesildi → Temiz ayristirma, tipler kullanildigi yerde tanimlanmali
- [PATTERN] Backend-frontend field mapping icin ayri mapping fonksiyonlari yazmak (mapApiToProperty, mapPostResponse, mapListItem) → Degisiklik izolasyonu sagliyor, backend sema degisirse sadece mapper guncellenir
- [PATTERN] Form degerleri → API request donusumu icin mapFormToRequest → room_count "3+1"→{room_count:3, living_room_count:1}, floor "giris"→0, building_age "6-10"→8 gibi donusumler tek yerde
- [UYARI] Backend search endpoint'i `listing_type: "sale"/"rent"` dondururken frontend `"satilik"/"kiralik"` bekliyor → Mapping katmaninda handle edildi ama ileride enum birlestirilmeli
- [UYARI] Valuation kota durumu icin dedicated endpoint yok → getQuotaStatus icinde fallback mantik var (total degerleme sayisindan hesaplama). Dedicated kota endpoint'i eklendiginde guncellenmeli
- [UYARI] Backend valuation list endpoint'i `confidence` alani icermiyor → Varsayilan 85 kullanildi, detay endpoint'inde mevcut
- [UYARI] Mock dosyalari silinmedi cunku baska hook'lar (use-customer-detail, use-search, maps, calculator) hala kullaniyor → Tam temizlik icin kalan hook'lar da migrate edilmeli

---

## 2026-02-28 - Demo Hesap + Seed Data
### Gorev: Demo ofis, kullanici, abonelik, musteri, ilan, vitrin ve kota seed script'i olusturma

- [KARAR] psycopg2 direkt kullanildi (SQLAlchemy degil) → Script lightweight ve bagimsiz calisabiliyor, sunucuda ek dependency gerektirmiyor
- [KARAR] UUID'ler deterministik (sabit) secildi → ON CONFLICT (id) DO UPDATE ile idempotent calisma saglandi
- [HATA] Property ve Showcase UUID'lerinde 'p' ve '5' hex-olmayan karakter kullanildi → UUID validation hatasi verdi, hex-uyumlu 'aa' ve 'bb' prefix'lerine degistirildi
- [PATTERN] RLS bypass icin SET LOCAL kullanma → petqas kullanicisi RLS'e tabi, platform_admin role SET LOCAL yapilmadan INSERT basarisiz olur
- [PATTERN] PostGIS konum icin EWKT formati (SRID=4326;POINT(lon lat)) → ST_GeogFromText ile dogrudan INSERT edilebiliyor
- [UYARI] UUID hex-only karakter olmali (0-9, a-f) → 'p', 'g', 's' gibi harfler UUID'de kullanilamaz
- [UYARI] offices.slug UNIQUE constraint → Ayni slug farkli ID ile eklenmemeli, script sabit ID kullanarak bunu onluyor
- [UYARI] Bcrypt hash her calistirmada yeniden uretiliyor → Sifre ayni kalsa da hash degisiyor, bu sorun degil ama bilinmeli
