# MIMARI-KARARLAR (ADR Log)

> Amaç: Mimari kararları "nedenleriyle" kayıt altına almak; ileride refactor, onboarding ve denetim süreçlerini kolaylaştırmak.
> Format: Problem → Seçenekler → Karar → Sonuçlar → Rollout Plan → Hedef Sprint

---

## ADR-0001 — Multi-tenant izolasyonu: RLS + `SET LOCAL`

- **Durum:** Proposed
- **Hedef Sprint:** S0
- **Problem / Bağlam:** Connection pool kullanılan ortamlarda (async/uvicorn + SQLAlchemy + pool) session-level `SET app.current_office_id` kalıntısı tenant sızıntısına yol açabilir. Aynı process içinde ardışık farklı tenant request'lerinde önceki tenant'ın verisi görünebilir.
- **Seçenekler:**
  1. Session-level `SET` — riskli, pool reuse'da sızıntı
  2. Transaction içinde `SET LOCAL` — transaction scope'una kapalı, otomatik temizlenir
  3. Uygulama seviyesinde tüm sorgularda `office_id` filtreleme — kolay ama kaçaklara açık
- **Karar:** Postgres transaction içinde **`SET LOCAL app.current_office_id = ...`** kullanılacak. `SET LOCAL` mutlaka **transaction başladıktan sonra** ve **ilk query'den önce** çağrılacak (middleware'de `BEGIN` → `SET LOCAL` → handler → `COMMIT/ROLLBACK` sırası). RLS **Property ile sınırlı kalmayacak**; veri taşıyan tüm tablolara uygulanacak: Customer, Conversation, Message, Match, Subscription, Payment, Transaction, Notification, AuditLog.
- **Hardening Notu — Owner/Privileged Role Bypass Riski:**
  PostgreSQL'de tablo owner'ı ve superuser rolleri RLS policy'lerini varsayılan olarak bypass eder. Bu, migration veya admin scriptlerinde farkında olmadan tenant izolasyonunun delinmesi anlamına gelir. Kritik data-bearing tablolarda **`ALTER TABLE ... FORCE ROW LEVEL SECURITY`** uygulanmalıdır. Bu sayede owner bile RLS'ye tabi olur. Admin erişimi gereken senaryolarda ayrı bir `admin_bypass` policy oluşturularak kontrollü bypass sağlanır. Uygulama DB kullanıcısı (`app_user`) kesinlikle tablo owner'ı olmamalıdır.
- **Sonuçlar:** Tenant izolasyonu üretimde daha güvenli ve denetlenebilir olur; unutulan bir WHERE koşulunun veri sızıntısına yol açması yapısal olarak engellenir. Pen-test/audit tarafında savunulabilir mimari.
- **Rollout Plan:**
  1. DB migration: tüm data-bearing tablolara `office_id` FK + RLS policy setleri + `FORCE ROW LEVEL SECURITY`
  2. Uygulama DB kullanıcısının owner olmadığını doğrulama; ayrı `app_user` rolü
  3. Middleware/DB session katmanında `SET LOCAL` entegrasyonu (BEGIN → SET LOCAL → query → COMMIT sırası)
  4. Cross-tenant erişim test case'leri (integration + unit): Tenant A ile giriş → Tenant B verisine erişim denemesi → başarısız olmalı
  5. Pool reuse senaryosu testi: aynı process içinde ardışık farklı tenant request'leri → önceki tenant verisi sızmıyor mu doğrulaması
  6. Owner bypass testi: app_user rolüyle FORCE RLS aktifken direkt SQL ile cross-tenant erişim denemesi → başarısız olmalı
  7. e2e: multi-tenant CRUD akışları

---

## ADR-0002 — Güvenilir async işler: Outbox Pattern + idempotency

