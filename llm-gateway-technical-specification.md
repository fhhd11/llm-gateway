# Технический Документ: LLM Gateway

## Введение

LLM Gateway — это standalone микросервис, разработанный как унифицированный прокси для взаимодействия с различными провайдерами Large Language Models (LLM), такими как OpenAI, Anthropic, Google Gemini и другими. Он интегрируется с LiteLLM для унификации API вызовов, Supabase для аутентификации и управления базой данных (балансы и транзакции), и FastAPI как основным фреймворком для создания высокопроизводительного API.

Цели:
- Обеспечить безопасный, масштабируемый и унифицированный доступ к LLM провайдерам.
- Реализовать биллинг с наценкой (markup) и atomic обновлениями баланса.
- Поддерживать streaming ответов для real-time взаимодействия.
- Соответствовать production-ready стандартам: async обработка, error handling, logging, monitoring, compliance с российским законодательством (FZ-152 для локализации данных в РФ via Yandex Cloud-integrated Supabase).

Документ описывает архитектуру, файловую структуру, технологический стек, потоки данных, взаимодействия компонентов, безопасность, масштабируемость и деплой. Все решения ориентированы на production: без моков, с реальными интеграциями, тестированием и мониторингом. Актуализация на 11 июля 2025 года на основе веб-поиска (FastAPI v0.116.0, LiteLLM v1.74.0-stable, Supabase-py v2.5.0).

## Архитектура

### Общая Архитектура
LLM Gateway — это stateless микросервис (кроме взаимодействий с DB), который действует как gateway между upstream сервисами (e.g., Orchestrator или Frontend) и LLM провайдерами. Он обрабатывает аутентификацию, rate limiting, проверку баланса, вызовы LLM и пост-обработку (billing).

- **Компоненты**:
  - **API Layer (FastAPI)**: Обработка HTTP запросов, включая streaming endpoints.
  - **LiteLLM Proxy**: Унификация вызовов к LLM, с поддержкой fallbacks, cost tracking via callbacks и rate limiting.
  - **Supabase Integration**: Аутентификация (JWT) и DB (PostgreSQL с Row Level Security — RLS для изоляции данных пользователей).
  - **Middleware**: Auth, rate limiting (SlowAPI с Redis для distributed storage).
  - **Services**: Бизнес-логика для billing и LLM вызовов.
  - **Monitoring & Logging**: Интеграция с Prometheus/Grafana для метрик, Langfuse для LLM tracing via LiteLLM callbacks, structlog для structured logging.

- **Внешние Зависимости**:
  - LLM Providers: OpenAI, Anthropic и т.д. (API keys в Vault или env).
  - Supabase: Hosted в РФ-compliant регионе (Yandex Cloud integration).
  - Redis: Для rate limiting и caching (опционально для session state, но в Gateway stateless).

- **Диаграмма Архитектуры (Текстовая)**:
  ```
  [Upstream (Orchestrator/Frontend)] --> [HTTPS Request (JWT, JSON payload)]
                                       |
                                       v
  [FastAPI App] --> [Middleware: Auth (Supabase JWT) --> Rate Limit (SlowAPI + Redis)]
                    |
                    v
  [Dependency: Get User ID] --> [Billing Check: Async Query Supabase DB (balances)]
                                |
                                v (If balance OK)
  [LiteLLM Service: Call completion(model, messages, stream=True)] --> [Fallback Router if needed]
                                                                       |
                                                                       v
  [LLM Provider API] <-- [Unified Call]
                      --> [Response (Streaming Chunks + Usage Tokens)]
                                |
                                v
  [Callback: Calculate Cost (tokens * price + markup)] --> [Atomic DB Update: Deduct balance, Insert transaction (Supabase)]
                                                           |
                                                           v
  [Stream Response to Upstream] + [Log to Langfuse/Prometheus]
  ```

Эта архитектура обеспечивает низкую latency (<100ms overhead), reliability (fallbacks) и security (RLS, JWT).

