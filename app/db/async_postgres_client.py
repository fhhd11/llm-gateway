"""
Async PostgreSQL client using asyncpg
Provides async database operations with connection pooling and transaction support
"""

import asyncpg
import logging
import asyncio
from typing import Optional, Dict, Any, List, Union
from contextlib import asynccontextmanager
from app.config import get_settings
from app.utils.retry import retry_with_exponential_backoff

logger = logging.getLogger(__name__)
settings = get_settings()


class AsyncPostgresClient:
    """Async PostgreSQL client with connection pooling"""
    
    def __init__(self, connection_string: str, pool_size: int = 10, max_overflow: int = 20):
        self.connection_string = connection_string
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self._pool: Optional[asyncpg.Pool] = None
        self._connection_attempts = 0
        self._max_connection_attempts = 3
    
    async def initialize(self):
        """Initialize connection pool with retry logic"""
        if self._pool is None:
            await self._initialize_with_retry()
    
    async def _initialize_with_retry(self):
        """Initialize connection pool with retry logic"""
        for attempt in range(self._max_connection_attempts):
            try:
                # Parse connection string to add SSL settings for Supabase
                connection_params = self._parse_connection_string()
                
                self._pool = await asyncpg.create_pool(
                    **connection_params,
                    min_size=2,  # Reduced min_size for better stability
                    max_size=self.pool_size + self.max_overflow,
                    command_timeout=settings.timeouts.database_timeout,
                    server_settings={
                        'application_name': 'llm-gateway',
                        'timezone': 'UTC'
                    },
                    # Add connection retry settings
                    connection_class=asyncpg.Connection
                )
                
                # Test the connection
                async with self._pool.acquire() as conn:
                    await conn.execute('SELECT 1')
                
                logger.info(f"PostgreSQL connection pool initialized successfully with {self.pool_size} connections")
                self._connection_attempts = 0  # Reset attempts on success
                return
                
            except Exception as e:
                self._connection_attempts += 1
                logger.error(f"Failed to initialize PostgreSQL connection pool (attempt {attempt + 1}/{self._max_connection_attempts}): {e}")
                
                if attempt < self._max_connection_attempts - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"Retrying connection in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("Max connection attempts reached. Using fallback mode.")
                    # Don't raise exception, let the application continue with fallback
                    return
    
    def _parse_connection_string(self) -> Dict[str, Any]:
        """Parse connection string and add SSL settings for Supabase"""
        # For Supabase, we need to ensure SSL is properly configured
        if 'supabase.co' in self.connection_string:
            # Supabase requires SSL - add SSL parameters to connection string
            if '?' in self.connection_string:
                # Connection string already has parameters
                ssl_params = '&sslmode=require'
                if 'sslmode=' not in self.connection_string:
                    connection_string = self.connection_string + ssl_params
                else:
                    connection_string = self.connection_string
            else:
                # No parameters in connection string
                connection_string = self.connection_string + '?sslmode=require'
            
            return {
                'dsn': connection_string
            }
        else:
            return {
                'dsn': self.connection_string
            }
    
    async def close(self):
        """Close connection pool"""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("PostgreSQL connection pool closed")
    
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection from pool with retry logic"""
        if self._pool is None:
            await self.initialize()
        
        if self._pool is None:
            # If pool initialization failed, raise a more descriptive error
            raise ConnectionError("Database connection pool is not available. Check your database configuration.")
        
        try:
            async with self._pool.acquire() as connection:
                yield connection
        except asyncpg.ConnectionDoesNotExistError:
            logger.error("Connection from pool does not exist. Attempting to reinitialize pool.")
            await self._reinitialize_pool()
            async with self._pool.acquire() as connection:
                yield connection
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    async def _reinitialize_pool(self):
        """Reinitialize the connection pool"""
        if self._pool:
            await self._pool.close()
            self._pool = None
        await self.initialize()
    
    @asynccontextmanager
    async def transaction(self):
        """Get database transaction with retry logic"""
        if self._pool is None:
            await self.initialize()
        
        if self._pool is None:
            raise ConnectionError("Database connection pool is not available. Check your database configuration.")
        
        try:
            async with self._pool.acquire() as connection:
                async with connection.transaction():
                    yield connection
        except Exception as e:
            logger.error(f"Database transaction error: {e}")
            raise
    
    @retry_with_exponential_backoff(max_attempts=3, base_delay=1.0)
    async def execute(self, query: str, *args) -> str:
        """Execute a command and return status with retry logic"""
        async with self.get_connection() as conn:
            return await conn.execute(query, *args)
    
    @retry_with_exponential_backoff(max_attempts=3, base_delay=1.0)
    async def fetch(self, query: str, *args) -> List[asyncpg.Record]:
        """Fetch multiple rows with retry logic"""
        async with self.get_connection() as conn:
            return await conn.fetch(query, *args)
    
    @retry_with_exponential_backoff(max_attempts=3, base_delay=1.0)
    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        """Fetch a single row with retry logic"""
        async with self.get_connection() as conn:
            return await conn.fetchrow(query, *args)
    
    @retry_with_exponential_backoff(max_attempts=3, base_delay=1.0)
    async def fetchval(self, query: str, *args) -> Any:
        """Fetch a single value with retry logic"""
        async with self.get_connection() as conn:
            return await conn.fetchval(query, *args)
    
    # Specific methods for billing operations
    async def get_balance(self, user_id: str) -> float:
        """Get user balance"""
        query = """
            SELECT balance FROM balances 
            WHERE user_id = $1
        """
        result = await self.fetchval(query, user_id)
        return float(result) if result is not None else 0.0
    
    async def update_balance(self, user_id: str, amount: float, description: str) -> Dict[str, Any]:
        """Update user balance with transaction record"""
        async with self.transaction() as conn:
            # Get current balance
            balance_query = "SELECT balance FROM balances WHERE user_id = $1"
            current_balance = await conn.fetchval(balance_query, user_id)
            balance_before = float(current_balance) if current_balance is not None else 0.0
            
            # Calculate new balance
            balance_after = balance_before + amount
            if balance_after < 0:
                raise ValueError(f"Insufficient balance. Current: {balance_before}, Required: {abs(amount)}")
            
            # Update balance
            upsert_query = """
                INSERT INTO balances (user_id, balance) 
                VALUES ($1, $2)
                ON CONFLICT (user_id) 
                DO UPDATE SET balance = $2
            """
            await conn.execute(upsert_query, user_id, balance_after)
            
            # Insert transaction record
            transaction_query = """
                INSERT INTO transactions (user_id, amount, type, description)
                VALUES ($1, $2, $3, $4)
                RETURNING id
            """
            transaction_type = "debit" if amount < 0 else "credit"
            transaction_id = await conn.fetchval(transaction_query, user_id, amount, transaction_type, description)
            
            return {
                "balance_before": balance_before,
                "balance_after": balance_after,
                "transaction_id": transaction_id,
                "success": True
            }
    
    async def get_transaction_history(self, user_id: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Get transaction history for user with pagination"""
        query = """
            SELECT id, user_id, amount, type, description, timestamp
            FROM transactions 
            WHERE user_id = $1 
            ORDER BY timestamp DESC 
            LIMIT $2 OFFSET $3
        """
        records = await self.fetch(query, user_id, limit, offset)
        return [dict(record) for record in records]
    
    async def validate_balance_integrity(self, user_id: str) -> Dict[str, Any]:
        """Validate balance integrity by comparing with transaction history"""
        # Get current balance
        current_balance = await self.get_balance(user_id)
        
        # Calculate balance from transactions
        query = "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE user_id = $1"
        calculated_balance = await self.fetchval(query, user_id)
        calculated_balance = float(calculated_balance) if calculated_balance is not None else 0.0
        
        # Get transaction count
        count_query = "SELECT COUNT(*) FROM transactions WHERE user_id = $1"
        transaction_count = await self.fetchval(count_query, user_id)
        
        is_valid = abs(current_balance - calculated_balance) < 0.001
        
        return {
            "user_id": user_id,
            "current_balance": current_balance,
            "calculated_balance": calculated_balance,
            "transaction_count": transaction_count,
            "is_valid": is_valid,
            "difference": current_balance - calculated_balance
        }
    
    async def create_user_balance(self, user_id: str, initial_balance: float = 0.0) -> bool:
        """Create initial balance for new user"""
        query = """
            INSERT INTO balances (user_id, balance)
            VALUES ($1, $2)
            ON CONFLICT (user_id) DO NOTHING
        """
        result = await self.execute(query, user_id, initial_balance)
        return "INSERT" in result
    
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user statistics"""
        # Get balance
        balance = await self.get_balance(user_id)
        
        # Get transaction stats
        stats_query = """
            SELECT 
                COUNT(*) as total_transactions,
                COUNT(CASE WHEN amount < 0 THEN 1 END) as debits,
                COUNT(CASE WHEN amount > 0 THEN 1 END) as credits,
                COALESCE(SUM(CASE WHEN amount < 0 THEN amount END), 0) as total_debits,
                COALESCE(SUM(CASE WHEN amount > 0 THEN amount END), 0) as total_credits,
                MIN(timestamp) as first_transaction,
                MAX(timestamp) as last_transaction
            FROM transactions 
            WHERE user_id = $1
        """
        stats = await self.fetchrow(stats_query, user_id)
        
        return {
            "user_id": user_id,
            "current_balance": balance,
            "total_transactions": stats["total_transactions"] if stats else 0,
            "debits": stats["debits"] if stats else 0,
            "credits": stats["credits"] if stats else 0,
            "total_debits": float(stats["total_debits"]) if stats else 0.0,
            "total_credits": float(stats["total_credits"]) if stats else 0.0,
            "first_transaction": stats["first_transaction"] if stats else None,
            "last_transaction": stats["last_transaction"] if stats else None
        }


# Global client instance
_async_postgres_client: Optional[AsyncPostgresClient] = None


async def get_async_postgres_client() -> AsyncPostgresClient:
    """Get or create async PostgreSQL client instance"""
    global _async_postgres_client
    
    if _async_postgres_client is None:
        # Parse database URL from settings
        db_url = settings.database.url
        _async_postgres_client = AsyncPostgresClient(
            connection_string=db_url,
            pool_size=settings.database.pool_size,
            max_overflow=settings.database.max_overflow
        )
        await _async_postgres_client.initialize()
    
    return _async_postgres_client


async def close_async_postgres_client():
    """Close async PostgreSQL client"""
    global _async_postgres_client
    
    if _async_postgres_client:
        await _async_postgres_client.close()
        _async_postgres_client = None 