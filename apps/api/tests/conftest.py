"""
Emlak Teknoloji Platformu - Test Fixtures

pytest fixtures: test database, test client, RLS test infrastructure,
outbox/messaging test altyapisi.

RLS Test Altyapisi:
    - setup_rls: RLS policy, FORCE RLS, app_user role, seed data olusturur
    - rls_session: app_user rolüyle baglanti (RLS enforced)
    - set_tenant_context(): SET LOCAL helper
    - Seed data: 2 ofis, her birine ait kayitlar (7 RLS tablosu)

Outbox Test Altyapisi (TASK-043):
    - outbox_worker: OutboxWorker instance (test session factory ile)
    - mock_messaging_service: Mock MessagingService (gercek API cagrisi yok)
    - create_outbox_event: Outbox event factory (committed — worker gorebilir)
    - fast_retry_policy: Hizli retry policy (test icin kisa sureler)
    - dlq_service: DLQService instance (test session factory ile)
    - outbox_monitor: OutboxMonitor instance (test session factory ile)

Data Pipeline Test Altyapisi (TASK-056):
    - sync_session: psycopg2 sync session (Celery task uyumlu repository testleri)
    - sync_session_factory: Sync session factory (test DB — cleanup icin)
"""

import asyncio
import hashlib
import hmac
import json
import uuid
from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker

from src.config import settings
from src.database import Base, get_db_session
from src.main import app
from src.services.dlq_service import DLQService
from src.services.inbox_service import InboxService
from src.services.outbox_monitor import OutboxMonitor
from src.services.outbox_worker import OutboxWorker
from src.services.retry_policy import RetryPolicy

# ================================================================
# Pre-generated UUIDs for deterministic seed data
# ================================================================
# Office A = "a" serisi, Office B = "b" serisi
OFFICE_A_ID = uuid.UUID("a0000000-0000-0000-0000-000000000001")
OFFICE_B_ID = uuid.UUID("b0000000-0000-0000-0000-000000000001")

USER_A_ID = uuid.UUID("a0000000-0000-0000-0000-000000000010")
USER_B_ID = uuid.UUID("b0000000-0000-0000-0000-000000000010")

CUSTOMER_A_ID = uuid.UUID("a0000000-0000-0000-0000-000000000020")
CUSTOMER_B_ID = uuid.UUID("b0000000-0000-0000-0000-000000000020")

PROPERTY_A_ID = uuid.UUID("a0000000-0000-0000-0000-000000000030")
PROPERTY_A_SHARED_ID = uuid.UUID("a0000000-0000-0000-0000-000000000031")
PROPERTY_B_ID = uuid.UUID("b0000000-0000-0000-0000-000000000030")

CONVERSATION_A_ID = uuid.UUID("a0000000-0000-0000-0000-000000000040")
CONVERSATION_B_ID = uuid.UUID("b0000000-0000-0000-0000-000000000040")

MESSAGE_A_ID = uuid.UUID("a0000000-0000-0000-0000-000000000050")
MESSAGE_B_ID = uuid.UUID("b0000000-0000-0000-0000-000000000050")

NOTIFICATION_A_ID = uuid.UUID("a0000000-0000-0000-0000-000000000060")
NOTIFICATION_B_ID = uuid.UUID("b0000000-0000-0000-0000-000000000060")

SUBSCRIPTION_A_ID = uuid.UUID("a0000000-0000-0000-0000-000000000070")
SUBSCRIPTION_B_ID = uuid.UUID("b0000000-0000-0000-0000-000000000070")

# ================================================================
# RLS-enforced tablolar (offices HARIC — tenant root)
# Migration 002_rls_policies ile eslesir.
# ================================================================
RLS_TABLES: list[str] = [
    "customers",
    "properties",
    "conversations",
    "messages",
    "notifications",
    "subscriptions",
    "users",
]

# ================================================================
# Test Database URL'leri
# ================================================================
# Superuser engine: tablo olusturma, RLS policy, seed data icin
TEST_DB_URL = (
    f"postgresql+asyncpg://test_user:test_pass@{settings.DB_HOST}:{settings.DB_PORT}/emlak_test"
)

# App user engine: RLS-enforced sorgular icin (superuser DEGIL)
RLS_TEST_DB_URL = (
    f"postgresql+asyncpg://app_user:test_app_user_pass"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/emlak_test"
)

