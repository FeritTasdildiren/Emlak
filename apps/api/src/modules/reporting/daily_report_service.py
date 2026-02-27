"""
Emlak Teknoloji Platformu - Daily Report Service

Gunluk ofis raporu icin veri toplama servisi.
Celery beat task tarafindan 20:00 TST'de cagirilir.

Mimari:
    - Sync psycopg2 session (Celery worker — async KULLANILMAZ)
    - Her ofis icin bagimsiz rapor olusturur
    - Rapor donemi: bugun (UTC 00:00 — rapor ani)

Metrикler:
    - Portfolyo: toplam ilan, bugun eklenen
    - Musteriler: toplam, bugun eklenen, pipeline dagilimi
    - Degerleme: bugun yapilan, kota kullanimi
    - Eslesmeler: bugun bulunan, ortalama skor

Referans: TASK-136, drift_check.py (sync DB pattern)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import case, func, select

from src.models.customer import Customer
from src.models.match import PropertyCustomerMatch
from src.models.office import Office
from src.models.property import Property
from src.models.valuation import PropertyValuation
from src.modules.valuations.models.usage_quota import UsageQuota

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


# ================================================================
# Data Model
# ================================================================


@dataclass
class DailyReportData:
    """Tek ofis icin gunluk rapor verisi."""

    office_id: str  # UUID string (JSON serializable)
    office_name: str
    report_date: str  # ISO date string

    # Portfolyo
    total_properties: int
    new_properties_today: int

    # Musteriler
    total_customers: int
    new_customers_today: int
    pipeline_new: int  # cold + warm
    pipeline_contacted: int  # hot
    pipeline_closed: int  # converted + lost

    # Degerleme
    valuations_today: int
    valuation_quota_used: int
    valuation_quota_limit: int

    # Eslesmeler
    matches_today: int
    avg_match_score: float

    # Dinamik mesaj
    dynamic_message: str


# ================================================================
# Service
# ================================================================


class DailyReportService:
    """
    Gunluk ofis raporu veri toplama servisi.

    Kullanim (Celery task icinde):
        with get_sync_session() as session:
            service = DailyReportService(session)
            reports = service.generate_all_reports()
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    # ── Public API ──

    def generate_all_reports(self) -> list[DailyReportData]:
        """Tum aktif ofisler icin gunluk rapor olustur."""
        offices = self._get_active_offices()
        return [self.generate_daily_report(office) for office in offices]

    def generate_daily_report(self, office: Office) -> DailyReportData:
        """Tek ofis icin gunluk rapor olustur."""
        today_start = datetime.now(UTC).replace(
            hour=0, minute=0, second=0, microsecond=0,
        )
        office_id = office.id

        # Paralel sorgu yapmiyoruz — sync session, sequential daha guvenli
        portfolio = self._get_portfolio_metrics(office_id, today_start)
        customers = self._get_customer_metrics(office_id, today_start)
        valuations = self._get_valuation_metrics(office_id, today_start)
        matches = self._get_match_metrics(office_id, today_start)
        dynamic_msg = self._build_dynamic_message(
            valuations=valuations,
            portfolio=portfolio,
            customers=customers,
        )

        return DailyReportData(
            office_id=str(office_id),
            office_name=office.name,
            report_date=date.today().isoformat(),
            total_properties=portfolio["total"],
            new_properties_today=portfolio["today"],
            total_customers=customers["total"],
            new_customers_today=customers["today"],
            pipeline_new=customers["pipeline_new"],
            pipeline_contacted=customers["pipeline_contacted"],
            pipeline_closed=customers["pipeline_closed"],
            valuations_today=valuations["today"],
            valuation_quota_used=valuations["quota_used"],
            valuation_quota_limit=valuations["quota_limit"],
            matches_today=matches["today"],
            avg_match_score=matches["avg_score"],
            dynamic_message=dynamic_msg,
        )

    # ── Private: DB Queries ──

    def _get_active_offices(self) -> list[Office]:
        """Aktif ofisleri getir."""
        stmt = select(Office).where(Office.is_active.is_(True))
        result = self._session.execute(stmt)
        return list(result.scalars().all())

    def _get_portfolio_metrics(
        self,
        office_id: object,
        today_start: datetime,
    ) -> dict:
        """Portfolyo metrikleri: toplam ilan + bugun eklenen."""
        # Toplam aktif ilan
        stmt_total = (
            select(func.count())
            .select_from(Property)
            .where(
                Property.office_id == office_id,
                Property.status == "active",
            )
        )
        total = self._session.execute(stmt_total).scalar() or 0

        # Bugun eklenen
        stmt_today = (
            select(func.count())
            .select_from(Property)
            .where(
                Property.office_id == office_id,
                Property.created_at >= today_start,
            )
        )
        today = self._session.execute(stmt_today).scalar() or 0

        return {"total": total, "today": today}

    def _get_customer_metrics(
        self,
        office_id: object,
        today_start: datetime,
    ) -> dict:
        """Musteri metrikleri: toplam, bugun eklenen, pipeline dagilimi."""
        # Toplam musteri
        stmt_total = (
            select(func.count())
            .select_from(Customer)
            .where(Customer.office_id == office_id)
        )
        total = self._session.execute(stmt_total).scalar() or 0

        # Bugun eklenen
        stmt_today = (
            select(func.count())
            .select_from(Customer)
            .where(
                Customer.office_id == office_id,
                Customer.created_at >= today_start,
            )
        )
        today = self._session.execute(stmt_today).scalar() or 0

        # Pipeline dagilimi (tek sorguda)
        # cold + warm → yeni, hot → iletisimde, converted + lost → kapandi
        stmt_pipeline = (
            select(
                func.sum(
                    case(
                        (Customer.lead_status.in_(["cold", "warm"]), 1),
                        else_=0,
                    )
                ).label("pipeline_new"),
                func.sum(
                    case(
                        (Customer.lead_status == "hot", 1),
                        else_=0,
                    )
                ).label("pipeline_contacted"),
                func.sum(
                    case(
                        (Customer.lead_status.in_(["converted", "lost"]), 1),
                        else_=0,
                    )
                ).label("pipeline_closed"),
            )
            .select_from(Customer)
            .where(Customer.office_id == office_id)
        )
        row = self._session.execute(stmt_pipeline).one()

        return {
            "total": total,
            "today": today,
            "pipeline_new": row.pipeline_new or 0,
            "pipeline_contacted": row.pipeline_contacted or 0,
            "pipeline_closed": row.pipeline_closed or 0,
        }

    def _get_valuation_metrics(
        self,
        office_id: object,
        today_start: datetime,
    ) -> dict:
        """Degerleme metrikleri: bugun yapilan + kota kullanimi."""
        # Bugun yapilan degerleme
        stmt_today = (
            select(func.count())
            .select_from(PropertyValuation)
            .where(
                PropertyValuation.office_id == office_id,
                PropertyValuation.created_at >= today_start,
            )
        )
        today = self._session.execute(stmt_today).scalar() or 0

        # Kota: bu ayin usage_quota kaydini bul
        current_month_start = date.today().replace(day=1)
        stmt_quota = (
            select(UsageQuota)
            .where(
                UsageQuota.office_id == office_id,
                UsageQuota.period_start == current_month_start,
            )
        )
        quota = self._session.execute(stmt_quota).scalars().first()

        quota_used = quota.valuations_used if quota else 0
        quota_limit = quota.valuations_limit if quota else 0

        return {
            "today": today,
            "quota_used": quota_used,
            "quota_limit": quota_limit,
        }

    def _get_match_metrics(
        self,
        office_id: object,
        today_start: datetime,
    ) -> dict:
        """Eslestirme metrikleri: bugun bulunan + ortalama skor."""
        stmt = (
            select(
                func.count().label("match_count"),
                func.coalesce(func.avg(PropertyCustomerMatch.score), 0).label(
                    "avg_score",
                ),
            )
            .select_from(PropertyCustomerMatch)
            .where(
                PropertyCustomerMatch.office_id == office_id,
                PropertyCustomerMatch.created_at >= today_start,
            )
        )
        row = self._session.execute(stmt).one()

        return {
            "today": row.match_count or 0,
            "avg_score": round(float(row.avg_score), 1),
        }

    # ── Private: Dynamic Message ──

    @staticmethod
    def _build_dynamic_message(
        *,
        valuations: dict,
        portfolio: dict,
        customers: dict,
    ) -> str:
        """Kota durumuna ve performansa gore dinamik mesaj olustur."""
        quota_limit = valuations["quota_limit"]
        quota_used = valuations["quota_used"]

        # Kota uyarisi (oncelikli)
        if quota_limit > 0:
            usage_pct = (quota_used / quota_limit) * 100
            if usage_pct >= 90:
                return (
                    "Degerleme kotaniz %90'in uzerinde! "
                    "Planınızı yukseltmeyi dusunun."
                )
            if usage_pct >= 75:
                return (
                    "Degerleme kotanizin %75'ini kullandiniz. "
                    "Ay sonuna kadar dikkatli kullanin."
                )

        # Performans tebrik
        if portfolio["today"] >= 5:
            return "Harika bir gun! Bugun 5+ yeni ilan eklendi."
        if customers["today"] >= 3:
            return "Guzel is! Bugun 3+ yeni musteri kazandiniz."

        return "Iyi aksamlar! Gunluk ozet raporunuz hazir."


