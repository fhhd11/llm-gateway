#!/bin/bash

# LLM Gateway Health Monitor Script
# This script monitors the health of LLM Gateway services and restarts if unhealthy

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
LOG_FILE="/var/log/llm-gateway/health-monitor.log"
MAX_RESTARTS=3
CHECK_INTERVAL=60  # seconds

echo -e "${BLUE}🏥 LLM Gateway Health Monitor${NC}"

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
    echo "$(date): ✅ $1" >> "$LOG_FILE"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    echo "$(date): ⚠️  $1" >> "$LOG_FILE"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
    echo "$(date): ❌ $1" >> "$LOG_FILE"
}

# Create log directory
sudo mkdir -p "$(dirname "$LOG_FILE")"
sudo chown $USER:$USER "$(dirname "$LOG_FILE")"

# Initialize restart counter
RESTART_COUNT_FILE="/tmp/llm-gateway-restart-count"
if [[ ! -f "$RESTART_COUNT_FILE" ]]; then
    echo "0" > "$RESTART_COUNT_FILE"
fi

# Function to check service health
check_service_health() {
    local service_name=$1
    local health_url=$2
    
    if [[ -n "$health_url" ]]; then
        # Check HTTP health endpoint
        if curl -f -s "$health_url" > /dev/null 2>&1; then
            return 0
        else
            return 1
        fi
    else
        # Check Docker container status
        if docker-compose -f "$COMPOSE_FILE" ps "$service_name" | grep -q "Up"; then
            return 0
        else
            return 1
        fi
    fi
}

# Function to restart service
restart_service() {
    local service_name=$1
    
    print_warning "Restarting $service_name..."
    
    # Increment restart counter
    local current_count=$(cat "$RESTART_COUNT_FILE")
    local new_count=$((current_count + 1))
    echo "$new_count" > "$RESTART_COUNT_FILE"
    
    # Check if we've exceeded max restarts
    if [[ $new_count -gt $MAX_RESTARTS ]]; then
        print_error "Maximum restart attempts ($MAX_RESTARTS) exceeded for $service_name"
        print_error "Manual intervention required"
        return 1
    fi
    
    # Restart the service
    docker-compose -f "$COMPOSE_FILE" restart "$service_name"
    
    # Wait for service to start
    sleep 10
    
    # Check if restart was successful
    if check_service_health "$service_name"; then
        print_status "$service_name restarted successfully"
        return 0
    else
        print_error "$service_name failed to restart"
        return 1
    fi
}

# Function to check system resources
check_system_resources() {
    # Check disk space
    local disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [[ $disk_usage -gt 90 ]]; then
        print_warning "Disk usage is high: ${disk_usage}%"
    fi
    
    # Check memory usage
    local mem_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    if [[ $mem_usage -gt 90 ]]; then
        print_warning "Memory usage is high: ${mem_usage}%"
    fi
    
    # Check CPU load
    local cpu_load=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    if (( $(echo "$cpu_load > 5.0" | bc -l) )); then
        print_warning "CPU load is high: $cpu_load"
    fi
}

# Function to send alert (placeholder for integration with monitoring systems)
send_alert() {
    local message=$1
    local level=$2
    
    # Log the alert
    echo "$(date): ALERT [$level] $message" >> "$LOG_FILE"
    
    # Here you can integrate with your preferred alerting system:
    # - Email
    # - Slack
    # - PagerDuty
    # - Telegram
    # - etc.
    
    # Example: Send to Slack (uncomment and configure)
    # curl -X POST -H 'Content-type: application/json' \
    #     --data "{\"text\":\"[LLM Gateway] $message\"}" \
    #     https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
    
    print_warning "Alert sent: $message"
}

# Main monitoring loop
monitor_services() {
    print_status "Starting health monitoring..."
    print_status "Check interval: ${CHECK_INTERVAL}s"
    print_status "Max restarts: $MAX_RESTARTS"
    
    while true; do
        echo "$(date): Running health checks..." >> "$LOG_FILE"
        
        # Check LLM Gateway health
        if ! check_service_health "llm-gateway" "http://localhost:8000/health"; then
            print_error "LLM Gateway is unhealthy"
            send_alert "LLM Gateway service is down" "CRITICAL"
            
            if ! restart_service "llm-gateway"; then
                send_alert "LLM Gateway failed to restart after $MAX_RESTARTS attempts" "CRITICAL"
            fi
        else
            print_status "LLM Gateway is healthy"
            # Reset restart counter on successful health check
            echo "0" > "$RESTART_COUNT_FILE"
        fi
        
        # Check Redis health
        if ! check_service_health "redis"; then
            print_error "Redis is unhealthy"
            send_alert "Redis service is down" "WARNING"
            
            if ! restart_service "redis"; then
                send_alert "Redis failed to restart after $MAX_RESTARTS attempts" "CRITICAL"
            fi
        else
            print_status "Redis is healthy"
        fi
        
        # Check system resources
        check_system_resources
        
        # Check Docker daemon
        if ! docker info > /dev/null 2>&1; then
            print_error "Docker daemon is not responding"
            send_alert "Docker daemon is down" "CRITICAL"
        fi
        
        # Sleep before next check
        sleep "$CHECK_INTERVAL"
    done
}

# Handle script interruption
trap 'print_status "Health monitor stopped"; exit 0' INT TERM

# Start monitoring
monitor_services 