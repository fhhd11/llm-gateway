# 🛠️ Руководство по разработке LLM Gateway

## 🚀 Быстрый старт для разработчиков

### 1. Настройка окружения

```bash
# Клонируйте репозиторий
git clone <your-repo-url>
cd llm-gateway

# Установите зависимости
make setup

# Настройте переменные окружения
cp env.example .env
# Отредактируйте .env файл
```

### 2. Запуск в режиме разработки

```bash
# Запуск с автоперезагрузкой
make dev

# Или с Docker
make docker-run
```

### 3. Запуск тестов

```bash
# Все тесты
make test

# С покрытием
make test-cov

# Только unit тесты
make test-unit

# Только интеграционные тесты
make test-integration
```

## 📁 Структура проекта

```
llm-gateway/
├── app/                    # Основной код
│   ├── config/            # Конфигурация и настройки
│   ├── routers/           # API роуты
│   ├── services/          # Бизнес-логика
│   ├── middleware/        # Middleware (auth, rate limiting)
│   ├── models/            # Pydantic модели
│   ├── utils/             # Утилиты
│   ├── db/                # Работа с базой данных
│   ├── health/            # Health checks
│   └── monitoring/        # Мониторинг и метрики
├── tests/                 # Тесты
│   ├── unit/             # Unit тесты
│   ├── integration/      # Интеграционные тесты
│   ├── conftest.py       # Pytest конфигурация
│   └── utils.py          # Тестовые утилиты
├── deployments/          # Деплой и Docker
└── docs/                 # Документация
```

## 🧪 Тестирование

### Структура тестов

- **Unit тесты** (`tests/unit/`) - тестируют отдельные функции и классы
- **Интеграционные тесты** (`tests/integration/`) - тестируют API endpoints
- **Fixtures** (`tests/conftest.py`) - общие тестовые данные и моки
- **Утилиты** (`tests/utils.py`) - вспомогательные функции для тестов

### Запуск тестов

```bash
# Все тесты
pytest

# С покрытием
pytest --cov=app --cov-report=html

# Конкретный тест
pytest tests/unit/test_main.py::TestHealthEndpoints::test_health_check_success

# С verbose выводом
pytest -v

# Параллельное выполнение
pytest -n auto
```

### Написание тестов

```python
# Пример unit теста
def test_health_check_success(client):
    """Test successful health check"""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "timestamp" in data

# Пример интеграционного теста
def test_chat_completions_requires_auth(client):
    """Test that chat completions endpoint requires authentication"""
    response = client.post("/v1/chat/completions", json={})
    assert response.status_code == 401
```

## 🔧 Разработка

### Добавление нового endpoint

1. **Создайте роут в `app/routers/`**
```python
from fastapi import APIRouter, Depends
from app.models.schemas import YourRequest, YourResponse

router = APIRouter()

@router.post("/your-endpoint", response_model=YourResponse)
async def your_endpoint(request: YourRequest):
    # Ваша логика
    return YourResponse(...)
```

2. **Добавьте в `app/main.py`**
```python
from app.routers import your_router

app.include_router(your_router.router)
```

3. **Создайте тесты**
```python
def test_your_endpoint(client):
    response = client.post("/your-endpoint", json={...})
    assert response.status_code == 200
```

### Добавление нового сервиса

1. **Создайте файл в `app/services/`**
```python
class YourService:
    def __init__(self):
        pass
    
    async def your_method(self):
        # Ваша логика
        pass
```

2. **Добавьте в зависимости (`app/dependencies.py`)**
```python
def get_your_service():
    return YourService()
```

### Работа с конфигурацией

```python
from app.config import get_settings

settings = get_settings()

# Использование настроек
if settings.debug:
    print("Debug mode enabled")
```

## 📝 Код стайл

### Форматирование

```bash
# Автоматическое форматирование
make format

# Проверка форматирования
make lint
```

### Правила

- **Black** - форматирование кода
- **isort** - сортировка импортов
- **flake8** - проверка стиля
- **mypy** - статическая типизация

### Pre-commit hooks

```bash
# Установка pre-commit
pip install pre-commit
pre-commit install

# Запуск на всех файлах
pre-commit run --all-files
```

## 🐳 Docker разработка

### Локальная разработка

```bash
# Сборка образа
make docker-build

# Запуск
make docker-run

# Логи
make docker-logs

# Остановка
make docker-stop
```

### Отладка в контейнере

```bash
# Запуск с отладкой
docker-compose -f deployments/docker-compose.yml up -d
docker-compose -f deployments/docker-compose.yml exec llm-gateway bash

# Просмотр логов
docker-compose -f deployments/docker-compose.yml logs -f llm-gateway
```

## 🔍 Отладка

### Логирование

```python
from app.utils.logging import logger

logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

### Отладка в IDE

1. **VS Code** - настройте `launch.json`
2. **PyCharm** - настройте конфигурацию запуска
3. **Docker** - используйте `docker-compose.override.yml`

### Health checks

```bash
# Проверка здоровья сервиса
curl http://localhost:8000/health

# Детальная проверка
curl http://localhost:8000/health/detailed

# Метрики
curl http://localhost:8000/metrics
```

## 📊 Мониторинг

### Prometheus метрики

```bash
# Просмотр метрик
curl http://localhost:8000/metrics

# Запуск Prometheus
docker-compose -f deployments/docker-compose.monitoring.yml up -d
```

### Логирование

```bash
# Просмотр логов
docker-compose logs -f llm-gateway

# Фильтрация логов
docker-compose logs -f llm-gateway | grep ERROR
```

## 🚀 Деплой

### Локальный тест

```bash
# Продакшн сборка
make docker-run-prod

# Проверка
make health
```

### Продакшн деплой

```bash
# Запуск продакшн сервисов
make start

# Остановка
make stop
```

## 🤝 Вклад в проект

### Workflow

1. **Fork репозитория**
2. **Создайте feature branch**
   ```bash
   git checkout -b feature/your-feature
   ```
3. **Внесите изменения**
4. **Добавьте тесты**
5. **Запустите проверки**
   ```bash
   make check
   ```
6. **Создайте Pull Request**

### Commit сообщения

Используйте conventional commits:

```
feat: add new endpoint for user management
fix: resolve authentication issue
docs: update API documentation
test: add unit tests for billing service
refactor: simplify configuration loading
```

### Code Review

- Все изменения должны проходить code review
- Тесты должны покрывать новую функциональность
- Документация должна быть обновлена
- Код должен соответствовать стилю проекта

## 📚 Полезные команды

```bash
# Помощь
make help

# Настройка окружения
make setup

# Запуск всех проверок
make check

# Очистка
make clean

# Конфигурация
make config
make validate
```

## 🆘 Поддержка

При возникновении проблем:

1. **Проверьте логи**: `make docker-logs`
2. **Проверьте здоровье**: `make health`
3. **Запустите тесты**: `make test`
4. **Создайте issue** в репозитории

## 🔗 Полезные ссылки

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Docker Documentation](https://docs.docker.com/)
- [Prometheus Documentation](https://prometheus.io/docs/) 