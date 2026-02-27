"""
Emlak Teknoloji Platformu - RLS Integration Test Suite

Row-Level Security policy'lerinin kapsamli dogrulamasi.
Multi-tenant veri izolasyonunun en kritik guvenlik katmani.

Test Kategorileri:
    A) Cross-tenant izolasyon (7 tablo) — her tabloda A↔B erisim engeli
    B) Pool reuse guvenlik — SET LOCAL transaction scope dogrulamasi
    C) Negatif testler — context yokken default deny, gecersiz UUID
    D) Shared properties — cross-office gorunurluk (FOR SELECT ONLY)
    E) Platform admin bypass — admin rolu ile tum user'lara erisim

Altyapi:
    - Tum testler app_user rolüyle calisir (superuser DEGIL)
    - FORCE ROW LEVEL SECURITY aktif — owner bile bypass edemez
    - Seed data: 2 ofis (Alpha, Beta), her birine ait kayitlar
    - Her test rollback ile temizlenir — testler birbirini etkilemez

Referanslar:
    - Migration 002_rls_policies: tenant_isolation + shared_properties + platform_admin_bypass
    - Migration 003_app_user_role: app_user rolu + GRANT'lar
    - Teknik Mimari: current_setting(..., true) missing-ok → NULL → default deny
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import text

from tests.conftest import (
    CONVERSATION_A_ID,
    CONVERSATION_B_ID,
    CUSTOMER_A_ID,
    CUSTOMER_B_ID,
    MESSAGE_A_ID,
    MESSAGE_B_ID,
    NOTIFICATION_A_ID,
    NOTIFICATION_B_ID,
    OFFICE_A_ID,
    OFFICE_B_ID,
    PROPERTY_A_ID,
    PROPERTY_A_SHARED_ID,
    PROPERTY_B_ID,
    SUBSCRIPTION_A_ID,
    SUBSCRIPTION_B_ID,
    USER_A_ID,
    USER_B_ID,
    rls_test_session_factory,
    set_tenant_context,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


# ================================================================
# A) Cross-Tenant Izolasyon Testleri
# ================================================================
# Her RLS-korunakli tablo icin:
#   - Office A context'inde: sadece A kayitlari gorunur
#   - Office B context'inde: sadece B kayitlari gorunur
#   - Karsi ofisin verisine ERISIM ENGELI
# ================================================================


class TestCrossTenantCustomers:
    """customers tablosu — tenant izolasyon dogrulamasi."""

    async def test_office_a_sees_only_own_customers(self, rls_session: AsyncSession) -> None:
        """Office A context'inde sadece A'nin musterileri gorunur."""
        await set_tenant_context(rls_session, OFFICE_A_ID)

        result = await rls_session.execute(text("SELECT id FROM customers"))
        rows = result.fetchall()

        ids = {row[0] for row in rows}
        assert CUSTOMER_A_ID in ids, "Office A kendi musterisini gormeli"
        assert CUSTOMER_B_ID not in ids, "Office B'nin musterisi gorunmemeli"
        assert len(rows) == 1

    async def test_office_b_cannot_see_office_a_customers(self, rls_session: AsyncSession) -> None:
        """Office B context'inde A'nin musterileri gorunmez."""
        await set_tenant_context(rls_session, OFFICE_B_ID)

        result = await rls_session.execute(text("SELECT id FROM customers"))
        rows = result.fetchall()

        ids = {row[0] for row in rows}
        assert CUSTOMER_B_ID in ids, "Office B kendi musterisini gormeli"
        assert CUSTOMER_A_ID not in ids, "Office A'nin musterisi gorunmemeli"
        assert len(rows) == 1


class TestCrossTenantUsers:
    """users tablosu — tenant izolasyon dogrulamasi."""

    async def test_office_a_sees_only_own_users(self, rls_session: AsyncSession) -> None:
        """Office A context'inde sadece A'nin kullanicilari gorunur."""
        await set_tenant_context(rls_session, OFFICE_A_ID)

        result = await rls_session.execute(text("SELECT id FROM users"))
        rows = result.fetchall()

        ids = {row[0] for row in rows}
        assert USER_A_ID in ids
        assert USER_B_ID not in ids

    async def test_office_b_sees_only_own_users(self, rls_session: AsyncSession) -> None:
        """Office B context'inde sadece B'nin kullanicilari gorunur."""
        await set_tenant_context(rls_session, OFFICE_B_ID)

        result = await rls_session.execute(text("SELECT id FROM users"))
        rows = result.fetchall()

        ids = {row[0] for row in rows}
        assert USER_B_ID in ids
        assert USER_A_ID not in ids


class TestCrossTenantProperties:
    """properties tablosu — tenant izolasyon dogrulamasi.

    NOT: Shared property (PROPERTY_A_SHARED_ID) shared_properties policy sayesinde
    B'ye gorunur. Bu test sadece normal (private) property'lerin izolasyonunu dogrular.
    """

    async def test_office_a_sees_own_properties(self, rls_session: AsyncSession) -> None:
        """Office A kendi ilanlarini gorur (private + shared dahil)."""
        await set_tenant_context(rls_session, OFFICE_A_ID)

        result = await rls_session.execute(text("SELECT id FROM properties"))
        rows = result.fetchall()

        ids = {row[0] for row in rows}
        assert PROPERTY_A_ID in ids, "A'nin private ilani gorunmeli"
        assert PROPERTY_A_SHARED_ID in ids, "A'nin shared ilani gorunmeli"
        assert PROPERTY_B_ID not in ids, "B'nin ilani gorunmemeli"

    async def test_office_b_sees_own_plus_shared(self, rls_session: AsyncSession) -> None:
        """Office B kendi ilani + A'nin shared ilani gorur, A'nin private'ini GORMEZ."""
        await set_tenant_context(rls_session, OFFICE_B_ID)

        result = await rls_session.execute(text("SELECT id FROM properties"))
        rows = result.fetchall()

        ids = {row[0] for row in rows}
        assert PROPERTY_B_ID in ids, "B'nin kendi ilani gorunmeli"
        assert PROPERTY_A_SHARED_ID in ids, (
            "A'nin shared ilani gorunmeli (shared_properties policy)"
        )
        assert PROPERTY_A_ID not in ids, "A'nin private ilani gorunmemeli"


