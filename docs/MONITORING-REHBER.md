# Emlak Teknoloji Platformu - Monitoring Rehberi

> Son guncelleme: 2026-02-26
> Versiyon: 1.0

## 1. Mimari Genel Bakis

```
┌─────────────┐    OTLP/gRPC     ┌──────────┐    Query    ┌──────────┐
│  FastAPI     │ ──────────────── │  Tempo   │ ◀───────── │  Grafana │
│  (OTel SDK)  │    :4317         │  :3200   │            │  :3001   │
└─────────────┘                   └──────────┘            └──────────┘
       │                                                       │
       │                                                       ├── Dashboards
       │  structlog/JSON                                       ├── Alerting
       ▼                                                       └── Notifications
  stdout → Docker logs                                              │
                                                              ┌─────┴──────┐
                                                              │  Telegram  │
                                                              │  Bot API   │
                                                              └────────────┘
```

### Bilesenler
| Bilesen | Teknoloji | Port | Amac |
|---------|----------|------|------|
| Tracing Backend | Grafana Tempo | 3200 (query), 4317 (OTLP) | Distributed trace saklama |
| Dashboard & Alerting | Grafana | 3001 (dis), 3000 (ic) | Gorsellestirme ve alert yonetimi |
| Instrumentation | OpenTelemetry SDK | - | Otomatik trace/metric toplama |
| Logging | structlog + JSON | - | Yapisal log ciktisi |
| Error Tracking | Sentry (opsiyonel) | - | Exception izleme |
| Notifications | Telegram Bot | - | Alert bildirimleri |

---

## 2. Erisim Bilgileri

| Servis | URL | Notlar |
|--------|-----|--------|
| Grafana | http://localhost:3001 | Anonim erisim (dev), prod'da auth aktif |
| Tempo Query | http://localhost:3200 | Sadece ic ag |
| OTLP Endpoint | http://localhost:4317 | gRPC, sadece ic ag |
| API Health | http://localhost:8000/health | Liveness probe |
| API DB Health | http://localhost:8000/health/db | Database probe |
| API Readiness | http://localhost:8000/health/ready | Full readiness probe |
| Admin Outbox | http://localhost:8000/admin/outbox/metrics | Outbox metrikleri |
| Admin DLQ | http://localhost:8000/admin/dlq | Dead Letter Queue |
| Admin Refresh | http://localhost:8000/admin/refresh/status | Data refresh durumu |

---

## 3. Dashboard Rehberi

### 3.1 Trace Explorer (Mevcut)
**UID**: `trace-explorer`
**Amac**: Detayli trace arama, latency analizi, hata inceleme
**Paneller**: Request Rate, Error Rate, Avg/P95 Latency, Trace Search,
             Top Slow Endpoints, Outbox/Celery Duration, Recent Errors

### 3.2 SLA Monitoring (Yeni)
**UID**: `sla-overview`
**Amac**: SLA uyum takibi, alert gecmisi, business metrikleri
**Bolumler**:

| Bolum | Panel Sayisi | Aciklama |
|-------|-------------|----------|
| SLA Overview | 7 | Uptime, p95, p99, error rate, degerleme, Celery stat |
| SLA Trend | 1 | 7 gunluk p95/p99/error trendi (timeseries) |
| Alert Gecmisi | 2 | Aktif alertler + son 24 saat degisiklikleri |
| Endpoint Performance | 3 | Heatmap, top slow endpoints, latency breakdown |
| Business Metrics | 5 | Degerleme/musteri/rapor/eslestirme sayilari + trend |
| Resource Usage | 6 | Request rate, error rate, outbox, celery gauge'lar + trend |
| ML Model Health | 3 | PSI score, basari orani, degerleme suresi trend |

**Degiskenler**:
- `$service` → Servis filtresi (emlak-api, emlak-celery, emlak-web)
- `$sla_window` → SLA olcum penceresi (24h, 7d, 30d)

---

## 4. Alert Kurallari

### 4.1 Alert Ozet Tablosu

| # | Alert | Esik | Bekleme | Severity | Telegram |
|---|-------|------|---------|----------|----------|
| 1 | API Down | /health fail | 5dk | CRITICAL | ✅ |
| 2 | DB Baglanti Koptu | /health/db fail | 3dk | CRITICAL | ✅ |
| 3 | Disk Yuksek | > %85 | 5dk | WARNING | ✅ |
| 4 | Memory Yuksek | > %90 | 5dk | HIGH | ✅ |
| 5 | Yuksek Latency | p95 > 3s | 5dk | WARNING | ❌ |
| 6 | Yuksek Error Rate | 5xx > %5 | 5dk | HIGH | ✅ |
| 7 | Outbox Lag | > 100 pending | 5dk | WARNING | ❌ |
| 8 | Celery Queue | > 50 pending | 10dk | WARNING | ❌ |
| 9 | ML Drift | PSI > 0.2 | 10dk | WARNING | ❌ |
| 10 | RLS Violation | > 0 | 0dk | CRITICAL | ✅ |
| 11 | SLA Uptime | < %99.5 | 15dk | HIGH | ✅ |
| 12 | SLA p95 Latency | > 500ms | 15dk | WARNING | ❌ |
| 13 | SLA Error Rate | > %1 | 10dk | HIGH | ✅ |

