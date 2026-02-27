"""
Emlak Teknoloji Platformu - Matching Service (v1)

Kural tabanlı ilan-müşteri eşleştirme motoru.

Skor Kriterleri (0-100, ağırlıklı ortalama):
    - Fiyat  (%30): Property.price vs Customer.budget_min/max
    - Konum  (%30): Property.district vs Customer.desired_districts[]
    - Oda    (%20): Property.rooms vs Customer.desired_rooms
    - Alan   (%20): Property.net_area vs Customer.desired_area_min/max

Kurallar:
    - Eksik kriter (null/empty) → atlanır, ağırlıklar normalize edilir
    - Minimum skor eşiği: 70 (altı oluşturulmaz)
    - Sadece buyer/renter müşteriler, sadece active ilanlar
    - Tenant izolasyonu: aynı office_id zorunlu
    - ON CONFLICT → mevcut skor güncellenir

Kullanım:
    matches = await MatchingService.find_matches_for_property(db, prop_id, office_id)
    matches = await MatchingService.find_matches_for_customer(db, cust_id, office_id)
"""

from __future__ import annotations

import json
import re
import time
from typing import TYPE_CHECKING

import structlog
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import noload

from src.core.exceptions import NotFoundError
from src.models.customer import Customer
from src.models.match import PropertyCustomerMatch
from src.models.property import Property

if TYPE_CHECKING:
    import uuid

    from celery.result import AsyncResult
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

# ---------- Constants ----------

SCORE_THRESHOLD = 70

DEFAULT_WEIGHTS: dict[str, float] = {
    "price": 0.30,
    "location": 0.30,
    "room": 0.20,
    "area": 0.20,
}


# ================================================================
# Room Parsing
# ================================================================


def parse_room_count(rooms_str: str | None) -> int | None:
    """
    Oda sayısı string'ini sayıya dönüştürür.

    Örnekler:
        "3+1" → 3
        "2+0" → 2
        "4"   → 4
        None  → None
        ""    → None
    """
    if not rooms_str or not rooms_str.strip():
        return None

    rooms_str = rooms_str.strip()

    # "3+1" pattern → ana oda sayısı (salon hariç)
    match = re.match(r"^(\d+)\s*\+\s*\d+$", rooms_str)
    if match:
        return int(match.group(1))

    # Plain number "4"
    match = re.match(r"^(\d+)$", rooms_str)
    if match:
        return int(match.group(1))

    return None


# ================================================================
# Score Calculators
# ================================================================


def _calculate_price_score(
    price: float,
    budget_min: float | None,
    budget_max: float | None,
) -> float | None:
    """
    Fiyat skor hesaplama.

    - Tam aralıkta [budget_min, budget_max] → 100
    - ±%20 dışında → 0
    - Arada lineer interpolasyon
    - Her iki bütçe sınırı da None ise → None (atla)
    """
    if budget_min is None and budget_max is None:
        return None

    price_f = float(price)

    # Sadece max var
    if budget_min is None:
        bmax = float(budget_max)  # type: ignore[arg-type]
        if price_f <= bmax:
            return 100.0
        upper = bmax * 1.2
        if price_f >= upper:
            return 0.0
        return max(0.0, 100.0 * (upper - price_f) / (upper - bmax))

    # Sadece min var
    if budget_max is None:
        bmin = float(budget_min)
        if price_f >= bmin:
            return 100.0
        lower = bmin * 0.8
        if price_f <= lower:
            return 0.0
        return max(0.0, 100.0 * (price_f - lower) / (bmin - lower))

    # Her ikisi de var
    bmin = float(budget_min)
    bmax = float(budget_max)

    if bmin <= price_f <= bmax:
        return 100.0

    if price_f < bmin:
        lower = bmin * 0.8
        if price_f <= lower:
            return 0.0
        return max(0.0, 100.0 * (price_f - lower) / (bmin - lower))

    # price > budget_max
    upper = bmax * 1.2
    if price_f >= upper:
        return 0.0
    return max(0.0, 100.0 * (upper - price_f) / (upper - bmax))


