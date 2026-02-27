"""
Emlak Teknoloji Platformu - Base Task

Tum Celery task'larinin turetilecegi temel sinif.

Ozellikler:
    - structlog entegrasyonu (task_id, task_name her log satirinda)
    - Otomatik retry: exponential backoff + jitter
    - on_failure / on_retry loglama
    - max_retries=3, retry_backoff_max=600s (10dk)
"""

from typing import Any

import structlog
from celery import Task

logger = structlog.get_logger("celery.task")


class BaseTask(Task):
    """
    Tum proje task'lari icin base class.

    Kullanim:
        @celery_app.task(bind=True, base=BaseTask, queue='default')
        def my_task(self, arg1, arg2):
            self.log.info("task_processing", arg1=arg1)
            ...

    Retry davranisi:
        - autoretry_for = (Exception,) → her exception'da retry
        - retry_backoff = True → exponential backoff (1s, 2s, 4s, ...)
        - retry_backoff_max = 600 → max 10 dakika bekleme
        - retry_jitter = True → thundering herd onleme
        - max_retries = 3 → en fazla 3 retry
    """

    # --- Retry Defaults ---
    autoretry_for = (Exception,)
    retry_backoff = True
    retry_backoff_max = 600  # max 10 dakika
    retry_jitter = True
    max_retries = 3

    @property
    def log(self) -> structlog.stdlib.BoundLogger:
        """
        Task-scoped structlog logger.

        Bind edilen alanlar:
            - task_id   → Celery task UUID
            - task_name → Task fonksiyon adi
            - request_id → HTTP request_id (varsa, signal handler bind eder)

        Not:
            request_id normalde task_prerun signal handler tarafindan
            structlog contextvars'a bind edilir ve otomatik eklenir.
            Buradaki explicit bind, signal handler calismadiginda
            (ornegin eager mode, test) fallback gorevi gorur.
        """
        bound = logger.bind(
            task_id=self.request.id,
            task_name=self.name,
        )

        # Signal handler context'e zaten bind etmis olabilir.
        # Ama eager mode veya testlerde signal atlanabilir — fallback:
        request_id = getattr(self.request, "request_id", None)
        if not request_id:
            headers = getattr(self.request, "headers", None)
            if isinstance(headers, dict):
                request_id = headers.get("request_id")

        if request_id:
            bound = bound.bind(request_id=request_id)

        return bound

    def on_failure(
        self,
        exc: BaseException,
        task_id: str,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        einfo: Any,
    ) -> None:
        """Task kalici olarak basarisiz olunca (tum retry'lar tukendi) logla."""
        logger.error(
            "task_failed",
            task_id=task_id,
            task_name=self.name,
            args=args,
            kwargs=kwargs,
            error=str(exc),
            error_type=type(exc).__name__,
            traceback=str(einfo),
        )
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_retry(
        self,
        exc: BaseException,
        task_id: str,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        einfo: Any,
    ) -> None:
        """Task retry edilirken logla."""
        logger.warning(
            "task_retry",
            task_id=task_id,
            task_name=self.name,
            retry_count=self.request.retries,
            max_retries=self.max_retries,
            args=args,
            kwargs=kwargs,
            error=str(exc),
            error_type=type(exc).__name__,
        )
        super().on_retry(exc, task_id, args, kwargs, einfo)

    def on_success(
        self,
        retval: Any,
        task_id: str,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> None:
        """Task basariyla tamamlaninca logla."""
        logger.info(
            "task_success",
            task_id=task_id,
            task_name=self.name,
        )
        super().on_success(retval, task_id, args, kwargs)
