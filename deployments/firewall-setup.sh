#!/bin/bash

# LLM Gateway Firewall Setup Script
# This script configures UFW firewall for LLM Gateway

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔥 Configuring Firewall for LLM Gateway${NC}"

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
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

# Check if UFW is installed
if ! command -v ufw &> /dev/null; then
    print_error "UFW is not installed. Please install it first:"
    echo "  Ubuntu/Debian: sudo apt-get install ufw"
    echo "  CentOS/RHEL: sudo yum install ufw"
    exit 1
fi

print_status "UFW is installed"

# Reset UFW to default
print_status "Resetting UFW to default state..."
ufw --force reset

# Set default policies
print_status "Setting default policies..."
ufw default deny incoming
ufw default allow outgoing

# Allow SSH (adjust port if needed)
print_status "Configuring SSH access..."
ufw allow ssh
ufw allow 22/tcp

# Allow HTTP and HTTPS
print_status "Configuring web access..."
ufw allow 80/tcp
ufw allow 443/tcp

# Allow LLM Gateway API port
print_status "Configuring LLM Gateway API access..."
ufw allow 8000/tcp

# Allow Redis (only from localhost for security)
print_status "Configuring Redis access..."
ufw allow from 127.0.0.1 to any port 6379

# Allow Prometheus metrics (optional, for monitoring)
print_status "Configuring monitoring access..."
ufw allow 9090/tcp  # Prometheus
ufw allow 3000/tcp  # Grafana

# Allow Docker ports (if needed)
print_status "Configuring Docker access..."
ufw allow 2375/tcp  # Docker daemon (unencrypted)
ufw allow 2376/tcp  # Docker daemon (encrypted)

# Rate limiting for API endpoints
print_status "Configuring rate limiting..."
ufw limit 8000/tcp

# Allow specific IP ranges (customize as needed)
# Example: Allow access from your office/development team
# ufw allow from 192.168.1.0/24 to any port 8000
# ufw allow from 10.0.0.0/8 to any port 8000

# Block common attack ports
print_status "Blocking common attack ports..."
ufw deny 23/tcp   # Telnet
ufw deny 21/tcp   # FTP
ufw deny 25/tcp   # SMTP
ufw deny 110/tcp  # POP3
ufw deny 143/tcp  # IMAP
ufw deny 3389/tcp # RDP

# Enable logging
print_status "Enabling firewall logging..."
ufw logging on

# Enable UFW
print_status "Enabling UFW firewall..."
ufw --force enable

# Show firewall status
print_status "Firewall configuration complete!"
echo ""
echo -e "${BLUE}📋 Firewall Status:${NC}"
ufw status verbose

echo ""
echo -e "${BLUE}📋 Allowed Services:${NC}"
echo -e "${GREEN}  SSH:${NC} Port 22"
echo -e "${GREEN}  HTTP:${NC} Port 80"
echo -e "${GREEN}  HTTPS:${NC} Port 443"
echo -e "${GREEN}  LLM Gateway API:${NC} Port 8000 (rate limited)"
echo -e "${GREEN}  Redis:${NC} Port 6379 (localhost only)"
echo -e "${GREEN}  Prometheus:${NC} Port 9090"
echo -e "${GREEN}  Grafana:${NC} Port 3000"
echo -e "${GREEN}  Docker:${NC} Ports 2375, 2376"

echo ""
echo -e "${BLUE}🔧 Useful Commands:${NC}"
echo -e "${GREEN}  Check status:${NC} sudo ufw status"
echo -e "${GREEN}  View logs:${NC} sudo tail -f /var/log/ufw.log"
echo -e "${GREEN}  Allow IP:${NC} sudo ufw allow from IP_ADDRESS"
echo -e "${GREEN}  Deny IP:${NC} sudo ufw deny from IP_ADDRESS"
echo -e "${GREEN}  Disable:${NC} sudo ufw disable"

print_status "Firewall setup completed successfully!"
print_warning "Make sure you can still access your server via SSH before closing this session" 