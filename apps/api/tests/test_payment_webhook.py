"""
Emlak Teknoloji Platformu - Payment Webhook Endpoint Tests

POST /webhooks/payments/iyzico endpoint integration testleri.

Test Kategorileri:
    A) Endpoint Temel Davranislari — imza dogrulama, HTTP status, auth bypass
    B) Payment Status Guncelleme — success/failure/refund webhook → DB state degisimi

Altyapi:
    - webhook_client fixture: session_factory + settings patched AsyncClient
    - create_test_payment fixture: izole subscription + payment olusturur
    - Her test kendi verisini olusturur ve sonra temizler (tam izolasyon)
    - Gercek DB UNIQUE constraint + HMAC signature kullanilir (mock DEGIL)

Referanslar:
    - src/modules/payments/router.py — iyzico_webhook handler
    - src/modules/payments/webhook.py — verify_webhook_signature
    - src/services/inbox_service.py — InboxService.receive_event (dedup)
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
from tests.conftest import WEBHOOK_SECRET, test_session_factory


def _sign(payload: dict, secret: str = WEBHOOK_SECRET) -> tuple[bytes, str]:
    """Webhook payload'i HMAC-SHA256 ile imzalar."""
    body = json.dumps(payload).encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return body, sig


# ================================================================
# A) Endpoint Temel Davranislari
# ================================================================