class TestCrossTenantConversations:
    """conversations tablosu — tenant izolasyon dogrulamasi."""

    async def test_office_a_sees_only_own_conversations(self, rls_session: AsyncSession) -> None:
        await set_tenant_context(rls_session, OFFICE_A_ID)

        result = await rls_session.execute(text("SELECT id FROM conversations"))
        rows = result.fetchall()

        ids = {row[0] for row in rows}
        assert CONVERSATION_A_ID in ids
        assert CONVERSATION_B_ID not in ids
        assert len(rows) == 1

    async def test_office_b_cannot_see_office_a_conversations(
        self, rls_session: AsyncSession
    ) -> None:
        await set_tenant_context(rls_session, OFFICE_B_ID)

        result = await rls_session.execute(text("SELECT id FROM conversations"))
        rows = result.fetchall()

        ids = {row[0] for row in rows}
        assert CONVERSATION_B_ID in ids
        assert CONVERSATION_A_ID not in ids


class TestCrossTenantMessages:
    """messages tablosu — tenant izolasyon dogrulamasi.

    Messages.office_id denormalize edilmistir (Conversation'dan kopyalenir).
    RLS policy dogrudan bu alan uzerinden calisir — JOIN gerekmez.
    """

    async def test_office_a_sees_only_own_messages(self, rls_session: AsyncSession) -> None:
        await set_tenant_context(rls_session, OFFICE_A_ID)

        result = await rls_session.execute(text("SELECT id FROM messages"))
        rows = result.fetchall()

        ids = {row[0] for row in rows}
        assert MESSAGE_A_ID in ids
        assert MESSAGE_B_ID not in ids

    async def test_office_b_sees_only_own_messages(self, rls_session: AsyncSession) -> None:
        await set_tenant_context(rls_session, OFFICE_B_ID)

        result = await rls_session.execute(text("SELECT id FROM messages"))
        rows = result.fetchall()

        ids = {row[0] for row in rows}
        assert MESSAGE_B_ID in ids
        assert MESSAGE_A_ID not in ids


