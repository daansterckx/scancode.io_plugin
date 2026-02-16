"""
ScanCode.io API Client

A Python client for integrating with self-hosted ScanCode.io instances.
Provides functionality to upload files, run scans, and retrieve results.
"""

from .client import ScanCodeIOClient
from .models import Project, ScanStatus, ScanResult
from .exceptions import (
    ScanCodeIOError,
    AuthenticationError,
    ProjectError,
    UploadError,
    ScanError,
)

__all__ = [
    "ScanCodeIOClient",
    "Project",
    "ScanStatus",
    "ScanResult",
    "ScanCodeIOError",
    "AuthenticationError",
    "ProjectError",
    "UploadError",
    "ScanError",
]

__version__ = "1.0.0"