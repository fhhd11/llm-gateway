# 🧪 Тестирование LLM Gateway

## 📁 Структура тестов

```
tests/
├── unit/                 # Unit тесты
│   ├── test_main.py     # Тесты основного приложения
│   ├── test_settings_components.py
│   ├── test_configuration.py
│   ├── test_health_checks.py
│   ├── test_billing_service.py
│   ├── test_litellm_service.py
│   ├── test_monitoring.py
│   ├── test_rate_limiting.py
│   ├── test_redis_client.py
│   └── ...
├── integration/          # Интеграционные тесты
│   └── test_api.py      # Тесты API endpoints
├── conftest.py          # Pytest конфигурация и фикстуры
├── utils.py             # Тестовые утилиты
└── README.md           # Этот файл
```

## 🚀 Запуск тестов

### Все тесты
```bash
pytest
```

### С покрытием
```bash
pytest --cov=app --cov-report=html --cov-report=term-missing
```

### Конкретные тесты
```bash
# Unit тесты
pytest tests/unit/

# Интеграционные тесты
pytest tests/integration/

# Конкретный тест
pytest tests/unit/test_main.py::TestHealthEndpoints::test_health_check_success
```

### Параллельное выполнение
```bash
pytest -n auto
```

## 📝 Написание тестов

### Unit тесты

```python
def test_health_check_success(client):
    """Test successful health check"""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "timestamp" in data
```

### Интеграционные тесты

```python
def test_chat_completions_requires_auth(client):
    """Test that chat completions endpoint requires authentication"""
    response = client.post("/v1/chat/completions", json={})
    assert response.status_code == 401
```

### Использование фикстур

```python
def test_with_mock_settings(mock_settings):
    """Test with mocked settings"""
    assert mock_settings.environment == "test"
    assert mock_settings.debug is True
```

## 🔧 Фикстуры

### Доступные фикстуры

- `client` - FastAPI TestClient
- `mock_settings` - Mock настроек
- `mock_supabase_client` - Mock Supabase клиента
- `mock_redis_client` - Mock Redis клиента
- `mock_litellm` - Mock LiteLLM
- `temp_env_file` - Временный .env файл
- `sample_jwt_token` - Пример JWT токена
- `sample_chat_request` - Пример запроса чата
- `sample_chat_response` - Пример ответа чата

### Создание новых фикстур

```python
@pytest.fixture
def my_fixture():
    """My custom fixture"""
    # Setup
    data = {"key": "value"}
    yield data
    # Cleanup
    pass
```

## 🛠️ Тестовые утилиты

### API тестирование

```python
from tests.utils import make_chat_request, make_models_request

# Создание запроса чата
response = make_chat_request(
    client=client,
    messages=[{"role": "user", "content": "Hello"}],
    model="gpt-4",
    token="your-jwt-token"
)

# Создание запроса моделей
response = make_models_request(client=client, token="your-jwt-token")
```

### Валидация ответов

```python
from tests.utils import validate_chat_response, validate_models_response

# Валидация ответа чата
assert validate_chat_response(response)

# Валидация ответа моделей
assert validate_models_response(response)
```

## 📊 Покрытие кода

### Генерация отчета

```bash
pytest --cov=app --cov-report=html
```

### Просмотр отчета

Откройте `htmlcov/index.html` в браузере для просмотра детального отчета покрытия.

### Целевое покрытие

Стремитесь к покрытию не менее 80% кода.

## 🔍 Отладка тестов

### Verbose вывод

```bash
pytest -v
```

### Остановка на первой ошибке

```bash
pytest -x
```

### Показать локальные переменные

```bash
pytest -l
```

### Отладка с pdb

```bash
pytest --pdb
```

## 🐳 Docker тестирование

### Тестирование в контейнере

```bash
# Сборка образа для тестов
docker build -f deployments/Dockerfile -t llm-gateway-test .

# Запуск тестов в контейнере
docker run --rm llm-gateway-test pytest
```

### Тестирование с зависимостями

```bash
# Запуск тестов с полным окружением
docker-compose -f deployments/docker-compose.yml run --rm llm-gateway pytest
```

## 📋 Best Practices

### 1. Именование тестов

```python
def test_function_name_should_do_something():
    """Test description"""
    pass
```

### 2. Группировка тестов

```python
class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_health_check_success(self):
        pass
    
    def test_health_check_failure(self):
        pass
```

### 3. Использование моков

```python
@patch('app.services.litellm_service.litellm')
def test_litellm_integration(mock_litellm):
    mock_litellm.completion.return_value = {"choices": [{"message": {"content": "Hello"}}]}
    # Test logic
```

### 4. Очистка ресурсов

```python
@pytest.fixture
def temp_file():
    with tempfile.NamedTemporaryFile() as f:
        yield f.name
    # File is automatically cleaned up
```

### 5. Тестирование исключений

```python
def test_invalid_input_raises_exception():
    with pytest.raises(ValueError):
        function_that_raises_value_error()
```

## 🚨 Известные проблемы

### 1. Асинхронные тесты

Для тестирования асинхронных функций используйте `pytest-asyncio`:

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result == expected
```

### 2. Тестирование с базой данных

Используйте транзакции или временные базы данных:

```python
@pytest.fixture
def db_session():
    # Setup test database
    session = create_test_session()
    yield session
    # Cleanup
    session.close()
```

## 📚 Полезные ссылки

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Pytest-cov](https://pytest-cov.readthedocs.io/) 