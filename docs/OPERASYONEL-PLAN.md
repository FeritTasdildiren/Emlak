# Emlak Teknoloji Platformu — Operasyonel Plan

**Tarih:** 2026-02-20
**Versiyon:** 1.0
**Hazırlayan:** codex-operasyonel-planlayici
**Kaynaklar:** PRODUCT-BACKLOG.md, TEKNIK-MIMARI.md, MIMARI-KARARLAR.md, PROJE-PLANI.md
**Durum:** Taslak — Orkestra Şefi onayı bekleniyor

---

## 1. Sprint Takvimi Özeti

### 1.1 Genel Bakış

| Faz | Sprintler | Hafta | Süre | Tema | Milestone |
|-----|-----------|-------|------|------|-----------|
| **Faz 0 — Temel** | S0-S4 | 1-10 | 10 hafta | Altyapı + Veri + AI v0 | Çalışan iskelet + Model v0 |
| **MVP-Alpha** | S5-S11 | 11-24 | 14 hafta | 9 Core Özellik | Alpha Lansman (30+ seed ofis) |
| **MVP-Beta** | S12-S18 | 25-38 | 14 hafta | 6 Ek Özellik + Elite | Beta Lansman (500+ kullanıcı) |

**Toplam:** 19 sprint, 38 hafta (~9.5 ay)

### 1.2 Sprint Takvimi

```
Sprint  Hafta     Tarih Aralığı (Tahmini)    Tema                          ADR'ler
──────  ────────  ──────────────────────────  ────────────────────────────  ────────────────────
S0      1-2       Mart Hafta 1-2              Mimari + DB + CI/CD           ADR-1,4(iskelet),8
S1      3-4       Mart Hafta 3-4              Messaging Gateway + Outbox    ADR-2,4(tam),5
S2      5-6       Nisan Hafta 1-2             Veri Pipeline + Area          ADR-6,7
S3      7-8       Nisan Hafta 3-4             AI Model v0 + MLOps          ADR-3
S4      9-10      Mayıs Hafta 1-2             Hukuki + PDF + TR Arama       ADR-9a,9b
──────  ────────  ──────────────────────────  ────────────────────────────  ────────────────────
S5      11-12     Mayıs Hafta 3-4             AI Değerleme v1 (EPIC-01)    —
S6      13-14     Haziran Hafta 1-2           Bölge+Harita+Deprem(E02-04)  —
S7      15-16     Haziran Hafta 3-4           CRM Temel (EPIC-05)          —
S8      17-18     Temmuz Hafta 1-2            AI İlan Asistanı (EPIC-06)   —
S9      19-20     Temmuz Hafta 3-4            Vitrin+Kredi (EPIC-07,08)    —
S10     21-22     Ağustos Hafta 1-2           Telegram Tam (EPIC-09)       —
S11     23-24     Ağustos Hafta 3-4           QA + Alpha Lansman           —
──────  ────────  ──────────────────────────  ────────────────────────────  ────────────────────
S12     25-26     Eylül Hafta 1-2             WhatsApp Cloud API/Elite(E10)—
S13     27-28     Eylül Hafta 3-4             EİDS Hibrit (EPIC-11)        —
S14     29-30     Ekim Hafta 1-2              Portföy Ağı Aktif (EPIC-12)  —
S15     31-32     Ekim Hafta 3-4              Scraping (EPIC-13)           —
S16     33-34     Kasım Hafta 1-2             AI Fotoğraf (EPIC-14)        —
S17     35-36     Kasım Hafta 3-4             Ofis Yönetim (EPIC-15)       —
S18     37-38     Aralık Hafta 1-2            QA + Beta Lansman            —
```

### 1.3 Görsel Timeline

```
Hafta:  1──2──3──4──5──6──7──8──9──10──11──12──13──14──15──16──17──18──19──20──21──22──23──24
        |════ FAZ 0 ══════════════|════════════════ MVP-ALPHA ══════════════════════════════|
        [S0  ][S1  ][S2  ][S3  ][S4  ][S5    ][S6    ][S7    ][S8    ][S9    ][S10   ][S11  ]
                                                                                      🚀Alpha

Hafta:  25──26──27──28──29──30──31──32──33──34──35──36──37──38
        |═══════════════════ MVP-BETA ═══════════════════════|
        [S12   ][S13   ][S14   ][S15   ][S16   ][S17   ][S18  ]
                                                          🚀Beta

Paralel İşler:
BSP Başvurusu ──────────────────────────────────────────────→ (onay S12'de)
Seed Ofis     ──────────→ Alpha Lansmanı → Organik büyüme ──→
Hukuki        ──────────────────→ Scraping kararı (S15) ────→
```

---

## 2. Sprint Detayları

---

### Sprint S0 — Mimari Temel + Güvenlik İskeleti

**Süre:** 2 hafta (Hafta 1-2)
**Hedef:** Çalışan monorepo iskeleti, DB şeması, CI/CD, auth altyapısı, güvenlik temeli
**ADR Entegrasyonu:** ADR-0001 (RLS + FORCE), ADR-0008 (Secrets), ADR-0004 iskelet (request_id)

| # | Görev | Effort | Agent Önerisi | Bağımlılık | Dalga |
|---|-------|--------|---------------|------------|-------|
| S0.1 | Monorepo oluştur (Next.js + FastAPI + Docker Compose) | M | claude-devops | — | D1 |
| S0.2 | GitHub Actions CI pipeline (lint, test, type-check) | M | claude-devops | — | D1 |
| S0.3 | PostgreSQL 16 + PostGIS + Redis Docker kurulumu | S | claude-devops | — | D1 |
| S0.4 | `.env.example` + GitHub Actions secrets yapılandırması (ADR-0008) | S | claude-devops | — | D1 |
| S0.5 | SQLAlchemy 2.0 async engine + session factory | M | claude-teknik-lider | S0.3 | D2 |
| S0.6 | Base model (id, timestamps, soft delete) + Alembic init | M | claude-teknik-lider | S0.5 | D2 |
| S0.7 | Core entity modelleri: User, Office, Subscription, Payment | L | claude-kidemli-gelistirici | S0.6 | D2 |
| S0.8 | RLS politikaları (ADR-0001): tüm data-bearing tablolar + FORCE RLS | L | claude-teknik-lider | S0.7 | D3 |
| S0.9 | `app_user` DB rolü oluştur, owner bypass testi | M | claude-teknik-lider | S0.8 | D3 |
| S0.10 | FastAPI middleware: tenant context (SET LOCAL) + request_id (ADR-0004) | M | claude-kidemli-gelistirici | S0.5 | D2 |
| S0.11 | JWT auth (register, login, refresh, me) | L | claude-kidemli-gelistirici | S0.7 | D3 |
| S0.12 | Structured logging: request_id her log satırında | S | codex-junior-gelistirici | S0.10 | D3 |
| S0.13 | Next.js 15 App Router iskeleti + Tailwind + temel layout | M | gemini-kodlayici | — | D1 |
| S0.14 | Landing page + Auth sayfaları (login/register) wireframe → UI | M | gemini-uiux-tasarimci | — | D1 |
| S0.15 | Auth sayfaları frontend implementasyonu | M | gemini-kodlayici | S0.14, S0.11 | D3 |
| S0.16 | Dashboard shell layout (sidebar, header, main area) | M | gemini-kodlayici | S0.13 | D2 |
| S0.17 | **Route yapısı:** (auth), (dashboard), tg/ grupları oluştur | S | gemini-kodlayici | S0.13 | D2 |
| S0.18 | Cross-tenant erişim test case'leri (integration) | M | claude-teknik-lider | S0.8, S0.9 | D4 |
| S0.19 | Hata yanıtlarında request_id alanı (RFC 7807) | S | codex-junior-gelistirici | S0.10 | D3 |
| S0.20 | MinIO Docker kurulum + storage.py S3 client | S | claude-devops | S0.3 | D2 |

**Dalga Yapısı:**
```
D1 (Gün 1-3):  S0.1 ─┐   S0.3 ──┐   S0.4    S0.13 ──┐   S0.14
                S0.2 ─┘          │                    │
D2 (Gün 4-6):        S0.5 ──────┘── S0.6     S0.16 ──┘   S0.17    S0.10    S0.20
D3 (Gün 7-9):              S0.7 ── S0.8    S0.11   S0.12   S0.15   S0.19
D4 (Gün 10):                    S0.9   S0.18
```

**Kabul Kriterleri:**
- [ ] `docker compose up` ile tüm servisler ayağa kalkıyor
- [ ] CI pipeline yeşil (lint + test + type-check)
- [ ] RLS testleri geçiyor: Tenant A, Tenant B verisine erişemiyor
- [ ] JWT auth akışı çalışıyor (register → login → me)
- [ ] request_id tüm log ve hata yanıtlarında mevcut
- [ ] `.env.example` repoda, gerçek secret'lar yalnızca CI/CD'de
- [ ] Next.js dashboard shell render oluyor, auth sayfaları çalışıyor
- [ ] Route yapısı: /(auth), /(dashboard), /tg/ path'leri erişilebilir

**Sprint Çıktıları:**
- Çalışan monorepo iskeleti (frontend + backend + infra)
- 7 core DB tablosu + RLS politikaları
- Auth sistemi (JWT)
- CI/CD pipeline
- Dashboard shell UI

---

### Sprint S1 — Messaging Gateway + Outbox + Payments + OTel

**Süre:** 2 hafta (Hafta 3-4)
**Hedef:** Güvenilir async işlem altyapısı, messaging gateway iskeleti, ödeme webhook güvenliği, tam observability
**ADR Entegrasyonu:** ADR-0002 (Outbox/Inbox), ADR-0005 (Payments), ADR-0004 tam (OTel)

| # | Görev | Effort | Agent Önerisi | Bağımlılık | Dalga |
|---|-------|--------|---------------|------------|-------|
| S1.1 | `outbox_events` tablosu + worker (SELECT FOR UPDATE SKIP LOCKED) | L | claude-kidemli-gelistirici | S0.6 | D1 |
| S1.2 | `inbox_events` tablosu + unique constraint dedup | M | claude-kidemli-gelistirici | S0.6 | D1 |
| S1.3 | Celery + Redis broker kurulumu + task altyapısı | M | claude-devops | S0.3 | D1 |
| S1.4 | Celery hook'ları: request_id propagation (before_task_publish → task_prerun) | M | claude-kidemli-gelistirici | S1.3, S0.10 | D2 |
| S1.5 | OpenTelemetry SDK: FastAPI + SQLAlchemy + httpx instrumentasyonu (ADR-0004 tam) | L | claude-teknik-lider | S0.10 | D1 |
| S1.6 | OTel exporter: Grafana Tempo / Jaeger yapılandırması | M | claude-devops | S1.5 | D2 |
| S1.7 | Messaging Gateway: abstract adapter interface (MessageChannel Protocol) | M | claude-teknik-lider | S0.6 | D1 |
| S1.8 | Telegram Adapter: aiogram 3.x + webhook endpoint | L | claude-kidemli-gelistirici | S1.7 | D2 |
| S1.9 | Telegram Bot: basic echo + /start + auth köprüsü | M | claude-kidemli-gelistirici | S1.8 | D3 |
| S1.10 | Messaging Service: şablon motoru (Jinja2) + kanal yönlendirici | M | claude-kidemli-gelistirici | S1.7 | D2 |
| S1.11 | Payment modeli: Subscription, Payment tabloları güncelleme | M | codex-junior-gelistirici | S0.7 | D1 |
| S1.12 | Payment webhook endpoint + signature verification | M | claude-kidemli-gelistirici | S1.11, S1.2 | D2 |
| S1.13 | payment_timeline + refund/void alanları | S | codex-junior-gelistirici | S1.11 | D2 |
| S1.14 | Outbox worker monitoring: lag metrikleri + stuck event alert | M | claude-devops | S1.1 | D3 |
| S1.15 | Failure/retry politikası: exponential backoff + max retry + DLQ | M | claude-kidemli-gelistirici | S1.1 | D3 |
| S1.16 | Notification modeli + NotificationService (in-app) | M | codex-junior-gelistirici | S0.7 | D2 |
| S1.17 | Frontend: hata ekranlarında request_id gösterimi (UX: "Hata kodu: REQ-xxxxx") | S | gemini-kodlayici | S0.19 | D2 |
| S1.18 | Trace explorer dashboard (Grafana) | S | claude-devops | S1.6 | D3 |
| S1.19 | Integration testler: outbox → worker → send akışı | M | claude-teknik-lider | S1.1, S1.8 | D4 |
| S1.20 | e2e: ödeme → webhook → inbox dedup → status güncelleme | M | claude-teknik-lider | S1.12 | D4 |

