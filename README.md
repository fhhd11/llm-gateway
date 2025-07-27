# LLM Gateway

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**Унифицированный API-шлюз для работы с Large Language Models**

Единый интерфейс для OpenAI, Anthropic, Google и других LLM провайдеров с биллингом, мониторингом и отказоустойчивостью.

[🚀 Быстрый старт](docs/QUICKSTART.md) • [📖 Документация](docs/README.md) • [🔌 API Reference](docs/API_REFERENCE.md)

</div>

---

## 🎯 Что это такое?

LLM Gateway — это унифицированный API-шлюз, который позволяет работать с различными провайдерами Large Language Models через единый интерфейс. Вместо интеграции с каждым провайдером отдельно, вы получаете один API для всех с встроенной системой биллинга, мониторинга и отказоустойчивости.

### ✨ Основные возможности

- 🔄 **Унифицированный API** - Один интерфейс для всех LLM провайдеров
- 💳 **Биллинг и учет** - Система учета использования и списания средств
- 🚦 **Rate Limiting** - Ограничение частоты запросов на пользователя и глобально
- 📊 **Мониторинг** - Интеграция с Prometheus, Sentry и Langfuse
- 🛡️ **Отказоустойчивость** - Circuit breaker и retry механизмы (временно отключены для стабильности)
- ⚡ **Кэширование** - Redis и in-memory кэширование
- 🔐 **Безопасность** - JWT аутентификация и валидация входных данных
- 🏥 **Health Checks** - Комплексная система проверки состояния

### 🤖 Поддерживаемые модели

| Провайдер | Модели |
|-----------|--------|
| **OpenAI** | gpt-4, gpt-3.5-turbo |
| **Anthropic** | claude-3 |
| **Google** | gemini-1.5-pro |

## 🚀 Быстрый старт

### За 5 минут

```bash
# 1. Клонируйте репозиторий
git clone <your-repo-url>
cd llm-gateway

# 2. Настройте переменные окружения
cp env.example .env
# Отредактируйте .env файл с вашими API ключами

# 3. Запустите с Docker
docker-compose -f deployments/docker-compose.yml up -d

# 4. Проверьте работу
curl http://localhost:8000/health
```

### Первый запрос

```bash
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
```

📖 **[Подробный быстрый старт](docs/QUICKSTART.md)**

## 🏗️ Архитектура

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
                    │  │   Health Checks      ││
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

## 🔧 Технологический стек

- **Backend**: FastAPI (Python 3.8+)
- **LLM Integration**: LiteLLM
- **Database**: PostgreSQL (Supabase)
- **Cache**: Redis
- **Authentication**: JWT
- **Monitoring**: Prometheus, Sentry, Langfuse
- **Containerization**: Docker & Docker Compose
- **Load Balancing**: Nginx
- **Process Management**: Gunicorn (production)
- **Error Handling**: Circuit Breaker, Retry mechanisms
- **Logging**: Structured logging with structlog

## 📚 Документация

📖 **[Полная документация](docs/DOCUMENTATION.md)** - Все руководства и справочники  
📋 **[Оглавление](docs/INDEX.md)** - Поиск по разделам документации  
🧭 **[Навигация](docs/NAVIGATION.md)** - Путеводитель по документации

### 🚀 Быстрый старт
- ⚡ [QUICKSTART.md](docs/QUICKSTART.md) - Быстрый старт за 5 минут
- 📖 [DOCUMENTATION.md](docs/DOCUMENTATION.md) - Полная документация проекта
- 🔌 [API_REFERENCE.md](docs/API_REFERENCE.md) - Подробный API Reference

### 🚀 Развертывание и разработка
- 🚀 [DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) - Полное руководство по развертыванию
- 🛠️ [DEVELOPMENT_GUIDE.md](docs/DEVELOPMENT_GUIDE.md) - Руководство по разработке

### 📋 Конфигурация
- ⚙️ [env.example](env.example) - Пример переменных окружения

