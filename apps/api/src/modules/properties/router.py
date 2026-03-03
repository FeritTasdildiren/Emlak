"""
Emlak Teknoloji Platformu - Properties Router

Ilan CRUD + paylasim ayarlari endpoint'leri.

Prefix: /api/v1/properties
Guvenlik: Tum endpoint'ler JWT gerektirir (ActiveUser dependency).
Tenant izolasyonu: office_id otomatik olarak JWT'den alinir.

Endpoint'ler:
    POST  /properties              -> Yeni ilan olustur (JWT)
    GET   /properties/{id}         -> Ilan detay (JWT)
    PATCH /properties/{id}         -> Ilan guncelle (JWT)
    PATCH /properties/{id}/sharing -> Paylasim ayarlarini guncelle (JWT)
    DELETE /properties/{id}        -> Ilan sil (JWT)
"""

from __future__ import annotations

import uuid  # noqa: TC003 — FastAPI path param runtime resolution icin gerekli
from typing import TYPE_CHECKING

import structlog
from fastapi import APIRouter, Request, status
from geoalchemy2 import Geometry
from geoalchemy2.elements import WKTElement
from sqlalchemy import func, select

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError
from src.dependencies import DBSession
from src.models.property import Property
from src.modules.audit.audit_service import AuditService
from src.modules.auth.dependencies import ActiveUser
from src.modules.properties.schemas import (
    PropertyCreate,
    PropertyDetailResponse,
    PropertyUpdate,
)
from src.modules.showcases.schemas import PropertySharingResponse, PropertySharingUpdate

logger = structlog.get_logger()

router = APIRouter(
    prefix="/api/v1/properties",
    tags=["properties"],
)


# ---------- Helpers ----------


async def _get_property(
    db: AsyncSession,
    property_id: uuid.UUID,
    office_id: uuid.UUID,
) -> Property:
    """Ilani ID ile getirir, tenant izolasyonlu."""
    result = await db.execute(
        select(Property).where(
            Property.id == property_id,
            Property.office_id == office_id,
        )
    )
    prop = result.scalar_one_or_none()
    if prop is None:
        raise NotFoundError(resource="Ilan", resource_id=str(property_id))
    return prop


async def _build_detail_response(
    db: AsyncSession,
    property_id: uuid.UUID,
    office_id: uuid.UUID,
) -> PropertyDetailResponse:
    """Property entity + PostGIS koordinatlarini iceren detay response olusturur."""
    stmt = (
        select(
            Property,
            func.ST_Y(Property.location.cast(Geometry)).label("lat"),
            func.ST_X(Property.location.cast(Geometry)).label("lon"),
        )
        .where(
            Property.id == property_id,
            Property.office_id == office_id,
        )
    )
    result = await db.execute(stmt)
    row = result.one_or_none()

    if row is None:
        raise NotFoundError(resource="Ilan", resource_id=str(property_id))

    prop = row[0]
    lat = row[1]
    lon = row[2]

    return PropertyDetailResponse(
        id=str(prop.id),
        title=prop.title,
        description=prop.description,
        property_type=prop.property_type,
        listing_type=prop.listing_type,
        price=float(prop.price),
        currency=prop.currency,
        rooms=prop.rooms,
        gross_area=float(prop.gross_area) if prop.gross_area is not None else None,
        net_area=float(prop.net_area) if prop.net_area is not None else None,
        floor_number=prop.floor_number,
        total_floors=prop.total_floors,
        building_age=prop.building_age,
        heating_type=prop.heating_type,
        bathroom_count=prop.bathroom_count,
        furniture_status=prop.furniture_status,
        building_type=prop.building_type,
        facade=prop.facade,
        city=prop.city,
        district=prop.district,
        neighborhood=prop.neighborhood,
        address=prop.address,
        latitude=float(lat) if lat is not None else None,
        longitude=float(lon) if lon is not None else None,
        photos=prop.photos or [],
        status=prop.status,
        created_at=prop.created_at,
        updated_at=prop.updated_at,
    )


# ---------- POST /properties ----------


