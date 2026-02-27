"""
Emlak Teknoloji Platformu - Data Pipeline Repositories

DB UPSERT islemleri. Sync SQLAlchemy session ile calisir (Celery uyumlu).
"""

from .area_repository import mark_area_failed, upsert_area_analysis
from .deprem_repository import mark_deprem_failed, upsert_deprem_risk
from .price_history_repository import batch_insert_price_history

__all__ = [
    "batch_insert_price_history",
    "mark_area_failed",
    "mark_deprem_failed",
    "upsert_area_analysis",
    "upsert_deprem_risk",
]
