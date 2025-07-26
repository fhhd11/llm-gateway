import litellm  # type: ignore
from app.config import get_settings
from app.monitoring.callbacks import track_cost_callback, start_llm_tracking, end_llm_tracking
import os
import time
import logging
from typing import List, Dict, Any, Optional
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential, 
    retry_if_exception_type,
    before_sleep_log,
    after_log
)
from pybreaker import CircuitBreaker, CircuitBreakerError
import httpx

logger = logging.getLogger(__name__)

# Setup LiteLLM
litellm.success_callback = [track_cost_callback]  # From monitoring

# Get settings instance
settings = get_settings()

# Set the correct env var for Gemini AI Studio
if settings.google_gemini_api_key:
    os.environ["GEMINI_API_KEY"] = settings.google_gemini_api_key

# Circuit breaker instances for different models
circuit_breakers: Dict[str, CircuitBreaker] = {}

def get_circuit_breaker(model: str) -> CircuitBreaker:
    """Get or create circuit breaker for specific model"""
    if model not in circuit_breakers:
        circuit_breakers[model] = CircuitBreaker(
            fail_max=settings.circuit_breaker_failure_threshold,
            reset_timeout=settings.circuit_breaker_recovery_timeout,
            exclude=[Exception]
        )
    return circuit_breakers[model]

# Retry decorator configuration
def get_retry_decorator():
    """Get retry decorator with configuration from settings"""
    return retry(
        stop=stop_after_attempt(settings.retry_max_attempts),
        wait=wait_exponential(
            multiplier=settings.retry_base_delay,
            max=settings.retry_max_delay,
            exp_base=settings.retry_exponential_base
        ),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException, Exception)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO)
    )

# Example fallback router (configure as needed)
router = litellm.Router(
    model_list=[
        {
            "model_name": "gpt-3.5-turbo", 
            "litellm_params": {
                "model": "openai/gpt-3.5-turbo",
                "api_key": settings.openai_api_key
            }
        },
        {
            "model_name": "gpt-4", 
            "litellm_params": {
                "model": "openai/gpt-4",
                "api_key": settings.openai_api_key
            }
        },
        {
            "model_name": "claude-3", 
            "litellm_params": {
                "model": "anthropic/claude-3-sonnet",
                "api_key": settings.anthropic_api_key
            }
        },
        {
            "model_name": "gemini-1.5-pro",
            "litellm_params": {
                "model": "gemini/gemini-1.5-pro",
                "api_key": settings.google_gemini_api_key
            }
        },
    ],
    set_verbose=True
)

async def _call_llm_internal(model: str, messages: list, stream: bool = False, user_id: str = "unknown"):
    """Internal function for LLM call without retry logic"""
    start_time = time.time()
    request_id = None
    
    try:
        # Start monitoring tracking
        request_id = start_llm_tracking(model, messages, user_id, stream)
        
        # Add monitoring data to kwargs for callback
        kwargs = {
            "user_id": user_id,
            "request_id": request_id
        }
        
        response = await router.acompletion(
            model=model, 
            messages=messages, 
            stream=stream,
            **kwargs
        )
        
        processing_time = time.time() - start_time
        logger.info(f"LLM call successful for model {model} in {processing_time:.2f}s")
        
        return response
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"LLM call failed for model {model} after {processing_time:.2f}s: {e}")
        
        # End monitoring tracking with error
        if request_id:
            end_llm_tracking(
                request_id=request_id,
                success=False,
                error_message=str(e)
            )
        
        raise

@get_retry_decorator()
async def _call_llm_with_retry(model: str, messages: list, stream: bool = False, user_id: str = "unknown"):
    """Call LLM with retry mechanism using tenacity"""
    return await _call_llm_internal(model, messages, stream, user_id)

