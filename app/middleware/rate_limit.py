from slowapi import Limiter  # type: ignore
from slowapi.util import get_remote_address  # type: ignore
from fastapi import Request  # type: ignore
from app.config import get_settings

settings = get_settings()
from app.utils.redis_client import redis_client
import limits.aio.storage  # type: ignore
import logging

logger = logging.getLogger(__name__)

# Настройка для использования redis-py вместо coredis (для async Redis)
limits.aio.storage.RedisStorage.implementation = "redispy"

def get_storage_uri():
    """Get storage URI based on configuration"""
    if settings.rate_limit_storage == "redis" and settings.rate_limit_enabled:
        # Check if Redis is available
        if redis_client.is_connected():
            logger.info("Using Redis for rate limiting")
            return f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
        else:
            logger.warning("Redis not available, falling back to memory storage")
            return "memory://"
    else:
        logger.info("Using memory storage for rate limiting")
        return "memory://"

# Limiter с dynamic storage URI
limiter = Limiter(
    key_func=get_remote_address,  # Или custom по user_id
    storage_uri=get_storage_uri()
)

def get_limiter() -> Limiter:
    """Get limiter instance with current storage configuration"""
    # Check if we need to update storage configuration
    current_storage = get_storage_uri()
    
    # Only update if storage URI changed or not set
    if not hasattr(limiter, '_storage_uri'):
        limiter._storage_uri = current_storage
        logger.info(f"Rate limiter storage initialized to: {current_storage}")
    elif limiter._storage_uri != current_storage:
        limiter._storage_uri = current_storage
        logger.info(f"Rate limiter storage updated to: {current_storage}")
    
    return limiter