def _calculate_location_score(
    district: str,
    desired_districts: list,
) -> float | None:
    """
    Konum skor hesaplama.

    - Exact match (case-insensitive) → 100
    - Yoksa → 0
    - desired_districts boş ise → None (atla)
    """
    if not desired_districts:
        return None

    district_lower = district.lower().strip()
    for d in desired_districts:
        if isinstance(d, str) and d.lower().strip() == district_lower:
            return 100.0

    return 0.0


def _calculate_room_score(
    property_rooms: str | None,
    desired_rooms: str | None,
) -> float | None:
    """
    Oda sayısı skor hesaplama.

    - Exact → 100
    - ±1   → 50
    - ±2   → 20
    - Daha fazla → 0
    - Herhangi biri None / parse edilemez ise → None (atla)
    """
    prop_count = parse_room_count(property_rooms)
    desired_count = parse_room_count(desired_rooms)

    if prop_count is None or desired_count is None:
        return None

    diff = abs(prop_count - desired_count)

    if diff == 0:
        return 100.0
    if diff == 1:
        return 50.0
    if diff == 2:
        return 20.0
    return 0.0


def _calculate_area_score(
    net_area: float | None,
    area_min: int | None,
    area_max: int | None,
) -> float | None:
    """
    Alan skor hesaplama.

    - Tam aralıkta [area_min, area_max] → 100
    - ±%20 dışında → 0
    - Arada lineer interpolasyon
    - net_area veya her iki sınır None ise → None (atla)
    """
    if net_area is None:
        return None

    if area_min is None and area_max is None:
        return None

    area_f = float(net_area)

    # Sadece max var
    if area_min is None:
        amax = float(area_max)  # type: ignore[arg-type]
        if area_f <= amax:
            return 100.0
        upper = amax * 1.2
        if area_f >= upper:
            return 0.0
        return max(0.0, 100.0 * (upper - area_f) / (upper - amax))

    # Sadece min var
    if area_max is None:
        amin = float(area_min)
        if area_f >= amin:
            return 100.0
        lower = amin * 0.8
        if area_f <= lower:
            return 0.0
        return max(0.0, 100.0 * (area_f - lower) / (amin - lower))

    # Her ikisi de var
    amin = float(area_min)
    amax = float(area_max)

    if amin <= area_f <= amax:
        return 100.0

    if area_f < amin:
        lower = amin * 0.8
        if area_f <= lower:
            return 0.0
        return max(0.0, 100.0 * (area_f - lower) / (amin - lower))

    # area > area_max
    upper = amax * 1.2
    if area_f >= upper:
        return 0.0
    return max(0.0, 100.0 * (upper - area_f) / (upper - amax))


# ================================================================
# Composite Score
# ================================================================


def calculate_match_score(
    prop: Property,
    customer: Customer,
) -> tuple[float, dict]:
    """
    İlan-müşteri çifti için bileşik skor hesaplar.

    Eksik kriterler atlanır, kalan ağırlıklar oransal normalize edilir.

    Returns:
        (final_score, details_dict) tuple.
        details_dict: price_score, location_score, room_score, area_score, weights_used
    """
    raw_scores: dict[str, float | None] = {
        "price": _calculate_price_score(
            prop.price, customer.budget_min, customer.budget_max,
        ),
        "location": _calculate_location_score(
            prop.district, customer.desired_districts,
        ),
        "room": _calculate_room_score(
            prop.rooms, customer.desired_rooms,
        ),
        "area": _calculate_area_score(
            prop.net_area, customer.desired_area_min, customer.desired_area_max,
        ),
    }

    # Aktif kriterleri filtrele (None olmayanlar)
    active_criteria = {k: v for k, v in raw_scores.items() if v is not None}

    if not active_criteria:
        return 0.0, {
            "price_score": None,
            "location_score": None,
            "room_score": None,
            "area_score": None,
            "weights_used": {},
        }

    # Ağırlıkları normalize et
    total_weight = sum(DEFAULT_WEIGHTS[k] for k in active_criteria)
    normalized_weights = {
        k: DEFAULT_WEIGHTS[k] / total_weight for k in active_criteria
    }

    # Ağırlıklı ortalama
    final_score = sum(
        active_criteria[k] * normalized_weights[k]
        for k in active_criteria
    )
    final_score = round(final_score, 2)

    details = {
        "price_score": round(raw_scores["price"], 2) if raw_scores["price"] is not None else None,
        "location_score": round(raw_scores["location"], 2) if raw_scores["location"] is not None else None,
        "room_score": round(raw_scores["room"], 2) if raw_scores["room"] is not None else None,
        "area_score": round(raw_scores["area"], 2) if raw_scores["area"] is not None else None,
        "weights_used": {k: round(v, 4) for k, v in normalized_weights.items()},
    }

    return final_score, details


