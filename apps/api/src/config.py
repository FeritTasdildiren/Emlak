"""
Emlak Teknoloji Platformu - Application Configuration

Tum environment degiskenleri Pydantic Settings uzerinden yonetilir.
.env dosyasindan otomatik okunur.
"""

from urllib.parse import quote_plus
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---------- App ----------
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # ---------- PostgreSQL ----------
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "emlak_dev"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "change_me_in_production"

    @property
    def DB_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{quote_plus(self.DB_PASSWORD)}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def DB_URL_SYNC(self) -> str:
        """Alembic migration'lar icin senkron URL."""
        return (
            f"postgresql+psycopg2://{self.DB_USER}:{quote_plus(self.DB_PASSWORD)}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # ---------- App DB User (RLS) ----------
    APP_DB_USER: str = "app_user"
    APP_DB_PASSWORD: str = "change_me_app_user_password"

    # ---------- Redis ----------
    REDIS_URL: str = "redis://localhost:6379/0"

    # ---------- Celery ----------
    # Broker: Redis DB 1 (task kuyrugu), Result: Redis DB 2 (task sonuclari)
    # Ana Redis (cache) DB 0'da kalir — izolasyon icin ayri DB'ler kullanilir
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ---------- MinIO / S3 ----------
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "change_me_minio_secret"
    MINIO_BUCKET: str = "emlak-media"
    MINIO_USE_SSL: bool = False

    # ---------- JWT ----------
    JWT_SECRET_KEY: str = "change_me_jwt_secret_key_min_32_chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ---------- Password Reset ----------
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30  # Reset token TTL (Redis)
    FRONTEND_URL: str = "http://localhost:3000"  # Sifre sifirlama linki icin

    # ---------- Sentry ----------
    SENTRY_DSN: str = ""

    # ---------- OpenTelemetry ----------
    OTEL_EXPORTER_OTLP_ENDPOINT: str = ""  # bos → OTel devre disi (dev ortami)
    OTEL_SERVICE_NAME: str = "emlak-api"

    # ---------- iyzico Payment Gateway ----------
    IYZICO_API_KEY: str = ""
    IYZICO_SECRET_KEY: str = ""
    IYZICO_WEBHOOK_SECRET: str = ""
    IYZICO_BASE_URL: str = "https://sandbox-api.iyzipay.com"

    # ---------- Telegram Bot ----------
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_BOT_USERNAME: str = ""
    TELEGRAM_WEBHOOK_URL: str = ""
    TELEGRAM_WEBHOOK_SECRET: str = ""  # X-Telegram-Bot-Api-Secret-Token dogrulamasi

    # ---------- Data Pipeline: TUIK ----------
    TUIK_CIP_BASE_URL: str = "https://cip.tuik.gov.tr"
    TUIK_DATA_PORTAL_BASE_URL: str = "https://data.tuik.gov.tr"

    # ---------- Data Pipeline: TCMB EVDS ----------
    TCMB_EVDS_API_KEY: str = ""  # Ucretsiz kayit: https://evds2.tcmb.gov.tr/
    TCMB_EVDS_BASE_URL: str = "https://evds2.tcmb.gov.tr/service/evds"

    # ---------- Data Pipeline: AFAD ----------
    AFAD_EARTHQUAKE_API_BASE_URL: str = "https://deprem.afad.gov.tr"
    AFAD_TDTH_BASE_URL: str = "https://tdth.afad.gov.tr"
    AFAD_TUCBS_WMS_URL: str = "https://tucbs-public-api.csb.gov.tr/trk_afad_tdth_wms"

    # ---------- Data Pipeline: TKGM ----------
    TKGM_API_BASE_URL: str = "https://cbsapi.tkgm.gov.tr/megsiswebapi.v3/api"
    TKGM_WMS_BASE_URL: str = "https://cbs.tkgm.gov.tr/geoserver/wms"

    # ---------- OpenAI ----------
    OPENAI_API_KEY: str = ""  # bos → no-op guard (mock response doner)

    # ---------- Data Pipeline: Genel ----------
    DATA_PIPELINE_TIMEOUT: int = 30  # HTTP istek zaman asimi (saniye)
    DATA_PIPELINE_MAX_RETRIES: int = 3  # Maksimum yeniden deneme sayisi


# Singleton settings instance
settings = Settings()
