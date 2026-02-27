"""
Emlak Teknoloji Platformu - RetryPolicy Unit Tests (TASK-043)

RetryPolicy dataclass, error classification ve policy matching testleri.

Test edilen bilesenler:
    - classify_exception(): Exception tipi siniflandirma
    - RetryPolicy: Frozen dataclass, backoff hesaplama, should_retry
    - get_policy_for_event(): Event tipi → policy eslestirme
    - DEFAULT_POLICIES: Onceden tanimli politika degerleri

Kirmizi cizgiler:
    - RetryPolicy frozen (immutable) olmali
    - Bilinmeyen exception → transient (guvenli taraf)
    - Jitter deterministik test edilebilmeli (jitter=False ile)
    - Delay max_delay_seconds'u asamaz
"""

from __future__ import annotations

import dataclasses

import pytest

from src.services.retry_policy import (
    DEFAULT_POLICIES,
    RetryPolicy,
    classify_exception,
    get_policy_for_event,
)


# ================================================================
# Test Error Classification
# ================================================================
class TestErrorClassification:
    """
    Exception tipi siniflandirma testleri.

    classify_exception() string-based class name matching kullanir.
    Bu testler farkli exception tipleri icin dogru sinifi dogrular.
    """

    def test_connection_error_is_transient(self):
        """ConnectionError → transient: gecici ag hatasi, retry yapilabilir."""
        exc = ConnectionError("Connection refused")
        assert classify_exception(exc) == "transient"

    def test_timeout_error_is_transient(self):
        """TimeoutError → transient: gecici timeout, retry yapilabilir."""
        exc = TimeoutError("Request timed out")
        assert classify_exception(exc) == "transient"

    def test_connection_refused_error_is_transient(self):
        """ConnectionRefusedError → transient: sunucu gecici olarak ulasılamaz."""
        exc = ConnectionRefusedError("Connection refused")
        assert classify_exception(exc) == "transient"

    def test_os_error_is_transient(self):
        """OSError → transient: gecici I/O hatasi."""
        exc = OSError("Network unreachable")
        assert classify_exception(exc) == "transient"

    def test_validation_error_is_permanent(self):
        """ValidationError → permanent: veri hatasi, retry anlamsiz."""

        class ValidationError(Exception):
            pass

        exc = ValidationError("Invalid payload")
        assert classify_exception(exc) == "permanent"

    def test_value_error_is_permanent(self):
        """ValueError → permanent: gecersiz deger, retry ile duzelmez."""
        exc = ValueError("Invalid value")
        assert classify_exception(exc) == "permanent"

    def test_type_error_is_permanent(self):
        """TypeError → permanent: tip hatasi, retry ile duzelmez."""
        exc = TypeError("Expected str, got int")
        assert classify_exception(exc) == "permanent"

    def test_key_error_is_permanent(self):
        """KeyError → permanent: eksik key, veri sorunu."""
        exc = KeyError("missing_field")
        assert classify_exception(exc) == "permanent"

    def test_http_5xx_status_is_transient(self):
        """HTTP 5xx status_code → transient: sunucu hatasi, retry yapilabilir."""

        class HttpError(Exception):
            def __init__(self, status_code: int) -> None:
                self.status_code = status_code

        exc = HttpError(502)
        assert classify_exception(exc) == "transient"

    def test_http_503_is_transient(self):
        """HTTP 503 Service Unavailable → transient."""

        class HttpError(Exception):
            def __init__(self, status_code: int) -> None:
                self.status_code = status_code

        exc = HttpError(503)
        assert classify_exception(exc) == "transient"

    def test_http_4xx_status_is_permanent(self):
        """HTTP 4xx status_code → permanent: client hatasi, retry anlamsiz."""

        class HttpError(Exception):
            def __init__(self, status_code: int) -> None:
                self.status_code = status_code

        exc = HttpError(422)
        assert classify_exception(exc) == "permanent"

    def test_http_404_is_permanent(self):
        """HTTP 404 Not Found → permanent: kaynak yok, retry duzeltmez."""

        class HttpError(Exception):
            def __init__(self, status_code: int) -> None:
                self.status_code = status_code

        exc = HttpError(404)
        assert classify_exception(exc) == "permanent"

    def test_unknown_error_is_unknown(self):
        """
        Bilinmeyen exception → 'unknown' (guvenli taraf).

        classify_exception 'unknown' doner, should_retry() bunu
        transient gibi degerlendirir (retry dene).
        """

        class WeirdCustomError(Exception):
            pass

        exc = WeirdCustomError("Something unusual")
        assert classify_exception(exc) == "unknown"

    def test_status_attr_as_string_code(self):
        """status attribute string olsa da int'e cevirilmeli."""

        class HttpResponseError(Exception):
            def __init__(self) -> None:
                self.status = "500"

        exc = HttpResponseError()
        assert classify_exception(exc) == "transient"