# ================================================================
# Matching Service
# ================================================================


class MatchingService:
    """
    Kural tabanlı eşleştirme motoru.

    İlan veya müşteri bazlı eşleştirme çalıştırır.
    Skor eşiği (70) üstündeki eşleşmeleri DB'ye batch upsert eder.
    Tenant izolasyonu: Sadece aynı office_id içinde çalışır.
    """

    @staticmethod
    async def find_matches_for_property(
        db: AsyncSession,
        property_id: uuid.UUID,
        office_id: uuid.UUID,
    ) -> list[dict]:
        """
        Verilen ilan için tüm uyumlu müşterileri bulur, skor hesaplar,
        eşik üstündekileri PropertyCustomerMatch olarak kaydeder.

        Args:
            db: Async database session.
            property_id: İlan UUID.
            office_id: Tenant (ofis) UUID.

        Returns:
            Oluşturulan/güncellenen eşleştirme kayıtları (dict listesi).

        Raises:
            NotFoundError: İlan bulunamadı veya aktif değil.
        """
        start_time = time.monotonic()

        # 1. Aktif ilanı getir (tenant izolasyonu dahil)
        # noload("*") — skor hesabı için ilişkili nesneler gerekmez
        result = await db.execute(
            select(Property)
            .options(noload("*"))
            .where(
                Property.id == property_id,
                Property.office_id == office_id,
                Property.status == "active",
            )
        )
        prop = result.scalar_one_or_none()

        if prop is None:
            raise NotFoundError(
                resource="Aktif ilan", resource_id=str(property_id),
            )

        # 2. Uygun müşterileri getir (buyer/renter, aynı ofis)
        result = await db.execute(
            select(Customer)
            .options(noload("*"))
            .where(
                Customer.office_id == office_id,
                Customer.customer_type.in_(["buyer", "renter"]),
            )
        )
        customers = list(result.scalars().all())

        # 3. Her müşteri için skor hesapla
        match_records: list[dict] = []
        for customer in customers:
            score, details = calculate_match_score(prop, customer)

            if score >= SCORE_THRESHOLD:
                match_records.append({
                    "office_id": office_id,
                    "property_id": property_id,
                    "customer_id": customer.id,
                    "score": score,
                    "status": "pending",
                    "notes": json.dumps(details, ensure_ascii=False),
                })

        # 4. Batch upsert (ON CONFLICT DO UPDATE)
        if match_records:
            stmt = insert(PropertyCustomerMatch).values(match_records)
            stmt = stmt.on_conflict_do_update(
                constraint="uq_matches_property_customer",
                set_={
                    "score": stmt.excluded.score,
                    "notes": stmt.excluded.notes,
                    "updated_at": text("now()"),
                },
            )
            await db.execute(stmt)
            await db.flush()

        elapsed_ms = int((time.monotonic() - start_time) * 1000)

        logger.info(
            "matching_completed_for_property",
            property_id=str(property_id),
            office_id=str(office_id),
            candidates=len(customers),
            matches_created=len(match_records),
            elapsed_ms=elapsed_ms,
        )

        return match_records

    @staticmethod
    async def find_matches_for_customer(
        db: AsyncSession,
        customer_id: uuid.UUID,
        office_id: uuid.UUID,
    ) -> list[dict]:
        """
        Verilen müşteri için tüm uyumlu ilanları bulur, skor hesaplar,
        eşik üstündekileri PropertyCustomerMatch olarak kaydeder.

        Args:
            db: Async database session.
            customer_id: Müşteri UUID.
            office_id: Tenant (ofis) UUID.

        Returns:
            Oluşturulan/güncellenen eşleştirme kayıtları (dict listesi).

        Raises:
            NotFoundError: Müşteri bulunamadı veya buyer/renter değil.
        """
        start_time = time.monotonic()

        # 1. Müşteriyi getir (buyer/renter kontrolü dahil)
        # noload("*") — skor hesabı için ilişkili nesneler gerekmez
        result = await db.execute(
            select(Customer)
            .options(noload("*"))
            .where(
                Customer.id == customer_id,
                Customer.office_id == office_id,
                Customer.customer_type.in_(["buyer", "renter"]),
            )
        )
        customer = result.scalar_one_or_none()

        if customer is None:
            raise NotFoundError(
                resource="Musteri (buyer/renter)", resource_id=str(customer_id),
            )

        # 2. Aktif ilanları getir (aynı ofis)
        result = await db.execute(
            select(Property)
            .options(noload("*"))
            .where(
                Property.office_id == office_id,
                Property.status == "active",
            )
        )
        properties = list(result.scalars().all())

        # 3. Her ilan için skor hesapla
        match_records: list[dict] = []
        for prop in properties:
            score, details = calculate_match_score(prop, customer)

            if score >= SCORE_THRESHOLD:
                match_records.append({
                    "office_id": office_id,
                    "property_id": prop.id,
                    "customer_id": customer_id,
                    "score": score,
                    "status": "pending",
                    "notes": json.dumps(details, ensure_ascii=False),
                })

        # 4. Batch upsert (ON CONFLICT DO UPDATE)
        if match_records:
            stmt = insert(PropertyCustomerMatch).values(match_records)
            stmt = stmt.on_conflict_do_update(
                constraint="uq_matches_property_customer",
                set_={
                    "score": stmt.excluded.score,
                    "notes": stmt.excluded.notes,
                    "updated_at": text("now()"),
                },
            )
            await db.execute(stmt)
            await db.flush()

        elapsed_ms = int((time.monotonic() - start_time) * 1000)

        logger.info(
            "matching_completed_for_customer",
            customer_id=str(customer_id),
            office_id=str(office_id),
            candidates=len(properties),
            matches_created=len(match_records),
            elapsed_ms=elapsed_ms,
        )

        return match_records