class TestCrossTenantNotifications:
    """notifications tablosu — tenant izolasyon dogrulamasi."""

    async def test_office_a_sees_only_own_notifications(self, rls_session: AsyncSession) -> None:
        await set_tenant_context(rls_session, OFFICE_A_ID)

        result = await rls_session.execute(text("SELECT id FROM notifications"))
        rows = result.fetchall()

        ids = {row[0] for row in rows}
        assert NOTIFICATION_A_ID in ids
        assert NOTIFICATION_B_ID not in ids

    async def test_office_b_sees_only_own_notifications(self, rls_session: AsyncSession) -> None:
        await set_tenant_context(rls_session, OFFICE_B_ID)

        result = await rls_session.execute(text("SELECT id FROM notifications"))
        rows = result.fetchall()

        ids = {row[0] for row in rows}
        assert NOTIFICATION_B_ID in ids
        assert NOTIFICATION_A_ID not in ids


class TestCrossTenantSubscriptions:
    """subscriptions tablosu — tenant izolasyon dogrulamasi."""

    async def test_office_a_sees_only_own_subscriptions(self, rls_session: AsyncSession) -> None:
        await set_tenant_context(rls_session, OFFICE_A_ID)

        result = await rls_session.execute(text("SELECT id FROM subscriptions"))
        rows = result.fetchall()

        ids = {row[0] for row in rows}
        assert SUBSCRIPTION_A_ID in ids
        assert SUBSCRIPTION_B_ID not in ids
        assert len(rows) == 1

    async def test_office_b_sees_only_own_subscriptions(self, rls_session: AsyncSession) -> None:
        await set_tenant_context(rls_session, OFFICE_B_ID)

        result = await rls_session.execute(text("SELECT id FROM subscriptions"))
        rows = result.fetchall()

        ids = {row[0] for row in rows}
        assert SUBSCRIPTION_B_ID in ids
        assert SUBSCRIPTION_A_ID not in ids


# ================================================================
# B) Pool Reuse Guvenlik Testleri
# ================================================================
# SET LOCAL transaction-scoped'dir. COMMIT/ROLLBACK ile temizlenir.
# Connection pool'dan alinan baglantida onceki tenant verisi SIZMAMALI.
# ================================================================


