# LLM Gateway - Документация

Добро пожаловать в документацию проекта LLM Gateway!

## 📚 Содержание документации

📋 **[Полное оглавление](INDEX.md)** - Поиск по всем разделам документации  
🧭 **[Навигация](NAVIGATION.md)** - Этот файл

### 🚀 Быстрый старт
- **[QUICKSTART.md](QUICKSTART.md)** - Быстрый старт за 5 минут
- **[DOCUMENTATION.md](DOCUMENTATION.md)** - Полная документация проекта

### 🔌 API и интеграция
- **[API_REFERENCE.md](API_REFERENCE.md)** - Подробный API Reference с примерами

### 🚀 Развертывание и разработка
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Полное руководство по развертыванию
- **[DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)** - Руководство по разработке

## 🎯 Что такое LLM Gateway?

LLM Gateway — это унифицированный API-шлюз для взаимодействия с различными провайдерами Large Language Models (LLM). Проект предоставляет единый интерфейс для работы с моделями от OpenAI, Anthropic, Google и других провайдеров.

### Основные возможности

- **Унифицированный API**: Единый интерфейс для всех LLM провайдеров
- **Биллинг и учет**: Система учета использования и списания средств
- **Rate Limiting**: Ограничение частоты запросов на пользователя и глобально
- **Мониторинг**: Интеграция с Prometheus, Sentry и Langfuse
- **Отказоустойчивость**: Circuit breaker и retry механизмы (временно отключены для стабильности)
- **Кэширование**: Redis и in-memory кэширование
- **Безопасность**: JWT аутентификация и валидация входных данных

### Поддерживаемые модели

- **OpenAI**: gpt-4, gpt-3.5-turbo
- **Anthropic**: claude-3
- **Google**: gemini-1.5-pro

## 🛠️ Технологический стек

- **Backend**: FastAPI (Python 3.8+)
- **LLM Integration**: LiteLLM
- **Database**: PostgreSQL (Supabase)
- **Cache**: Redis
- **Authentication**: JWT
- **Monitoring**: Prometheus, Sentry, Langfuse
- **Containerization**: Docker & Docker Compose
- **Load Balancing**: Nginx
- **Process Management**: Gunicorn (production)

## 📖 Как использовать документацию

### Для новичков
1. Начните с **[QUICKSTART.md](QUICKSTART.md)** для быстрого старта
2. Изучите **[DOCUMENTATION.md](DOCUMENTATION.md)** для полного понимания

### Для разработчиков
1. Прочитайте **[DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)** для настройки среды разработки
2. Изучите **[API_REFERENCE.md](API_REFERENCE.md)** для интеграции

### Для DevOps
1. Используйте **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** для развертывания
2. Обратитесь к **[DOCUMENTATION.md](DOCUMENTATION.md)** для мониторинга и безопасности

## 🔗 Полезные ссылки

- [Основной README](../README.md) - Обзор проекта
- [GitHub Repository](https://github.com/your-username/llm-gateway) - Исходный код
- [Issues](https://github.com/your-username/llm-gateway/issues) - Сообщить о проблеме
- [Discussions](https://github.com/your-username/llm-gateway/discussions) - Обсуждения

## 📝 Вклад в документацию

Если вы нашли ошибку в документации или хотите добавить что-то новое:

1. Создайте issue с описанием проблемы
2. Сделайте fork репозитория
3. Внесите изменения в документацию
4. Создайте Pull Request

## 📄 Лицензия

Документация распространяется под той же лицензией, что и проект - MIT License.

---

**Версия документации**: 1.0.0  
**Последнее обновление**: 2024-01-15  
**Соответствует коду**: Да