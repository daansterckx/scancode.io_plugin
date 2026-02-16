#!/bin/bash

# ScanCode.io Server Setup Script
# This script helps you set up ScanCode.io on your VM

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  ScanCode.io Server Setup${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

if ! command_exists docker; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    echo "  Ubuntu/Debian: sudo apt-get install docker.io docker-compose"
    echo "  Or follow: https://docs.docker.com/engine/install/"
    exit 1
fi

if ! command_exists docker-compose; then
    echo -e "${RED}Docker Compose is not installed. Please install it first.${NC}"
    echo "  sudo apt-get install docker-compose"
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose are installed${NC}"

# Check Docker is running
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}Docker daemon is not running. Please start Docker.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker daemon is running${NC}"

# Generate secrets
echo ""
echo -e "${BLUE}Generating secrets...${NC}"

if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    
    # Generate secure passwords
    DB_PASSWORD=$(openssl rand -base64 32 | tr -d /=+ | cut -c1-32)
    SECRET_KEY=$(openssl rand -base64 50 | tr -d /=+ | cut -c1-50)
    
    # Get server IP
    SERVER_IP=$(hostname -I | awk '{print $1}')
    
    cat > .env << EOF
# ScanCode.io Environment Configuration
# Generated automatically on $(date)

# SECURITY
SECRET_KEY=$SECRET_KEY
DB_PASSWORD=$DB_PASSWORD

# NETWORK - Update with your server's IP/hostname
ALLOWED_HOSTS=localhost,127.0.0.1,$SERVER_IP,$(hostname -f 2>/dev/null || echo 'localhost')
CORS_ALLOWED_ORIGINS=
CSRF_TRUSTED_ORIGINS=http://$SERVER_IP:8000

# PORTS
WEB_PORT=8000
NGINX_PORT=80
NGINX_SSL_PORT=443

# PERFORMANCE
WORKER_MEMORY_LIMIT=8G
WORKER_TIMEOUT=3600
GUNICORN_WORKERS=4

# DEBUG
DEBUG=False
EOF
    
    echo -e "${GREEN}✓ Created .env file with secure passwords${NC}"
    echo -e "${YELLOW}  IMPORTANT: Edit .env to customize ALLOWED_HOSTS${NC}"
else
    echo -e "${YELLOW}.env file already exists, skipping creation${NC}"
fi

# Create SSL directory structure for production
echo ""
echo -e "${BLUE}Setting up directories...${NC}"
mkdir -p nginx/ssl
mkdir -p backups

echo -e "${GREEN}✓ Directories created${NC}"

# Pull images
echo ""
echo -e "${BLUE}Pulling Docker images...${NC}"
docker-compose pull

echo -e "${GREEN}✓ Images pulled${NC}"

# Show configuration
echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Setup Complete!${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo -e "Configuration saved to: ${GREEN}.env${NC}"
echo ""
echo "Next steps:"
echo ""
echo "1. Review the configuration:"
echo "   nano .env"
echo ""
echo "2. Start ScanCode.io:"
echo "   ./start.sh"
echo ""
echo "3. Access the web interface:"
echo "   http://$(hostname -I | awk '{print $1}'):8000"
echo ""
echo "4. Create a superuser (for admin access):"
echo "   ./manage.sh createsuperuser"
echo ""
echo "Documentation: https://scancodeio.readthedocs.io/"
echo ""