import asyncio
import time
import logging
from typing import Callable, Any, Optional, TypeVar, Union
from functools import wraps
from enum import Enum
import random

logger = logging.getLogger(__name__)

T = TypeVar('T')

class CircuitState(Enum):
    """Состояния circuit breaker"""
    CLOSED = "closed"      # Нормальная работа
    OPEN = "open"          # Блокировка запросов
    HALF_OPEN = "half_open"  # Тестовые запросы

class CircuitBreaker:
    """Circuit Breaker для защиты от каскадных сбоев"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = CircuitState.CLOSED
    
    def can_execute(self) -> bool:
        """Проверяет, можно ли выполнить запрос"""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                logger.info(f"Circuit breaker transitioning to HALF_OPEN state")
                return True
            return False
        
        # HALF_OPEN state
        return True
    
    def on_success(self):
        """Обработка успешного запроса"""
        # Успешный запрос всегда закрывает circuit breaker из любого состояния
        if self.state != CircuitState.CLOSED:
            logger.info(f"Circuit breaker transitioning to CLOSED state after success")
            self.state = CircuitState.CLOSED
        
        self.failure_count = 0
    
    def on_failure(self):
        """Обработка неудачного запроса"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
    
    def get_state(self) -> dict:
        """Возвращает текущее состояние circuit breaker"""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout
        }

class RetryConfig:
    """Конфигурация для retry механизма"""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retry_exceptions: tuple = (Exception,)
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retry_exceptions = retry_exceptions

def calculate_delay(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True
) -> float:
    """Вычисляет задержку для retry с exponential backoff"""
    delay = min(base_delay * (exponential_base ** attempt), max_delay)
    
    if jitter:
        # Добавляем случайность для предотвращения thundering herd
        delay = delay * (0.5 + random.random() * 0.5)
    
    return delay

def retry_with_exponential_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_exceptions: tuple = (Exception,)
):
    """Декоратор для retry с exponential backoff"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    if asyncio.iscoroutinefunction(func):
                        result = await func(*args, **kwargs)
                    else:
                        result = func(*args, **kwargs)
                    
                    if attempt > 0:
                        logger.info(f"Function {func.__name__} succeeded after {attempt} retries")
                    
                    return result
                    
                except retry_exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        logger.error(f"Function {func.__name__} failed after {max_attempts} attempts: {e}")
                        raise
                    
                    delay = calculate_delay(
                        attempt,
                        base_delay,
                        max_delay,
                        exponential_base,
                        jitter
                    )
                    
                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt + 1}/{max_attempts}): {e}. "
                        f"Retrying in {delay:.2f}s"
                    )
                    
                    await asyncio.sleep(delay)
            
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    result = func(*args, **kwargs)
                    
                    if attempt > 0:
                        logger.info(f"Function {func.__name__} succeeded after {attempt} retries")
                    
                    return result
                    
                except retry_exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        logger.error(f"Function {func.__name__} failed after {max_attempts} attempts: {e}")
                        raise
                    
                    delay = calculate_delay(
                        attempt,
                        base_delay,
                        max_delay,
                        exponential_base,
                        jitter
                    )
                    
                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt + 1}/{max_attempts}): {e}. "
                        f"Retrying in {delay:.2f}s"
                    )
                    
                    time.sleep(delay)
            
            raise last_exception
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

async def async_retry(
    func: Callable[..., Any],
    *args,
    config: Optional[RetryConfig] = None,
    circuit_breaker: Optional[CircuitBreaker] = None,
    **kwargs
) -> Any:
    """Выполняет функцию с retry механизмом"""
    
    if config is None:
        config = RetryConfig()
    
    last_exception = None
    
    for attempt in range(config.max_retries + 1):
        try:
            # Проверяем circuit breaker
            if circuit_breaker and not circuit_breaker.can_execute():
                raise Exception("Circuit breaker is open")
            
            # Выполняем функцию
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Успешное выполнение
            if circuit_breaker:
                circuit_breaker.on_success()
            
            if attempt > 0:
                logger.info(f"Function succeeded after {attempt} retries")
            
            return result
            
        except Exception as e:
            last_exception = e
            
            # Проверяем, нужно ли retry
            if not isinstance(e, config.retry_exceptions):
                logger.error(f"Non-retryable exception: {e}")
                raise
            
            # Обновляем circuit breaker
            if circuit_breaker:
                circuit_breaker.on_failure()
            
            # Последняя попытка
            if attempt == config.max_retries:
                logger.error(f"Function failed after {config.max_retries} retries: {e}")
                raise
            
            # Вычисляем задержку
            delay = calculate_delay(
                attempt,
                config.base_delay,
                config.max_delay,
                config.exponential_base,
                config.jitter
            )
            
            logger.warning(
                f"Function failed (attempt {attempt + 1}/{config.max_retries + 1}): {e}. "
                f"Retrying in {delay:.2f}s"
            )
            
            await asyncio.sleep(delay)
    
    # Не должно дойти до этой точки
    raise last_exception

def retry(
    config: Optional[RetryConfig] = None,
    circuit_breaker: Optional[CircuitBreaker] = None
):
    """Декоратор для добавления retry функциональности"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            return await async_retry(func, *args, config=config, circuit_breaker=circuit_breaker, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            return asyncio.run(async_retry(func, *args, config=config, circuit_breaker=circuit_breaker, **kwargs))
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator 