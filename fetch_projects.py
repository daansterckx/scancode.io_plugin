#!/usr/bin/env python3
import os
import sys
import argparse
import json
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scancodeio_client import ScanCodeIOClient, ScanCodeIOError


def format_duration(seconds):
    if not seconds:
        return "N/A"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


def format_size(size_bytes):
    if not size_bytes:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"


def get_status_emoji(status):
    status_map = {
        "success": "[OK]",
        "failure": "[FAIL]",
        "running": "[RUN]",
        "not_started": "[WAIT]",
        "queued": "[QUEUE]",
    }
    return status_map.get(status, "❓")


def fetch_projects(client, limit=20):
    try:
        print(f"Fetching projects...")
        projects = client.list_projects(limit=limit)
        print(f"Found {len(projects)} projects\n")
        
        for i, project in enumerate(projects, 1):
            print(f"{'='*60}")
            print(f"Project {i}: {project.name}")
            print(f"{'='*60}")
            print(f"  UUID: {project.uuid}")
            print(f"  Created: {project.created_date.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  URL: {project.url or 'N/A'}")
            print(f"  Input Sources: {len(project.input_sources)}")
            print(f"  Status: {project.status.value}")
            
            if project.input_sources:
                print(f"\n  Input Files:")
                for source in project.input_sources:
                    filename = source.get('filename', 'Unknown')
                    print(f"    [FILE] {filename}")
            
            print()
        
        return projects
        
    except ScanCodeIOError as e:
        print(f"Error: {e}")
        sys.exit(1)


def fetch_project_details(client, project_uuid):
    try:
        project = client.get_project(project_uuid)
        
        print(f"{'='*60}")
        print(f"Project: {project.name}")
        print(f"{'='*60}")
        print(f"UUID: {project.uuid}")
        print(f"Created: {project.created_date.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Status: {project.status.value}")
        print(f"URL: {project.url or 'N/A'}")
        
        if project.input_sources:
            print(f"\n[FILES] Input Files:")
            for source in project.input_sources:
                filename = source.get('filename', 'Unknown')
                is_uploaded = "✓" if source.get('is_uploaded') else "✗"
                print(f"  [{is_uploaded}] {filename}")
        
        if project.extra_data and 'runs' in project.extra_data:
            print(f"\n[PIPELINES] Pipeline Runs:")
            for run in project.extra_data['runs']:
                status = run.get('status', 'unknown')
                pipeline = run.get('pipeline_name', 'unknown')
                emoji = get_status_emoji(status)
                print(f"  {emoji} {pipeline}")
                print(f"     Status: {status}")
                
                if run.get('execution_time'):
                    duration = format_duration(run['execution_time'])
                    print(f"     Duration: {duration}")
                
                if run.get('task_start_date'):
                    start = run['task_start_date'][:19].replace('T', ' ')
                    print(f"     Started: {start}")
                
                if run.get('task_exitcode') is not None and run['task_exitcode'] != 0:
                    print(f"     Exit Code: {run['task_exitcode']}")
                    if run.get('task_output'):
                        # Show first line of error
                        error_lines = run['task_output'].strip().split('\n')
                        if error_lines:
                            print(f"     Error: {error_lines[0][:100]}")
        
        return project
        
    except ScanCodeIOError as e:
        print(f"Error fetching project: {e}")
        sys.exit(1)


