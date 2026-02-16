"""
Asynchronous ScanCode.io API Client using asyncio.
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import aiohttp

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


class AsyncScanCodeIOClient:
    """
    Async client for interacting with a self-hosted ScanCode.io instance.
    
    Example:
        >>> async with AsyncScanCodeIOClient(
        ...     base_url="https://scancode.example.com",
        ...     api_key="your-api-key"
        ... ) as client:
        ...     result = await client.scan_file("/path/to/file.zip", wait=True)
        ...     print(result.summary)
    """
    
    DEFAULT_TIMEOUT = 300
    POLL_INTERVAL = 5
    
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        verify_ssl: bool = True,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        await self._init_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def _init_session(self):
        """Initialize aiohttp session."""
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Token {self.api_key}"
        
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        connector = aiohttp.TCPConnector(ssl=self.verify_ssl)
        
        self._session = aiohttp.ClientSession(
            headers=headers,
            timeout=timeout,
            connector=connector,
        )
    
    async def close(self):
        """Close the aiohttp session."""
        if self._session:
            await self._session.close()
            self._session = None
    
    def _ensure_session(self):
        if self._session is None:
            raise ScanCodeIOError("Client not initialized. Use async context manager.")
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> aiohttp.ClientResponse:
        """Make an async HTTP request."""
        self._ensure_session()
        
        url = urljoin(f"{self.base_url}/api/", endpoint.lstrip("/"))
        
        try:
            async with self._session.request(method, url, **kwargs) as response:
                # Read the response
                status = response.status
                text = await response.text()
                
                # Check for errors
                if status == 401:
                    raise AuthenticationError(
                        "Authentication failed. Check your API key.",
                        status_code=status,
                        response=text,
                    )
                elif status == 403:
                    raise AuthenticationError(
                        "Access forbidden. Check your permissions.",
                        status_code=status,
                        response=text,
                    )
                elif status == 404:
                    raise NotFoundError(
                        f"Resource not found: {endpoint}",
                        status_code=status,
                        response=text,
                    )
                elif status == 429:
                    raise RateLimitError(
                        "Rate limit exceeded. Please try again later.",
                        status_code=status,
                        response=text,
                    )
                elif 500 <= status < 600:
                    raise ServerError(
                        f"Server error: {status}",
                        status_code=status,
                        response=text,
                    )
                elif status >= 400:
                    raise ScanCodeIOError(
                        f"API request failed: {status} - {text}",
                        status_code=status,
                        response=text,
                    )
                
                # Create a response-like object
                return MockResponse(status, text)
                
        except asyncio.TimeoutError as e:
            raise ScanCodeIOError(f"Request timed out: {e}")
        except aiohttp.ClientError as e:
            raise ScanCodeIOError(f"Request failed: {e}")
    
    async def _get_json(self, endpoint: str) -> Dict[str, Any]:
        """Make async GET request and return JSON."""
        response = await self._make_request("GET", endpoint)
        return response.json()
    
    async def _post_json(
        self,
        endpoint: str,
        data: Optional[Dict] = None,
        files: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Make async POST request and return JSON."""
        if files:
            # Handle multipart form data for file uploads
            form = aiohttp.FormData()
            for key, (filename, file_data) in files.items():
                form.add_field(key, file_data, filename=filename)
            if data:
                for key, value in data.items():
                    form.add_field(key, value)
            
            response = await self._make_request("POST", endpoint, data=form)
        else:
            response = await self._make_request("POST", endpoint, data=data)
        
        return response.json()
    
    async def create_project(
        self,
        name: str,
        pipelines: Optional[List[str]] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> Project:
        """Create a new project."""
        if pipelines is None:
            pipelines = ["scan_package"]
        
        data = {"name": name, "pipelines": pipelines}
        if settings:
            data.update(settings)
        
        try:
            response_data = await self._post_json("projects/", data=data)
            return Project.from_api(response_data, self.base_url)
        except ScanCodeIOError as e:
            raise ProjectError(f"Failed to create project: {e}") from e
    
    async def get_project(self, project_uuid: str) -> Project:
        """Get a project by UUID."""
        try:
            data = await self._get_json(f"projects/{project_uuid}/")
            return Project.from_api(data, self.base_url)
        except NotFoundError:
            raise
        except ScanCodeIOError as e:
            raise ProjectError(f"Failed to get project: {e}") from e
    
    async def upload_file(
        self,
        project_uuid: str,
        file_path: Union[str, Path],
        filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Upload a file to a project."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise UploadError(f"File not found: {file_path}")
        
        upload_name = filename or file_path.name
        
        try:
            file_content = file_path.read_bytes()
            files = {"upload_file": (upload_name, file_content)}
            data = {"description": f"Uploaded {upload_name}"}
            
            response_data = await self._post_json(
                f"projects/{project_uuid}/upload/",
                files=files,
                data=data,
            )
            return response_data
        except ScanCodeIOError as e:
            raise UploadError(f"Failed to upload file: {e}") from e
    
    async def execute_pipeline(self, project_uuid: str) -> Dict[str, Any]:
        """Start pipeline execution."""
        try:
            return await self._post_json(f"projects/{project_uuid}/execute_pipeline/")
        except ScanCodeIOError as e:
            raise ScanError(f"Failed to start pipeline: {e}") from e
    
    async def wait_for_completion(
        self,
        project_uuid: str,
        timeout: Optional[int] = None,
        poll_interval: Optional[int] = None,
    ) -> Project:
        """Wait for scan completion."""
        timeout = timeout or 3600
        poll_interval = poll_interval or self.POLL_INTERVAL
        
        start_time = asyncio.get_event_loop().time()
        
        while True:
            project = await self.get_project(project_uuid)
            
            if project.is_complete():
                return project
            
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                raise ScanError(
                    f"Scan timed out after {timeout} seconds. "
                    f"Current status: {project.status.value}"
                )
            
            await asyncio.sleep(poll_interval)
    
    async def get_scan_results(self, project_uuid: str) -> ScanResult:
        """Get scan results."""
        project = await self.get_project(project_uuid)
        
        if project.status not in (ScanStatus.SUCCESS, ScanStatus.FAILURE):
            raise ScanError(
                f"Scan not complete. Current status: {project.status.value}"
            )
        
        try:
            data = await self._get_json(f"projects/{project_uuid}/results/")
            return ScanResult.from_api(project, data)
        except ScanCodeIOError as e:
            raise ScanError(f"Failed to get results: {e}") from e
    
    async def scan_file(
        self,
        file_path: Union[str, Path],
        project_name: Optional[str] = None,
        pipelines: Optional[List[str]] = None,
        wait: bool = True,
        timeout: Optional[int] = None,
        delete_on_complete: bool = False,
    ) -> ScanResult:
        """End-to-end file scanning."""
        file_path = Path(file_path)
        name = project_name or file_path.name
        
        project = await self.create_project(name=name, pipelines=pipelines)
        
        try:
            await self.upload_file(project.uuid, file_path)
            await self.execute_pipeline(project.uuid)
            
            if wait:
                project = await self.wait_for_completion(project.uuid, timeout=timeout)
                
                if not project.is_successful():
                    raise ScanError(
                        f"Scan failed: {project.error or 'Unknown error'}"
                    )
                
                result = await self.get_scan_results(project.uuid)
            else:
                result = ScanResult(
                    project=project,
                    files=[],
                    summary={},
                    raw_data={},
                )
            
            return result
            
        except Exception:
            if delete_on_complete:
                try:
                    await self._delete_project(project.uuid)
                except Exception:
                    pass
            raise
        finally:
            if delete_on_complete and wait:
                try:
                    await self._delete_project(project.uuid)
                except Exception:
                    pass
    
    async def _delete_project(self, project_uuid: str) -> None:
        """Delete a project."""
        try:
            await self._make_request("DELETE", f"projects/{project_uuid}/")
        except ScanCodeIOError as e:
            raise ProjectError(f"Failed to delete project: {e}") from e


class MockResponse:
    """Mock response object for async compatibility."""
    
    def __init__(self, status: int, text: str):
        self.status = status
        self._text = text
    
    def json(self) -> Dict:
        import json
        return json.loads(self._text)
    
    @property
    def content(self) -> bytes:
        return self._text.encode()
    
    def __await__(self):
        async def _await():
            return self
        return _await().__await__()