**Dalga Yapısı:**
```
D1 (Gün 1-3):  S1.1   S1.2   S1.3   S1.5   S1.7   S1.11
D2 (Gün 4-6):  S1.4   S1.6   S1.8   S1.10  S1.12  S1.13  S1.16  S1.17
D3 (Gün 7-9):  S1.9   S1.14  S1.15  S1.18
D4 (Gün 10):   S1.19  S1.20
```

**Kabul Kriterleri:**
- [ ] Outbox worker: event yazıldı → 5sn içinde işlendi
- [ ] Inbox dedup: aynı event_id iki kez yazılamıyor
- [ ] Telegram bot /start komutu çalışıyor, webhook üzerinden
- [ ] OTel trace: request → DB → external API zinciri Grafana'da görünüyor
- [ ] Payment webhook signature doğrulaması aktif
- [ ] Retry politikası: 3 başarısız deneme → DLQ'ya düşüyor

**Sprint Çıktıları:**
- Outbox/Inbox pattern altyapısı
- Çalışan Telegram bot (echo level)
- Unified Messaging Gateway iskeleti
- OTel tracing pipeline
- Payment webhook güvenliği

---

### Sprint S2 — Veri Toplama Pipeline + Area/Deprem Provenance + Messaging Capability

**Süre:** 2 hafta (Hafta 5-6)
**Hedef:** Dış veri kaynaklarından veri toplama, bölge/deprem veri modeli, messaging capability modeli
**ADR Entegrasyonu:** ADR-0006 (AreaAnalysis provenance + refresh), ADR-0007 (Messaging capability)

