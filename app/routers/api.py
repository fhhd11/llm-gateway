from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from typing import Dict, Any, Optional, List
import json
import logging
import time
import asyncio
from functools import lru_cache
from app.services.billing_service import estimate_cost, update_balance, get_balance
from app.services.litellm_service import call_llm, get_supported_models
from app.dependencies import get_current_user_async
from app.models.schemas import ChatCompletionRequest, ChatCompletionResponse, ModelInfo
from app.utils.exceptions import InsufficientFundsError, LLMServiceError
from app.utils.redis_client import redis_client
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()

# Memory cache fallback for models
_models_cache = None
_models_cache_timestamp = 0
MODELS_CACHE_TTL = 300  # 5 minutes

def get_models_from_cache():
    """Get models from memory cache with TTL"""
    global _models_cache, _models_cache_timestamp
    current_time = time.time()
    
    if (_models_cache is not None and 
        current_time - _models_cache_timestamp < MODELS_CACHE_TTL):
        return _models_cache
    
    return None

def set_models_cache(models):
    """Set models in memory cache"""
    global _models_cache, _models_cache_timestamp
    _models_cache = models
    _models_cache_timestamp = time.time()

async def get_cached_models():
    """Get models with Redis caching and memory fallback"""
    try:
        # Try Redis first
        if settings.rate_limit_storage == "redis" and redis_client.is_connected():
            cached_models = await redis_client.get("models:list")
            if cached_models:
                logger.debug("Models retrieved from Redis cache")
                return json.loads(cached_models)
    except Exception as e:
        logger.warning(f"Redis cache failed, falling back to memory: {e}")
    
    # Fallback to memory cache
    memory_cached = get_models_from_cache()
    if memory_cached:
        logger.debug("Models retrieved from memory cache")
        return memory_cached
    
    # No cache available, fetch fresh data
    logger.debug("No cache available, fetching fresh models")
    return None

async def set_cached_models(models):
    """Set models in cache (Redis + memory)"""
    try:
        # Set in Redis
        if settings.rate_limit_storage == "redis" and redis_client.is_connected():
            await redis_client.setex(
                "models:list", 
                MODELS_CACHE_TTL, 
                json.dumps(models)
            )
            logger.debug("Models cached in Redis")
    except Exception as e:
        logger.warning(f"Failed to cache models in Redis: {e}")
    
    # Always set in memory as fallback
    set_models_cache(models)
    logger.debug("Models cached in memory")

@router.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    request: ChatCompletionRequest,
    user_id: str = Depends(get_current_user_async)
):
    """
    Обрабатывает запросы на завершение чата через LiteLLM
    """
    try:
        # Оцениваем стоимость запроса
        estimated_cost = estimate_cost(request)
        
        # Проверяем баланс пользователя
        current_balance = await get_balance(user_id)
        
        if current_balance < estimated_cost:
            raise InsufficientFundsError(
                f"Insufficient funds. Required: ${estimated_cost:.4f}, Available: ${current_balance:.4f}"
            )
        
        # Вызываем LLM сервис
        llm_response = await call_llm(
            model=request.model,
            messages=[{"role": msg.role, "content": msg.content} for msg in request.messages],
            stream=False,
            user_id=user_id
        )
        
        # Вычисляем реальную стоимость
        actual_cost = estimate_cost(request, llm_response)
        
        # Обновляем баланс пользователя
        await update_balance(
            user_id, 
            -actual_cost, 
            f"Chat completion with {request.model}"
        )
        
        # Преобразуем LiteLLM ответ в правильный формат для FastAPI
        response_dict = {
            "id": llm_response.id,
            "object": llm_response.object,
            "created": llm_response.created,
            "model": llm_response.model,
            "choices": [
                {
                    "index": choice.index,
                    "message": {
                        "role": choice.message.role,
                        "content": choice.message.content,
                        "tool_calls": choice.message.tool_calls,
                        "function_call": choice.message.function_call
                    },
                    "finish_reason": choice.finish_reason
                }
                for choice in llm_response.choices
            ],
            "usage": {
                "prompt_tokens": llm_response.usage.prompt_tokens,
                "completion_tokens": llm_response.usage.completion_tokens,
                "total_tokens": llm_response.usage.total_tokens
            }
        }
        
        return response_dict
        
    except InsufficientFundsError:
        raise
    except LLMServiceError as e:
        logger.error(f"LLM service error: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in chat_completions: {e}")
        # Return a fallback response for graceful degradation
        logger.warning(f"Returning fallback response due to error: {e}")
        return {
            "id": "fallback-response",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request.model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "I'm experiencing technical difficulties. Please try again later."
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            },
            "warning": "Fallback response due to service issues"
        }

