# Scripts

Эта папка содержит вспомогательные скрипты для разработки и поддержания проекта LLM Gateway.

## 📁 Содержание

### 🔍 `check_documentation.py`
Проверяет соответствие документации реальному коду проекта.

**Проверяет:**
- API endpoints в коде vs документации
- Поддерживаемые модели в коде vs документации
- Переменные окружения в коде vs env.example
- Структуру файлов проекта

**Использование:**
```bash
python scripts/check_documentation.py
```

### 🧹 `clean_project.py`
Очищает проект от временных файлов и кэша.

**Удаляет:**
- Временные файлы (*.tmp, *.log, *.pid, etc.)
- Кэш директории (__pycache__, .pytest_cache, etc.)
- Дублирующиеся файлы
- Файлы IDE (.vscode, .idea, etc.)

**Использование:**
```bash
# Показать что будет удалено (dry run)
python scripts/clean_project.py --dry-run

# Выполнить очистку
python scripts/clean_project.py
```

### 🚀 `pre_commit_hook.py`
Pre-commit hook для автоматической проверки перед коммитами.

**Выполняет:**
- Проверку документации
- Запуск тестов
- Линтинг кода
- Проверку форматирования

**Использование:**
```bash
python scripts/pre_commit_hook.py
```

## 🔧 Интеграция

### Pre-commit hooks
Скрипты интегрированы в pre-commit hooks через `.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: check-documentation
      name: Check Documentation
      entry: python scripts/check_documentation.py
      language: python
      files: ^(app/|docs/|README\.md|env\.example)
```

### Makefile
Добавлены команды в Makefile:

```makefile
check-docs: ## Check documentation consistency
	python scripts/check_documentation.py

clean: ## Clean up cache and temporary files
	python scripts/clean_project.py --dry-run

clean-force: ## Force clean up cache and temporary files
	python scripts/clean_project.py
```

## 📋 Рекомендации по использованию

### Для разработчиков
1. **Перед коммитом**: Запустите `make check-docs` для проверки документации
2. **Периодически**: Запускайте `make clean` для очистки проекта
3. **При проблемах**: Используйте `python scripts/check_documentation.py` для диагностики

### Для CI/CD
1. **Включите проверку документации** в pipeline
2. **Используйте pre-commit hooks** для автоматической проверки
3. **Добавьте очистку** в build процесс

### Для поддержания актуальности
1. **Обновляйте документацию** при изменении кода
2. **Запускайте проверки** регулярно
3. **Исправляйте найденные несоответствия** сразу

## 🐛 Устранение неполадок

### Проблемы с проверкой документации
```bash
# Запустите детальную проверку
python scripts/check_documentation.py

# Проверьте конкретные файлы
python scripts/check_documentation.py --verbose
```

### Проблемы с очисткой
```bash
# Сначала посмотрите что будет удалено
python scripts/clean_project.py --dry-run

# Затем выполните очистку
python scripts/clean_project.py
```

## 📝 Добавление новых скриптов

При добавлении новых скриптов:

1. **Создайте файл** в папке `scripts/`
2. **Добавьте описание** в этот README.md
3. **Интегрируйте** в Makefile если нужно
4. **Добавьте в pre-commit** если это проверка
5. **Обновите .gitignore** если скрипт создает временные файлы