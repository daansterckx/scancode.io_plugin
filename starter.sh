#!/bin/bash

# ScanCode.io Client Starter Script
# This script helps you run the ScanCode.io integration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_FILE=""

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is installed
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.7 or higher."
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    print_success "Found Python $PYTHON_VERSION"
}

# Check/install dependencies
check_dependencies() {
    print_info "Checking dependencies..."
    
    if ! python3 -c "import requests" 2>/dev/null; then
        print_warning "requests not found. Installing..."
        pip3 install requests aiohttp
    else
        print_success "Dependencies OK"
    fi
}

# Show usage information
show_usage() {
    cat << EOF

Usage: ./starter.sh [OPTIONS] [FILE]

ScanCode.io Client Starter Script

Options:
    -h, --help          Show this help message
    -u, --url URL       ScanCode.io instance URL
    -k, --key KEY       API key for authentication
    -n, --name NAME     Project name (default: filename)
    -o, --output FILE   Export results to JSON file
    -w, --wait          Wait for scan completion (default)
    --no-wait           Don't wait for completion
    --keep              Keep project after scan
    -t, --timeout SEC   Timeout in seconds (default: 3600)
    -e, --example NUM   Run example script (1-6)
    --demo              Run with demo/test data

Environment Variables:
    SCANCODE_URL        ScanCode.io instance URL
    SCANCODE_API_KEY    API key for authentication

Examples:
    # Scan a file
    ./starter.sh /path/to/file.zip

    # Scan with custom URL
    ./starter.sh -u https://scancode.example.com /path/to/file.zip

    # Scan and export results
    ./starter.sh -o results.json /path/to/file.zip

    # Run example 1 (simple scan)
    ./starter.sh -e 1

EOF
}

# Run the complete example
run_complete() {
    local file="$1"
    local extra_args="${2:-}"
    
    print_info "Running complete scan..."
    
    if [ ! -f "$file" ]; then
        print_error "File not found: $file"
        exit 1
    fi
    
    python3 "$SCRIPT_DIR/example_complete.py" \
        $extra_args \
        "$file"
}

# Run an example
run_example() {
    local num="$1"
    
    print_info "Running example $num..."
    
    cd "$SCRIPT_DIR"
    
    case $num in
        1)
            print_info "Example 1: Simple file scan"
            ;;
        2)
            print_info "Example 2: Step-by-step control"
            ;;
        3)
            print_info "Example 3: Multiple files"
            ;;
        4)
            print_info "Example 4: Async scanning"
            ;;
        5)
            print_info "Example 5: Analyze results"
            ;;
        6)
            print_info "Example 6: Monitor scan progress"
            ;;
        *)
            print_error "Unknown example: $num (use 1-6)"
            exit 1
            ;;
    esac
    
    python3 "$SCRIPT_DIR/examples/basic_usage.py" <<< "$num"
}

# Main function
main() {
    # Parse arguments
    local file=""
    local url=""
    local key=""
    local name=""
    local output=""
    local wait_flag="--wait"
    local keep=""
    local timeout=""
    local example=""
    local demo=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -u|--url)
                url="--url $2"
                shift 2
                ;;
            -k|--key)
                key="--api-key $2"
                shift 2
                ;;
            -n|--name)
                name="--name $2"
                shift 2
                ;;
            -o|--output)
                output="--output $2"
                shift 2
                ;;
            -w|--wait)
                wait_flag="--wait"
                shift
                ;;
            --no-wait)
                wait_flag=""
                shift
                ;;
            --keep)
                keep="--keep"
                shift
                ;;
            -t|--timeout)
                timeout="--timeout $2"
                shift 2
                ;;
            -e|--example)
                example="$2"
                shift 2
                ;;
            --demo)
                demo=true
                shift
                ;;
            -*)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
            *)
                file="$1"
                shift
                ;;
        esac
    done
    
    # Check Python
    check_python
    
    # Check dependencies
    check_dependencies
    
    # Run example if requested
    if [ -n "$example" ]; then
        run_example "$example"
        exit 0
    fi
    
    # Demo mode - create a test file
    if [ "$demo" = true ]; then
        print_info "Demo mode - creating test file..."
        
        # Create a temporary directory with some files
        DEMO_DIR=$(mktemp -d)
        mkdir -p "$DEMO_DIR/test-project/src"
        
        # Create a sample Python file with license header
        cat > "$DEMO_DIR/test-project/src/main.py" << 'PYEOF'
#!/usr/bin/env python3
# Copyright (c) 2024 Example Corp
# SPDX-License-Identifier: MIT

def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()
PYEOF

        # Create a sample package.json
        cat > "$DEMO_DIR/test-project/package.json" << 'JSONEOF'
{
  "name": "demo-project",
  "version": "1.0.0",
  "license": "MIT",
  "dependencies": {
    "lodash": "^4.17.21"
  }
}
JSONEOF

        # Create README
        cat > "$DEMO_DIR/test-project/README.md" << 'MDEOF'
# Demo Project

This is a demo project for testing ScanCode.io integration.
MDEOF

        # Create the zip file
        cd "$DEMO_DIR"
        zip -r test-project.zip test-project/
        file="$DEMO_DIR/test-project.zip"
        
        print_success "Created demo file: $file"
        
        # Set default URL if not provided
        if [ -z "$url" ] && [ -z "$SCANCODE_URL" ]; then
            print_warning "No ScanCode.io URL provided. Using placeholder."
            print_info "Set SCANCODE_URL environment variable or use -u flag"
        fi
    fi
    
    # Check if file is provided
    if [ -z "$file" ]; then
        print_error "No file specified. Use -h for help."
        exit 1
    fi
    
    # Build extra arguments
    local extra_args="$url $key $name $output $wait_flag $keep $timeout"
    
    # Run the scan
    run_complete "$file" "$extra_args"
    
    # Cleanup demo files
    if [ "$demo" = true ] && [ -d "$DEMO_DIR" ]; then
        rm -rf "$DEMO_DIR"
        print_info "Cleaned up demo files"
    fi
}

# Run main function
main "$@"