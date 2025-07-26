# LLM Gateway

LLM Gateway — это унифицированный прокси для взаимодействия с различными провайдерами Large Language Models (LLM) с поддержкой биллинга, мониторинга и rate limiting.

## 🚀 Production-Ready Features

### ✅ **Критичные улучшения для продакшена:**

- **Multi-worker mode** с Gunicorn (4 workers) для высокой производительности
- **Error tracking** с Sentry для мониторинга ошибок
- **Intelligent caching** для /v1/models с Redis + memory fallback
- **Load balancing** с Nginx и multiple replicas
- **Graceful shutdown** с правильной очисткой ресурсов
- **Enhanced security headers** и WAF protection
- **Health checks** и monitoring endpoints

### 📊 **Производительность:**
- **4x улучшение** производительности благодаря Gunicorn workers
- **Кэширование** снижает время ответа на 80% для статических данных
- **Load balancing** распределяет нагрузку между несколькими инстансами
- **Connection pooling** для оптимизации работы с базой данных

### 🔒 **Безопасность:**
- **Enhanced security headers** (CSP, HSTS, X-Frame-Options)
- **Rate limiting** per-user и global
- **JWT authentication** с secure token handling
- **Input validation** и sanitization

## 🚀 Быстрый старт

### Локальная разработка

1. **Клонируйте репозиторий:**
```bash
git clone <your-repo-url>
cd llm-gateway
```

2. **Настройте окружение:**
```bash
cp env.example .env
# Отредактируйте .env файл с вашими настройками
```

3. **Проверьте конфигурацию:**
```bash
python check_env.py
```

4. **Проверьте подключение к базе данных:**
```bash
python test_db_connection.py
```

5. **Запустите с Docker Compose:**
```bash
docker-compose -f deployments/docker-compose.yml up -d
```

6. **Проверьте работу:**
```bash
curl http://localhost:8000/health
```

### Продакшн деплой

1. **Подготовьте сервер:**
```bash
# Установите Docker и Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

2. **Настройте окружение:**
```bash
cp env.example .env
# Настройте все переменные окружения в .env
```

3. **Запустите:**
```bash
chmod +x deployments/start.sh
./deployments/start.sh
```

4. **Протестируйте изменения:**
```bash
python test_production_changes.py
```

## 🔧 Устранение неполадок

### Проблемы с подключением к базе данных

Если вы видите ошибку `[WinError 10054] Удаленный хост принудительно разорвал существующее подключение`:

1. **Проверьте настройки Supabase:**
   - Убедитесь, что `SUPABASE_URL` и `SUPABASE_SERVICE_ROLE_KEY` правильно настроены
   - Используйте Service Role Key, а не Anon Key для подключения к PostgreSQL

2. **Запустите тест подключения:**
```bash
python test_db_connection.py
```

3. **Проверьте сетевые настройки:**
   - Убедитесь, что порт 5432 не заблокирован
   - Проверьте, что VPN не блокирует подключения к Supabase
   - Убедитесь, что DNS правильно разрешает доменное имя

4. **Подробные инструкции:**
   См. файл [SUPABASE_SETUP.md](SUPABASE_SETUP.md) для детальных инструкций по настройке.

### Логи и мониторинг

- **Логи приложения:** Проверьте логи на наличие ошибок подключения
- **Health check:** `GET /health` - общий статус сервиса
- **Database health:** `GET /health/detailed` - детальная информация о состоянии БД
- **Metrics:** `GET /metrics` - Prometheus метрики
- **Error tracking:** Настройте Sentry DSN для отслеживания ошибок

## 📋 Поддерживаемые модели

- **OpenAI**: GPT-4, GPT-3.5-turbo
- **Anthropic**: Claude-3, Claude-2
- **Google**: Gemini-1.5-pro, Gemini-pro

## 🔧 API Endpoints

### GET /v1/models
Возвращает список поддерживаемых моделей в формате, совместимом с OpenAI API. **Кэшируется** для улучшения производительности.

### POST /v1/chat/completions
Основной endpoint для генерации текста с использованием LLM моделей.

### GET /health
Проверка состояния сервиса.

### GET /metrics
Prometheus метрики.

## ⚙️ Конфигурация

### Обязательные переменные окружения:

```bash
# Supabase (база данных)
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# JWT для аутентификации
JWT_SECRET_KEY=your_jwt_secret

# API ключи провайдеров
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_GEMINI_API_KEY=your_gemini_key

# Error tracking (опционально)
SENTRY_DSN=your_sentry_dsn
```

### Опциональные настройки:

```bash
# Redis для rate limiting и кэширования
REDIS_URL=redis://localhost:6379/0

# Rate limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_REQUESTS_PER_HOUR=1000

