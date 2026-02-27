"""
Emlak Teknoloji Platformu - End-to-End Payment Flow Tests

Tam odeme akisi: webhook → inbox dedup → payment + subscription status guncelleme.

Test Kategorileri:
    A) Tam Akis — payment confirmation, refund
    B) Idempotency — duplicate webhook, cift isleme koruması
    C) Guard Rails — void sonrasi webhook, multi-tenant izolasyon

Altyapi:
    - webhook_client: session factory + settings patched AsyncClient
    - create_test_payment: izole payment + subscription factory
    - Gercek DB islemleri — UNIQUE constraint, FK, status guncelleme
    - Her test izole: kendi subscription + payment + cleanup

Pipeline:
    HTTP POST /webhooks/payments/iyzico
        → HMAC-SHA256 imza dogrulama
        → JSON payload parse
        → InboxService.receive_event() (dedup)
        → _update_payment_and_subscription() (status guncelleme)
        → 200 OK

Referanslar:
    - src/modules/payments/router.py — iyzico_webhook + _update_payment_and_subscription
    - src/modules/payments/webhook.py — verify_webhook_signature
    - src/services/inbox_service.py — InboxService (inbox pattern)
    - src/models/payment.py — Payment (status, paid_at, refunded_at vb.)
    - src/models/subscription.py — Subscription (status, payment_failed_count vb.)
"""

from __future__ import annotations

import hashlib
import hmac
import json
import uuid

from sqlalchemy import select

from src.models.inbox_event import InboxEvent
from src.models.payment import Payment
from src.models.subscription import Subscription
from tests.conftest import (
    OFFICE_A_ID,
    OFFICE_B_ID,
    WEBHOOK_SECRET,
    test_session_factory,
)


def _sign(payload: dict, secret: str = WEBHOOK_SECRET) -> tuple[bytes, str]:
    """Webhook payload'i HMAC-SHA256 ile imzalar."""
    body = json.dumps(payload).encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return body, sig


# ================================================================
# A) Tam Payment Akisi Testleri
# ================================================================


