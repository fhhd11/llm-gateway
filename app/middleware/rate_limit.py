from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request
from app.config import settings
import limits.aio.storage  # Для настройки implementation

# Настройка для использования redis-py вместо coredis (для async Redis)
limits.aio.storage.RedisStorage.implementation = "redispy"

# Limiter с async storage URI (префикс "async+" для async mode)
limiter = Limiter(
    key_func=get_remote_address,  # Или custom по user_id
    storage_uri="async+" + settings.redis_url  # Например, "async+redis://localhost:6379"
)