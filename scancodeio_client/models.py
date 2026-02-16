"""
Data models for ScanCode.io API responses.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ScanStatus(str, Enum):
    """Possible scan statuses."""
    NOT_STARTED = "not_started"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    STOPPED = "stopped"


@dataclass
class Project:
    """Represents a ScanCode.io project."""
    
    uuid: str
    name: str
    created_date: datetime
    status: ScanStatus
    input_sources: List[Dict[str, Any]] = field(default_factory=list)
    pipelines: List[str] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)
    extra_data: Dict[str, Any] = field(default_factory=dict)
    url: Optional[str] = None
    error: Optional[str] = None
    
    @classmethod
    def from_api(cls, data: Dict[str, Any], base_url: str = "") -> "Project":
        """Create a Project instance from API response data."""
        created = data.get("created_date")
        if created and isinstance(created, str):
            created = datetime.fromisoformat(created.replace("Z", "+00:00"))
        
        return cls(
            uuid=data.get("uuid", ""),
            name=data.get("name", ""),
            created_date=created or datetime.utcnow(),
            status=ScanStatus(data.get("status", "not_started")),
            input_sources=data.get("input_sources", []),
            pipelines=data.get("pipelines", []),
            settings=data.get("settings", {}),
            extra_data=data.get("extra_data", {}),
            url=f"{base_url}/project/{data.get('uuid', '')}" if base_url else None,
            error=data.get("error"),
        )
    
    def is_complete(self) -> bool:
        """Check if the scan has completed (success or failure)."""
        return self.status in (ScanStatus.SUCCESS, ScanStatus.FAILURE, ScanStatus.STOPPED)
    
    def is_successful(self) -> bool:
        """Check if the scan completed successfully."""
        return self.status == ScanStatus.SUCCESS
    
    def __str__(self) -> str:
        return f"Project({self.name}, {self.status.value})"


@dataclass
class Package:
    """Represents a discovered package."""
    
    type: str
    namespace: Optional[str]
    name: str
    version: Optional[str]
    purl: Optional[str]
    license_expressions: List[str] = field(default_factory=list)
    copyright: Optional[str] = None
    holder: Optional[str] = None
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "Package":
        return cls(
            type=data.get("type", ""),
            namespace=data.get("namespace"),
            name=data.get("name", ""),
            version=data.get("version"),
            purl=data.get("purl"),
            license_expressions=data.get("license_expressions", []),
            copyright=data.get("copyright"),
            holder=data.get("holder"),
        )


@dataclass
class FileResult:
    """Represents scan results for a single file."""
    
    path: str
    type: str
    size: int
    sha1: Optional[str] = None
    md5: Optional[str] = None
    sha256: Optional[str] = None
    mime_type: Optional[str] = None
    file_type: Optional[str] = None
    programming_language: Optional[str] = None
    is_binary: bool = False
    is_text: bool = False
    is_archive: bool = False
    is_media: bool = False
    detected_license_expression: Optional[str] = None
    detected_license_expression_spdx: Optional[str] = None
    copyright: Optional[str] = None
    holder: Optional[str] = None
    authors: List[str] = field(default_factory=list)
    scanners: List[str] = field(default_factory=list)
    packages: List[Package] = field(default_factory=list)
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "FileResult":
        packages = [
            Package.from_api(pkg) for pkg in data.get("packages", [])
        ]
        
        return cls(
            path=data.get("path", ""),
            type=data.get("type", ""),
            size=data.get("size", 0),
            sha1=data.get("sha1"),
            md5=data.get("md5"),
            sha256=data.get("sha256"),
            mime_type=data.get("mime_type"),
            file_type=data.get("file_type"),
            programming_language=data.get("programming_language"),
            is_binary=data.get("is_binary", False),
            is_text=data.get("is_text", False),
            is_archive=data.get("is_archive", False),
            is_media=data.get("is_media", False),
            detected_license_expression=data.get("detected_license_expression"),
            detected_license_expression_spdx=data.get("detected_license_expression_spdx"),
            copyright=data.get("copyright"),
            holder=data.get("holder"),
            authors=data.get("authors", []),
            scanners=data.get("scanners", []),
            packages=packages,
        )


@dataclass
class ScanSummary:
    """Summary of scan results."""
    
    total_files: int
    total_directories: int
    total_size: int
    license_detections: int
    copyright_detections: int
    package_detections: int
    files_with_license: int
    files_with_copyright: int
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "ScanSummary":
        return cls(
            total_files=data.get("total_files", 0),
            total_directories=data.get("total_directories", 0),
            total_size=data.get("total_size", 0),
            license_detections=data.get("license_detections", 0),
            copyright_detections=data.get("copyright_detections", 0),
            package_detections=data.get("package_detections", 0),
            files_with_license=data.get("files_with_license", 0),
            files_with_copyright=data.get("files_with_copyright", 0),
        )


@dataclass
class ScanResult:
    """Complete scan results for a project."""
    
    project: Project
    files: List[FileResult]
    summary: ScanSummary
    raw_data: Dict[str, Any]
    
    @classmethod
    def from_api(cls, project: Project, data: Dict[str, Any]) -> "ScanResult":
        files_data = data.get("files", [])
        files = [FileResult.from_api(f) for f in files_data]
        
        summary_data = data.get("summary", {})
        summary = ScanSummary.from_api(summary_data)
        
        return cls(
            project=project,
            files=files,
            summary=summary,
            raw_data=data,
        )
    
    def get_files_with_licenses(self) -> List[FileResult]:
        """Get all files that have detected licenses."""
        return [f for f in self.files if f.detected_license_expression]
    
    def get_files_with_copyrights(self) -> List[FileResult]:
        """Get all files that have detected copyrights."""
        return [f for f in self.files if f.copyright]
    
    def get_packages(self) -> List[Package]:
        """Get all discovered packages."""
        packages = []
        for f in self.files:
            packages.extend(f.packages)
        return packages
    
    def get_unique_license_expressions(self) -> List[str]:
        """Get all unique license expressions found."""
        expressions = set()
        for f in self.files:
            if f.detected_license_expression:
                expressions.add(f.detected_license_expression)
        return sorted(list(expressions))