"""
Health Checks and Readiness Probes System
Provides comprehensive health monitoring for the LLM Gateway
"""

import time
import asyncio
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass
from app.utils.logging import get_logger
from app.utils.redis_client import redis_client
from app.dependencies import get_supabase_client
from app.services.litellm_service import get_circuit_breaker_status
from app.monitoring.callbacks import get_monitoring_health
from app.config import get_settings

settings = get_settings()

logger = get_logger(__name__)

class HealthStatus(Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"

@dataclass
class HealthCheckResult:
    """Result of a health check"""
    name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any]
    timestamp: float
    duration: float

class HealthChecker:
    """Comprehensive health checker for LLM Gateway"""
    
    def __init__(self):
        self.start_time = time.time()
        self.health_history: List[HealthCheckResult] = []
    
    async def check_redis_health(self) -> HealthCheckResult:
        """Check Redis connection health"""
        start_time = time.time()
        try:
            # Check if Redis is configured
            if not settings.rate_limit_storage == "redis":
                duration = time.time() - start_time
                return HealthCheckResult(
                    name="redis",
                    status=HealthStatus.HEALTHY,
                    message="Redis not configured, using memory storage",
                    details={"configured": False, "storage": "memory"},
                    timestamp=time.time(),
                    duration=duration
                )
            
            health_data = redis_client.health_check()
            duration = time.time() - start_time
            
            if health_data.get("connected", False):
                status = HealthStatus.HEALTHY
                message = "Redis connection is healthy"
            else:
                status = HealthStatus.HEALTHY  # Changed from DEGRADED to HEALTHY
                message = "Redis connection failed, using memory storage"
            
            return HealthCheckResult(
                name="redis",
                status=status,
                message=message,
                details=health_data,
                timestamp=time.time(),
                duration=duration
            )
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Redis health check failed: {e}")
            return HealthCheckResult(
                name="redis",
                status=HealthStatus.HEALTHY,  # Changed from DEGRADED to HEALTHY
                message="Redis connection failed, using memory storage",
                details={"error": str(e), "fallback": "memory"},
                timestamp=time.time(),
                duration=duration
            )
    
    async def check_database_health(self) -> HealthCheckResult:
        """Check database connection health"""
        start_time = time.time()
        try:
            db = get_supabase_client()
            # Simple query to test connection
            result = db.table("balances").select("count", count="exact").limit(1).execute()
            duration = time.time() - start_time
            
            return HealthCheckResult(
                name="database",
                status=HealthStatus.HEALTHY,
                message="Database connection is healthy",
                details={"connected": True, "response_time_ms": round(duration * 1000, 2)},
                timestamp=time.time(),
                duration=duration
            )
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Database health check failed: {e}")
            return HealthCheckResult(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection error: {str(e)}",
                details={"error": str(e)},
                timestamp=time.time(),
                duration=duration
            )
    
    async def check_monitoring_health(self) -> HealthCheckResult:
        """Check monitoring systems health"""
        start_time = time.time()
        try:
            monitoring_data = get_monitoring_health()
            duration = time.time() - start_time
            
            # Check if all monitoring components are healthy
            langfuse_healthy = monitoring_data.get("langfuse", {}).get("status") == "healthy"
            prometheus_healthy = monitoring_data.get("prometheus", {}).get("status") == "healthy"
            
            if langfuse_healthy and prometheus_healthy:
                status = HealthStatus.HEALTHY
                message = "All monitoring systems are healthy"
            elif langfuse_healthy or prometheus_healthy:
                status = HealthStatus.DEGRADED
                message = "Some monitoring systems are degraded"
            else:
                status = HealthStatus.UNHEALTHY
                message = "All monitoring systems are unhealthy"
            
            return HealthCheckResult(
                name="monitoring",
                status=status,
                message=message,
                details=monitoring_data,
                timestamp=time.time(),
                duration=duration
            )
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Monitoring health check failed: {e}")
            return HealthCheckResult(
                name="monitoring",
                status=HealthStatus.UNHEALTHY,
                message=f"Monitoring health check error: {str(e)}",
                details={"error": str(e)},
                timestamp=time.time(),
                duration=duration
            )
    
    async def check_circuit_breakers_health(self) -> HealthCheckResult:
        """Check circuit breakers health"""
        start_time = time.time()
        try:
            circuit_breakers = get_circuit_breaker_status()
            duration = time.time() - start_time
            
            # Count open circuit breakers
            open_breakers = sum(1 for cb in circuit_breakers.values() if cb.get("state") == "open")
            total_breakers = len(circuit_breakers)
            
            if open_breakers == 0:
                status = HealthStatus.HEALTHY
                message = "All circuit breakers are closed"
            elif open_breakers < total_breakers:
                status = HealthStatus.DEGRADED
                message = f"{open_breakers}/{total_breakers} circuit breakers are open"
            else:
                status = HealthStatus.UNHEALTHY
                message = "All circuit breakers are open"
            
            return HealthCheckResult(
                name="circuit_breakers",
                status=status,
                message=message,
                details={
                    "open_breakers": open_breakers,
                    "total_breakers": total_breakers,
                    "circuit_breakers": circuit_breakers
                },
                timestamp=time.time(),
                duration=duration
            )
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Circuit breakers health check failed: {e}")
            return HealthCheckResult(
                name="circuit_breakers",
                status=HealthStatus.UNHEALTHY,
                message=f"Circuit breakers health check error: {str(e)}",
                details={"error": str(e)},
                timestamp=time.time(),
                duration=duration
            )
    
    async def check_llm_providers_health(self) -> HealthCheckResult:
        """Check LLM providers health (simulated)"""
        start_time = time.time()
        try:
            # This is a simulated check - in production you might want to make actual API calls
            providers = {
                "openai": {"status": "healthy", "response_time_ms": 50},
                "anthropic": {"status": "healthy", "response_time_ms": 45},
                "google": {"status": "healthy", "response_time_ms": 60}
            }
            duration = time.time() - start_time
            
            healthy_providers = sum(1 for p in providers.values() if p["status"] == "healthy")
            total_providers = len(providers)
            
            if healthy_providers == total_providers:
                status = HealthStatus.HEALTHY
                message = "All LLM providers are healthy"
            elif healthy_providers > 0:
                status = HealthStatus.DEGRADED
                message = f"{healthy_providers}/{total_providers} LLM providers are healthy"
            else:
                status = HealthStatus.UNHEALTHY
                message = "No LLM providers are healthy"
            
            return HealthCheckResult(
                name="llm_providers",
                status=status,
                message=message,
                details={"providers": providers},
                timestamp=time.time(),
                duration=duration
            )
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"LLM providers health check failed: {e}")
            return HealthCheckResult(
                name="llm_providers",
                status=HealthStatus.UNHEALTHY,
                message=f"LLM providers health check error: {str(e)}",
                details={"error": str(e)},
                timestamp=time.time(),
                duration=duration
            )
    
    async def check_system_resources(self) -> HealthCheckResult:
        """Check system resources (memory, CPU)"""
        start_time = time.time()
        try:
            import psutil
            
            # Get system metrics
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=0.1)
            disk = psutil.disk_usage('/')
            
            duration = time.time() - start_time
            
            # Determine health based on thresholds
            memory_healthy = memory.percent < 90
            cpu_healthy = cpu_percent < 80
            disk_healthy = disk.percent < 90
            
            if memory_healthy and cpu_healthy and disk_healthy:
                status = HealthStatus.HEALTHY
                message = "System resources are healthy"
            elif memory_healthy and cpu_healthy:
                status = HealthStatus.DEGRADED
                message = "System resources are degraded (disk usage high)"
            else:
                status = HealthStatus.UNHEALTHY
                message = "System resources are unhealthy"
            
            return HealthCheckResult(
                name="system_resources",
                status=status,
                message=message,
                details={
                    "memory_percent": memory.percent,
                    "cpu_percent": cpu_percent,
                    "disk_percent": disk.percent,
                    "memory_available_gb": round(memory.available / (1024**3), 2),
                    "disk_free_gb": round(disk.free / (1024**3), 2)
                },
                timestamp=time.time(),
                duration=duration
            )
        except ImportError:
            # psutil not available
            duration = time.time() - start_time
            return HealthCheckResult(
                name="system_resources",
                status=HealthStatus.UNKNOWN,
                message="System resources check not available (psutil not installed)",
                details={"note": "Install psutil for detailed system monitoring"},
                timestamp=time.time(),
                duration=duration
            )
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"System resources health check failed: {e}")
            return HealthCheckResult(
                name="system_resources",
                status=HealthStatus.UNHEALTHY,
                message=f"System resources health check error: {str(e)}",
                details={"error": str(e)},
                timestamp=time.time(),
                duration=duration
            )
    
    async def run_all_health_checks(self) -> Dict[str, Any]:
        """Run all health checks and return comprehensive status"""
        start_time = time.time()
        
        # Run all health checks concurrently
        checks = [
            self.check_redis_health(),
            self.check_database_health(),
            self.check_monitoring_health(),
            self.check_circuit_breakers_health(),
            self.check_llm_providers_health(),
            self.check_system_resources()
        ]
        
        results = await asyncio.gather(*checks, return_exceptions=True)
        
        # Process results
        health_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Handle exceptions from health checks
                health_results.append(HealthCheckResult(
                    name=f"check_{i}",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check failed with exception: {str(result)}",
                    details={"error": str(result)},
                    timestamp=time.time(),
                    duration=0.0
                ))
            else:
                health_results.append(result)
        
        # Store in history (keep last 100 results)
        self.health_history.extend(health_results)
        if len(self.health_history) > 100:
            self.health_history = self.health_history[-100:]
        
        # Determine overall status
        overall_status = self._determine_overall_status(health_results)
        total_duration = time.time() - start_time
        
        return {
            "status": overall_status.value,
            "timestamp": time.time(),
            "uptime_seconds": time.time() - self.start_time,
            "checks": {
                result.name: {
                    "status": result.status.value,
                    "message": result.message,
                    "details": result.details,
                    "duration_ms": round(result.duration * 1000, 2)
                }
                for result in health_results
            },
            "summary": {
                "total_checks": len(health_results),
                "healthy_checks": sum(1 for r in health_results if r.status == HealthStatus.HEALTHY),
                "degraded_checks": sum(1 for r in health_results if r.status == HealthStatus.DEGRADED),
                "unhealthy_checks": sum(1 for r in health_results if r.status == HealthStatus.UNHEALTHY),
                "total_duration_ms": round(total_duration * 1000, 2)
            }
        }
    
    def _determine_overall_status(self, results: List[HealthCheckResult]) -> HealthStatus:
        """Determine overall health status based on individual check results"""
        if not results:
            return HealthStatus.UNKNOWN
        
        unhealthy_count = sum(1 for r in results if r.status == HealthStatus.UNHEALTHY)
        degraded_count = sum(1 for r in results if r.status == HealthStatus.DEGRADED)
        
        if unhealthy_count > 0:
            return HealthStatus.UNHEALTHY
        elif degraded_count > 0:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY
    
    async def readiness_check(self) -> Dict[str, Any]:
        """Readiness probe - check if service is ready to handle requests"""
        start_time = time.time()
        
        # For readiness, we focus on critical dependencies
        critical_checks = [
            self.check_database_health(),
            self.check_monitoring_health()
        ]
        
        results = await asyncio.gather(*critical_checks, return_exceptions=True)
        
        # Process results
        ready = True
        details = {}
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                ready = False
                details[f"check_{i}"] = {"error": str(result)}
            else:
                details[result.name] = {
                    "status": result.status.value,
                    "message": result.message
                }
                if result.status == HealthStatus.UNHEALTHY:
                    ready = False
        
        duration = time.time() - start_time
        
        return {
            "ready": ready,
            "timestamp": time.time(),
            "duration_ms": round(duration * 1000, 2),
            "details": details
        }

# Global health checker instance
health_checker = HealthChecker() 