# LLM Gateway - Полная документация

## 📋 Содержание

1. [Обзор проекта](#обзор-проекта)
2. [Архитектура](#архитектура)
3. [Техническое описание](#техническое-описание)
4. [API документация](#api-документация)
5. [Конфигурация](#конфигурация)
6. [Развертывание](#развертывание)
7. [Мониторинг](#мониторинг)
8. [Безопасность](#безопасность)
9. [Примеры использования](#примеры-использования)
10. [Устранение неполадок](#устранение-неполадок)

## 🎯 Обзор проекта

### Что такое LLM Gateway?

LLM Gateway — это унифицированный API-шлюз для взаимодействия с различными провайдерами Large Language Models (LLM). Проект предоставляет единый интерфейс для работы с моделями от OpenAI, Anthropic, Google и других провайдеров.

### Основные возможности

- **Унифицированный API**: Единый интерфейс для всех LLM провайдеров
- **Биллинг и учет**: Система учета использования и списания средств
- **Rate Limiting**: Ограничение частоты запросов на пользователя и глобально
- **Мониторинг**: Интеграция с Prometheus, Sentry и Langfuse
- **Отказоустойчивость**: Circuit breaker и retry механизмы
- **Кэширование**: Redis и in-memory кэширование
- **Безопасность**: JWT аутентификация и валидация входных данных

### Поддерживаемые модели

- **OpenAI**: GPT-4, GPT-3.5-turbo
- **Anthropic**: Claude-3, Claude-2
- **Google**: Gemini-1.5-pro, Gemini-pro

## 🏗️ Архитектура

### Компоненты системы

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Apps   │    │   Web Browser   │    │   Mobile Apps   │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │      Nginx (Load Balancer)│
                    └─────────────┬─────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │    LLM Gateway (FastAPI)  │
                    │  ┌───────────────────────┐│
                    │  │   Rate Limiting      ││
                    │  │   Authentication     ││
                    │  │   Billing Service    ││
                    │  │   LiteLLM Service    ││
                    │  │   Monitoring         ││
                    │  └───────────────────────┘│
                    └─────────────┬─────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
┌─────────▼─────────┐  ┌─────────▼─────────┐  ┌─────────▼─────────┐
│   Redis Cache     │  │  Supabase (DB)    │  │   LLM Providers   │
│   - Rate Limiting │  │  - User Balances  │  │  - OpenAI         │
│   - Models Cache  │  │  - Transactions   │  │  - Anthropic      │
│   - Session Data  │  │  - User Stats     │  │  - Google         │
└───────────────────┘  └───────────────────┘  └───────────────────┘
```

### Технологический стек

- **Backend**: FastAPI (Python 3.8+)
- **LLM Integration**: LiteLLM
- **Database**: PostgreSQL (Supabase)
- **Cache**: Redis
- **Authentication**: JWT
- **Monitoring**: Prometheus, Sentry, Langfuse
- **Containerization**: Docker & Docker Compose
- **Load Balancing**: Nginx
- **Process Management**: Gunicorn (production)

## 🔧 Техническое описание

### Структура проекта

```
llm-gateway/
├── app/                          # Основной код приложения
│   ├── config/                   # Конфигурация
│   │   ├── environment.py        # Настройки окружения
│   │   ├── secrets.py            # Управление секретами
│   │   ├── settings.py           # Основные настройки
│   │   └── utils.py              # Утилиты конфигурации
│   ├── db/                       # Работа с базой данных
│   │   ├── async_postgres_client.py  # Async PostgreSQL клиент
│   │   └── supabase_client.py    # Supabase клиент
│   ├── dependencies.py           # FastAPI зависимости
│   ├── health/                   # Health checks
│   │   └── health_checks.py      # Проверки здоровья
│   ├── main.py                   # Точка входа приложения
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
├── deployments/                  # Конфигурация развертывания
│   ├── docker-compose.yml        # Docker Compose (dev)
│   ├── docker-compose.prod.yml   # Docker Compose (prod)
│   ├── Dockerfile                # Docker образ
│   ├── nginx.conf                # Nginx конфигурация
│   ├── start.sh                  # Скрипт запуска
│   ├── stop.sh                   # Скрипт остановки
│   ├── backup.sh                 # Скрипт бэкапа
│   ├── health-monitor.sh         # Мониторинг здоровья
│   ├── firewall-setup.sh         # Настройка файрвола
│   ├── ssl-setup.sh              # Настройка SSL
│   ├── logrotate.conf            # Ротация логов
│   ├── llm-gateway.service       # Systemd сервис
│   ├── k8s/                      # Kubernetes манифесты
│   └── monitoring/               # Конфигурация мониторинга
├── tests/                        # Тесты
├── requirements.txt              # Зависимости
├── pyproject.toml               # Конфигурация проекта
├── env.example                  # Пример переменных окружения
└── README.md                    # Основная документация
```

### Основные компоненты

#### 1. FastAPI приложение (`app/main.py`)

Основная точка входа приложения с настройкой:
- Sentry для error tracking
- Health check endpoints
- Graceful shutdown
- Middleware для rate limiting

#### 2. API роуты (`app/routers/api.py`)

Основные API endpoints:
- `/v1/chat/completions` - генерация текста
- `/v1/chat/completions/stream` - потоковая генерация
- `/v1/models` - список моделей (с кэшированием)
- `/billing/balance` - баланс пользователя
- `/billing/transactions` - история транзакций

#### 3. LiteLLM сервис (`app/services/litellm_service.py`)

Интеграция с различными LLM провайдерами:
- Router для маршрутизации запросов
- Circuit breaker для отказоустойчивости
- Retry механизмы
- Health checks для LLM сервисов

#### 4. Биллинг сервис (`app/services/billing_service.py`)

Управление балансом пользователей:
- Получение и обновление баланса
- История транзакций
- Оценка стоимости запросов
- Graceful degradation при недоступности БД

#### 5. Конфигурация (`app/config/settings.py`)

Централизованная конфигурация с поддержкой:
- Переменных окружения
- Секретов
- Environment-specific настроек
- Валидации конфигурации

## 📚 API документация

### Базовый URL
```
http://localhost:8000
```

### Аутентификация

Все API endpoints требуют JWT токен в заголовке:
```
Authorization: Bearer <your-jwt-token>
```

### Endpoints

#### 1. Генерация текста

**POST** `/v1/chat/completions`

Запрос:
```json
{
  "model": "gpt-3.5-turbo",
  "messages": [
    {
      "role": "user",
      "content": "Привет, как дела?"
    }
  ],
  "stream": false
}
```

Ответ:
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "gpt-3.5-turbo",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Привет! У меня все хорошо, спасибо что спросили. Как дела у вас?"
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
```

#### 2. Потоковая генерация

**POST** `/v1/chat/completions/stream`

Аналогично обычной генерации, но с `"stream": true`. Возвращает Server-Sent Events.

#### 3. Список моделей

**GET** `/v1/models`

Ответ:
```json
[
  {
    "id": "gpt-3.5-turbo",
    "object": "model",
    "created": 1677652288,
    "owned_by": "openai",
    "permission": [...],
    "root": "gpt-3.5-turbo",
    "parent": null
  }
]
```

#### 4. Баланс пользователя

**GET** `/billing/balance`

Ответ:
```json
{
  "user_id": "user123",
  "balance": 95.50
}
```

#### 5. История транзакций

**GET** `/billing/transactions?limit=10&offset=0`

Ответ:
```json
{
  "user_id": "user123",
  "transactions": [
    {
      "id": "txn_123",
      "amount": -0.002,
      "description": "Chat completion with gpt-3.5-turbo",
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ],
  "limit": 10,
  "offset": 0
}
```

### Health Check Endpoints

#### 1. Основной health check

**GET** `/health`

#### 2. Детальный health check

**GET** `/health/detailed`

#### 3. Circuit breaker статус

**GET** `/health/circuit-breakers`

#### 4. Системные ресурсы

**GET** `/health/system`

#### 5. История health checks

**GET** `/health/history`

#### 6. Readiness probe

**GET** `/ready`

#### 7. Prometheus метрики

**GET** `/metrics`

## ⚙️ Конфигурация

### Переменные окружения

Скопируйте `env.example` в `.env` и настройте:

```bash
# Основные настройки
HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=INFO
ENVIRONMENT=production
APP_VERSION=1.0.0

# База данных (Supabase)
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Rate Limiting
RATE_LIMIT_STORAGE=redis
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_REQUESTS_PER_HOUR=1000

# Аутентификация
JWT_SECRET_KEY=your_jwt_secret_key_here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# API ключи провайдеров
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_GEMINI_API_KEY=your_google_gemini_api_key_here

# Retry и Circuit Breaker
RETRY_ENABLED=true
RETRY_MAX_ATTEMPTS=3
RETRY_BASE_DELAY=1.0
RETRY_MAX_DELAY=60.0
CIRCUIT_BREAKER_ENABLED=true
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60

# Мониторинг
PROMETHEUS_ENABLED=true
LANGFUSE_ENABLED=false
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key_here
LANGFUSE_SECRET_KEY=your_langfuse_secret_key_here
SENTRY_DSN=your_sentry_dsn_here

# Биллинг
BILLING_ENABLED=true
BILLING_CURRENCY=USD
BILLING_DEFAULT_BALANCE=100.0

# Безопасность
CORS_ORIGINS=["http://localhost:3000", "https://yourdomain.com"]
ALLOWED_HOSTS=["localhost", "127.0.0.1", "yourdomain.com"]
```

### Проверка конфигурации

```bash
# Проверка переменных окружения
python check_env.py

# Проверка подключения к базе данных
python test_db_connection.py

# Тест production изменений
python test_production_changes.py
```

## 🚀 Развертывание

### Локальная разработка

1. **Клонирование и настройка:**
```bash
git clone <your-repo-url>
cd llm-gateway
cp env.example .env
# Отредактируйте .env файл
```

2. **Запуск с Docker Compose:**
```bash
docker-compose -f deployments/docker-compose.yml up -d
```

3. **Проверка работы:**
```bash
curl http://localhost:8000/health
```

### Продакшн развертывание

1. **Подготовка сервера:**
```bash
# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

2. **Настройка окружения:**
```bash
cp env.example .env
# Настройте все переменные окружения
```

3. **Запуск:**
```bash
chmod +x deployments/start.sh
./deployments/start.sh
```

### Docker конфигурация

#### Локальная разработка (`deployments/docker-compose.yml`)
- Один экземпляр приложения
- Redis для кэширования
- Health checks
- Volume для логов

#### Продакшн (`deployments/docker-compose.prod.yml`)
- Multi-worker mode с Gunicorn
- Nginx load balancer
- Мониторинг (Prometheus, Grafana)
- Backup и ротация логов

### Kubernetes развертывание

Манифесты в `deployments/k8s/`:
- `deployment.yaml` - Deployment, Service, Ingress, HPA
- `secrets.yaml` - Секреты и ConfigMaps

```bash
kubectl apply -f deployments/k8s/
```

## 📊 Мониторинг

### Health Checks

- **Основной**: `GET /health` - общий статус
- **Детальный**: `GET /health/detailed` - статус компонентов
- **Системный**: `GET /health/system` - ресурсы системы
- **Circuit Breaker**: `GET /health/circuit-breakers` - статус circuit breakers
- **История**: `GET /health/history` - история проверок

### Prometheus метрики

**GET** `/metrics`

Основные метрики:
- `llm_requests_total` - общее количество запросов
- `llm_requests_duration_seconds` - время выполнения запросов
- `llm_requests_errors_total` - количество ошибок
- `user_balance` - баланс пользователей
- `rate_limit_requests_total` - количество rate limit событий

### Sentry интеграция

Настройте `SENTRY_DSN` для:
- Error tracking
- Performance monitoring
- Release tracking

### Langfuse интеграция

Настройте Langfuse для:
- LLM observability
- Cost tracking
- Performance analysis

### Логирование

Структурированные логи в JSON формате:
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "message": "LLM call successful",
  "model": "gpt-3.5-turbo",
  "user_id": "user123",
  "duration_ms": 1250
}
```

## 🔒 Безопасность

### Аутентификация

JWT-based аутентификация:
- Токены в заголовке `Authorization: Bearer <token>`
- Настраиваемое время жизни токенов
- Secure token handling

### Rate Limiting

- **Per-user**: Ограничение на пользователя
- **Global**: Общие ограничения
- **Storage**: Redis или in-memory
- **Configurable**: Настраиваемые лимиты

### Валидация входных данных

- Pydantic модели для валидации
- Sanitization входных данных
- Защита от injection атак

### CORS

Настраиваемые CORS политики:
```python
CORS_ORIGINS=["http://localhost:3000", "https://yourdomain.com"]
ALLOWED_HOSTS=["localhost", "127.0.0.1", "yourdomain.com"]
```

### Security Headers

- CSP (Content Security Policy)
- HSTS (HTTP Strict Transport Security)
- X-Frame-Options
- X-Content-Type-Options

## 💡 Примеры использования

### Python клиент

```python
import requests
import json

# Конфигурация
BASE_URL = "http://localhost:8000"
API_TOKEN = "your-jwt-token"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# Получение списка моделей
response = requests.get(f"{BASE_URL}/v1/models", headers=headers)
models = response.json()
print("Доступные модели:", [model["id"] for model in models])

# Генерация текста
chat_data = {
    "model": "gpt-3.5-turbo",
    "messages": [
        {"role": "user", "content": "Расскажи о Python"}
    ],
    "stream": False
}

response = requests.post(
    f"{BASE_URL}/v1/chat/completions",
    headers=headers,
    json=chat_data
)

result = response.json()
print("Ответ:", result["choices"][0]["message"]["content"])

# Проверка баланса
balance_response = requests.get(f"{BASE_URL}/billing/balance", headers=headers)
balance = balance_response.json()
print(f"Баланс: ${balance['balance']}")
```

### JavaScript клиент

```javascript
const BASE_URL = 'http://localhost:8000';
const API_TOKEN = 'your-jwt-token';

const headers = {
    'Authorization': `Bearer ${API_TOKEN}`,
    'Content-Type': 'application/json'
};

// Получение моделей
async function getModels() {
    const response = await fetch(`${BASE_URL}/v1/models`, { headers });
    const models = await response.json();
    console.log('Доступные модели:', models.map(m => m.id));
    return models;
}

// Генерация текста
async function generateText(prompt) {
    const data = {
        model: 'gpt-3.5-turbo',
        messages: [{ role: 'user', content: prompt }],
        stream: false
    };

    const response = await fetch(`${BASE_URL}/v1/chat/completions`, {
        method: 'POST',
        headers,
        body: JSON.stringify(data)
    });

    const result = await response.json();
    return result.choices[0].message.content;
}

// Потоковая генерация
async function generateTextStream(prompt) {
    const data = {
        model: 'gpt-3.5-turbo',
        messages: [{ role: 'user', content: prompt }],
        stream: true
    };

    const response = await fetch(`${BASE_URL}/v1/chat/completions/stream`, {
        method: 'POST',
        headers,
        body: JSON.stringify(data)
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = line.slice(6);
                if (data === '[DONE]') return;
                
                try {
                    const parsed = JSON.parse(data);
                    if (parsed.choices[0]?.delta?.content) {
                        console.log(parsed.choices[0].delta.content);
                    }
                } catch (e) {
                    // Игнорируем ошибки парсинга
                }
            }
        }
    }
}

// Проверка баланса
async function getBalance() {
    const response = await fetch(`${BASE_URL}/billing/balance`, { headers });
    const balance = await response.json();
    console.log(`Баланс: $${balance.balance}`);
    return balance.balance;
}

// Использование
(async () => {
    await getModels();
    const text = await generateText('Привет, как дела?');
    console.log('Ответ:', text);
    await getBalance();
})();
```

### cURL примеры

```bash
# Получение моделей
curl -H "Authorization: Bearer your-jwt-token" \
     http://localhost:8000/v1/models

# Генерация текста
curl -X POST \
     -H "Authorization: Bearer your-jwt-token" \
     -H "Content-Type: application/json" \
     -d '{
       "model": "gpt-3.5-turbo",
       "messages": [
         {"role": "user", "content": "Привет!"}
       ],
       "stream": false
     }' \
     http://localhost:8000/v1/chat/completions

# Потоковая генерация
curl -X POST \
     -H "Authorization: Bearer your-jwt-token" \
     -H "Content-Type: application/json" \
     -d '{
       "model": "gpt-3.5-turbo",
       "messages": [
         {"role": "user", "content": "Расскажи историю"}
       ],
       "stream": true
     }' \
     http://localhost:8000/v1/chat/completions/stream

# Проверка баланса
curl -H "Authorization: Bearer your-jwt-token" \
     http://localhost:8000/billing/balance

# Health check
curl http://localhost:8000/health
```

## 🛠️ Устранение неполадок

### Частые проблемы

#### 1. Проблемы с подключением к базе данных

**Симптомы**: Ошибки `[WinError 10054]` или `Connection refused`

**Решение**:
```bash
# Проверьте настройки Supabase
python test_db_connection.py

# Убедитесь, что используете Service Role Key, а не Anon Key
# Проверьте, что порт 5432 не заблокирован
```

#### 2. Проблемы с Redis

**Симптомы**: Rate limiting не работает, ошибки подключения

**Решение**:
```bash
# Проверьте, что Redis запущен
docker-compose ps redis

# Проверьте подключение
redis-cli ping

# Перезапустите Redis
docker-compose restart redis
```

#### 3. Проблемы с API ключами

**Симптомы**: Ошибки 401 или 403 от LLM провайдеров

**Решение**:
```bash
# Проверьте переменные окружения
python check_env.py

# Убедитесь, что API ключи действительны
# Проверьте лимиты API провайдеров
```

#### 4. Проблемы с производительностью

**Симптомы**: Медленные ответы, таймауты

**Решение**:
```bash
# Проверьте логи
docker-compose logs llm-gateway

# Проверьте метрики
curl http://localhost:8000/metrics

# Проверьте circuit breaker статус
curl http://localhost:8000/health/circuit-breakers
```

### Логи и диагностика

#### Просмотр логов

```bash
# Логи приложения
docker-compose logs llm-gateway

# Логи с follow
docker-compose logs -f llm-gateway

# Логи за последний час
docker-compose logs --since=1h llm-gateway
```

#### Health checks

```bash
# Основной health check
curl http://localhost:8000/health

# Детальный health check
curl http://localhost:8000/health/detailed

# Системные ресурсы
curl http://localhost:8000/health/system
```

#### Метрики

```bash
# Prometheus метрики
curl http://localhost:8000/metrics

# Circuit breaker статус
curl http://localhost:8000/health/circuit-breakers
```

### Восстановление после сбоев

#### Автоматическое восстановление

- Circuit breaker автоматически восстанавливается
- Retry механизмы повторяют неудачные запросы
- Graceful degradation при недоступности компонентов

#### Ручное восстановление

```bash
# Перезапуск сервисов
docker-compose restart

# Полная перезагрузка
docker-compose down
docker-compose up -d

# Очистка кэша Redis
docker-compose exec redis redis-cli FLUSHALL
```

### Контакты и поддержка

При возникновении проблем:

1. Проверьте логи: `docker-compose logs llm-gateway`
2. Проверьте health endpoint: `curl http://localhost:8000/health`
3. Запустите тесты: `python test_production_changes.py`
4. Создайте issue в репозитории с подробным описанием проблемы

---

**Версия документации**: 1.0.0  
**Последнее обновление**: 2024-01-15  
**Соответствует коду**: Да