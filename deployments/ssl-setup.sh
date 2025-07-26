#!/bin/bash

# LLM Gateway SSL Setup Script
# This script sets up SSL certificates using Let's Encrypt

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔒 Setting up SSL Certificates for LLM Gateway${NC}"

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

# Configuration
DOMAIN=""
EMAIL=""

# Get domain from user
read -p "Enter your domain name (e.g., api.yourdomain.com): " DOMAIN
if [[ -z "$DOMAIN" ]]; then
    print_error "Domain name is required"
    exit 1
fi

# Get email from user
read -p "Enter your email address for Let's Encrypt notifications: " EMAIL
if [[ -z "$EMAIL" ]]; then
    print_error "Email address is required"
    exit 1
fi

print_status "Domain: $DOMAIN"
print_status "Email: $EMAIL"

# Check if domain resolves to this server
print_status "Checking domain resolution..."
SERVER_IP=$(curl -s ifconfig.me)
DOMAIN_IP=$(dig +short "$DOMAIN" | head -1)

if [[ "$SERVER_IP" != "$DOMAIN_IP" ]]; then
    print_warning "Domain $DOMAIN does not resolve to this server's IP ($SERVER_IP)"
    print_warning "Make sure your DNS is configured correctly before proceeding"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    print_status "Domain resolution verified"
fi

# Install certbot if not installed
if ! command -v certbot &> /dev/null; then
    print_status "Installing certbot..."
    
    # Detect OS and install certbot
    if command -v apt-get &> /dev/null; then
        # Ubuntu/Debian
        apt-get update
        apt-get install -y certbot python3-certbot-nginx
    elif command -v yum &> /dev/null; then
        # CentOS/RHEL
        yum install -y certbot python3-certbot-nginx
    elif command -v dnf &> /dev/null; then
        # Fedora
        dnf install -y certbot python3-certbot-nginx
    else
        print_error "Unsupported package manager. Please install certbot manually."
        exit 1
    fi
fi

print_status "Certbot is installed"

# Stop nginx temporarily for certificate generation
print_status "Stopping nginx for certificate generation..."
systemctl stop nginx 2>/dev/null || true

# Create temporary nginx configuration for certificate generation
print_status "Creating temporary nginx configuration..."
cat > /etc/nginx/sites-available/temp-ssl << EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}
EOF

# Enable temporary site
ln -sf /etc/nginx/sites-available/temp-ssl /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Create web root directory
mkdir -p /var/www/html

# Test nginx configuration
print_status "Testing nginx configuration..."
nginx -t

# Start nginx
print_status "Starting nginx..."
systemctl start nginx

# Generate SSL certificate
print_status "Generating SSL certificate..."
certbot certonly --webroot \
    --webroot-path=/var/www/html \
    --email="$EMAIL" \
    --agree-tos \
    --no-eff-email \
    --domains="$DOMAIN"

# Check if certificate was generated successfully
if [[ ! -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]]; then
    print_error "Failed to generate SSL certificate"
    exit 1
fi

print_status "SSL certificate generated successfully"

# Create production nginx configuration
print_status "Creating production nginx configuration..."
cat > /etc/nginx/sites-available/llm-gateway << EOF
# Rate limiting zones
limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone \$binary_remote_addr zone=health:10m rate=30r/s;

# Upstream for LLM Gateway
upstream llm_gateway {
    server 127.0.0.1:8000;
    keepalive 32;
}

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name $DOMAIN;
    
    # Redirect all HTTP traffic to HTTPS
    return 301 https://\$server_name\$request_uri;
}

# Main HTTPS server
server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    # SSL Security Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';";

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # Client max body size
    client_max_body_size 10M;

    # Timeouts
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;

    # Health check endpoint (no rate limiting)
    location /health {
        limit_req zone=health burst=5 nodelay;
        
        proxy_pass http://llm_gateway;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Health check specific headers
        proxy_set_header Connection "";
        proxy_http_version 1.1;
    }

    # Metrics endpoint (no rate limiting)
    location /metrics {
        limit_req zone=health burst=5 nodelay;
        
        proxy_pass http://llm_gateway;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # API endpoints with rate limiting
    location /v1/ {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://llm_gateway;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # API specific headers
        proxy_set_header Connection "";
        proxy_http_version 1.1;
        
        # CORS headers
        add_header Access-Control-Allow-Origin \$http_origin always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization" always;
        add_header Access-Control-Expose-Headers "Content-Length,Content-Range" always;
        
        # Handle preflight requests
        if (\$request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin \$http_origin;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
            add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization";
            add_header Access-Control-Max-Age 1728000;
            add_header Content-Type "text/plain; charset=utf-8";
            add_header Content-Length 0;
            return 204;
        }
    }

    # Root endpoint
    location / {
        limit_req zone=api burst=10 nodelay;
        
        proxy_pass http://llm_gateway;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Logging
    access_log /var/log/nginx/llm_gateway_access.log;
    error_log /var/log/nginx/llm_gateway_error.log;
}
EOF

# Enable production site
rm -f /etc/nginx/sites-enabled/temp-ssl
ln -sf /etc/nginx/sites-available/llm-gateway /etc/nginx/sites-enabled/

# Test nginx configuration
print_status "Testing nginx configuration..."
nginx -t

# Reload nginx
print_status "Reloading nginx..."
systemctl reload nginx

# Set up automatic certificate renewal
print_status "Setting up automatic certificate renewal..."
cat > /etc/cron.d/ssl-renewal << EOF
# Renew SSL certificates twice daily
0 12 * * * root certbot renew --quiet --deploy-hook "systemctl reload nginx"
0 0 * * * root certbot renew --quiet --deploy-hook "systemctl reload nginx"
EOF

# Test certificate renewal
print_status "Testing certificate renewal..."
certbot renew --dry-run

print_status "SSL setup completed successfully!"
echo ""
echo -e "${BLUE}📋 SSL Configuration Summary:${NC}"
echo -e "${GREEN}  Domain:${NC} $DOMAIN"
echo -e "${GREEN}  Certificate:${NC} /etc/letsencrypt/live/$DOMAIN/"
echo -e "${GREEN}  Auto-renewal:${NC} Enabled (twice daily)"
echo -e "${GREEN}  HTTPS:${NC} https://$DOMAIN"

echo ""
echo -e "${BLUE}🔧 Useful Commands:${NC}"
echo -e "${GREEN}  Check certificate:${NC} sudo certbot certificates"
echo -e "${GREEN}  Manual renewal:${NC} sudo certbot renew"
echo -e "${GREEN}  Test renewal:${NC} sudo certbot renew --dry-run"
echo -e "${GREEN}  View nginx logs:${NC} sudo tail -f /var/log/nginx/llm_gateway_*.log"

print_status "SSL setup completed successfully!"
print_warning "Make sure your LLM Gateway is running on port 8000 before testing HTTPS" 