class TestPoolReuse:
    """Connection pool reuse'da tenant context sizintisi kontrolu."""

    async def test_set_local_cleared_after_commit(self, setup_rls) -> None:
        """
        Transaction 1: Office A context set → A verisini gor.
        Transaction 2: Context set ETME → 0 satir donmeli (default deny).

        SET LOCAL'in COMMIT ile temizlendigini dogrular.
        Pool'dan ayni connection alinsa bile onceki tenant etkisiz.
        """
        # Transaction 1: Office A context
        async with rls_test_session_factory() as session, session.begin():
            await set_tenant_context(session, OFFICE_A_ID)
            result = await session.execute(text("SELECT COUNT(*) FROM customers"))
            count = result.scalar()
            assert count > 0, "Office A'nin musterileri gorunmeli"
        # Transaction commit edildi — SET LOCAL temizlendi

        # Transaction 2: Hic SET LOCAL yapmadan sorgu
        async with rls_test_session_factory() as session, session.begin():
            result = await session.execute(text("SELECT COUNT(*) FROM customers"))
            count = result.scalar()
            assert count == 0, (
                "SET LOCAL yapilmadan 0 satir donmeli — "
                "onceki transaction'in tenant context'i sizmamis olmali"
            )

    async def test_set_local_cleared_after_rollback(self, setup_rls) -> None:
        """
        Transaction 1: Office A context set → ROLLBACK.
        Transaction 2: Context set ETME → 0 satir donmeli.

        SET LOCAL'in ROLLBACK ile de temizlendigini dogrular.
        """
        # Transaction 1: Office A context + explicit rollback
        async with rls_test_session_factory() as session:
            await session.begin()
            await set_tenant_context(session, OFFICE_A_ID)
            result = await session.execute(text("SELECT COUNT(*) FROM customers"))
            assert result.scalar() > 0
            await session.rollback()  # Explicit rollback

        # Transaction 2: Temiz — SET LOCAL olmadan
        async with rls_test_session_factory() as session, session.begin():
            result = await session.execute(text("SELECT COUNT(*) FROM customers"))
            assert result.scalar() == 0, "Rollback sonrasi context sizmamis olmali"

    async def test_sequential_tenant_switch(self, setup_rls) -> None:
        """
        Ardisik transaction'larda tenant degistirme:
        1. Transaction 1 → Office A → A verisi
        2. Transaction 2 → Office B → B verisi (A verisi YATIRILMAMALI)

        Pool reuse senaryosunda veri izolasyonunun korundugunun dogrulamasi.
        """
        # Transaction 1: Office A
        async with rls_test_session_factory() as session, session.begin():
            await set_tenant_context(session, OFFICE_A_ID)
            result = await session.execute(text("SELECT id FROM customers"))
            ids_a = {row[0] for row in result.fetchall()}
            assert CUSTOMER_A_ID in ids_a
            assert CUSTOMER_B_ID not in ids_a

        # Transaction 2: Office B (ayni pool, potansiyel ayni connection)
        async with rls_test_session_factory() as session, session.begin():
            await set_tenant_context(session, OFFICE_B_ID)
            result = await session.execute(text("SELECT id FROM customers"))
            ids_b = {row[0] for row in result.fetchall()}
            assert CUSTOMER_B_ID in ids_b, "B'nin musterisi gorunmeli"
            assert CUSTOMER_A_ID not in ids_b, "A'nin musterisi sizmamis olmali"


# ================================================================
# C) Negatif Testler
# ================================================================
# Default deny: context yokken hic veri donmemeli.
# Invalid UUID: gecersiz office_id ile hic veri donmemeli.
# FORCE RLS: app_user'in bypass girisimi basarisiz olmali.
# ================================================================


class TestNegativeScenarios:
    """RLS'in reddetmesi gereken senaryolar."""

    async def test_no_tenant_context_returns_empty(self, rls_session: AsyncSession) -> None:
        """
        SET LOCAL yapilmadan sorgu → 0 satir.

        current_setting('app.current_office_id', true) → NULL (missing-ok)
        NULL::uuid = office_id karsilastirmasi → FALSE → hic satir uyusmaz.
        Bu, "default deny" davranisinin dogrulamasidir.
        """
        # Kasitli olarak set_tenant_context CAGIRMIYORUZ
        result = await rls_session.execute(text("SELECT COUNT(*) FROM customers"))
        assert result.scalar() == 0, "Tenant context olmadan veri donmemeli (default deny)"

        result = await rls_session.execute(text("SELECT COUNT(*) FROM users"))
        assert result.scalar() == 0, "Users tablosunda da default deny gecerli olmali"

        result = await rls_session.execute(text("SELECT COUNT(*) FROM properties"))
        # Shared properties policy: is_shared=true AND share_visibility='network'
        # Shared property context'siz de gorunebilir (permissive OR)
        count = result.scalar()
        assert count <= 1, (
            "Context yokken sadece shared property gorunmeli (en fazla 1), "
            f"ama {count} satir dondu"
        )

    async def test_invalid_uuid_returns_empty(self, rls_session: AsyncSession) -> None:
        """
        Gecersiz (var olmayan) office_id ile SET LOCAL → 0 satir.

        UUID formati gecerli ama veritabaninda boyle bir ofis yok.
        Hicbir satirin office_id'si bu UUID ile eslesemez → 0 satir.
        """
        fake_office_id = uuid.UUID("deadbeef-dead-dead-dead-deaddeadbeef")
        await set_tenant_context(rls_session, fake_office_id)

        for table in [
            "customers",
            "users",
            "conversations",
            "messages",
            "notifications",
            "subscriptions",
        ]:
            result = await rls_session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            assert count == 0, f"{table}: gecersiz office_id ile {count} satir dondu, 0 bekleniyor"

    async def test_force_rls_prevents_bypass(self, rls_session: AsyncSession) -> None:
        """
        FORCE ROW LEVEL SECURITY aktif — app_user table owner olmasa bile
        (zaten degil) RLS bypass YAPILAMAZ.

        Bu test, app_user'in dogrudan tum verilere erisenedigini dogrular.
        SET LOCAL olmadan herhangi bir tabloya erisim denenir → 0 satir.

        NOT: Gercek superuser (postgres) FORCE RLS'i bile bypass eder.
        Ama app_user superuser DEGIL — FORCE RLS tam etkili.
        """
        # SET LOCAL yapmadan tum tablolari tara
        total_accessible = 0
        for table in [
            "customers",
            "users",
            "conversations",
            "messages",
            "notifications",
            "subscriptions",
        ]:
            result = await rls_session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            total_accessible += result.scalar() or 0

        assert total_accessible == 0, (
            f"app_user RLS'i bypass edemedi ama {total_accessible} satir erisilebilir "
            "— FORCE RLS calisiyor olmali"
        )


