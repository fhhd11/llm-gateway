# LLM Gateway - API Reference

## 📋 Содержание

1. [Обзор API](#обзор-api)
2. [Аутентификация](#аутентификация)
3. [Endpoints](#endpoints)
4. [Модели данных](#модели-данных)
5. [Коды ошибок](#коды-ошибок)
6. [Rate Limiting](#rate-limiting)
7. [Примеры запросов](#примеры-запросов)

## 🎯 Обзор API

### Базовый URL
```
http://localhost:8000
```

### Версионирование
API использует версионирование в URL: `/v1/`

### Формат ответов
Все ответы возвращаются в формате JSON с кодировкой UTF-8.

### Content-Type
- **Запросы**: `application/json`
- **Ответы**: `application/json`
- **Потоковые ответы**: `text/plain` (Server-Sent Events)

## 🔐 Аутентификация

### JWT токены

Все API endpoints требуют JWT токен в заголовке:

```
Authorization: Bearer <your-jwt-token>
```

### Получение токена

Токены должны быть получены через вашу систему аутентификации. LLM Gateway не предоставляет endpoints для генерации токенов.

### Время жизни токена

Настраивается через переменную окружения:
```bash
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Пример заголовков

```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
     -H "Content-Type: application/json" \
     http://localhost:8000/v1/models
```

## 📡 Endpoints

### Chat Completions

#### POST /v1/chat/completions

Генерирует завершение чата с использованием LLM модели.

**Запрос:**
```json
{
  "model": "gpt-3.5-turbo",
  "messages": [
    {
      "role": "system",
      "content": "Ты полезный ассистент."
    },
    {
      "role": "user",
      "content": "Привет, как дела?"
    }
  ],
  "stream": false,
  "max_tokens": 1000,
  "temperature": 0.7,
  "top_p": 1.0,
  "frequency_penalty": 0.0,
  "presence_penalty": 0.0
}
```

**Параметры:**
- `model` (string, required): ID модели для использования
- `messages` (array, required): Массив сообщений в формате chat
- `stream` (boolean, optional): Включить потоковый ответ (по умолчанию false)
- `max_tokens` (integer, optional): Максимальное количество токенов в ответе
- `temperature` (float, optional): Температура для генерации (0.0-2.0)
- `top_p` (float, optional): Top-p sampling (0.0-1.0)
- `frequency_penalty` (float, optional): Штраф за частоту (-2.0-2.0)
- `presence_penalty` (float, optional): Штраф за присутствие (-2.0-2.0)

**Ответ:**
```json
{
  "id": "chatcmpl-1234567890abcdef",
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
    "prompt_tokens": 15,
    "completion_tokens": 12,
    "total_tokens": 27
  }
}
```

#### POST /v1/chat/completions/stream

Потоковая версия chat completions. Возвращает Server-Sent Events.

**Запрос:** Аналогично обычному endpoint, но с `"stream": true`

**Ответ:** Поток событий в формате:
```
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"gpt-3.5-turbo","choices":[{"index":0,"delta":{"role":"assistant","content":"Привет"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"gpt-3.5-turbo","choices":[{"index":0,"delta":{"content":"! У меня все хорошо"},"finish_reason":null}]}

data: [DONE]
```

### Models

#### GET /v1/models

Возвращает список доступных моделей.

**Запрос:** Без параметров

**Ответ:**
```json
[
  {
    "id": "gpt-3.5-turbo",
    "object": "model",
    "created": 1677652288,
    "owned_by": "openai",
    "permission": [
      {
        "id": "modelperm-0",
        "object": "model_permission",
        "created": 1677652288,
        "allow_create_engine": false,
        "allow_sampling": true,
        "allow_logprobs": true,
        "allow_search_indices": false,
        "allow_view": true,
        "allow_fine_tuning": false,
        "organization": "*",
        "group": null,
        "is_blocking": false
      }
    ],
    "root": "gpt-3.5-turbo",
    "parent": null
  },
  {
    "id": "gpt-4",
    "object": "model",
    "created": 1677652288,
    "owned_by": "openai",
    "permission": [...],
    "root": "gpt-4",
    "parent": null
  },
  {
    "id": "claude-3",
    "object": "model",
    "created": 1677652288,
    "owned_by": "anthropic",
    "permission": [...],
    "root": "claude-3",
    "parent": null
  },
  {
    "id": "gemini-1.5-pro",
    "object": "model",
    "created": 1677652288,
    "owned_by": "google",
    "permission": [...],
    "root": "gemini-1.5-pro",
    "parent": null
  }
]
```

### Billing

#### GET /billing/balance

Возвращает текущий баланс пользователя.

**Запрос:** Без параметров

**Ответ:**
```json
{
  "user_id": "user123",
  "balance": 95.50
}
```

#### GET /billing/transactions

Возвращает историю транзакций пользователя.

**Параметры:**
- `limit` (integer, optional): Количество транзакций (по умолчанию 10, максимум 100)
- `offset` (integer, optional): Смещение для пагинации (по умолчанию 0)

**Запрос:**
```bash
GET /billing/transactions?limit=5&offset=0
```

**Ответ:**
```json
{
  "user_id": "user123",
  "transactions": [
    {
      "id": "txn_1234567890",
      "user_id": "user123",
      "amount": -0.002,
      "description": "Chat completion with gpt-3.5-turbo",
      "timestamp": "2024-01-15T10:30:00Z",
      "balance_after": 95.498
    },
    {
      "id": "txn_1234567891",
      "user_id": "user123",
      "amount": 100.0,
      "description": "Initial balance",
      "timestamp": "2024-01-15T09:00:00Z",
      "balance_after": 95.5
    }
  ],
  "limit": 5,
  "offset": 0,
  "total": 2
}
```

### Health Checks

#### GET /health

Основной health check endpoint.

**Ответ:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "environment": "production",
  "components": {
    "database": "healthy",
    "redis": "healthy",
    "llm_services": "healthy"
  },
  "rate_limit_storage": "redis",
  "retry_enabled": true,
  "circuit_breaker_enabled": true
}
```

#### GET /health/detailed

Детальный health check с информацией о каждом компоненте.

**Ответ:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "components": {
    "database": {
      "status": "healthy",
      "message": "Database connection successful",
      "details": {
        "connection_pool_size": 5,
        "active_connections": 2
      },
      "duration_ms": 15.2
    },
    "redis": {
      "status": "healthy",
      "message": "Redis connection successful",
      "details": {
        "connected": true,
        "memory_usage": "2.5MB"
      },
      "duration_ms": 5.1
    },
    "llm_services": {
      "status": "healthy",
      "message": "All LLM services operational",
      "details": {
        "gpt-3.5-turbo": "healthy",
        "gpt-4": "healthy",
        "claude-3": "healthy",
        "gemini-1.5-pro": "healthy"
      },
      "duration_ms": 1250.8
    }
  }
}
```

#### GET /health/circuit-breakers

Статус circuit breakers для всех LLM сервисов.

#### GET /health/monitoring

Статус систем мониторинга (Prometheus, Sentry, Langfuse).

**Ответ:**
```json
{
  "langfuse": {
    "status": "healthy",
    "enabled": true,
    "host": "https://cloud.langfuse.com"
  },
  "prometheus": {
    "status": "healthy",
    "enabled": true
  },
  "sentry": {
    "status": "healthy",
    "enabled": true
  }
}
```

**Ответ:**
```json
{
  "circuit_breakers": {
    "gpt-3.5-turbo": {
      "state": "closed",
      "failure_count": 0,
      "last_failure_time": null,
      "failure_threshold": 5,
      "recovery_timeout": 60
    },
    "gpt-4": {
      "state": "closed",
      "failure_count": 0,
      "last_failure_time": null,
      "failure_threshold": 5,
      "recovery_timeout": 60
    }
  },
  "retry_config": {
    "enabled": true,
    "max_attempts": 3,
    "base_delay": 1.0,
    "max_delay": 60.0,
    "exponential_base": 2.0,
    "jitter": true
  },
  "circuit_breaker_config": {
    "enabled": true,
    "failure_threshold": 5,
    "recovery_timeout": 60
  }
}
```

#### GET /health/system

Проверка системных ресурсов.

**Ответ:**
```json
{
  "status": "healthy",
  "message": "System resources are normal",
  "details": {
    "cpu_usage_percent": 15.2,
    "memory_usage_percent": 45.8,
    "disk_usage_percent": 23.1,
    "network_connections": 125
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "duration_ms": 12.5
}
```

#### GET /health/history

История последних health checks.

**Ответ:**
```json
{
  "history": [
    {
      "name": "database",
      "status": "healthy",
      "message": "Database connection successful",
      "timestamp": "2024-01-15T10:30:00Z",
      "duration_ms": 15.2
    },
    {
      "name": "redis",
      "status": "healthy",
      "message": "Redis connection successful",
      "timestamp": "2024-01-15T10:30:00Z",
      "duration_ms": 5.1
    }
  ],
  "total_checks": 25
}
```

#### GET /ready

Readiness probe для Kubernetes.

**Ответ:**
```json
{
  "ready": true,
  "timestamp": "2024-01-15T10:30:00Z",
  "checks": {
    "database": true,
    "redis": true,
    "llm_services": true
  }
}
```

#### GET /metrics

Prometheus метрики.

**Ответ:**
```
# HELP llm_requests_total Total number of LLM requests
# TYPE llm_requests_total counter
llm_requests_total{model="gpt-3.5-turbo",status="success"} 1250
llm_requests_total{model="gpt-4",status="success"} 450
llm_requests_total{model="gpt-3.5-turbo",status="error"} 12

# HELP llm_requests_duration_seconds Duration of LLM requests
# TYPE llm_requests_duration_seconds histogram
llm_requests_duration_seconds_bucket{model="gpt-3.5-turbo",le="0.1"} 100
llm_requests_duration_seconds_bucket{model="gpt-3.5-turbo",le="0.5"} 800
llm_requests_duration_seconds_bucket{model="gpt-3.5-turbo",le="1.0"} 1200

# HELP user_balance Current user balance
# TYPE user_balance gauge
user_balance{user_id="user123"} 95.50

# HELP rate_limit_requests_total Total number of rate limit events
# TYPE rate_limit_requests_total counter
rate_limit_requests_total{type="user_limit"} 5
rate_limit_requests_total{type="global_limit"} 2
```

## 📊 Модели данных

### ChatMessage

```json
{
  "role": "user|assistant|system",
  "content": "Текст сообщения"
}
```

### ChatCompletionRequest

```json
{
  "model": "string",
  "messages": ["ChatMessage"],
  "stream": "boolean",
  "max_tokens": "integer",
  "temperature": "float",
  "top_p": "float",
  "frequency_penalty": "float",
  "presence_penalty": "float"
}
```

### ChatCompletionResponse

```json
{
  "id": "string",
  "object": "chat.completion",
  "created": "integer",
  "model": "string",
  "choices": [
    {
      "index": "integer",
      "message": {
        "role": "assistant",
        "content": "string",
        "tool_calls": "array",
        "function_call": "object"
      },
      "finish_reason": "string"
    }
  ],
  "usage": {
    "prompt_tokens": "integer",
    "completion_tokens": "integer",
    "total_tokens": "integer"
  }
}
```

### ModelInfo

```json
{
  "id": "string",
  "object": "model",
  "created": "integer",
  "owned_by": "string",
  "permission": ["ModelPermission"],
  "root": "string",
  "parent": "string"
}
```

### Transaction

```json
{
  "id": "string",
  "user_id": "string",
  "amount": "float",
  "description": "string",
  "timestamp": "string",
  "balance_after": "float"
}
```

## ❌ Коды ошибок

### HTTP статус коды

- `200 OK` - Успешный запрос
- `400 Bad Request` - Неверный запрос
- `401 Unauthorized` - Не авторизован
- `403 Forbidden` - Доступ запрещен
- `404 Not Found` - Ресурс не найден
- `429 Too Many Requests` - Превышен лимит запросов
- `500 Internal Server Error` - Внутренняя ошибка сервера
- `503 Service Unavailable` - Сервис недоступен

### Формат ошибок

```json
{
  "detail": "Описание ошибки",
  "code": 400,
  "error_type": "validation_error"
}
```

### Типичные ошибки

#### 401 Unauthorized
```json
{
  "detail": "Invalid or missing authentication token",
  "code": 401,
  "error_type": "authentication_error"
}
```

#### 429 Too Many Requests
```json
{
  "detail": "Rate limit exceeded. Try again in 60 seconds.",
  "code": 429,
  "error_type": "rate_limit_error"
}
```

#### 503 Service Unavailable
```json
{
  "detail": "LLM service temporarily unavailable",
  "code": 503,
  "error_type": "service_error"
}
```

## 🚦 Rate Limiting

### Лимиты

- **Per-user**: 60 запросов в минуту
- **Global**: 1000 запросов в час
- **Настраиваемые**: Через переменные окружения

### Заголовки ответа

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1642234567
```

### Обработка превышения лимита

При превышении лимита возвращается:
- HTTP статус: `429 Too Many Requests`
- Retry-After заголовок с временем ожидания
- JSON ответ с описанием ошибки

## 💡 Примеры запросов

### Python

```python
import requests
import json

BASE_URL = "http://localhost:8000"
API_TOKEN = "your-jwt-token"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# Получение моделей
response = requests.get(f"{BASE_URL}/v1/models", headers=headers)
models = response.json()
print("Модели:", [m["id"] for m in models])

# Chat completion
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

if response.status_code == 200:
    result = response.json()
    print("Ответ:", result["choices"][0]["message"]["content"])
else:
    print("Ошибка:", response.json())
```

### JavaScript

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
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

// Chat completion
async function chatCompletion(messages) {
    const data = {
        model: 'gpt-3.5-turbo',
        messages,
        stream: false
    };

    const response = await fetch(`${BASE_URL}/v1/chat/completions`, {
        method: 'POST',
        headers,
        body: JSON.stringify(data)
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail);
    }

    return await response.json();
}

// Потоковая генерация
async function streamChatCompletion(messages, onChunk) {
    const data = {
        model: 'gpt-3.5-turbo',
        messages,
        stream: true
    };

    const response = await fetch(`${BASE_URL}/v1/chat/completions/stream`, {
        method: 'POST',
        headers,
        body: JSON.stringify(data)
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail);
    }

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
                        onChunk(parsed.choices[0].delta.content);
                    }
                } catch (e) {
                    // Игнорируем ошибки парсинга
                }
            }
        }
    }
}

// Использование
(async () => {
    try {
        const models = await getModels();
        console.log('Доступные модели:', models.map(m => m.id));

        const result = await chatCompletion([
            { role: 'user', content: 'Привет!' }
        ]);
        console.log('Ответ:', result.choices[0].message.content);

        // Потоковая генерация
        await streamChatCompletion(
            [{ role: 'user', content: 'Расскажи историю' }],
            (chunk) => process.stdout.write(chunk)
        );
    } catch (error) {
        console.error('Ошибка:', error.message);
    }
})();
```

### cURL

```bash
# Получение моделей
curl -H "Authorization: Bearer your-jwt-token" \
     http://localhost:8000/v1/models

# Chat completion
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

### Go

```go
package main

import (
    "bytes"
    "encoding/json"
    "fmt"
    "io"
    "net/http"
)

const (
    BaseURL   = "http://localhost:8000"
    APIToken  = "your-jwt-token"
)

type ChatMessage struct {
    Role    string `json:"role"`
    Content string `json:"content"`
}

type ChatCompletionRequest struct {
    Model    string        `json:"model"`
    Messages []ChatMessage `json:"messages"`
    Stream   bool          `json:"stream"`
}

type ChatCompletionResponse struct {
    ID      string `json:"id"`
    Object  string `json:"object"`
    Created int64  `json:"created"`
    Model   string `json:"model"`
    Choices []struct {
        Index   int `json:"index"`
        Message struct {
            Role    string `json:"role"`
            Content string `json:"content"`
        } `json:"message"`
        FinishReason string `json:"finish_reason"`
    } `json:"choices"`
    Usage struct {
        PromptTokens     int `json:"prompt_tokens"`
        CompletionTokens int `json:"completion_tokens"`
        TotalTokens      int `json:"total_tokens"`
    } `json:"usage"`
}

func main() {
    // Получение моделей
    models, err := getModels()
    if err != nil {
        fmt.Printf("Ошибка получения моделей: %v\n", err)
        return
    }
    fmt.Printf("Доступные модели: %v\n", models)

    // Chat completion
    request := ChatCompletionRequest{
        Model: "gpt-3.5-turbo",
        Messages: []ChatMessage{
            {Role: "user", Content: "Привет!"},
        },
        Stream: false,
    }

    response, err := chatCompletion(request)
    if err != nil {
        fmt.Printf("Ошибка chat completion: %v\n", err)
        return
    }

    fmt.Printf("Ответ: %s\n", response.Choices[0].Message.Content)
}

func getModels() ([]string, error) {
    req, err := http.NewRequest("GET", BaseURL+"/v1/models", nil)
    if err != nil {
        return nil, err
    }

    req.Header.Set("Authorization", "Bearer "+APIToken)

    client := &http.Client{}
    resp, err := client.Do(req)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()

    var models []map[string]interface{}
    if err := json.NewDecoder(resp.Body).Decode(&models); err != nil {
        return nil, err
    }

    var modelIDs []string
    for _, model := range models {
        if id, ok := model["id"].(string); ok {
            modelIDs = append(modelIDs, id)
        }
    }

    return modelIDs, nil
}

func chatCompletion(request ChatCompletionRequest) (*ChatCompletionResponse, error) {
    jsonData, err := json.Marshal(request)
    if err != nil {
        return nil, err
    }

    req, err := http.NewRequest("POST", BaseURL+"/v1/chat/completions", bytes.NewBuffer(jsonData))
    if err != nil {
        return nil, err
    }

    req.Header.Set("Authorization", "Bearer "+APIToken)
    req.Header.Set("Content-Type", "application/json")

    client := &http.Client{}
    resp, err := client.Do(req)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()

    var response ChatCompletionResponse
    if err := json.NewDecoder(resp.Body).Decode(&response); err != nil {
        return nil, err
    }

    return &response, nil
}
```

---

**Версия API**: 1.0.0  
**Последнее обновление**: 2024-01-15  
**Соответствует коду**: Да