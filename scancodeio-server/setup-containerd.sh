#!/bin/bash

# ScanCode.io Containerd Setup Script
# Works with nerdctl (Docker-compatible CLI for containerd)

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  ScanCode.io Containerd Setup${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Check for nerdctl
if ! command -v nerdctl &> /dev/null; then
    echo -e "${RED}nerdctl not found. Please install nerdctl:${NC}"
    echo "  curl -sSL https://github.com/containerd/nerdctl/releases/download/v1.7.0/nerdctl-1.7.0-linux-amd64.tar.gz | tar xz -C /usr/local/bin"
    exit 1
fi

# Check for containerd
if ! nerdctl info &> /dev/null; then
    echo -e "${RED}containerd is not running. Please start containerd.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ containerd and nerdctl are available${NC}"

# Generate secrets
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    
    # Generate secure passwords
    DB_PASSWORD=$(openssl rand -base64 32 | tr -d /=+ | cut -c1-32)
    SECRET_KEY=$(openssl rand -base64 50 | tr -d /=+ | cut -c1-50)
    
    # Get server IP
    SERVER_IP=$(hostname -I | awk '{print $1}')
    
    cat > .env << EOF
# ScanCode.io Environment Configuration
SECRET_KEY=$SECRET_KEY
DB_PASSWORD=$DB_PASSWORD

# CSRF: Allow all hosts for remote API access
ALLOWED_HOSTS=*
CORS_ALLOWED_ORIGINS=*
CSRF_TRUSTED_ORIGINS=http://*,https://*

# Network
WEB_PORT=8000

# Performance
WORKER_MEMORY_LIMIT=8G
WORKER_TIMEOUT=3600
GUNICORN_WORKERS=4

# Debug
DEBUG=False
EOF
    
    echo -e "${GREEN}✓ Created .env file${NC}"
else
    echo -e "${YELLOW}.env file already exists${NC}"
fi

# Create directories
mkdir -p nginx/ssl backups

# Pull images with explicit registry
# Use docker.io prefix for Docker Hub images
echo ""
echo -e "${BLUE}Pulling images...${NC}"
nerdctl pull docker.io/postgres:15-alpine
nerdctl pull docker.io/redis:7-alpine
nerdctl pull docker.io/clamav/clamav:latest
nerdctl pull docker.io/nexb/scancode.io:latest
nerdctl pull docker.io/nginx:alpine

echo -e "${GREEN}✓ Images pulled${NC}"

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Setup Complete!${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo "To start ScanCode.io:"
echo "  ./start-containerd.sh"
echo ""
echo "Or manually:"
echo "  nerdctl compose -f compose-containerd.yaml up -d"
echo ""