### 4.2 Notification Politikasi

```
              ┌──────────────┐
              │  Alert Fired │
              └──────┬───────┘
                     │
         ┌───────────┼───────────┐
         ▼           ▼           ▼
    ┌─────────┐ ┌─────────┐ ┌─────────┐
    │CRITICAL │ │  HIGH   │ │WARNING  │
    └────┬────┘ └────┬────┘ └────┬────┘
         │           │           │
    Telegram    Telegram    Telegram
    10s wait    30s wait    1m wait
    1dk group   5dk group   10dk group
    15dk repeat 30dk repeat 4h repeat
```

### 4.3 Mute Penceresi
- **Bakim**: Pazar 03:00-04:00 (Europe/Istanbul)
- Alert-rules.yml icerisinde `maintenance-window` olarak tanimli
- Gerektiginde Grafana UI'dan da mute yapilabilir

---

## 5. Telegram Entegrasyonu

### 5.1 Kurulum Adimlari

1. **Bot Olusturma**
   ```
   @BotFather → /newbot → "Emlak Monitor Bot" → token al
   ```

2. **Grup Ayarlari**
   ```
   Bot'u gruba ekle → /start yaz
   https://api.telegram.org/bot<TOKEN>/getUpdates → chat_id al
   ```

3. **Environment Degiskenleri** (.env dosyasina ekle)
   ```bash
   TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
   TELEGRAM_CHAT_ID=-1001234567890
   TELEGRAM_DEVOPS_CHAT_ID=-1009876543210  # Opsiyonel
   ```

