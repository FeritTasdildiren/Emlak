"""
Emlak Teknoloji Platformu — Alembic Environment Configuration

psycopg2 (sync) driver ile migration yönetimi.
Uygulama asyncpg kullanır, Alembic ise sync çalışır — bu Alembic best practice'dir.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from src.config import settings
from src.database import Base

# Alembic Config nesnesi — alembic.ini değerlerine erişim sağlar
config = context.config

# Logging konfigürasyonu
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------- Tüm modelleri import et (autogenerate için ZORUNLU) ----------
import src.models  # noqa: F401

# Target metadata — Base.metadata üzerinden tüm tablo tanımlarını alır
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Offline (SQL-only) migration modu.

    Veritabanı bağlantısı kurmadan SQL çıktısı üretir.
    CI/CD pipeline'larında kullanışlıdır.
    """
    context.configure(
        url=settings.DB_URL_SYNC,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Online migration modu.

    psycopg2 sync engine üzerinden veritabanına bağlanır.
    Alembic sync çalışır — asyncpg burada kullanılmaz.
    """
    connectable = create_engine(
        settings.DB_URL_SYNC,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
