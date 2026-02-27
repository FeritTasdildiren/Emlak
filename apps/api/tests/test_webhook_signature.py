"""
Emlak Teknoloji Platformu - Webhook Signature Verification Tests

iyzico HMAC-SHA256 imza dogrulama unit testleri.

Test Kategorileri:
    - Gecerli imza dogrulamasi
    - Gecersiz/eksik imza reddi
    - Bos body edge case
    - Timing-safe karsilastirma (compare_digest) dogrulamasi
    - Tampered (degistirilmis) body tespiti

Altyapi:
    - Pure unit tests — veritabani veya HTTP client GEREKMEZ
    - Mock Request nesneleri kullanilir
    - Gercek HMAC hesabi yapilir (hardcoded signature KULLANILMAZ)
"""

from __future__ import annotations

import hashlib
import hmac
import inspect
import json
from unittest.mock import AsyncMock, MagicMock

from src.modules.payments.webhook import signature_error_response, verify_webhook_signature

# ================================================================
# Helper: Mock Request Builder
# ================================================================


def _make_request(
    body: bytes,
    headers: dict[str, str] | None = None,
    path: str = "/webhooks/payments/iyzico",
) -> MagicMock:
    """
    Mock Starlette Request nesnesi olusturur.

    Args:
        body: Ham istek govdesi (bytes).
        headers: HTTP header dict (varsayilan: bos).
        path: URL path (varsayilan: webhook endpoint).

    Returns:
        MagicMock: request.body() async, request.headers, request.url.path, request.client.host
    """
    request = MagicMock()
    request.body = AsyncMock(return_value=body)
    request.headers = headers or {}
    request.url.path = path
    request.client = MagicMock()
    request.client.host = "127.0.0.1"
    return request


def _compute_signature(body: bytes, secret: str) -> str:
    """HMAC-SHA256 hex digest hesaplar."""
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


# ================================================================
# A) Webhook Signature Verification Tests
# ================================================================


