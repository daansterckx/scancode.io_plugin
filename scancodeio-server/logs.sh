#!/bin/bash

# ScanCode.io Logs Script

set -e

cd "$(dirname "$0")"

# Check arguments
SERVICE=""
FOLLOW=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--follow)
            FOLLOW=true
            shift
            ;;
        -s|--service)
            SERVICE="$2"
            shift 2
            ;;
        *)
            SERVICE="$1"
            shift
            ;;
    esac
done

if [ "$FOLLOW" = true ]; then
    docker-compose logs -f ${SERVICE:-}
else
    docker-compose logs ${SERVICE:-}
fi
