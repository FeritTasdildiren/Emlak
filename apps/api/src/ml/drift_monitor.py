"""
Emlak Teknoloji Platformu - Drift Monitor

Basit drift tespiti ve confidence trend izleme.
PredictionLog verilerini kullanarak giris dagilimi degisimlerini
ve model confidence trendini izler.

PSI (Population Stability Index):
    PSI < 0.1  : Stabil — dagilim degismemis
    0.1 - 0.25 : Orta drift — izleme gerekli
    > 0.25     : Ciddi drift — model yeniden egitimi gerekebilir

Referans: TASK-067
"""

from __future__ import annotations

import math
from collections import Counter
from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.prediction_log import PredictionLog

logger = structlog.get_logger()

# ---------- Egitim Verisinden Hesaplanan Referans Dagilimlar ----------
# Kaynak: istanbul_training_data.csv (3749 kayit)
REFERENCE_STATS = {
    "net_sqm": {"mean": 103.91, "std": 52.05, "min": 25.0, "max": 418.0},
    "building_age": {"mean": 21.84, "std": 11.06},
    "room_distribution": {
        "1+0": 0.045,
        "1+1": 0.094,
        "2+1": 0.209,
        "3+1": 0.371,
        "4+1": 0.162,
        "5+": 0.118,
    },
}


