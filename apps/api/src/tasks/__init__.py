"""
Emlak Teknoloji Platformu - Background Tasks

Celery task modulleri.

Kuyruklar:
    - default        → genel amacli task'lar
    - outbox         → transactional outbox polling
    - notifications  → bildirim task'lari (email, push, SMS)

Beat Schedule Task'lari:
    - area_refresh         → Haftalik bolge analiz guncelleme (Pazartesi 03:00)
    - deprem_risk_refresh  → Aylik deprem risk guncelleme (Ayin 1'i 04:00)
    - weekly_report        → Haftalik model performans raporu (Pazartesi 08:00)
    - daily_report         → Gunluk ofis raporu (Her gun 20:00 TST)

On-demand Task'lar:
    - trigger_matching_for_property  → Ilan icin eslestirme + bildirim
    - trigger_matching_for_customer  → Musteri icin eslestirme + bildirim

Tum task'lar BaseTask'tan turetilir:
    - structlog entegrasyonu
    - autoretry (exponential backoff + jitter)
    - on_failure / on_retry loglama
"""

from src.tasks.area_refresh import refresh_area_data
from src.tasks.base import BaseTask
from src.tasks.daily_report import send_daily_office_reports
from src.tasks.deprem_risk_refresh import refresh_deprem_risk
from src.tasks.weekly_report import generate_weekly_model_report

__all__ = [
    "BaseTask",
    "generate_weekly_model_report",
    "refresh_area_data",
    "refresh_deprem_risk",
    "send_daily_office_reports",
]
