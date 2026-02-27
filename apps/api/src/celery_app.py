"""
Emlak Teknoloji Platformu - Celery Application

Celery worker ve beat konfigurasyonu.

Mimari:
    Redis DB 0 → Cache (FastAPI uygulama cache)
    Redis DB 1 → Celery Broker (task kuyrugu)
    Redis DB 2 → Celery Result Backend (task sonuclari)

Guvenlik:
    - JSON serializer zorunlu (pickle YASAK — arbitrary code execution riski)
    - task_acks_late = True (worker crash'te task kaybolmaz, broker'da kalir)
    - worker_prefetch_multiplier = 1 (adil dagitim, uzun task'lar kuyrugu bloklamaz)

Kuyruklar:
    - default   → genel amacli task'lar
    - outbox    → transactional outbox polling (5s periyot)
    - notifications → bildirim task'lari (email, push, SMS)
"""

from celery import Celery
from celery.schedules import crontab
from kombu import Exchange, Queue

from src.config import settings

celery_app = Celery("emlak")

# ---------- Broker & Backend ----------
celery_app.conf.broker_url = settings.CELERY_BROKER_URL
celery_app.conf.result_backend = settings.CELERY_RESULT_BACKEND

# ---------- Serialization (pickle YASAK) ----------
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]
celery_app.conf.event_serializer = "json"

# ---------- Timezone ----------
celery_app.conf.timezone = "Europe/Istanbul"
celery_app.conf.enable_utc = True

# ---------- Task Execution ----------
celery_app.conf.task_track_started = True
celery_app.conf.task_acks_late = True
celery_app.conf.worker_prefetch_multiplier = 1

# ---------- Result Backend ----------
celery_app.conf.result_expires = 3600  # Sonuclar 1 saat sonra temizlenir
celery_app.conf.result_extended = True  # Task args/kwargs result'ta gorunur (debug icin)

# ---------- Worker ----------
celery_app.conf.worker_send_task_events = True  # Flower monitoring icin
celery_app.conf.task_send_sent_event = True

# ---------- Queues ----------
default_exchange = Exchange("default", type="direct")
outbox_exchange = Exchange("outbox", type="direct")
notifications_exchange = Exchange("notifications", type="direct")

celery_app.conf.task_queues = (
    Queue("default", default_exchange, routing_key="default"),
    Queue("outbox", outbox_exchange, routing_key="outbox"),
    Queue("notifications", notifications_exchange, routing_key="notifications"),
)
celery_app.conf.task_default_queue = "default"
celery_app.conf.task_default_exchange = "default"
celery_app.conf.task_default_routing_key = "default"

# ---------- Beat Schedule ----------
celery_app.conf.beat_schedule = {
    "poll-outbox-every-5s": {
        "task": "src.tasks.outbox_poll.poll_outbox",
        "schedule": 5.0,  # 5 saniye
        "options": {"queue": "outbox"},
    },
    "monitor-outbox-every-60s": {
        "task": "src.tasks.outbox_monitor_task.monitor_outbox_health",
        "schedule": 60.0,  # 60 saniye
        "options": {"queue": "default"},
    },
    # ── Data Pipeline: Area Analysis Refresh (Haftalik) ──
    "refresh-area-data-weekly": {
        "task": "src.tasks.area_refresh.refresh_area_data",
        "schedule": crontab(
            hour=3,
            minute=0,
            day_of_week="monday",  # Her Pazartesi 03:00
        ),
        "options": {"queue": "default"},
    },
    # ── Data Pipeline: Deprem Risk Refresh (Aylik) ──
    "refresh-deprem-risk-monthly": {
        "task": "src.tasks.deprem_risk_refresh.refresh_deprem_risk",
        "schedule": crontab(
            hour=4,
            minute=0,
            day_of_month="1",  # Her ayin 1'i 04:00
        ),
        "options": {"queue": "default"},
    },
    # ── Refresh Status Monitor (30 dakikada bir) ──
    "check-refresh-status-30min": {
        "task": "src.tasks.refresh_monitor.check_refresh_status",
        "schedule": 1800,  # 30 dakika
        "options": {"queue": "default"},
    },
    # ── ML: Weekly Model Performance Report (Haftalik) ──
    "weekly-model-report": {
        "task": "src.tasks.weekly_report.generate_weekly_model_report",
        "schedule": crontab(
            hour=8,
            minute=0,
            day_of_week="monday",  # Her Pazartesi 08:00
        ),
        "options": {"queue": "default"},
    },
    # ── ML: Drift Check (Gunluk 06:00) ──
    "check-drift-daily": {
        "task": "src.tasks.drift_check.check_drift",
        "schedule": crontab(
            hour=6,
            minute=0,
        ),
        "options": {"queue": "default"},
    },
    # ── Reporting: Daily Office Report (Gunluk 20:00 TST = 17:00 UTC) ──
    "send-daily-reports-20": {
        "task": "src.tasks.daily_report.send_daily_office_reports",
        "schedule": crontab(hour=17, minute=0),
        "options": {"queue": "notifications"},
    },
}

# ---------- Auto-discover Tasks ----------
celery_app.autodiscover_tasks(["src.tasks", "src.modules.matches"])

# ---------- Signal Handlers ----------
# Import etmek yeterli: @before_task_publish.connect gibi dekoratorler
# modul yuklenince otomatik register olur. Explicit kullanim yok.
import src.tasks.signals  # noqa: F401