# ================================================================
# Test RetryPolicy Calculation
# ================================================================
class TestRetryPolicyCalculation:
    """
    RetryPolicy hesaplama testleri.

    Exponential backoff, jitter, max delay cap ve should_retry
    karar mantigi test edilir.
    """

    def test_frozen_dataclass_immutable(self):
        """RetryPolicy frozen=True — attribute degistirilemez."""
        policy = RetryPolicy()
        with pytest.raises(dataclasses.FrozenInstanceError):
            policy.max_retries = 10  # type: ignore[misc]

    def test_default_values(self):
        """Varsayilan degerler dogru olmali."""
        policy = RetryPolicy()
        assert policy.max_retries == 5
        assert policy.base_delay_seconds == 10.0
        assert policy.max_delay_seconds == 3600.0
        assert policy.backoff_multiplier == 2.0
        assert policy.jitter is True
        assert policy.jitter_range == 0.25

    def test_calculate_delay_first_retry_no_jitter(self):
        """
        Ilk retry (count=1): base_delay * multiplier^1.

        jitter=False ile deterministik test.
        delay = 10 * 2^1 = 20.0
        """
        policy = RetryPolicy(
            base_delay_seconds=10.0,
            backoff_multiplier=2.0,
            jitter=False,
        )
        delay = policy.calculate_next_retry(retry_count=1)
        assert delay == 20.0

    def test_calculate_delay_zero_retry(self):
        """
        Ilk deneme (count=0): base_delay * multiplier^0 = base_delay.
        """
        policy = RetryPolicy(
            base_delay_seconds=10.0,
            backoff_multiplier=2.0,
            jitter=False,
        )
        delay = policy.calculate_next_retry(retry_count=0)
        assert delay == 10.0

    def test_calculate_delay_exponential_growth(self):
        """
        Exponential buyume: delay = base * multiplier^count.

        count=3 → 10 * 2^3 = 80.0
        """
        policy = RetryPolicy(
            base_delay_seconds=10.0,
            backoff_multiplier=2.0,
            jitter=False,
        )
        delay = policy.calculate_next_retry(retry_count=3)
        assert delay == 80.0

    def test_calculate_delay_max_cap(self):
        """
        Delay max_delay_seconds ust sinirini asamaz.

        count=20 → 10 * 2^20 = 10,485,760 ama max_delay=100 → 100.0
        """
        policy = RetryPolicy(
            base_delay_seconds=10.0,
            backoff_multiplier=2.0,
            max_delay_seconds=100.0,
            jitter=False,
        )
        delay = policy.calculate_next_retry(retry_count=20)
        assert delay == 100.0

    def test_jitter_adds_randomness(self):
        """
        Jitter aktifken ayni parametrelerle farkli delay'ler uretir.

        100 hesaplamada en az 2 farkli deger gormeliyiz.
        """
        policy = RetryPolicy(
            base_delay_seconds=10.0,
            backoff_multiplier=2.0,
            jitter=True,
            jitter_range=0.25,
        )
        delays = {policy.calculate_next_retry(retry_count=3) for _ in range(100)}
        # Jitter ile en az birkac farkli deger olmali
        assert len(delays) > 1, "Jitter farkli delay uretmeli"

    def test_jitter_stays_within_range(self):
        """
        Jitter degerleri beklenen aralikta olmali.

        base_delay=10, count=0 → nominal=10.0
        jitter_range=0.25 → 10 * 0.25 = 2.5 sapma
        Beklenen aralik: [7.5, 12.5] ama min 1.0 guard var.
        """
        policy = RetryPolicy(
            base_delay_seconds=10.0,
            backoff_multiplier=2.0,
            jitter=True,
            jitter_range=0.25,
        )
        for _ in range(200):
            delay = policy.calculate_next_retry(retry_count=0)
            # Nominal 10.0, jitter +/- %25 → [7.5, 12.5]
            assert 7.0 <= delay <= 13.0, f"Delay aralik disinda: {delay}"

    def test_delay_minimum_is_one_second(self):
        """
        Delay minimum 1.0 saniye — negatif veya sifir olamaz.

        Cok kucuk base_delay + buyuk negatif jitter durumunda bile >= 1.0.
        """
        policy = RetryPolicy(
            base_delay_seconds=0.01,
            backoff_multiplier=1.0,
            jitter=True,
            jitter_range=0.99,
        )
        for _ in range(100):
            delay = policy.calculate_next_retry(retry_count=0)
            assert delay >= 1.0, f"Delay 1.0'dan kucuk olamaz: {delay}"

    def test_should_retry_within_limit(self):
        """retry_count < max_retries → True (transient error ile)."""
        policy = RetryPolicy(max_retries=5)
        assert policy.should_retry(retry_count=3, exception=ConnectionError()) is True

    def test_should_not_retry_max_exceeded(self):
        """retry_count >= max_retries → False (limit asildi)."""
        policy = RetryPolicy(max_retries=5)
        assert policy.should_retry(retry_count=5, exception=ConnectionError()) is False
        assert policy.should_retry(retry_count=6, exception=ConnectionError()) is False

    def test_should_not_retry_permanent_error(self):
        """Permanent error → False (retry anlamsiz, direkt DLQ)."""
        policy = RetryPolicy(max_retries=5)
        assert policy.should_retry(retry_count=1, exception=ValueError("bad")) is False

    def test_should_retry_unknown_error(self):
        """
        Bilinmeyen error → True (guvenli taraf: retry dene).

        classify_exception 'unknown' doner → should_retry bunu
        permanent olmayan olarak degerlendirir.
        """

        class MysteryError(Exception):
            pass

        policy = RetryPolicy(max_retries=5)
        assert policy.should_retry(retry_count=1, exception=MysteryError()) is True

    def test_should_retry_no_exception(self):
        """Exception verilmezse (genel failure) → True."""
        policy = RetryPolicy(max_retries=5)
        assert policy.should_retry(retry_count=1, exception=None) is True

    def test_policy_level_permanent_override(self):
        """
        Policy-seviyesi permanent_exceptions override.

        Normalde 'unknown' olan bir exception, policy'de
        permanent_exceptions'a eklenirse DLQ'ya gider.
        """

        class SpecialError(Exception):
            pass

        policy = RetryPolicy(
            max_retries=5,
            permanent_exceptions=frozenset({"SpecialError"}),
        )
        assert policy.should_retry(retry_count=1, exception=SpecialError()) is False

    def test_policy_level_retryable_override(self):
        """
        Policy-seviyesi retryable_exceptions override.

        Normalde 'permanent' olan ValueError, policy'de
        retryable_exceptions'a eklenirse retry yapilir.
        """
        policy = RetryPolicy(
            max_retries=5,
            retryable_exceptions=frozenset({"ValueError"}),
        )
        assert policy.should_retry(retry_count=1, exception=ValueError("test")) is True


