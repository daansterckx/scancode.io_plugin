"""
Exception classes for ScanCode.io client.
"""


class ScanCodeIOError(Exception):
    """Base exception for ScanCode.io client errors."""
    
    def __init__(self, message, status_code=None, response=None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class AuthenticationError(ScanCodeIOError):
    """Raised when authentication fails (401/403 responses)."""
    pass


class ProjectError(ScanCodeIOError):
    """Raised when project operations fail."""
    pass


class UploadError(ScanCodeIOError):
    """Raised when file upload fails."""
    pass


class ScanError(ScanCodeIOError):
    """Raised when scan operations fail."""
    pass


class NotFoundError(ScanCodeIOError):
    """Raised when a resource is not found (404)."""
    pass


class RateLimitError(ScanCodeIOError):
    """Raised when API rate limit is exceeded (429)."""
    pass


class ServerError(ScanCodeIOError):
    """Raised when server returns 5xx error."""
    pass