# ================================================================
# D) Shared Properties (Cross-Office Gorunurluk) Testleri
# ================================================================
# shared_properties policy: FOR SELECT
# USING (is_shared = true AND share_visibility = 'network')
#
# Permissive OR: tenant_isolation VEYA shared_properties
# → Baska ofisin shared ilani SELECT ile gorunur, UPDATE/DELETE ile GORUNMEZ.
# ================================================================


class TestSharedProperties:
    """properties tablosu — cross-office paylasim policy dogrulamasi."""

    async def test_shared_property_visible_to_other_office(
        self, rls_session: AsyncSession
    ) -> None:
        """
        Office B, Office A'nin shared (network) property'sini gorebilir.

        Policy: is_shared=true AND share_visibility='network' → FOR SELECT gorunur.
        tenant_isolation || shared_properties = permissive OR.
        """
        await set_tenant_context(rls_session, OFFICE_B_ID)

        result = await rls_session.execute(
            text("SELECT id, title FROM properties WHERE id = :pid"),
            {"pid": PROPERTY_A_SHARED_ID},
        )
        row = result.fetchone()

        assert row is not None, "A'nin shared property'si B'ye gorunmeli"
        assert row[1] == "Villa Alpha Shared"

    async def test_non_shared_property_invisible_to_other_office(
        self, rls_session: AsyncSession
    ) -> None:
        """
        Office B, Office A'nin private property'sini GOREMEZ.

        Property A: is_shared=false, share_visibility='private'
        → Ne tenant_isolation ne shared_properties eslesiyor.
        """
        await set_tenant_context(rls_session, OFFICE_B_ID)

        result = await rls_session.execute(
            text("SELECT id FROM properties WHERE id = :pid"),
            {"pid": PROPERTY_A_ID},
        )
        row = result.fetchone()

        assert row is None, "A'nin private property'si B'ye gorunmemeli"

    async def test_shared_property_read_only_for_other_office(
        self, rls_session: AsyncSession
    ) -> None:
        """
        Office B, Office A'nin shared property'sini UPDATE edemez.

        shared_properties policy FOR SELECT ONLY.
        UPDATE icin sadece tenant_isolation gecerli:
            office_id = B → A'nin property'si eslesmiyor → 0 row affected.
        """
        await set_tenant_context(rls_session, OFFICE_B_ID)

        # UPDATE denemesi — 0 row affected olmali
        result = await rls_session.execute(
            text("UPDATE properties SET title = 'Hacked!' WHERE id = :pid"),
            {"pid": PROPERTY_A_SHARED_ID},
        )

        assert result.rowcount == 0, (
            "Office B, A'nin shared property'sini UPDATE edebilmemeli — "
            "shared_properties policy FOR SELECT ONLY"
        )

    async def test_shared_property_not_deletable_by_other_office(
        self, rls_session: AsyncSession
    ) -> None:
        """
        Office B, Office A'nin shared property'sini DELETE edemez.

        DELETE icin sadece tenant_isolation gecerli:
            office_id = B → A'nin property'si eslesmiyor → 0 row affected.
        """
        await set_tenant_context(rls_session, OFFICE_B_ID)

        result = await rls_session.execute(
            text("DELETE FROM properties WHERE id = :pid"),
            {"pid": PROPERTY_A_SHARED_ID},
        )

        assert result.rowcount == 0, "Office B, A'nin shared property'sini DELETE edebilmemeli"


