from fastapi import Depends, HTTPException, Header  # type: ignore
import jwt  # type: ignore
import base64  # type: ignore
from supabase import create_client, Client  # type: ignore
from app.config import get_settings

settings = get_settings()
import logging
import httpx
from typing import Optional

logger = logging.getLogger("jwt")

def get_authorization_header() -> str:
    """Helper function for testing - returns the authorization header"""
    # This is a placeholder for testing
    # In real usage, this would come from the request
    return "Bearer test_token"

def get_supabase_client() -> Client:
    """Создает sync Supabase client для обратной совместимости"""
    if not settings.supabase_url or not settings.supabase_key:
        raise ValueError("Supabase URL and key are required")
        
    try:
        return create_client(settings.supabase_url, settings.supabase_key)
    except Exception as e:
        logger.error(f"Failed to create Supabase client: {e}")
        # Fallback: create client without any additional parameters
        from supabase import Client as SupabaseClient
        return SupabaseClient(settings.supabase_url, settings.supabase_key)

async def get_supabase_client_async() -> Client:
    """Создает async Supabase client для новых операций"""
    # Supabase-py пока не поддерживает нативный async, но мы можем использовать httpx
    # для async HTTP запросов. Пока оставляем sync client, но готовим структуру
    return get_supabase_client()

def _decode_jwt_secret(secret: str) -> str:
    """Decode base64 JWT secret to string"""
    try:
        # Try to decode as base64 first
        decoded = base64.b64decode(secret)
        return decoded.decode('utf-8')
    except Exception:
        # If it's not base64, return as is
        return secret

def get_current_user(authorization: str = Header(...)):
    """
    Получает и верифицирует JWT токен для аутентификации пользователя.
    
    Args:
        authorization: Authorization header с Bearer токеном
        
    Returns:
        str: ID пользователя из токена
        
    Raises:
        ValueError: Если токен недействителен или отсутствует
    """
    try:
        # Извлекаем токен из Authorization header
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header format")
        
        token: str = authorization.replace("Bearer ", "")
        
        if not token:
            raise HTTPException(status_code=401, detail="Empty token")
        
        # Определяем параметры верификации на основе окружения
        verify_signature = settings.security.jwt_verify
        jwt_secret = settings.security.jwt_secret
        
        if verify_signature and not jwt_secret:
            raise HTTPException(status_code=500, detail="JWT verification enabled but no secret configured")
        
        # Если верификация отключена, просто возвращаем токен
        if not verify_signature:
            return token
        
        try:
            # Декодируем JWT секрет из base64
            decoded_secret = _decode_jwt_secret(jwt_secret)
            
            # Декодируем токен с верификацией
            payload = jwt.decode(
                token, 
                decoded_secret, 
                algorithms=["HS256"],
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_aud": False,  # Disable audience verification for Supabase tokens
                    "require": ["exp", "iat", "sub"]
                }
            )
            
            logger.debug(f"JWT payload decoded successfully: {payload.get('sub', 'unknown')}")
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidSignatureError:
            raise HTTPException(status_code=401, detail="Invalid token signature")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
        except Exception as e:
            logger.error(f"Unexpected JWT error: {e}")
            raise HTTPException(status_code=401, detail=f"Token processing error: {e}")
        
        # Извлекаем user_id из payload
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Missing 'sub' field")
        
        # Дополнительные проверки для production
        if verify_signature:
            # Проверяем issuer если указан
            if "iss" in payload:
                expected_issuer = settings.supabase_url
                actual_issuer = payload["iss"]
                
                # Handle both formats: with and without /auth/v1
                if actual_issuer.endswith("/auth/v1"):
                    actual_issuer = actual_issuer.replace("/auth/v1", "")
                
                if actual_issuer != expected_issuer:
                    logger.warning(f"Token issuer mismatch: {payload['iss']} != {expected_issuer}")
            
            # Проверяем аудиторию если указана
            if "aud" in payload and payload["aud"] != "authenticated":
                logger.warning(f"Token audience mismatch: {payload['aud']} != authenticated")
        
        logger.info(f"User authenticated successfully: {user_id}")
        return user_id
        
    except HTTPException:
        # Re-raise HTTPException exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_current_user: {e}")
        raise HTTPException(status_code=401, detail=f"Authentication failed: {e}")

async def get_current_user_async(authorization: Optional[str] = Header(None)):
    """
    Async wrapper for get_current_user for FastAPI dependency injection
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    return get_current_user(authorization)