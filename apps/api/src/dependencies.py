"""
Emlak Teknoloji Platformu - FastAPI Dependencies

Ortak dependency'ler buradan yonetilir.
"""

from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db_session

# ---------- Database Session ----------
DBSession = Annotated[AsyncSession, Depends(get_db_session)]


# ---------- Request ID ----------
def get_request_id(request: Request) -> str:
    """
    Mevcut request'in request_id degerini dondurur.

    RequestIdMiddleware tarafindan request.state'e yazilir.
    Middleware aktif degilse (test gibi) 'unknown' doner.

    Kullanim:
        @app.get("/items")
        async def get_items(request_id: str = Depends(get_request_id)):
            logger.info("processing", request_id=request_id)
    """
    return getattr(request.state, "request_id", "unknown")


RequestId = Annotated[str, Depends(get_request_id)]


# TODO: Add authentication dependencies
# async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
#     ...
# CurrentUser = Annotated[User, Depends(get_current_user)]

# TODO: Add Redis dependency
# async def get_redis() -> Redis:
#     ...
# RedisClient = Annotated[Redis, Depends(get_redis)]

# TODO: Add pagination dependency
# class PaginationParams:
#     def __init__(self, skip: int = 0, limit: int = 20):
#         self.skip = skip
#         self.limit = min(limit, 100)
# Pagination = Annotated[PaginationParams, Depends()]