4. **Docker Compose** (Grafana environment'ina ekle)
   ```yaml
   grafana:
     environment:
       - GF_UNIFIED_ALERTING_ENABLED=true
       - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
       - TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID}
   ```

### 5.2 Mesaj Formatlari

**Critical Alert Ornegi:**
```
🔴 FIRING

API Servisi Down
Severity: critical

📋 API 5 dakikadir yanit vermiyor!
📝 /health endpoint'i basarisiz
🕐 26.02.2026 14:30:00

🏷 Ortam: production
📊 SLA Dashboard
```

**Resolved Ornegi:**
```
🟢 RESOLVED

API Servisi Down
Severity: critical

📋 API servisi tekrar aktif
🕐 26.02.2026 14:45:00

🏷 Ortam: production
```

---

## 6. Health Check Endpoint'leri

### 6.1 Endpoint Detaylari

| Endpoint | Tip | Kontrol | Basarisizlik |
|----------|-----|---------|-------------|
| GET /health | Liveness | Process canli mi | 503 |
| GET /health/db | DB Probe | SELECT 1 | 503 |
| GET /health/pdf | PDF Probe | WeasyPrint render | 503 |
| GET /health/ready | Readiness | DB + Redis + MinIO + Outbox + PDF | 503 |

### 6.2 Readiness Detay

/health/ready endpointi su kontrolleri yapar:
```json
{
  "status": "healthy",
  "checks": {
    "database": "ok",
    "redis": "ok",
    "minio": "ok",
    "outbox": {
      "status": "ok",
      "pending_count": 3,
      "stuck_count": 0,
      "avg_lag_seconds": 1.2
    },
    "pdf_engine": "ok"
  }
}
```

**Degraded durumlar**:
- `outbox.stuck_count > 0` → warning
- `outbox.pending_count > 1000` → degraded
- `outbox.avg_lag > 60s` → degraded
- `pdf_engine` hatasi → readiness'i bloklamaz (opsiyonel)

---

## 7. Troubleshooting Rehberi

### 7.1 Alert: API Down
```bash
# 1. Container durumunu kontrol et
docker ps | grep emlak-api

# 2. Loglari incele
docker logs emlak-api --tail 100

# 3. Health check manual test
curl -f http://localhost:8000/health

# 4. Bagimliliklari kontrol et
curl http://localhost:8000/health/ready

# 5. Restart (son care)
docker compose restart api
```

### 7.2 Alert: DB Connection Lost
```bash
# 1. PostgreSQL durumu
docker ps | grep emlak-db
docker logs emlak-db --tail 50

# 2. Connection count
docker exec emlak-db psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

# 3. DB test
docker exec emlak-db pg_isready -U postgres -d emlak_dev

# 4. API tarafindaki connection pool
curl http://localhost:8000/health/db
```

### 7.3 Alert: High Error Rate
```bash
# 1. Son hatalari Trace Explorer'dan incele
# Grafana → Trace Explorer → Recent Errors paneli

# 2. API loglarinda 5xx ara
docker logs emlak-api --tail 500 | grep -i "500\|error\|exception"

# 3. Sentry'de son exception'lari kontrol et (kuruluysa)

# 4. Son deploy'u kontrol et
git log --oneline -5
```

### 7.4 Alert: Outbox Lag
```bash
# 1. Admin endpoint'ten metrikler
curl http://localhost:8000/admin/outbox/metrics

# 2. Stuck event'leri kontrol et
curl http://localhost:8000/admin/outbox/stuck

# 3. Celery worker durumu
docker logs emlak-celery-worker --tail 50

# 4. Stuck event release (gerekirse)
curl -X POST http://localhost:8000/admin/outbox/stuck/{event_id}/release
```

### 7.5 Alert: ML Drift
```bash
# 1. Drift raporu (admin endpointi varsa)
# PSI > 0.2 olan feature'lari tespit et

# 2. Son verilerle model performansi
cd apps/api && uv run python -m src.ml.trainer

# 3. Feature dagilimlarini karsilastir
# Egitim vs production veri dagilimi kontrolu
```

---

## 8. Operasyonel Prosedurler

### 8.1 Yeni Alert Ekleme
1. `infra/grafana/provisioning/alerting/alert-rules.yml` dosyasini duzenle
2. Yeni rule'u uygun gruba ekle
3. Label'larda severity ve alert_channel belirle
4. `docker compose restart grafana` ile yukle
5. Grafana UI'dan alert'in aktif oldugunu dogrula

### 8.2 Alert Mute Etme
- **Gecici**: Grafana UI → Alerting → Silences → New silence
- **Kalici**: alert-rules.yml icinde mute_time_intervals kullan
- **Telegram**: 15dk repeat_interval varsayilan mute suresi

### 8.3 Dashboard Ekleme/Duzenleme
1. JSON dosyasini `infra/grafana/provisioning/dashboards/` altina ekle
2. `"id": null` ve unique `"uid"` kullan
3. `"schemaVersion": 39` kullan
4. Datasource uid'yi `"tempo"` olarak ayarla
5. 30sn icerisinde Grafana otomatik yukler

### 8.4 Tempo Retention Degisikligi
```yaml
# infra/tempo/tempo.yaml
compactor:
  compaction:
    block_retention: 168h   # 72h → 7 gun
```
> Not: Retention artirildikca disk kullanimi artar. Disk alert esigini gozden gecir.

---

## 9. Production Checklist

- [ ] Grafana anonim erisimi kapatildi (`GF_AUTH_ANONYMOUS_ENABLED=false`)
- [ ] Grafana login formu aktif (`GF_AUTH_DISABLE_LOGIN_FORM=false`)
- [ ] Admin sifresi degistirildi (`GF_SECURITY_ADMIN_PASSWORD`)
- [ ] Telegram bot token .env'de (`TELEGRAM_BOT_TOKEN`)
- [ ] Telegram chat id .env'de (`TELEGRAM_CHAT_ID`)
- [ ] Tempo retention production icin ayarlandi (>= 7 gun)
- [ ] OTel sampling orani dusuruldu (prod icin %10-25)
- [ ] Sentry DSN yapilandirildi
- [ ] Health check endpoint'leri dis izlemeden de kontrol ediliyor
- [ ] Alert notification testi yapildi (test alert gonderildi)
- [ ] SLA dashboard ekip ile paylasil di
- [ ] On-call rotasyonu belirlendi
- [ ] Runbook'lar olusturuldu ve guncellendi

---

## 10. Dosya Yapisi

```
infra/
├── grafana/
│   └── provisioning/
│       ├── alerting/
│       │   └── alert-rules.yml          ← Alert kurallari (13 kural)
│       ├── dashboards/
│       │   ├── dashboard.yml            ← Provisioning config
│       │   ├── trace-explorer.json      ← Trace dashboard (mevcut)
│       │   └── sla-monitoring.json      ← SLA dashboard (yeni)
│       ├── datasources/
│       │   └── tempo.yaml               ← Tempo datasource
│       └── notifiers/
│           └── telegram.yml             ← Telegram bildirim config
├── tempo/
│   └── tempo.yaml                       ← Tempo yapilandirmasi
├── monitoring/
│   └── .gitkeep                         ← Gelecek genislemeler
└── docker/
    ├── Dockerfile.api
    ├── Dockerfile.web
    └── Dockerfile.worker

docs/
├── SLA-TANIMLARI.md                     ← SLA tanimlari
└── MONITORING-REHBER.md                 ← Bu dosya
```

---

## 11. Revizyon Gecmisi

| Tarih | Versiyon | Degisiklik |
|-------|----------|-----------|
| 2026-02-26 | 1.0 | Ilk monitoring rehberi olusturuldu |
