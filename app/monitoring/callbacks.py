import time
import logging
import uuid
from typing import Dict, Any, Optional
from app.monitoring.langfuse_client import langfuse_client
from app.monitoring.prometheus_metrics import prometheus_metrics

logger = logging.getLogger(__name__)

# Global storage for tracking requests
request_tracking: Dict[str, Dict[str, Any]] = {}

def track_cost_callback(
    kwargs: Dict[str, Any],
    completion_response: Any,
    start_time: float,
    end_time: float
):
    """
    Callback для отслеживания стоимости LLM запросов.
    Интегрирован с Langfuse и Prometheus.
    """
    try:
        # Извлекаем данные из kwargs
        model = kwargs.get("model", "unknown")
        messages = kwargs.get("messages", [])
        user_id = kwargs.get("user_id", "unknown")
        request_id = kwargs.get("request_id", str(uuid.uuid4()))
        
        # Вычисляем duration
        duration = end_time - start_time
        
        # Извлекаем usage из response
        usage = None
        cost = None
        status = "success"
        error_message = None
        
        if hasattr(completion_response, 'usage') and completion_response.usage:
            usage = {
                "prompt_tokens": getattr(completion_response.usage, 'prompt_tokens', 0),
                "completion_tokens": getattr(completion_response.usage, 'completion_tokens', 0),
                "total_tokens": getattr(completion_response.usage, 'total_tokens', 0)
            }
        
        # Вычисляем примерную стоимость (можно уточнить)
        if usage and usage.get("total_tokens"):
            # Примерные цены (можно вынести в конфиг)
            base_prices = {
                "gpt-4": 0.00003,
                "claude-3": 0.000015,
                "gemini-1.5-pro": 0.0000125
            }
            price_per_token = base_prices.get(model, 0.00002)
            cost = usage["total_tokens"] * price_per_token
        
        # Записываем метрики в Prometheus
        prometheus_metrics.record_llm_request(
            model=model,
            status=status,
            user_id=user_id,
            duration=duration,
            tokens=usage,
            cost=cost
        )
        
        # Завершаем отслеживание в Langfuse
        if request_id in request_tracking:
            generation_id = request_tracking[request_id].get("generation_id")
            if generation_id:
                langfuse_client.end_generation(
                    generation_id=generation_id,
                    output=str(completion_response) if completion_response else None,
                    usage=usage,
                    cost=cost
                )
            
            # Очищаем tracking
            del request_tracking[request_id]
        
        logger.info(
            f"LLM request completed - Model: {model}, Duration: {duration:.2f}s, "
            f"Tokens: {usage.get('total_tokens', 0) if usage else 0}, Cost: ${cost:.6f if cost else 0.0}"
        )
        
    except Exception as e:
        logger.error(f"Error in track_cost_callback: {e}")
        
        # Записываем ошибку в метрики
        try:
            model = kwargs.get("model", "unknown")
            user_id = kwargs.get("user_id", "unknown")
            duration = end_time - start_time
            
            prometheus_metrics.record_llm_request(
                model=model,
                status="error",
                user_id=user_id,
                duration=duration,
                error_message=str(e)
            )
            
            # Завершаем с ошибкой в Langfuse
            request_id = kwargs.get("request_id")
            if request_id and request_id in request_tracking:
                generation_id = request_tracking[request_id].get("generation_id")
                if generation_id:
                    langfuse_client.end_generation(
                        generation_id=generation_id,
                        error=str(e)
                    )
                del request_tracking[request_id]
                
        except Exception as metric_error:
            logger.error(f"Error recording error metrics: {metric_error}")