## 🔌 API Endpoints

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/v1/chat/completions` | POST | Генерация текста |
| `/v1/chat/completions/stream` | POST | Потоковая генерация |
| `/v1/models` | GET | Список доступных моделей (с кэшированием) |
| `/billing/balance` | GET | Баланс пользователя |
| `/billing/transactions` | GET | История транзакций |
| `/health` | GET | Основная проверка состояния |
| `/health/detailed` | GET | Детальная проверка состояния |
| `/health/circuit-breakers` | GET | Статус circuit breakers |
| `/health/monitoring` | GET | Статус мониторинга |
| `/health/system` | GET | Системные ресурсы |
| `/health/history` | GET | История health checks (последние 10) |
| `/ready` | GET | Readiness probe для Kubernetes |
| `/metrics` | GET | Prometheus метрики |

📖 **[Подробный API Reference](docs/API_REFERENCE.md)**

## ⚙️ Конфигурация

### Обязательные переменные окружения

```bash
# База данных (Supabase)
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here

# Аутентификация
JWT_SECRET_KEY=your_jwt_secret_key_here

# API ключи провайдеров (хотя бы один)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_GEMINI_API_KEY=your_google_gemini_api_key_here
GOOGLE_API_KEY=your_google_api_key_here  # Дополнительный Google API ключ
```

### Опциональные настройки

```bash
# Redis
REDIS_URL=redis://localhost:6379/0

# Rate Limiting
RATE_LIMIT_STORAGE=redis  # redis or memory
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_REQUESTS_PER_HOUR=1000

# Retry & Circuit Breaker
RETRY_ENABLED=true
RETRY_MAX_ATTEMPTS=3
CIRCUIT_BREAKER_ENABLED=true
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5

# Мониторинг
SENTRY_DSN=your_sentry_dsn_here
LANGFUSE_ENABLED=false
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key_here
LANGFUSE_SECRET_KEY=your_langfuse_secret_key_here

# Биллинг
BILLING_ENABLED=true
BILLING_CURRENCY=USD
BILLING_DEFAULT_BALANCE=100.0
LITE_LLM_MARKUP=0.25  # Процент наценки для LiteLLM
```

📖 **[Подробная конфигурация](docs/DEPLOYMENT_GUIDE.md#конфигурация)**

## 🐳 Развертывание

### Локальная разработка

```bash
# Запуск с Docker Compose
docker-compose -f deployments/docker-compose.yml up -d

# Или с помощью Makefile
make docker-run

# Проверка работы
curl http://localhost:8000/health
```

### Продакшн

```bash
# Запуск продакшн сервисов
docker-compose -f deployments/docker-compose.prod.yml up -d

# Или с помощью скрипта
chmod +x deployments/start.sh
./deployments/start.sh

# Или с помощью Makefile
make docker-run-prod
```

### Kubernetes

```bash
# Применение манифестов
kubectl apply -f deployments/k8s/
```

### Управление сервисами

```bash
# Запуск
make start

# Остановка
make stop

# Просмотр логов
make docker-logs

# Проверка состояния
make health
```

📖 **[Подробное руководство по развертыванию](docs/DEPLOYMENT_GUIDE.md)**

## 📊 Мониторинг

### Health Checks

- **Основной**: `GET /health` - общий статус сервиса
- **Детальный**: `GET /health/detailed` - статус всех компонентов
- **Системный**: `GET /health/system` - ресурсы системы
- **Circuit Breaker**: `GET /health/circuit-breakers` - статус circuit breakers
- **Мониторинг**: `GET /health/monitoring` - статус мониторинга
- **История**: `GET /health/history` - история health checks (последние 10)
- **Readiness**: `GET /ready` - готовность к обработке запросов

### Метрики

- **Prometheus**: `GET /metrics` - метрики производительности
- **Grafana**: Дашборды для визуализации
- **Sentry**: Error tracking и performance monitoring
- **Langfuse**: LLM observability

### Логирование

- **Структурированные логи** с structlog
- **Уровни логирования** (DEBUG, INFO, WARNING, ERROR)
- **Контекстная информация** в каждом логе
- **Ротация логов** с logrotate

## 🔒 Безопасность

- **JWT аутентификация** - Secure token handling
- **Rate limiting** - Per-user и global ограничения
- **CORS настройки** - Контроль доступа
- **Input validation** - Валидация и sanitization входных данных
- **Security headers** - CSP, HSTS, X-Frame-Options
- **Circuit breaker** - Защита от каскадных сбоев (временно отключен)
- **Graceful degradation** - Fallback responses при ошибках

## 🧪 Тестирование

```bash
# Установка dev зависимостей
pip install -r requirements-dev.txt
# или
make install-dev

