"""
Utility functions for working with ScanCode.io results.
"""

from pathlib import Path
from typing import Dict, List, Set, Union
import json

from .models import ScanResult, FileResult, Package


def generate_license_report(result: ScanResult) -> Dict:
    """
    Generate a summary report of all licenses found.
    
    Args:
        result: ScanResult to analyze
        
    Returns:
        Dictionary with license summary
    """
    license_files = {}
    
    for file in result.files:
        if file.detected_license_expression:
            expr = file.detected_license_expression
            if expr not in license_files:
                license_files[expr] = []
            license_files[expr].append(file.path)
    
    return {
        "total_unique_licenses": len(license_files),
        "total_files_with_licenses": len(result.get_files_with_licenses()),
        "licenses": {
            license_expr: {
                "file_count": len(files),
                "files": files,
            }
            for license_expr, files in license_files.items()
        },
    }


def generate_copyright_report(result: ScanResult) -> Dict:
    """
    Generate a summary report of all copyrights found.
    
    Args:
        result: ScanResult to analyze
        
    Returns:
        Dictionary with copyright summary
    """
    copyright_holders = {}
    
    for file in result.files:
        if file.holder:
            holder = file.holder
            if holder not in copyright_holders:
                copyright_holders[holder] = []
            copyright_holders[holder].append(file.path)
    
    return {
        "total_unique_holders": len(copyright_holders),
        "total_files_with_copyright": len(result.get_files_with_copyrights()),
        "holders": {
            holder: {
                "file_count": len(files),
                "files": files,
            }
            for holder, files in copyright_holders.items()
        },
    }


def generate_package_report(result: ScanResult) -> Dict:
    """
    Generate a summary report of all packages found.
    
    Args:
        result: ScanResult to analyze
        
    Returns:
        Dictionary with package summary
    """
    packages_by_type = {}
    all_packages = result.get_packages()
    
    for pkg in all_packages:
        pkg_type = pkg.type
        if pkg_type not in packages_by_type:
            packages_by_type[pkg_type] = []
        packages_by_type[pkg_type].append({
            "name": pkg.name,
            "version": pkg.version,
            "namespace": pkg.namespace,
            "purl": pkg.purl,
            "licenses": pkg.license_expressions,
        })
    
    return {
        "total_packages": len(all_packages),
        "packages_by_type": packages_by_type,
        "unique_purls": list(set(
            pkg.purl for pkg in all_packages if pkg.purl
        )),
    }


def export_to_json(result: ScanResult, output_path: Union[str, Path]) -> None:
    """
    Export scan results to a JSON file.
    
    Args:
        result: ScanResult to export
        output_path: Path for output file
    """
    output_path = Path(output_path)
    
    data = {
        "project": {
            "uuid": result.project.uuid,
            "name": result.project.name,
            "status": result.project.status.value,
            "created_date": result.project.created_date.isoformat(),
        },
        "summary": {
            "total_files": result.summary.total_files,
            "total_directories": result.summary.total_directories,
            "total_size": result.summary.total_size,
            "license_detections": result.summary.license_detections,
            "copyright_detections": result.summary.copyright_detections,
            "package_detections": result.summary.package_detections,
        },
        "files": [
            {
                "path": f.path,
                "type": f.type,
                "size": f.size,
                "sha1": f.sha1,
                "md5": f.md5,
                "license": f.detected_license_expression,
                "license_spdx": f.detected_license_expression_spdx,
                "copyright": f.copyright,
                "holder": f.holder,
                "packages": [
                    {
                        "type": p.type,
                        "name": p.name,
                        "version": p.version,
                        "purl": p.purl,
                    }
                    for p in f.packages
                ],
            }
            for f in result.files
        ],
        "license_report": generate_license_report(result),
        "copyright_report": generate_copyright_report(result),
        "package_report": generate_package_report(result),
    }
    
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)


def find_files_by_license(result: ScanResult, license_expression: str) -> List[FileResult]:
    """
    Find all files matching a specific license expression.
    
    Args:
        result: ScanResult to search
        license_expression: License expression to match
        
    Returns:
        List of matching FileResult objects
    """
    return [
        f for f in result.files
        if f.detected_license_expression and license_expression.lower() in f.detected_license_expression.lower()
    ]


def find_files_by_extension(result: ScanResult, extension: str) -> List[FileResult]:
    """
    Find all files with a specific extension.
    
    Args:
        result: ScanResult to search
        extension: File extension (with or without dot)
        
    Returns:
        List of matching FileResult objects
    """
    ext = extension if extension.startswith(".") else f".{extension}"
    return [f for f in result.files if f.path.endswith(ext)]


def get_top_level_directories(result: ScanResult) -> Set[str]:
    """
    Get the set of top-level directories in the scanned code.
    
    Args:
        result: ScanResult to analyze
        
    Returns:
        Set of top-level directory names
    """
    directories = set()
    for f in result.files:
        parts = f.path.split("/")
        if len(parts) > 1:
            directories.add(parts[0])
    return directories


def estimate_risk_level(result: ScanResult) -> Dict:
    """
    Estimate the risk level based on license findings.
    
    Args:
        result: ScanResult to analyze
        
    Returns:
        Dictionary with risk assessment
    """
    high_risk_licenses = ["gpl", "agpl", "proprietary", "commercial", "closed"]
    medium_risk_licenses = ["lgpl", "mpl", "epl", "cddl"]
    
    high_risk_files = []
    medium_risk_files = []
    unknown_license_files = []
    
    for f in result.files:
        if not f.detected_license_expression:
            unknown_license_files.append(f)
        else:
            license_lower = f.detected_license_expression.lower()
            if any(risk in license_lower for risk in high_risk_licenses):
                high_risk_files.append(f)
            elif any(risk in license_lower for risk in medium_risk_licenses):
                medium_risk_files.append(f)
    
    # Determine overall risk
    if high_risk_files:
        risk_level = "high"
    elif medium_risk_files:
        risk_level = "medium"
    elif unknown_license_files:
        risk_level = "low"  # Unknown might be fine or might need review
    else:
        risk_level = "low"
    
    return {
        "risk_level": risk_level,
        "high_risk_files": len(high_risk_files),
        "medium_risk_files": len(medium_risk_files),
        "unknown_license_files": len(unknown_license_files),
        "high_risk_details": [
            {"path": f.path, "license": f.detected_license_expression}
            for f in high_risk_files[:20]  # Limit details
        ],
    }