async def call_llm(model: str, messages: list, stream: bool = False, user_id: str = "unknown"):
    """Call LLM with retry mechanism and circuit breaker"""
    
    # For now, simplify and just use the internal function directly
    # TODO: Re-enable circuit breaker and retry logic after fixing async issues
    return await _call_llm_internal(model, messages, stream, user_id)

def get_supported_models() -> List[Dict[str, Any]]:
    """
    Возвращает список поддерживаемых моделей в формате, совместимом с OpenAI API.
    """
    current_time = int(time.time())
    
    models = [
        {
            "id": "gpt-3.5-turbo",
            "object": "model",
            "created": current_time,
            "owned_by": "openai",
            "permission": [
                {
                    "id": "modelperm-0",
                    "object": "model_permission",
                    "created": current_time,
                    "allow_create_engine": False,
                    "allow_sampling": True,
                    "allow_logprobs": True,
                    "allow_search_indices": False,
                    "allow_view": True,
                    "allow_fine_tuning": False,
                    "organization": "*",
                    "group": None,
                    "is_blocking": False
                }
            ],
            "root": "gpt-3.5-turbo",
            "parent": None
        },
        {
            "id": "gpt-4",
            "object": "model",
            "created": current_time,
            "owned_by": "openai",
            "permission": [
                {
                    "id": "modelperm-1",
                    "object": "model_permission",
                    "created": current_time,
                    "allow_create_engine": False,
                    "allow_sampling": True,
                    "allow_logprobs": True,
                    "allow_search_indices": False,
                    "allow_view": True,
                    "allow_fine_tuning": False,
                    "organization": "*",
                    "group": None,
                    "is_blocking": False
                }
            ],
            "root": "gpt-4",
            "parent": None
        },
        {
            "id": "claude-3",
            "object": "model",
            "created": current_time,
            "owned_by": "anthropic",
            "permission": [
                {
                    "id": "modelperm-2",
                    "object": "model_permission",
                    "created": current_time,
                    "allow_create_engine": False,
                    "allow_sampling": True,
                    "allow_logprobs": True,
                    "allow_search_indices": False,
                    "allow_view": True,
                    "allow_fine_tuning": False,
                    "organization": "*",
                    "group": None,
                    "is_blocking": False
                }
            ],
            "root": "claude-3",
            "parent": None
        },
        {
            "id": "gemini-1.5-pro",
            "object": "model",
            "created": current_time,
            "owned_by": "google",
            "permission": [
                {
                    "id": "modelperm-3",
                    "object": "model_permission",
                    "created": current_time,
                    "allow_create_engine": False,
                    "allow_sampling": True,
                    "allow_logprobs": True,
                    "allow_search_indices": False,
                    "allow_view": True,
                    "allow_fine_tuning": False,
                    "organization": "*",
                    "group": None,
                    "is_blocking": False
                }
            ],
            "root": "gemini-1.5-pro",
            "parent": None
        }
    ]
    
    return models

def get_circuit_breaker_status() -> Dict[str, Dict[str, Any]]:
    """Get status of all circuit breakers"""
    return {
        model: {
            "state": cb.current_state,
            "failure_count": cb.fail_counter,
            "last_failure_time": cb.last_failure_time,
            "failure_threshold": cb.fail_max,
            "recovery_timeout": cb.reset_timeout
        }
        for model, cb in circuit_breakers.items()
    }

async def health_check_llm_services() -> Dict[str, Any]:
    """Health check for LLM services"""
    health_status = {
        "overall": "healthy",
        "services": {},
        "circuit_breakers": get_circuit_breaker_status()
    }
    
    # Test each model with a simple request
    test_messages = [{"role": "user", "content": "Hello"}]
    
    for model in ["gpt-3.5-turbo", "claude-3", "gemini-1.5-pro"]:
        try:
            # Quick test call
            await call_llm(model, test_messages, stream=False, user_id="health-check")
            health_status["services"][model] = "healthy"
        except Exception as e:
            health_status["services"][model] = f"unhealthy: {str(e)}"
            health_status["overall"] = "degraded"
    
    return health_status