| # | Görev | Effort | Agent Önerisi | Bağımlılık | Dalga |
|---|-------|--------|---------------|------------|-------|
| S2.1 | AreaAnalysis + DepremRisk + PriceHistory tablo modelleri | M | codex-junior-gelistirici | S0.6 | D1 |
| S2.2 | Provenance şeması: source, timestamp, version, refresh_status, last_refreshed_at | M | claude-kidemli-gelistirici | S2.1 | D1 |
| S2.3 | TÜİK MEDAŞ API client (konut satış istatistikleri, nüfus) | M | claude-web-arastirmaci | — | D1 |
| S2.4 | TCMB EVDS API client (konut fiyat endeksi, faiz) | M | claude-web-arastirmaci | — | D1 |
| S2.5 | AFAD TDTH API client (deprem tehlike, PGA) | M | claude-web-arastirmaci | — | D1 |
| S2.6 | TKGM Parsel WMS/WFS client (ada/parsel, koordinat) | L | claude-web-arastirmaci | — | D1 |
| S2.7 | Celery beat job: area_refresh (il → ilçe → mahalle katmanlı batch) | L | claude-kidemli-gelistirici | S2.1, S1.3 | D2 |
| S2.8 | Celery beat job: deprem_risk_refresh | M | claude-kidemli-gelistirici | S2.1, S1.3 | D2 |
| S2.9 | Veri normalizasyon pipeline: API response → DB entity | L | claude-kidemli-gelistirici | S2.3, S2.4, S2.5 | D2 |
| S2.10 | Stale data UI badge: "Güncel değil — son güncelleme: [tarih]" | S | gemini-kodlayici | S2.2 | D3 |
| S2.11 | Refresh failure alert: monitoring + bildirim | S | claude-devops | S2.7, S2.8 | D3 |
| S2.12 | Adapter capability modeli: get_capabilities() JSON yapısı (ADR-0007) | M | claude-teknik-lider | S1.7 | D1 |
| S2.13 | Telegram adapter capability tanımlama | S | codex-junior-gelistirici | S2.12 | D2 |
| S2.14 | WhatsApp adapter capability tanımlama (stub — S12'de tam) | S | codex-junior-gelistirici | S2.12 | D2 |
| S2.15 | Property + Valuation + ScrapedListing tablo modelleri | L | claude-kidemli-gelistirici | S0.6 | D1 |
| S2.16 | Property FTS trigger + indeks stratejisi implementasyonu | M | claude-teknik-lider | S2.15 | D2 |
| S2.17 | WhatsApp BSP başvurusu başlat (360dialog) | S | claude-devops | — | D1 |
| S2.18 | İstanbul pilot veri yükleme: 3 ilçe (Kadıköy, Üsküdar, Ataşehir) | M | claude-web-arastirmaci | S2.9 | D3 |
| S2.19 | Integration test: veri toplama → normalize → DB yazma | M | claude-teknik-lider | S2.9 | D3 |

**Dalga Yapısı:**
```
D1 (Gün 1-3):  S2.1  S2.2  S2.3  S2.4  S2.5  S2.6  S2.12  S2.15  S2.17
D2 (Gün 4-7):  S2.7  S2.8  S2.9  S2.13  S2.14  S2.16
D3 (Gün 8-10): S2.10  S2.11  S2.18  S2.19
```

**Kabul Kriterleri:**
- [ ] TÜİK, TCMB, AFAD API'lerinden veri çekiliyor
- [ ] AreaAnalysis tablosunda 3 ilçe verisi mevcut
- [ ] DepremRisk PGA değerleri yüklenmiş
- [ ] Celery beat refresh job'ları zamanlanmış ve çalışıyor
- [ ] Stale data badge UI'da gösteriliyor
- [ ] Adapter capability JSON yapısı çalışıyor
- [ ] Property tablosu FTS indeksleri aktif

**Sprint Çıktıları:**
- 4 dış API client (TÜİK, TCMB, AFAD, TKGM)
- Veri toplama + normalizasyon pipeline
- Bölge/Deprem veri modelleri + provenance
- Property veri modeli + FTS
- Messaging capability modeli

---

### Sprint S3 — AI Değerleme Model v0 + MLOps Altyapısı

**Süre:** 2 hafta (Hafta 7-8)
**Hedef:** LightGBM değerleme modeli v0, MLOps minimum (registry + prediction log), temel UI bileşenleri
**ADR Entegrasyonu:** ADR-0003 (MLOps: ModelRegistry + PredictionLog + drift)

| # | Görev | Effort | Agent Önerisi | Bağımlılık | Dalga |
|---|-------|--------|---------------|------------|-------|
| S3.1 | model_registry tablosu: model_name, version, artifact_url, metrics | M | codex-junior-gelistirici | S0.6 | D1 |
| S3.2 | prediction_log tablosu: input, output, confidence, model_version | M | codex-junior-gelistirici | S0.6 | D1 |
| S3.3 | Eğitim veri seti hazırlama: TKGM + TÜİK + PriceHistory birleştirme | L | claude-web-arastirmaci | S2.18 | D1 |
| S3.4 | Feature engineering: m², oda, kat, yaş, ilçe, mahalle encoding | L | claude-teknik-lider | S3.3 | D2 |
| S3.5 | LightGBM model eğitimi: satılık konut fiyat tahmini | XL | claude-teknik-lider | S3.4 | D2 |
| S3.6 | Model değerlendirme: RMSE, MAE, R², MAPE <%22 hedefi | M | claude-teknik-lider | S3.5 | D3 |
| S3.7 | Inference pipeline: input → preprocess → predict → postprocess | L | claude-kidemli-gelistirici | S3.5 | D3 |
| S3.8 | Otomatik prediction_log yazımı (inference pipeline'da) | M | claude-kidemli-gelistirici | S3.7, S3.2 | D3 |
| S3.9 | model_registry'ye v0 kaydı (artifact_url, metrics) | S | claude-teknik-lider | S3.6, S3.1 | D3 |
| S3.10 | Emsal bulma algoritması: PostGIS distance + benzer özellik sorgusu | L | claude-kidemli-gelistirici | S2.15, S2.16 | D2 |
| S3.11 | Basit drift sinyali: giriş dağılımı + confidence trend izleme | M | claude-teknik-lider | S3.8 | D4 |
| S3.12 | Haftalık metrik raporu (Celery beat → e-posta/log) | S | codex-junior-gelistirici | S3.9, S1.3 | D4 |
| S3.13 | UI: Temel form bileşenleri (Input, Select, Button, Card) + Zod | M | gemini-kodlayici | S0.13 | D1 |
| S3.14 | UI: Değerleme formu wireframe → tasarım | M | gemini-uiux-tasarimci | — | D1 |
| S3.15 | UI: Değerleme formu implementasyonu (React Hook Form + Zod) | M | gemini-kodlayici | S3.13, S3.14 | D2 |
| S3.16 | UI: Değerleme sonuç kartı (min/max/avg, güven skoru) | M | gemini-kodlayici | S3.14 | D3 |
| S3.17 | **Route: /dashboard/valuations → sayfa + layout** | S | gemini-kodlayici | S0.17, S3.15 | D3 |

**Dalga Yapısı:**
```
D1 (Gün 1-3):  S3.1  S3.2  S3.3  S3.13  S3.14
D2 (Gün 4-6):  S3.4  S3.5  S3.10  S3.15
D3 (Gün 7-9):  S3.6  S3.7  S3.8  S3.9  S3.16  S3.17
D4 (Gün 10):   S3.11  S3.12
```

**Kabul Kriterleri:**
- [ ] LightGBM model MAPE <%22 (İstanbul pilot veri seti)
- [ ] Inference pipeline: girdi → tahmin <3 saniye
- [ ] prediction_log'a her tahmin otomatik yazılıyor
- [ ] model_registry'de v0 kaydı mevcut
- [ ] Emsal sorgusu en az 3 benzer mülk dönüyor
- [ ] Değerleme formu UI'da çalışıyor ve sonuç kartı gösteriliyor
- [ ] /dashboard/valuations route'u erişilebilir

**Sprint Çıktıları:**
- LightGBM Değerleme Model v0
- MLOps altyapısı (registry + log + drift)
- Emsal bulma algoritması
- Değerleme UI (form + sonuç kartı)

---

### Sprint S4 — Hukuki Çerçeve + PDF + TR Arama + Seed Ofis

**Süre:** 2 hafta (Hafta 9-10)
**Hedef:** WeasyPrint PDF stabilizasyonu, Türkçe arama kalitesi, seed ofis hazırlığı, hukuki çerçeve
**ADR Entegrasyonu:** ADR-0009a (WeasyPrint), ADR-0009b (TR arama FTS + unaccent + pg_trgm)

| # | Görev | Effort | Agent Önerisi | Bağımlılık | Dalga |
|---|-------|--------|---------------|------------|-------|
| S4.1 | WeasyPrint Docker: apt + pip version pin + Türkçe fontlar (Noto Sans) | M | claude-devops | S0.1 | D1 |
| S4.2 | PDF rapor şablonu: değerleme raporu HTML → PDF | L | claude-kidemli-gelistirici | S4.1, S3.7 | D2 |
| S4.3 | PDF smoke test: örnek doküman + sayfa sayısı/boyut doğrulaması | S | codex-junior-gelistirici | S4.2 | D3 |
| S4.4 | `/health/pdf` healthcheck endpoint | S | codex-junior-gelistirici | S4.1 | D2 |
| S4.5 | `CREATE EXTENSION unaccent` + `CREATE EXTENSION pg_trgm` | S | claude-teknik-lider | S0.3 | D1 |
| S4.6 | Turkish-aware text search config + unaccent + normalize fonksiyonu | M | claude-teknik-lider | S4.5 | D2 |
| S4.7 | Turkish lowercasing doğrulama: İ/ı, I/i varyasyonları test seti | M | claude-teknik-lider | S4.6 | D3 |
| S4.8 | İlan başlık/açıklama trigram index + hybrid sorgu (FTS + trigram similarity) | M | claude-kidemli-gelistirici | S4.6, S2.16 | D3 |
| S4.9 | Arama kalitesi testi: typo/varyasyon listesiyle precision/recall ölçümü | M | claude-teknik-lider | S4.8 | D4 |
| S4.10 | Arama endpoint: `/api/v1/properties/search` (FTS + geo + filtre) | L | claude-kidemli-gelistirici | S4.8 | D3 |
| S4.11 | Seed ofis aday listesi: İstanbul Anadolu Yakası 30 hedef | M | claude-web-arastirmaci | — | D1 |
| S4.12 | Seed ofis iletişim materyali + demo hazırlığı | M | gemini-uiux-tasarimci | S4.11 | D2 |
| S4.13 | KVKK uyum dokümanı taslağı (aydınlatma metni, rıza formu) | M | claude-web-arastirmaci | — | D1 |
| S4.14 | Scraping hukuki araştırma: ToS analizi, emsal kararlar | M | claude-web-arastirmaci | — | D1 |
| S4.15 | EİDS yasal çerçeve araştırma | S | claude-web-arastirmaci | — | D1 |
| S4.16 | UI: Arama bileşeni (autocomplete, filtreler) | M | gemini-kodlayici | S4.10 | D4 |
| S4.17 | **Route: /dashboard/properties → portföy liste sayfası** | S | gemini-kodlayici | S0.17 | D2 |
| S4.18 | UI: Property CRUD form (ilan ekleme/düzenleme) | L | gemini-kodlayici | S3.13, S4.17 | D3 |

**Dalga Yapısı:**
```
D1 (Gün 1-3):  S4.1  S4.5  S4.11  S4.13  S4.14  S4.15
D2 (Gün 4-6):  S4.2  S4.4  S4.6  S4.12  S4.17
D3 (Gün 7-9):  S4.3  S4.7  S4.8  S4.10  S4.18
D4 (Gün 10):   S4.9  S4.16
```

**Kabul Kriterleri:**
- [ ] PDF rapor üretimi çalışıyor (Türkçe karakterler doğru)
- [ ] "satilik" araması "satılık" sonuçlarını dönüyor
- [ ] İ/ı/I/i tüm varyasyonlar doğru normalize ediliyor
- [ ] 30+ seed ofis aday listesi hazır
- [ ] KVKK aydınlatma metni taslağı hazır
- [ ] Scraping hukuki görüş raporu hazır
- [ ] Property CRUD form çalışıyor
- [ ] /dashboard/properties route'u erişilebilir

**Sprint Çıktıları:**
- WeasyPrint PDF pipeline (stabil)
- Türkçe arama altyapısı (unaccent + pg_trgm)
- Property CRUD + arama
- Seed ofis listesi + iletişim materyali
- Hukuki çerçeve dokümanları (KVKK, Scraping, EİDS)

**🚩 GATE G0 (Hafta 10 sonu):** Alpha'ya devam kararı
- AI model v0 çalışıyor ✓
- 20+ seed ofis LOI ✓
- BSP başvurusu yapılmış ✓
- KVKK uyum dokümanı ✓

---

### Sprint S5 — AI Değerleme Motoru v1 (EPIC-01)

**Süre:** 2 hafta (Hafta 11-12)
**Hedef:** Tam fonksiyonel değerleme motoru: emsal karşılaştırma, güven aralığı, PDF rapor, API + UI
**EPIC:** EPIC-01 (AI Değerleme Motoru + Emsal Analiz)

| # | Görev | Effort | Agent Önerisi | Bağımlılık | Dalga |
|---|-------|--------|---------------|------------|-------|
| S5.1 | Değerleme API: POST /api/v1/valuations (kota kontrollü) | M | claude-kidemli-gelistirici | S3.7 | D1 |
| S5.2 | Değerleme API: GET geçmiş, GET detay, GET comparables | M | codex-junior-gelistirici | S5.1 | D2 |
| S5.3 | Emsal analiz: min 3 adet benzer ilan + uzaklık + fiyat farkı hesaplama | L | claude-kidemli-gelistirici | S3.10 | D1 |
| S5.4 | Değerleme PDF raporu: firma logosu, danışman bilgisi, fiyat analizi, bölge trendi | L | claude-kidemli-gelistirici | S4.2, S5.3 | D2 |
| S5.5 | GET /api/v1/valuations/:id/pdf endpoint | S | codex-junior-gelistirici | S5.4 | D3 |
| S5.6 | Model v1 iyileştirme: daha fazla veri + hyperparameter tuning (MAPE <%18 hedef) | L | claude-teknik-lider | S3.5, S2.18 | D1 |
| S5.7 | Güven aralığı hesaplama: %80 olasılıkla X-Y TL arası | M | claude-teknik-lider | S5.6 | D2 |
| S5.8 | Bölge m² fiyat karşılaştırması: ilan fiyatı vs bölge ortalaması | M | claude-kidemli-gelistirici | S2.1 | D2 |
| S5.9 | Fiyat anomali tespiti: sapma uyarısı | M | claude-teknik-lider | S5.8 | D3 |
| S5.10 | UsageQuota modeli: valuations_used sayacı | M | codex-junior-gelistirici | S0.7 | D1 |
| S5.11 | UI: Değerleme sonuç sayfası (emsal listesi + harita pinleri + fiyat grafik) | L | gemini-kodlayici | S3.16 | D2 |
| S5.12 | UI: PDF indirme butonu | S | gemini-kodlayici | S5.5 | D3 |
| S5.13 | UI: Değerleme geçmişi listesi | M | gemini-kodlayici | S5.2 | D3 |
| S5.14 | **Route: /dashboard/valuations/[id] → detay sayfası** | S | gemini-kodlayici | S3.17, S5.11 | D3 |
| S5.15 | Telegram bot: /degerleme komutu → basit değerleme | M | claude-kidemli-gelistirici | S1.9, S5.1 | D3 |
| S5.16 | Kota aşımı UX: kullanıcıya plan yükseltme önerisi | S | gemini-kodlayici | S5.10 | D3 |
| S5.17 | e2e test: form → API → model → emsal → PDF → indirme | L | claude-teknik-lider | S5.5 | D4 |

**Dalga Yapısı:**
```
D1 (Gün 1-3):  S5.1  S5.3  S5.6  S5.10
D2 (Gün 4-6):  S5.2  S5.4  S5.7  S5.8  S5.11
D3 (Gün 7-9):  S5.5  S5.9  S5.12  S5.13  S5.14  S5.15  S5.16
D4 (Gün 10):   S5.17
```

**Kabul Kriterleri:**
- [ ] Değerleme formu → <3 saniye sonuç
- [ ] Min 3 emsal ilan listeleniyor (uzaklık + fiyat farkı)
- [ ] PDF rapor: Türkçe, logo, grafik, danışman bilgisi
- [ ] Model v1 MAPE <%18
- [ ] Kota kontrolü çalışıyor (Starter: 10/ay, Pro: 100/ay)
- [ ] Telegram /degerleme komutu çalışıyor
- [ ] /dashboard/valuations/[id] route'u çalışıyor

**Sprint Çıktıları:**
- Tam fonksiyonel AI Değerleme Motoru v1
- Emsal analiz + PDF rapor
- Kota yönetimi
- Telegram değerleme komutu

---

### Sprint S6 — Bölge Analiz + Harita + Deprem Risk (EPIC-02, 03, 04)

**Süre:** 2 hafta (Hafta 13-14)
**Hedef:** Bölge analiz kartları, harita entegrasyonu, deprem risk skoru — 3 EPIC paralel
**EPIC:** EPIC-02 (Bölge Analiz), EPIC-03 (Harita), EPIC-04 (Deprem Risk)

| # | Görev | Effort | Agent Önerisi | Bağımlılık | Dalga |
|---|-------|--------|---------------|------------|-------|
| S6.1 | Bölge analiz API: GET /areas/:city/:district, GET /areas/.../neighborhood | M | claude-kidemli-gelistirici | S2.1 | D1 |
| S6.2 | Bölge karşılaştırma API: GET /areas/compare?areas=X,Y (Pro+) | M | claude-kidemli-gelistirici | S6.1 | D2 |
| S6.3 | Fiyat trendi API: GET /areas/.../trends (PriceHistory) | M | codex-junior-gelistirici | S2.1 | D1 |
| S6.4 | Deprem Risk API: GET /earthquake/risk, GET /earthquake/building | M | claude-kidemli-gelistirici | S2.1, S2.5 | D1 |
| S6.5 | Deprem bina güvenlik skoru: yaş + kat + zemin → renk kodu (K/S/Y) | M | claude-teknik-lider | S6.4 | D2 |
| S6.6 | MapLibre GL JS entegrasyonu + OpenStreetMap base layer | L | gemini-kodlayici | S0.13 | D1 |
| S6.7 | Harita API: GET /maps/properties?bbox, GET /maps/heatmap, GET /maps/poi | L | claude-kidemli-gelistirici | S2.15 | D1 |
| S6.8 | Harita: portföy pinleri + tıkla → ilan özeti popup | M | gemini-kodlayici | S6.6, S6.7 | D2 |
| S6.9 | Harita: POI katmanları (okul, metro, hastane) açma/kapatma | M | gemini-kodlayici | S6.8 | D3 |
| S6.10 | Harita: yürüme mesafesi hesaplama (POI'ye) | S | gemini-kodlayici | S6.9 | D3 |
| S6.11 | UI: Bölge analiz kartı tasarımı (demografik, fiyat, yatırım skoru) | M | gemini-uiux-tasarimci | — | D1 |
| S6.12 | UI: Bölge analiz kartı implementasyonu | L | gemini-kodlayici | S6.11, S6.1 | D2 |
| S6.13 | UI: Bölge karşılaştırma sayfası (A vs B) | M | gemini-kodlayici | S6.12, S6.2 | D3 |
| S6.14 | UI: Fiyat trendi grafikleri (Chart.js / Recharts) | M | gemini-kodlayici | S6.3 | D2 |
| S6.15 | UI: Deprem risk badge'i (K/S/Y renk kodu + disclaimer) | S | gemini-kodlayici | S6.5 | D2 |
| S6.16 | **Route: /dashboard/areas → bölge analiz sayfası** | S | gemini-kodlayici | S0.17, S6.12 | D3 |
| S6.17 | **Route: /dashboard/maps → harita görünümü** | S | gemini-kodlayici | S0.17, S6.8 | D3 |
| S6.18 | Amortisman süresi hesaplama: kira/satış oranı | S | claude-kidemli-gelistirici | S6.1 | D2 |
| S6.19 | TÜİK demografik veri: nüfus yoğunluğu + yaş dağılımı grafikleri | M | gemini-kodlayici | S2.3 | D3 |

**Dalga Yapısı:**
```
D1 (Gün 1-3):  S6.1  S6.3  S6.4  S6.6  S6.7  S6.11
D2 (Gün 4-6):  S6.2  S6.5  S6.8  S6.12  S6.14  S6.15  S6.18
D3 (Gün 7-9):  S6.9  S6.10  S6.13  S6.16  S6.17  S6.19
D4 (Gün 10):   [Entegrasyon testi + bug fix]
```

**Kabul Kriterleri:**
- [ ] Bölge analiz kartında: ort. m² fiyatı, amortisman, demografik bilgi
- [ ] 2 bölge karşılaştırması çalışıyor (Pro+)
- [ ] Fiyat trendi grafiği 6 aylık veri gösteriyor
- [ ] Harita üzerinde portföy pinleri görünüyor, tıkla → özet
- [ ] POI katmanları açılıp kapatılabiliyor
- [ ] Deprem risk: renk kodu + disclaimer gösteriliyor
- [ ] /dashboard/areas ve /dashboard/maps route'ları çalışıyor

**Sprint Çıktıları:**
- Bölge analiz kartları + karşılaştırma
- MapLibre harita entegrasyonu + POI
- Deprem risk skoru sistemi
- Fiyat trendi grafikleri

---

### Sprint S7 — CRM Temel (EPIC-05)

**Süre:** 2 hafta (Hafta 15-16)
**Hedef:** Müşteri kayıt, iletişim takip, not/etiket, temel eşleştirme bildirimi
**EPIC:** EPIC-05 (CRM Müşteri-Portföy Eşleştirme)

| # | Görev | Effort | Agent Önerisi | Bağımlılık | Dalga |
|---|-------|--------|---------------|------------|-------|
| S7.1 | Customer CRUD API: POST/GET/PATCH/DELETE /customers | M | claude-kidemli-gelistirici | S2.15 | D1 |
| S7.2 | Customer arama/filtre: isim, telefon, tip, bütçe, bölge | M | codex-junior-gelistirici | S7.1 | D2 |
| S7.3 | Customer notes API: POST /customers/:id/notes | S | codex-junior-gelistirici | S7.1 | D2 |
| S7.4 | Customer timeline API: GET /customers/:id/timeline | M | codex-junior-gelistirici | S7.1 | D2 |
| S7.5 | Match (Eşleştirme) CRUD API: GET /matches, PATCH durum | M | claude-kidemli-gelistirici | S7.1 | D2 |
| S7.6 | Eşleştirme algoritması v1: kural tabanlı (fiyat, oda, konum %80+ uyuşma) | L | claude-teknik-lider | S7.5, S2.15 | D2 |
| S7.7 | Eşleştirme tetikleme: yeni Property eklendiğinde otomatik match çalıştır | M | claude-kidemli-gelistirici | S7.6, S1.1 | D3 |
| S7.8 | Eşleştirme bildirimi: in-app + Telegram notification | M | claude-kidemli-gelistirici | S7.7, S1.16 | D3 |
| S7.9 | Quick Add (hızlı kayıt) özelliği: minimal form | S | gemini-kodlayici | S7.1 | D2 |
| S7.10 | UI: Müşteri liste sayfası (tablo + filtreler + lead status badge) | L | gemini-kodlayici | S7.2 | D2 |
| S7.11 | UI: Müşteri detay sayfası (bilgi + notlar + timeline + eşleşmeler) | L | gemini-kodlayici | S7.3, S7.4 | D3 |
| S7.12 | UI: Müşteri form (ekleme/düzenleme) | M | gemini-kodlayici | S3.13 | D1 |
| S7.13 | UI: Eşleştirme listesi + "İlgileniyorum/Geç" aksiyonları | M | gemini-kodlayici | S7.5 | D3 |
| S7.14 | **Route: /dashboard/customers → müşteri listesi** | S | gemini-kodlayici | S0.17, S7.10 | D3 |
| S7.15 | **Route: /dashboard/customers/[id] → müşteri detay** | S | gemini-kodlayici | S7.14, S7.11 | D3 |
| S7.16 | Telegram bot: /musteri komutu → hızlı müşteri kayıt | M | claude-kidemli-gelistirici | S1.9, S7.1 | D3 |
| S7.17 | Lead status yönetimi: cold/warm/hot/converted/lost geçişleri | S | codex-junior-gelistirici | S7.1 | D2 |
| S7.18 | Customer kota kontrolü: plan bazlı müşteri limiti | S | codex-junior-gelistirici | S5.10 | D2 |

**Dalga Yapısı:**
```
D1 (Gün 1-3):  S7.1  S7.12
D2 (Gün 4-6):  S7.2  S7.3  S7.4  S7.5  S7.6  S7.9  S7.10  S7.17  S7.18
D3 (Gün 7-9):  S7.7  S7.8  S7.11  S7.13  S7.14  S7.15  S7.16
D4 (Gün 10):   [Entegrasyon testi + eşleştirme doğrulama]
```

**Kabul Kriterleri:**
- [ ] Müşteri CRUD çalışıyor (ekleme, listeleme, düzenleme, silme)
- [ ] Quick Add: 3 alanlı hızlı kayıt
- [ ] Eşleştirme: yeni portföy → %80+ uyuşma → bildirim
- [ ] Telegram /musteri komutu çalışıyor
- [ ] Lead status pipeline görsel
- [ ] /dashboard/customers ve /dashboard/customers/[id] çalışıyor

**Sprint Çıktıları:**
- CRM müşteri yönetimi (CRUD + arama)
- Kural tabanlı eşleştirme motoru v1
- Eşleştirme bildirimi (in-app + Telegram)
- Müşteri UI (liste + detay + form)

**🚩 GATE G1 (Hafta 16 sonu):** Portföy eşleştirme açılsın mı?
- 50+ portföy yüklenmiş ✓
- Eşleştirme algoritması doğrulanmış ✓

---

### Sprint S8 — AI İlan Asistanı (EPIC-06)

**Süre:** 2 hafta (Hafta 17-18)
**Hedef:** LLM ile ilan metni üretimi, temel fotoğraf iyileştirme, çoklu portal export
**EPIC:** EPIC-06 (AI İlan Asistanı)

| # | Görev | Effort | Agent Önerisi | Bağımlılık | Dalga |
|---|-------|--------|---------------|------------|-------|
| S8.1 | LLM servis: Claude/GPT API entegrasyonu (prompt engineering) | L | claude-teknik-lider | — | D1 |
| S8.2 | İlan metni üretim API: POST /listings/generate-text | M | claude-kidemli-gelistirici | S8.1 | D2 |
| S8.3 | Ton seçenekleri: "Kurumsal", "Samimi", "Acil" prompt varyantları | M | claude-teknik-lider | S8.1 | D2 |
| S8.4 | SEO optimizasyonu: anahtar kelime enjeksiyonu, başlık formatı | M | claude-teknik-lider | S8.2 | D3 |
| S8.5 | Temel fotoğraf iyileştirme: aydınlatma düzeltme, HDR efekti | L | claude-kidemli-gelistirici | — | D1 |
| S8.6 | Fotoğraf iyileştirme API: POST /listings/enhance-photo | M | claude-kidemli-gelistirici | S8.5 | D2 |
| S8.7 | Fotoğraf yükleme: multipart upload → MinIO + thumbnail | M | codex-junior-gelistirici | S0.20 | D1 |
| S8.8 | Çoklu portal export: Sahibinden, Hepsiemlak format şablonları | M | codex-junior-gelistirici | S8.2 | D3 |
| S8.9 | UsageQuota: listings_used, photos_used sayaçları | S | codex-junior-gelistirici | S5.10 | D1 |
| S8.10 | UI: İlan asistanı tasarım (özellik girişi → önizleme → düzenleme) | M | gemini-uiux-tasarimci | — | D1 |
| S8.11 | UI: İlan asistanı implementasyonu | L | gemini-kodlayici | S8.10, S8.2 | D2 |
| S8.12 | UI: Ton seçimi + sonuç önizleme + kopyalama | M | gemini-kodlayici | S8.11, S8.3 | D3 |
| S8.13 | UI: Fotoğraf yükleme + iyileştirme önce/sonra karşılaştırma | M | gemini-kodlayici | S8.6, S8.7 | D3 |
| S8.14 | **Route: /dashboard/listings → ilan asistanı sayfası** | S | gemini-kodlayici | S0.17, S8.11 | D3 |
| S8.15 | Telegram bot: fotoğraf gönder → iyileştir komutu | M | claude-kidemli-gelistirici | S1.9, S8.6 | D3 |
| S8.16 | Export API: POST /listings/export (format seçimli) | S | codex-junior-gelistirici | S8.8 | D4 |

**Dalga Yapısı:**
```
D1 (Gün 1-3):  S8.1  S8.5  S8.7  S8.9  S8.10
D2 (Gün 4-6):  S8.2  S8.3  S8.6  S8.11
D3 (Gün 7-9):  S8.4  S8.8  S8.12  S8.13  S8.14  S8.15
D4 (Gün 10):   S8.16
```

**Kabul Kriterleri:**
- [ ] LLM ile ilan metni üretimi çalışıyor (<5 saniye)
- [ ] 3 ton seçeneği mevcut ve farklı çıktı üretiyor
- [ ] Fotoğraf iyileştirme: aydınlatma düzeltme görsel olarak fark edilir
- [ ] Çoklu portal export (en az 2 format)
- [ ] Pro+ kota kontrolü çalışıyor
- [ ] /dashboard/listings route'u çalışıyor

**Sprint Çıktıları:**
- AI İlan Asistanı (metin + fotoğraf)
- Fotoğraf yükleme pipeline
- Portal export şablonları

---

### Sprint S9 — Portföy Vitrin + Kredi Hesaplayıcı (EPIC-07, 08)

**Süre:** 2 hafta (Hafta 19-20)
**Hedef:** Danışman portföy vitrini (public link), kredi hesaplayıcı, temel eşleştirme motoru genişletme
**EPIC:** EPIC-07 (Portföy Vitrin + Temel Eşleştirme), EPIC-08 (Kredi Hesaplayıcı)

| # | Görev | Effort | Agent Önerisi | Bağımlılık | Dalga |
|---|-------|--------|---------------|------------|-------|
| S9.1 | Vitrin modeli: seçili ilanlar, danışman bilgi, public slug | M | claude-kidemli-gelistirici | S2.15 | D1 |
| S9.2 | Vitrin API: oluştur/güncelle/sil + public GET (slug ile) | M | claude-kidemli-gelistirici | S9.1 | D2 |
| S9.3 | Vitrin public sayfası: responsive, mobil uyumlu, danışman iletişim sticky | L | gemini-kodlayici | S9.2 | D3 |
| S9.4 | **Route: /vitrin/[slug] → public vitrin sayfası (SSR/SEO)** | M | gemini-kodlayici | S9.3 | D3 |
| S9.5 | Vitrin tasarımı: wireframe + UI | M | gemini-uiux-tasarimci | — | D1 |
| S9.6 | Vitrin yönetim UI: ilan seçme, sıralama, önizleme | M | gemini-kodlayici | S9.5, S9.2 | D3 |
| S9.7 | **Route: /dashboard/network → portföy ağı sayfası (stub)** | S | gemini-kodlayici | S0.17 | D2 |
| S9.8 | Portföy paylaşım: is_shared toggle + share_visibility ayarı | M | claude-kidemli-gelistirici | S2.15 | D2 |
| S9.9 | Paylaşım ağı listesi: GET /properties/network (shared=true) | M | codex-junior-gelistirici | S9.8 | D3 |
| S9.10 | Kredi hesaplama formülleri: taksit, toplam geri ödeme, amortisman tablosu | M | codex-junior-gelistirici | — | D1 |
| S9.11 | Kredi API: POST /calculator/credit, GET /calculator/rates | S | codex-junior-gelistirici | S9.10 | D2 |
| S9.12 | Banka faiz oranları: TCMB ortalama + manual override | S | codex-junior-gelistirici | S2.4 | D2 |
| S9.13 | UI: Kredi hesaplayıcı tasarımı | S | gemini-uiux-tasarimci | — | D1 |
| S9.14 | UI: Kredi hesaplayıcı implementasyonu + banka karşılaştırma | M | gemini-kodlayici | S9.13, S9.11 | D3 |
| S9.15 | **Route: /dashboard/calculator → kredi hesaplayıcı** | S | gemini-kodlayici | S0.17, S9.14 | D3 |
| S9.16 | Telegram bot: /kredi komutu → basit kredi hesaplama | S | claude-kidemli-gelistirici | S1.9, S9.10 | D3 |
| S9.17 | WhatsApp click-to-chat: portföy kartından "WhatsApp'a Paylaş" butonu (`wa.me` link oluşturucu) | S | gemini-kodlayici | S9.3 | D3 |
| S9.18 | Manuel link oluşturucu: seçili ilanlar → toplu paylaşım linki + kopyala butonu (opsiyonel) | S | codex-junior-gelistirici | S9.17 | D3 |

**Dalga Yapısı:**
```
D1 (Gün 1-3):  S9.1  S9.5  S9.10  S9.13
D2 (Gün 4-6):  S9.2  S9.7  S9.8  S9.11  S9.12
D3 (Gün 7-9):  S9.3  S9.4  S9.6  S9.9  S9.14  S9.15  S9.16
D4 (Gün 10):   [Entegrasyon testi]
```

**Kabul Kriterleri:**
- [ ] Vitrin public sayfası: responsive, danışman bilgi sticky
- [ ] Vitrin paylaşım linki oluşturuluyor ve erişilebilir
- [ ] Portföy paylaşım ağına ilan açma/kapama çalışıyor
- [ ] Kredi hesaplayıcı: tutar + vade + faiz → taksit tablosu
- [ ] /vitrin/[slug], /dashboard/network, /dashboard/calculator route'ları çalışıyor
- [ ] WhatsApp click-to-chat: portföy kartından "WhatsApp'a Paylaş" butonu çalışıyor (native WA açılıyor)

**Sprint Çıktıları:**
- Portföy vitrin sistemi (public link + yönetim)
- Portföy paylaşım altyapısı (temel)
- Kredi hesaplayıcı
- WhatsApp click-to-chat (Starter/Pro — BSP gerektirmez)

---

### Sprint S10 — Telegram Tam Entegrasyon (EPIC-09)

**Süre:** 2 hafta (Hafta 21-22)
**Hedef:** Telegram Bot tam fonksiyon, Mini App dashboard, tüm özelliklerin Telegram'a bağlanması
**EPIC:** EPIC-09 (Telegram Bot + Mini App)

| # | Görev | Effort | Agent Önerisi | Bağımlılık | Dalga |
|---|-------|--------|---------------|------------|-------|
| S10.1 | Telegram Mini App: /tg layout (üst bar yok, alt navigasyon) + @tma.js/sdk | L | gemini-kodlayici | S0.17 | D1 |
| S10.2 | Mini App auth köprüsü: Telegram initData → JWT token | M | claude-kidemli-gelistirici | S0.11, S1.8 | D1 |
| S10.3 | Mini App dashboard: özet kartlar (portföy, müşteri, eşleşme, bildirim sayıları) | L | gemini-kodlayici | S10.1, S10.2 | D2 |
| S10.4 | Mini App: değerleme formu (mobil uyumlu) | M | gemini-kodlayici | S10.3, S5.11 | D3 |
| S10.5 | Mini App: CRM liste + hızlı kayıt | M | gemini-kodlayici | S10.3, S7.10 | D3 |
| S10.6 | Bot conversation flow: fotoğraf + konum → ilan taslağı oluşturma | XL | claude-kidemli-gelistirici | S1.9, S8.2, S8.7 | D2 |
| S10.7 | Bot: bildirim entegrasyonu (eşleşme, fiyat değişikliği, rapor) | L | claude-kidemli-gelistirici | S7.8, S1.16 | D2 |
| S10.8 | Bot: inline keyboard ile CRM aksiyonları (eşleşme → ilgileniyorum/geç) | M | claude-kidemli-gelistirici | S7.13 | D3 |
| S10.9 | Bot: /portfoy komutu → portföy listesi + arama | M | codex-junior-gelistirici | S1.9, S2.15 | D2 |
| S10.10 | Bot: /rapor komutu → günlük/haftalık özet | M | codex-junior-gelistirici | S1.9 | D2 |
| S10.11 | Bot: gün sonu ofis raporu (20:00 otomatik — Celery beat) | M | claude-kidemli-gelistirici | S10.10, S1.3 | D3 |
| S10.12 | Bot: dosya paylaşımı (PDF rapor, fotoğraf) | S | codex-junior-gelistirici | S1.9 | D2 |
| S10.13 | Bot error handling: kullanıcı dostu hata mesajları + request_id | S | codex-junior-gelistirici | S0.12 | D3 |
| S10.14 | **Route: /tg/page → Mini App dashboard** | S | gemini-kodlayici | S10.1, S10.3 | D3 |
| S10.15 | **Route: /tg/valuation → Mini App değerleme** | S | gemini-kodlayici | S10.4 | D3 |
| S10.16 | **Route: /tg/crm → Mini App CRM** | S | gemini-kodlayici | S10.5 | D3 |
| S10.17 | Bot komut menüsü: Telegram BotFather komut listesi güncelleme | S | codex-junior-gelistirici | S10.6 | D4 |
| S10.18 | e2e test: fotoğraf gönder → ilan taslağı → düzenle → kaydet | L | claude-teknik-lider | S10.6 | D4 |

**Dalga Yapısı:**
```
D1 (Gün 1-3):  S10.1  S10.2
D2 (Gün 4-6):  S10.3  S10.6  S10.7  S10.9  S10.10  S10.12
D3 (Gün 7-9):  S10.4  S10.5  S10.8  S10.11  S10.13  S10.14  S10.15  S10.16
D4 (Gün 10):   S10.17  S10.18
```

**Kabul Kriterleri:**
- [ ] Mini App Telegram içinden açılıyor, auth çalışıyor
- [ ] Bot conversation flow: fotoğraf + konum → ilan taslağı (kesintisiz)
- [ ] Eşleştirme bildirimi Telegram'dan geliyor
- [ ] Gün sonu rapor otomatik geliyor (20:00)
- [ ] Mini App'te değerleme ve CRM kullanılabiliyor
- [ ] /tg/* route'ları çalışıyor
- [ ] Bot mesajlaşma başarı oranı %95+

**Sprint Çıktıları:**
- Telegram Mini App (dashboard + değerleme + CRM)
- Telegram Bot tam fonksiyon (10+ komut)
- Bildirim entegrasyonu
- Otomatik raporlama

---

### Sprint S11 — QA + Stabilizasyon + Alpha Lansman

**Süre:** 2 hafta (Hafta 23-24)
**Hedef:** Bug fix, performans optimizasyonu, güvenlik taraması, seed ofis onboarding, Alpha lansman
**EPIC:** Cross-cutting (tüm Alpha özellikleri)

| # | Görev | Effort | Agent Önerisi | Bağımlılık | Dalga |
|---|-------|--------|---------------|------------|-------|
| S11.1 | QA test senaryoları: tüm Alpha özellikleri için kapsamlı test planı | L | claude-qa-senaryo | Tüm S5-S10 | D1 |
| S11.2 | Fonksiyonel test çalıştırma: test planına göre | XL | gemini-test-muhendisi | S11.1 | D2 |
| S11.3 | Bug fix sprint: kritik ve yüksek öncelikli bug'lar | XL | claude-kidemli-gelistirici + gemini-kodlayici | S11.2 | D3 |
| S11.4 | Performans optimizasyonu: DB sorgu analizi, N+1 tespiti, cache | L | claude-teknik-lider | S11.2 | D3 |
| S11.5 | Güvenlik taraması: OWASP Top 10 kontrol listesi | L | claude-guvenlik-analisti | — | D1 |
| S11.6 | Güvenlik bulguları düzeltme | M | claude-kidemli-gelistirici | S11.5 | D3 |
| S11.7 | Responsive test: mobil + tablet + desktop | M | claude-misafir-tester | S11.2 | D3 |
| S11.8 | UX mikro-kopya revizyonu: Türkçe dil kontrolü, CTA metinleri | M | claude-ux-mikrokopi | S11.2 | D2 |
| S11.9 | Seed ofis onboarding: 30 ofis → portföy yükleme + eğitim | L | claude-web-arastirmaci | S4.12 | D2 |
| S11.10 | Staging deploy + smoke test | M | claude-devops | S11.3 | D4 |
| S11.11 | Production deploy pipeline hazırlığı | M | claude-devops | S11.10 | D4 |
| S11.12 | Monitoring dashboard: Grafana alert'leri + SLA tanımları | M | claude-devops | — | D1 |
| S11.13 | Kullanıcı dokümanı: temel kullanım kılavuzu (Telegram bot + Web) | M | codex-junior-gelistirici | S11.2 | D3 |
| S11.14 | Alpha lansman: production deploy + seed ofis açılışı | L | claude-devops | S11.11 | D4 |
| S11.15 | Landing page SEO + meta tag'ler | S | gemini-kodlayici | — | D2 |

**Dalga Yapısı:**
```
D1 (Gün 1-2):  S11.1  S11.5  S11.12
D2 (Gün 3-5):  S11.2  S11.8  S11.9  S11.15
D3 (Gün 6-8):  S11.3  S11.4  S11.6  S11.7  S11.13
D4 (Gün 9-10): S11.10  S11.11  S11.14
```

**Kabul Kriterleri:**
- [ ] Kritik bug sayısı: 0
- [ ] Yüksek öncelikli bug: ≤3 (bilinen, workaround mevcut)
- [ ] OWASP Top 10: tüm maddeler kontrol edildi
- [ ] Sayfa yükleme süresi <3 saniye (desktop), <5 saniye (mobil)
- [ ] 30+ seed ofis onboard edildi
- [ ] Production deploy başarılı
- [ ] Monitoring alert'leri aktif

**Sprint Çıktıları:**
- 🚀 **ALPHA LANSMAN**
- 30+ seed ofis aktif
- Starter + Pro kademeleri açık
- 9 core özellik çalışıyor

**🚩 GATE G2 (Hafta 24 sonu):** Beta'ya geçiş kararı
- 100+ aktif kullanıcı ✓
- 50+ ücretli abone ✓
- NPS > 40 ✓
- Aylık churn < %10 ✓

---

### Sprint S12 — WhatsApp Cloud API / Elite (EPIC-10)

**Süre:** 2 hafta (Hafta 25-26)
**Hedef:** WhatsApp Cloud API (BSP) tam entegrasyon — Elite plan. Template mesajlar, çift yönlü iletişim, delivery/read takibi. *Not: Starter/Pro click-to-chat Alpha'da S9'da tamamlanmıştır.*
**EPIC:** EPIC-10 (WhatsApp Cloud API — Elite)
**Dış Bağımlılık:** BSP onayı (360dialog)

| # | Görev | Effort | Agent Önerisi | Bağımlılık | Dalga |
|---|-------|--------|---------------|------------|-------|
| S12.1 | WhatsApp Adapter: 360dialog Cloud API entegrasyonu | L | claude-kidemli-gelistirici | S1.7, S2.14 | D1 |
| S12.2 | WhatsApp webhook endpoint: POST /api/v1/whatsapp/webhook | M | claude-kidemli-gelistirici | S12.1 | D2 |
| S12.3 | Template mesaj yönetimi: oluşturma + Meta onay takibi | M | claude-kidemli-gelistirici | S12.1 | D2 |
| S12.4 | Template şablonları: ilan paylaşım kartı, randevu hatırlatma, eşleşme bildirimi | M | codex-junior-gelistirici | S12.3 | D3 |
| S12.5 | Çift yönlü iletişim: gelen mesaj → Conversation → agent'a bildirim | L | claude-kidemli-gelistirici | S12.2 | D3 |
| S12.6 | Maliyet optimizasyonu: Telegram (0 TL) > WhatsApp (0.05+ TL) yönlendirme | M | claude-kidemli-gelistirici | S12.1 | D3 |
| S12.7 | WhatsApp Cloud API kota yönetimi: Elite plan mesaj limiti (50/ay) | M | codex-junior-gelistirici | S5.10 | D2 |
| S12.8 | Gönderim loglama: Message tablosuna WhatsApp mesaj kaydı | S | codex-junior-gelistirici | S12.1 | D2 |
| S12.9 | UI: "WhatsApp'tan Gönder" butonu (ilan detay sayfasında) | M | gemini-kodlayici | S12.1 | D3 |
| S12.10 | UI: Mesajlaşma inbox (Telegram + WhatsApp birleşik görünüm) | L | gemini-kodlayici | S12.5 | D3 |
| S12.11 | **Route: /dashboard/messages → mesajlaşma inbox** | S | gemini-kodlayici | S0.17, S12.10 | D3 |
| S12.12 | Opt-in/opt-out yönetimi: KVKK uyumlu rıza | S | claude-kidemli-gelistirici | S12.1 | D2 |
| S12.13 | Fallback zinciri testi: Telegram fail → WhatsApp → SMS | M | claude-teknik-lider | S12.1 | D4 |

**Kabul Kriterleri:**
- [ ] WhatsApp template mesaj gönderilip teslim ediliyor
- [ ] Çift yönlü iletişim: gelen mesaj agent'a bildirim
- [ ] Maliyet yönlendirmesi: default Telegram, override WhatsApp
- [ ] Fallback zinciri çalışıyor
- [ ] KVKK opt-in/opt-out mevcut

---

### Sprint S13 — EİDS Hibrit Doğrulama (EPIC-11)

**Süre:** 2 hafta (Hafta 27-28)
**Hedef:** Manuel numara giriş + OCR belge doğrulama + "Doğrulanmış İlan" rozeti
**EPIC:** EPIC-11 (EİDS Hibrit Doğrulama)

| # | Görev | Effort | Agent Önerisi | Bağımlılık | Dalga |
|---|-------|--------|---------------|------------|-------|
| S13.1 | Tesseract + OpenCV kurulumu (Docker) | M | claude-devops | S0.1 | D1 |
| S13.2 | OCR pipeline: belge fotoğrafı → metin çıkarma → numara parse | L | claude-kidemli-gelistirici | S13.1 | D2 |
| S13.3 | EİDS doğrulama API: POST /eids/verify (manuel), POST /eids/upload-document (OCR) | M | claude-kidemli-gelistirici | S13.2 | D3 |
| S13.4 | Admin onay akışı: pending → verified/rejected + rejection_reason | M | codex-junior-gelistirici | S13.3 | D3 |
| S13.5 | "Doğrulanmış İlan" rozet sistemi: property.eids_status badge | S | gemini-kodlayici | S13.3 | D3 |
| S13.6 | UI: EİDS doğrulama formu (numara giriş + belge yükleme) | M | gemini-kodlayici | S13.3 | D3 |
| S13.7 | **Route: /dashboard/eids → doğrulama sayfası** | S | gemini-kodlayici | S0.17 | D2 |
| S13.8 | Audit log: tüm EİDS işlemleri kayıt altında | S | codex-junior-gelistirici | S13.3 | D3 |

**Kabul Kriterleri:**
- [ ] OCR ile belge numarası okunuyor
- [ ] Admin onay akışı çalışıyor
- [ ] "Doğrulanmış İlan" rozeti görünüyor

---

### Sprint S14 — Portföy Paylaşım Ağı Aktif (EPIC-12)

**Süre:** 2 hafta (Hafta 29-30)
**Hedef:** Gelişmiş eşleştirme, aktif paylaşım, temel komisyon akışı, moderasyon
**EPIC:** EPIC-12 (Portföy Paylaşım Ağı Aktif)

| # | Görev | Effort | Agent Önerisi | Bağımlılık | Dalga |
|---|-------|--------|---------------|------------|-------|
| S14.1 | Gelişmiş eşleştirme: ML tabanlı skor (kural tabanlından geçiş) | XL | claude-teknik-lider | S7.6 | D1 |
| S14.2 | Cross-office eşleştirme: "Paylaşıma Aç" → anonim bildirim (Pro+) | L | claude-kidemli-gelistirici | S14.1, S9.8 | D2 |
| S14.3 | Komisyon akışı: anlaşma önerisi + kabul/red + tutar girişi | L | claude-kidemli-gelistirici | S14.2 | D3 |
| S14.4 | Gizlilik: müşteri verisi gizli, sadece "Eşleşme var" bildirimi | M | claude-kidemli-gelistirici | S14.2 | D2 |
| S14.5 | Moderasyon paneli: raporla/engelle, güven skoru | M | codex-junior-gelistirici | S14.2 | D3 |
| S14.6 | UI: Portföy ağı feed (eşleşmeler, paylaşılan ilanlar) | L | gemini-kodlayici | S14.2 | D3 |
| S14.7 | UI: Komisyon akışı UI (anlaşma + durum takibi) | M | gemini-kodlayici | S14.3 | D4 |
| S14.8 | **Route: /dashboard/network güncelleme** | S | gemini-kodlayici | S9.7, S14.6 | D3 |
| S14.9 | Telegram bot: ağ bildirimleri + eşleşme aksiyonları | M | claude-kidemli-gelistirici | S14.2, S10.7 | D3 |

**Kabul Kriterleri:**
- [ ] Cross-office eşleştirme anonim bildirim ile çalışıyor
- [ ] Sadece Pro+ kullanıcılar bildirim alıyor
- [ ] Müşteri verisi gizli kalıyor
- [ ] Komisyon akışı: öneri → kabul → tamamla

---

### Sprint S15 — Çoklu Site Scraping (EPIC-13)

**Süre:** 2 hafta (Hafta 31-32)
**Hedef:** Koşullu scraping: ortaklık varsa API, yoksa sınırlı aggregate istatistik
**EPIC:** EPIC-13 (Çoklu Site Scraping)
**Dış Bağımlılık:** Hukuki onay (S4.14)

| # | Görev | Effort | Agent Önerisi | Bağımlılık | Dalga |
|---|-------|--------|---------------|------------|-------|
| S15.1 | Scraping altyapısı: Scrapy + proxy pool yönetimi | L | claude-kidemli-gelistirici | — | D1 |
| S15.2 | Sahibinden parser: aggregate fiyat/özellik verisi (kişisel veri yok) | L | claude-kidemli-gelistirici | S15.1 | D2 |
| S15.3 | Hepsiemlak parser | M | codex-junior-gelistirici | S15.1 | D2 |
| S15.4 | Veri normalizasyon + deduplication pipeline | L | claude-teknik-lider | S15.2 | D3 |
| S15.5 | ScrapedListing → PriceHistory aggregation | M | claude-teknik-lider | S15.4 | D3 |
| S15.6 | Bölge bazlı ort. m² fiyat istatistikleri | M | codex-junior-gelistirici | S15.5 | D4 |
| S15.7 | UI: Pazar istatistikleri dashboard (Elite) | L | gemini-kodlayici | S15.6 | D4 |
| S15.8 | Rate limiting + anti-detection: respectful scraping | M | claude-kidemli-gelistirici | S15.1 | D2 |

**🚩 GATE G3 (Hafta 30):** Scraping açılsın mı?
- Hukuki çerçeve tamam ✓
- Ortaklık veya hukuki görüş ✓

---

### Sprint S16 — Gelişmiş AI Fotoğraf (EPIC-14)

**Süre:** 2 hafta (Hafta 33-34)
**Hedef:** Virtual staging, dekorasyon önerisi, gelişmiş fotoğraf işleme
**EPIC:** EPIC-14 (Gelişmiş AI Fotoğraf)

| # | Görev | Effort | Agent Önerisi | Bağımlılık | Dalga |
|---|-------|--------|---------------|------------|-------|
| S16.1 | Virtual staging API: Stable Diffusion / DALL-E entegrasyonu | XL | claude-teknik-lider | S8.5 | D1 |
| S16.2 | POST /listings/virtual-staging endpoint (Elite) | M | claude-kidemli-gelistirici | S16.1 | D2 |
| S16.3 | Orijinal vs işlenmiş yan yana gösterim + "Sanal Düzenleme" filigranı | M | gemini-kodlayici | S16.2 | D3 |
| S16.4 | GPU maliyet kontrolü: per-image maliyet sınırı + kota | M | claude-teknik-lider | S16.1 | D2 |
| S16.5 | Akıllı Fiyat Önerisi: survival analysis + "hızlı satış" vs "max getiri" | L | claude-teknik-lider | S5.6 | D1 |
| S16.6 | Fiyat önerisi API + UI | M | claude-kidemli-gelistirici + gemini-kodlayici | S16.5 | D3 |

---

### Sprint S17 — Ofis Yönetim Paneli (EPIC-15)

**Süre:** 2 hafta (Hafta 35-36)
**Hedef:** Elite kademe: çoklu kullanıcı yönetimi, danışman performans KPI, komisyon hesabı, raporlama
**EPIC:** EPIC-15 (Ofis Yönetim Paneli + Raporlama)

| # | Görev | Effort | Agent Önerisi | Bağımlılık | Dalga |
|---|-------|--------|---------------|------------|-------|
| S17.1 | Multi-user yönetim: davet, rol atama, aktif/pasif | L | claude-kidemli-gelistirici | S0.11 | D1 |
| S17.2 | Danışman performans KPI: satış hunisi, gösterimler, kapatmalar | L | claude-teknik-lider | S7.1 | D1 |
| S17.3 | Komisyon hesaplama motoru: oran + tutar + paylaşım | M | claude-kidemli-gelistirici | S14.3 | D2 |
| S17.4 | Rapor API: GET /reports/office-summary, GET /reports/agent-performance | M | codex-junior-gelistirici | S17.2 | D2 |
| S17.5 | UI: Ofis yönetim dashboard (danışman listesi + performans grafikleri) | L | gemini-kodlayici | S17.4 | D3 |
| S17.6 | UI: Haftalık otomatik rapor (Celery beat → e-posta + Telegram) | M | codex-junior-gelistirici | S17.4, S1.3 | D3 |
| S17.7 | **Route: /dashboard/reports → raporlama sayfası (Elite)** | S | gemini-kodlayici | S0.17, S17.5 | D3 |
| S17.8 | Tarih aralığına göre filtreleme | S | codex-junior-gelistirici | S17.4 | D3 |

---

### Sprint S18 — QA + Güvenlik + Beta Lansman

**Süre:** 2 hafta (Hafta 37-38)
**Hedef:** Tam QA döngüsü, penetrasyon testi, performans testi, genel lansman
**EPIC:** Cross-cutting (tüm Beta özellikleri)

| # | Görev | Effort | Agent Önerisi | Bağımlılık | Dalga |
|---|-------|--------|---------------|------------|-------|
| S18.1 | Tam QA test planı: Alpha + Beta özellikleri | L | claude-qa-senaryo | Tüm | D1 |
| S18.2 | Fonksiyonel test çalıştırma | XL | gemini-test-muhendisi | S18.1 | D2 |
| S18.3 | Penetrasyon testi: OWASP + RLS + WhatsApp webhook | L | claude-guvenlik-analisti | — | D1 |
| S18.4 | Performans/yük testi: 500+ eşzamanlı kullanıcı simülasyonu | L | claude-devops | — | D1 |
| S18.5 | Bug fix sprint: tüm kritik/yüksek bulgular | XL | claude-kidemli-gelistirici + gemini-kodlayici | S18.2, S18.3 | D3 |
| S18.6 | Performans optimizasyonu: darboğaz giderme | L | claude-teknik-lider | S18.4 | D3 |
| S18.7 | Responsive + cross-browser test | M | claude-misafir-tester | S18.2 | D3 |
| S18.8 | UX son kontrolü + Türkçe dil geçişi | M | claude-ux-mikrokopi | S18.2 | D2 |
| S18.9 | Production deploy: blue-green veya canary | L | claude-devops | S18.5 | D4 |
| S18.10 | Beta lansman: genel erişim açılışı | M | claude-devops | S18.9 | D4 |

**Kabul Kriterleri (Beta Go/No-Go — G4):**
- [ ] 500+ aktif kullanıcı
- [ ] Ünit economics pozitif
- [ ] ARPU ≥ 600 TL
- [ ] Churn < %8
- [ ] Güvenlik taraması temiz
- [ ] Portföy ağında 80+ ofis, 50+ eşleştirme

---

## 3. Dalga Sistemi

### 3.1 Dalga Felsefesi

Her sprint 4 dalgaya (D1-D4) bölünür. Tek kişi + AI agent modeli için dalga sistemi şöyle çalışır:

| Dalga | Gün | Amaç | Paralellik Stratejisi |
|-------|-----|------|----------------------|
| **D1** | 1-3 | Temel + bağımsız görevler | Maks paralel: 4-6 agent aynı anda |
| **D2** | 4-6 | D1 çıktılarına bağlı görevler | Orta paralel: 3-4 agent |
| **D3** | 7-9 | Entegrasyon + UI + route | Yoğun: hepsini birleştir |
| **D4** | 10 | Test + doğrulama + bug fix | Seri: entegrasyon testi |

### 3.2 Bağımlılık Grafiği (Sprint Arası)

```
S0 ─────────────────────────────────────────────────────────────────────────
 ├──→ S1 (Outbox, Messaging, OTel)
 │     ├──→ S2 (Veri Pipeline, Capability)
 │     │     ├──→ S3 (AI Model, MLOps)
 │     │     │     └──→ S5 (Değerleme v1) ──→ S6 (Bölge, Harita, Deprem)
 │     │     │                                  │
 │     │     └──→ S4 (PDF, TR Arama) ──────────┘
 │     │
 │     ├──→ S7 (CRM) ──→ S9 (Vitrin, Kredi)
 │     │                   │
 │     └──→ S10 (Telegram Tam) ←──────────┤
 │                                          │
 └──→ S8 (AI İlan Asistanı) ───────────────┘
                                              │
S11 (Alpha QA) ←──────────────────────────────┘

S12 (WhatsApp) ←── S1 (Gateway)
S13 (EİDS) ←── S0 (DB)
S14 (Portföy Ağı) ←── S7 (CRM) + S9 (Vitrin)
S15 (Scraping) ←── S4 (Hukuki)
S16 (AI Fotoğraf) ←── S8 (İlan Asistanı)
S17 (Ofis Yönetim) ←── S7 (CRM)
S18 (Beta QA) ←── Tüm
```

### 3.3 Kritik Yol

```
S0 → S1 → S2 → S3 → S5 → S6 → S7 → S10 → S11 (Alpha) → S14 → S18 (Beta)
 │                                    │
 └──── Paralel: S8 ──────────────────┘

Kritik yol süresi: 24 hafta (Alpha) + 14 hafta (Beta) = 38 hafta
Sıkıştırma potansiyeli: S7-S8 paralel çalıştırılabilir → 2 hafta kazanç
```

---

## 4. Agent Yük Dağılımı

### 4.1 Sprint Bazlı Görev Sayısı

| Agent | S0 | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 | S9 | S10 | S11 | S12 | S13 | S14 | S15 | S16 | S17 | S18 | **Toplam** |
|-------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:----------:|
| **claude-teknik-lider** | 5 | 3 | 2 | 5 | 4 | 3 | 1 | 1 | 1 | — | 1 | 1 | 1 | — | 1 | 2 | 2 | 1 | 1 | **35** |
| **claude-kidemli-gelistirici** | 3 | 7 | 3 | 2 | 2 | 3 | 3 | 4 | 3 | 3 | 5 | 1 | 5 | 2 | 3 | 2 | 1 | 2 | 1 | **55** |
| **gemini-kodlayici** | 4 | 1 | 1 | 3 | 2 | 4 | 9 | 5 | 4 | 4 | 6 | 1 | 3 | 2 | 2 | 1 | 1 | 2 | — | **55** |
| **codex-junior-gelistirici** | 2 | 3 | 3 | 2 | 1 | 2 | 1 | 3 | 3 | 4 | 3 | 1 | 2 | 1 | 1 | 1 | — | 3 | — | **36** |
| **claude-devops** | 4 | 3 | 1 | — | 1 | — | — | — | — | — | — | 3 | — | 1 | — | — | — | — | 3 | **16** |
| **claude-web-arastirmaci** | — | — | 5 | 1 | 3 | — | — | — | — | — | — | 1 | — | — | — | — | — | — | — | **10** |
| **gemini-uiux-tasarimci** | 1 | — | — | 1 | 1 | — | 1 | — | 1 | 1 | — | — | — | — | — | — | — | — | — | **6** |
| **claude-qa-senaryo** | — | — | — | — | — | — | — | — | — | — | — | 1 | — | — | — | — | — | — | 1 | **2** |
| **gemini-test-muhendisi** | — | — | — | — | — | — | — | — | — | — | — | 1 | — | — | — | — | — | — | 1 | **2** |
| **claude-guvenlik-analisti** | — | — | — | — | — | — | — | — | — | — | — | 1 | — | — | — | — | — | — | 1 | **2** |
| **claude-ux-mikrokopi** | — | — | — | — | — | — | — | — | — | — | — | 1 | — | — | — | — | — | — | 1 | **2** |
| **claude-misafir-tester** | — | — | — | — | — | — | — | — | — | — | — | 1 | — | — | — | — | — | — | 1 | **2** |

### 4.2 Darboğaz Analizi

| Darboğaz | Neden | Sprint | Çözüm |
|----------|-------|--------|-------|
| **claude-kidemli-gelistirici** | En yoğun agent (55 görev), her sprintte kritik yolda | S1, S10, S12 | D1'de bağımsız görevleri codex-junior'a devret |
| **gemini-kodlayici** | UI yoğun sprintlerde (S6, S10) 6-9 görev | S6, S10 | Wireframe'ler D1'de hazır olmalı, UI implementasyonu D2-D3'e yayılmalı |
| **claude-teknik-lider** | S0, S3'te yoğun (5 görev), model eğitimi zaman alıcı | S0, S3 | Model eğitimi background job, doğrulama D3'te |
| **İnsan (Ferit)** | Code review + onay + seed ofis iletişimi | S4, S11 | Review'ları batch'le, seed iletişimini paralel yürüt |

### 4.3 Önerilen Paralelleme Stratejisi

```
Haftalık İş Akışı (Tek Kişi + AI Agents):

Pazartesi:
  08:00-10:00  Ferit: Sprint review + görev atama
  10:00-18:00  AI Agents: D1 görevleri (paralel)
  18:00-19:00  Ferit: D1 çıktılarını review

Salı-Çarşamba:
  08:00-09:00  Ferit: D1 feedback + D2 tetikleme
  09:00-18:00  AI Agents: D2 görevleri
  18:00-19:00  Ferit: D2 review

Perşembe:
  08:00-09:00  Ferit: D2 onay + D3 tetikleme
  09:00-18:00  AI Agents: D3 görevleri (entegrasyon)
  18:00-19:00  Ferit: D3 review

Cuma:
  08:00-12:00  AI Agents: D4 test + bug fix
  12:00-15:00  Ferit: Demo hazırlık + son review
  15:00-17:00  Sprint demo + retrospektif
```

---

## 5. Risk ve Bağımlılık Matrisi

### 5.1 Dış Bağımlılıklar

| # | Bağımlılık | Etkilenen Sprint | Olasılık | Etki | Mitigation |
|---|-----------|-----------------|----------|------|------------|
| D1 | WhatsApp BSP onayı (4-12 hafta) | S12 | Orta | Yüksek | Telegram birincil kanal; S2'de başvuru, S12'ye kadar süre var. Starter/Pro click-to-chat BSP gerektirmez (S9'da hazır) |
| D2 | Scraping hukuki onay | S15 | Yüksek | Orta | S4'te hukuki araştırma; ortaklık yoksa sınırlı istatistik modu |
| D3 | TÜİK/TCMB API erişimi | S2 | Düşük | Orta | Alternatif veri kaynakları + cache |
| D4 | AFAD/Kandilli veri erişimi | S2 | Düşük | Düşük | Birden fazla kaynak, graceful degradation |
| D5 | GPU maliyet (AI Fotoğraf) | S16 | Orta | Orta | Per-image kota, başlangıçta API-based (DALL-E) |
| D6 | Seed ofis LOI (30 ofis) | S4, S11 | Orta | Yüksek | Saha ekibi paralel çalışma, hedef 50 aday'dan 30 LOI |
| D7 | Ödeme gateway entegrasyonu | S1 | Düşük | Orta | iyzico/Stripe → test ortamı S1'de, canlı S4'te |

### 5.2 İç Bağımlılıklar (Sprint Arası)

| Kaynak Sprint | Hedef Sprint | Bağımlılık Türü | Kritiklik |
|---------------|-------------|-----------------|-----------|
| S0 | S1, S2, S3, S4, S5+ | DB şeması, auth, CI/CD | 🔴 Kritik |
| S1 | S2, S10, S12 | Messaging Gateway, Celery, Outbox | 🔴 Kritik |
| S2 | S3, S5, S6 | Veri pipeline, Property modeli | 🔴 Kritik |
| S3 | S5 | AI Model v0, inference pipeline | 🔴 Kritik |
| S4 | S5, S15 | PDF, TR arama, hukuki çerçeve | 🟡 Yüksek |
| S5 | S6 | Değerleme API, emsal algoritması | 🟡 Yüksek |
| S7 | S9, S10, S14, S17 | CRM veri modeli, eşleştirme | 🟡 Yüksek |
| S8 | S10, S16 | İlan asistanı, fotoğraf pipeline | 🟢 Orta |
| S9 | S14 | Vitrin, paylaşım altyapısı | 🟢 Orta |

### 5.3 Risk Mitigation Planı

| Risk | Tetiklenme Koşulu | Plan A | Plan B |
|------|-------------------|--------|--------|
| BSP onay gecikmesi | S12'ye kadar onay yok | Click-to-chat link ile devam | SMS adapter fallback |
| Model MAPE >%22 | S3 sonunda hedef tutmadı | Daha fazla veri toplama (S4'e sarkma) | Feature engineering iterasyon |
| Seed ofis <20 LOI | S4 sonunda hedef tutmadı | Hedef bölgeyi genişlet (Avrupa yakası ekle) | Freemium self-serve açılış |
| Scraping hukuki red | S15 başında hukuki görüş negatif | Sadece aggregate istatistik modu | Ortaklık API ile devam |
| Sprint sarkması | Herhangi sprint %120+ effort | Kapsam daraltma (Should/Could → sonraki sprint) | Sprint uzatma (1 hafta) |

---

## 6. Milestone'lar ve Demo Noktaları

### 6.1 Milestone Tablosu

| # | Milestone | Hafta | Demo İçeriği | Go/No-Go Kriterleri |
|---|-----------|:-----:|-------------|-------------------|
| **M0** | Çalışan İskelet | 2 | Docker up → auth → dashboard shell | CI yeşil, RLS testleri geçiyor |
| **M1** | İletişim Altyapısı | 4 | Telegram bot echo, OTel trace | Bot webhook çalışıyor, trace görünüyor |
| **M2** | Veri Hazır | 6 | 3 ilçe verisi, API client'lar | Veri pipeline çalışıyor |
| **M3** | AI Model v0 | 8 | Canlı değerleme demosu | MAPE <%22 |
| **M4** | **Faz 0 Tamamlandı** | 10 | PDF rapor, arama, seed ofis listesi | **GATE G0** |
| **M5** | Değerleme v1 | 12 | Tam değerleme akışı + PDF | MAPE <%18, emsal ≥3 |
| **M6** | Veri Zenginliği | 14 | Bölge kartı + harita + deprem risk | 3 EPIC tamamlandı |
| **M7** | CRM Çalışıyor | 16 | Müşteri kayıt → eşleşme → bildirim | **GATE G1** |
| **M8** | AI İlan | 18 | İlan metni + fotoğraf iyileştirme | LLM çıktı kalitesi |
| **M9** | Vitrin + Kredi | 20 | Public vitrin linki, kredi hesaplama | Vitrin responsive |
| **M10** | Telegram Tam | 22 | Mini App demo, bot conversation flow | Bot %95+ başarı oranı |
| **M11** | **🚀 ALPHA LANSMAN** | 24 | 9 özellik demo, seed ofis onboard | **GATE G2** |
| **M12** | WhatsApp API (Elite) Aktif | 26 | Template mesaj gönderim demosu (Cloud API) | BSP onaylı, Elite plan aktif |
| **M13** | EİDS | 28 | OCR demo, rozet gösterim | OCR accuracy |
| **M14** | Portföy Ağı | 30 | Cross-office eşleşme demosu | **GATE G3** |
| **M15** | Scraping | 32 | Pazar istatistikleri | Hukuki uyum |
| **M16** | AI Fotoğraf | 34 | Virtual staging demo | GPU maliyet kontrolü |
| **M17** | Elite Kademe | 36 | Ofis yönetim paneli, KPI'lar | Multi-user çalışıyor |
| **M18** | **🚀 BETA LANSMAN** | 38 | 15 özellik tam demo | **GATE G4** |

### 6.2 Demo Akışları

**Alpha MVP Demo (Hafta 24):**
1. Kayıt → Login → Dashboard
2. Değerleme: adres gir → AI fiyat tahmini → emsal listesi → PDF indir
3. CRM: müşteri ekle → eşleşme bildirimi al
4. Bölge: mahalle analiz kartı → harita → deprem risk
5. İlan: özellik gir → AI metin → fotoğraf iyileştir
6. Telegram: Mini App aç → değerleme → CRM kayıt
7. Vitrin: public link paylaş

**Beta MVP Demo (Hafta 38):**
1-7. (Alpha demosu +)
8. WhatsApp (Elite): Cloud API template mesaj → çift yönlü iletişim (Starter/Pro: click-to-chat Alpha'da mevcut)
9. EİDS: belge yükle → OCR → doğrulanmış rozet
10. Portföy Ağı: paylaşıma aç → cross-office eşleşme → komisyon akışı
11. Scraping: pazar istatistikleri dashboard
12. AI Fotoğraf: boş oda → virtual staging
13. Elite: ofis yönetim paneli → danışman KPI → rapor

---

## 7. Effort Özeti

### 7.1 Sprint Bazlı Effort Dağılımı

| Sprint | S | M | L | XL | Toplam Görev | Toplam Effort Puanı* |
|--------|:-:|:-:|:-:|:--:|:------------:|:-------------------:|
| S0 | 4 | 10 | 4 | 0 | 20 | 38 |
| S1 | 3 | 9 | 6 | 0 | 20 | 41 |
| S2 | 4 | 8 | 5 | 0 | 19 | 37 |
| S3 | 2 | 6 | 4 | 1 | 17 | 38 |
| S4 | 3 | 8 | 4 | 0 | 18 | 35 |
| S5 | 3 | 6 | 5 | 0 | 17 | 35 |
| S6 | 4 | 8 | 5 | 0 | 19 | 37 |
| S7 | 4 | 7 | 4 | 0 | 18 | 33 |
| S8 | 3 | 6 | 4 | 0 | 16 | 31 |
| S9 | 4 | 7 | 3 | 0 | 16 | 28 |
| S10 | 5 | 5 | 4 | 2 | 18 | 39 |
| S11 | 2 | 5 | 4 | 2 | 15 | 37 |
| S12 | 2 | 5 | 4 | 0 | 13 | 27 |
| S13 | 2 | 3 | 2 | 0 | 8 | 15 |
| S14 | 1 | 3 | 3 | 1 | 9 | 22 |
| S15 | 0 | 3 | 3 | 0 | 8 | 18 |
| S16 | 0 | 3 | 1 | 1 | 6 | 16 |
| S17 | 2 | 3 | 3 | 0 | 8 | 17 |
| S18 | 0 | 2 | 4 | 2 | 10 | 26 |

*Effort Puanı: S=1, M=2, L=3, XL=5

### 7.2 Faz Bazlı Özet

| Faz | Sprint | Toplam Görev | Toplam Effort | Ortalama/Sprint |
|-----|--------|:------------:|:-------------:|:---------------:|
| Faz 0 | S0-S4 | 94 | 189 | 37.8 |
| Alpha | S5-S11 | 119 | 240 | 34.3 |
| Beta | S12-S18 | 62 | 141 | 20.1 |
| **TOPLAM** | **S0-S18** | **275** | **570** | **30.0** |

---

## 8. Route Katmanı Checklist

> **⚠️ TECRÜBİ DERS:** Route katmanı olmadan bileşen sadece dosyadır. Her UI bileşeni için route tanımlama zorunludur.

| Sprint | Route | Sayfa | Durum |
|--------|-------|-------|:-----:|
| S0 | `/(auth)/login` | Login sayfası | ✅ |
| S0 | `/(auth)/register` | Kayıt sayfası | ✅ |
| S0 | `/(dashboard)/layout` | Dashboard shell | ✅ |
| S0 | `/tg/layout` | Telegram Mini App layout | ✅ |
| S3 | `/(dashboard)/valuations` | Değerleme listesi | ✅ |
| S4 | `/(dashboard)/properties` | Portföy listesi | ✅ |
| S5 | `/(dashboard)/valuations/[id]` | Değerleme detayı | ✅ |
| S6 | `/(dashboard)/areas` | Bölge analiz | ✅ |
| S6 | `/(dashboard)/maps` | Harita görünümü | ✅ |
| S7 | `/(dashboard)/dashboard/customers` | Müşteri listesi | ✅ |
| S7 | `/(dashboard)/dashboard/customers/[id]` | Müşteri detayı | ✅ |
| S8 | `/(dashboard)/listings` | İlan asistanı | ✅ |
| S9 | `/vitrin/[slug]` | Public vitrin | ✅ |
| S9 | `/(dashboard)/network` | Portföy ağı | ✅ |
| S9 | `/(dashboard)/calculator` | Kredi hesaplayıcı | ✅ |
| S10 | `/tg/page` | Mini App dashboard | ✅ |
| S10 | `/tg/valuation` | Mini App değerleme | ✅ |
| S10 | `/tg/crm` | Mini App CRM | ✅ |
| S12 | `/(dashboard)/messages` | Mesajlaşma inbox | ✅ |
| S13 | `/(dashboard)/eids` | EİDS doğrulama | ✅ |
| S17 | `/(dashboard)/reports` | Raporlama (Elite) | ✅ |
| — | `/(dashboard)/settings` | Ayarlar | ✅ |

---