# Запуск тестов
pytest tests/ -v
# или
make test

# С покрытием
pytest tests/ --cov=app --cov-report=html
# или
make test-cov

# Линтинг
make lint

# Форматирование кода
make format

# Все проверки
make check
```

## 📁 Структура проекта

```
llm-gateway/
├── app/                          # Основной код приложения
│   ├── config/                   # Конфигурация
│   │   ├── environment.py        # Управление окружением
│   │   ├── secrets.py            # Управление секретами
│   │   ├── settings.py           # Настройки приложения
│   │   └── utils.py              # Утилиты конфигурации
│   ├── db/                       # Работа с базой данных
│   │   ├── async_postgres_client.py  # PostgreSQL клиент
│   │   └── supabase_client.py    # Supabase клиент
│   ├── health/                   # Health checks
│   │   └── health_checks.py      # Система проверки состояния
│   ├── middleware/               # Middleware
│   │   ├── auth.py               # Аутентификация
│   │   └── rate_limit.py         # Rate limiting
│   ├── models/                   # Pydantic модели
│   │   └── schemas.py            # API схемы
│   ├── monitoring/               # Мониторинг
│   │   ├── callbacks.py          # LiteLLM callbacks
│   │   ├── langfuse_client.py    # Langfuse интеграция
│   │   └── prometheus_metrics.py # Prometheus метрики
│   ├── routers/                  # API роуты
│   │   └── api.py                # Основные endpoints
│   ├── services/                 # Бизнес-логика
│   │   ├── billing_service.py    # Биллинг
│   │   └── litellm_service.py    # LLM интеграция
│   ├── utils/                    # Утилиты
│   │   ├── exceptions.py         # Кастомные исключения
│   │   ├── logging.py            # Логирование
│   │   ├── redis_client.py       # Redis клиент
│   │   └── retry.py              # Retry механизмы
│   ├── config.py                 # Конфигурация приложения
│   ├── dependencies.py           # FastAPI зависимости
│   ├── main.py                   # Точка входа FastAPI
│   └── __init__.py
├── docs/                         # 📚 Документация
│   ├── README.md                 # Главная страница документации
│   ├── INDEX.md                  # Оглавление
│   ├── QUICKSTART.md             # Быстрый старт
│   ├── DOCUMENTATION.md          # Полная документация
│   ├── API_REFERENCE.md          # API Reference
│   ├── DEPLOYMENT_GUIDE.md       # Руководство по развертыванию
│   ├── DEVELOPMENT_GUIDE.md      # Руководство по разработке
│   ├── STRUCTURE.md              # Структура документации
│   └── .gitkeep
├── deployments/                  # Конфигурация развертывания
│   ├── docker-compose.yml        # Docker Compose (dev)
│   ├── docker-compose.prod.yml   # Docker Compose (prod)
│   ├── docker-compose.monitoring.yml # Мониторинг
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
│   ├── crontab                   # Cron задачи
│   ├── test_gemini.sh            # Тест Gemini
│   ├── test_request.json         # Тестовый запрос
│   ├── k8s/                      # Kubernetes манифесты
│   │   ├── deployment.yaml       # Deployment
│   │   └── secrets.yaml          # Секреты
│   └── monitoring/               # Конфигурация мониторинга
│       ├── alertmanager.yml      # Alertmanager
│       ├── grafana-dashboard.json # Grafana дашборд
│       └── prometheus-rules.yml  # Prometheus правила
├── tests/                        # Тесты
│   ├── conftest.py               # Конфигурация pytest
│   ├── utils.py                  # Утилиты для тестов
│   └── README.md                 # Документация тестов
├── .github/                      # GitHub конфигурация
├── .git/                         # Git репозиторий
├── config_cli.py                 # CLI для управления конфигурацией
├── start_server.py               # Скрипт запуска сервера
├── run_server.bat                # Windows скрипт запуска
├── Makefile                      # Команды для разработки
├── pyproject.toml                # Конфигурация проекта
├── requirements.txt              # Зависимости
├── requirements-dev.txt          # Dev зависимости
├── test_requirements.txt         # Тестовые зависимости
├── env.example                   # Пример переменных окружения
├── supabase_db.sql               # SQL схема базы данных
├── test_request.json             # Тестовый запрос
├── llm-gateway-backup.tar.gz     # Бэкап
├── LICENSE                       # Лицензия
├── .gitignore                    # Git ignore
├── .flake8                       # Конфигурация flake8
├── .pre-commit-config.yaml       # Pre-commit hooks
└── README.md                     # Этот файл
```

## 🛠️ Разработка

### Установка окружения

```bash
# Клонирование и настройка
git clone <your-repo-url>
cd llm-gateway

