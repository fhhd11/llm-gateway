#!/bin/bash

# LLM Gateway Production Startup Script
# This script starts the LLM Gateway in production mode with all necessary services

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
ENV_FILE="$PROJECT_DIR/.env"
LOG_DIR="/var/log/llm-gateway"

echo -e "${BLUE}🚀 Starting LLM Gateway Production Deployment${NC}"

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

# Check if Docker is installed and running
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! docker info &> /dev/null; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

print_status "Docker is installed and running"

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

print_status "Docker Compose is available"

# Check if .env file exists
if [[ ! -f "$ENV_FILE" ]]; then
    print_warning ".env file not found. Creating from env.example..."
    if [[ -f "$PROJECT_DIR/env.example" ]]; then
        cp "$PROJECT_DIR/env.example" "$ENV_FILE"
        print_warning "Please edit $ENV_FILE with your actual configuration values"
        print_warning "Then run this script again"
        exit 1
    else
        print_error "env.example file not found. Please create .env file manually."
        exit 1
    fi
fi

print_status "Environment file found"

# Create log directory if it doesn't exist
sudo mkdir -p "$LOG_DIR"
sudo chown $USER:$USER "$LOG_DIR"

print_status "Log directory created: $LOG_DIR"

# Check if ports are available
check_port() {
    local port=$1
    if netstat -tuln | grep -q ":$port "; then
        print_warning "Port $port is already in use"
        return 1
    fi
    return 0
}

check_port 8000 || {
    print_warning "Port 8000 is in use. Stopping existing containers..."
    docker-compose -f "$COMPOSE_FILE" down 2>/dev/null || true
}

check_port 6379 || {
    print_warning "Port 6379 (Redis) is in use. Make sure Redis is not running elsewhere."
}

# Pull latest images
print_status "Pulling latest Docker images..."
docker-compose -f "$COMPOSE_FILE" pull

# Build images if needed
print_status "Building Docker images..."
docker-compose -f "$COMPOSE_FILE" build --no-cache

# Start services
print_status "Starting LLM Gateway services..."
docker-compose -f "$COMPOSE_FILE" up -d

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 10

# Check service health
print_status "Checking service health..."

# Check LLM Gateway
for i in {1..30}; do
    if curl -f http://localhost:8000/health &>/dev/null; then
        print_status "LLM Gateway is healthy"
        break
    fi
    
    if [[ $i -eq 30 ]]; then
        print_error "LLM Gateway failed to start properly"
        docker-compose -f "$COMPOSE_FILE" logs llm-gateway
        exit 1
    fi
    
    echo -n "."
    sleep 2
done

# Check Redis
if docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping | grep -q "PONG"; then
    print_status "Redis is healthy"
else
    print_warning "Redis health check failed"
fi

# Show service status
print_status "Service status:"
docker-compose -f "$COMPOSE_FILE" ps

# Show logs
print_status "Recent logs:"
docker-compose -f "$COMPOSE_FILE" logs --tail=20

# Show endpoints
echo -e "${BLUE}📋 Available endpoints:${NC}"
echo -e "${GREEN}  Health Check:${NC} http://localhost:8000/health"
echo -e "${GREEN}  API Docs:${NC} http://localhost:8000/docs"
echo -e "${GREEN}  Metrics:${NC} http://localhost:8000/metrics"
echo -e "${GREEN}  Models:${NC} http://localhost:8000/v1/models"

# Show useful commands
echo -e "${BLUE}🔧 Useful commands:${NC}"
echo -e "${GREEN}  View logs:${NC} docker-compose -f $COMPOSE_FILE logs -f"
echo -e "${GREEN}  Stop services:${NC} docker-compose -f $COMPOSE_FILE down"
echo -e "${GREEN}  Restart services:${NC} docker-compose -f $COMPOSE_FILE restart"
echo -e "${GREEN}  Check status:${NC} docker-compose -f $COMPOSE_FILE ps"

print_status "LLM Gateway is now running in production mode!"
print_status "Check the logs above for any warnings or errors" 