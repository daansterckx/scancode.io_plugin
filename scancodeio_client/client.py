"""
Main ScanCode.io API Client.
"""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import requests

from .exceptions import (
    AuthenticationError,
    NotFoundError,
    ProjectError,
    RateLimitError,
    ScanCodeIOError,
    ScanError,
    ServerError,
    UploadError,
)
from .models import Project, ScanResult, ScanStatus


class ScanCodeIOClient:
    """
    Client for interacting with a self-hosted ScanCode.io instance.
    
    Example:
        >>> client = ScanCodeIOClient(
        ...     base_url="https://scancode.example.com",
        ...     api_key="your-api-key"
        ... )
        >>> result = client.scan_file("/path/to/file.zip", wait=True)
        >>> print(result.summary)
    """
    
    DEFAULT_TIMEOUT = 300  # 5 minutes for file uploads
    POLL_INTERVAL = 5  # seconds between status checks
    
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        verify_ssl: bool = True,
    ):
        """
        Initialize the ScanCode.io client.
        
        Args:
            base_url: URL of the ScanCode.io instance (e.g., "https://scancode.example.com")
            api_key: API key for authentication (if required by your instance)
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self._session = requests.Session()
        
        # Set default headers
        self._session.headers.update({
            "Accept": "application/json",
        })
        
        if api_key:
            self._session.headers["Authorization"] = f"Token {api_key}"
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> requests.Response:
        """
        Make an HTTP request to the API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint (will be appended to base_url)
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object
            
        Raises:
            ScanCodeIOError: If the request fails
        """
        url = urljoin(f"{self.base_url}/api/", endpoint.lstrip("/"))
        
        try:
            response = self._session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                verify=self.verify_ssl,
                **kwargs
            )
        except requests.exceptions.Timeout as e:
            raise ScanCodeIOError(f"Request timed out: {e}")
        except requests.exceptions.ConnectionError as e:
            raise ScanCodeIOError(f"Connection error: {e}")
        except requests.exceptions.RequestException as e:
            raise ScanCodeIOError(f"Request failed: {e}")
        
        # Handle HTTP errors
        if response.status_code == 401:
            raise AuthenticationError(
                "Authentication failed. Check your API key.",
                status_code=response.status_code,
                response=response.text,
            )
        elif response.status_code == 403:
            raise AuthenticationError(
                "Access forbidden. Check your permissions.",
                status_code=response.status_code,
                response=response.text,
            )
        elif response.status_code == 404:
            raise NotFoundError(
                f"Resource not found: {endpoint}",
                status_code=response.status_code,
                response=response.text,
            )
        elif response.status_code == 429:
            raise RateLimitError(
                "Rate limit exceeded. Please try again later.",
                status_code=response.status_code,
                response=response.text,
            )
        elif 500 <= response.status_code < 600:
            raise ServerError(
                f"Server error: {response.status_code}",
                status_code=response.status_code,
                response=response.text,
            )
        elif not response.ok:
            raise ScanCodeIOError(
                f"API request failed: {response.status_code} - {response.text}",
                status_code=response.status_code,
                response=response.text,
            )
        
        return response
    
    def _get_json(self, endpoint: str) -> Dict[str, Any]:
        """Make a GET request and return JSON."""
        response = self._make_request("GET", endpoint)
        return response.json()
    
    def _post_json(
        self,
        endpoint: str,
        data: Optional[Dict] = None,
        files: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Make a POST request and return JSON."""
        kwargs = {}
        if data:
            kwargs["data"] = data
        if files:
            kwargs["files"] = files
        
        response = self._make_request("POST", endpoint, **kwargs)
        return response.json()
    
    def _delete(self, endpoint: str) -> None:
        """Make a DELETE request."""
        self._make_request("DELETE", endpoint)
    
    def create_project(
        self,
        name: str,
        pipelines: Optional[List[str]] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> Project:
        """
        Create a new project.
        
        Args:
            name: Project name
            pipelines: List of pipeline names to run (default: ["scan_package"])
            settings: Additional project settings
            
        Returns:
            Created Project instance
        """
        if pipelines is None:
            pipelines = ["scan_package"]
        
        data = {
            "name": name,
            "pipelines": pipelines,
        }
        
        if settings:
            data.update(settings)
        
        try:
            response_data = self._post_json("projects/", data=data)
            return Project.from_api(response_data, self.base_url)
        except ScanCodeIOError as e:
            raise ProjectError(f"Failed to create project: {e}") from e
    
    def get_project(self, project_uuid: str) -> Project:
        """
        Get a project by UUID.
        
        Args:
            project_uuid: Project UUID
            
        Returns:
            Project instance
        """
        try:
            data = self._get_json(f"projects/{project_uuid}/")
            return Project.from_api(data, self.base_url)
        except NotFoundError:
            raise
        except ScanCodeIOError as e:
            raise ProjectError(f"Failed to get project: {e}") from e
    
    def list_projects(self, limit: int = 100) -> List[Project]:
        """
        List all projects.
        
        Args:
            limit: Maximum number of projects to return
            
        Returns:
            List of Project instances
        """
        try:
            data = self._get_json(f"projects/?limit={limit}")
            results = data.get("results", [])
            return [Project.from_api(p, self.base_url) for p in results]
        except ScanCodeIOError as e:
            raise ProjectError(f"Failed to list projects: {e}") from e
    
    def delete_project(self, project_uuid: str) -> None:
        """
        Delete a project.
        
        Args:
            project_uuid: Project UUID
        """
        try:
            self._delete(f"projects/{project_uuid}/")
        except NotFoundError:
            raise
        except ScanCodeIOError as e:
            raise ProjectError(f"Failed to delete project: {e}") from e
    
    def upload_file(
        self,
        project_uuid: str,
        file_path: Union[str, Path],
        filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Upload a file to a project.
        
        Args:
            project_uuid: Project UUID
            file_path: Path to the file to upload
            filename: Optional filename override
            
        Returns:
            API response data
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise UploadError(f"File not found: {file_path}")
        
        upload_name = filename or file_path.name
        
        try:
            with open(file_path, "rb") as f:
                files = {"upload_file": (upload_name, f)}
                data = {"description": f"Uploaded {upload_name}"}
                
                response_data = self._post_json(
                    f"projects/{project_uuid}/upload/",
                    files=files,
                    data=data,
                )
                return response_data
        except ScanCodeIOError as e:
            raise UploadError(f"Failed to upload file: {e}") from e
        except IOError as e:
            raise UploadError(f"Failed to read file: {e}") from e
    
    def execute_pipeline(self, project_uuid: str) -> Dict[str, Any]:
        """
        Start pipeline execution for a project.
        
        Args:
            project_uuid: Project UUID
            
        Returns:
            API response data
        """
        try:
            return self._post_json(f"projects/{project_uuid}/execute_pipeline/")
        except ScanCodeIOError as e:
            raise ScanError(f"Failed to start pipeline: {e}") from e
    
    def get_scan_results(
        self,
        project_uuid: str,
        format: str = "json",
    ) -> ScanResult:
        """
        Get scan results for a project.
        
        Args:
            project_uuid: Project UUID
            format: Result format (json, xlsx, spdx, etc.)
            
        Returns:
            ScanResult instance
        """
        project = self.get_project(project_uuid)
        
        if project.status not in (ScanStatus.SUCCESS, ScanStatus.FAILURE):
            raise ScanError(
                f"Scan not complete. Current status: {project.status.value}"
            )
        
        try:
            if format == "json":
                data = self._get_json(f"projects/{project_uuid}/results/")
            else:
                # For other formats, return raw response
                response = self._make_request(
                    "GET",
                    f"projects/{project_uuid}/results/?format={format}",
                )
                data = {"raw_content": response.content, "format": format}
            
            return ScanResult.from_api(project, data)
        except ScanCodeIOError as e:
            raise ScanError(f"Failed to get results: {e}") from e
    
    def wait_for_completion(
        self,
        project_uuid: str,
        timeout: Optional[int] = None,
        poll_interval: Optional[int] = None,
    ) -> Project:
        """
        Wait for a project scan to complete.
        
        Args:
            project_uuid: Project UUID
            timeout: Maximum time to wait (seconds)
            poll_interval: Seconds between status checks
            
        Returns:
            Project instance with final status
            
        Raises:
            ScanError: If scan fails or times out
        """
        timeout = timeout or 3600  # Default 1 hour
        poll_interval = poll_interval or self.POLL_INTERVAL
        
        start_time = time.time()
        
        while True:
            project = self.get_project(project_uuid)
            
            if project.is_complete():
                return project
            
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise ScanError(
                    f"Scan timed out after {timeout} seconds. "
                    f"Current status: {project.status.value}"
                )
            
            time.sleep(poll_interval)
    
    def scan_file(
        self,
        file_path: Union[str, Path],
        project_name: Optional[str] = None,
        pipelines: Optional[List[str]] = None,
        wait: bool = True,
        timeout: Optional[int] = None,
        delete_on_complete: bool = False,
    ) -> ScanResult:
        """
        Convenience method to scan a file end-to-end.
        
        This method:
        1. Creates a project
        2. Uploads the file
        3. Starts the pipeline
        4. Waits for completion (if wait=True)
        5. Retrieves and returns results
        6. Optionally deletes the project
        
        Args:
            file_path: Path to the file to scan
            project_name: Optional project name (defaults to filename)
            pipelines: List of pipelines to run
            wait: Whether to wait for scan completion
            timeout: Maximum time to wait
            delete_on_complete: Whether to delete the project after scanning
            
        Returns:
            ScanResult with complete scan results
        """
        file_path = Path(file_path)
        name = project_name or file_path.name
        
        # Create project
        project = self.create_project(name=name, pipelines=pipelines)
        
        try:
            # Upload file
            self.upload_file(project.uuid, file_path)
            
            # Start pipeline
            self.execute_pipeline(project.uuid)
            
            if wait:
                # Wait for completion
                project = self.wait_for_completion(project.uuid, timeout=timeout)
                
                if not project.is_successful():
                    raise ScanError(
                        f"Scan failed: {project.error or 'Unknown error'}"
                    )
                
                # Get results
                result = self.get_scan_results(project.uuid)
            else:
                # Return empty result if not waiting
                result = ScanResult(
                    project=project,
                    files=[],
                    summary={},
                    raw_data={},
                )
            
            return result
            
        except Exception:
            # Clean up on error if requested
            if delete_on_complete:
                try:
                    self.delete_project(project.uuid)
                except Exception:
                    pass
            raise
        finally:
            # Clean up after successful scan if requested
            if delete_on_complete and wait:
                try:
                    self.delete_project(project.uuid)
                except Exception:
                    pass