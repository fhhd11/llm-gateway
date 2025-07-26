#!/bin/bash

# LLM Gateway Production Stop Script
# This script stops the LLM Gateway and all related services

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

echo -e "${BLUE}🛑 Stopping LLM Gateway Production Services${NC}"

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

# Check if Docker is running
if ! docker info &> /dev/null; then
    print_error "Docker is not running"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed"
    exit 1
fi

# Check if compose file exists
if [[ ! -f "$COMPOSE_FILE" ]]; then
    print_error "Docker Compose file not found: $COMPOSE_FILE"
    exit 1
fi

# Show current status
print_status "Current service status:"
docker-compose -f "$COMPOSE_FILE" ps

# Stop services gracefully
print_status "Stopping LLM Gateway services..."
docker-compose -f "$COMPOSE_FILE" down

# Check if services are stopped
if docker-compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
    print_warning "Some services are still running. Force stopping..."
    docker-compose -f "$COMPOSE_FILE" down --remove-orphans
fi

# Verify all services are stopped
if docker-compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
    print_error "Failed to stop all services"
    docker-compose -f "$COMPOSE_FILE" ps
    exit 1
else
    print_status "All services stopped successfully"
fi

# Optional: Remove containers and networks
read -p "Do you want to remove containers and networks? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Removing containers and networks..."
    docker-compose -f "$COMPOSE_FILE" down --remove-orphans --volumes
    print_status "Containers and networks removed"
fi

# Optional: Clean up unused Docker resources
read -p "Do you want to clean up unused Docker resources? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Cleaning up unused Docker resources..."
    docker system prune -f
    print_status "Docker cleanup completed"
fi

print_status "LLM Gateway services stopped successfully!" 