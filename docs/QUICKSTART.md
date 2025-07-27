# LLM Gateway - Быстрый старт

## 🚀 За 5 минут

### 1. Клонирование и настройка

```bash
# Клонируйте репозиторий
git clone <your-repo-url>
cd llm-gateway

# Скопируйте и настройте переменные окружения
cp env.example .env
```

### 2. Настройка .env файла

Отредактируйте `.env` файл, добавив ваши API ключи:

```bash
# Обязательные настройки
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here

# API ключи (хотя бы один)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_GEMINI_API_KEY=your_google_gemini_api_key_here
GOOGLE_API_KEY=your_google_api_key_here  # Дополнительный Google API ключ

# JWT секрет
JWT_SECRET_KEY=your_jwt_secret_key_here
```

### 3. Запуск с Docker

```bash
# Запуск всех сервисов
docker-compose -f deployments/docker-compose.yml up -d

# Проверка статуса
docker-compose -f deployments/docker-compose.yml ps
```

### 4. Проверка работы

```bash
# Health check
curl http://localhost:8000/health

# Получение списка моделей
curl -H "Authorization: Bearer your-jwt-token" \
     http://localhost:8000/v1/models
```

### 5. Первый запрос

```bash
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
```

## 📋 Что дальше?

- 📖 [Полная документация](DOCUMENTATION.md)
- 🔌 [API Reference](API_REFERENCE.md)
- 🚀 [Руководство по развертыванию](DEPLOYMENT_GUIDE.md)
- 🛠️ [Руководство по разработке](DEVELOPMENT_GUIDE.md)

## 🆘 Нужна помощь?

1. Проверьте логи: `docker-compose logs llm-gateway`
2. Проверьте health endpoint: `curl http://localhost:8000/health`
3. Создайте issue в репозитории

---

**Время настройки**: ~5 минут  
**Версия**: 1.0.0