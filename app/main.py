import time
import os
from fastapi import FastAPI  # type: ignore
from app.routers import api
from app.middleware.rate_limit import limiter, get_limiter
from slowapi.errors import RateLimitExceeded  # type: ignore
from app.utils.logging import logger
from app.utils.redis_client import redis_client
from app.services.litellm_service import get_circuit_breaker_status
from app.monitoring.callbacks import get_monitoring_health
from app.monitoring.prometheus_metrics import prometheus_metrics
from app.health import health_checker
from slowapi.middleware import SlowAPIMiddleware  # type: ignore
from fastapi.responses import JSONResponse, Response  # type: ignore
from app.config import get_settings
from app.db.async_postgres_client import get_async_postgres_client, close_async_postgres_client

# Initialize Sentry for error tracking
try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    
    # Only initialize Sentry if DSN is provided
    sentry_dsn = os.getenv("SENTRY_DSN")
    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[
                FastApiIntegration(),
                RedisIntegration(),
                SqlalchemyIntegration(),
            ],
            traces_sample_rate=0.1,  # Sample 10% of transactions
            profiles_sample_rate=0.1,  # Sample 10% of profiles
            environment=os.getenv("ENVIRONMENT", "development"),
            release=os.getenv("APP_VERSION", "1.0.0"),
        )
        logger.info("Sentry initialized successfully")
    else:
        logger.info("Sentry DSN not provided, skipping Sentry initialization")
except ImportError:
    logger.warning("Sentry SDK not installed, skipping Sentry initialization")

settings = get_settings()

app = FastAPI()

app.state.limiter = limiter
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse(content={"detail": "Rate limit exceeded"}, status_code=429)

app.include_router(api.router)

@app.on_event("startup")
async def startup():
    logger.info("Application startup complete.")
    
    # Initialize Redis connection
    if settings.rate_limit_storage == "redis":
        try:
            if redis_client.is_connected():
                logger.info("Redis connected successfully")
            else:
                logger.warning("Redis connection failed, using memory storage")
        except Exception as e:
            logger.error(f"Redis initialization error: {e}")
    
    # Initialize PostgreSQL connection
    try:
        db_client = await get_async_postgres_client()
        # Check if the pool was actually created
        if db_client._pool is not None:
            logger.info("PostgreSQL connection pool initialized successfully")
        else:
            logger.warning("PostgreSQL connection pool initialization failed, using fallback mode")
    except Exception as e:
        logger.error(f"PostgreSQL initialization error: {e}")
        logger.warning("Application will continue with database fallback mode")

@app.on_event("shutdown")
async def shutdown():
    """Graceful shutdown with proper cleanup"""
    logger.info("Starting graceful shutdown...")
    
    try:
        # Close Redis connection
        logger.info("Closing Redis connection...")
        redis_client.close()
        logger.info("Redis connection closed successfully")
    except Exception as e:
        logger.error(f"Error closing Redis connection: {e}")
    
    try:
        # Close PostgreSQL connection
        logger.info("Closing PostgreSQL connection pool...")
        await close_async_postgres_client()
        logger.info("PostgreSQL connection pool closed successfully")
    except Exception as e:
        logger.error(f"Error closing PostgreSQL connection: {e}")
    
    # Close any other resources if needed
    try:
        # Close any background tasks or workers
        logger.info("Cleaning up background resources...")
        # Add any additional cleanup here
    except Exception as e:
        logger.error(f"Error during background cleanup: {e}")
    
    logger.info("Graceful shutdown completed")

app.add_middleware(SlowAPIMiddleware)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    try:
        health_data = await health_checker.run_all_health_checks()
        
        # Add legacy fields for backward compatibility
        health_data["rate_limit_storage"] = get_limiter()._storage_uri if hasattr(get_limiter(), '_storage_uri') else "unknown"
        health_data["retry_enabled"] = settings.retry_enabled
        health_data["circuit_breaker_enabled"] = settings.circuit_breaker_enabled
        
        return health_data
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }

# Circuit breaker status endpoint
@app.get("/health/circuit-breakers")
async def circuit_breaker_status():
    """Get status of all circuit breakers"""
    return {
        "circuit_breakers": get_circuit_breaker_status(),
        "retry_config": {
            "enabled": settings.retry_enabled,
            "max_attempts": settings.retry_max_attempts,
            "base_delay": settings.retry_base_delay,
            "max_delay": settings.retry_max_delay,
            "exponential_base": settings.retry_exponential_base,
            "jitter": settings.retry_jitter
        },
        "circuit_breaker_config": {
            "enabled": settings.circuit_breaker_enabled,
            "failure_threshold": settings.circuit_breaker_failure_threshold,
            "recovery_timeout": settings.circuit_breaker_recovery_timeout
        }
    }

# Prometheus metrics endpoint
@app.get("/metrics")
async def get_prometheus_metrics():
    """Prometheus metrics endpoint"""
    try:
        metrics = prometheus_metrics.get_metrics()
        return Response(
            content=metrics,
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )
    except Exception as e:
        logger.error(f"Error generating Prometheus metrics: {e}")
        return Response(
            content="# Error generating metrics\n",
            media_type="text/plain; version=0.0.4; charset=utf-8",
            status_code=500
        )

# Readiness probe endpoint
@app.get("/ready")
async def readiness_probe():
    """Readiness probe - check if service is ready to handle requests"""
    try:
        readiness_data = await health_checker.readiness_check()
        return readiness_data
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            "ready": False,
            "error": str(e),
            "timestamp": time.time()
        }

# Detailed health check endpoint
@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with individual component status"""
    try:
        health_data = await health_checker.run_all_health_checks()
        return health_data
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }

# Monitoring health endpoint
@app.get("/health/monitoring")
async def monitoring_health():
    """Detailed monitoring health check"""
    return get_monitoring_health()

# System resources health endpoint
@app.get("/health/system")
async def system_health():
    """System resources health check"""
    try:
        result = await health_checker.check_system_resources()
        return {
            "status": result.status.value,
            "message": result.message,
            "details": result.details,
            "timestamp": result.timestamp,
            "duration_ms": round(result.duration * 1000, 2)
        }
    except Exception as e:
        logger.error(f"System health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }

# Health check history endpoint
@app.get("/health/history")
async def health_history():
    """Get health check history"""
    try:
        history = health_checker.health_history[-10:]  # Last 10 checks
        return {
            "history": [
                {
                    "name": result.name,
                    "status": result.status.value,
                    "message": result.message,
                    "timestamp": result.timestamp,
                    "duration_ms": round(result.duration * 1000, 2)
                }
                for result in history
            ],
            "total_checks": len(health_checker.health_history)
        }
    except Exception as e:
        logger.error(f"Health history check failed: {e}")
        return {
            "error": str(e),
            "timestamp": time.time()
        }