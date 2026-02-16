#!/bin/bash

# ScanCode.io Containerd Start Script

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}Starting ScanCode.io with containerd...${NC}"

# Check for .env
if [ ! -f .env ]; then
    echo "Error: .env file not found. Run ./setup-containerd.sh first."
    exit 1
fi

# Load environment
export $(grep -v '^#' .env | xargs)

# Start with nerdctl compose
echo "Starting services..."
nerdctl compose -f compose-containerd.yaml up -d

echo ""
echo -e "${GREEN}✓ ScanCode.io is starting!${NC}"
echo ""
echo "Services starting up:"
echo "  - Database (postgres)"
echo "  - Cache (redis)"
echo "  - Antivirus (clamav) - first startup downloads virus definitions"
echo "  - Web application"
echo "  - Worker"
echo ""
echo "Wait 30-60 seconds for ClamAV to download virus definitions."
echo ""
echo "View logs: ./logs-containerd.sh"
echo "Stop: ./stop-containerd.sh"
echo ""
echo "Access URLs:"
echo "  Web UI: http://$(hostname -I | awk '{print $1}'):8000"
echo "  API: http://$(hostname -I | awk '{print $1}'):8000/api/"
echo ""