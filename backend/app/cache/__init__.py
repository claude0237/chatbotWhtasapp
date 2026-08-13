"""Cache Service for Redis"""
from typing import Optional, Any, List
import json
import redis.asyncio as redis
import logging
from sqlalchemy.orm import DeclarativeBase
from app.config import settings
from app.logging_config import log_with_context


class SQLAlchemyEncoder(json.JSONEncoder):
    """Custom JSON encoder for SQLAlchemy objects"""
    def default(self, obj):
        if isinstance(obj, DeclarativeBase):
            # Convert SQLAlchemy model to dictionary
            return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
        return super().default(obj)


class CacheService:
    """Generic Redis cache service with async support"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.logger = logging.getLogger("app.cache")
    
    async def _ensure_client(self):
        """Lazily initialize Redis client"""
        if self.redis_client is None and settings.redis_cache_url:
            try:
                self.redis_client = redis.from_url(settings.redis_cache_url, decode_responses=True)
                log_with_context(
                    self.logger,
                    logging.INFO,
                    "REDIS_CONNECTION_SUCCESS",
                    url=settings.redis_cache_url
                )
            except Exception as e:
                log_with_context(
                    self.logger,
                    logging.ERROR,
                    "REDIS_CONNECTION_FAILED",
                    url=settings.redis_cache_url,
                    error_message=str(e),
                    exc_info=True
                )
    
    def _make_key(self, prefix: str, *parts: Any) -> str:
        """Generate cache key from prefix and parts"""
        key_parts = [str(p) for p in parts if p is not None]
        return f"{prefix}:{':'.join(key_parts)}"
    
    async def get(self, prefix: str, *parts: Any) -> Optional[Any]:
        """Get value from cache"""
        await self._ensure_client()
        if not self.redis_client:
            return None
        
        try:
            key = self._make_key(prefix, *parts)
            cached = await self.redis_client.get(key)
            if cached:
                log_with_context(
                    self.logger,
                    logging.INFO,
                    "REDIS_GET_SUCCESS",
                    key=key
                )
                return json.loads(cached)
        except Exception as e:
            log_with_context(
                self.logger,
                logging.ERROR,
                "REDIS_GET_FAILED",
                key=self._make_key(prefix, *parts),
                error_message=str(e),
                exc_info=True
            )
        
        return None
    
    async def set(self, prefix: str, *parts: Any, value: Any, ttl: int = 900) -> bool:
        """Set value in cache with TTL (default 15 minutes)"""
        await self._ensure_client()
        if not self.redis_client:
            return False
        
        try:
            key = self._make_key(prefix, *parts)
            await self.redis_client.setex(key, ttl, json.dumps(value, cls=SQLAlchemyEncoder))
            log_with_context(
                self.logger,
                logging.INFO,
                "REDIS_SET_SUCCESS",
                key=key,
                ttl=ttl
            )
            return True
        except Exception as e:
            log_with_context(
                self.logger,
                logging.ERROR,
                "REDIS_SET_FAILED",
                key=self._make_key(prefix, *parts),
                ttl=ttl,
                error_message=str(e),
                exc_info=True
            )
            return False
    
    async def delete(self, prefix: str, *parts: Any) -> bool:
        """Delete value from cache"""
        await self._ensure_client()
        if not self.redis_client:
            return False
        
        try:
            key = self._make_key(prefix, *parts)
            await self.redis_client.delete(key)
            return True
        except Exception:
            return False
    
    async def delete_pattern(self, pattern: str) -> bool:
        """Delete all keys matching pattern"""
        await self._ensure_client()
        if not self.redis_client:
            return False
        
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
            return True
        except Exception:
            return False
    
    async def invalidate_company(self, company_id: str) -> bool:
        """Invalidate all cache entries for a company"""
        await self._ensure_client()
        if not self.redis_client:
            return False
        
        try:
            patterns = [
                f"bot_config:{company_id}:*",
                f"products:{company_id}:*",
                f"categories:{company_id}:*",
                f"keywords:{company_id}:*",
                f"scenarios:{company_id}:*",
            ]
            for pattern in patterns:
                await self.delete_pattern(pattern)
            return True
        except Exception:
            return False


# Singleton instance
_cache_service: Optional[CacheService] = None


async def get_cache_service() -> CacheService:
    """Get or create cache service singleton"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