class TestPaymentEndToEndFlow:
    """Tam odeme akisi: webhook → inbox → status guncelleme."""

    async def test_full_payment_confirmation_flow(
        self, webhook_client, create_test_payment
    ) -> None:
        """
        Uctan uca basarili odeme akisi:

        1. Payment olustur (pending)
        2. Webhook gonder (valid signature, success)
        3. InboxEvent olusturuldugunu dogrula
        4. Payment status: completed oldugunu dogrula
        5. paid_at set edildigini dogrula
        6. Subscription status: active, payment_failed_count: 0
        """
        # 1. Payment olustur
        data = await create_test_payment(
            payment_status="pending",
            subscription_status="trial",
        )
        event_id = f"e2e-confirm-{uuid.uuid4().hex[:8]}"

        # 2. Webhook gonder
        payload = {
            "iyziEventId": event_id,
            "iyziEventType": "success",
            "paymentId": data["external_id"],
        }
        body, sig = _sign(payload)

        resp = await webhook_client.post(
            "/webhooks/payments/iyzico",
            content=body,
            headers={"X-IYZ-Signature": sig, "Content-Type": "application/json"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

        # 3-6. DB dogrulamalari
        async with test_session_factory() as session:
            # 3. InboxEvent olusturuldu mu?
            inbox_result = await session.execute(
                select(InboxEvent).where(InboxEvent.event_id == event_id)
            )
            inbox_event = inbox_result.scalar_one_or_none()
            assert inbox_event is not None, "InboxEvent olusturulmali"
            assert inbox_event.source == "iyzico"
            assert inbox_event.event_type == "payment.success"
            assert inbox_event.payload == payload

            # 4-5. Payment durumu
            payment = (
                await session.execute(
                    select(Payment).where(Payment.id == data["payment_id"])
                )
            ).scalar_one()

            assert payment.status == "completed", (
                f"Payment status 'completed' olmali, '{payment.status}' bulundu"
            )
            assert payment.paid_at is not None, "paid_at set edilmeli"
            assert payment.external_status == "success"
            assert payment.error_message is None

            # 6. Subscription durumu
            sub = (
                await session.execute(
                    select(Subscription).where(
                        Subscription.id == data["subscription_id"]
                    )
                )
            ).scalar_one()

            assert sub.status == "active", (
                f"Subscription 'active' olmali, '{sub.status}' bulundu"
            )
            assert sub.payment_failed_count == 0
            assert sub.last_payment_at is not None

    async def test_payment_refund_flow(
        self, webhook_client, create_test_payment
    ) -> None:
        """
        Uctan uca iade akisi:

        1. Completed payment mevcut
        2. Refund webhook gonder
        3. InboxEvent olusturuldugunu dogrula (dedup kaydi)
        4. Payment: status refunded, refunded_at set
        5. Subscription: status cancelled
        """
        # 1. Completed payment olustur
        data = await create_test_payment(
            payment_status="completed",
            subscription_status="active",
        )
        event_id = f"e2e-refund-{uuid.uuid4().hex[:8]}"

        # 2. Refund webhook
        payload = {
            "iyziEventId": event_id,
            "iyziEventType": "refund",
            "paymentId": data["external_id"],
        }
        body, sig = _sign(payload)

        resp = await webhook_client.post(
            "/webhooks/payments/iyzico",
            content=body,
            headers={"X-IYZ-Signature": sig, "Content-Type": "application/json"},
        )
        assert resp.status_code == 200

        # 3-5. DB dogrulamalari
        async with test_session_factory() as session:
            # 3. InboxEvent
            inbox_event = (
                await session.execute(
                    select(InboxEvent).where(InboxEvent.event_id == event_id)
                )
            ).scalar_one_or_none()
            assert inbox_event is not None

            # 4. Payment
            payment = (
                await session.execute(
                    select(Payment).where(Payment.id == data["payment_id"])
                )
            ).scalar_one()

            assert payment.status == "refunded"
            assert payment.refunded_at is not None
            assert payment.external_status == "refund"

            # 5. Subscription
            sub = (
                await session.execute(
                    select(Subscription).where(
                        Subscription.id == data["subscription_id"]
                    )
                )
            ).scalar_one()

            assert sub.status == "cancelled"


# ================================================================
# B) Idempotency Testleri
# ================================================================


class TestPaymentIdempotency:
    """Webhook dedup ve idempotency dogrulamasi."""

    async def test_duplicate_webhook_no_double_update(
        self, webhook_client, create_test_payment
    ) -> None:
        """
        Ayni webhook 2 kez gonderilir:

        1. Payment olustur (pending)
        2. Ayni webhook 2 kez gonder (ayni event_id + ayni body)
        3. Ilk webhook: InboxEvent olusturulur + payment guncellenir
        4. Ikinci webhook: InboxEvent dedup → 200 OK + skip
        5. DB'de sadece 1 InboxEvent olmali

        Bu test inbox dedup'in HTTP katmaninda calistigini dogrular.
        """
        data = await create_test_payment(payment_status="pending")
        event_id = f"e2e-dup-{uuid.uuid4().hex[:8]}"

        payload = {
            "iyziEventId": event_id,
            "iyziEventType": "success",
            "paymentId": data["external_id"],
        }
        body, sig = _sign(payload)
        headers = {"X-IYZ-Signature": sig, "Content-Type": "application/json"}

        # Ilk webhook
        resp1 = await webhook_client.post(
            "/webhooks/payments/iyzico", content=body, headers=headers
        )
        assert resp1.status_code == 200

        # Ikinci webhook — ayni event_id, ayni body
        resp2 = await webhook_client.post(
            "/webhooks/payments/iyzico", content=body, headers=headers
        )
        assert resp2.status_code == 200

        # DB dogrulamalari
        async with test_session_factory() as session:
            # Sadece 1 InboxEvent
            inbox_events = (
                await session.execute(
                    select(InboxEvent).where(InboxEvent.event_id == event_id)
                )
            ).scalars().all()
            assert len(inbox_events) == 1, (
                f"Duplicate webhook icin sadece 1 InboxEvent olmali, "
                f"{len(inbox_events)} bulundu"
            )

            # Payment durumu: completed (tek sefer guncellenmis)
            payment = (
                await session.execute(
                    select(Payment).where(Payment.id == data["payment_id"])
                )
            ).scalar_one()
            assert payment.status == "completed"


# ================================================================
# C) Guard Rails & Multi-Tenant Testleri
# ================================================================


class TestPaymentGuardRails:
    """Sinir kosullari ve multi-tenant izolasyon."""

    async def test_late_webhook_after_refund(
        self, webhook_client, create_test_payment
    ) -> None:
        """
        Refunded payment'e gec kalmis success webhook:

        1. Refunded payment olustur
        2. Success webhook gonder (gec kalmis)
        3. Payment status degisir (mevcut kodda guard YOK)

        NOT: Mevcut _update_payment_and_subscription implementasyonu
        onceki status'u kontrol etmez. Bu test MEVCUT davranisi dogrular.

        TODO: Gelecekte status guard eklenirse bu test guncellenmeli:
            - Beklenen: status DEGISMEMELI (refunded korunmali)
            - Mevcut: status 'completed' olarak degisiyor
        """
        data = await create_test_payment(
            payment_status="refunded",
            subscription_status="cancelled",
        )
        event_id = f"e2e-late-{uuid.uuid4().hex[:8]}"

        payload = {
            "iyziEventId": event_id,
            "iyziEventType": "success",
            "paymentId": data["external_id"],
        }
        body, sig = _sign(payload)

        resp = await webhook_client.post(
            "/webhooks/payments/iyzico",
            content=body,
            headers={"X-IYZ-Signature": sig, "Content-Type": "application/json"},
        )
        assert resp.status_code == 200

        async with test_session_factory() as session:
            payment = (
                await session.execute(
                    select(Payment).where(Payment.id == data["payment_id"])
                )
            ).scalar_one()

            # MEVCUT DAVRANIŞ: status degisiyor (guard yok)
            # Gelecekte bu assertion'i degistir:
            #   assert payment.status == "refunded"  # Guard eklendikten sonra
            assert payment.status == "completed", (
                "Mevcut kodda status guard yok — refunded payment "
                "completed'a donuyor. Bu bilinen bir gap'tir."
            )

    async def test_multi_tenant_payment_isolation(
        self, webhook_client, create_test_payment
    ) -> None:
        """
        Multi-tenant izolasyon:

        1. Office A payment + Office B payment olustur
        2. Office A icin success webhook gonder
        3. Sadece Office A payment guncellenir
        4. Office B payment DEGISMEZ

        Bu test RLS degil, is mantigi izolasyonunu dogrular:
            - Webhook handler external_id ile payment bulur
            - Sadece eslesen payment guncellenir
            - Diger ofislerin payment'lari etkilenmez
        """
        # 1. Iki ofis icin payment olustur
        data_a = await create_test_payment(
            office_id=OFFICE_A_ID,
            payment_status="pending",
        )
        data_b = await create_test_payment(
            office_id=OFFICE_B_ID,
            payment_status="pending",
        )

        # 2. Sadece Office A icin webhook
        event_id = f"e2e-multi-{uuid.uuid4().hex[:8]}"
        payload = {
            "iyziEventId": event_id,
            "iyziEventType": "success",
            "paymentId": data_a["external_id"],
        }
        body, sig = _sign(payload)

        resp = await webhook_client.post(
            "/webhooks/payments/iyzico",
            content=body,
            headers={"X-IYZ-Signature": sig, "Content-Type": "application/json"},
        )
        assert resp.status_code == 200

        # 3-4. DB dogrulamalari
        async with test_session_factory() as session:
            # Office A payment guncellenmis olmali
            payment_a = (
                await session.execute(
                    select(Payment).where(Payment.id == data_a["payment_id"])
                )
            ).scalar_one()
            assert payment_a.status == "completed", (
                f"Office A payment 'completed' olmali, '{payment_a.status}' bulundu"
            )

            # Office B payment DEGISMEMIS olmali
            payment_b = (
                await session.execute(
                    select(Payment).where(Payment.id == data_b["payment_id"])
                )
            ).scalar_one()
            assert payment_b.status == "pending", (
                f"Office B payment 'pending' kalmali, '{payment_b.status}' bulundu — "
                "baska ofisin webhook'u bu payment'i etkilememeli"
            )

    async def test_failure_increments_failed_count(
        self, webhook_client, create_test_payment
    ) -> None:
        """
        Ardisik basarisiz odemeler → payment_failed_count artar.

        1. Payment olustur
        2. Failure webhook #1 gonder → count = 1
        3. Failure webhook #2 gonder → count = 2
        """
        data = await create_test_payment(
            payment_status="pending",
            subscription_status="active",
        )

        for i in range(2):
            event_id = f"e2e-fail-{i}-{uuid.uuid4().hex[:8]}"
            payload = {
                "iyziEventId": event_id,
                "iyziEventType": "failure",
                "paymentId": data["external_id"],
                "errorMessage": f"Failure #{i + 1}",
            }
            body, sig = _sign(payload)

            resp = await webhook_client.post(
                "/webhooks/payments/iyzico",
                content=body,
                headers={
                    "X-IYZ-Signature": sig,
                    "Content-Type": "application/json",
                },
            )
            assert resp.status_code == 200

        # Subscription failed count dogrula
        async with test_session_factory() as session:
            sub = (
                await session.execute(
                    select(Subscription).where(
                        Subscription.id == data["subscription_id"]
                    )
                )
            ).scalar_one()

            assert sub.payment_failed_count == 2, (
                f"2 basarisiz odemeden sonra count=2 olmali, "
                f"{sub.payment_failed_count} bulundu"
            )
            assert sub.status == "past_due"

    async def test_success_after_failure_resets_count(
        self, webhook_client, create_test_payment
    ) -> None:
        """
        Basarisiz sonrasi basarili odeme → payment_failed_count sifirlanir.

        1. Failure webhook → count = 1, status = past_due
        2. Success webhook → count = 0, status = active
        """
        data = await create_test_payment(
            payment_status="pending",
            subscription_status="active",
        )

        # 1. Failure
        fail_payload = {
            "iyziEventId": f"e2e-reset-fail-{uuid.uuid4().hex[:8]}",
            "iyziEventType": "failure",
            "paymentId": data["external_id"],
        }
        body, sig = _sign(fail_payload)
        await webhook_client.post(
            "/webhooks/payments/iyzico",
            content=body,
            headers={"X-IYZ-Signature": sig, "Content-Type": "application/json"},
        )

        # 2. Success
        success_payload = {
            "iyziEventId": f"e2e-reset-ok-{uuid.uuid4().hex[:8]}",
            "iyziEventType": "success",
            "paymentId": data["external_id"],
        }
        body, sig = _sign(success_payload)
        await webhook_client.post(
            "/webhooks/payments/iyzico",
            content=body,
            headers={"X-IYZ-Signature": sig, "Content-Type": "application/json"},
        )

        # Dogrula
        async with test_session_factory() as session:
            sub = (
                await session.execute(
                    select(Subscription).where(
                        Subscription.id == data["subscription_id"]
                    )
                )
            ).scalar_one()

            assert sub.payment_failed_count == 0, (
                "Success sonrasi failed_count sifirlanmali"
            )
            assert sub.status == "active"
