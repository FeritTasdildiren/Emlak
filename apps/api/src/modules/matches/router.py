"""
Emlak Teknoloji Platformu - Matches Router

İlan-Müşteri eşleştirme API endpoint'leri.

Prefix: /api/v1/matches
Güvenlik: Tüm endpoint'ler JWT gerektirir (ActiveUser dependency).
Tenant izolasyonu: office_id otomatik olarak JWT'den alınır.

Endpoint'ler:
    GET    /matches                        → Eşleştirme listesi (filtre)
    GET    /matches/{id}                   → Eşleştirme detay
    PATCH  /matches/{id}/status            → Eşleştirme durumunu güncelle
    POST   /matches/run/property/{id}      → İlan için eşleştirme çalıştır
    POST   /matches/run/customer/{id}      → Müşteri için eşleştirme çalıştır
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Annotated

import structlog
from fastapi import APIRouter, Query

from src.dependencies import DBSession
from src.modules.auth.dependencies import ActiveUser
from src.modules.matches.matching_service import MatchingService
from src.modules.matches.schemas import (
    MatchListResponse,
    MatchResponse,
    MatchRunResponse,
    MatchStatusUpdate,
)
from src.modules.matches.service import MatchService

if TYPE_CHECKING:
    import uuid

logger = structlog.get_logger()

router = APIRouter(
    prefix="/api/v1/matches",
    tags=["matches"],
)


def _to_response(match) -> MatchResponse:
    """PropertyCustomerMatch entity'sini response modeline dönüştürür."""
    return MatchResponse(
        id=str(match.id),
        property_id=str(match.property_id),
        customer_id=str(match.customer_id),
        score=match.score,
        status=match.status,
        matched_at=match.matched_at,
        responded_at=match.responded_at,
        notes=match.notes,
        created_at=match.created_at,
        updated_at=match.updated_at,
    )


# ---------- GET /matches ----------


@router.get(
    "",
    response_model=MatchListResponse,
    summary="Eşleştirme listesi",
    description="Ofise ait eşleştirmeleri sayfalama ve filtrelerle listeler.",
)
async def list_matches(
    db: DBSession,
    current_user: ActiveUser,
    page: int = Query(default=1, ge=1, description="Sayfa numarası"),
    per_page: int = Query(default=20, ge=1, le=100, description="Sayfa başına kayıt (max 100)"),
    customer_id: Annotated[uuid.UUID | None, Query(description="Müşteri ID filtresi")] = None,
    property_id: Annotated[uuid.UUID | None, Query(description="İlan ID filtresi")] = None,
    status: str | None = Query(default=None, description="Durum filtresi"),
) -> MatchListResponse:
    """
    Ofise ait eşleştirmeleri listeler.

    - Score'a göre azalan sırada sıralanır
    - Filtreler: customer_id, property_id, status
    """
    matches, total = await MatchService.list_matches(
        db=db,
        office_id=current_user.office_id,
        page=page,
        per_page=per_page,
        customer_id=customer_id,
        property_id=property_id,
        status=status,
    )

    return MatchListResponse(
        items=[_to_response(m) for m in matches],
        total=total,
        page=page,
        per_page=per_page,
    )


# ---------- GET /matches/{id} ----------


@router.get(
    "/{match_id}",
    response_model=MatchResponse,
    summary="Eşleştirme detay",
    description="Belirtilen eşleştirmenin detaylarını döndürür.",
)
async def get_match(
    match_id: uuid.UUID,
    db: DBSession,
    current_user: ActiveUser,
) -> MatchResponse:
    """
    Eşleştirme detayını getirir.

    - Sadece kendi ofisinin eşleştirmeleri görülebilir
    - Eşleştirme bulunamazsa 404
    """
    match = await MatchService.get_by_id(
        db=db,
        match_id=match_id,
        office_id=current_user.office_id,
    )
    return _to_response(match)


# ---------- PATCH /matches/{id}/status ----------


@router.patch(
    "/{match_id}/status",
    response_model=MatchResponse,
    summary="Eşleştirme durumunu güncelle",
    description="Belirtilen eşleştirmenin durumunu günceller.",
)
async def update_match_status(
    match_id: uuid.UUID,
    body: MatchStatusUpdate,
    db: DBSession,
    current_user: ActiveUser,
) -> MatchResponse:
    """
    Eşleştirme durumunu günceller.

    Geçerli durumlar: pending, interested, passed, contacted, converted
    """
    match = await MatchService.update_status(
        db=db,
        match_id=match_id,
        office_id=current_user.office_id,
        new_status=body.status,
        notes=body.notes,
    )
    return _to_response(match)


# ---------- POST /matches/run/property/{property_id} ----------


@router.post(
    "/run/property/{property_id}",
    response_model=MatchRunResponse,
    summary="İlan için eşleştirme çalıştır",
    description="Verilen ilan için tüm uyumlu müşterileri bulur ve eşleştirir.",
)
async def run_matching_for_property(
    property_id: uuid.UUID,
    db: DBSession,
    current_user: ActiveUser,
) -> MatchRunResponse:
    """
    Bir ilan için eşleştirme motorunu çalıştırır.

    - Sadece aktif ilanlar için çalışır
    - Aynı ofisteki buyer/renter müşteriler taranır
    - Skor ≥ 70 olan eşleşmeler oluşturulur / güncellenir
    """
    start_time = time.monotonic()

    matches = await MatchingService.find_matches_for_property(
        db=db,
        property_id=property_id,
        office_id=current_user.office_id,
    )

    elapsed_ms = int((time.monotonic() - start_time) * 1000)
    top_score = max((m["score"] for m in matches), default=None)

    return MatchRunResponse(
        matches_found=len(matches),
        matches_created=len(matches),
        top_score=top_score,
        execution_time_ms=elapsed_ms,
    )


# ---------- POST /matches/run/customer/{customer_id} ----------


@router.post(
    "/run/customer/{customer_id}",
    response_model=MatchRunResponse,
    summary="Müşteri için eşleştirme çalıştır",
    description="Verilen müşteri için tüm uyumlu ilanları bulur ve eşleştirir.",
)
async def run_matching_for_customer(
    customer_id: uuid.UUID,
    db: DBSession,
    current_user: ActiveUser,
) -> MatchRunResponse:
    """
    Bir müşteri için eşleştirme motorunu çalıştırır.

    - Sadece buyer/renter tipi müşteriler için çalışır
    - Aynı ofisteki aktif ilanlar taranır
    - Skor ≥ 70 olan eşleşmeler oluşturulur / güncellenir
    """
    start_time = time.monotonic()

    matches = await MatchingService.find_matches_for_customer(
        db=db,
        customer_id=customer_id,
        office_id=current_user.office_id,
    )

    elapsed_ms = int((time.monotonic() - start_time) * 1000)
    top_score = max((m["score"] for m in matches), default=None)

    return MatchRunResponse(
        matches_found=len(matches),
        matches_created=len(matches),
        top_score=top_score,
        execution_time_ms=elapsed_ms,
    )