### Масштабируемость и Надежность
- **Horizontal Scaling**: Stateless дизайн позволяет запускать multiple instances в Kubernetes (Yandex Managed Kubernetes).
- **Fault Tolerance**: LiteLLM fallbacks (auto-switch providers); DB retries via exponential backoff.
- **Performance**: Async I/O everywhere (FastAPI async routes, asyncpg для DB если нужно расширить supabase-py).
- **Monitoring**: Prometheus для метрик (e.g., request latency, error rates); Grafana dashboards; LiteLLM callbacks для tracing.

## Файловая Структура

Проект организован как mono-repo для простоты, с четким разделением concerns. Структура следует best practices для FastAPI (из GitHub zhanymkanov/fastapi-best-practices: modular, testable, with config separation).

```
llm-gateway/
├── app/
│   ├── __init__.py
│   ├── main.py                  # Entry point: FastAPI app creation, middleware setup, router includes
│   ├── config.py                # Settings via Pydantic (env vars: SUPABASE_URL, LITE_LLM_KEYS, etc.)
│   ├── dependencies.py          # FastAPI dependencies (e.g., get_current_user, get_db_client)
│   ├── routers/
│   │   └── api.py               # Endpoints: /v1/chat/completions, /v1/models (list available models)
│   ├── services/
│   │   ├── litellm_service.py   # Wrappers for LiteLLM (completion calls, callbacks for cost tracking)
│   │   └── billing_service.py   # Logic for balance checks, updates (async DB interactions)
│   ├── db/
│   │   └── supabase_client.py   # Supabase client initialization and async queries/updates
│   ├── middleware/
│   │   ├── auth.py              # JWT authentication middleware (Supabase-specific)
│   │   └── rate_limit.py        # SlowAPI configuration with Redis backend
│   ├── models/
│   │   └── schemas.py           # Pydantic models (e.g., ChatCompletionRequest, ChatCompletionResponse)
│   ├── utils/
│   │   ├── logging.py           # Structured logging setup (structlog)
│   │   └── exceptions.py        # Custom exceptions (e.g., InsufficientFundsError)
│   └── monitoring/
│       └── callbacks.py         # LiteLLM callbacks for monitoring (cost, traces to Langfuse)
├── tests/
│   ├── unit/
│   │   ├── test_litellm_service.py  # Unit tests for LLM calls (with mocks for providers)
│   │   └── test_billing_service.py  # Unit tests for billing logic
│   ├── integration/
│   │   └── test_api.py              # Integration tests for endpoints (using TestClient, real Supabase if possible)
│   └── conftest.py                  # Pytest fixtures (e.g., app client)
├── deployments/
│   ├── Dockerfile                   # Multi-stage build for production
│   ├── docker-compose.yml           # Local dev setup (with Redis, Supabase mock if needed, but prod uses real)
│   └── k8s/                         # Kubernetes manifests (deployments, services, secrets)
├── .github/
│   └── workflows/
│       └── ci-cd.yml                # GitHub Actions: lint, test, build, deploy to Yandex Cloud
├── requirements.txt                 # Production dependencies
├── requirements-dev.txt             # Dev dependencies (pytest, black, etc.)
├── .env.example                     # Sample environment variables
├── pyproject.toml                   # Black, isort, pylint config
├── README.md                        # Project overview, setup instructions
└── LICENSE                          # MIT or proprietary
```

Эта структура обеспечивает maintainability: тесты изолированы, config централизован.

## Технологический Стек

- **Backend Framework**: FastAPI v0.116.0 (high-performance, async, auto-docs via Swagger).
- **LLM Proxy**: LiteLLM v1.74.0-stable (supports 100+ providers, built-in proxy, callbacks, fallbacks).
- **Database & Auth**: Supabase (PostgreSQL with RLS, JWT auth); supabase-py v2.5.0 for client.
- **Rate Limiting**: SlowAPI v0.1.9 with Redis backend (aioredis для async).
- **Logging**: structlog v24.1.0 (structured JSON logs).
- **Monitoring**: Langfuse v2.x (via LiteLLM callbacks); Prometheus v2.53.0 + Grafana.
- **Other**: Pydantic v2.7.4 (validation), httpx v0.27.0 (async HTTP), python-dotenv v1.0.1 (env loading).
- **Infrastructure**: Docker, Kubernetes, Vault для secrets.
- **Testing**: pytest v8.2.2 (80%+ coverage), Locust для load testing.
- **CI/CD**: GitHub Actions (black/isort lint, pytest, Docker build/push).

