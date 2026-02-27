# Emlak Teknoloji Platformu

Turkiye emlak pazari icin yapay zeka destekli teknoloji platformu.

## Teknoloji Yigini

| Katman | Teknoloji |
|--------|-----------|
| **Backend API** | Python 3.12, FastAPI, SQLAlchemy 2.0 (async) |
| **Frontend** | Next.js 15, React, TypeScript |
| **Veritabani** | PostgreSQL 16 + PostGIS 3.4 |
| **Cache** | Redis 7.2 |
| **Object Storage** | MinIO (S3 uyumlu) |
| **Task Queue** | Celery + Redis |
| **Paket Yonetimi** | uv (Python), pnpm (Node.js) |
| **CI/CD** | GitHub Actions |
| **Container** | Docker, Docker Compose |

## Hizli Baslangic

### Gereksinimler

- [Docker](https://docs.docker.com/get-docker/) & Docker Compose
- [uv](https://docs.astral.sh/uv/) (Python paket yonetimi, lokal gelistirme icin)
- [Node.js 22+](https://nodejs.org/) & [pnpm](https://pnpm.io/) (frontend icin)
- Make (opsiyonel ama tavsiye edilir)

### 1. Ortam Degiskenlerini Ayarla

```bash
cp .env.example .env
# .env dosyasindaki degerleri kendi ortaminiza gore duzenleyin
```

### 2. Servisleri Baslat

```bash
# Tum servisleri ayaga kaldir
make up

# veya docker compose ile
docker compose up -d
```

### 3. Servislere Eris

| Servis | URL |
|--------|-----|
| API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/api/docs |
| API Docs (ReDoc) | http://localhost:8000/api/redoc |
| MinIO Console | http://localhost:9001 |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

### 4. Sagligi Kontrol Et

```bash
curl http://localhost:8000/health
```

## Gelistirme

### Proje Yapisi

```
Emlak/
├── apps/
│   ├── api/                  # FastAPI Backend
│   │   ├── src/
│   │   │   ├── core/         # Ortak utility'ler, exception'lar
│   │   │   ├── middleware/    # Custom middleware'ler
│   │   │   ├── models/       # SQLAlchemy modelleri
│   │   │   ├── modules/      # Feature modulleri (users, listings, vb.)
│   │   │   ├── tasks/        # Celery gorevleri
│   │   │   ├── config.py     # Pydantic Settings
│   │   │   ├── database.py   # DB engine & session
│   │   │   ├── dependencies.py
│   │   │   └── main.py       # FastAPI app entry point
│   │   ├── tests/            # Pytest testleri
│   │   ├── migrations/       # Alembic migration'lar
│   │   ├── pyproject.toml
│   │   └── Dockerfile
│   └── web/                  # Next.js Frontend (ayri agent tarafindan kurulacak)
├── infra/
│   ├── docker/               # Production Dockerfile'lar
│   ├── db/                   # Veritabani init script'leri
│   ├── nginx/                # Nginx konfigurasyonu
│   └── monitoring/           # Monitoring yapilandirmasi
├── docs/                     # Proje dokumantasyonu
├── docker-compose.yml
├── Makefile
├── .env.example
└── .github/workflows/ci.yml
```

### Kullanisli Komutlar

```bash
make help           # Tum komutlari listele
make up             # Servisleri baslat
make down           # Servisleri durdur
make logs           # Tum log'lari izle
make logs-api       # Sadece API log'larini izle
make test           # Testleri calistir
make lint           # Linter calistir
make format         # Kodu formatla
make migrate        # Migration'lari calistir
make migrate-create MSG="aciklama"  # Yeni migration olustur
make db-shell       # PostgreSQL shell'ine baglan
make clean          # Her seyi temizle
```

### Lokal Gelistirme (Docker olmadan)

```bash
# API bagimliliklerini kur
cd apps/api
uv sync --dev

# Testleri calistir
uv run pytest -v

# Linter & formatter
uv run ruff check src/ tests/
uv run ruff format src/ tests/
```

## CI/CD

GitHub Actions ile otomatik CI pipeline:

- **Path-filtered**: Sadece degisen bolum icin testler calisir
- **Python CI**: ruff check → ruff format → pytest
- **Node.js CI**: eslint → tsc --noEmit
- **Service containers**: PostGIS + Redis test icin otomatik ayaga kalkar

## Lisans

Tescilli yazilim. Tum haklari saklidir.