@router.post(
    "",
    response_model=PropertyDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yeni ilan olustur",
    description="Yeni bir emlak ilani olusturur. JWT zorunlu, tenant izolasyonlu.",
)
async def create_property(
    request: Request,
    body: PropertyCreate,
    db: DBSession,
    current_user: ActiveUser,
) -> PropertyDetailResponse:
    """
    Yeni ilan olusturur.

    - agent_id: Oturum acmis kullanicinin ID'si
    - office_id: JWT'den alinan tenant ofis ID'si (RLS)
    - Koordinatlar PostGIS GEOGRAPHY POINT olarak kaydedilir
    - KVKK audit kaydi olusturulur
    """
    prop = Property(
        agent_id=current_user.id,
        office_id=current_user.office_id,
        title=body.title,
        description=body.description,
        property_type=body.property_type,
        listing_type=body.listing_type,
        price=body.price,
        currency=body.currency,
        rooms=body.rooms,
        gross_area=body.gross_area,
        net_area=body.net_area,
        floor_number=body.floor_number,
        total_floors=body.total_floors,
        building_age=body.building_age,
        heating_type=body.heating_type,
        bathroom_count=body.bathroom_count,
        furniture_status=body.furniture_status,
        building_type=body.building_type,
        facade=body.facade,
        city=body.city,
        district=body.district,
        neighborhood=body.neighborhood,
        address=body.address,
        location=WKTElement(f"POINT({body.lon} {body.lat})", srid=4326),
        features=body.features or {},
        photos=body.photos or [],
        status=body.status,
    )

    db.add(prop)
    await db.flush()

    logger.info(
        "property_created",
        property_id=str(prop.id),
        office_id=str(current_user.office_id),
        agent_id=str(current_user.id),
        listing_type=body.listing_type,
    )

    # KVKK Audit: Ilan olusturma kaydi
    await AuditService.log_action(
        db=db,
        user_id=current_user.id,
        office_id=current_user.office_id,
        action="CREATE",
        entity_type="Property",
        entity_id=str(prop.id),
        new_value={"title": body.title, "listing_type": body.listing_type},
        request=request,
    )

    return await _build_detail_response(
        db=db,
        property_id=prop.id,
        office_id=current_user.office_id,
    )


# ---------- GET /properties/{property_id} ----------


@router.get(
    "/{property_id}",
    response_model=PropertyDetailResponse,
    summary="Ilan detay",
    description="Belirtilen ilanin tum detaylarini dondurur. JWT zorunlu, tenant izolasyonlu.",
)
async def get_property_detail(
    property_id: uuid.UUID,
    db: DBSession,
    current_user: ActiveUser,
) -> PropertyDetailResponse:
    """
    Ilan detayini getirir.

    - Sadece kendi ofisinin ilanlari gorulebilir (tenant isolation)
    - Ilan bulunamazsa 404
    - Koordinatlar PostGIS GEOGRAPHY'den cikarilir
    """
    # Property entity + koordinatlari tek sorguda getir
    stmt = (
        select(
            Property,
            func.ST_Y(
                Property.location.cast(Geometry)
            ).label("lat"),
            func.ST_X(
                Property.location.cast(Geometry)
            ).label("lon"),
        )
        .where(
            Property.id == property_id,
            Property.office_id == current_user.office_id,
        )
    )
    result = await db.execute(stmt)
    row = result.one_or_none()

    if row is None:
        raise NotFoundError(resource="Ilan", resource_id=str(property_id))

    prop = row[0]
    lat = row[1]
    lon = row[2]

    return PropertyDetailResponse(
        id=str(prop.id),
        title=prop.title,
        description=prop.description,
        property_type=prop.property_type,
        listing_type=prop.listing_type,
        price=float(prop.price),
        currency=prop.currency,
        rooms=prop.rooms,
        gross_area=float(prop.gross_area) if prop.gross_area is not None else None,
        net_area=float(prop.net_area) if prop.net_area is not None else None,
        floor_number=prop.floor_number,
        total_floors=prop.total_floors,
        building_age=prop.building_age,
        heating_type=prop.heating_type,
        bathroom_count=prop.bathroom_count,
        furniture_status=prop.furniture_status,
        building_type=prop.building_type,
        facade=prop.facade,
        city=prop.city,
        district=prop.district,
        neighborhood=prop.neighborhood,
        address=prop.address,
        latitude=float(lat) if lat is not None else None,
        longitude=float(lon) if lon is not None else None,
        photos=prop.photos or [],
        status=prop.status,
        created_at=prop.created_at,
        updated_at=prop.updated_at,
    )


# ---------- PATCH /properties/{property_id}/sharing ----------


@router.patch(
    "/{property_id}/sharing",
    response_model=PropertySharingResponse,
    summary="Ilan paylasim ayarlarini guncelle",
    description=(
        "Ilanin ofisler arasi paylasim durumunu ve gorunurlugunu gunceller. "
        "is_shared: true yapildiginda ilan diger ofislerce gorulebilir hale gelir."
    ),
)
async def update_property_sharing(
    request: Request,
    property_id: uuid.UUID,
    body: PropertySharingUpdate,
    db: DBSession,
    current_user: ActiveUser,
) -> PropertySharingResponse:
    """
    Ilan paylasim ayarlarini gunceller.

    - is_shared: Ofisler arasi paylasima ac/kapat
    - share_visibility: private | shared | public
    - Ilan bulunamazsa 404
    """
    prop = await _get_property(
        db=db,
        property_id=property_id,
        office_id=current_user.office_id,
    )

    prop.is_shared = body.is_shared
    prop.share_visibility = body.share_visibility

    await db.flush()

    logger.info(
        "property_sharing_updated",
        property_id=str(property_id),
        office_id=str(current_user.office_id),
        is_shared=body.is_shared,
        share_visibility=body.share_visibility,
    )

    # KVKK Audit: Ilan guncelleme kaydi
    await AuditService.log_action(
        db=db,
        user_id=current_user.id,
        office_id=current_user.office_id,
        action="UPDATE",
        entity_type="Property",
        entity_id=str(property_id),
        new_value={
            "is_shared": body.is_shared,
            "share_visibility": body.share_visibility,
        },
        request=request,
    )

    return PropertySharingResponse(
        id=str(prop.id),
        is_shared=prop.is_shared,
        share_visibility=prop.share_visibility,
    )


