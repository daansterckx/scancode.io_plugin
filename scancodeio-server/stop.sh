#!/bin/bash

# ScanCode.io Stop Script

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

cd "$(dirname "$0")"

echo -e "${BLUE}Stopping ScanCode.io...${NC}"

docker-compose down

echo -e "${GREEN}✓ ScanCode.io stopped${NC}"
