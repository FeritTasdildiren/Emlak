"""
Emlak Teknoloji Platformu - Weekly Model Performance Report

Haftalik model performans metriklerini toplayip yapilandirilmis rapor olusturur.

Metrikler:
    - PredictionLog tablosundan son 7 gunun tahminleri
    - Toplam tahmin, ortalama latency, confidence, fiyat dagilimi
    - Ilce bazli istatistikler, confidence trendi, latency percentile'lari
    - Uyari mekanizmasi (dusuk confidence, yuksek latency, vb.)

Kullanim:
    from src.core.sync_database import get_sync_session
    from src.ml.weekly_report import WeeklyReportService

    with get_sync_session() as session:
        service = WeeklyReportService(session)
        report = service.generate_weekly_report()
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


class WeeklyReportService:
    """Haftalik model performans raporu olusturur."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def generate_weekly_report(self) -> dict[str, Any]:
        """
        Son 7 gunun tahmin metriklerini topla.

        PredictionLog tablosundan veri cekilir. Veri yoksa
        bos/sifir degerlerle graceful rapor doner.

        Returns:
            Yapilandirilmis rapor dict'i (summary, price_distribution,
            top_districts, confidence_trend, latency_percentiles, alerts).
        """
        today = date.today()
        period_start = today - timedelta(days=7)

        # ── Aktif model versiyonunu bul ──
        model_version = self._get_active_model_version()

        # ── Summary metrikleri ──
        summary = self._get_summary(period_start, today)

        # ── Fiyat dagilimi ──
        price_distribution = self._get_price_distribution(period_start, today)

        # ── Ilce bazli istatistikler ──
        top_districts = self._get_top_districts(period_start, today)

        # ── Confidence trendi ──
        confidence_trend = self._get_confidence_trend(period_start, today)

        # ── Latency percentile'lari ──
        latency_percentiles = self._get_latency_percentiles(period_start, today)

        # ── Alert'ler ──
        alerts = self._generate_alerts(summary, confidence_trend)

        return {
            "report_date": str(today),
            "period": {
                "start": str(period_start),
                "end": str(today),
            },
            "model_version": model_version,
            "summary": summary,
            "price_distribution": price_distribution,
            "top_districts": top_districts,
            "confidence_trend": confidence_trend,
            "latency_percentiles": latency_percentiles,
            "alerts": alerts,
        }

    def _get_active_model_version(self) -> str:
        """ModelRegistry'den aktif model versiyonunu getir."""
        row = self.session.execute(
            text(
                "SELECT version FROM model_registry "
                "WHERE status = 'active' "
                "ORDER BY created_at DESC LIMIT 1"
            )
        ).fetchone()

        if row:
            return row[0]
        return "v0"

    def _get_summary(self, period_start: date, period_end: date) -> dict[str, Any]:
        """Toplam tahmin, ortalama latency/confidence/fiyat, benzersiz kullanici/ilce."""
        row = self.session.execute(
            text(
                "SELECT "
                "  COUNT(*) AS total_predictions, "
                "  COALESCE(AVG(latency_ms), 0) AS avg_latency_ms, "
                "  COALESCE(AVG(confidence), 0) AS avg_confidence, "
                "  COALESCE(AVG((output_data->>'estimated_price')::numeric), 0) AS avg_estimated_price, "
                "  COUNT(DISTINCT office_id) AS unique_users, "
                "  COUNT(DISTINCT input_data->>'district') AS unique_districts "
                "FROM prediction_logs "
                "WHERE created_at >= :start AND created_at < :end + interval '1 day'"
            ),
            {"start": str(period_start), "end": str(period_end)},
        ).fetchone()

        if not row or row[0] == 0:
            return {
                "total_predictions": 0,
                "avg_latency_ms": 0,
                "avg_confidence": 0,
                "avg_estimated_price": 0,
                "unique_users": 0,
                "unique_districts": 0,
            }

        return {
            "total_predictions": row[0],
            "avg_latency_ms": round(float(row[1]), 1),
            "avg_confidence": round(float(row[2]), 2),
            "avg_estimated_price": int(row[3]),
            "unique_users": row[4],
            "unique_districts": row[5],
        }

    def _get_price_distribution(
        self, period_start: date, period_end: date
    ) -> dict[str, dict[str, Any]]:
        """Fiyat aralik dagilimi: 0-1M, 1-3M, 3-5M, 5M+."""
        rows = self.session.execute(
            text(
                "SELECT "
                "  CASE "
                "    WHEN (output_data->>'estimated_price')::numeric < 1000000 THEN '0_1M' "
                "    WHEN (output_data->>'estimated_price')::numeric < 3000000 THEN '1_3M' "
                "    WHEN (output_data->>'estimated_price')::numeric < 5000000 THEN '3_5M' "
                "    ELSE '5M_plus' "
                "  END AS price_bucket, "
                "  COUNT(*) AS cnt "
                "FROM prediction_logs "
                "WHERE created_at >= :start AND created_at < :end + interval '1 day' "
                "GROUP BY price_bucket "
                "ORDER BY price_bucket"
            ),
            {"start": str(period_start), "end": str(period_end)},
        ).fetchall()

        # Tum bucket'lari sifirla
        distribution: dict[str, dict[str, Any]] = {
            "0_1M": {"count": 0, "pct": 0.0},
            "1_3M": {"count": 0, "pct": 0.0},
            "3_5M": {"count": 0, "pct": 0.0},
            "5M_plus": {"count": 0, "pct": 0.0},
        }

        total = sum(r[1] for r in rows)
        if total == 0:
            return distribution

        for row in rows:
            bucket = row[0]
            count = row[1]
            if bucket in distribution:
                distribution[bucket] = {
                    "count": count,
                    "pct": round(count / total * 100, 1),
                }

        return distribution

    def _get_top_districts(
        self, period_start: date, period_end: date
    ) -> list[dict[str, Any]]:
        """Ilce bazli tahmin sayisi ve ortalama fiyat (azalan sirada, en fazla 10)."""
        rows = self.session.execute(
            text(
                "SELECT "
                "  input_data->>'district' AS district, "
                "  COUNT(*) AS cnt, "
                "  AVG((output_data->>'estimated_price')::numeric) AS avg_price "
                "FROM prediction_logs "
                "WHERE created_at >= :start AND created_at < :end + interval '1 day' "
                "  AND input_data->>'district' IS NOT NULL "
                "GROUP BY district "
                "ORDER BY cnt DESC "
                "LIMIT 10"
            ),
            {"start": str(period_start), "end": str(period_end)},
        ).fetchall()

        return [
            {
                "district": row[0],
                "count": row[1],
                "avg_price": int(row[2]),
            }
            for row in rows
        ]

    def _get_confidence_trend(
        self, period_start: date, period_end: date
    ) -> dict[str, Any]:
        """Gunluk confidence ortalamasi ve trend hesapla."""
        rows = self.session.execute(
            text(
                "SELECT "
                "  created_at::date AS day, "
                "  AVG(confidence) AS avg_conf, "
                "  COUNT(*) AS cnt "
                "FROM prediction_logs "
                "WHERE created_at >= :start AND created_at < :end + interval '1 day' "
                "GROUP BY day "
                "ORDER BY day"
            ),
            {"start": str(period_start), "end": str(period_end)},
        ).fetchall()

        daily = [
            {
                "date": str(row[0]),
                "avg": round(float(row[1]), 2),
                "count": row[2],
            }
            for row in rows
        ]

        daily_avgs = [d["avg"] for d in daily]
        week_avg = round(sum(daily_avgs) / len(daily_avgs), 2) if daily_avgs else 0
        trend = self._calculate_trend(daily_avgs)

        return {
            "daily": daily,
            "week_avg": week_avg,
            "trend": trend,
        }

    def _get_latency_percentiles(
        self, period_start: date, period_end: date
    ) -> dict[str, int]:
        """Latency percentile'lari: p50, p90, p95, p99 (PostgreSQL percentile_cont)."""
        row = self.session.execute(
            text(
                "SELECT "
                "  COALESCE(percentile_cont(0.50) WITHIN GROUP (ORDER BY latency_ms), 0), "
                "  COALESCE(percentile_cont(0.90) WITHIN GROUP (ORDER BY latency_ms), 0), "
                "  COALESCE(percentile_cont(0.95) WITHIN GROUP (ORDER BY latency_ms), 0), "
                "  COALESCE(percentile_cont(0.99) WITHIN GROUP (ORDER BY latency_ms), 0) "
                "FROM prediction_logs "
                "WHERE created_at >= :start AND created_at < :end + interval '1 day' "
                "  AND latency_ms IS NOT NULL"
            ),
            {"start": str(period_start), "end": str(period_end)},
        ).fetchone()

        if not row:
            return {"p50": 0, "p90": 0, "p95": 0, "p99": 0}

        return {
            "p50": int(row[0]),
            "p90": int(row[1]),
            "p95": int(row[2]),
            "p99": int(row[3]),
        }

    def _calculate_trend(self, daily_values: list[float]) -> str:
        """
        Trend hesapla: Son 3 gun ortalamasi vs onceki 4 gun ortalamasi.

        - Fark > +0.05: IMPROVING
        - Fark < -0.05: DECLINING
        - Digerleri: STABLE
        """
        if len(daily_values) < 4:
            return "STABLE"

        recent = daily_values[-3:]
        previous = daily_values[:-3]

        recent_avg = sum(recent) / len(recent)
        previous_avg = sum(previous) / len(previous)
        diff = recent_avg - previous_avg

        if diff > 0.05:
            return "IMPROVING"
        if diff < -0.05:
            return "DECLINING"
        return "STABLE"

    def _generate_alerts(
        self,
        summary: dict[str, Any],
        confidence_trend: dict[str, Any],
    ) -> list[dict[str, str]]:
        """
        Alert kurallari:
        - total_predictions == 0 → "Hic tahmin yapilmadi" (WARNING)
        - avg_confidence < 0.7 → "Dusuk confidence" (WARNING)
        - avg_latency_ms > 200 → "Yuksek latency" (WARNING)
        - confidence trend DECLINING → "Confidence trend dusuyor" (INFO)
        """
        alerts: list[dict[str, str]] = []

        if summary["total_predictions"] == 0:
            alerts.append({
                "severity": "WARNING",
                "message": "Son 7 gunde hic tahmin yapilmadi",
            })
            return alerts

        if summary["avg_confidence"] < 0.7:
            alerts.append({
                "severity": "WARNING",
                "message": (
                    f"Dusuk confidence: {summary['avg_confidence']:.2f} "
                    f"(esik: 0.70)"
                ),
            })

        if summary["avg_latency_ms"] > 200:
            alerts.append({
                "severity": "WARNING",
                "message": (
                    f"Yuksek latency: {summary['avg_latency_ms']:.1f}ms "
                    f"(esik: 200ms)"
                ),
            })

        if confidence_trend.get("trend") == "DECLINING":
            alerts.append({
                "severity": "INFO",
                "message": "Confidence trend dusuyor",
            })

        return alerts
