# LLM Gateway - Руководство по разработке

## 📋 Содержание

1. [Настройка среды разработки](#настройка-среды-разработки)
2. [Архитектура кода](#архитектура-кода)
3. [Структура проекта](#структура-проекта)
4. [API разработка](#api-разработка)
5. [Тестирование](#тестирование)
6. [Логирование и отладка](#логирование-и-отладка)
7. [Конфигурация](#конфигурация)
8. [Безопасность](#безопасность)
9. [Производительность](#производительность)
10. [Стиль кода](#стиль-кода)

## 🛠️ Настройка среды разработки

### Требования

- **Python**: 3.8+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Git**: 2.30+
- **IDE**: VS Code, PyCharm или аналогичный

### Установка зависимостей

```bash
# Клонирование репозитория
git clone <your-repo-url>
cd llm-gateway

# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/macOS
# или
venv\Scripts\activate     # Windows

# Установка зависимостей
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Настройка IDE

#### VS Code

Создайте `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": false,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.args": ["--profile", "black"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

#### PyCharm

1. Откройте проект в PyCharm
2. Настройте интерпретатор Python на `venv/bin/python`
3. Включите автоимпорт и форматирование кода

### Настройка pre-commit hooks

```bash
# Установка pre-commit
pip install pre-commit

# Настройка hooks
pre-commit install

# Создание .pre-commit-config.yaml
cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
EOF
```

## 🏗️ Архитектура кода

### Принципы архитектуры

1. **Слоистая архитектура**: Разделение на слои (API, сервисы, данные)
2. **Dependency Injection**: Внедрение зависимостей через FastAPI
3. **SOLID принципы**: Следование принципам SOLID
4. **Async/Await**: Использование асинхронного программирования
5. **Error Handling**: Централизованная обработка ошибок

### Слои приложения

```
┌─────────────────────────────────────┐
│           API Layer                 │
│  (FastAPI Routes & Middleware)      │
├─────────────────────────────────────┤
│         Service Layer               │
│  (Business Logic & External APIs)   │
├─────────────────────────────────────┤
│         Data Layer                  │
│  (Database & Cache Operations)      │
├─────────────────────────────────────┤
│        Infrastructure               │
│  (Config, Logging, Monitoring)      │
└─────────────────────────────────────┘
```

### Основные компоненты

#### 1. FastAPI приложение (`app/main.py`)

```python
from fastapi import FastAPI
from app.routers import api
from app.middleware.rate_limit import limiter
from app.health import health_checker

app = FastAPI(
    title="LLM Gateway",
    description="Unified API for multiple LLM providers",
    version="1.0.0"
)

# Middleware
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# Routers
app.include_router(api.router)

# Health checks
@app.get("/health")
async def health_check():
    return await health_checker.run_all_health_checks()
```

#### 2. API роуты (`app/routers/api.py`)

```python
from fastapi import APIRouter, Depends, HTTPException
from app.services.litellm_service import call_llm
from app.services.billing_service import get_balance, update_balance
from app.dependencies import get_current_user_async

router = APIRouter()

@router.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    user_id: str = Depends(get_current_user_async)
):
    # Проверка баланса
    balance = await get_balance(user_id)
    if balance < estimated_cost:
        raise InsufficientFundsError()
    
    # Вызов LLM
    response = await call_llm(request.model, request.messages)
    
    # Обновление баланса
    await update_balance(user_id, -actual_cost)
    
    return response
```

#### 3. Сервисы (`app/services/`)

```python
# litellm_service.py
class LiteLLMService:
    def __init__(self):
        self.router = self._setup_router()
        self.circuit_breakers = {}
    
    async def call_llm(self, model: str, messages: list, user_id: str):
        # Circuit breaker logic
        breaker = self._get_circuit_breaker(model)
        
        try:
            return await breaker.call_async(
                self._make_llm_request, model, messages, user_id
            )
        except CircuitBreakerError:
            raise LLMServiceError(f"Service {model} is temporarily unavailable")

# billing_service.py
class BillingService:
    def __init__(self, db_client: AsyncPostgresClient):
        self.db = db_client
    
    async def get_balance(self, user_id: str) -> float:
        return await self.db.get_balance(user_id)
    
    async def update_balance(self, user_id: str, amount: float, description: str):
        return await self.db.update_balance(user_id, amount, description)
```

#### 4. Модели данных (`app/models/schemas.py`)

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Content of the message")

class ChatCompletionRequest(BaseModel):
    model: str = Field(..., description="Model to use for completion")
    messages: List[ChatMessage] = Field(..., description="List of messages")
    stream: bool = Field(False, description="Whether to stream the response")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Temperature for generation")
```

## 📁 Структура проекта

### Подробная структура

```
llm-gateway/
├── app/                          # Основной код приложения
│   ├── __init__.py
│   ├── main.py                   # Точка входа FastAPI приложения
│   ├── config/                   # Конфигурация
│   │   ├── __init__.py
│   │   ├── environment.py        # Настройки окружения
│   │   ├── secrets.py            # Управление секретами
│   │   ├── settings.py           # Основные настройки
│   │   └── utils.py              # Утилиты конфигурации
│   ├── db/                       # Работа с базой данных
│   │   ├── async_postgres_client.py  # Async PostgreSQL клиент
│   │   └── supabase_client.py    # Supabase клиент
│   ├── dependencies.py           # FastAPI зависимости
│   ├── health/                   # Health checks
│   │   ├── __init__.py
│   │   └── health_checks.py      # Проверки здоровья
│   ├── middleware/               # Middleware
│   │   ├── auth.py               # Аутентификация
│   │   └── rate_limit.py         # Rate limiting
│   ├── models/                   # Pydantic модели
│   │   └── schemas.py            # API схемы
│   ├── monitoring/               # Мониторинг
│   │   ├── callbacks.py          # Callbacks для мониторинга
│   │   ├── langfuse_client.py    # Langfuse интеграция
│   │   └── prometheus_metrics.py # Prometheus метрики
│   ├── routers/                  # API роуты
│   │   └── api.py                # Основные API endpoints
│   ├── services/                 # Бизнес-логика
│   │   ├── billing_service.py    # Биллинг сервис
│   │   └── litellm_service.py    # LiteLLM интеграция
│   └── utils/                    # Утилиты
│       ├── exceptions.py         # Кастомные исключения
│       ├── logging.py            # Логирование
│       ├── redis_client.py       # Redis клиент
│       └── retry.py              # Retry механизмы
├── tests/                        # Тесты
│   ├── __init__.py
│   ├── conftest.py               # Конфигурация pytest
│   ├── test_api.py               # Тесты API
│   ├── test_services.py          # Тесты сервисов
│   ├── test_integration.py       # Интеграционные тесты
│   └── utils.py                  # Утилиты для тестов
├── deployments/                  # Конфигурация развертывания
├── requirements.txt              # Зависимости
├── requirements-dev.txt          # Зависимости для разработки
├── pyproject.toml               # Конфигурация проекта
├── .env.example                 # Пример переменных окружения
└── README.md                    # Документация
```

### Конвенции именования

- **Файлы**: snake_case (например, `billing_service.py`)
- **Классы**: PascalCase (например, `BillingService`)
- **Функции/методы**: snake_case (например, `get_balance`)
- **Переменные**: snake_case (например, `user_balance`)
- **Константы**: UPPER_SNAKE_CASE (например, `MAX_RETRY_ATTEMPTS`)
- **Модули**: snake_case (например, `async_postgres_client`)

## 🔌 API разработка

### Создание нового endpoint

1. **Определение схемы данных** (`app/models/schemas.py`):

```python
class NewRequest(BaseModel):
    field1: str = Field(..., description="Description of field1")
    field2: Optional[int] = Field(None, description="Description of field2")

class NewResponse(BaseModel):
    result: str
    status: str
```

2. **Добавление сервиса** (`app/services/new_service.py`):

```python
class NewService:
    def __init__(self, dependency1, dependency2):
        self.dep1 = dependency1
        self.dep2 = dependency2
    
    async def process_request(self, request: NewRequest) -> NewResponse:
        # Бизнес-логика
        result = await self.dep1.process(request.field1)
        status = await self.dep2.check_status(request.field2)
        
        return NewResponse(result=result, status=status)
```

3. **Создание endpoint** (`app/routers/api.py`):

```python
from app.services.new_service import NewService
from app.models.schemas import NewRequest, NewResponse

@router.post("/v1/new-endpoint", response_model=NewResponse)
async def new_endpoint(
    request: NewRequest,
    user_id: str = Depends(get_current_user_async),
    new_service: NewService = Depends(get_new_service)
):
    """
    Описание нового endpoint
    
    Args:
        request: Входные данные
        user_id: ID пользователя из токена
        new_service: Сервис для обработки
    
    Returns:
        NewResponse: Результат обработки
    
    Raises:
        HTTPException: При ошибках обработки
    """
    try:
        return await new_service.process_request(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in new_endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

4. **Добавление зависимости** (`app/dependencies.py`):

```python
def get_new_service() -> NewService:
    return NewService(
        dependency1=get_dependency1(),
        dependency2=get_dependency2()
    )
```

### Обработка ошибок

```python
from app.utils.exceptions import CustomException
from fastapi import HTTPException
from fastapi.responses import JSONResponse

# Кастомные исключения
class InsufficientFundsError(CustomException):
    def __init__(self, required: float, available: float):
        self.required = required
        self.available = available
        super().__init__(f"Insufficient funds. Required: ${required}, Available: ${available}")

# Обработчики исключений
@app.exception_handler(InsufficientFundsError)
async def insufficient_funds_handler(request, exc):
    return JSONResponse(
        status_code=402,
        content={
            "detail": str(exc),
            "code": 402,
            "error_type": "insufficient_funds",
            "required": exc.required,
            "available": exc.available
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "code": 500,
            "error_type": "internal_error"
        }
    )
```

### Валидация данных

```python
from pydantic import BaseModel, Field, validator
from typing import List

class ChatCompletionRequest(BaseModel):
    model: str = Field(..., description="Model to use")
    messages: List[ChatMessage] = Field(..., min_items=1, description="Messages")
    stream: bool = Field(False, description="Stream response")
    max_tokens: int = Field(None, ge=1, le=4000, description="Max tokens")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Temperature")
    
    @validator('model')
    def validate_model(cls, v):
        allowed_models = ['gpt-3.5-turbo', 'gpt-4', 'claude-3', 'gemini-1.5-pro']
        if v not in allowed_models:
            raise ValueError(f'Model must be one of: {allowed_models}')
        return v
    
    @validator('messages')
    def validate_messages(cls, v):
        if not v:
            raise ValueError('At least one message is required')
        
        # Проверка ролей
        valid_roles = ['user', 'assistant', 'system']
        for msg in v:
            if msg.role not in valid_roles:
                raise ValueError(f'Invalid role: {msg.role}. Must be one of: {valid_roles}')
        
        return v
```

## 🧪 Тестирование

### Типы тестов

1. **Unit тесты**: Тестирование отдельных функций/методов
2. **Integration тесты**: Тестирование взаимодействия компонентов
3. **API тесты**: Тестирование HTTP endpoints
4. **Performance тесты**: Тестирование производительности

### Структура тестов

```
tests/
├── __init__.py
├── conftest.py              # Конфигурация pytest
├── unit/                    # Unit тесты
│   ├── test_services.py
│   ├── test_models.py
│   └── test_utils.py
├── integration/             # Integration тесты
│   ├── test_database.py
│   ├── test_redis.py
│   └── test_llm.py
├── api/                     # API тесты
│   ├── test_chat.py
│   ├── test_models.py
│   └── test_billing.py
└── utils.py                 # Утилиты для тестов
```

### Примеры тестов

#### Unit тест

```python
# tests/unit/test_billing_service.py
import pytest
from unittest.mock import AsyncMock, patch
from app.services.billing_service import BillingService
from app.utils.exceptions import InsufficientFundsError

class TestBillingService:
    @pytest.fixture
    def mock_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def billing_service(self, mock_db):
        return BillingService(mock_db)
    
    @pytest.mark.asyncio
    async def test_get_balance_success(self, billing_service, mock_db):
        # Arrange
        user_id = "user123"
        expected_balance = 100.0
        mock_db.get_balance.return_value = expected_balance
        
        # Act
        result = await billing_service.get_balance(user_id)
        
        # Assert
        assert result == expected_balance
        mock_db.get_balance.assert_called_once_with(user_id)
    
    @pytest.mark.asyncio
    async def test_update_balance_insufficient_funds(self, billing_service, mock_db):
        # Arrange
        user_id = "user123"
        amount = -150.0
        mock_db.update_balance.side_effect = ValueError("Insufficient balance")
        
        # Act & Assert
        with pytest.raises(InsufficientFundsError):
            await billing_service.update_balance(user_id, amount, "test")
```

#### API тест

```python
# tests/api/test_chat.py
import pytest
from httpx import AsyncClient
from app.main import app

class TestChatAPI:
    @pytest.mark.asyncio
    async def test_chat_completion_success(self):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post(
                "/v1/chat/completions",
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": "Hello"}],
                    "stream": False
                },
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "choices" in data
            assert len(data["choices"]) > 0
            assert "message" in data["choices"][0]
    
    @pytest.mark.asyncio
    async def test_chat_completion_invalid_model(self):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post(
                "/v1/chat/completions",
                json={
                    "model": "invalid-model",
                    "messages": [{"role": "user", "content": "Hello"}],
                    "stream": False
                },
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_chat_completion_unauthorized(self):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post(
                "/v1/chat/completions",
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": "Hello"}],
                    "stream": False
                }
                # No Authorization header
            )
            
            assert response.status_code == 401
```

#### Integration тест

```python
# tests/integration/test_database.py
import pytest
import asyncio
from app.db.async_postgres_client import AsyncPostgresClient

class TestDatabaseIntegration:
    @pytest.fixture
    async def db_client(self):
        client = AsyncPostgresClient()
        await client.connect()
        yield client
        await client.close()
    
    @pytest.mark.asyncio
    async def test_balance_operations(self, db_client):
        # Arrange
        user_id = "test_user_123"
        initial_balance = 100.0
        
        # Act - Create user balance
        await db_client.create_user_balance(user_id, initial_balance)
        
        # Assert - Check initial balance
        balance = await db_client.get_balance(user_id)
        assert balance == initial_balance
        
        # Act - Update balance
        amount = -25.0
        result = await db_client.update_balance(user_id, amount, "test transaction")
        
        # Assert - Check updated balance
        assert result["balance_after"] == initial_balance + amount
        
        # Act - Get updated balance
        new_balance = await db_client.get_balance(user_id)
        assert new_balance == initial_balance + amount
```

### Конфигурация pytest

```python
# tests/conftest.py
import pytest
import asyncio
from unittest.mock import AsyncMock
from app.main import app
from app.config import get_settings

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def settings():
    """Get test settings."""
    return get_settings()

@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    return AsyncMock()

@pytest.fixture
def mock_db():
    """Mock database client."""
    return AsyncMock()

@pytest.fixture
def mock_llm_service():
    """Mock LLM service."""
    return AsyncMock()

@pytest.fixture
async def client():
    """Async client for testing."""
    from httpx import AsyncClient
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
```

### Запуск тестов

```bash
# Все тесты
pytest

# Только unit тесты
pytest tests/unit/

# Только API тесты
pytest tests/api/

# С покрытием
pytest --cov=app --cov-report=html

# Параллельное выполнение
pytest -n auto

# Verbose output
pytest -v

# Остановка при первой ошибке
pytest -x

# Показать локальные переменные при ошибке
pytest -l
```

## 📝 Логирование и отладка

### Настройка логирования

```python
# app/utils/logging.py
import structlog
import logging
from typing import Any, Dict

def setup_logging(level: str = "INFO", format: str = "json"):
    """Setup structured logging."""
    
    # Настройка structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Настройка стандартного logging
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, level.upper()),
    )

# Создание логгера
logger = structlog.get_logger()

# Использование
def some_function(user_id: str, data: Dict[str, Any]):
    logger.info(
        "Processing user request",
        user_id=user_id,
        data_size=len(data),
        operation="process_request"
    )
    
    try:
        # Логика обработки
        result = process_data(data)
        logger.info(
            "Request processed successfully",
            user_id=user_id,
            result_size=len(result)
        )
        return result
    except Exception as e:
        logger.error(
            "Error processing request",
            user_id=user_id,
            error=str(e),
            exc_info=True
        )
        raise
```

### Отладка

#### Отладочные логи

```python
import logging

# Включение debug логов
logging.getLogger().setLevel(logging.DEBUG)

# Отладочные логи для конкретного модуля
logging.getLogger("app.services.litellm_service").setLevel(logging.DEBUG)
```

#### Использование pdb

```python
import pdb

def complex_function(data):
    # Установка breakpoint
    pdb.set_trace()
    
    # Логика обработки
    result = process_data(data)
    return result
```

#### Использование ipdb (для лучшего опыта)

```bash
pip install ipdb
```

```python
import ipdb

def complex_function(data):
    ipdb.set_trace()
    # Логика обработки
```

### Профилирование

```python
import cProfile
import pstats
from functools import wraps

def profile_function(func):
    """Decorator для профилирования функции."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        result = func(*args, **kwargs)
        profiler.disable()
        
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        stats.print_stats(10)  # Top 10 functions
        
        return result
    return wrapper

# Использование
@profile_function
def slow_function():
    # Медленная логика
    pass
```

## ⚙️ Конфигурация

### Управление конфигурацией

```python
# app/config/settings.py
from pydantic_settings import BaseSettings
from typing import Optional, List
from pydantic import Field

class Settings(BaseSettings):
    # Основные настройки
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    
    # База данных
    supabase_url: str = Field(..., description="Supabase URL")
    supabase_key: str = Field(..., description="Supabase key")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")
    
    # API ключи
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_gemini_api_key: Optional[str] = None
    
    # Rate limiting
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_requests_per_minute: int = Field(default=60)
    
    # Retry settings
    retry_enabled: bool = Field(default=True)
    retry_max_attempts: int = Field(default=3)
    
    # Circuit breaker
    circuit_breaker_enabled: bool = Field(default=True)
    circuit_breaker_failure_threshold: int = Field(default=5)
    
    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"

# Глобальный экземпляр настроек
settings = Settings()
```

### Environment-specific конфигурация

```python
# app/config/environment.py
from typing import Dict, Any
import os

class EnvironmentConfig:
    @staticmethod
    def get_environment_name() -> str:
        return os.getenv("ENVIRONMENT", "development")
    
    @staticmethod
    def get_environment_config() -> Dict[str, Any]:
        env = EnvironmentConfig.get_environment_name()
        
        configs = {
            "development": {
                "debug": True,
                "log_level": "DEBUG",
                "rate_limit_enabled": False,
                "retry_enabled": False,
                "circuit_breaker_enabled": False,
            },
            "staging": {
                "debug": False,
                "log_level": "INFO",
                "rate_limit_enabled": True,
                "retry_enabled": True,
                "circuit_breaker_enabled": True,
            },
            "production": {
                "debug": False,
                "log_level": "WARNING",
                "rate_limit_enabled": True,
                "retry_enabled": True,
                "circuit_breaker_enabled": True,
            }
        }
        
        return configs.get(env, configs["development"])
```

### Управление секретами

```python
# app/config/secrets.py
import os
from typing import Optional

class SecretsManager:
    @staticmethod
    def get_secret(name: str) -> Optional[str]:
        """Get secret from environment or external source."""
        # Сначала проверяем переменные окружения
        value = os.getenv(name)
        if value:
            return value
        
        # Затем проверяем внешние источники (AWS Secrets Manager, etc.)
        # Это можно расширить для интеграции с внешними системами
        
        return None
    
    @staticmethod
    def get_required_secret(name: str) -> str:
        """Get required secret, raise error if not found."""
        value = SecretsManager.get_secret(name)
        if not value:
            raise ValueError(f"Required secret {name} not found")
        return value

# Глобальный экземпляр
secrets_manager = SecretsManager()
```

## 🔒 Безопасность

### Аутентификация и авторизация

```python
# app/middleware/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from app.config import get_settings

settings = get_settings()
security = HTTPBearer()

async def get_current_user_async(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Validate JWT token and return user ID."""
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=["HS256"]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_id
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
```

### Rate Limiting

```python
# app/middleware/rate_limit.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.config import get_settings

settings = get_settings()

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[
        f"{settings.rate_limit_requests_per_minute}/minute",
        f"{settings.rate_limit_requests_per_hour}/hour"
    ]
)

# Применение rate limiting к endpoint
@limiter.limit("5/minute")
@router.post("/v1/chat/completions")
async def chat_completions(request: Request):
    # Логика endpoint
    pass
```

### Валидация входных данных

```python
from pydantic import BaseModel, validator, Field
import re

class UserInput(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    
    @validator('content')
    def validate_content(cls, v):
        # Проверка на XSS
        if '<script>' in v.lower():
            raise ValueError('Script tags are not allowed')
        
        # Проверка на SQL injection
        sql_patterns = [
            r'(\b(union|select|insert|update|delete|drop|create)\b)',
            r'(\b(or|and)\b\s+\d+\s*=\s*\d+)',
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError('Invalid input detected')
        
        return v
```

### CORS настройки

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

## ⚡ Производительность

### Асинхронное программирование

```python
import asyncio
from typing import List
import aiohttp

class AsyncService:
    async def process_multiple_requests(self, urls: List[str]) -> List[str]:
        """Обработка множественных запросов асинхронно."""
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_url(session, url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return [r for r in results if not isinstance(r, Exception)]
    
    async def fetch_url(self, session: aiohttp.ClientSession, url: str) -> str:
        """Получение данных по URL."""
        async with session.get(url) as response:
            return await response.text()
```

### Кэширование

```python
import asyncio
from typing import Optional, Any
import json

class CacheService:
    def __init__(self, redis_client):
        self.redis = redis_client
        self._local_cache = {}
        self._local_cache_ttl = {}
    
    async def get(self, key: str) -> Optional[Any]:
        """Получение значения из кэша."""
        # Сначала проверяем локальный кэш
        if key in self._local_cache:
            if asyncio.get_event_loop().time() < self._local_cache_ttl[key]:
                return self._local_cache[key]
            else:
                del self._local_cache[key]
                del self._local_cache_ttl[key]
        
        # Затем проверяем Redis
        try:
            value = await self.redis.get(key)
            if value:
                parsed_value = json.loads(value)
                # Кэшируем локально
                self._local_cache[key] = parsed_value
                self._local_cache_ttl[key] = asyncio.get_event_loop().time() + 300  # 5 минут
                return parsed_value
        except Exception as e:
            logger.warning(f"Redis cache error: {e}")
        
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Установка значения в кэш."""
        try:
            await self.redis.setex(key, ttl, json.dumps(value))
            # Обновляем локальный кэш
            self._local_cache[key] = value
            self._local_cache_ttl[key] = asyncio.get_event_loop().time() + min(ttl, 300)
        except Exception as e:
            logger.warning(f"Redis cache error: {e}")
```

### Connection Pooling

```python
import asyncpg
from typing import Optional

class DatabasePool:
    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None
    
    async def get_pool(self) -> asyncpg.Pool:
        """Получение connection pool."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                host=settings.db_host,
                port=settings.db_port,
                user=settings.db_user,
                password=settings.db_password,
                database=settings.db_name,
                min_size=5,
                max_size=20,
                command_timeout=60,
                server_settings={
                    'application_name': 'llm_gateway'
                }
            )
        return self._pool
    
    async def close(self):
        """Закрытие connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
```

## 📏 Стиль кода

### PEP 8 и Black

```bash
# Форматирование кода
black app/ tests/

# Проверка стиля
flake8 app/ tests/

# Сортировка импортов
isort app/ tests/
```

### Type Hints

```python
from typing import List, Dict, Optional, Union, Any
from pydantic import BaseModel

def process_data(
    data: List[Dict[str, Any]], 
    config: Optional[Dict[str, Any]] = None
) -> Union[str, List[str]]:
    """Process data with type hints."""
    if config is None:
        config = {}
    
    result: List[str] = []
    for item in data:
        processed = process_item(item, config)
        result.append(processed)
    
    return result if len(result) > 1 else result[0]

class UserModel(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool = True
    metadata: Optional[Dict[str, Any]] = None
```

### Docstrings

```python
def complex_function(param1: str, param2: int, optional_param: bool = False) -> str:
    """
    Краткое описание функции.
    
    Подробное описание функции, включая детали реализации
    и примеры использования.
    
    Args:
        param1: Описание первого параметра
        param2: Описание второго параметра
        optional_param: Описание опционального параметра (по умолчанию False)
    
    Returns:
        str: Описание возвращаемого значения
    
    Raises:
        ValueError: Когда param1 пустой
        TypeError: Когда param2 не является числом
    
    Example:
        >>> result = complex_function("test", 42, True)
        >>> print(result)
        "processed_test_42"
    
    Note:
        Эта функция является частью критического пути и должна
        обрабатываться с осторожностью.
    """
    if not param1:
        raise ValueError("param1 cannot be empty")
    
    if not isinstance(param2, int):
        raise TypeError("param2 must be an integer")
    
    result = f"processed_{param1}_{param2}"
    if optional_param:
        result += "_optional"
    
    return result
```

### Комментарии

```python
# Хорошие комментарии
def calculate_tokens(text: str) -> int:
    """Calculate approximate token count for text."""
    # Rough estimation: 4 characters per token
    # This is a simplified approach; production should use proper tokenization
    return len(text) // 4

# Плохие комментарии
def add(a, b):
    # Add a and b  # Очевидно из кода
    return a + b

# Полезные комментарии для сложной логики
def process_llm_response(response: Dict[str, Any]) -> str:
    """Process LLM response and extract content."""
    
    # Handle different response formats from various providers
    if 'choices' in response:
        # OpenAI format
        return response['choices'][0]['message']['content']
    elif 'content' in response:
        # Anthropic format
        return response['content']
    else:
        # Fallback for unknown formats
        logger.warning(f"Unknown response format: {response}")
        return str(response)
```

---

**Версия документации**: 1.0.0  
**Последнее обновление**: 2024-01-15  
**Соответствует коду**: Да