"""
Emlak Teknoloji Platformu - Retry Policy

Konfigüre edilebilir retry politikasi: exponential backoff + jitter.
Event tipi bazinda farkli stratejiler tanimlanabilir.

Kullanim:
    policy = get_policy_for_event("payment.webhook")
    if policy.should_retry(retry_count=3, exception=exc):
        delay = policy.calculate_next_retry(retry_count=3)

Thundering Herd Korunmasi:
    Jitter ZORUNLU. Ayni anda retry eden event'lerin
    ayni saniyeye yigilmasini engeller.

Referans: TASK-041
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

# ---------- Error Classification ----------

# Gecici hatalar: retry yapilabilir
TRANSIENT_EXCEPTIONS: frozenset[str] = frozenset({
    "ConnectionError",
    "TimeoutError",
    "ConnectionRefusedError",
    "ConnectionResetError",
    "BrokenPipeError",
    "OSError",
    "IOError",
    # HTTP 5xx yanit hatalari
    "ServerError",
    "BadGatewayError",
    "ServiceUnavailableError",
    "GatewayTimeoutError",
    # Async / network
    "asyncio.TimeoutError",
    "aiohttp.ClientError",
    "httpx.TransportError",
    "httpx.TimeoutException",
    # Redis
    "redis.ConnectionError",
    "redis.TimeoutError",
})

# Kalici hatalar: retry YAPILMAZ, direkt DLQ
PERMANENT_EXCEPTIONS: frozenset[str] = frozenset({
    "ValidationError",
    "ValueError",
    "TypeError",
    "KeyError",
    "AttributeError",
    "AuthenticationError",
    "PermissionDenied",
    # HTTP 4xx yanit hatalari
    "ClientError",
    "NotFoundError",
    "UnprocessableEntityError",
    # JSON / Serialization
    "json.JSONDecodeError",
    "pydantic.ValidationError",
})


def classify_exception(exc: Exception) -> str:
    """
    Exception'i siniflandirir: 'transient', 'permanent' veya 'unknown'.

    Siniflandirma Stratejisi:
        1. Exception sinif adi PERMANENT listesinde → permanent (DLQ)
        2. Exception sinif adi TRANSIENT listesinde → transient (retry)
        3. Exception'in HTTP status code'u varsa:
           - 4xx → permanent
           - 5xx → transient
        4. Bilinmeyen → transient (guvenli taraf: retry dene)

    Returns:
        'transient' | 'permanent' | 'unknown'
    """
    exc_class_name = type(exc).__name__

    # Tam isim kontrolu (module.ClassName)
    exc_full_name = f"{type(exc).__module__}.{exc_class_name}"

    # Permanent kontrol
    if exc_class_name in PERMANENT_EXCEPTIONS or exc_full_name in PERMANENT_EXCEPTIONS:
        return "permanent"

    # Transient kontrol
    if exc_class_name in TRANSIENT_EXCEPTIONS or exc_full_name in TRANSIENT_EXCEPTIONS:
        return "transient"

    # HTTP status code tabanli kontrol (httpx, aiohttp vb.)
    status_code = getattr(exc, "status_code", None) or getattr(exc, "status", None)
    if status_code is not None:
        try:
            code = int(status_code)
            if 400 <= code < 500:
                return "permanent"
            if 500 <= code < 600:
                return "transient"
        except (ValueError, TypeError):
            pass

    # Bilinmeyen hata → guvenli taraf: transient (retry dene)
    return "unknown"


# ---------- RetryPolicy Dataclass ----------


@dataclass(frozen=True)
class RetryPolicy:
    """
    Tek bir event tipi icin retry politikasi.

    Attributes:
        max_retries: Maksimum tekrar deneme sayisi.
        base_delay_seconds: Ilk retry oncesi bekleme suresi (saniye).
        max_delay_seconds: Ust sinir bekleme suresi (sonsuz bekleme yok).
        backoff_multiplier: Her retry'da carpan (exponential backoff).
        jitter: True ise rastgele gecikme eklenir (thundering herd korunmasi).
        jitter_range: Jitter orani (0.0 - 1.0). Ornegin 0.25 = +/-%25 sapma.
    """

    max_retries: int = 5
    base_delay_seconds: float = 10.0
    max_delay_seconds: float = 3600.0  # 1 saat ust sinir
    backoff_multiplier: float = 2.0
    jitter: bool = True
    jitter_range: float = 0.25

    # Opsiyonel: Bu policy'ye ozel exception override'lar
    retryable_exceptions: frozenset[str] = field(default_factory=frozenset)
    permanent_exceptions: frozenset[str] = field(default_factory=frozenset)

    def calculate_next_retry(self, retry_count: int) -> float:
        """
        Sonraki retry icin bekleme suresini hesaplar (saniye).

        Formul:
            delay = base_delay * (multiplier ^ retry_count)
            delay = min(delay, max_delay)     # Ust sinir
            delay = delay * (1 + jitter)       # Jitter eklenir

        Args:
            retry_count: Simdiye kadar yapilmis deneme sayisi (0-based).

        Returns:
            Bekleme suresi (saniye, float).
        """
        # Exponential backoff
        delay = self.base_delay_seconds * (self.backoff_multiplier ** retry_count)

        # Ust sinir — sonsuz bekleme yok
        delay = min(delay, self.max_delay_seconds)

        # Jitter — thundering herd korunmasi (ZORUNLU)
        if self.jitter:
            jitter_delta = delay * self.jitter_range
            delay = delay + random.uniform(-jitter_delta, jitter_delta)

        # Negatif delay olamaz (jitter nedeniyle)
        return max(delay, 1.0)

    def should_retry(self, retry_count: int, exception: Exception | None = None) -> bool:
        """
        Bu event retry edilmeli mi?

        Kontroller:
            1. retry_count >= max_retries → False (limit asildi)
            2. Exception permanent ise → False (DLQ'ya gonder)
            3. Exception transient veya unknown ise → True (retry)

        Args:
            retry_count: Mevcut deneme sayisi.
            exception: Olusan hata (opsiyonel).

        Returns:
            True ise retry yapilmali, False ise DLQ'ya gonderilmeli.
        """
        # Max retry kontrolu
        if retry_count >= self.max_retries:
            return False

        # Exception yoksa (genel failure) → retry
        if exception is None:
            return True

        exc_class_name = type(exception).__name__

        # Policy-seviyesi permanent override
        if self.permanent_exceptions and exc_class_name in self.permanent_exceptions:
            return False

        # Policy-seviyesi retryable override
        if self.retryable_exceptions and exc_class_name in self.retryable_exceptions:
            return True

        # Genel siniflandirma
        classification = classify_exception(exception)
        return classification != "permanent"


# ---------- Default Policies ----------

DEFAULT_POLICIES: dict[str, RetryPolicy] = {
    # Odeme webhook'lari: Kritik — cok retry, uzun bekleme
    # Odeme gateway'leri gecici hata verebilir (5xx, timeout)
    "payment_webhook": RetryPolicy(
        max_retries=10,
        base_delay_seconds=30.0,
        max_delay_seconds=7200.0,   # 2 saat ust sinir
        backoff_multiplier=2.0,
        jitter=True,
        jitter_range=0.25,
    ),

    # Bildirimler: Dusuk oncelik — az retry, kisa bekleme
    # Kullaniciya bildirim gitmezse kritik degil
    "notification": RetryPolicy(
        max_retries=3,
        base_delay_seconds=5.0,
        max_delay_seconds=300.0,    # 5 dakika ust sinir
        backoff_multiplier=2.0,
        jitter=True,
        jitter_range=0.3,
    ),

    # Telegram mesajlari: Orta oncelik
    # Telegram API rate limit veya gecici hata verebilir
    "telegram_message": RetryPolicy(
        max_retries=5,
        base_delay_seconds=15.0,
        max_delay_seconds=1800.0,   # 30 dakika ust sinir
        backoff_multiplier=2.0,
        jitter=True,
        jitter_range=0.2,
    ),

    # Fallback: Bilinmeyen event tipleri icin varsayilan politika
    "*": RetryPolicy(
        max_retries=5,
        base_delay_seconds=10.0,
        max_delay_seconds=3600.0,   # 1 saat ust sinir
        backoff_multiplier=2.0,
        jitter=True,
        jitter_range=0.25,
    ),
}


def get_policy_for_event(event_type: str) -> RetryPolicy:
    """
    Event tipine gore uygun retry politikasini dondurur.

    Eslestirme Stratejisi:
        1. Tam esleme: "payment.webhook" → DEFAULT_POLICIES["payment.webhook"]
        2. Prefix esleme: "payment.webhook.iyzico" → "payment_webhook" (. → _)
        3. Kategori esleme: "payment.*" → "payment_webhook" (ilk segment)
        4. Fallback: "*" → Varsayilan politika

    Args:
        event_type: Event tipi (ör: "payment.completed", "notification.send").

    Returns:
        Eslesen RetryPolicy instance.
    """
    # 1. Tam esleme (nokta → alt cizgi donusumu ile)
    normalized = event_type.replace(".", "_")

    if normalized in DEFAULT_POLICIES:
        return DEFAULT_POLICIES[normalized]

    # 2. Prefix esleme — en uzun eslesen policy key'i bul
    # Ornegin "payment_webhook_iyzico" → "payment_webhook" eslesmeli
    best_match: str | None = None
    best_len = 0

    for key in DEFAULT_POLICIES:
        if key == "*":
            continue
        if normalized.startswith(key) and len(key) > best_len:
            best_match = key
            best_len = len(key)

    if best_match is not None:
        return DEFAULT_POLICIES[best_match]

    # 3. Kategori esleme — ilk segment
    # Ornegin "payment.completed" → "payment" prefix'i ile eslesen var mi?
    first_segment = normalized.split("_")[0]
    for key in DEFAULT_POLICIES:
        if key == "*":
            continue
        if key.startswith(first_segment):
            return DEFAULT_POLICIES[key]

    # 4. Fallback
    return DEFAULT_POLICIES["*"]
