import redis
from app.config import get_settings

settings = get_settings()
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class RedisClient:
    """Redis client wrapper with connection management and health checks"""
    
    def __init__(self):
        self._client: Optional[redis.Redis] = None
        self._connected = False
    
    def get_client(self) -> redis.Redis:
        """Get Redis client instance, creating it if necessary"""
        if self._client is None:
            try:
                self._client = redis.Redis(
                    host=settings.redis.host,
                    port=settings.redis.port,
                    db=settings.redis.db,
                    password=settings.redis.password,
                    ssl=settings.redis.use_ssl,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
                logger.info(f"Redis client initialized for {settings.redis.host}:{settings.redis.port}")
            except Exception as e:
                logger.error(f"Failed to initialize Redis client: {e}")
                raise
        
        return self._client
    
    def is_connected(self) -> bool:
        """Check if Redis is connected and responding"""
        try:
            client = self.get_client()
            client.ping()
            self._connected = True
            return True
        except Exception as e:
            logger.warning(f"Redis connection check failed: {e}")
            self._connected = False
            return False
    
    def health_check(self) -> dict:
        """Perform comprehensive health check"""
        try:
            client = self.get_client()
            client.ping()
            
            # Test basic operations
            test_key = "health_check_test"
            client.set(test_key, "test_value", ex=10)
            value = client.get(test_key)
            client.delete(test_key)
            
            if value != "test_value":
                raise Exception("Redis read/write test failed")
            
            return {
                "status": "healthy",
                "connected": True,
                "host": settings.redis.host,
                "port": settings.redis.port
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e),
                "host": settings.redis.host,
                "port": settings.redis.port
            }
    
    def close(self):
        """Close Redis connection"""
        if self._client:
            try:
                self._client.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")
            finally:
                self._client = None
                self._connected = False

# Global Redis client instance
redis_client = RedisClient() 