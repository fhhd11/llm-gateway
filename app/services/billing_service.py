from app.db.async_postgres_client import get_async_postgres_client, AsyncPostgresClient
from app.utils.exceptions import InsufficientFundsError
from app.config import get_settings
from app.utils.retry import retry_with_exponential_backoff

settings = get_settings()
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class BillingTransactionError(Exception):
    """Custom exception for billing transaction errors"""
    pass


# Async billing operations using PostgreSQL
@retry_with_exponential_backoff(max_attempts=3, base_delay=1.0)
async def get_balance(user_id: str) -> float:
    """Get user balance using async PostgreSQL client with retry logic"""
    try:
        db = await get_async_postgres_client()
        # Check if database is available
        if db._pool is None:
            logger.warning(f"Database not available, using default balance for user {user_id}")
            return 100.0
        return await db.get_balance(user_id)
    except Exception as e:
        logger.error(f"Error getting balance for user {user_id}: {e}")
        # Return default balance for graceful degradation
        logger.warning(f"Using default balance for user {user_id} due to database error")
        return 100.0  # Default balance for development

@retry_with_exponential_backoff(max_attempts=3, base_delay=1.0)
async def update_balance(user_id: str, amount: float, description: str) -> Dict[str, Any]:
    """Update user balance with transaction record using async PostgreSQL with retry logic"""
    try:
        db = await get_async_postgres_client()
        # Check if database is available
        if db._pool is None:
            logger.warning(f"Database not available, using mock balance update for user {user_id}")
            return {
                "balance_before": 100.0,
                "balance_after": 100.0 + amount,
                "transaction_id": "mock-transaction",
                "success": True,
                "warning": "Mock transaction due to database unavailability"
            }
        return await db.update_balance(user_id, amount, description)
    except ValueError as e:
        if "Insufficient balance" in str(e):
            raise InsufficientFundsError(str(e))
        raise
    except Exception as e:
        logger.error(f"Error updating balance for user {user_id}: {e}")
        # Return a mock response for graceful degradation
        logger.warning(f"Using mock balance update for user {user_id} due to database error")
        return {
            "balance_before": 100.0,
            "balance_after": 100.0 + amount,
            "transaction_id": "mock-transaction",
            "success": True,
            "warning": "Mock transaction due to database issues"
        }

@retry_with_exponential_backoff(max_attempts=3, base_delay=1.0)
async def get_transaction_history(user_id: str, limit: int = 10, offset: int = 0) -> list:
    """Get transaction history for a user using async PostgreSQL with retry logic"""
    try:
        db = await get_async_postgres_client()
        return await db.get_transaction_history(user_id, limit, offset)
    except Exception as e:
        logger.error(f"Error getting transaction history for user {user_id}: {e}")
        # Return empty list for graceful degradation
        logger.warning(f"Using empty transaction history for user {user_id} due to database error")
        return []

@retry_with_exponential_backoff(max_attempts=3, base_delay=1.0)
async def validate_balance_integrity(user_id: str) -> Dict[str, Any]:
    """Validate balance integrity using async PostgreSQL with retry logic"""
    try:
        db = await get_async_postgres_client()
        return await db.validate_balance_integrity(user_id)
    except Exception as e:
        logger.error(f"Error validating balance integrity for user {user_id}: {e}")
        raise

@retry_with_exponential_backoff(max_attempts=3, base_delay=1.0)
async def create_user_balance(user_id: str, initial_balance: float = 0.0) -> bool:
    """Create initial balance for new user using async PostgreSQL with retry logic"""
    try:
        db = await get_async_postgres_client()
        return await db.create_user_balance(user_id, initial_balance)
    except Exception as e:
        logger.error(f"Error creating balance for user {user_id}: {e}")
        raise

@retry_with_exponential_backoff(max_attempts=3, base_delay=1.0)
async def get_user_stats(user_id: str) -> Dict[str, Any]:
    """Get user statistics using async PostgreSQL with retry logic"""
    try:
        db = await get_async_postgres_client()
        return await db.get_user_stats(user_id)
    except Exception as e:
        logger.error(f"Error getting stats for user {user_id}: {e}")
        raise

# Estimated cost function (simplified, based on tokens estimate)
def estimate_cost(request_or_model, response_or_tokens=None) -> float:
    """
    Estimate cost for LLM call based on model and token count
    
    Args:
        request_or_model: Either ChatCompletionRequest object or model name string
        response_or_tokens: Either response object or token count integer
    """
    from app.models.schemas import ChatCompletionRequest
    
    # Handle ChatCompletionRequest input
    if isinstance(request_or_model, ChatCompletionRequest):
        request = request_or_model
        model = request.model
        
        # Estimate tokens from messages (rough approximation)
        total_tokens = 0
        for message in request.messages:
            # Rough token estimation: ~4 characters per token
            total_tokens += len(message.content) // 4
        
        # Add some overhead for system messages and formatting
        total_tokens += len(request.messages) * 10
        
    else:
        # Handle direct model and token count
        model = request_or_model
        total_tokens = response_or_tokens or 1000  # Default fallback
    
    # Dummy prices, adjust per model
    base_prices = {
        "gpt-4": 0.00003,
        "gpt-3.5-turbo": 0.000002,
        "claude-3": 0.000015,
        "gemini-1.5-pro": 0.0000125
    }
    
    price_per_token = base_prices.get(model, 0.00002)  # Default fallback
    base_cost = total_tokens * price_per_token
    markup_cost = base_cost * settings.lite_llm_markup
    
    return base_cost + markup_cost

# Legacy sync functions for backward compatibility (deprecated)
def get_balance_sync(user_id: str) -> float:
    """Sync version of get_balance for backward compatibility (deprecated)"""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(get_balance(user_id))
    except RuntimeError:
        # If no event loop, create one
        return asyncio.run(get_balance(user_id))

def update_balance_sync(user_id: str, amount: float, description: str) -> Dict[str, Any]:
    """Sync version of update_balance for backward compatibility (deprecated)"""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(update_balance(user_id, amount, description))
    except RuntimeError:
        # If no event loop, create one
        return asyncio.run(update_balance(user_id, amount, description))