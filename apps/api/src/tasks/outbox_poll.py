"""
Emlak Teknoloji Platformu - Outbox Polling Task

Transactional Outbox Pattern implementasyonu.

Celery Beat tarafindan 5 saniyede bir tetiklenir.
outbox tablosundaki islenmemis event'leri okur,
ilgili handler'lara dispatch eder ve
basarili olanlari "processed" olarak isaretler.

Bu pattern sayesinde:
    - DB transaction + event publish atomik olur
    - Event kaybi olmaz (at-least-once delivery)
    - Distributed transaction'a gerek kalmaz
"""

from src.celery_app import celery_app
from src.tasks.base import BaseTask


@celery_app.task(bind=True, base=BaseTask, queue="outbox", name="src.tasks.outbox_poll.poll_outbox")
def poll_outbox(self) -> dict:
    """
    Outbox tablosundan islenmemis event'leri oku ve dispatch et.

    Celery Beat tarafindan 5 saniyede bir cagirilir.
    Senkron task — Celery worker'da calisir (async degil).

    Returns:
        dict: Islenen event sayisi ve detaylari.

    TODO: Outbox modeli ve dispatch mekanizmasi TASK-029'da implement edilecek.
          Asagidaki placeholder, Celery altyapisinin dogru calistigini dogrular.
    """
    self.log.debug("outbox_poll_started")

    # TODO: Asagidaki kisim outbox modeli hazir olunca implement edilecek:
    #
    # 1. Outbox tablosundan status='pending' kayitlari oku (SELECT ... FOR UPDATE SKIP LOCKED)
    # 2. Her event icin ilgili handler'i cagir
    # 3. Basarili olanlari status='processed' olarak guncelle
    # 4. Basarisiz olanlari retry_count++ ile birak
    #
    # Ornek:
    #   from src.database import sync_session_factory
    #   with sync_session_factory() as session:
    #       events = session.execute(
    #           select(OutboxEvent)
    #           .where(OutboxEvent.status == "pending")
    #           .with_for_update(skip_locked=True)
    #           .limit(100)
    #       ).scalars().all()
    #       ...

    processed_count = 0

    self.log.debug(
        "outbox_poll_completed",
        processed_count=processed_count,
    )

    return {"processed_count": processed_count}