Все версии актуальны на 11 июля 2025 (из web_search).

## Потоки Данных и Взаимодействия

### Основной Поток Запроса (/v1/chat/completions)
1. **Incoming Request**: JSON payload (model, messages) с JWT в Authorization header от upstream (e.g., Orchestrator).
2. **Middleware Processing**:
   - Auth: dependencies.get_current_user() verifies JWT, extracts user_id.
   - Rate Limit: middleware.rate_limit() checks limits (e.g., 10 req/min per user_id) via Redis.
3. **Billing Check**: services.billing_service.check_balance(user_id, estimated_cost) — async query к Supabase balances table.
4. **LLM Call**: services.litellm_service.call_llm(model, messages, stream=True) — использует LiteLLM completion с fallback.
5. **Response Handling**: StreamingResponse yields chunks; на success callback (LiteLLM) рассчитывается cost.
6. **Billing Update**: services.billing_service.update_balance(user_id, -cost, "LLM call") — atomic INSERT/UPDATE в Supabase (используя transactions via Supabase RPC для atomicity).
7. **Logging/Monitoring**: utils.logging.log_request(); monitoring.callbacks.track_usage() sends to Langfuse.
8. **Error Flow**: Если balance low — raise exceptions.InsufficientFundsError (HTTP 402); provider error — fallback or 500 with retry.

### Взаимодействия Сервисов
- **Internal**: Routers вызывают services; services используют db/supabase_client и LiteLLM.
- **External**: 
  - Supabase: Async HTTP calls via supabase-py (для auth verification и DB ops).
  - LLM Providers: HTTP via LiteLLM (secrets из config).
  - Redis: Для rate limiting (aioredis client in middleware).
  - Monitoring: Async pushes to Langfuse/Prometheus.

### DB Схема (Supabase PostgreSQL)
- **Tables**:
  - balances: user_id (UUID PK), balance (DECIMAL).
  - transactions: id (UUID PK), user_id (FK), amount (DECIMAL), type (TEXT), timestamp (TIMESTAMP), description (TEXT).
- **RLS Policies**: SELECT/UPDATE only for auth.uid() = user_id.
- **Compliance**: Данные локализованы в РФ; нет хранения sensitive chat data.

## Компоненты: Детальное Описание

### Routers (routers/api.py)
- Endpoints: POST /v1/chat/completions (Pydantic validation via schemas.ChatCompletionRequest).
- Async routes для streaming.

### Services
- **litellm_service.py**: Wrappers для litellm.completion; setup Router для fallbacks; callbacks для cost calc (e.g., cost = tokens * model_price + markup).
- **billing_service.py**: Async funcs для get_balance, update_balance (with transaction logic).

### Middleware
- **auth.py**: JWT decode с jose; integrate Supabase JWKS if needed.
- **rate_limit.py**: Limiter(key_func=get_user_id_from_jwt, storage_uri="redis://...").

### Utils и Monitoring
- Custom logging: JSON format для cloud logs.
- Callbacks: LiteLLM success/failure hooks для tracing.

## Безопасность
- **Auth**: JWT only; no sessions.
- **Data Security**: RLS; encrypt secrets in Vault.
- **Rate Limiting**: Prevent DDoS/abuse.
- **Compliance**: Audit logs in transactions table; FZ-152 via Yandex hosting.
- **Vulnerabilities**: OWASP top 10 mitigated (e.g., input validation via Pydantic).

## Деплой и CI/CD
- **Dockerfile**: Multi-stage (build deps separate).
- **Kubernetes**: Deployment с replicas=3, HPA для auto-scaling.
- **CI/CD**: GitHub Actions — on push: lint (black), test (pytest --cov), build Docker, deploy to Yandex if main branch.
- **Env Management**: Secrets via K8s Secrets; .env for local.

## Тестирование
- **Unit**: Mock LiteLLM/Supabase; coverage >90% for services.
- **Integration**: FastAPI TestClient; real Supabase test instance.
- **Load**: Locust scripts для 1000 concurrent users.
- **E2E**: Postman collections для full flows.