# ================================================================
# Trigger Helpers (Celery .delay() wrappers)
# ================================================================


def trigger_matching_after_property_create(
    property_id: uuid.UUID,
    office_id: uuid.UUID,
) -> AsyncResult:
    """
    İlan oluşturulduktan sonra eşleştirme tetikler.

    Celery task'ını kuyruğa atar (.delay()).
    İleride property CRUD router POST'una eklenecek.

    Args:
        property_id: Yeni oluşturulan ilan UUID.
        office_id: Tenant UUID.

    Returns:
        Celery AsyncResult — task takip için.
    """
    from src.modules.matches.tasks import trigger_matching_for_property

    logger.info(
        "matching_triggered_for_property",
        property_id=str(property_id),
        office_id=str(office_id),
    )

    return trigger_matching_for_property.delay(
        str(property_id),
        str(office_id),
    )


def trigger_matching_after_customer_create(
    customer_id: uuid.UUID,
    office_id: uuid.UUID,
) -> AsyncResult:
    """
    Müşteri oluşturulduktan sonra eşleştirme tetikler.

    Celery task'ını kuyruğa atar (.delay()).
    customers/router.py POST endpoint'ine entegre edilecek.

    Args:
        customer_id: Yeni oluşturulan müşteri UUID.
        office_id: Tenant UUID.

    Returns:
        Celery AsyncResult — task takip için.
    """
    from src.modules.matches.tasks import trigger_matching_for_customer

    logger.info(
        "matching_triggered_for_customer",
        customer_id=str(customer_id),
        office_id=str(office_id),
    )

    return trigger_matching_for_customer.delay(
        str(customer_id),
        str(office_id),
    )