class TestPaymentWebhookEndpoint:
    """POST /webhooks/payments/iyzico endpoint testleri."""

    async def test_valid_webhook_accepted(
        self, webhook_client, create_test_payment
    ) -> None:
        """Gecerli imza + payload → 200 doner."""
        data = await create_test_payment()

        payload = {
            "iyziEventId": f"evt-{uuid.uuid4().hex[:8]}",
            "iyziEventType": "success",
            "paymentId": data["external_id"],
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
        assert resp.json()["status"] == "ok"

    async def test_invalid_signature_returns_403(self, webhook_client) -> None:
        """Gecersiz imza → 403 Forbidden."""
        body = json.dumps({"paymentId": "xxx"}).encode()

        resp = await webhook_client.post(
            "/webhooks/payments/iyzico",
            content=body,
            headers={
                "X-IYZ-Signature": "invalid-signature-value",
                "Content-Type": "application/json",
            },
        )

        assert resp.status_code == 403
        assert resp.json()["title"] == "Forbidden"

    async def test_missing_signature_returns_403(self, webhook_client) -> None:
        """X-IYZ-Signature header eksik → 403."""
        body = json.dumps({"paymentId": "xxx"}).encode()

        resp = await webhook_client.post(
            "/webhooks/payments/iyzico",
            content=body,
            headers={"Content-Type": "application/json"},
        )

        assert resp.status_code == 403

    async def test_webhook_creates_inbox_event(
        self, webhook_client, create_test_payment
    ) -> None:
        """Gecerli webhook → InboxEvent olusturulur."""
        data = await create_test_payment()
        event_id = f"evt-inbox-{uuid.uuid4().hex[:8]}"

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

        # InboxEvent DB'de olusturulmus mu?
        async with test_session_factory() as session:
            result = await session.execute(
                select(InboxEvent).where(InboxEvent.event_id == event_id)
            )
            inbox_event = result.scalar_one_or_none()

            assert inbox_event is not None, "InboxEvent olusturulmali"
            assert inbox_event.source == "iyzico"
            assert inbox_event.event_type == "payment.success"

    async def test_duplicate_webhook_idempotent(
        self, webhook_client, create_test_payment
    ) -> None:
        """
        Ayni event_id ile ikinci webhook → dedup, 200 doner, cift isleme yok.

        Inbox pattern sayesinde:
            1. Ilk webhook → InboxEvent olusturulur + payment guncellenir
            2. Ikinci webhook → InboxEvent duplicate → 200 OK + skip
        """
        data = await create_test_payment()
        event_id = f"evt-dup-{uuid.uuid4().hex[:8]}"

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
        assert resp1.json()["status"] == "ok"

        # Ikinci webhook — ayni event_id
        resp2 = await webhook_client.post(
            "/webhooks/payments/iyzico", content=body, headers=headers
        )
        assert resp2.status_code == 200
        assert "skipped" in resp2.json().get("detail", "").lower() or \
               resp2.json()["status"] == "ok"

        # InboxEvent sadece 1 tane olmali
        async with test_session_factory() as session:
            result = await session.execute(
                select(InboxEvent).where(InboxEvent.event_id == event_id)
            )
            events = result.scalars().all()
            assert len(events) == 1, "Duplicate event_id icin sadece 1 InboxEvent olmali"

    async def test_webhook_bypasses_jwt_auth(self, webhook_client) -> None:
        """
        /webhooks/ prefix → PUBLIC_PATH_PREFIXES'te, JWT gerekmez.

        Authorization header OLMADAN webhook gonderilir.
        TenantMiddleware atlanir — sadece HMAC signature dogrulanir.
        """
        payload = {
            "iyziEventId": f"evt-auth-{uuid.uuid4().hex[:8]}",
            "iyziEventType": "success",
            "paymentId": "non-existent-payment",
        }
        body, sig = _sign(payload)

        # Authorization header YOK — JWT bypass dogrulamasi
        resp = await webhook_client.post(
            "/webhooks/payments/iyzico",
            content=body,
            headers={
                "X-IYZ-Signature": sig,
                "Content-Type": "application/json",
            },
        )

        # 401/403 JWT hatasi DEĞİL, 200 donmeli
        assert resp.status_code == 200, (
            f"Webhook JWT gerektirmemeli — {resp.status_code} dondü, 200 bekleniyor"
        )

    async def test_webhook_bypasses_tenant_context(
        self, webhook_client, create_test_payment
    ) -> None:
        """
        Webhook endpoint'i tenant context gerektirmez.

        SET LOCAL yapilmadan payment query calisir
        (payments tablosu RLS_TABLES listesinde DEGIL).
        """
        data = await create_test_payment()

        payload = {
            "iyziEventId": f"evt-tenant-{uuid.uuid4().hex[:8]}",
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

    async def test_invalid_json_returns_200(self, webhook_client) -> None:
        """
        Gecersiz JSON payload → 200 doner (iyzico retry onleme).

        iyzico'nun gereksiz retry yapmasini onlemek icin
        her zaman 200 dondurulur (imza gecerli olduktan sonra).
        """
        body = b"this is not json {{{}"
        sig = hmac.new(
            WEBHOOK_SECRET.encode("utf-8"), body, hashlib.sha256
        ).hexdigest()

        resp = await webhook_client.post(
            "/webhooks/payments/iyzico",
            content=body,
            headers={"X-IYZ-Signature": sig, "Content-Type": "application/json"},
        )

        assert resp.status_code == 200
        assert "error" in resp.json().get("status", "")

    async def test_missing_required_fields_returns_200(
        self, webhook_client
    ) -> None:
        """
        Zorunlu alanlar (iyziEventId, iyziEventType) eksik → 200.

        Payload gecerli JSON ama gerekli alanlar yok.
        """
        payload = {"someOtherField": "value"}
        body, sig = _sign(payload)

        resp = await webhook_client.post(
            "/webhooks/payments/iyzico",
            content=body,
            headers={"X-IYZ-Signature": sig, "Content-Type": "application/json"},
        )

        assert resp.status_code == 200
        assert resp.json()["status"] == "error"


# ================================================================
# B) Payment Status Guncelleme
# ================================================================


class TestPaymentStatusUpdate:
    """Odeme durumu guncelleme akisi."""

    async def test_payment_completed_on_success(
        self, webhook_client, create_test_payment
    ) -> None:
        """
        Basarili odeme webhook → payment status: completed, paid_at set.

        Status mapping: success → completed
        Subscription: status → active, payment_failed_count → 0
        """
        data = await create_test_payment(payment_status="pending")

        payload = {
            "iyziEventId": f"evt-ok-{uuid.uuid4().hex[:8]}",
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

        # Payment durumunu dogrula
        async with test_session_factory() as session:
            payment = (
                await session.execute(
                    select(Payment).where(Payment.id == data["payment_id"])
                )
            ).scalar_one()

            assert payment.status == "completed", f"Beklenen: completed, Gelen: {payment.status}"
            assert payment.paid_at is not None, "paid_at set edilmeli"
            assert payment.error_message is None, "Basarili odemede error_message None olmali"
            assert payment.external_status == "success"

            # Subscription durumunu dogrula
            sub = (
                await session.execute(
                    select(Subscription).where(
                        Subscription.id == data["subscription_id"]
                    )
                )
            ).scalar_one()

            assert sub.status == "active"
            assert sub.payment_failed_count == 0
            assert sub.last_payment_at is not None

    async def test_payment_failed(
        self, webhook_client, create_test_payment
    ) -> None:
        """
        Basarisiz odeme webhook → payment status: failed.

        Status mapping: failure → failed
        Subscription: status → past_due, payment_failed_count += 1
        """
        data = await create_test_payment(payment_status="pending")

        payload = {
            "iyziEventId": f"evt-fail-{uuid.uuid4().hex[:8]}",
            "iyziEventType": "failure",
            "paymentId": data["external_id"],
            "errorMessage": "Insufficient funds",
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

            assert payment.status == "failed"
            assert payment.error_message == "Insufficient funds"

            sub = (
                await session.execute(
                    select(Subscription).where(
                        Subscription.id == data["subscription_id"]
                    )
                )
            ).scalar_one()

            assert sub.status == "past_due"
            assert sub.payment_failed_count == 1

    async def test_payment_refund(
        self, webhook_client, create_test_payment
    ) -> None:
        """
        Iade webhook → payment status: refunded, refunded_at set.

        Status mapping: refund → refunded
        Subscription: status → cancelled
        """
        data = await create_test_payment(payment_status="completed")

        payload = {
            "iyziEventId": f"evt-refund-{uuid.uuid4().hex[:8]}",
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

        async with test_session_factory() as session:
            payment = (
                await session.execute(
                    select(Payment).where(Payment.id == data["payment_id"])
                )
            ).scalar_one()

            assert payment.status == "refunded"
            assert payment.refunded_at is not None
            assert payment.external_status == "refund"

            sub = (
                await session.execute(
                    select(Subscription).where(
                        Subscription.id == data["subscription_id"]
                    )
                )
            ).scalar_one()

            assert sub.status == "cancelled"

    async def test_unmapped_event_type_handled(
        self, webhook_client, create_test_payment
    ) -> None:
        """
        Bilinmeyen event type (void, cancel vb.) → loglama, status degismez.

        _IYZICO_STATUS_MAP'te olmayan event type'lar:
            - InboxEvent olusturulur (idempotency kaydı)
            - Payment status DEGISMEZ (new_status = None)
            - 200 OK dondurulur

        NOT: Mevcut kodda void/cancel icin explicit handling YOK.
        Bu event type'lar "unmapped" olarak loglanir.
        """
        data = await create_test_payment(payment_status="completed")

        payload = {
            "iyziEventId": f"evt-void-{uuid.uuid4().hex[:8]}",
            "iyziEventType": "void",  # _IYZICO_STATUS_MAP'te YOK
            "paymentId": data["external_id"],
        }
        body, sig = _sign(payload)

        resp = await webhook_client.post(
            "/webhooks/payments/iyzico",
            content=body,
            headers={"X-IYZ-Signature": sig, "Content-Type": "application/json"},
        )
        assert resp.status_code == 200

        # Payment status degismemis olmali
        async with test_session_factory() as session:
            payment = (
                await session.execute(
                    select(Payment).where(Payment.id == data["payment_id"])
                )
            ).scalar_one()

            assert payment.status == "completed", (
                "Unmapped event type payment status'u degistirmemeli"
            )

    async def test_unknown_payment_external_id_handled(
        self, webhook_client, create_test_payment
    ) -> None:
        """
        Bilinmeyen external_id → loglama yapilir, hata firlatilmaz.

        DB'de karsiligi olmayan paymentId ile webhook geldiginde:
            - InboxEvent olusturulur
            - Payment bulunamaz → uyari loglanir
            - 200 OK dondurulur (exception FIRLATILMAZ)
        """
        # create_test_payment'i sadece fixture cleanup icin cagir
        await create_test_payment()

        payload = {
            "iyziEventId": f"evt-unknown-{uuid.uuid4().hex[:8]}",
            "iyziEventType": "success",
            "paymentId": "non-existent-external-id-xyz",
        }
        body, sig = _sign(payload)

        resp = await webhook_client.post(
            "/webhooks/payments/iyzico",
            content=body,
            headers={"X-IYZ-Signature": sig, "Content-Type": "application/json"},
        )

        # Hata DEĞİL, 200 donmeli
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
