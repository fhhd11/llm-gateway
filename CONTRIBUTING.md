# 🤝 Руководство по контрибьюции в LLM Gateway

Спасибо за интерес к проекту LLM Gateway! Мы приветствуем вклад от сообщества.

## 🚀 Быстрый старт

### 1. Fork и клонирование

```bash
# Fork репозитория на GitHub
# Затем клонируйте ваш fork
git clone https://github.com/your-username/llm-gateway.git
cd llm-gateway

# Добавьте upstream репозиторий
git remote add upstream https://github.com/original-owner/llm-gateway.git
```

### 2. Настройка окружения

```bash
# Установите зависимости
make setup

# Настройте переменные окружения
cp env.example .env
# Отредактируйте .env файл
```

### 3. Создание feature branch

```bash
# Создайте новую ветку
git checkout -b feature/your-feature-name

# Или для исправления багов
git checkout -b fix/bug-description
```

## 📝 Процесс разработки

### 1. Внесение изменений

- Пишите чистый, читаемый код
- Следуйте существующим соглашениям по именованию
- Добавляйте комментарии к сложной логике
- Обновляйте документацию при необходимости

### 2. Тестирование

```bash
# Запустите все тесты
make test

# Проверьте покрытие
make test-cov

# Запустите линтинг
make lint

# Форматирование кода
make format
```

### 3. Commit сообщения

Используйте [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new endpoint for user management
fix: resolve authentication issue
docs: update API documentation
test: add unit tests for billing service
refactor: simplify configuration loading
style: format code according to style guide
perf: optimize database queries
ci: update GitHub Actions workflow
```

### 4. Push и Pull Request

```bash
# Push ваши изменения
git push origin feature/your-feature-name

# Создайте Pull Request на GitHub
```

## 📋 Стандарты кода

### Python

- **Python 3.11+**
- **Black** для форматирования
- **isort** для сортировки импортов
- **flake8** для линтинга
- **mypy** для статической типизации

### Структура кода

```python
"""
Module docstring.
"""
import os
from typing import Dict, List, Optional

from app.config import get_settings
from app.models.schemas import YourModel


class YourClass:
    """Class docstring."""
    
    def __init__(self, param: str):
        """Initialize the class."""
        self.param = param
    
    def your_method(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Method docstring.
        
        Args:
            data: Input data
            
        Returns:
            Processed result or None
        """
        # Implementation
        pass
```

### Тестирование

- Покрытие кода должно быть не менее 80%
- Каждая новая функция должна иметь тесты
- Используйте моки для внешних зависимостей
- Группируйте связанные тесты в классы

### Документация

- Обновляйте README.md при изменении API
- Добавляйте docstrings к функциям и классам
- Обновляйте примеры кода
- Документируйте breaking changes

## 🔍 Code Review

### Что проверяется

- **Функциональность**: код работает как ожидается
- **Тестирование**: адекватное покрытие тестами
- **Производительность**: нет очевидных проблем с производительностью
- **Безопасность**: нет уязвимостей безопасности
- **Документация**: обновлена при необходимости
- **Стиль кода**: соответствует стандартам проекта

### Процесс review

1. **Автоматические проверки** должны пройти
2. **Code review** от maintainer'ов
3. **Тесты** должны проходить
4. **Документация** должна быть обновлена

## 🐛 Сообщение о багах

### Создание issue

При создании issue укажите:

1. **Краткое описание** проблемы
2. **Шаги для воспроизведения**
3. **Ожидаемое поведение**
4. **Фактическое поведение**
5. **Версия** проекта
6. **Окружение** (OS, Python версия, etc.)
7. **Логи** ошибок (если есть)

### Пример issue

```markdown
## Описание
При попытке аутентификации возникает ошибка 500.

## Шаги для воспроизведения
1. Отправьте POST запрос на /v1/chat/completions
2. Используйте невалидный JWT токен
3. Получите ошибку 500 вместо 401

## Ожидаемое поведение
Должна возвращаться ошибка 401 Unauthorized.

## Фактическое поведение
Возвращается ошибка 500 Internal Server Error.

## Версия
v1.2.0

## Окружение
- OS: Ubuntu 20.04
- Python: 3.11.0
- Docker: 20.10.0
```

## 💡 Предложение новых функций

### Создание feature request

1. **Проверьте существующие issues** - возможно, функция уже запрошена
2. **Опишите проблему** - что вы пытаетесь решить
3. **Предложите решение** - как это можно реализовать
4. **Обсудите альтернативы** - другие способы решения
5. **Оцените сложность** - насколько сложно реализовать

### Пример feature request

```markdown
## Проблема
Нужна возможность экспорта логов в различные форматы.

## Предлагаемое решение
Добавить endpoint /admin/logs/export с параметрами:
- format: json, csv, xml
- date_from: ISO date
- date_to: ISO date
- level: INFO, WARNING, ERROR

## Альтернативы
1. Использовать существующий /metrics endpoint
2. Добавить webhook для отправки логов

## Сложность
Средняя - требует изменения логирования и добавления новых endpoints.
```

## 🚀 Запуск проекта

### Локальная разработка

```bash
# Установка зависимостей
make setup

# Запуск в режиме разработки
make dev

# Запуск тестов
make test

# Проверка кода
make check
```

### Docker разработка

```bash
# Сборка образа
make docker-build

# Запуск
make docker-run

# Логи
make docker-logs
```

## 📚 Полезные ресурсы

### Документация

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Docker Documentation](https://docs.docker.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)

### Инструменты

- **Black**: `black app/ tests/`
- **isort**: `isort app/ tests/`
- **flake8**: `flake8 app/ tests/`
- **mypy**: `mypy app/`

## 🏷️ Labels для issues

- `bug` - Ошибка в коде
- `enhancement` - Улучшение существующей функции
- `feature` - Новая функция
- `documentation` - Улучшение документации
- `good first issue` - Хорошо для новичков
- `help wanted` - Нужна помощь
- `priority: high` - Высокий приоритет
- `priority: low` - Низкий приоритет

## 📞 Получение помощи

### Каналы поддержки

1. **GitHub Issues** - для багов и feature requests
2. **GitHub Discussions** - для общих вопросов
3. **Pull Request** - для предложений изменений

### Перед обращением за помощью

1. **Проверьте документацию** - возможно, ответ уже есть
2. **Поищите в issues** - возможно, проблема уже обсуждалась
3. **Попробуйте воспроизвести** - убедитесь, что проблема воспроизводится
4. **Подготовьте минимальный пример** - упростите проблему

## 🎉 Признание вклада

Все значимые вклады будут отмечены в:

- **README.md** - список контрибьюторов
- **Release notes** - упоминание в релизах
- **GitHub** - автоматическое добавление в contributors

## 📄 Лицензия

Внося изменения в проект, вы соглашаетесь с тем, что ваш вклад будет лицензирован под той же лицензией, что и проект (MIT License).

---

**Спасибо за ваш вклад в LLM Gateway! 🚀** 