@router.post("/v1/chat/completions/stream")
async def chat_completions_stream(
    request: ChatCompletionRequest,
    user_id: str = Depends(get_current_user_async)
):
    """
    Обрабатывает потоковые запросы на завершение чата
    """
    try:
        # Оцениваем стоимость запроса
        estimated_cost = estimate_cost(request)
        
        # Проверяем баланс пользователя
        current_balance = await get_balance(user_id)
        
        if current_balance < estimated_cost:
            raise InsufficientFundsError(
                f"Insufficient funds. Required: ${estimated_cost:.4f}, Available: ${current_balance:.4f}"
            )
        
        # Создаем потоковый ответ
        async def generate_stream():
            total_cost = 0.0
            try:
                response = await call_llm(
                    model=request.model,
                    messages=[{"role": msg.role, "content": msg.content} for msg in request.messages],
                    stream=True,
                    user_id=user_id
                )
                async for chunk in response:
                    total_cost += estimate_cost(request, chunk)
                    # Convert LiteLLM object to dict for JSON serialization
                    chunk_dict = {
                        "id": getattr(chunk, 'id', None),
                        "object": getattr(chunk, 'object', 'chat.completion.chunk'),
                        "created": getattr(chunk, 'created', int(time.time())),
                        "model": getattr(chunk, 'model', request.model),
                        "choices": [
                            {
                                "index": choice.index,
                                "delta": {
                                    "role": getattr(choice.delta, 'role', 'assistant'),
                                    "content": getattr(choice.delta, 'content', ''),
                                    "function_call": getattr(choice.delta, 'function_call', None),
                                    "tool_calls": getattr(choice.delta, 'tool_calls', None)
                                },
                                "finish_reason": getattr(choice, 'finish_reason', None)
                            }
                            for choice in chunk.choices
                        ] if hasattr(chunk, 'choices') else []
                    }
                    yield f"data: {json.dumps(chunk_dict)}\n\n"
                
                # Обновляем баланс после завершения стрима
                await update_balance(
                    user_id, 
                    -total_cost, 
                    f"Streaming chat completion with {request.model}"
                )
                
            except Exception as e:
                logger.error(f"Error in streaming response: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache"}
        )
        
    except InsufficientFundsError:
        raise
    except LLMServiceError as e:
        logger.error(f"LLM service error: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in chat_completions_stream: {e}")
        # Return a fallback streaming response for graceful degradation
        logger.warning(f"Returning fallback streaming response due to error: {e}")
        
        async def fallback_stream():
            yield f"data: {json.dumps({'error': 'Service temporarily unavailable. Please try again later.'})}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            fallback_stream(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache"}
        )

@router.get("/v1/models", response_model=List[ModelInfo])
async def list_models():
    """
    Возвращает список доступных моделей с кэшированием
    """
    try:
        # Try to get from cache first
        cached_models = await get_cached_models()
        if cached_models:
            return cached_models
        
        # Fetch fresh models if not in cache
        models = get_supported_models()
        
        # Cache the models for future requests
        await set_cached_models(models)
        
        return models
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        raise HTTPException(status_code=500, detail="Failed to get models")

# Health check endpoint moved to main.py to avoid duplication

@router.get("/billing/balance")
async def get_user_balance(user_id: str = Depends(get_current_user_async)):
    """
    Получить баланс пользователя
    """
    try:
        balance = await get_balance(user_id)
        return {"user_id": user_id, "balance": balance}
    except Exception as e:
        logger.error(f"Error getting balance for user {user_id}: {e}")
        # Return default balance for graceful degradation
        logger.warning(f"Returning default balance for user {user_id} due to database error")
        return {"user_id": user_id, "balance": 100.0, "warning": "Using default balance due to database issues"}

@router.get("/billing/transactions")
async def get_user_transactions(
    user_id: str = Depends(get_current_user_async),
    limit: int = 10,
    offset: int = 0
):
    """
    Получить историю транзакций пользователя
    """
    try:
        from app.services.billing_service import get_transaction_history
        transactions = await get_transaction_history(user_id, limit, offset)
        return {
            "user_id": user_id,
            "transactions": transactions,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error getting transactions for user {user_id}: {e}")
        # Return empty transactions for graceful degradation
        logger.warning(f"Returning empty transactions for user {user_id} due to database error")
        return {
            "user_id": user_id,
            "transactions": [],
            "limit": limit,
            "offset": offset,
            "warning": "Using empty transactions due to database issues"
        }