# ---------- Superuser Test Engine ----------
test_engine = create_async_engine(
    TEST_DB_URL,
    echo=False,
    pool_pre_ping=True,
)

test_session_factory = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# ---------- App User Test Engine (RLS enforced) ----------
rls_test_engine = create_async_engine(
    RLS_TEST_DB_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=2,
)

rls_test_session_factory = async_sessionmaker(
    rls_test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ================================================================
# SET LOCAL Helper
# ================================================================
async def set_tenant_context(
    session: AsyncSession,
    office_id: uuid.UUID,
    role: str = "agent",
) -> None:
    """
    PostgreSQL SET LOCAL ile tenant context ayarlar.

    SET LOCAL transaction scope'unda gecerli — COMMIT/ROLLBACK ile otomatik temizlenir.
    RLS policy'ler bu degiskenleri kullanarak veri izolasyonu saglar.

    Args:
        session: Aktif AsyncSession (transaction icinde olmali)
        office_id: Hedef ofis UUID'i
        role: Kullanici rolu (agent, office_admin, platform_admin vb.)
    """
    await session.execute(
        text("SET LOCAL app.current_office_id = :oid"),
        {"oid": str(office_id)},
    )
    await session.execute(
        text("SET LOCAL app.current_user_role = :role"),
        {"role": role},
    )


# ================================================================
# Event Loop (session-scoped)
# ================================================================
# NOT: pytest-asyncio 0.24+ event_loop fixture deprecation uyarisi verir.
# Gelecekte pyproject.toml'e asyncio_default_fixture_loop_scope = "session" eklenmeli.
@pytest.fixture(scope="session")
def event_loop():
    """Session-scoped event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ================================================================
# Database Setup (superuser — tablo olusturma)
# ================================================================
@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    """Test database'ini olusturur ve test sonunda temizler."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


# ================================================================
# RLS Setup (superuser — policy + role + seed data)
# ================================================================
@pytest_asyncio.fixture(scope="session")
async def setup_rls(setup_database):
    """
    RLS test altyapisini kurar:
    1. ENABLE + FORCE ROW LEVEL SECURITY (7 tablo)
    2. Tenant isolation policy'leri
    3. shared_properties policy (FOR SELECT)
    4. platform_admin_bypass policy (FOR ALL on users)
    5. app_user DB rolu + GRANT
    6. Seed data (2 ofis + iliskili kayitlar)

    Bu fixture session-scoped'dir — tum RLS testleri icin bir kez calisir.
    Seed data superuser ile eklenir (RLS bypass).
    """
    async with test_engine.begin() as conn:
        # ---- 1. ENABLE + FORCE RLS ----
        for table in RLS_TABLES:
            await conn.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"))
            await conn.execute(text(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY"))

        # ---- 2. Tenant isolation policies (FOR ALL) ----
        for table in RLS_TABLES:
            await conn.execute(
                text(
                    f"CREATE POLICY tenant_isolation_{table} ON {table} "
                    f"USING (office_id = current_setting('app.current_office_id', true)::uuid)"
                )
            )

        # ---- 3. Shared properties policy (FOR SELECT) ----
        await conn.execute(
            text(
                "CREATE POLICY shared_properties ON properties "
                "FOR SELECT "
                "USING (is_shared = true AND share_visibility = 'network')"
            )
        )

        # ---- 4. Platform admin bypass (FOR ALL on users) ----
        await conn.execute(
            text(
                "CREATE POLICY platform_admin_bypass ON users "
                "FOR ALL "
                "USING (current_setting('app.current_user_role', true) = 'platform_admin')"
            )
        )

        # ---- 5. app_user DB rolu ----
        await conn.execute(
            text(
                "DO $$ "
                "BEGIN "
                "    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_user') THEN "
                "        CREATE ROLE app_user LOGIN PASSWORD 'test_app_user_pass'; "
                "    END IF; "
                "END $$"
            )
        )
        await conn.execute(text("GRANT USAGE ON SCHEMA public TO app_user"))
        await conn.execute(
            text("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user")
        )
        await conn.execute(
            text("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user")
        )

        # ---- 6. Seed data ----
        await _seed_rls_test_data(conn)

    yield

    # Teardown: dispose rls engine (tablo drop'u setup_database teardown'inda olur)
    await rls_test_engine.dispose()


async def _seed_rls_test_data(conn) -> None:
    """
    RLS testleri icin seed data olusturur.

    2 ofis (A, B) ve her birine ait kayitlar:
    - users, customers, properties, conversations, messages, notifications, subscriptions.

    Ek olarak Office A'ya ait 1 adet shared property (cross-office gorunur).

    NOT: Superuser baglantisi ile calisir — RLS bypass edilir.
    NOT: Raw SQL kullanilir — ORM GeoAlchemy2 Geography serializasyon
         sorunlarindan kacinmak ve DB katmanini dogrudan test etmek icin.
    """
    # ---- Offices (no RLS — tenant root) ----
    await conn.execute(
        text("""
        INSERT INTO offices (id, name, slug, city, district)
        VALUES
            (:id_a, 'Office Alpha', 'office-alpha', 'Istanbul', 'Kadikoy'),
            (:id_b, 'Office Beta', 'office-beta', 'Istanbul', 'Besiktas')
    """),
        {"id_a": OFFICE_A_ID, "id_b": OFFICE_B_ID},
    )

    # ---- Users (RLS) ----
    await conn.execute(
        text("""
        INSERT INTO users (id, email, password_hash, full_name, role, office_id)
        VALUES
            (:id_a, 'agent-a@test.com', '$2b$12$dummyhashA000000000000000000000000000000000000000', 'Agent Alpha', 'agent', :off_a),
            (:id_b, 'agent-b@test.com', '$2b$12$dummyhashB000000000000000000000000000000000000000', 'Agent Beta', 'agent', :off_b)
    """),
        {
            "id_a": USER_A_ID,
            "id_b": USER_B_ID,
            "off_a": OFFICE_A_ID,
            "off_b": OFFICE_B_ID,
        },
    )

    # ---- Customers (RLS) ----
    await conn.execute(
        text("""
        INSERT INTO customers (id, office_id, full_name, phone, status)
        VALUES
            (:id_a, :off_a, 'Musteri Alpha', '+905551111111', 'active'),
            (:id_b, :off_b, 'Musteri Beta', '+905552222222', 'active')
    """),
        {
            "id_a": CUSTOMER_A_ID,
            "id_b": CUSTOMER_B_ID,
            "off_a": OFFICE_A_ID,
            "off_b": OFFICE_B_ID,
        },
    )

    # ---- Properties (RLS) — 2 normal + 1 shared ----
    # Property A: Office A'nin normal ilani (private)
    await conn.execute(
        text("""
        INSERT INTO properties (
            id, office_id, agent_id, title, property_type, listing_type,
            price, location, city, district, is_shared, share_visibility
        ) VALUES (
            :id, :off, :agent, 'Daire Alpha', 'daire', 'sale',
            500000, ST_GeogFromText('SRID=4326;POINT(29.03 41.01)'),
            'Istanbul', 'Kadikoy', false, 'private'
        )
    """),
        {"id": PROPERTY_A_ID, "off": OFFICE_A_ID, "agent": USER_A_ID},
    )

    # Property A-Shared: Office A'nin paylasima acik ilani (network)
    await conn.execute(
        text("""
        INSERT INTO properties (
            id, office_id, agent_id, title, property_type, listing_type,
            price, location, city, district, is_shared, share_visibility
        ) VALUES (
            :id, :off, :agent, 'Villa Alpha Shared', 'villa', 'sale',
            2500000, ST_GeogFromText('SRID=4326;POINT(29.04 41.02)'),
            'Istanbul', 'Kadikoy', true, 'network'
        )
    """),
        {"id": PROPERTY_A_SHARED_ID, "off": OFFICE_A_ID, "agent": USER_A_ID},
    )

    # Property B: Office B'nin normal ilani (private)
    await conn.execute(
        text("""
        INSERT INTO properties (
            id, office_id, agent_id, title, property_type, listing_type,
            price, location, city, district, is_shared, share_visibility
        ) VALUES (
            :id, :off, :agent, 'Daire Beta', 'daire', 'rent',
            15000, ST_GeogFromText('SRID=4326;POINT(29.00 41.05)'),
            'Istanbul', 'Besiktas', false, 'private'
        )
    """),
        {"id": PROPERTY_B_ID, "off": OFFICE_B_ID, "agent": USER_B_ID},
    )

    # ---- Subscriptions (RLS) ----
    await conn.execute(
        text("""
        INSERT INTO subscriptions (id, office_id, plan_type, status, start_date, monthly_price)
        VALUES
            (:id_a, :off_a, 'pro', 'active', NOW(), 799),
            (:id_b, :off_b, 'starter', 'trial', NOW(), 399)
    """),
        {
            "id_a": SUBSCRIPTION_A_ID,
            "id_b": SUBSCRIPTION_B_ID,
            "off_a": OFFICE_A_ID,
            "off_b": OFFICE_B_ID,
        },
    )

    # ---- Conversations (RLS) ----
    await conn.execute(
        text("""
        INSERT INTO conversations (id, office_id, customer_id, channel, status)
        VALUES
            (:id_a, :off_a, :cust_a, 'telegram', 'open'),
            (:id_b, :off_b, :cust_b, 'whatsapp', 'open')
    """),
        {
            "id_a": CONVERSATION_A_ID,
            "id_b": CONVERSATION_B_ID,
            "off_a": OFFICE_A_ID,
            "off_b": OFFICE_B_ID,
            "cust_a": CUSTOMER_A_ID,
            "cust_b": CUSTOMER_B_ID,
        },
    )

    # ---- Messages (RLS — office_id denormalize) ----
    await conn.execute(
        text("""
        INSERT INTO messages (id, conversation_id, office_id, direction, content, channel)
        VALUES
            (:id_a, :conv_a, :off_a, 'inbound', 'Merhaba, daire hakkinda bilgi alabilir miyim?', 'telegram'),
            (:id_b, :conv_b, :off_b, 'outbound', 'Tabii, size yardimci olabilirim.', 'whatsapp')
    """),
        {
            "id_a": MESSAGE_A_ID,
            "id_b": MESSAGE_B_ID,
            "conv_a": CONVERSATION_A_ID,
            "conv_b": CONVERSATION_B_ID,
            "off_a": OFFICE_A_ID,
            "off_b": OFFICE_B_ID,
        },
    )

    # ---- Notifications (RLS) ----
    await conn.execute(
        text("""
        INSERT INTO notifications (id, user_id, office_id, type, title, body)
        VALUES
            (:id_a, :usr_a, :off_a, 'new_message', 'Yeni mesaj', 'Musteri Alpha mesaj gonderdi'),
            (:id_b, :usr_b, :off_b, 'new_match', 'Yeni eslesme', 'Yeni ilan eslesmesi bulundu')
    """),
        {
            "id_a": NOTIFICATION_A_ID,
            "id_b": NOTIFICATION_B_ID,
            "usr_a": USER_A_ID,
            "usr_b": USER_B_ID,
            "off_a": OFFICE_A_ID,
            "off_b": OFFICE_B_ID,
        },
    )


# ================================================================
# RLS Session Fixture (app_user — FORCE RLS enforced)
# ================================================================
@pytest_asyncio.fixture
async def rls_session(setup_rls) -> AsyncGenerator[AsyncSession, None]:
    """
    app_user rolüyle calisan session — RLS testleri icin.

    Her test fonksiyonu icin yeni session olusturulur.
    Transaction baslatilir, test bitince ROLLBACK yapilir.
    SET LOCAL degiskenleri transaction scope'unda temizlenir.

    ONEMLI: Bu session superuser DEGIL. FORCE RLS aktif.
    """
    async with rls_test_session_factory() as session:
        # Begin transaction — SET LOCAL icin gerekli
        await session.begin()
        yield session
        # Her test sonrasi rollback — veri degisiklikleri geri alinir
        await session.rollback()


# ================================================================
# Standard Test Fixtures (mevcut — RLS disindaki testler icin)
# ================================================================
@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Her test icin temiz bir database session (superuser)."""
    async with test_session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Test HTTP client with overridden database dependency."""

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db_session] = _override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ================================================================
# Payment / Webhook Test Infrastructure
# ================================================================
# Deterministic UUIDs for payment tests ("80" serisi)
PAYMENT_A_ID = uuid.UUID("a0000000-0000-0000-0000-000000000080")
PAYMENT_B_ID = uuid.UUID("b0000000-0000-0000-0000-000000000080")

# HMAC-SHA256 test secret — production secret ile ayni OLMAMALI
WEBHOOK_SECRET = "test-webhook-secret-key-for-hmac-256"


@pytest.fixture
def webhook_secret() -> str:
    """Test webhook secret for HMAC-SHA256 signature verification."""
    return WEBHOOK_SECRET


@pytest.fixture
def create_signed_webhook():
    """
    HMAC-SHA256 imzali webhook payload factory.

    Returns:
        Callable: (payload, secret?) -> (body_bytes, signature_hex)
    """

    def _create(
        payload: dict, secret: str = WEBHOOK_SECRET
    ) -> tuple[bytes, str]:
        body = json.dumps(payload).encode("utf-8")
        signature = hmac.new(
            secret.encode("utf-8"), body, hashlib.sha256
        ).hexdigest()
        return body, signature

    return _create


@pytest.fixture
def inbox_service() -> InboxService:
    """InboxService instance for direct service testing."""
    return InboxService()


@pytest_asyncio.fixture
async def ensure_test_offices():
    """
    Test ofislerinin DB'de var olmasini saglar (idempotent).

    ON CONFLICT DO NOTHING sayesinde setup_rls ile catisma olmaz.
    Payment/webhook testlerinin FK ihtiyaclarini karsilar.
    """
    async with test_engine.begin() as conn:
        await conn.execute(
            text("""
                INSERT INTO offices (id, name, slug, city, district)
                VALUES
                    (:a, 'Test Office A', 'test-office-a', 'Istanbul', 'Kadikoy'),
                    (:b, 'Test Office B', 'test-office-b', 'Istanbul', 'Besiktas')
                ON CONFLICT (id) DO NOTHING
            """),
            {"a": OFFICE_A_ID, "b": OFFICE_B_ID},
        )


@pytest_asyncio.fixture
async def create_test_payment(ensure_test_offices):
    """
    Factory fixture: test payment + subscription olusturur.

    Her cagri yeni subscription + payment olusturur (tam izolasyon).
    Test bitiminde otomatik cleanup yapilir.

    Usage:
        data = await create_test_payment()
        data = await create_test_payment(office_id=OFFICE_B_ID, payment_status="completed")

    Returns:
        dict: {"payment_id", "subscription_id", "external_id", "office_id"}
    """
    created_payments: list[uuid.UUID] = []
    created_subscriptions: list[uuid.UUID] = []

    async def _factory(
        office_id: uuid.UUID = OFFICE_A_ID,
        amount: float = 299.00,
        payment_status: str = "pending",
        subscription_status: str = "active",
        external_id: str | None = None,
    ) -> dict:
        pid = uuid.uuid4()
        sid = uuid.uuid4()
        ext = external_id or f"test-ext-{uuid.uuid4().hex[:8]}"

        async with test_engine.begin() as conn:
            # Subscription (her test icin ayri — tam izolasyon)
            await conn.execute(
                text("""
                    INSERT INTO subscriptions
                        (id, office_id, plan_type, status,
                         start_date, monthly_price, features)
                    VALUES (:id, :off, 'pro', :st, NOW(), 799, '{}')
                """),
                {"id": sid, "off": office_id, "st": subscription_status},
            )
            # Payment
            await conn.execute(
                text("""
                    INSERT INTO payments
                        (id, office_id, subscription_id, amount,
                         status, payment_method, external_id, metadata)
                    VALUES (:id, :off, :sub, :amt, :st, 'iyzico', :ext, '{}')
                """),
                {
                    "id": pid,
                    "off": office_id,
                    "sub": sid,
                    "amt": amount,
                    "st": payment_status,
                    "ext": ext,
                },
            )

        created_payments.append(pid)
        created_subscriptions.append(sid)

        return {
            "payment_id": pid,
            "subscription_id": sid,
            "external_id": ext,
            "office_id": office_id,
        }

    yield _factory

    # Cleanup — FK sirasi: inbox_events → payments → subscriptions
    async with test_engine.begin() as conn:
        await conn.execute(
            text("DELETE FROM inbox_events WHERE source = 'iyzico'")
        )
        for pid in created_payments:
            await conn.execute(
                text("DELETE FROM payments WHERE id = :id"), {"id": pid}
            )
        for sid in created_subscriptions:
            await conn.execute(
                text("DELETE FROM subscriptions WHERE id = :id"), {"id": sid}
            )


@pytest_asyncio.fixture
async def webhook_client(monkeypatch):
    """
    Webhook endpoint testleri icin AsyncClient.

    Patch'ler:
        - async_session_factory → test_session_factory (test DB'ye yonlendir)
        - settings.IYZICO_WEBHOOK_SECRET → WEBHOOK_SECRET (test secret)

    NOT: /webhooks/ prefix PUBLIC_PATH_PREFIXES'te oldugu icin
    JWT middleware atlanir — sadece HMAC signature dogrulanir.
    """
    monkeypatch.setattr(
        "src.modules.payments.router.async_session_factory",
        test_session_factory,
    )
    monkeypatch.setattr(settings, "IYZICO_WEBHOOK_SECRET", WEBHOOK_SECRET)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def clean_inbox_events():
    """Test sonrasi inbox_events tablosunu temizle."""
    yield
    async with test_engine.begin() as conn:
        await conn.execute(
            text("DELETE FROM inbox_events WHERE source IN ('test', 'iyzico')")
        )


# ================================================================
# Outbox / Messaging Test Infrastructure (TASK-043)
# ================================================================
# Deterministic UUIDs for outbox tests ("e" serisi — event)
OUTBOX_EVENT_ID_1 = uuid.UUID("e0000000-0000-0000-0000-000000000001")
OUTBOX_EVENT_ID_2 = uuid.UUID("e0000000-0000-0000-0000-000000000002")
OUTBOX_EVENT_ID_3 = uuid.UUID("e0000000-0000-0000-0000-000000000003")
OUTBOX_EVENT_ID_4 = uuid.UUID("e0000000-0000-0000-0000-000000000004")
OUTBOX_EVENT_ID_5 = uuid.UUID("e0000000-0000-0000-0000-000000000005")

# Aggregate ID for outbox events (deterministic)
OUTBOX_AGGREGATE_ID = uuid.UUID("e0000000-0000-0000-0000-0000000000a0")

# INSERT SQL for outbox events — raw SQL (ORM dependency yok)
_OUTBOX_INSERT_SQL = (
    "INSERT INTO outbox_events "
    "(id, office_id, event_type, aggregate_type, aggregate_id, "
    " payload, status, retry_count, max_retries, locked_at, locked_by, "
    " next_retry_at, error_message) "
    "VALUES "
    "(:id, :office_id, :event_type, :aggregate_type, :aggregate_id, "
    " :payload::jsonb, :status, :retry_count, :max_retries, :locked_at, "
    " :locked_by, :next_retry_at, :error_message)"
)


@pytest.fixture
def outbox_worker() -> OutboxWorker:
    """
    OutboxWorker instance — test session factory ile.

    Worker kendi session'ini acar (poll_and_process icinde).
    test_session_factory superuser'dir — RLS'den etkilenmez.
    """
    return OutboxWorker(test_session_factory)


@pytest.fixture
def mock_messaging_service() -> AsyncMock:
    """
    Mock MessagingService — gercek Telegram API cagrisi yapma.

    Varsayilan davranis: basarili gonderim (success=True).
    Test icinde side_effect ile hata simule edilebilir.
    """
    mock = AsyncMock()
    mock.send_message.return_value = {
        "success": True,
        "message_id": "mock-msg-001",
        "error": None,
    }
    mock.route_message.return_value = "telegram_bot"
    return mock


@pytest.fixture
def fast_retry_policy() -> RetryPolicy:
    """
    Hizli retry policy — testlerde uzun bekleme olmadan retry testi.

    max_retries=3, base_delay=0.1s, max_delay=1s, jitter KAPALI.
    Jitter kapali olmasi delay hesaplamalarini deterministik yapar.
    """
    return RetryPolicy(
        max_retries=3,
        base_delay_seconds=0.1,
        max_delay_seconds=1.0,
        backoff_multiplier=2.0,
        jitter=False,
        jitter_range=0.0,
    )


@pytest.fixture
def dlq_service() -> DLQService:
    """DLQService instance — test session factory ile."""
    return DLQService(test_session_factory)


@pytest.fixture
def outbox_monitor() -> OutboxMonitor:
    """
    OutboxMonitor instance — test session factory ile.

    stuck_threshold_seconds=1 (test icin hizli stuck tespiti).
    OTel metrikleri no-op (test ortaminda OTEL_EXPORTER yok).
    """
    return OutboxMonitor(
        test_session_factory,
        stuck_threshold_seconds=1,  # Test icin 1 saniye (normalde 300s)
    )


@pytest_asyncio.fixture
async def create_outbox_event(ensure_test_offices):
    """
    Factory fixture: committed outbox event olusturur.

    Worker kendi session'ini actigi icin, event'in DB'de COMMITTED
    olmasi gerekir. Bu fixture INSERT + COMMIT yapar.
    Teardown'da tum olusturulan event'leri siler.

    Usage:
        eid = await create_outbox_event(event_type="telegram_message")
        eid = await create_outbox_event(status="dead_letter", retry_count=5)
    """
    created_ids: list[uuid.UUID] = []

    async def _factory(
        event_id: uuid.UUID | None = None,
        office_id: uuid.UUID = OFFICE_A_ID,
        event_type: str = "test.event",
        aggregate_type: str = "TestAggregate",
        aggregate_id: uuid.UUID | None = None,
        payload: dict[str, Any] | None = None,
        status: str = "pending",
        retry_count: int = 0,
        max_retries: int = 5,
        locked_at: str | None = None,
        locked_by: str | None = None,
        next_retry_at: str | None = None,
        error_message: str | None = None,
    ) -> uuid.UUID:
        eid = event_id or uuid.uuid4()
        agg_id = aggregate_id or OUTBOX_AGGREGATE_ID

        async with test_session_factory() as session, session.begin():
            await session.execute(
                text(_OUTBOX_INSERT_SQL),
                {
                    "id": str(eid),
                    "office_id": str(office_id),
                    "event_type": event_type,
                    "aggregate_type": aggregate_type,
                    "aggregate_id": str(agg_id),
                    "payload": json.dumps(payload or {"test": True}),
                    "status": status,
                    "retry_count": retry_count,
                    "max_retries": max_retries,
                    "locked_at": locked_at,
                    "locked_by": locked_by,
                    "next_retry_at": next_retry_at,
                    "error_message": error_message,
                },
            )

        created_ids.append(eid)
        return eid

    yield _factory

    # Teardown: cleanup
    if created_ids:
        async with test_session_factory() as session, session.begin():
            for eid in created_ids:
                await session.execute(
                    text("DELETE FROM outbox_events WHERE id = :id"),
                    {"id": str(eid)},
                )


async def get_outbox_event_status(event_id: uuid.UUID) -> dict[str, Any] | None:
    """
    Helper: Outbox event'in guncel durumunu DB'den okur.

    Test assertion'larinda kullanilir — fixture degildir,
    dogrudan import edilebilir.

    Returns:
        dict: status, retry_count, locked_by, error_message vb.
        None: Event bulunamadi.
    """
    async with test_session_factory() as session:
        result = await session.execute(
            text(
                "SELECT id, status, retry_count, max_retries, locked_at, "
                "       locked_by, processed_at, next_retry_at, error_message, "
                "       event_type, office_id "
                "FROM outbox_events WHERE id = :id"
            ),
            {"id": str(event_id)},
        )
        row = result.fetchone()
        if row is None:
            return None
        return {
            "id": str(row[0]),
            "status": row[1],
            "retry_count": row[2],
            "max_retries": row[3],
            "locked_at": row[4],
            "locked_by": row[5],
            "processed_at": row[6],
            "next_retry_at": row[7],
            "error_message": row[8],
            "event_type": row[9],
            "office_id": str(row[10]),
        }


# ================================================================
# Sync Session (Data Pipeline — TASK-056)
# ================================================================
# psycopg2 sync engine: Celery task'larin kullandigi repository'leri
# gercek PostgreSQL ile test etmek icin (PostGIS, UPSERT, JSONB).
# SQLite KULLANILAMAZ — GEOGRAPHY, ST_GeogFromText, ON CONFLICT
# gibi PostgreSQL-specifik ozellikler test edilmektedir.

SYNC_TEST_DB_URL = (
    f"postgresql+psycopg2://test_user:test_pass"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/emlak_test"
)

_sync_test_engine = create_engine(
    SYNC_TEST_DB_URL,
    echo=False,
    pool_pre_ping=True,
)

sync_test_session_factory = sessionmaker(
    bind=_sync_test_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@pytest.fixture
def sync_session(setup_database) -> Session:
    """
    Sync SQLAlchemy session — data pipeline repository testleri icin.

    psycopg2 driver: Celery task'larin uretim ortaminda kullandigi
    ayni driver ile test yapilir (asyncpg DEGIL).
    Her test sonrasi ROLLBACK — tam izolasyon.

    Kullanim:
        def test_upsert(sync_session):
            upsert_area_analysis(sync_session, data)
            sync_session.flush()
            ...
    """
    session = sync_test_session_factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