class TestWebhookSignatureVerification:
    """iyzico HMAC-SHA256 imza dogrulamasi."""

    async def test_valid_signature_passes(self) -> None:
        """Dogru imza → (True, raw_body) doner."""
        secret = "test-secret-key-32chars-minimum!"
        body = json.dumps({"paymentId": "pay-123", "status": "success"}).encode()
        signature = _compute_signature(body, secret)

        request = _make_request(body, {"X-IYZ-Signature": signature})
        is_valid, raw_body = await verify_webhook_signature(request, secret)

        assert is_valid is True
        assert raw_body == body

    async def test_invalid_signature_rejected(self) -> None:
        """Yanlis imza → (False, raw_body) doner."""
        body = json.dumps({"paymentId": "pay-123"}).encode()
        request = _make_request(body, {"X-IYZ-Signature": "deadbeef" * 8})

        is_valid, raw_body = await verify_webhook_signature(request, "real-secret")

        assert is_valid is False
        assert raw_body == body

    async def test_missing_signature_header(self) -> None:
        """X-IYZ-Signature header eksik → rejected."""
        body = json.dumps({"paymentId": "pay-123"}).encode()
        # Header dict'te X-IYZ-Signature yok
        request = _make_request(body, {"Content-Type": "application/json"})

        is_valid, raw_body = await verify_webhook_signature(request, "test-secret")

        assert is_valid is False
        assert raw_body == body

    async def test_empty_body_with_valid_signature(self) -> None:
        """Bos body icin dogru imza → gecerli."""
        secret = "test-secret"
        body = b""
        signature = _compute_signature(body, secret)

        request = _make_request(body, {"X-IYZ-Signature": signature})
        is_valid, raw_body = await verify_webhook_signature(request, secret)

        assert is_valid is True
        assert raw_body == b""

    async def test_empty_body_with_wrong_signature(self) -> None:
        """Bos body + yanlis imza → rejected."""
        body = b""
        request = _make_request(body, {"X-IYZ-Signature": "wrong"})

        is_valid, _raw_body = await verify_webhook_signature(request, "test-secret")

        assert is_valid is False

    def test_timing_safe_comparison_used(self) -> None:
        """
        hmac.compare_digest kullaniliyor (timing attack korumasi).

        Kaynak kodda compare_digest cagrisinin var oldigini dogrular.
        Bu, constant-time string karsilastirmasini garanti eder —
        timing side-channel saldirilarini onler.
        """
        source = inspect.getsource(verify_webhook_signature)
        assert "compare_digest" in source, (
            "verify_webhook_signature fonksiyonunda hmac.compare_digest "
            "kullanilmali — timing attack korumasi icin zorunlu"
        )

    async def test_tampered_body_rejected(self) -> None:
        """
        Body degistirilmis → imza uyusmaz.

        Orjinal body icin hesaplanan imza, degistirilmis body ile uyusmaz.
        Bu, MITM saldiri senaryosunu simule eder.
        """
        secret = "test-secret-key"
        original_body = json.dumps(
            {"paymentId": "pay-123", "amount": "100.00"}
        ).encode()
        tampered_body = json.dumps(
            {"paymentId": "pay-123", "amount": "999999.99"}
        ).encode()

        # Orjinal body icin imza hesapla
        signature = _compute_signature(original_body, secret)

        # Degistirilmis body + orjinal imza gonder
        request = _make_request(tampered_body, {"X-IYZ-Signature": signature})
        is_valid, raw_body = await verify_webhook_signature(request, secret)

        assert is_valid is False, "Tampered body ile imza uyusmamali"
        assert raw_body == tampered_body, "Ham body dogru donmeli (parse icin kullanilir)"

    async def test_different_secrets_produce_different_results(self) -> None:
        """Farkli secret'lar farkli imza uretir — yanlis secret reject edilir."""
        body = json.dumps({"test": True}).encode()
        correct_secret = "correct-secret"
        wrong_secret = "wrong-secret"

        signature = _compute_signature(body, correct_secret)
        request = _make_request(body, {"X-IYZ-Signature": signature})

        # Dogru secret ile dogrula
        is_valid, _ = await verify_webhook_signature(request, correct_secret)
        assert is_valid is True

        # Yanlis secret ile dogrula — request.body() tekrar cagrilacak
        request2 = _make_request(body, {"X-IYZ-Signature": signature})
        is_valid2, _ = await verify_webhook_signature(request2, wrong_secret)
        assert is_valid2 is False


# ================================================================
# B) Signature Error Response Tests
# ================================================================


class TestSignatureErrorResponse:
    """signature_error_response fonksiyonu testleri."""

    def test_returns_403_status_code(self) -> None:
        """403 Forbidden status code doner."""
        request = MagicMock()
        request.state.request_id = "req-test-001"

        response = signature_error_response(request)

        assert response.status_code == 403

    def test_response_body_contains_rfc7807_fields(self) -> None:
        """Yanit RFC 7807 Problem Details formatinda."""
        request = MagicMock()
        request.state.request_id = "req-test-002"

        response = signature_error_response(request)
        body = json.loads(response.body)

        assert body["type"] == "about:blank"
        assert body["title"] == "Forbidden"
        assert body["status"] == 403
        assert "detail" in body

    def test_response_includes_request_id(self) -> None:
        """Yanit icinde request_id bulunur (tracing icin)."""
        request = MagicMock()
        request.state.request_id = "req-trace-xyz"

        response = signature_error_response(request)
        body = json.loads(response.body)

        assert body["request_id"] == "req-trace-xyz"

    def test_response_handles_missing_request_id(self) -> None:
        """request_id yoksa None doner (hata firlatmaz)."""
        request = MagicMock(spec=[])  # state attribute yok
        request.state = MagicMock(spec=[])  # request_id attribute yok

        # getattr(request.state, "request_id", None) → None donmeli
        response = signature_error_response(request)
        body = json.loads(response.body)

        assert body["request_id"] is None