def start_llm_tracking(
    model: str,
    messages: list,
    user_id: str,
    stream: bool = False
) -> str:
    """
    Начинает отслеживание LLM запроса.
    Возвращает request_id для последующего использования.
    """
    try:
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Начинаем отслеживание в Langfuse
        generation_id = langfuse_client.start_generation(
            request_id=request_id,
            model=model,
            messages=messages,
            user_id=user_id,
            stream=stream
        )
        
        # Сохраняем информацию для tracking
        request_tracking[request_id] = {
            "generation_id": generation_id,
            "start_time": start_time,
            "model": model,
            "user_id": user_id,
            "stream": stream
        }
        
        # Увеличиваем счетчик активных запросов
        prometheus_metrics.increment_active_requests("llm")
        
        logger.info(f"Started LLM tracking - Request ID: {request_id}, Model: {model}")
        
        return request_id
        
    except Exception as e:
        logger.error(f"Error starting LLM tracking: {e}")
        return str(uuid.uuid4())  # Fallback ID

def end_llm_tracking(
    request_id: str,
    success: bool = True,
    error_message: Optional[str] = None,
    usage: Optional[Dict[str, int]] = None,
    cost: Optional[float] = None
):
    """
    Завершает отслеживание LLM запроса.
    """
    try:
        if request_id not in request_tracking:
            logger.warning(f"Request ID {request_id} not found in tracking")
            return
        
        tracking_info = request_tracking[request_id]
        end_time = time.time()
        duration = end_time - tracking_info["start_time"]
        
        # Уменьшаем счетчик активных запросов
        prometheus_metrics.decrement_active_requests("llm")
        
        # Завершаем в Langfuse
        generation_id = tracking_info.get("generation_id")
        if generation_id:
            langfuse_client.end_generation(
                generation_id=generation_id,
                usage=usage,
                cost=cost,
                error=error_message if not success else None
            )
        
        # Очищаем tracking
        del request_tracking[request_id]
        
        logger.info(f"Ended LLM tracking - Request ID: {request_id}, Duration: {duration:.2f}s")
        
    except Exception as e:
        logger.error(f"Error ending LLM tracking: {e}")

def track_api_request(
    endpoint: str,
    method: str,
    status_code: int,
    duration: float,
    user_id: Optional[str] = None
):
    """
    Отслеживает API запросы.
    """
    try:
        # Записываем метрики
        prometheus_metrics.record_api_request(
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            duration=duration
        )
        
        # Логируем запрос
        logger.info(
            f"API request - {method} {endpoint}, Status: {status_code}, "
            f"Duration: {duration:.3f}s, User: {user_id or 'anonymous'}"
        )
        
    except Exception as e:
        logger.error(f"Error tracking API request: {e}")

def track_rate_limit_exceeded(endpoint: str, user_id: str):
    """
    Отслеживает превышение rate limit.
    """
    try:
        prometheus_metrics.record_rate_limit_exceeded(endpoint, user_id)
        logger.warning(f"Rate limit exceeded - Endpoint: {endpoint}, User: {user_id}")
    except Exception as e:
        logger.error(f"Error tracking rate limit: {e}")

def track_circuit_breaker_open(model: str):
    """
    Отслеживает открытие circuit breaker.
    """
    try:
        prometheus_metrics.record_circuit_breaker_open(model)
        logger.warning(f"Circuit breaker opened - Model: {model}")
    except Exception as e:
        logger.error(f"Error tracking circuit breaker: {e}")

def update_circuit_breaker_state(model: str, state: str):
    """
    Обновляет состояние circuit breaker в метриках.
    """
    try:
        prometheus_metrics.update_circuit_breaker_state(model, state)
    except Exception as e:
        logger.error(f"Error updating circuit breaker state: {e}")

def update_user_balance(user_id: str, balance: float):
    """
    Обновляет баланс пользователя в метриках.
    """
    try:
        prometheus_metrics.update_user_balance(user_id, balance)
    except Exception as e:
        logger.error(f"Error updating user balance: {e}")

def get_monitoring_health() -> Dict[str, Any]:
    """
    Возвращает статус здоровья всех monitoring компонентов.
    """
    return {
        "langfuse": langfuse_client.health_check(),
        "prometheus": prometheus_metrics.health_check(),
        "active_requests": len(request_tracking)
    }