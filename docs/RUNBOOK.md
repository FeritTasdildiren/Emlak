# Runbook — Operasyonel Notlar

> Amac: Sik kullanilan operasyonel komutlar, acil durum prosedUrleri ve migration yonetimi.

---

## 1. Migration Rollback Stratejisi

### Alembic Temel Komutlar

```bash
# Mevcut migration durumunu gor
alembic current

# Migration gecmisini listele
alembic history --verbose

# Son migration'i geri al
alembic downgrade -1

# Belirli bir revision'a geri don
alembic downgrade <revision_id>

# Yeni migration olustur (autogenerate)
alembic revision --autogenerate -m "aciklama"

# Tum migration'lari bastan calistir
alembic upgrade head
```

### Rollback Kurallari

1. **Her migration'da `downgrade()` fonksiyonu ZORUNLU yazilmalidir.**
   Migration PR review'da downgrade olmayan migration reject edilir.

2. **Veri kaybi riski olan migration'lar geri alinamaz:**
   - `DROP COLUMN` — veri kaybolur, rollback ile geri gelmez
   - `DROP TABLE` — tablo ve veri tamamen silinir
   - `TRUNCATE` — veri silinir
   Bu durumlarda rollback yerine **yeni migration ile ekleme** yapilir (additive-only).

3. **RLS policy migration'lari idempotent olmalidir:**
   ```sql
   -- DOGRU: IF EXISTS ile guvenli rollback
   DROP POLICY IF EXISTS tenant_isolation ON properties;
   ALTER TABLE properties DISABLE ROW LEVEL SECURITY;

   -- YANLIS: IF EXISTS olmadan → policy yoksa hata verir
   DROP POLICY tenant_isolation ON properties;
   ```

4. **Production'da migration ONCE staging'de test edilir.**
   CI pipeline'da staging DB'ye upgrade+downgrade cycle testi zorunludur.

5. **Buyuk tablo migration'larinda (>1M row) `CONCURRENTLY` kullanim:**
   ```sql
   -- Index ekleme (tablo kilitlemez)
   CREATE INDEX CONCURRENTLY idx_name ON table_name (column);
   ```

### Mevcut Migration'lar

| # | Dosya | Icerik | Rollback Notu |
|---|-------|--------|---------------|
| 1 | `001_initial_schema.py` | 8 tablo (offices, users, subscriptions, properties, customers, conversations, messages, matches) + 17 indeks + TSVECTOR trigger | DOWN: tum tablolari DROP CASCADE |
| 2 | `002_rls_policies.py` | RLS policy'ler + FORCE RLS (7 tablo) + messages.office_id denormalize | DOWN: policy'leri DROP, RLS DISABLE, office_id DROP |
| 3 | `003_app_user_role.py` | app_user DB role + GRANT/REVOKE | DOWN: role REVOKE + DROP |

### Acil Durum: Production Migration Geri Alma

```bash
# 1. Mevcut durumu kontrol et
alembic current

# 2. Son basarili revision'i belirle
alembic history --verbose

# 3. Geri al (dikkatli!)
alembic downgrade -1

# 4. Dogrulama
alembic current
```

**UYARI:** Production'da rollback yapmadan once:
- DB yedegini al (`pg_dump`)
- Downgrade fonksiyonunun veri kaybi yaratip yaratmayacagini kontrol et
- Mumkunse maintenance window'da yap

---

## 2. Healthcheck Endpoint'leri

| Endpoint | Amac | Basarisiz Yanit |
|----------|------|-----------------|
| `GET /health` | Liveness probe — process ayakta mi | - (her zaman 200) |
| `GET /health/db` | Database baglanti kontrolu | 503 + `{"database": "disconnected"}` |
| `GET /health/ready` | Tum bagimliliklar hazir mi (DB + Redis + MinIO) | 503 + `{"status": "degraded"}` |

### Docker Compose Healthcheck Eslesmesi

```yaml
# API servisi
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 5s
  retries: 3

# Readiness (deployment sonrasi)
# curl -f http://localhost:8000/health/ready
```

### Kubernetes Probe Eslesmesi

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 30

readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 10
```

---

## 3. Sik Kullanilan Komutlar

### Gelistirme Ortami

```bash
# Servisleri baslat
make up

# Sadece API'yi baslat (hot reload)
make dev-api

# Loglari izle
make logs

# DB migration calistir
make migrate

# Testleri calistir
make test
```

### Production

```bash
# Deployment oncesi kontrol
curl -s http://localhost:8000/health/ready | jq .

# DB baglantisini kontrol et
curl -s http://localhost:8000/health/db | jq .