# ---------- PATCH /properties/{property_id} ----------


@router.patch(
    "/{property_id}",
    response_model=PropertyDetailResponse,
    summary="Ilan guncelle",
    description=(
        "Ilanin bilgilerini gunceller (partial update). "
        "Sadece gonderilen alanlar guncellenir, diger alanlar degismez."
    ),
)
async def update_property(
    request: Request,
    property_id: uuid.UUID,
    body: PropertyUpdate,
    db: DBSession,
    current_user: ActiveUser,
) -> PropertyDetailResponse:
    """
    Ilan bilgilerini gunceller (partial update).

    - Sadece request body'de gonderilen alanlar guncellenir (exclude_unset)
    - lat/lon guncellenirse PostGIS location da guncellenir
    - Ilan bulunamazsa 404
    - KVKK audit kaydi olusturulur
    """
    prop = await _get_property(
        db=db,
        property_id=property_id,
        office_id=current_user.office_id,
    )

    update_data = body.model_dump(exclude_unset=True)

    if not update_data:
        # Guncellenecek alan yok, mevcut hali don
        return await _build_detail_response(
            db=db,
            property_id=property_id,
            office_id=current_user.office_id,
        )

    # lat/lon alanlarini ayir — bunlar dogrudan model alanlariy degil
    new_lat = update_data.pop("lat", None)
    new_lon = update_data.pop("lon", None)

    # Standart alanlari guncelle
    for field, value in update_data.items():
        setattr(prop, field, value)

    # Koordinat guncelleme: lat veya lon degistiyse location yeniden hesapla
    if new_lat is not None or new_lon is not None:
        # Mevcut koordinatlari al (degismeyen deger icin)
        coord_stmt = select(
            func.ST_Y(Property.location.cast(Geometry)).label("cur_lat"),
            func.ST_X(Property.location.cast(Geometry)).label("cur_lon"),
        ).where(Property.id == property_id)
        coord_result = await db.execute(coord_stmt)
        coord_row = coord_result.one()

        final_lat = new_lat if new_lat is not None else float(coord_row.cur_lat)
        final_lon = new_lon if new_lon is not None else float(coord_row.cur_lon)
        prop.location = WKTElement(f"POINT({final_lon} {final_lat})", srid=4326)

    await db.flush()

    logger.info(
        "property_updated",
        property_id=str(property_id),
        office_id=str(current_user.office_id),
        updated_fields=list(body.model_dump(exclude_unset=True).keys()),
    )

    # KVKK Audit: Ilan guncelleme kaydi
    await AuditService.log_action(
        db=db,
        user_id=current_user.id,
        office_id=current_user.office_id,
        action="UPDATE",
        entity_type="Property",
        entity_id=str(property_id),
        new_value=body.model_dump(exclude_unset=True),
        request=request,
    )

    return await _build_detail_response(
        db=db,
        property_id=property_id,
        office_id=current_user.office_id,
    )


# ---------- DELETE /properties/{property_id} ----------


@router.delete(
    "/{property_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Ilan sil",
    description="Ilani kalici olarak siler (hard delete). Geri alinamaz.",
)
async def delete_property(
    request: Request,
    property_id: uuid.UUID,
    db: DBSession,
    current_user: ActiveUser,
) -> None:
    """
    Ilani kalici olarak siler.

    - Hard delete — kayit veritabanindan tamamen silinir
    - Ilan bulunamazsa 404
    - KVKK audit kaydi olusturulur
    """
    prop = await _get_property(
        db=db,
        property_id=property_id,
        office_id=current_user.office_id,
    )

    property_title = prop.title

    await db.delete(prop)
    await db.flush()

    logger.info(
        "property_deleted",
        property_id=str(property_id),
        office_id=str(current_user.office_id),
        title=property_title,
    )

    # KVKK Audit: Ilan silme kaydi
    await AuditService.log_action(
        db=db,
        user_id=current_user.id,
        office_id=current_user.office_id,
        action="DELETE",
        entity_type="Property",
        entity_id=str(property_id),
        new_value={"title": property_title},
        request=request,
    )