# ================================================================
# E) Platform Admin Bypass Testleri
# ================================================================
# platform_admin_bypass policy: FOR ALL on users
# USING (current_setting('app.current_user_role', true) = 'platform_admin')
#
# Platform admin: tum ofislerdeki tum kullanicilari gorebilir.
# Normal rol: sadece kendi ofisinin kullanicilarini gorur.
# ================================================================


class TestPlatformAdminBypass:
    """users tablosu — platform_admin_bypass policy dogrulamasi."""

    async def test_platform_admin_sees_all_users(self, rls_session: AsyncSession) -> None:
        """
        platform_admin rolü ile tum ofislerin kullanicilari gorunur.

        Policy: current_setting('app.current_user_role') = 'platform_admin' → FOR ALL
        Permissive OR: tenant_isolation || platform_admin_bypass
        → Platform admin tum user'lari gorur.
        """
        # Office A context ama platform_admin rolu
        await set_tenant_context(rls_session, OFFICE_A_ID, role="platform_admin")

        result = await rls_session.execute(text("SELECT id FROM users"))
        rows = result.fetchall()

        ids = {row[0] for row in rows}
        assert USER_A_ID in ids, "Platform admin kendi ofisinin kullanicilarini gormeli"
        assert USER_B_ID in ids, "Platform admin diger ofisin kullanicilarini da gormeli"
        assert len(rows) >= 2, f"En az 2 user gorunmeli, {len(rows)} goruldu"

    async def test_non_admin_cannot_see_other_office_users(
        self, rls_session: AsyncSession
    ) -> None:
        """
        Normal (agent) rolü ile sadece kendi ofisinin kullanicilari gorunur.

        tenant_isolation: office_id = A → sadece A user'lari
        platform_admin_bypass: role='agent' ≠ 'platform_admin' → FALSE
        OR → sadece tenant_isolation gecerli.
        """
        await set_tenant_context(rls_session, OFFICE_A_ID, role="agent")

        result = await rls_session.execute(text("SELECT id FROM users"))
        rows = result.fetchall()

        ids = {row[0] for row in rows}
        assert USER_A_ID in ids, "Agent kendi ofisinin kullanicilarini gormeli"
        assert USER_B_ID not in ids, "Agent baska ofisin kullanicilarini gormemeli"

    async def test_platform_admin_can_modify_other_office_users(
        self, rls_session: AsyncSession
    ) -> None:
        """
        platform_admin_bypass FOR ALL policy'si:
        Admin, baska ofisin kullanicisini UPDATE edebilir.

        NOT: Bu test UPDATE denemesi yapar, rollback ile geri alinir.
        """
        await set_tenant_context(rls_session, OFFICE_A_ID, role="platform_admin")

        # Office B'nin kullanicisini guncelle
        result = await rls_session.execute(
            text("UPDATE users SET full_name = 'Updated By Admin' WHERE id = :uid"),
            {"uid": USER_B_ID},
        )

        assert result.rowcount == 1, (
            "Platform admin baska ofisin kullanicisini guncelleyebilmeli "
            "(platform_admin_bypass FOR ALL)"
        )
        # NOT: rls_session fixture rollback yapar — degisiklik kalici degil