# Установка зависимостей
make install-dev

# Настройка окружения
make setup

# Запуск в режиме разработки
make dev
```

### Полезные команды

```bash
# Показать справку
make help

# Проверка конфигурации
make config

# Валидация конфигурации
make validate

# Форматирование кода
make format

# Линтинг
make lint

# Тестирование
make test

# Все проверки
make check

# Очистка
make clean
```

### CLI для конфигурации

```bash
# Показать конфигурацию
python config_cli.py show

# Показать краткую сводку
python config_cli.py show --summary

# Валидация конфигурации
python config_cli.py validate
```

## 🤝 Вклад в проект

Мы приветствуем вклад в развитие проекта! 

1. **Fork** репозитория
2. Создайте **feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit** изменения (`git commit -m 'Add amazing feature'`)
4. **Push** в branch (`git push origin feature/amazing-feature`)
5. Откройте **Pull Request**

### Требования к коду

- Следуйте [стилю кода](docs/DEVELOPMENT_GUIDE.md#стиль-кода)
- Добавляйте тесты для новых функций
- Обновляйте документацию при необходимости
- Проверяйте код с помощью `pre-commit` hooks

## 🆘 Поддержка

### Устранение неполадок

1. **Проверьте логи**:
   ```bash
   docker-compose logs llm-gateway
   # или
   make docker-logs
   ```

2. **Проверьте health endpoint**:
   ```bash
   curl http://localhost:8000/health
   # или
   make health
   ```

3. **Проверьте конфигурацию**:
   ```bash
   make config
   make validate
   ```

4. **Запустите тесты**:
   ```bash
   make test
   ```

5. **Создайте issue** в репозитории с подробным описанием проблемы

### Полезные ссылки

- 📖 [Полная документация](docs/README.md)
- 🔌 [API Reference](docs/API_REFERENCE.md)
- 🚀 [Руководство по развертыванию](docs/DEPLOYMENT_GUIDE.md)
- 🛠️ [Руководство по разработке](docs/DEVELOPMENT_GUIDE.md)

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. См. файл [LICENSE](LICENSE) для деталей.

## 🔗 Полезные ссылки

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LiteLLM Documentation](https://docs.litellm.ai/)
- [Supabase Documentation](https://supabase.com/docs)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Sentry Documentation](https://docs.sentry.io/)
- [Langfuse Documentation](https://langfuse.com/docs)

---

<div align="center">

**LLM Gateway** - Унифицированный API для всех LLM провайдеров

[⭐ Star на GitHub](https://github.com/your-username/llm-gateway) • [📖 Документация](docs/README.md) • [🚀 Быстрый старт](docs/QUICKSTART.md)

</div>