# DB yedek al
pg_dump -h localhost -p 5432 -U postgres emlak_dev > backup_$(date +%Y%m%d_%H%M%S).sql
```

---

## 4. CI/CD Pipeline

### Pipeline Mimarisi

```
  PR/Push to main         Tag Push (v*)
       │                       │
       ▼                       ▼
  ┌─────────┐           ┌─────────────┐
  │   CI    │           │  Validate   │
  │ (ci.yml)│           │  Tag Format │
  └────┬────┘           └──────┬──────┘
       │                       │
       ▼                       ▼
  ┌──────────────┐      ┌─────────────┐
  │ Deploy       │      │  CI Gate    │
  │ Staging      │      │  (full)     │
  │ (auto)       │      └──────┬──────┘
  └──────────────┘             │
                          ┌────┴────┐
                          ▼         ▼
                    ┌──────────┐ ┌──────────┐
                    │ Build API│ │ Build Web│
                    └─────┬────┘ └────┬─────┘
                          │           │
                          ▼           ▼
                    ┌─────────────────────┐
                    │  Deploy Production  │
                    │  (manual approval)  │
                    └─────────────────────┘
```

### Workflow Dosyalari

| Dosya | Trigger | Amac |
|-------|---------|------|
| `.github/workflows/ci.yml` | PR + push to main | Lint + test (path-filtered) |
| `.github/workflows/deploy-staging.yml` | push to main | Staging'e otomatik deploy |
| `.github/workflows/deploy-prod.yml` | tag push (v*) | Production'a deploy (approval gerekli) |

### Staging Deploy

```bash
# Otomatik: main branch'e push yapildiginda tetiklenir
# Manuel: GitHub Actions → Deploy Staging → Run workflow

# Sunucuda mevcut durumu kontrol et
ssh user@157.173.116.230
ls -la /var/www/uniqmys/current    # Aktif release symlink'i
ls -la /var/www/uniqmys/releases/  # Tum release'ler
pm2 status                          # PM2 servis durumu
```

### Production Deploy

```bash
# 1. Yeni tag olustur (semver)
git tag v1.2.3
git push origin v1.2.3

# 2. GitHub Actions'da "production" environment approval'i onayla
# 3. Pipeline otomatik olarak:
#    - Test suite calistirir
#    - Build yapar (API + Web)
#    - Pre-deploy DB backup alir
#    - Atomic symlink switch ile deploy eder
#    - PM2 graceful reload yapar
#    - Health check kontrol eder
#    - Basarisiz olursa otomatik rollback yapar
```

### Manuel Rollback

```bash
# GitHub Actions uzerinden:
# Deploy Production → Run workflow → rollback: true

# Sunucuda manuel:
ssh user@157.173.116.230
cd /var/www/uniqmys

# Mevcut release'i gor
readlink -f current

# Onceki release'e geri don
PREVIOUS=$(ls -dt releases/*/ | head -2 | tail -1)
ln -sfn "$PREVIOUS" current
pm2 reload ecosystem.config.js --update-env

# Dogrula
curl -s http://localhost:8000/health | jq .
```

### GitHub Secrets Gereksinimleri

Asagidaki secret'lar GitHub repo Settings → Secrets → Actions altinda tanimlanmalidir:

| Secret | Aciklama | Ornek |
|--------|----------|-------|
| `SSH_PRIVATE_KEY` | Deploy sunucusu SSH private key | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `SSH_USER` | Deploy sunucusu kullanici adi | `deploy` veya `root` |

### GitHub Environments Ayarlari

1. **staging** environment:
   - Protection rules: yok (otomatik deploy)
   - URL: `https://staging.uniqmys.com`

2. **production** environment:
   - Protection rules: **Required reviewers** (en az 1 onay)
   - URL: `https://uniqmys.com`
   - Deployment branches: sadece tag'ler

### Sunucu Dizin Yapisi

```
/var/www/uniqmys/
├── current → releases/v1.2.3_20260227_143000/  # Aktif release (symlink)
├── releases/
│   ├── v1.2.3_20260227_143000/                 # Son release
│   │   ├── apps/api/                           # API kodu
│   │   ├── apps/web/                           # Web build
│   │   ├── VERSION                             # Versiyon dosyasi
│   │   └── logs → ../../shared/logs            # Shared symlink
│   ├── v1.2.2_20260225_120000/                 # Onceki release
│   └── ...                                     # (son 5-7 tane tutulur)
├── shared/
│   ├── .env                                    # API env dosyasi
│   ├── .env.web                                # Web env dosyasi
│   ├── logs/                                   # Kalici log dizini
│   └── uploads/                                # Kalici upload dizini
├── backups/
│   └── pre_deploy_20260227_143000.sql.gz       # DB backup'lar
└── ecosystem.config.js                         # PM2 konfigurasyonu
```

### PDF CI Ortami

WeasyPrint PDF testleri CI'da calisabilmesi icin asagidaki sistem paketleri gereklidir:

```bash
# CI'da yuklenen paketler (Ubuntu):
sudo apt-get install -y --no-install-recommends \
  libpango-1.0-0 \
  libpangocairo-1.0-0 \
  libgdk-pixbuf-2.0-0 \
  libcairo2 \
  libglib2.0-0 \
  libffi-dev \
  fonts-noto-core \
  fonts-noto-extra
```

Bu paketler olmadan `test_pdf_smoke.py` testleri `skipif` ile atlanir.
Docker image'larinda bu bagimliliklar zaten Dockerfile'da mevcuttur.
