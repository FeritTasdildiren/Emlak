# ============================================
# Emlak Teknoloji Platformu - Makefile
# ============================================

.PHONY: help up down logs migrate test lint format build clean celery-worker celery-beat celery-logs celery-local-worker celery-local-beat grafana grafana-logs grafana-dashboard traces

# Default target
help: ## Show this help
	@echo "Emlak Teknoloji Platformu - Available Commands:"
	@echo "================================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---------- Docker Compose ----------
up: ## Start all services (docker compose up -d)
	docker compose up -d
	@echo "\n✅ Services started!"
	@echo "   API:     http://localhost:8000"
	@echo "   Docs:    http://localhost:8000/api/docs"
	@echo "   MinIO:   http://localhost:9001"
	@echo "   Grafana: http://localhost:3001"
	@echo "   DB:      localhost:5432"

down: ## Stop all services
	docker compose down

down-v: ## Stop all services and remove volumes
	docker compose down -v

restart: ## Restart all services
	docker compose restart

logs: ## Tail logs for all services
	docker compose logs -f

logs-api: ## Tail logs for API service
	docker compose logs -f api

build: ## Build all Docker images
	docker compose build

rebuild: ## Rebuild and restart all services
	docker compose up -d --build

# ---------- Database ----------
migrate: ## Run Alembic migrations
	docker compose exec api uv run alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create MSG="add users table")
	docker compose exec api uv run alembic revision --autogenerate -m "$(MSG)"

migrate-down: ## Rollback last migration
	docker compose exec api uv run alembic downgrade -1

db-shell: ## Open PostgreSQL shell
	docker compose exec db psql -U postgres -d emlak_dev

# ---------- Testing ----------
test: ## Run API tests
	docker compose exec api uv run pytest -v --tb=short

test-cov: ## Run API tests with coverage
	docker compose exec api uv run pytest -v --tb=short --cov=src --cov-report=html

test-local: ## Run tests locally (without Docker)
	cd apps/api && uv run pytest -v --tb=short

# ---------- Linting & Formatting ----------
lint: ## Run linter (ruff check)
	cd apps/api && uv run ruff check src/ tests/

format: ## Format code (ruff format)
	cd apps/api && uv run ruff format src/ tests/

format-check: ## Check formatting without changes
	cd apps/api && uv run ruff format --check src/ tests/

lint-fix: ## Auto-fix linting issues
	cd apps/api && uv run ruff check --fix src/ tests/

# ---------- Celery ----------
celery-worker: ## Start Celery worker (Docker)
	docker compose up -d celery-worker
	@echo "\n✅ Celery worker started! Queues: default, outbox, notifications"

celery-beat: ## Start Celery beat scheduler (Docker)
	docker compose up -d celery-beat
	@echo "\n✅ Celery beat started!"

celery-logs: ## Tail Celery worker + beat logs
	docker compose logs -f celery-worker celery-beat

celery-local-worker: ## Start Celery worker locally (without Docker)
	cd apps/api && uv run celery -A src.celery_app worker --loglevel=info -Q default,outbox,notifications

celery-local-beat: ## Start Celery beat locally (without Docker)
	cd apps/api && uv run celery -A src.celery_app beat --loglevel=info

# ---------- Observability (Tempo + Grafana) ----------
grafana: ## Start Tempo + Grafana (tracing dashboard)
	docker compose up -d tempo grafana
	@echo "\n✅ Observability stack started!"
	@echo "   Grafana:  http://localhost:3001"
	@echo "   Tempo:    http://localhost:3200"
	@echo "   OTLP gRPC: localhost:4317"

grafana-logs: ## Tail Tempo + Grafana logs
	docker compose logs -f tempo grafana

grafana-dashboard: ## Open Trace Explorer dashboard in browser
	@echo "Opening Trace Explorer dashboard..."
	@open "http://localhost:3001/d/trace-explorer/trace-explorer?orgId=1" 2>/dev/null || \
		xdg-open "http://localhost:3001/d/trace-explorer/trace-explorer?orgId=1" 2>/dev/null || \
		echo "Open in browser: http://localhost:3001/d/trace-explorer/trace-explorer?orgId=1"

traces: ## Open Grafana Explore with Tempo datasource
	@echo "Opening Grafana Explore (Tempo)..."
	@open "http://localhost:3001/explore?orgId=1&left=%7B%22datasource%22:%22tempo%22%7D" 2>/dev/null || \
		xdg-open "http://localhost:3001/explore?orgId=1&left=%7B%22datasource%22:%22tempo%22%7D" 2>/dev/null || \
		echo "Open in browser: http://localhost:3001/explore?orgId=1&left=%7B%22datasource%22:%22tempo%22%7D"

# ---------- API Development ----------
api-shell: ## Open a shell in the API container
	docker compose exec api bash

api-deps: ## Install API dependencies locally
	cd apps/api && uv sync --dev

# ---------- Utilities ----------
clean: ## Remove all containers, volumes, and build artifacts
	docker compose down -v --remove-orphans
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true

env: ## Create .env from .env.example
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅ .env created from .env.example"; \
		echo "⚠️  Please update the values in .env"; \
	else \
		echo "⚠️  .env already exists. Skipping."; \
	fi

status: ## Show status of all services
	docker compose ps
