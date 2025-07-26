# 🚀 Руководство по развертыванию LLM Gateway

## 📋 Быстрый старт

### 1. Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Перезагрузка для применения изменений
sudo reboot
```

### 2. Настройка проекта

```bash
# Клонирование репозитория
git clone <your-repo-url>
cd llm-gateway

# Настройка переменных окружения
cp env.example .env
nano .env  # Отредактируйте с вашими настройками
```

### 3. Запуск

```bash
# Запуск продакшн сервисов
chmod +x deployments/start.sh
./deployments/start.sh

# Проверка статуса
docker-compose -f deployments/docker-compose.prod.yml ps
```

## ⚙️ Конфигурация

### Обязательные переменные окружения

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# JWT
JWT_SECRET_KEY=your_strong_secret_key

# API ключи
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
GOOGLE_GEMINI_API_KEY=your-gemini-key

# Redis
REDIS_URL=redis://localhost:6379/0
```

### Опциональные настройки

```bash
# Rate limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_REQUESTS_PER_HOUR=1000

# Мониторинг
PROMETHEUS_ENABLED=true
LANGFUSE_ENABLED=false

# Логирование
LOG_LEVEL=INFO
```

## 🐳 Docker развертывание

### Локальная разработка

```bash
# Запуск
docker-compose -f deployments/docker-compose.yml up -d

# Логи
docker-compose -f deployments/docker-compose.yml logs -f

# Остановка
docker-compose -f deployments/docker-compose.yml down
```

### Продакшн

```bash
# Запуск
docker-compose -f deployments/docker-compose.prod.yml up -d

# Логи
docker-compose -f deployments/docker-compose.prod.yml logs -f

# Остановка
docker-compose -f deployments/docker-compose.prod.yml down
```

### Мониторинг

```bash
# Запуск мониторинга
docker-compose -f deployments/docker-compose.monitoring.yml up -d

# Доступ к Grafana: http://your-server:3000 (admin/admin)
# Доступ к Prometheus: http://your-server:9090
```

## 🔒 Безопасность

### Настройка файрвола

```bash
# Установка UFW
sudo apt install ufw

# Настройка правил
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp  # LLM Gateway
sudo ufw allow 3000/tcp  # Grafana
sudo ufw allow 9090/tcp  # Prometheus

# Включение файрвола
sudo ufw enable
```

### SSL сертификаты

```bash
# Установка Certbot
sudo apt install certbot

# Получение сертификата
sudo certbot certonly --standalone -d your-domain.com

# Автоматическое обновление
sudo crontab -e
# Добавьте: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 📊 Мониторинг

### Health checks

```bash
# Проверка здоровья
curl http://localhost:8000/health

# Детальная проверка
curl http://localhost:8000/health/detailed

# Метрики
curl http://localhost:8000/metrics
```

### Логирование

```bash
# Просмотр логов
docker-compose -f deployments/docker-compose.prod.yml logs -f llm-gateway

# Фильтрация ошибок
docker-compose -f deployments/docker-compose.prod.yml logs -f llm-gateway | grep ERROR
```

### Алерты

Настройте алерты в Prometheus для:
- Высокой нагрузки
- Ошибок API
- Проблем с базой данных
- Исчерпания ресурсов

## 🔧 Управление сервисом

### Systemd сервис

```bash
# Копирование сервиса
sudo cp deployments/llm-gateway.service /etc/systemd/system/

# Включение автозапуска
sudo systemctl enable llm-gateway

# Запуск
sudo systemctl start llm-gateway

# Статус
sudo systemctl status llm-gateway

# Остановка
sudo systemctl stop llm-gateway
```

### Скрипты управления

```bash
# Запуск
./deployments/start.sh

# Остановка
./deployments/stop.sh

# Бэкап
./deployments/backup.sh

# Мониторинг здоровья
./deployments/health-monitor.sh
```

## 📈 Масштабирование

### Горизонтальное масштабирование

```bash
# Увеличение количества реплик
docker-compose -f deployments/docker-compose.prod.yml up -d --scale llm-gateway=3
```

### Kubernetes

```bash
# Применение манифестов
kubectl apply -f deployments/k8s/

# Проверка статуса
kubectl get pods
kubectl get services
```

## 🔄 Обновления

### Обновление приложения

```bash
# Остановка сервисов
./deployments/stop.sh

# Обновление кода
git pull origin main

# Пересборка образов
docker-compose -f deployments/docker-compose.prod.yml build

# Запуск
./deployments/start.sh
```

### Откат

```bash
# Откат к предыдущей версии
git checkout <previous-commit>
./deployments/stop.sh
docker-compose -f deployments/docker-compose.prod.yml build
./deployments/start.sh
```

## 🛠️ Устранение неполадок

### Проверка логов

```bash
# Логи приложения
docker-compose -f deployments/docker-compose.prod.yml logs llm-gateway

# Логи базы данных
docker-compose -f deployments/docker-compose.prod.yml logs postgres

# Логи Redis
docker-compose -f deployments/docker-compose.prod.yml logs redis
```

### Проверка ресурсов

```bash
# Использование CPU и памяти
docker stats

# Дисковое пространство
df -h

# Сетевые соединения
netstat -tulpn
```

### Перезапуск сервисов

```bash
# Перезапуск конкретного сервиса
docker-compose -f deployments/docker-compose.prod.yml restart llm-gateway

# Перезапуск всех сервисов
docker-compose -f deployments/docker-compose.prod.yml restart
```

## 📚 Полезные команды

```bash
# Статус всех контейнеров
docker-compose -f deployments/docker-compose.prod.yml ps

# Просмотр конфигурации
docker-compose -f deployments/docker-compose.prod.yml config

# Очистка неиспользуемых ресурсов
docker system prune -a

# Бэкап базы данных
docker-compose -f deployments/docker-compose.prod.yml exec postgres pg_dump -U postgres > backup.sql
```

## 🆘 Поддержка

При возникновении проблем:

1. **Проверьте логи**: `docker-compose logs -f llm-gateway`
2. **Проверьте здоровье**: `curl http://localhost:8000/health`
3. **Проверьте ресурсы**: `docker stats`
4. **Создайте issue** в репозитории

## 🔗 Полезные ссылки

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Nginx Documentation](https://nginx.org/en/docs/) 