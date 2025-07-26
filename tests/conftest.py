"""
Pytest configuration and fixtures for LLM Gateway tests
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import os
import tempfile

from app.main import app


@pytest.fixture
def client():
    """Test client for FastAPI app"""
    return TestClient(app)


@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    with patch('app.config.settings.get_settings') as mock:
        settings = Mock()
        settings.environment = "test"
        settings.debug = True
        settings.supabase_url = "https://test.supabase.co"
        settings.supabase_key = "test-key"
        settings.openai_api_key = "test-openai-key"
        settings.anthropic_api_key = "test-anthropic-key"
        settings.google_gemini_api_key = "test-gemini-key"
        settings.rate_limit_enabled = False
        settings.retry_enabled = False
        settings.circuit_breaker_enabled = False
        settings.monitoring.langfuse_enabled = False
        settings.monitoring.prometheus_enabled = False
        settings.security.jwt_secret = "test-jwt-secret"
        settings.redis.url = "redis://localhost:6379/0"
        settings.database.url = "postgresql://test:test@localhost:5432/test"
        
        mock.return_value = settings
        yield settings


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing"""
    with patch('app.db.supabase_client.supabase_client') as mock:
        client = Mock()
        mock.return_value = client
        yield client


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing"""
    with patch('app.utils.redis_client.redis_client') as mock:
        client = Mock()
        client.is_connected.return_value = True
        mock.return_value = client
        yield client


@pytest.fixture
def mock_litellm():
    """Mock LiteLLM for testing"""
    with patch('app.services.litellm_service.litellm') as mock:
        yield mock


@pytest.fixture
def temp_env_file():
    """Create temporary .env file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("""
SUPABASE_URL=https://test.supabase.co
SUPABASE_KEY=test-key
OPENAI_API_KEY=test-openai-key
ANTHROPIC_API_KEY=test-anthropic-key
GOOGLE_GEMINI_API_KEY=test-gemini-key
JWT_SECRET_KEY=test-jwt-secret
REDIS_URL=redis://localhost:6379/0
        """)
        temp_file = f.name
    
    yield temp_file
    
    # Cleanup
    try:
        os.unlink(temp_file)
    except OSError:
        pass


@pytest.fixture
def sample_jwt_token():
    """Sample JWT token for testing"""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"


@pytest.fixture
def sample_chat_request():
    """Sample chat completion request"""
    return {
        "model": "gpt-4",
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ],
        "stream": False,
        "max_tokens": 100
    }


@pytest.fixture
def sample_chat_response():
    """Sample chat completion response"""
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": "gpt-4",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Hello! I'm doing well, thank you for asking. How can I help you today?"
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 9,
            "completion_tokens": 12,
            "total_tokens": 21
        }
    } 