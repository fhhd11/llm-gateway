# LLM Gateway - Руководство по развертыванию

## 📋 Содержание

1. [Требования к системе](#требования-к-системе)
2. [Локальная разработка](#локальная-разработка)
3. [Продакшн развертывание](#продакшн-развертывание)
4. [Docker развертывание](#docker-развертывание)
5. [Kubernetes развертывание](#kubernetes-развертывание)
6. [Мониторинг и логирование](#мониторинг-и-логирование)
7. [Безопасность](#безопасность)
8. [Backup и восстановление](#backup-и-восстановление)
9. [Обновление](#обновление)
10. [Устранение неполадок](#устранение-неполадок)

## 💻 Требования к системе

### Минимальные требования

- **CPU**: 2 ядра
- **RAM**: 4 GB
- **Диск**: 20 GB свободного места
- **ОС**: Linux (Ubuntu 20.04+), macOS, Windows 10+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+

### Рекомендуемые требования

- **CPU**: 4+ ядра
- **RAM**: 8+ GB
- **Диск**: 50+ GB SSD
- **Сеть**: Стабильное интернет-соединение
- **SSL**: Сертификат для HTTPS

### Зависимости

- **Python**: 3.8+
- **PostgreSQL**: 13+ (через Supabase)
- **Redis**: 6.0+
- **Nginx**: 1.18+ (для продакшна)

## 🛠️ Локальная разработка

### 1. Подготовка окружения

```bash
# Клонирование репозитория
git clone <your-repo-url>
cd llm-gateway

# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/macOS
# или
venv\Scripts\activate     # Windows

# Установка зависимостей
pip install -r requirements.txt
pip install -r requirements-dev.txt  # для разработки
```

### 2. Настройка конфигурации

```bash
# Копирование примера конфигурации
cp env.example .env

# Редактирование .env файла
nano .env  # или любой текстовый редактор
```

**Обязательные настройки для разработки:**

```bash
# Основные настройки
HOST=0.0.0.0
PORT=8000
DEBUG=true
LOG_LEVEL=DEBUG
ENVIRONMENT=development

# База данных (Supabase)
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here

# Redis (локальный)
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379

# Аутентификация
JWT_SECRET_KEY=your_jwt_secret_key_here

# API ключи провайдеров (хотя бы один)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_GEMINI_API_KEY=your_google_gemini_api_key_here
```

### 3. Запуск с Docker Compose

```bash
# Запуск всех сервисов
docker-compose -f deployments/docker-compose.yml up -d

# Проверка статуса
docker-compose -f deployments/docker-compose.yml ps

# Просмотр логов
docker-compose -f deployments/docker-compose.yml logs -f llm-gateway
```

### 4. Проверка работы

```bash
# Health check
curl http://localhost:8000/health

# Получение списка моделей
curl -H "Authorization: Bearer your-jwt-token" \
     http://localhost:8000/v1/models

# Тест chat completion
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

### 5. Запуск тестов

```bash
# Установка dev зависимостей
pip install -r requirements-dev.txt

# Запуск тестов
pytest

# Запуск тестов с покрытием
pytest --cov=app --cov-report=html

# Запуск тестов production изменений
python test_production_changes.py
```

## 🚀 Продакшн развертывание

### 1. Подготовка сервера

#### Ubuntu/Debian

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
sudo apt install -y curl wget git unzip software-properties-common apt-transport-https ca-certificates gnupg lsb-release

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

#### CentOS/RHEL

```bash
# Установка Docker
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Запуск Docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

### 2. Настройка файрвола

```bash
# Установка UFW
sudo apt install -y ufw

# Настройка правил
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp  # только для внутреннего доступа

# Включение файрвола
sudo ufw enable
sudo ufw status
```

### 3. Настройка SSL (Let's Encrypt)

```bash
# Установка Certbot
sudo apt install -y certbot python3-certbot-nginx

# Получение сертификата
sudo certbot --nginx -d yourdomain.com

# Автоматическое обновление
sudo crontab -e
# Добавить строку:
# 0 12 * * * /usr/bin/certbot renew --quiet
```

### 4. Развертывание приложения

```bash
# Клонирование репозитория
git clone <your-repo-url>
cd llm-gateway

# Настройка конфигурации
cp env.example .env
nano .env  # настройте все переменные

# Проверка конфигурации
python check_env.py
python test_db_connection.py

# Запуск продакшн сервисов
chmod +x deployments/start.sh
./deployments/start.sh
```

### 5. Настройка systemd сервиса

```bash
# Копирование сервис файла
sudo cp deployments/llm-gateway.service /etc/systemd/system/

# Редактирование пути в сервис файле
sudo nano /etc/systemd/system/llm-gateway.service

# Включение автозапуска
sudo systemctl daemon-reload
sudo systemctl enable llm-gateway
sudo systemctl start llm-gateway

# Проверка статуса
sudo systemctl status llm-gateway
```

## 🐳 Docker развертывание

### Локальная разработка

**Файл**: `deployments/docker-compose.yml`

```yaml
version: '3.8'

services:
  llm-gateway:
    build:
      context: ..
      dockerfile: deployments/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - HOST=0.0.0.0
      - PORT=8000
      - DEBUG=false
      - LOG_LEVEL=INFO
      - REDIS_URL=redis://redis:6379/0
      - RATE_LIMIT_STORAGE=redis
    env_file:
      - ../.env
    depends_on:
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - llm-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    command: redis-server --appendonly yes
    networks:
      - llm-network

volumes:
  redis_data:

networks:
  llm-network:
    driver: bridge
```

### Продакшн развертывание

**Файл**: `deployments/docker-compose.prod.yml`

```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - nginx_logs:/var/log/nginx
    depends_on:
      - llm-gateway
    restart: unless-stopped
    networks:
      - llm-network

  llm-gateway:
    build:
      context: ..
      dockerfile: deployments/Dockerfile
    environment:
      - HOST=0.0.0.0
      - PORT=8000
      - DEBUG=false
      - LOG_LEVEL=INFO
      - REDIS_URL=redis://redis:6379/0
      - RATE_LIMIT_STORAGE=redis
    env_file:
      - ../.env
    depends_on:
      - redis
      - postgres
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - llm-network

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    networks:
      - llm-network

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    networks:
      - llm-network

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    restart: unless-stopped
    networks:
      - llm-network

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana-dashboard.json:/etc/grafana/provisioning/dashboards/dashboard.json:ro
    depends_on:
      - prometheus
    restart: unless-stopped
    networks:
      - llm-network

volumes:
  redis_data:
  postgres_data:
  prometheus_data:
  grafana_data:
  nginx_logs:

networks:
  llm-network:
    driver: bridge
```

### Dockerfile

**Файл**: `deployments/Dockerfile`

```dockerfile
FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Копирование файлов зависимостей
COPY requirements.txt .
COPY pyproject.toml .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY app/ ./app/
COPY config_cli.py .
COPY start_server.py .

# Создание пользователя для безопасности
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Экспорт порта
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Команда запуска
CMD ["python", "start_server.py"]
```

### Запуск и управление

```bash
# Запуск продакшн сервисов
docker-compose -f deployments/docker-compose.prod.yml up -d

# Просмотр логов
docker-compose -f deployments/docker-compose.prod.yml logs -f llm-gateway

# Остановка сервисов
docker-compose -f deployments/docker-compose.prod.yml down

# Перезапуск конкретного сервиса
docker-compose -f deployments/docker-compose.prod.yml restart llm-gateway

# Обновление образа
docker-compose -f deployments/docker-compose.prod.yml pull
docker-compose -f deployments/docker-compose.prod.yml up -d
```

## ☸️ Kubernetes развертывание

### Подготовка кластера

```bash
# Создание namespace
kubectl create namespace llm-gateway

# Создание секретов
kubectl apply -f deployments/k8s/secrets.yaml -n llm-gateway

# Применение манифестов
kubectl apply -f deployments/k8s/deployment.yaml -n llm-gateway
```

### Манифесты

**Файл**: `deployments/k8s/deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-gateway
  namespace: llm-gateway
spec:
  replicas: 3
  selector:
    matchLabels:
      app: llm-gateway
  template:
    metadata:
      labels:
        app: llm-gateway
    spec:
      containers:
      - name: llm-gateway
        image: your-registry/llm-gateway:latest
        ports:
        - containerPort: 8000
        env:
        - name: HOST
          value: "0.0.0.0"
        - name: PORT
          value: "8000"
        - name: DEBUG
          value: "false"
        - name: LOG_LEVEL
          value: "INFO"
        envFrom:
        - secretRef:
            name: llm-gateway-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: llm-gateway-service
  namespace: llm-gateway
spec:
  selector:
    app: llm-gateway
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: llm-gateway-hpa
  namespace: llm-gateway
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: llm-gateway
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: llm-gateway-ingress
  namespace: llm-gateway
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - yourdomain.com
    secretName: llm-gateway-tls
  rules:
  - host: yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: llm-gateway-service
            port:
              number: 80
```

**Файл**: `deployments/k8s/secrets.yaml`

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: llm-gateway-secrets
  namespace: llm-gateway
type: Opaque
data:
  SUPABASE_URL: <base64-encoded-value>
  SUPABASE_KEY: <base64-encoded-value>
  SUPABASE_SERVICE_ROLE_KEY: <base64-encoded-value>
  OPENAI_API_KEY: <base64-encoded-value>
  ANTHROPIC_API_KEY: <base64-encoded-value>
  GOOGLE_GEMINI_API_KEY: <base64-encoded-value>
  JWT_SECRET_KEY: <base64-encoded-value>
  REDIS_PASSWORD: <base64-encoded-value>
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: llm-gateway-config
  namespace: llm-gateway
data:
  HOST: "0.0.0.0"
  PORT: "8000"
  DEBUG: "false"
  LOG_LEVEL: "INFO"
  ENVIRONMENT: "production"
  RATE_LIMIT_STORAGE: "redis"
  RETRY_ENABLED: "true"
  CIRCUIT_BREAKER_ENABLED: "true"
```

### Управление развертыванием

```bash
# Проверка статуса
kubectl get pods -n llm-gateway
kubectl get services -n llm-gateway
kubectl get ingress -n llm-gateway

# Просмотр логов
kubectl logs -f deployment/llm-gateway -n llm-gateway

# Масштабирование
kubectl scale deployment llm-gateway --replicas=5 -n llm-gateway

# Обновление образа
kubectl set image deployment/llm-gateway llm-gateway=your-registry/llm-gateway:new-version -n llm-gateway

# Откат к предыдущей версии
kubectl rollout undo deployment/llm-gateway -n llm-gateway
```

## 📊 Мониторинг и логирование

### Prometheus конфигурация

**Файл**: `deployments/monitoring/prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "prometheus-rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'llm-gateway'
    static_configs:
      - targets: ['llm-gateway:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']
```

### Grafana дашборд

**Файл**: `deployments/monitoring/grafana-dashboard.json`

```json
{
  "dashboard": {
    "id": null,
    "title": "LLM Gateway Dashboard",
    "tags": ["llm-gateway"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "LLM Requests",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(llm_requests_total[5m])",
            "legendFormat": "{{model}}"
          }
        ]
      },
      {
        "id": 2,
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(llm_requests_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "id": 3,
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(llm_requests_errors_total[5m])",
            "legendFormat": "Errors"
          }
        ]
      }
    ]
  }
}
```

### Настройка логирования

**Файл**: `deployments/logrotate.conf`

```
/var/log/llm-gateway/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 app app
    postrotate
        systemctl reload llm-gateway
    endscript
}
```

### Health monitoring скрипт

**Файл**: `deployments/health-monitor.sh`

```bash
#!/bin/bash

# Конфигурация
HEALTH_URL="http://localhost:8000/health"
ALERT_EMAIL="admin@yourdomain.com"
LOG_FILE="/var/log/llm-gateway/health-monitor.log"

# Проверка здоровья
check_health() {
    response=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)
    
    if [ $response -ne 200 ]; then
        echo "$(date): Health check failed with status $response" >> $LOG_FILE
        # Отправка алерта
        echo "LLM Gateway health check failed at $(date)" | mail -s "LLM Gateway Alert" $ALERT_EMAIL
        return 1
    fi
    
    echo "$(date): Health check passed" >> $LOG_FILE
    return 0
}

# Основной цикл
while true; do
    check_health
    sleep 60
done
```

## 🔒 Безопасность

### Настройка файрвола

```bash
# Установка UFW
sudo apt install -y ufw

# Настройка правил
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Включение файрвола
sudo ufw enable
```

### SSL/TLS настройка

```bash
# Установка Certbot
sudo apt install -y certbot python3-certbot-nginx

# Получение сертификата
sudo certbot --nginx -d yourdomain.com

# Автоматическое обновление
sudo crontab -e
# Добавить:
# 0 12 * * * /usr/bin/certbot renew --quiet
```

### Nginx конфигурация

**Файл**: `deployments/nginx.conf`

```nginx
events {
    worker_connections 1024;
}

http {
    upstream llm_gateway {
        server llm-gateway:8000;
        server llm-gateway:8001;
        server llm-gateway:8002;
        server llm-gateway:8003;
    }

    server {
        listen 80;
        server_name yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

        location / {
            proxy_pass http://llm_gateway;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Rate limiting
            limit_req zone=api burst=10 nodelay;
            limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
        }

        location /health {
            proxy_pass http://llm_gateway;
            access_log off;
        }

        location /metrics {
            proxy_pass http://llm_gateway;
            allow 127.0.0.1;
            deny all;
        }
    }
}
```

## 💾 Backup и восстановление

### Скрипт backup

**Файл**: `deployments/backup.sh`

```bash
#!/bin/bash

# Конфигурация
BACKUP_DIR="/var/backups/llm-gateway"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Создание директории для backup
mkdir -p $BACKUP_DIR

# Backup базы данных
echo "Creating database backup..."
docker-compose -f deployments/docker-compose.prod.yml exec -T postgres pg_dump -U $POSTGRES_USER $POSTGRES_DB > $BACKUP_DIR/db_backup_$DATE.sql

# Backup конфигурации
echo "Creating configuration backup..."
tar -czf $BACKUP_DIR/config_backup_$DATE.tar.gz .env deployments/

# Backup логов
echo "Creating logs backup..."
tar -czf $BACKUP_DIR/logs_backup_$DATE.tar.gz /var/log/llm-gateway/

# Удаление старых backup
find $BACKUP_DIR -name "*.sql" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: $BACKUP_DIR"
```

### Восстановление

```bash
# Восстановление базы данных
docker-compose -f deployments/docker-compose.prod.yml exec -T postgres psql -U $POSTGRES_USER $POSTGRES_DB < backup_file.sql

# Восстановление конфигурации
tar -xzf config_backup_$DATE.tar.gz

# Восстановление логов
tar -xzf logs_backup_$DATE.tar.gz
```

### Автоматический backup

```bash
# Добавление в crontab
sudo crontab -e

# Добавить строку для ежедневного backup в 2:00
0 2 * * * /path/to/llm-gateway/deployments/backup.sh
```

## 🔄 Обновление

### Обновление с Docker

```bash
# Остановка сервисов
docker-compose -f deployments/docker-compose.prod.yml down

# Обновление кода
git pull origin main

# Обновление переменных окружения
cp env.example .env
# Отредактировать .env с новыми настройками

# Обновление образов
docker-compose -f deployments/docker-compose.prod.yml build --no-cache
docker-compose -f deployments/docker-compose.prod.yml pull

# Запуск обновленных сервисов
docker-compose -f deployments/docker-compose.prod.yml up -d

# Проверка статуса
docker-compose -f deployments/docker-compose.prod.yml ps
curl http://localhost:8000/health
```

### Обновление с Kubernetes

```bash
# Обновление образа
kubectl set image deployment/llm-gateway llm-gateway=your-registry/llm-gateway:new-version -n llm-gateway

# Мониторинг обновления
kubectl rollout status deployment/llm-gateway -n llm-gateway

# Откат при необходимости
kubectl rollout undo deployment/llm-gateway -n llm-gateway
```

### Скрипт обновления

**Файл**: `deployments/update.sh`

```bash
#!/bin/bash

set -e

echo "Starting LLM Gateway update..."

# Backup перед обновлением
./deployments/backup.sh

# Остановка сервисов
docker-compose -f deployments/docker-compose.prod.yml down

# Обновление кода
git pull origin main

# Обновление образов
docker-compose -f deployments/docker-compose.prod.yml build --no-cache
docker-compose -f deployments/docker-compose.prod.yml pull

# Запуск сервисов
docker-compose -f deployments/docker-compose.prod.yml up -d

# Ожидание готовности
echo "Waiting for services to be ready..."
sleep 30

# Проверка здоровья
if curl -f http://localhost:8000/health; then
    echo "Update completed successfully!"
else
    echo "Update failed! Rolling back..."
    docker-compose -f deployments/docker-compose.prod.yml down
    git reset --hard HEAD~1
    docker-compose -f deployments/docker-compose.prod.yml up -d
    echo "Rollback completed"
    exit 1
fi
```

## 🛠️ Устранение неполадок

### Частые проблемы

#### 1. Проблемы с подключением к базе данных

```bash
# Проверка подключения
python test_db_connection.py

# Проверка логов
docker-compose logs postgres

# Перезапуск базы данных
docker-compose restart postgres
```

#### 2. Проблемы с Redis

```bash
# Проверка статуса Redis
docker-compose exec redis redis-cli ping

# Проверка логов
docker-compose logs redis

# Очистка кэша
docker-compose exec redis redis-cli FLUSHALL
```

#### 3. Проблемы с производительностью

```bash
# Проверка метрик
curl http://localhost:8000/metrics

# Проверка circuit breaker статуса
curl http://localhost:8000/health/circuit-breakers

# Проверка системных ресурсов
curl http://localhost:8000/health/system
```

#### 4. Проблемы с SSL

```bash
# Проверка сертификата
openssl s_client -connect yourdomain.com:443

# Обновление сертификата
sudo certbot renew

# Проверка конфигурации Nginx
sudo nginx -t
```

### Логи и диагностика

#### Просмотр логов

```bash
# Логи приложения
docker-compose logs llm-gateway

# Логи с follow
docker-compose logs -f llm-gateway

# Логи за определенный период
docker-compose logs --since="2024-01-15T10:00:00" llm-gateway

# Логи с временными метками
docker-compose logs -t llm-gateway
```

#### Health checks

```bash
# Основной health check
curl http://localhost:8000/health

# Детальный health check
curl http://localhost:8000/health/detailed

# Системные ресурсы
curl http://localhost:8000/health/system

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
# Перезапуск всех сервисов
docker-compose restart

# Полная перезагрузка
docker-compose down
docker-compose up -d

# Восстановление из backup
./deployments/backup.sh restore
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