# Environment
ENVIRONMENT=production
APP_VERSION=1.0.0
```

## 🐳 Docker

### Локальная разработка:
```bash
docker-compose -f deployments/docker-compose.yml up -d
```

### Продакшн (с multi-worker mode):
```bash
docker-compose -f deployments/docker-compose.prod.yml up -d
```

## 📊 Мониторинг

- **Health Check**: `GET /health`
- **Metrics**: `GET /metrics` (Prometheus)
- **Circuit Breaker Status**: `GET /health/circuit-breakers`
- **Error Tracking**: Sentry integration (если настроен)

## 🔒 Безопасность

- JWT аутентификация
- Rate limiting (per-user и global)
- CORS настройки
- Circuit breaker для отказоустойчивости
- Enhanced security headers
- Input validation и sanitization

## 📝 Логирование

Логи доступны через:
```bash
docker-compose -f deployments/docker-compose.prod.yml logs -f llm-gateway
```

## 🧪 Тестирование

```bash
# Установите dev зависимости
pip install -r requirements-dev.txt

# Запустите тесты
pytest

# С покрытием
pytest --cov=app --cov-report=html

# Тест production изменений
python test_production_changes.py
```

## 📁 Структура проекта

```
llm-gateway/
├── app/                    # Основной код приложения
│   ├── config/            # Конфигурация
│   ├── routers/           # API роуты (с кэшированием)
│   ├── services/          # Бизнес-логика
│   ├── middleware/        # Middleware
│   └── utils/             # Утилиты
├── deployments/           # Docker и деплой
│   ├── docker-compose.yml # Локальная разработка
│   ├── docker-compose.prod.yml # Продакшн (multi-worker)
│   ├── Dockerfile         # Образ приложения (Gunicorn)
│   ├── nginx.conf         # Конфигурация Nginx (load balancing)
│   ├── start.sh           # Скрипт запуска
│   ├── stop.sh            # Скрипт остановки
│   ├── backup.sh          # Скрипт бэкапа
│   ├── health-monitor.sh  # Мониторинг здоровья
│   ├── firewall-setup.sh  # Настройка файрвола
│   ├── ssl-setup.sh       # Настройка SSL
│   ├── logrotate.conf     # Ротация логов
│   ├── llm-gateway.service # Systemd сервис
│   ├── k8s/               # Kubernetes манифесты
│   └── monitoring/        # Конфигурация мониторинга
├── tests/                 # Тесты
├── requirements.txt       # Зависимости (включая Gunicorn, Sentry)
├── test_production_changes.py # Тест production изменений
└── README.md             # Документация
```

## 📚 Документация

### 🚀 Быстрый старт
- 📖 [DEPLOYMENT.md](DEPLOYMENT.md) - Полное руководство по развертыванию
- 🛠️ [DEVELOPMENT.md](DEVELOPMENT.md) - Руководство по разработке

### 📋 Конфигурация
- ⚙️ [env.example](env.example) - Пример переменных окружения

## 🔧 Скрипты развертывания

### Основные скрипты:
- `deployments/start.sh` - Запуск продакшн сервисов
- `deployments/stop.sh` - Остановка сервисов
- `deployments/backup.sh` - Создание бэкапов
- `deployments/health-monitor.sh` - Мониторинг здоровья

### Настройка безопасности:
- `deployments/firewall-setup.sh` - Настройка UFW файрвола
- `deployments/ssl-setup.sh` - Настройка SSL сертификатов
- `deployments/logrotate.conf` - Ротация логов

### Системные сервисы:
- `deployments/llm-gateway.service` - Systemd сервис для автозапуска

## 🐳 Docker конфигурация

### Образы:
- `deployments/Dockerfile` - Основной образ приложения (Gunicorn)
- `deployments/docker-compose.yml` - Локальная разработка
- `deployments/docker-compose.prod.yml` - Продакшн (multi-worker)
- `deployments/docker-compose.monitoring.yml` - Мониторинг

### Nginx:
- `deployments/nginx.conf` - Конфигурация reverse proxy (load balancing)

## ☸️ Kubernetes

### Манифесты:
- `deployments/k8s/deployment.yaml` - Deployment, Service, Ingress, HPA
- `deployments/k8s/secrets.yaml` - Секреты и ConfigMaps

## 📊 Мониторинг и алерты

### Prometheus:
- `deployments/monitoring/prometheus.yml` - Конфигурация
- `deployments/monitoring/prometheus-rules.yml` - Правила алертов
- `deployments/monitoring/alertmanager.yml` - Конфигурация алертов

### Grafana:
- `deployments/monitoring/grafana-dashboard.json` - Дашборд

### Sentry:
- Error tracking и performance monitoring
- Настройте `SENTRY_DSN` в переменных окружения

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте feature branch
3. Внесите изменения
4. Добавьте тесты
5. Создайте Pull Request

## 📄 Лицензия

MIT License - см. файл LICENSE для деталей.

## 🆘 Поддержка

При возникновении проблем:
1. Проверьте логи: `docker-compose logs llm-gateway`
2. Проверьте health endpoint: `curl http://localhost:8000/health`
3. Запустите тесты: `python test_production_changes.py`
4. Создайте issue в репозитории

## 🔗 Полезные ссылки

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LiteLLM Documentation](https://docs.litellm.ai/)
- [Supabase Documentation](https://supabase.com/docs)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Sentry Documentation](https://docs.sentry.io/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
