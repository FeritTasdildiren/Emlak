"""
Emlak Teknoloji Platformu - Database Configuration

SQLAlchemy 2.0 async engine ve session factory.

ONEMLI — Dual-Session Problemi ve Cozumu:
    TenantMiddleware, authenticated request'lerde JWT'den office_id ve role
    bilgisini cikartip request.state'e yazar. Ancak middleware kendi oturumunu
    KULLANMAZ — SET LOCAL islemini endpoint'lerin kullandigi oturumda yapmak
    gerekir. Bu nedenle get_db_session() Request nesnesini alir ve
    request.state.office_id / request.state.user_role mevcutsa otomatik olarak
    SET LOCAL uygular. Boylece RLS policy'ler dogru calisir.

    Public endpoint'ler icin (register, login, forgot-password vb.)
    request.state'te office_id olmaz → SET LOCAL atlanir → bu endpoint'lerdeki
    servis fonksiyonlari kendi icinde platform_admin bypass SET LOCAL yapar.
"""

from collections.abc import AsyncGenerator

from fastapi import Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from src.config import settings

# ---------- Async Engine ----------
engine = create_async_engine(
    settings.DB_URL,
    echo=settings.APP_DEBUG,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# ---------- Session Factory ----------
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ---------- Base Model ----------
class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""

    pass


# ---------- Session Dependency ----------
async def get_db_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency: veritabani session'i yield eder.

    TenantMiddleware tarafindan request.state'e yazilan office_id ve user_role
    varsa, session basinda SET LOCAL ile RLS degiskenleri ayarlanir.
    Bu sayede endpoint'lerin kullandigi oturum ile RLS uyumlu calisir.

    Public endpoint'lerde (register, login vb.) request.state'te office_id
    bulunmaz — SET LOCAL atlanir, servis fonksiyonlari kendi bypass'ini yapar.

    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db_session)):
            ...
    """
    async with async_session_factory() as session:
        try:
            # --- RLS SET LOCAL: TenantMiddleware bilgileri varsa uygula ---
            office_id = getattr(request.state, "office_id", None)
            user_role = getattr(request.state, "user_role", None)

            if office_id:
                # asyncpg SET LOCAL parameterized query desteklemiyor —
                # f-string kullanilir (office_id JWT'den gelir, guvenlidir)
                await session.execute(
                    text(f"SET LOCAL app.current_office_id = '{office_id}'")
                )
            if user_role:
                await session.execute(
                    text(f"SET LOCAL app.current_user_role = '{user_role}'")
                )

            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
