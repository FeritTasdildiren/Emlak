"""
Emlak Teknoloji Platformu - JWT Blacklist

Redis üzerinde geçersiz kılınmış (logged out) token'ları tutar.
"""

import structlog
from redis.asyncio import Redis

logger = structlog.get_logger()


class TokenBlacklist:
    """
    Redis tabanlı token blacklist yönetimi.
    """

    def __init__(self, redis: Redis):
        self.redis = redis
        self.prefix = "blacklist:"

    async def add(self, token: str, expire_seconds: int) -> None:
        """
        Token'ı blacklist'e ekler.
        expire_seconds: Token'ın kalan ömrü kadar TTL atanır.
        """
        key = f"{self.prefix}{token}"
        await self.redis.setex(key, expire_seconds, "1")
        logger.info("token_blacklisted", token_suffix=token[-8:])

    async def is_blacklisted(self, token: str) -> bool:
        """
        Token blacklist'te mi kontrol eder.
        """
        key = f"{self.prefix}{token}"
        return await self.redis.exists(key) > 0