def fetch_scan_results(client, project_uuid, export_json=None):
    try:
        # First get project to check what runs are available
        project = client.get_project(project_uuid)
        
        print(f"\n{'='*60}")
        print(f"Scan Results for: {project.name}")
        print(f"{'='*60}")
        print(f"Project Status: {project.status.value}")
        
        # Get ALL runs from the project - fetch directly from API
        all_runs = []
        
        try:
            full_data = client._get_json(f"projects/{project_uuid}/")
            if isinstance(full_data, dict) and 'runs' in full_data:
                all_runs = full_data['runs']
        except Exception as e:
            # Fallback to extra_data
            if hasattr(project, 'extra_data') and project.extra_data:
                if isinstance(project.extra_data, dict) and 'runs' in project.extra_data:
                    all_runs = project.extra_data['runs']
        
        if not all_runs:
            print(f"\n[WARN] No scan runs found for this project.")
            return None
        
        print(f"\n[INFO] Found {len(all_runs)} scan run(s):")
        print(f"{'='*60}\n")
        
        # Show ALL runs with their details
        for i, run in enumerate(all_runs, 1):
            status = run.get('status', 'unknown')
            pipeline = run.get('pipeline_name', 'unknown')
            emoji = get_status_emoji(status)
            
            print(f"Run {i}: {emoji} {pipeline}")
            print(f"  Status: {status}")
            print(f"  UUID: {run.get('uuid', 'N/A')}")
            
            if run.get('execution_time'):
                duration = format_duration(run['execution_time'])
                print(f"  Duration: {duration}")
            
            if run.get('task_start_date'):
                start = run['task_start_date'][:19].replace('T', ' ')
                print(f"  Started: {start}")
            
            if run.get('task_end_date'):
                end = run['task_end_date'][:19].replace('T', ' ')
                print(f"  Ended: {end}")
            
            if run.get('task_exitcode') is not None:
                print(f"  Exit Code: {run['task_exitcode']}")
            
            if run.get('results_url'):
                print(f"  Results URL: {run['results_url']}")
            if run.get('summary_url'):
                print(f"  Summary URL: {run['summary_url']}")
            
            if status == 'failure' and run.get('task_output'):
                error_lines = run['task_output'].strip().split('\n')
                if error_lines and error_lines[0]:
                    print(f"  Error: {error_lines[0][:200]}")
            
            print()
        
        # Try to fetch detailed results for completed runs
        completed_runs = [r for r in all_runs if r.get('status') == 'success']
        
        if completed_runs:
            print(f"{'='*60}")
            print(f"Detailed Results from Latest Completed Scan")
            print(f"{'='*60}\n")
            
            latest_run = completed_runs[-1]
            print(f"Latest completed run: {latest_run.get('pipeline_name')}\n")
            
            # Try to get detailed scan results (bypass status check)
            try:
                # Try to get vulnerabilities from dedicated endpoint first
                vuln_data = None
                try:
                    vuln_data = client._get_json(f"projects/{project_uuid}/vulnerabilities/")
                    print(f"DEBUG - Vuln endpoint response type: {type(vuln_data)}")
                    if isinstance(vuln_data, dict):
                        print(f"DEBUG - Vuln endpoint keys: {vuln_data.keys()}")
                    elif isinstance(vuln_data, list):
                        print(f"DEBUG - Vuln endpoint list length: {len(vuln_data)}")
                except Exception as e:
                    print(f"DEBUG - Vuln endpoint error: {e}")
                
                result_data = client._get_json(f"projects/{project_uuid}/results/")
                print(f"DEBUG - Result data keys: {result_data.keys() if isinstance(result_data, dict) else 'N/A'}")
                print(f"DEBUG - Result data type: {type(result_data)}")
                if isinstance(result_data, dict):
                    if 'summary' in result_data:
                        print(f"DEBUG - Summary: {result_data['summary']}")
                    if 'files' in result_data:
                        print(f"DEBUG - Number of files: {len(result_data['files'])}")
                    if 'vulnerabilities' in result_data:
                        print(f"DEBUG - Number of vulnerabilities: {len(result_data['vulnerabilities'])}")
                    else:
                        print(f"DEBUG - No vulnerabilities key found")
                    # Check for vulns in dependencies
                    if 'dependencies' in result_data:
                        deps = result_data['dependencies']
                        print(f"DEBUG - Number of dependencies: {len(deps)}")
                        # Check first few deps for vulns
                        for i, dep in enumerate(deps[:5]):
                            if dep.get('vulnerabilities'):
                                print(f"DEBUG - Dep {i} has {len(dep['vulnerabilities'])} vulns: {dep.get('purl', 'N/A')}")
                    # Check for vulns in packages
                    if 'packages' in result_data:
                        pkgs = result_data['packages']
                        print(f"DEBUG - Number of packages: {len(pkgs)}")
                        # Check for affected_by_vulnerabilities
                        total_vulns = 0
                        for i, pkg in enumerate(pkgs):
                            vulns = pkg.get('affected_by_vulnerabilities', [])
                            if vulns:
                                total_vulns += len(vulns)
                                if i < 5:  # Print first 5
                                    print(f"DEBUG - Package {i} ({pkg.get('purl', 'N/A')}) has {len(vulns)} vulns")
                        print(f"DEBUG - Total vulnerabilities across all packages: {total_vulns}")
                from scancodeio_client.models import ScanResult
                result = ScanResult.from_api(project, result_data)
                
                # Calculate summary from actual data since API doesn't return summary field
                files = result_data.get('files', []) or []
                packages = result_data.get('packages', []) or []
                total_files = len(files)
                total_dirs = len(set(f.get('path', '').split('/')[0] for f in files if f.get('path') and '/' in f.get('path', '')))
                total_size = sum((f.get('size') or 0) for f in files)
                license_detections = sum(1 for f in files if f.get('detected_license_expression'))
                copyright_detections = sum(1 for f in files if f.get('copyrights'))
                package_detections = len(packages)
                
                print(f"\n{'='*60}")
                print(f"Scan Results")
                print(f"{'='*60}")
                print(f"\n[SUMMARY] Summary:")
                print(f"  Total Files: {total_files:,}")
                print(f"  Total Directories: {total_dirs:,}")
                print(f"  Total Size: {format_size(total_size)}")
                print(f"  License Detections: {license_detections:,}")
                print(f"  Copyright Detections: {copyright_detections:,}")
                print(f"  Package Detections: {package_detections:,}")
                licenses = result.get_unique_license_expressions()
                if licenses:
                    print(f"\n[LICENSES] Licenses Found ({len(licenses)} unique):")
                    for i, license_expr in enumerate(licenses[:200], 1):
                        # Wrap long license expressions at 70 chars
                        if len(license_expr) > 70:
                            print(f"  {i}. {license_expr[:67]}...")
                        else:
                            print(f"  {i}. {license_expr}")
                    if len(licenses) > 200:
                        print(f"  ... and {len(licenses) - 200} more")
                # Display vulnerabilities from packages and dependencies
                all_vulnerabilities = []
                
                # Get from packages
                packages = result_data.get('packages', [])
                for pkg in packages:
                    vulns = pkg.get('affected_by_vulnerabilities', [])
                    for vuln in vulns:
                        vuln['package'] = pkg.get('purl', 'Unknown')
                        all_vulnerabilities.append(vuln)
                
                # Get from dependencies
                dependencies = result_data.get('dependencies', [])
                for dep in dependencies:
                    vulns = dep.get('affected_by_vulnerabilities', [])
                    for vuln in vulns:
                        vuln['package'] = dep.get('purl', 'Unknown')
                        vuln['source'] = 'dependency'
                        all_vulnerabilities.append(vuln)
                
                if all_vulnerabilities:
                    print(f"\n[VULN] Vulnerabilities Found ({len(all_vulnerabilities)} total):")
                    for i, vuln in enumerate(all_vulnerabilities[:50], 1):
                        vuln_id = vuln.get('vulnerability_id', 'Unknown')
                        severity = vuln.get('severity', 'Unknown')
                        summary = vuln.get('summary', '')
                        pkg_name = vuln.get('package', 'Unknown')
                        print(f"  {i}. {vuln_id} (Severity: {severity}) - Package: {pkg_name}")
                        if summary:
                            # Truncate long summaries
                            if len(summary) > 70:
                                print(f"     {summary[:67]}...")
                            else:
                                print(f"     {summary}")
                    if len(all_vulnerabilities) > 50:
                        print(f"  ... and {len(all_vulnerabilities) - 50} more")
                
                packages = result.get_packages()
                if packages:
                    print(f"\n[PACKAGES] Packages Found ({len(packages)} total):")
                    pkg_by_type = {}
                    for pkg in packages:
                        pkg_type = pkg.type or 'unknown'
                        if pkg_type not in pkg_by_type:
                            pkg_by_type[pkg_type] = []
                        pkg_by_type[pkg_type].append(pkg)
                    
                    for pkg_type, pkgs in sorted(pkg_by_type.items()):
                        print(f"  {pkg_type}: {len(pkgs)}")
                        for pkg in pkgs[:50]:  
                            version = f"@{pkg.version}" if pkg.version else ""
                            print(f"    • {pkg.name}{version}")
                        if len(pkgs) > 50:
                            print(f"    ... and {len(pkgs) - 50} more")
                licensed_files = result.get_files_with_licenses()
                if licensed_files:
                    print(f"\n[LICENSED] Files with Licenses ({len(licensed_files)} total):")
                    for f in licensed_files[:100]:
                        license_info = f.detected_license_expression or "Unknown"
                        print(f"  • {f.path}")
                        print(f"    License: {license_info}")
                    if len(licensed_files) > 100:
                        print(f"  ... and {len(licensed_files) - 100} more")
                copyright_files = result.get_files_with_copyrights()
                if copyright_files:
                    print(f"\n[COPYRIGHT] Files with Copyrights ({len(copyright_files)} total):")
                    for f in copyright_files[:100]:
                        holder = f.holder or "Unknown"
                        print(f"  • {f.path}")
                        print(f"    Holder: {holder}")
                    if len(copyright_files) > 100:
                        print(f"  ... and {len(copyright_files) - 100} more")
                if export_json:
                    output_data = {
                        "project": {
                            "uuid": result.project.uuid,
                            "name": result.project.name,
                            "status": result.project.status.value,
                        },
                        "runs": [
                            {
                                "pipeline_name": r.get('pipeline_name'),
                                "status": r.get('status'),
                                "uuid": r.get('uuid'),
                                "execution_time": r.get('execution_time'),
                                "task_start_date": r.get('task_start_date'),
                                "task_end_date": r.get('task_end_date'),
                            }
                            for r in all_runs
                        ],
                        "summary": {
                            "total_files": result.summary.total_files,
                            "total_directories": result.summary.total_directories,
                            "total_size": result.summary.total_size,
                            "license_detections": result.summary.license_detections,
                            "copyright_detections": result.summary.copyright_detections,
                            "package_detections": result.summary.package_detections,
                        },
                        "licenses": licenses,
                        "vulnerabilities": [
                            {
                                "vulnerability_id": v.get('vulnerability_id'),
                                "severity": v.get('severity'),
                                "summary": v.get('summary'),
                                "affected_package": v.get('affected_package'),
                            }
                            for v in (result_data.get('vulnerabilities') or [])
                        ],
                        "packages": [
                            {
                                "type": p.type,
                                "name": p.name,
                                "version": p.version,
                                "purl": p.purl,
                                "license_expressions": p.license_expressions,
                            }
                            for p in packages
                        ],
                        "files": [
                            {
                                "path": f.path,
                                "license": f.detected_license_expression,
                                "copyright": f.copyright,
                                "holder": f.holder,
                            }
                            for f in result.files[:1000]
                        ],
                    }
                    
                    with open(export_json, 'w') as f:
                        json.dump(output_data, f, indent=2)
                    print(f"\n[SAVED] Results exported to: {export_json}")
                
                return result
                
            except Exception as e:
                print(f"[WARN] Could not fetch detailed scan results: {e}")
                print(f"\n    Basic run information is shown above.")
        
        return all_runs
        
    except ScanCodeIOError as e:
        print(f"Error fetching results: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Fetch and display ScanCode.io projects and scan results"
    )
    parser.add_argument(
        "--url",
        default=os.getenv("SCANCODE_URL", "http://localhost:8000"),
        help="ScanCode.io URL (or set SCANCODE_URL env var)"
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("SCANCODE_API_KEY"),
        help="API key (or set SCANCODE_API_KEY env var)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of projects to fetch (default: 20)"
    )
    parser.add_argument(
        "--project",
        metavar="UUID",
        help="Show detailed info for a specific project UUID"
    )
    parser.add_argument(
        "--results",
        metavar="UUID",
        help="Fetch scan results for a specific project UUID"
    )
    parser.add_argument(
        "--export",
        metavar="FILE",
        help="Export results to JSON file (use with --results)"
    )
    
    args = parser.parse_args()
    
    client = ScanCodeIOClient(base_url=args.url, api_key=args.api_key)
    try:
        projects = client.list_projects(limit=1)
        print(f"[OK] Connected to {args.url}\n")
    except ScanCodeIOError as e:
        print(f"[ERROR] Connection failed: {e}")
        sys.exit(1)
    if args.project:
        fetch_project_details(client, args.project)
    elif args.results:
        fetch_scan_results(client, args.results, export_json=args.export)
    else:
        fetch_projects(client, args.limit)


if __name__ == "__main__":
    main()