class DriftMonitor:
    """Basit drift tespiti ve confidence trend izleme."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # Giris Dagilimi Kontrolu
    # ------------------------------------------------------------------

    async def check_input_distribution(self, days: int = 7) -> dict:
        """
        Son X gundeki tahminlerin giris dagilimini kontrol et.

        Olculer:
            - net_sqm: ortalama, std, min, max
            - building_age: ortalama, std
            - room_count: dagilim (1+0, 1+1, 2+1, 3+1, 4+1, 5+)
            - district: en sik 5 ilce ve yuzdeleri
            - PSI: room distribution uzerinden referans dagilimla karsilastirma
        """
        cutoff = datetime.now(UTC) - timedelta(days=days)

        stmt = select(PredictionLog).where(PredictionLog.created_at >= cutoff)
        result = await self.session.execute(stmt)
        logs = result.scalars().all()

        if not logs:
            return {
                "status": "no_data",
                "days": days,
                "sample_count": 0,
                "net_sqm": {},
                "building_age": {},
                "room_distribution": {},
                "district_distribution": {},
                "psi": {"total_psi": 0, "status": "no_data", "details": {}},
            }

        net_sqms: list[float] = []
        building_ages: list[int] = []
        room_types: list[str] = []
        districts: list[str] = []

        for log in logs:
            inp = log.input_data or {}

            if "net_sqm" in inp:
                net_sqms.append(float(inp["net_sqm"]))
            if "building_age" in inp:
                building_ages.append(int(inp["building_age"]))

            rc = inp.get("room_count", 0)
            lc = inp.get("living_room_count", 0)
            if rc >= 5:
                room_types.append("5+")
            else:
                room_types.append(f"{rc}+{lc}")

            if "district" in inp:
                districts.append(inp["district"])

        # net_sqm istatistikleri
        net_sqm_stats = _compute_stats(net_sqms) if net_sqms else {}

        # building_age istatistikleri
        building_age_stats = {}
        if building_ages:
            ages_f = [float(a) for a in building_ages]
            building_age_stats = _compute_stats(ages_f, include_minmax=False)

        # room distribution
        room_dist = _distribution(room_types)

        # district distribution (top 5)
        district_dist = {}
        if districts:
            counter = Counter(districts)
            total = len(districts)
            district_dist = {d: round(c / total, 4) for d, c in counter.most_common(5)}

        # PSI
        psi_result = calculate_psi(room_dist)

        return {
            "status": "ok",
            "days": days,
            "sample_count": len(logs),
            "net_sqm": net_sqm_stats,
            "building_age": building_age_stats,
            "room_distribution": room_dist,
            "district_distribution": district_dist,
            "psi": psi_result,
            "reference": REFERENCE_STATS,
        }

    # ------------------------------------------------------------------
    # Confidence Trend
    # ------------------------------------------------------------------

    async def check_confidence_trend(self, days: int = 30) -> dict:
        """
        Confidence skorunun zaman icindeki trendini izle.

        - Gunluk ortalama confidence
        - 7 gunluk hareketli ortalama
        - Son 7 gun ort < 0.7 → WARNING, < 0.5 → ALARM
        """
        cutoff = datetime.now(UTC) - timedelta(days=days)

        stmt = (
            select(
                func.date(PredictionLog.created_at).label("day"),
                func.avg(PredictionLog.confidence).label("avg_confidence"),
                func.count().label("count"),
            )
            .where(
                PredictionLog.created_at >= cutoff,
                PredictionLog.confidence.isnot(None),
            )
            .group_by(func.date(PredictionLog.created_at))
            .order_by(func.date(PredictionLog.created_at))
        )

        result = await self.session.execute(stmt)
        rows = result.all()

        if not rows:
            return {
                "status": "no_data",
                "days": days,
                "daily": [],
                "moving_avg_7d": None,
                "alert_level": None,
            }

        daily = [
            {
                "date": str(row.day),
                "avg_confidence": round(float(row.avg_confidence), 4),
                "count": row.count,
            }
            for row in rows
        ]

        # 7 gunluk hareketli ortalama
        confidences = [d["avg_confidence"] for d in daily]
        last_7 = confidences[-7:] if len(confidences) >= 7 else confidences
        moving_avg_7d = round(sum(last_7) / len(last_7), 4)

        alert_level = None
        if moving_avg_7d < 0.5:
            alert_level = "ALARM"
        elif moving_avg_7d < 0.7:
            alert_level = "WARNING"

        return {
            "status": "ok",
            "days": days,
            "daily": daily,
            "moving_avg_7d": moving_avg_7d,
            "alert_level": alert_level,
        }

    # ------------------------------------------------------------------
    # Genel Tahmin Istatistikleri
    # ------------------------------------------------------------------

    async def get_prediction_stats(self, days: int = 7) -> dict:
        """
        Genel tahmin istatistikleri.

        - Toplam tahmin sayisi, ortalama latency, ortalama confidence
        - Min/max/ortalama tahmin fiyati
        - En cok talep edilen ilceler (top 5)
        """
        cutoff = datetime.now(UTC) - timedelta(days=days)

        # Aggregate metrikler
        agg_stmt = select(
            func.count().label("total"),
            func.avg(PredictionLog.latency_ms).label("avg_latency_ms"),
            func.avg(PredictionLog.confidence).label("avg_confidence"),
        ).where(PredictionLog.created_at >= cutoff)

        agg_result = await self.session.execute(agg_stmt)
        agg = agg_result.one()

        total = agg.total or 0
        if total == 0:
            return {"status": "no_data", "days": days, "total_predictions": 0}

        # JSON field'lardan fiyat ve ilce bilgisi
        json_stmt = select(
            PredictionLog.input_data,
            PredictionLog.output_data,
        ).where(PredictionLog.created_at >= cutoff)

        json_result = await self.session.execute(json_stmt)
        json_rows = json_result.all()

        prices: list[int] = []
        district_counter: Counter[str] = Counter()

        for inp, out in json_rows:
            if out and "estimated_price" in out:
                prices.append(int(out["estimated_price"]))
            if inp and "district" in inp:
                district_counter[inp["district"]] += 1

        price_stats: dict = {}
        if prices:
            price_stats = {
                "avg_price": round(sum(prices) / len(prices)),
                "min_price": min(prices),
                "max_price": max(prices),
            }

        top_districts = [
            {"district": d, "count": c} for d, c in district_counter.most_common(5)
        ]

        return {
            "status": "ok",
            "days": days,
            "total_predictions": total,
            "avg_latency_ms": (
                round(float(agg.avg_latency_ms)) if agg.avg_latency_ms else None
            ),
            "avg_confidence": (
                round(float(agg.avg_confidence), 4) if agg.avg_confidence else None
            ),
            **price_stats,
            "top_districts": top_districts,
        }

    # ------------------------------------------------------------------
    # Birlesik Drift Raporu
    # ------------------------------------------------------------------

    async def generate_drift_report(self) -> dict:
        """
        Tum drift metriklerini birlestiren rapor.

        Returns:
            - input_distribution: check_input_distribution() sonucu
            - confidence_trend: check_confidence_trend() sonucu
            - prediction_stats: get_prediction_stats() sonucu
            - overall_status: GREEN | YELLOW | RED
            - alerts: [{level, message, metric, value}]
        """
        input_dist = await self.check_input_distribution()
        confidence = await self.check_confidence_trend()
        stats = await self.get_prediction_stats()

        alerts: list[dict] = []
        overall_status = "GREEN"

        # --- PSI kontrol ---
        psi = input_dist.get("psi", {})
        psi_value = psi.get("total_psi", 0)
        if psi_value > 0.25:
            alerts.append(
                {
                    "level": "CRITICAL",
                    "message": "Ciddi giris dagilimi kaymasi tespit edildi",
                    "metric": "psi",
                    "value": psi_value,
                }
            )
            overall_status = "RED"
        elif psi_value > 0.1:
            alerts.append(
                {
                    "level": "WARNING",
                    "message": "Orta seviye giris dagilimi kaymasi",
                    "metric": "psi",
                    "value": psi_value,
                }
            )
            if overall_status != "RED":
                overall_status = "YELLOW"

        # --- Confidence kontrol ---
        confidence_alert = confidence.get("alert_level")
        if confidence_alert == "ALARM":
            alerts.append(
                {
                    "level": "CRITICAL",
                    "message": "Confidence skoru kritik seviyede dusuk (< 0.5)",
                    "metric": "confidence_7d_avg",
                    "value": confidence.get("moving_avg_7d"),
                }
            )
            overall_status = "RED"
        elif confidence_alert == "WARNING":
            alerts.append(
                {
                    "level": "WARNING",
                    "message": "Confidence skoru dusuk (< 0.7)",
                    "metric": "confidence_7d_avg",
                    "value": confidence.get("moving_avg_7d"),
                }
            )
            if overall_status != "RED":
                overall_status = "YELLOW"

        # --- Tahmin sayisi kontrol ---
        total = stats.get("total_predictions", 0)
        if total == 0:
            alerts.append(
                {
                    "level": "WARNING",
                    "message": "Son 7 gunde hic tahmin yapilmamis",
                    "metric": "total_predictions",
                    "value": 0,
                }
            )
            if overall_status != "RED":
                overall_status = "YELLOW"

        return {
            "input_distribution": input_dist,
            "confidence_trend": confidence,
            "prediction_stats": stats,
            "overall_status": overall_status,
            "alerts": alerts,
            "generated_at": datetime.now(UTC).isoformat(),
        }


# ======================================================================
# Yardimci Fonksiyonlar
# ======================================================================


def calculate_psi(actual_dist: dict[str, float]) -> dict:
    """
    PSI (Population Stability Index) hesapla.

    Room distribution uzerinden referans dagilimla karsilastirir.

    PSI = SUM((actual_pct - expected_pct) * ln(actual_pct / expected_pct))
    """
    ref = REFERENCE_STATS["room_distribution"]

    if not actual_dist:
        return {"total_psi": 0, "status": "no_data", "details": {}}

    all_keys = set(ref.keys()) | set(actual_dist.keys())
    epsilon = 0.0001  # sifir bolme onleme

    total_psi = 0.0
    details: dict[str, float] = {}

    for key in sorted(all_keys):
        expected = max(ref.get(key, epsilon), epsilon)
        actual = max(actual_dist.get(key, epsilon), epsilon)

        psi_i = (actual - expected) * math.log(actual / expected)
        total_psi += psi_i
        details[key] = round(psi_i, 6)

    total_psi = round(total_psi, 6)

    if total_psi > 0.25:
        status = "severe_drift"
    elif total_psi > 0.1:
        status = "moderate_drift"
    else:
        status = "stable"

    return {"total_psi": total_psi, "status": status, "details": details}


def _compute_stats(
    values: list[float], include_minmax: bool = True
) -> dict[str, float]:
    """Temel istatistikler: mean, std, min, max."""
    n = len(values)
    if n == 0:
        return {}
    mean = sum(values) / n
    std = (sum((x - mean) ** 2 for x in values) / max(n - 1, 1)) ** 0.5
    result = {"mean": round(mean, 2), "std": round(std, 2)}
    if include_minmax:
        result["min"] = min(values)
        result["max"] = max(values)
    return result


def _distribution(items: list[str]) -> dict[str, float]:
    """Liste icerisindeki eleman dagilimini hesapla."""
    if not items:
        return {}
    counter = Counter(items)
    total = len(items)
    return {k: round(v / total, 4) for k, v in sorted(counter.items())}
