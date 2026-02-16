#!/usr/bin/env python3
"""
Complete working example of ScanCode.io integration.

This example:
1. Creates a project
2. Uploads a file
3. Runs the scan pipeline
4. Waits for completion
5. Retrieves and displays results
6. Optionally cleans up

Usage:
    export SCANCODE_URL="https://scancode.example.com"
    export SCANCODE_API_KEY="your-api-key"
    python example_complete.py /path/to/file.zip
"""

import argparse
import os
import sys
from pathlib import Path

# Add the package to path (in real use, install with pip)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scancodeio_client import ScanCodeIOClient, ScanCodeIOError
from scancodeio_client.utils import (
    generate_license_report,
    generate_copyright_report,
    generate_package_report,
    export_to_json,
    estimate_risk_level,
)


def main():
    parser = argparse.ArgumentParser(description="Scan a file with ScanCode.io")
    parser.add_argument("file", help="Path to file to scan")
    parser.add_argument("--url", help="ScanCode.io URL (or set SCANCODE_URL env var)")
    parser.add_argument("--api-key", help="API key (or set SCANCODE_API_KEY env var)")
    parser.add_argument("--name", help="Project name (default: filename)")
    parser.add_argument("--wait", action="store_true", default=True, help="Wait for completion")
    parser.add_argument("--no-wait", dest="wait", action="store_false", help="Don't wait for completion")
    parser.add_argument("--keep", action="store_true", help="Keep project after scan")
    parser.add_argument("--output", "-o", help="Export results to JSON file")
    parser.add_argument("--timeout", type=int, default=3600, help="Timeout in seconds")
    
    args = parser.parse_args()
    
    # Get configuration
    base_url = args.url or os.getenv("SCANCODE_URL")
    api_key = args.api_key or os.getenv("SCANCODE_API_KEY")
    
    if not base_url:
        print("Error: ScanCode.io URL required. Use --url or set SCANCODE_URL env var.")
        sys.exit(1)
    
    # Check file exists
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    
    # Initialize client
    print(f"Connecting to {base_url}...")
    client = ScanCodeIOClient(
        base_url=base_url,
        api_key=api_key,
    )
    
    try:
        # Verify connection by listing projects
        projects = client.list_projects(limit=1)
        print(f"✓ Connected successfully")
        
    except ScanCodeIOError as e:
        print(f"✗ Connection failed: {e}")
        sys.exit(1)
    
    # Determine project name
    project_name = args.name or file_path.name
    
    print(f"\nScanning: {file_path}")
    print(f"Project name: {project_name}")
    print(f"Wait for completion: {args.wait}")
    print(f"Timeout: {args.timeout}s")
    print(f"Delete after scan: {not args.keep}")
    print()
    
    try:
        # Perform scan
        result = client.scan_file(
            file_path=file_path,
            project_name=project_name,
            wait=args.wait,
            timeout=args.timeout,
            delete_on_complete=not args.keep,
        )
        
        if args.wait:
            # Display results
            print("=" * 60)
            print("SCAN RESULTS")
            print("=" * 60)
            
            print(f"\nProject: {result.project.name}")
            print(f"UUID: {result.project.uuid}")
            print(f"Status: {result.project.status.value}")
            print(f"URL: {result.project.url or 'N/A'}")
            
            print(f"\n--- Summary ---")
            print(f"Total files: {result.summary.total_files}")
            print(f"Total directories: {result.summary.total_directories}")
            print(f"Total size: {result.summary.total_size:,} bytes")
            print(f"License detections: {result.summary.license_detections}")
            print(f"Copyright detections: {result.summary.copyright_detections}")
            print(f"Package detections: {result.summary.package_detections}")
            
            # License report
            license_report = generate_license_report(result)
            print(f"\n--- Licenses ({license_report['total_unique_licenses']} unique) ---")
            for license_expr, info in license_report['licenses'].items():
                print(f"  • {license_expr}: {info['file_count']} files")
            
            # Package report
            package_report = generate_package_report(result)
            print(f"\n--- Packages ({package_report['total_packages']} total) ---")
            for pkg_type, packages in package_report['packages_by_type'].items():
                print(f"  • {pkg_type}: {len(packages)} packages")
            
            # Risk assessment
            risk = estimate_risk_level(result)
            print(f"\n--- Risk Assessment ({risk['risk_level'].upper()}) ---")
            if risk['high_risk_files']:
                print(f"  ⚠️  {risk['high_risk_files']} high-risk files")
                for detail in risk['high_risk_details'][:5]:
                    print(f"     - {detail['path']}: {detail['license']}")
            if risk['medium_risk_files']:
                print(f"  ⚠  {risk['medium_risk_files']} medium-risk files")
            if risk['unknown_license_files']:
                print(f"  ?  {risk['unknown_license_files']} files with unknown license")
            
            # Export if requested
            if args.output:
                export_to_json(result, args.output)
                print(f"\n✓ Results exported to: {args.output}")
            
            # Display a few sample files
            print(f"\n--- Sample Files ---")
            for f in result.files[:5]:
                license_info = f.detected_license_expression or "No license"
                print(f"  • {f.path}")
                print(f"    Size: {f.size:,} bytes | License: {license_info}")
            
            print()
            print("=" * 60)
            print("SCAN COMPLETE")
            print("=" * 60)
            
        else:
            # Not waiting - just started
            print(f"\n✓ Scan started: {result.project.name}")
            print(f"  UUID: {result.project.uuid}")
            print(f"  Status: {result.project.status.value}")
            print(f"\nUse this UUID to check status and get results later.")
            
            if not args.keep:
                print("\nNote: Project will NOT be auto-deleted (wait=False)")
    
    except ScanCodeIOError as e:
        print(f"\n✗ Scan failed: {e}")
        if e.status_code:
            print(f"  Status code: {e.status_code}")
        sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n⚠ Scan interrupted by user")
        sys.exit(130)
    
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()