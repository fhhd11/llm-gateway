#!/bin/bash

# LLM Gateway Backup Script
# This script creates backups of Redis data, environment, and logs

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$PROJECT_DIR/deployments/docker-compose.prod.yml"
BACKUP_DIR="/var/backups/llm-gateway"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="llm-gateway-backup-$DATE"

echo -e "${BLUE}💾 Creating LLM Gateway Backup${NC}"

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Create backup directory
sudo mkdir -p "$BACKUP_DIR"
sudo chown $USER:$USER "$BACKUP_DIR"

print_status "Backup directory: $BACKUP_DIR"

# Create backup subdirectory
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"
mkdir -p "$BACKUP_PATH"

print_status "Creating backup: $BACKUP_NAME"

# Backup Redis data
print_status "Backing up Redis data..."
if docker-compose -f "$COMPOSE_FILE" ps redis | grep -q "Up"; then
    docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli BGSAVE
    sleep 5
    
    # Copy Redis dump file
    if docker-compose -f "$COMPOSE_FILE" exec -T redis test -f /data/dump.rdb; then
        docker cp $(docker-compose -f "$COMPOSE_FILE" ps -q redis):/data/dump.rdb "$BACKUP_PATH/redis-dump.rdb"
        print_status "Redis data backed up successfully"
    else
        print_warning "Redis dump file not found"
    fi
else
    print_warning "Redis container is not running"
fi

# Backup environment file
print_status "Backing up environment configuration..."
if [[ -f "$PROJECT_DIR/.env" ]]; then
    cp "$PROJECT_DIR/.env" "$BACKUP_PATH/env-backup"
    print_status "Environment file backed up"
else
    print_warning "Environment file not found"
fi

# Backup logs
print_status "Backing up application logs..."
LOG_DIR="/var/log/llm-gateway"
if [[ -d "$LOG_DIR" ]]; then
    tar -czf "$BACKUP_PATH/logs.tar.gz" -C "$LOG_DIR" . 2>/dev/null || true
    print_status "Logs backed up"
else
    print_warning "Log directory not found: $LOG_DIR"
fi

# Backup Docker volumes
print_status "Backing up Docker volumes..."
VOLUME_BACKUP="$BACKUP_PATH/volumes"
mkdir -p "$VOLUME_BACKUP"

# Get list of volumes
VOLUMES=$(docker volume ls --format "{{.Name}}" | grep llm-gateway || true)

if [[ -n "$VOLUMES" ]]; then
    for volume in $VOLUMES; do
        print_status "Backing up volume: $volume"
        docker run --rm -v "$volume":/data -v "$VOLUME_BACKUP":/backup alpine tar -czf "/backup/$volume.tar.gz" -C /data . || true
    done
else
    print_warning "No Docker volumes found"
fi

# Backup configuration files
print_status "Backing up configuration files..."
CONFIG_BACKUP="$BACKUP_PATH/config"
mkdir -p "$CONFIG_BACKUP"

# Copy important config files
cp "$PROJECT_DIR/env.example" "$CONFIG_BACKUP/" 2>/dev/null || true
cp "$PROJECT_DIR/requirements.txt" "$CONFIG_BACKUP/" 2>/dev/null || true
cp "$PROJECT_DIR/requirements-dev.txt" "$CONFIG_BACKUP/" 2>/dev/null || true
cp "$COMPOSE_FILE" "$CONFIG_BACKUP/" 2>/dev/null || true
cp "$PROJECT_DIR/deployments/Dockerfile" "$CONFIG_BACKUP/" 2>/dev/null || true

print_status "Configuration files backed up"

# Create backup manifest
print_status "Creating backup manifest..."
cat > "$BACKUP_PATH/backup-manifest.txt" << EOF
LLM Gateway Backup Manifest
===========================
Backup Date: $(date)
Backup Name: $BACKUP_NAME
Backup Path: $BACKUP_PATH

Contents:
- Redis data dump
- Environment configuration
- Application logs
- Docker volumes
- Configuration files

Backup Size: $(du -sh "$BACKUP_PATH" | cut -f1)

System Information:
- Docker Version: $(docker --version)
- Docker Compose Version: $(docker-compose --version)
- OS: $(uname -a)

EOF

print_status "Backup manifest created"

# Compress backup
print_status "Compressing backup..."
cd "$BACKUP_DIR"
tar -czf "$BACKUP_NAME.tar.gz" "$BACKUP_NAME"
rm -rf "$BACKUP_NAME"

BACKUP_SIZE=$(du -h "$BACKUP_NAME.tar.gz" | cut -f1)
print_status "Backup compressed: $BACKUP_NAME.tar.gz ($BACKUP_SIZE)"

# Clean up old backups (keep last 7 days)
print_status "Cleaning up old backups..."
find "$BACKUP_DIR" -name "llm-gateway-backup-*.tar.gz" -mtime +7 -delete 2>/dev/null || true

# Show backup summary
echo -e "${BLUE}📋 Backup Summary:${NC}"
echo -e "${GREEN}  Backup file:${NC} $BACKUP_DIR/$BACKUP_NAME.tar.gz"
echo -e "${GREEN}  Size:${NC} $BACKUP_SIZE"
echo -e "${GREEN}  Location:${NC} $BACKUP_DIR"

# List all backups
echo -e "${BLUE}📁 Available backups:${NC}"
ls -lh "$BACKUP_DIR"/*.tar.gz 2>/dev/null || echo "No backups found"

print_status "Backup completed successfully!"
print_status "To restore, extract the backup and follow the restoration guide" 