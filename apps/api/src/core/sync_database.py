"""
Emlak Teknoloji Platformu - Sync Database Engine (Celery Tasks)

Celery worker'lar async loop icerisinde calisMAZ.
Bu modul, Celery task'larinin veritabanina senkron erisimi icin
psycopg2 tabanli SQLAlchemy engine ve session factory saglar.

Mimari Karar:
    - FastAPI  → asyncpg  (src/database.py)
    - Celery   → psycopg2 (bu dosya)
    - Alembic  → psycopg2 (settings.DB_URL_SYNC)

Pool Konfigurasyonu:
    - pool_size=5       → worker basina 5 connection (Celery prefork icin yeterli)
    - max_overflow=3    → peak zamanlarda +3 ek connection
    - pool_pre_ping=True → stale connection tespiti (SELECT 1)
    - pool_recycle=1800  → 30 dakikada connection yenile (PgBouncer uyumu)

Kullanim:
    from src.core.sync_database import get_sync_session

    with get_sync_session() as session:
        result = session.execute(text("SELECT 1"))
        session.commit()
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.config import settings

# ---------- Sync Engine (psycopg2) ----------
sync_engine = create_engine(
    settings.DB_URL_SYNC,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=3,
    pool_recycle=1800,
    echo=False,  # Celery task'larda SQL loglama kapali — structlog yeterli
)

# ---------- Session Factory ----------
SyncSessionFactory = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# ---------- Context Manager ----------
@contextmanager
def get_sync_session() -> Generator[Session, None, None]:
    """
    Celery task'lar icin sync veritabani session'i.

    Usage:
        with get_sync_session() as session:
            session.execute(...)
            session.commit()

    - commit() cagrilmazsa otomatik rollback yapilir.
    - Exception durumunda rollback garantili.
    - finally blogu session'i her durumda kapatir.
    """
    session = SyncSessionFactory()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
