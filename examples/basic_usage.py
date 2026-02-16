#!/usr/bin/env python3
"""
Basic usage examples for ScanCode.io client.
"""

import os
from scancodeio_client import ScanCodeIOClient

# Configuration
SCANCODE_URL = os.getenv("SCANCODE_URL", "https://scancode.example.com")
API_KEY = os.getenv("SCANCODE_API_KEY", "your-api-key")


def example_1_simple_scan():
    """Example 1: Simple end-to-end file scan."""
    client = ScanCodeIOClient(
        base_url=SCANCODE_URL,
        api_key=API_KEY,
    )
    
    # Scan a file - this will create project, upload, run pipeline, 
    # wait for completion, and get results
    result = client.scan_file(
        file_path="/path/to/your/code.zip",
        wait=True,
        delete_on_complete=False,  # Keep project for inspection
    )
    
    print(f"Project: {result.project.name}")
    print(f"Status: {result.project.status.value}")
    print(f"Files scanned: {result.summary.total_files}")
    print(f"Unique licenses: {len(result.get_unique_license_expressions())}")
    
    return result


def example_2_step_by_step():
    """Example 2: Step-by-step control over the process."""
    client = ScanCodeIOClient(
        base_url=SCANCODE_URL,
        api_key=API_KEY,
    )
    
    # 1. Create a project
    project = client.create_project(
        name="my-code-analysis",
        pipelines=["scan_package"],
    )
    print(f"Created project: {project.uuid}")
    
    # 2. Upload file
    client.upload_file(
        project_uuid=project.uuid,
        file_path="/path/to/your/code.zip",
    )
    print("File uploaded")
    
    # 3. Start the scan
    client.execute_pipeline(project.uuid)
    print("Scan started")
    
    # 4. Wait for completion
    project = client.wait_for_completion(
        project_uuid=project.uuid,
        timeout=3600,  # 1 hour timeout
    )
    print(f"Scan completed with status: {project.status.value}")
    
    # 5. Get results
    result = client.get_scan_results(project.uuid)
    print(f"Found {result.summary.license_detections} license detections")
    
    # 6. Clean up
    client.delete_project(project.uuid)
    print("Project deleted")
    
    return result


def example_3_multiple_files():
    """Example 3: Scanning multiple files."""
    client = ScanCodeIOClient(
        base_url=SCANCODE_URL,
        api_key=API_KEY,
    )
    
    files_to_scan = [
        "/path/to/file1.zip",
        "/path/to/file2.tar.gz",
        "/path/to/file3",
    ]
    
    results = []
    for file_path in files_to_scan:
        print(f"\nScanning: {file_path}")
        result = client.scan_file(
            file_path=file_path,
            wait=True,
            delete_on_complete=True,  # Clean up after each scan
        )
        results.append(result)
        print(f"  Licenses found: {result.get_unique_license_expressions()}")
    
    return results


def example_4_async_scanning():
    """Example 4: Async/await usage."""
    import asyncio
    from scancodeio_client.async_client import AsyncScanCodeIOClient
    
    async def scan_multiple_async():
        async with AsyncScanCodeIOClient(
            base_url=SCANCODE_URL,
            api_key=API_KEY,
        ) as client:
            
            # Start multiple scans concurrently
            tasks = [
                client.scan_file("/path/to/file1.zip", wait=True),
                client.scan_file("/path/to/file2.zip", wait=True),
                client.scan_file("/path/to/file3.zip", wait=True),
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    print(f"Error: {result}")
                else:
                    print(f"Completed: {result.project.name}")
            
            return results
    
    return asyncio.run(scan_multiple_async())


def example_5_analyze_results():
    """Example 5: Working with scan results."""
    from scancodeio_client.utils import (
        generate_license_report,
        generate_package_report,
        export_to_json,
        estimate_risk_level,
    )
    
    client = ScanCodeIOClient(
        base_url=SCANCODE_URL,
        api_key=API_KEY,
    )
    
    # Run scan
    result = client.scan_file(
        file_path="/path/to/your/code.zip",
        wait=True,
    )
    
    # Generate license report
    license_report = generate_license_report(result)
    print("License Report:")
    print(f"  Total unique licenses: {license_report['total_unique_licenses']}")
    for license_expr, info in license_report['licenses'].items():
        print(f"  - {license_expr}: {info['file_count']} files")
    
    # Generate package report
    package_report = generate_package_report(result)
    print(f"\nPackages found: {package_report['total_packages']}")
    
    # Risk assessment
    risk = estimate_risk_level(result)
    print(f"\nRisk Level: {risk['risk_level'].upper()}")
    if risk['high_risk_files']:
        print(f"  ⚠️  {risk['high_risk_files']} files with high-risk licenses")
    
    # Export to JSON
    export_to_json(result, "scan_results.json")
    print("\nResults exported to scan_results.json")


def example_6_monitor_scan():
    """Example 6: Monitor scan progress."""
    import time
    
    client = ScanCodeIOClient(
        base_url=SCANCODE_URL,
        api_key=API_KEY,
    )
    
    # Create and start scan
    project = client.create_project(name="monitored-scan")
    client.upload_file(project.uuid, "/path/to/large-file.zip")
    client.execute_pipeline(project.uuid)
    
    # Monitor progress
    while True:
        project = client.get_project(project.uuid)
        print(f"Status: {project.status.value}")
        
        if project.is_complete():
            break
        
        time.sleep(5)
    
    if project.is_successful():
        result = client.get_scan_results(project.uuid)
        print(f"Scan complete! Found {len(result.files)} files")
    else:
        print(f"Scan failed: {project.error}")
    
    client.delete_project(project.uuid)


if __name__ == "__main__":
    # Run the example you want
    print("Select an example to run:")
    print("1. Simple scan")
    print("2. Step-by-step control")
    print("3. Multiple files")
    print("4. Async scanning")
    print("5. Analyze results")
    print("6. Monitor progress")
    
    choice = input("Enter number (1-6): ")
    
    examples = {
        "1": example_1_simple_scan,
        "2": example_2_step_by_step,
        "3": example_3_multiple_files,
        "4": example_4_async_scanning,
        "5": example_5_analyze_results,
        "6": example_6_monitor_scan,
    }
    
    if choice in examples:
        examples[choice]()
    else:
        print("Invalid choice")