# ================================================================
# Test Policy Matching
# ================================================================
class TestPolicyMatching:
    """
    Event tipi → RetryPolicy eslestirme testleri.

    get_policy_for_event() esleme stratejisi:
    1. Tam esleme (nokta → alt cizgi donusumu)
    2. Prefix esleme (en uzun match)
    3. Kategori esleme (ilk segment)
    4. Fallback → "*"
    """

    def test_exact_match(self):
        """
        Tam esleme: "payment.webhook" → payment_webhook policy.

        Nokta alt cizgiye donusturulur.
        """
        policy = get_policy_for_event("payment.webhook")
        assert policy.max_retries == 10  # payment_webhook policy
        assert policy.base_delay_seconds == 30.0

    def test_exact_match_notification(self):
        """notification → notification policy (max_retries=3)."""
        policy = get_policy_for_event("notification")
        assert policy.max_retries == 3
        assert policy.base_delay_seconds == 5.0

    def test_exact_match_telegram(self):
        """telegram.message → telegram_message policy (max_retries=5)."""
        policy = get_policy_for_event("telegram.message")
        assert policy.max_retries == 5
        assert policy.base_delay_seconds == 15.0

    def test_prefix_match(self):
        """
        Prefix esleme: "payment.webhook.iyzico" → payment_webhook policy.

        "payment_webhook_iyzico" prefix'i "payment_webhook" ile eslesir.
        """
        policy = get_policy_for_event("payment.webhook.iyzico")
        assert policy.max_retries == 10  # payment_webhook

    def test_category_match(self):
        """
        Kategori esleme: "payment.completed" ilk segment "payment"
        → "payment_webhook" key'i "payment" ile basladigi icin eslesir.
        """
        policy = get_policy_for_event("payment.completed")
        assert policy.max_retries == 10  # payment_webhook (kategori esleme)

    def test_fallback_to_default(self):
        """
        Fallback: Hicbir policy ile eslesmeyen event tipi → "*" policy.
        """
        policy = get_policy_for_event("completely.unknown.event.type")
        assert policy == DEFAULT_POLICIES["*"]
        assert policy.max_retries == 5
        assert policy.base_delay_seconds == 10.0

    def test_default_policies_all_present(self):
        """DEFAULT_POLICIES'de beklenen tum key'ler mevcut olmali."""
        expected_keys = {"payment_webhook", "notification", "telegram_message", "*"}
        assert set(DEFAULT_POLICIES.keys()) == expected_keys

    def test_each_default_policy_is_retry_policy(self):
        """Tum DEFAULT_POLICIES degerleri RetryPolicy instance olmali."""
        for key, policy in DEFAULT_POLICIES.items():
            assert isinstance(policy, RetryPolicy), f"{key} RetryPolicy degil: {type(policy)}"
