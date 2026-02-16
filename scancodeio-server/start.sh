#!/bin/bash

# ScanCode.io Start Script

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}Starting ScanCode.io...${NC}"

# Check if .env exists
if [ ! -f .env ]; then
    echo "Error: .env file not found. Run ./setup.sh first."
    exit 1
fi

# Load environment
export $(grep -v '^#' .env | xargs)

# Start services
echo "Starting Docker containers..."
docker-compose up -d

echo ""
echo -e "${GREEN}✓ ScanCode.io is starting up!${NC}"
echo ""
echo "Services:"
echo "  - Web:      http://localhost:${WEB_PORT:-8000}"
echo "  - Database: postgres (internal)"
echo "  - Redis:    redis (internal)"
echo "  - Worker:   processing scans"
echo ""
echo "View logs: ./logs.sh"
echo "Stop:      ./stop.sh"
echo "Status:    ./status.sh"
echo ""