- **Durum:** Accepted (Concurrency Strategy Confirmed S0)
- **Hedef Sprint:** S1
- **Problem / Bağlam:** "DB'ye yazıldı ama dış servise gitmedi" / "dış servise gitti ama DB'ye yazılamadı" tutarsızlıkları ve retry'larda duplicate riskleri. Özellikle mesaj gönderimi, ödeme webhook işleme ve doğrulama akışlarında kritik.
- **Seçenekler:**
  1. Direkt Celery publish/send — basit ama tutarsızlık riski
  2. Outbox Pattern (DB'de kuyruk) — atomiklik garantisi
  3. Tamamen event-stream (Kafka vb.) — Faz-2+
- **Karar:** Kritik aksiyonlarda **Outbox** uygulanacak: DB commit → `outbox_events` row → worker publish/send. Tüm dış çağrılar **idempotency key** (ör. `message.id`, `payment.intent_id`) ile korunacak.
- **Worker Concurrency Notu:**
  Birden fazla outbox worker aynı anda çalışabilir. Aynı event'in birden çok worker tarafından kapılmasını engellemek için event seçimi **`SELECT ... FOR UPDATE SKIP LOCKED`** ile yapılacak. Outbox tablosunda `status` (pending/processing/sent/failed) + `locked_at` + `locked_by` alanları bulunacak. Worker: `UPDATE outbox SET status='processing', locked_at=now(), locked_by=worker_id WHERE id IN (SELECT id FROM outbox WHERE status='pending' FOR UPDATE SKIP LOCKED LIMIT N)` paterni uygulanacak.
- **Tasarım Notu — Polling vs LISTEN/NOTIFY:**
  - **MVP (S1):** Outbox worker polling ile çalışacak (basit, stabil, kabul edilebilir latency)
  - **Faz-2:** LISTEN/NOTIFY ile tetikleme değerlendirilebilir. Ancak NOTIFY mesajları garanti teslim değildir (connection drop'ta kaybolabilir). Bu yüzden doğru yaklaşım **"notify + fallback polling"** hibrit modelidir: NOTIFY hızlı tetikleme sağlar, polling ise kaçan event'leri yakalar. Polling interval'i NOTIFY aktifken daha uzun tutulabilir (ör. 30s vs 5s).
- **Ek: Inbox Pattern (incoming event store):**
  Özellikle payment webhook gibi dış kaynaklardan gelen event'lerde, event önce `inbox_events` tablosuna yazılır (`event_id` unique constraint). Bu sayede duplicate event zaten DB seviyesinde reddedilir, ardından işleme alınır. Outbox giden akış, Inbox gelen akış için birbirini tamamlayan ikili yapı oluşturur.
- **Sonuçlar:** Atomiklik, izlenebilirlik, tekrar gönderim kontrolü ve operasyonel debug kolaylığı.
- **Rollout Plan:**
  1. `outbox_events` tablosu: id, event_type, payload, status, locked_at, locked_by, created_at, processed_at, retry_count
  2. `inbox_events` tablosu: event_id (unique), source, payload, status, created_at, processed_at
  3. Outbox worker: `SELECT ... FOR UPDATE SKIP LOCKED` + status management
  4. Adapter dedup: idempotency key kontrolü
  5. Failure/retry politikası (exponential backoff + max retry + dead letter queue)
  6. Monitoring: outbox lag metrikleri, stuck event alert'leri

---

## ADR-0003 — MLOps minimumu: ModelRegistry + PredictionLog + drift sinyalleri

- **Durum:** Proposed
- **Hedef Sprint:** S3
- **Problem / Bağlam:** Üretimde modelin hangi versiyonla, hangi veriye göre çalıştığı; tahminlerin geriye dönük kalitesi ve bozulma (drift) takibi. Bunlar yoksa valuation sistemi güven kaybeder ve debug çok pahalı olur.
- **Seçenekler:**
  1. Script ile eğit, dosyayı değiştir — izlenemez
  2. Minimum registry + log — MVP uygun
  3. Tam ML platformu (MLflow vb.) — Faz-2+
- **Karar:**
  - `model_registry`: model_name, version, artifact_url, trained_at, metrics (RMSE, MAE, R²), data_snapshot_id
  - `prediction_log`: input features, output, confidence, model_version, timestamp, actual_outcome (varsa)
  - Basit drift: giriş dağılımları (m², oda sayısı, ilçe) + confidence trendleri ile "model bozuluyor" sinyali
- **Feedback Loop Stratejisi:**
  Gerçek satış/kira fiyatını yakalamak her zaman mümkün olmayabilir. Bu durumda **proxy feedback** kullanılacak:
  - Satıldı / satılmadı (binary)
  - Kaç günde satıldı (time-to-sale)
  - Fiyatta kaç revizyon gördü (price revision count)
  - İlan görüntülenme/tıklanma oranı (demand signal)

  Bu proxy'ler, doğrudan fiyat karşılaştırması olmasa bile modelin pratik başarısını ölçmeye yeter.
- **Sonuçlar:** Değerleme güvenilirliği artar; "model neden böyle dedi?" sorusu cevaplanabilir olur; drift erken yakalanır.
- **Rollout Plan:**
  1. model_registry + prediction_log şemaları (S3)
  2. Inference pipeline'da otomatik log yazımı (S3)
  3. Haftalık metrik raporu (S3 sonu)
  4. Feedback loop aktivasyonu: proxy feedback veri toplama (S4)
  5. (Opsiyonel) Yeniden eğitim tetikleyicileri (S4+)

---

## ADR-0004 — Observability: request_id/trace_id korelasyonu + OTel (backend)

- **Durum:** Proposed
- **Hedef Sprint:** S0 (iskelet) → S1 (tam OTel)
- **Problem / Bağlam:** Sentry/metrics tek başına yeterli değil; request → celery task → external API zincirinde iz sürmek zor. Prod issue çözüm süresi gereksiz uzuyor.
- **Seçenekler:**
  1. Sadece log/metric — korelasyon yok
  2. Korelasyon id'leri + structured logging — minimum
  3. OpenTelemetry ile distributed tracing — tam çözüm
- **Karar:** Her API request'inde **`request_id`**, her Celery task'ta **`trace_id`** taşınacak. Backend'de **OpenTelemetry** ile DB ve dış servis çağrıları trace edilecek.
- **Pratik Uygulama Notları:**
  - FastAPI middleware'de `request_id` üretilir (UUID) ve response header'a + log context'e eklenir
  - Celery'ye taşıma: `celery.signals.before_task_publish` ile task header'a `request_id` enjekte edilir; `task_prerun` ile worker tarafında log context'e alınır
  - Müşteri desteği için: hata ekranlarında `request_id` görünür olmalı ("Bu kodu destek ekibine iletin" UX pattern'i). Bu sayede destek talebi → log → root cause zinciri dakikalar içinde kurulabilir
- **Sonuçlar:** Prod issue çözüm süresi düşer; kök neden analizi hızlanır; müşteri destek süreci iyileşir.
- **Rollout Plan:**
  - **S0 — İskelet (korelasyon altyapısı):**
    1. FastAPI middleware → request_id üretimi (UUID v7 önerilir — zamana sıralı) + response header (`X-Request-ID`)
    2. Structured log formatı: tüm log satırlarında `request_id` alanı
    3. Celery hook'ları → `before_task_publish` ile task header'a `request_id` propagation; `task_prerun` ile worker log context'e alma
    4. Hata yanıtlarında `request_id` alanı (API error response body'de)
  - **S1 — Tam OTel entegrasyonu:**
    1. OpenTelemetry SDK (Python) entegrasyonu: FastAPI + SQLAlchemy + httpx instrumentasyonu
    2. OTel exporter yapılandırması (Jaeger veya Grafana Tempo)
    3. Trace explorer dashboard'u (Grafana)
    4. Frontend hata ekranlarında request_id gösterimi (UX: "Hata kodu: REQ-xxxxx")

---

## ADR-0005 — Payments: webhook güvenliği + refund/void + timeline + ledger

- **Durum:** Proposed
- **Hedef Sprint:** S1
- **Problem / Bağlam:** Webhook'larda duplicate event ve sahte çağrı riski; refund/iptal süreçleri netleşmezse finansal kaos. Ayrıca finansal hareketlerin denetlenebilir bir kaydı olmazsa muhasebe ve compliance zorlukları çıkar.
- **Seçenekler:**
  1. Basit "payment success" flag — yetersiz
  2. Signature verification + idempotency + refund modelleme + ledger — önerilen
- **Karar:**
  - Webhook **signature verification** (provider'a özgü: iyzico HMAC, Stripe webhook secret, vb.)
  - Event **idempotency**: `event_id` unique constraint (Inbox pattern ile — bkz. ADR-0002)
  - Refund/void akışları modelleme
  - `payment_timeline` / audit izleri
- **Opsiyonel ama Önerilen — Ledger Yaklaşımı:**
  Finansal hareketleri append-only bir `ledger_entries` tablosunda tutmak:
  - Satır tipleri: `charge`, `refund`, `discount`, `credit`, `chargeback`
  - Her satır: amount, currency, payment_id, entry_type, created_at, description
  - Bakiye = SUM(charges) - SUM(refunds+chargebacks) + SUM(credits) - SUM(discounts)
  - Bu yapı finansal raporlama, mutabakat (reconciliation) ve denetim için çok güçlü bir temel oluşturur
- **Sonuçlar:** Güvenlik ve denetlenebilirlik artar; müşteri destek süreçleri oturur; finansal mutabakat kolaylaşır.
- **Rollout Plan:**
  1. Provider seçimi → webhook endpoint oluşturma
  2. Signature verification implementasyonu (provider-specific)
  3. `inbox_events` ile event idempotency (ADR-0002 ile ortak altyapı)
  4. Payment schema güncellemesi: refund/void alanları + `payment_timeline`
  5. (Opsiyonel) `ledger_entries` tablosu + reconciliation raporu
  6. e2e: ödeme → webhook → refund → bakiye doğrulama

---

## ADR-0006 — AreaAnalysis / DepremRisk: provenance + periyodik refresh pipeline

- **Durum:** Proposed
- **Hedef Sprint:** S2
- **Problem / Bağlam:** Tablolar var ama güncelleme sıklığı, kaynak versiyonu ve denetim izi net değilse veri çürür ve müşteriye yanlış bilgi verme riski doğar.
- **Seçenekler:**
  1. Manual update — riskli, izlenemez
  2. Celery beat ile schedule + provenance — önerilen
  3. Full data platform — Faz-2+
- **Karar:** Celery beat ile **periyodik batch refresh**. `data_sources` alanı "liste" değil **source + timestamp + version** yapısında tutulacak.
- **Stale Data Stratejisi:**
  - Her veri kaydında `last_refreshed_at` alanı tutulur
  - Veri **X aydan** (konfigüre edilebilir, varsayılan 6 ay) eskiyse UI'da **"Güncel değil — son güncelleme: [tarih]"** badge/uyarı gösterilir
  - Refresh job başarısız olursa: son başarılı veri korunur + alert gönderilir + `refresh_status: FAILED` kaydedilir
  - Kullanıcıya "veri yok" yerine "eski veri + uyarı" göstermek tercih edilir (graceful degradation)
- **Sonuçlar:** Denetlenebilirlik ve veri güvenilirliği artar; müşteri tarafında yanlış bilgi riski azalır.
- **Rollout Plan:**
  1. Celery beat job tanımı (area_refresh, deprem_risk_refresh)
  2. Batch stratejisi (il → ilçe → mahalle katmanlı)
  3. Provenance şeması: source, timestamp, version, refresh_status
  4. Stale data UI badge implementasyonu
  5. İzleme/alert: refresh başarısızlık bildirimi

---

## ADR-0007 — Messaging statüleri: kanal bazlı capability modeli

- **Durum:** Proposed
- **Hedef Sprint:** S2
- **Problem / Bağlam:** "delivered/read" sinyali her kanalda yok veya güvenilir değil (Telegram Bot API vs WhatsApp). Tek tip statü KPI'ları ve UI'ı yanıltır.
- **Seçenekler:**
  1. Tek tip statü tüm kanallara — yanlış/yanıltıcı
  2. Adapter capability modeli — önerilen
- **Karar:** Connector/adapter seviyesinde capability tanımlanacak. UI ve raporlama bu capability'ye göre davranacak.
- **Genişletilebilirlik Notu:**
  Capability modeli enum yerine **flag set / JSON capabilities** yapısında tasarlanacak. Bu sayede yeni yetenekler kod değişikliği olmadan eklenebilir:
  ```json
  {
    "supports_delivered": true,
    "supports_read": false,
    "supports_typing_indicator": false,
    "supports_reactions": false,
    "supports_thread_reply": false,
    "supports_media_upload": true,
    "max_message_length": 4096
  }
  ```
  Her adapter kendi capabilities JSON'unu döner; UI bu JSON'a göre dinamik davranır.
- **Sonuçlar:** Ürün doğruluğu ve raporlama güvenilirliği artar. Yeni kanal ekleme maliyeti düşer.
- **Rollout Plan:**
  1. Adapter interface güncellemesi: `get_capabilities()` metodu
  2. Telegram + WhatsApp adapter'larında capability tanımlama
  3. UI mapping: capability'ye göre statü gösterimi
  4. Rapor metrikleri revizyonu: "read rate" sadece read destekleyen kanallarda hesaplanır

---

## ADR-0008 — Secrets yönetimi: repo'da secret yok

- **Durum:** Proposed
- **Hedef Sprint:** S0
- **Problem / Bağlam:** Repo'da encrypted `.env` bile pratikte key rotasyonu, erişim sınırlandırma ve yanlışlıkla sızıntı riski taşır. Ekip büyüdükçe yönetimi zorlaşır.
- **Seçenekler:**
  1. Repo'da encrypted env — önerilmez
  2. CI/CD ile inject + sunucuda env — MVP uygun
  3. SOPS+age veya Vault/Infisical — Faz-1/2
- **Karar:** Repo'da sadece `.env.example` (tüm key'ler boş değerle). Gerçek secrets **CI/CD** üzerinden (GitHub Actions secrets / environment) inject edilecek. Sunucuda `.env` sadece deploy target'ta yaşar. İleri aşamada SOPS+age veya Vault/Infisical değerlendirilecek.
- **Sonuçlar:** Güvenlik ve operasyonel kontrol artar; rotation kolaylaşır.
- **Rollout Plan:**
  1. Repo temizliği: mevcut .env dosyalarının gitignore'a eklenmesi
  2. `.env.example` oluşturulması (tüm key'ler, açıklamalar, boş değerler)
  3. CI/CD secret store yapılandırması (GitHub Actions secrets)
  4. Deploy pipeline'da env inject mekanizması
  5. Rotation prosedürü dokümantasyonu

---

## ADR-0009a — PDF üretimi: WeasyPrint bağımlılık stabilizasyonu

- **Durum:** Proposed
- **Hedef Sprint:** S4
- **Problem / Bağlam:** WeasyPrint, pango/cairo/fontlar gibi native bağımlılıklara sahip. Docker container'da bu bağımlılıklar sabitlenmezse prod'da sürpriz hatalar çıkabiliyor.
- **Seçenekler:**
  1. "Çalışırsa çalışır" container — riskli
  2. Pin'li bağımlılıklar + healthcheck — önerilen
  3. Alternatif PDF engine (Puppeteer/Playwright + Chromium) — Faz-2+ değerlendirmesi
- **Karar:** Docker image'da WeasyPrint + native bağımlılıkları (pango, cairo, fontconfig, Türkçe fontlar) **version pin** ile sabitlenecek. PDF üretimi için healthcheck endpoint'i eklenecek.
- **Sonuçlar:** PDF stabilitesi artar; prod'da "font eksik / render bozuk" sürprizleri engellenir.
- **Rollout Plan:**
  1. Dockerfile'da apt paketleri + pip paketleri version pin
  2. Türkçe font paketi (Noto Sans, vb.) dahil edilmesi
  3. PDF smoke test: örnek doküman üretimi + sayfa sayısı/boyut doğrulaması
  4. Healthcheck: `/health/pdf` endpoint'i

---

## ADR-0009b — Türkçe arama kalitesi: FTS + unaccent + pg_trgm

- **Durum:** Proposed
- **Hedef Sprint:** S4
- **Problem / Bağlam:** Türkçe metin aramasında kısaltmalar, imla hataları ve "ş/ı/ğ/ü/ö/ç" varyasyonları (özellikle kullanıcı ASCII ile yazdığında) arama kalitesini düşürüyor.
- **Seçenekler:**
  1. Sadece PostgreSQL FTS — Türkçe'ye duyarsız
  2. FTS + unaccent + pg_trgm kombinasyonu — toleranslı arama
  3. Meilisearch'e geçiş — Faz-2 (bkz. TEKNIK-MIMARI.md SearchService interface)
- **Karar:** PostgreSQL'de **unaccent** extension ile diacritic normalizasyonu + **pg_trgm** ile fuzzy matching kombinasyonu uygulanacak. Bu sayede "satilik" → "satılık", "kacak" → "kaçak" gibi varyasyonlar yakalanır.
- **Türkçe `ı/İ` Lowercasing Tuzağı:**
  PostgreSQL'in varsayılan `lower()` fonksiyonu locale'e bağlıdır ve Türkçe `İ → i` (İngilizce) yerine `İ → ı` (Türkçe) dönüşümünü her zaman doğru yapmayabilir. Normalize fonksiyonunda (ör. custom `turkish_lower()` veya `translate()` ile explicit mapping) bu varyasyonların doğru çalıştığı bir test seti ile doğrulanmalıdır. Test seti: `İstanbul/istanbul/ıstanbul`, `IŞIK/ışık/isik`, `İLAN/ilan/ılan` gibi yaygın tuzak kelimeler.
- **Sonuçlar:** Kullanıcı arama deneyimi iyileşir; "gerçek hayattaki" ilan metinlerine uygun toleranslı arama sağlanır.
- **Rollout Plan:**
  1. `CREATE EXTENSION unaccent` + `CREATE EXTENSION pg_trgm`
  2. Unaccent + Turkish-aware text search config oluşturma
  3. Turkish lowercasing doğrulama: normalize fonksiyonu + test seti (`İ/ı`, `I/i` varyasyonları)
  4. İlan başlık/açıklama alanlarında trigram index
  5. Arama endpoint'inde FTS + trigram similarity hybrid sorgu
  6. Arama kalitesi testi: yaygın typo/varyasyon listesiyle precision/recall ölçümü

---

## Sprint Eşleştirme Özeti

| Sprint | ADR'ler | Tema |
|--------|---------|------|
| **S0** | ADR-0001 (RLS + FORCE), ADR-0008 (Secrets), ADR-0004 iskelet (request_id) | Güvenlik temeli + observability iskeleti |
| **S1** | ADR-0002 (Outbox/Inbox), ADR-0005 (Payments), ADR-0004 tam (OTel) | Güvenilirlik + observability + finans |
| **S2** | ADR-0006 (AreaAnalysis), ADR-0007 (Messaging capability) | Veri kalitesi + ürün doğruluğu |
| **S3** | ADR-0003 (MLOps) | AI/ML altyapısı |
| **S4** | ADR-0009a (WeasyPrint), ADR-0009b (TR arama) | Stabilite + arama kalitesi |
