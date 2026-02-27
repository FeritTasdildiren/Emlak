"""
Emlak Teknoloji Platformu - Celery Signal Handlers

HTTP request_id'yi Celery task zinciri boyunca tasir.
FastAPI → Celery publish → Celery worker akisinda request_id kaybolmaz.

Akis:
    1. FastAPI middleware structlog contextvars'a request_id bind eder
    2. before_task_publish: Publisher (FastAPI) tarafinda calisir,
       contextvars'dan request_id alir ve task message headers'a ekler
    3. task_prerun: Worker tarafinda calisir,
       headers'dan request_id alir ve structlog contextvars'a bind eder
    4. task_postrun: Worker tarafinda calisir,
       contextvars temizler (task izolasyonu, leak onleme)

Neden onemli:
    - Bir HTTP request birden fazla async task tetikleyebilir
    - request_id olmadan hangi task'in hangi request'ten geldigini bilemezsiniz
    - Distributed tracing'in temel tasiyicisi: log aggregation'da
      request_id ile filtreleyerek tum akisi gorebilirsiniz
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog
from celery.signals import before_task_publish, task_postrun, task_prerun

if TYPE_CHECKING:
    from celery import Task

logger = structlog.get_logger("celery.signals")

# ---------------------------------------------------------------------------
# 1) PUBLISHER SIDE — FastAPI process'inde calisir
# ---------------------------------------------------------------------------


@before_task_publish.connect
def propagate_request_id_to_headers(
    headers: dict[str, Any],
    **kwargs: Any,
) -> None:
    """
    Task publish edilmeden hemen once calisir (publisher/FastAPI tarafinda).

    structlog contextvars'dan request_id'yi okuyup AMQP message headers'a ekler.
    Bu sayede request_id network uzerinden worker'a ulasir.

    Not:
        headers dict'i Celery tarafindan referansla gonderilir,
        in-place mutation yeterlidir — yeni dict dondurmek gerekmez.
    """
    ctx = structlog.contextvars.get_contextvars()
    request_id = ctx.get("request_id")

    if request_id:
        headers["request_id"] = request_id


# ---------------------------------------------------------------------------
# 2) WORKER SIDE — Celery worker process'inde calisir
# ---------------------------------------------------------------------------


def _extract_request_id(task: Task) -> str | None:
    """
    Task request'inden request_id cikarir.

    Celery versiyonlari arasinda header erisim yontemi degisebilir.
    Bu fonksiyon iki yontemi de dener:
        1. task.request uzerinde dogrudan attribute (Celery 5+ custom headers merge)
        2. task.request.headers dict'inden okuma (fallback)

    Returns:
        request_id veya None (eger propagate edilmediyse, ornegin beat task'lari)
    """
    # Yontem 1: Celery 5+ custom header'lari request attribute olarak sunar
    request_id = getattr(task.request, "request_id", None)

    # Yontem 2: Fallback — headers dict'inden oku
    if not request_id:
        headers = getattr(task.request, "headers", None)
        if isinstance(headers, dict):
            request_id = headers.get("request_id")

    return request_id


@task_prerun.connect
def bind_request_context(
    task_id: str,
    task: Task,
    **kwargs: Any,
) -> None:
    """
    Task calistirilmadan hemen once calisir (worker tarafinda).

    1. Onceki task'tan kalan contextvars'i temizler (izolasyon)
    2. request_id varsa structlog contextvars'a bind eder
    3. task_id ve task_name'i de bind eder

    Bu sayede task icindeki TUM log satirlari otomatik olarak
    request_id, task_id, task_name icerir — ekstra bind gerekmez.
    """
    # Onceki task'in context'ini temizle (worker ayni process'te
    # birden fazla task calistirir — prefork pool'da bile)
    structlog.contextvars.clear_contextvars()

    request_id = _extract_request_id(task)

    bind_kwargs: dict[str, Any] = {
        "task_id": task_id,
        "task_name": task.name,
    }

    if request_id:
        bind_kwargs["request_id"] = request_id

    structlog.contextvars.bind_contextvars(**bind_kwargs)

    logger.debug(
        "task_context_bound",
        request_id=request_id,
        task_id=task_id,
        task_name=task.name,
    )


@task_postrun.connect
def clear_request_context(**kwargs: Any) -> None:
    """
    Task calistirildiktan sonra calisir (basari veya hata farketmez).

    contextvars'i temizler → sonraki task onceki task'in
    request_id'sini miras almaz.

    Not:
        task_prerun'da da clear yapiyoruz ama task_postrun'da da
        yapmak defensive programming — eger task_prerun atlanirsa
        (ornegin worker restart) bile context temiz kalir.
    """
    structlog.contextvars.clear_contextvars()
