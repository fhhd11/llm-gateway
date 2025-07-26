import time
import logging
from typing import Dict, Any, Optional
from prometheus_client import (
    Counter, 
    Histogram, 
    Gauge, 
    Summary,
    generate_latest,
    CONTENT_TYPE_LATEST
)
from prometheus_client.core import CollectorRegistry

logger = logging.getLogger(__name__)

class PrometheusMetrics:
    """Класс для управления Prometheus метриками"""
    
    def __init__(self):
        # Создаем отдельный registry для изоляции метрик
        self.registry = CollectorRegistry()
        
        # Counters
        self.llm_requests_total = Counter(
            'llm_requests_total',
            'Total number of LLM requests',
            ['model', 'status', 'user_id'],
            registry=self.registry
        )
        
        self.llm_tokens_total = Counter(
            'llm_tokens_total',
            'Total number of tokens processed',
            ['model', 'token_type', 'user_id'],
            registry=self.registry
        )
        
        self.llm_cost_total = Counter(
            'llm_cost_total',
            'Total cost of LLM requests',
            ['model', 'user_id'],
            registry=self.registry
        )
        
        self.api_requests_total = Counter(
            'api_requests_total',
            'Total number of API requests',
            ['endpoint', 'method', 'status_code'],
            registry=self.registry
        )
        
        self.rate_limit_exceeded_total = Counter(
            'rate_limit_exceeded_total',
            'Total number of rate limit violations',
            ['endpoint', 'user_id'],
            registry=self.registry
        )
        
        self.circuit_breaker_opens_total = Counter(
            'circuit_breaker_opens_total',
            'Total number of circuit breaker opens',
            ['model'],
            registry=self.registry
        )
        
        # Histograms
        self.llm_request_duration_seconds = Histogram(
            'llm_request_duration_seconds',
            'Duration of LLM requests',
            ['model', 'status'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
            registry=self.registry
        )
        
        self.api_request_duration_seconds = Histogram(
            'api_request_duration_seconds',
            'Duration of API requests',
            ['endpoint', 'method'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
            registry=self.registry
        )
        
        # Gauges
        self.active_requests = Gauge(
            'active_requests',
            'Number of active requests',
            ['endpoint'],
            registry=self.registry
        )
        
        self.circuit_breaker_state = Gauge(
            'circuit_breaker_state',
            'Circuit breaker state (0=closed, 1=half_open, 2=open)',
            ['model'],
            registry=self.registry
        )
        
        self.user_balance = Gauge(
            'user_balance',
            'Current user balance',
            ['user_id'],
            registry=self.registry
        )
        
        # Summaries
        self.llm_response_size_bytes = Summary(
            'llm_response_size_bytes',
            'Size of LLM responses in bytes',
            ['model'],
            registry=self.registry
        )
    
    def record_llm_request(
        self,
        model: str,
        status: str,
        user_id: str,
        duration: float,
        tokens: Optional[Dict[str, int]] = None,
        cost: Optional[float] = None,
        response_size: Optional[int] = None
    ):
        """Записывает метрики для LLM запроса"""
        try:
            # Increment request counter
            self.llm_requests_total.labels(
                model=model,
                status=status,
                user_id=user_id
            ).inc()
            
            # Record duration
            self.llm_request_duration_seconds.labels(
                model=model,
                status=status
            ).observe(duration)
            
            # Record tokens if available
            if tokens:
                for token_type, count in tokens.items():
                    if count > 0:
                        self.llm_tokens_total.labels(
                            model=model,
                            token_type=token_type,
                            user_id=user_id
                        ).inc(count)
            
            # Record cost if available
            if cost and cost > 0:
                self.llm_cost_total.labels(
                    model=model,
                    user_id=user_id
                ).inc(cost)
            
            # Record response size if available
            if response_size:
                self.llm_response_size_bytes.labels(model=model).observe(response_size)
                
        except Exception as e:
            logger.error(f"Failed to record LLM metrics: {e}")
    
    def record_api_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        duration: float
    ):
        """Записывает метрики для API запроса"""
        try:
            # Increment request counter
            self.api_requests_total.labels(
                endpoint=endpoint,
                method=method,
                status_code=str(status_code)
            ).inc()
            
            # Record duration
            self.api_request_duration_seconds.labels(
                endpoint=endpoint,
                method=method
            ).observe(duration)
            
        except Exception as e:
            logger.error(f"Failed to record API metrics: {e}")
    
    def record_rate_limit_exceeded(self, endpoint: str, user_id: str):
        """Записывает метрику превышения rate limit"""
        try:
            self.rate_limit_exceeded_total.labels(
                endpoint=endpoint,
                user_id=user_id
            ).inc()
        except Exception as e:
            logger.error(f"Failed to record rate limit metrics: {e}")
    
    def record_circuit_breaker_open(self, model: str):
        """Записывает метрику открытия circuit breaker"""
        try:
            self.circuit_breaker_opens_total.labels(model=model).inc()
        except Exception as e:
            logger.error(f"Failed to record circuit breaker metrics: {e}")
    
    def update_circuit_breaker_state(self, model: str, state: str):
        """Обновляет состояние circuit breaker"""
        try:
            state_value = {
                "closed": 0,
                "half_open": 1,
                "open": 2
            }.get(state, 0)
            
            self.circuit_breaker_state.labels(model=model).set(state_value)
        except Exception as e:
            logger.error(f"Failed to update circuit breaker state: {e}")
    
    def update_user_balance(self, user_id: str, balance: float):
        """Обновляет баланс пользователя"""
        try:
            self.user_balance.labels(user_id=user_id).set(balance)
        except Exception as e:
            logger.error(f"Failed to update user balance: {e}")
    
    def increment_active_requests(self, endpoint: str):
        """Увеличивает счетчик активных запросов"""
        try:
            self.active_requests.labels(endpoint=endpoint).inc()
        except Exception as e:
            logger.error(f"Failed to increment active requests: {e}")
    
    def decrement_active_requests(self, endpoint: str):
        """Уменьшает счетчик активных запросов"""
        try:
            self.active_requests.labels(endpoint=endpoint).dec()
        except Exception as e:
            logger.error(f"Failed to decrement active requests: {e}")
    
    def get_metrics(self) -> bytes:
        """Возвращает метрики в формате Prometheus"""
        try:
            return generate_latest(self.registry)
        except Exception as e:
            logger.error(f"Failed to generate metrics: {e}")
            return b""
    
    def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья метрик"""
        try:
            # Проверяем, что можем генерировать метрики
            metrics = self.get_metrics()
            return {
                "status": "healthy",
                "metrics_size": len(metrics),
                "registry_size": len(self.registry._collector_to_names)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

# Global metrics instance
prometheus_metrics = PrometheusMetrics() 