# ================================================================
# Telegram Mesaj Formatlayici
# ================================================================


def format_daily_report_telegram(report: DailyReportData) -> str:
    """
    DailyReportData'yi Telegram mesaj formatina donusturur.

    Telegram markdown kullanilmiyor — duz metin + emoji.
    Max 4096 karakter limiti icinde kalir.
    """
    # Kota yuzde hesabi
    if report.valuation_quota_limit > 0:
        quota_pct = round(
            (report.valuation_quota_used / report.valuation_quota_limit) * 100,
        )
    else:
        quota_pct = 0

    return (
        f"\U0001f4ca Gunluk Rapor — {report.office_name} — {report.report_date}\n"
        f"\n"
        f"\U0001f3e0 Portfolyo\n"
        f"\u2022 Toplam: {report.total_properties} ilan\n"
        f"\u2022 Bugun eklenen: {report.new_properties_today}\n"
        f"\n"
        f"\U0001f465 Musteriler\n"
        f"\u2022 Toplam: {report.total_customers} | Bugun: {report.new_customers_today}\n"
        f"\u2022 Pipeline: {report.pipeline_new} yeni, "
        f"{report.pipeline_contacted} iletisimde, "
        f"{report.pipeline_closed} kapandi\n"
        f"\n"
        f"\U0001f4c8 Degerleme\n"
        f"\u2022 Bugun: {report.valuations_today} degerleme\n"
        f"\u2022 Kota: {report.valuation_quota_used}/{report.valuation_quota_limit}"
        f" (%{quota_pct})\n"
        f"\n"
        f"\U0001f3af Eslesmeler\n"
        f"\u2022 Bugun: {report.matches_today} yeni eslestirme\n"
        f"\u2022 Ort. skor: %{report.avg_match_score}\n"
        f"\n"
        f"\u26a1 {report.dynamic_message}"
    )
