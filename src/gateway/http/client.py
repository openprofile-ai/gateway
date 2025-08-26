"""
HTTP client interface and implementation for making requests to external services.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import httpx


class HTTPClientInterface(ABC):
    """
    Interface for making HTTP requests to external services.

    This abstraction allows for easier testing and mocking of HTTP requests.
    """

    @abstractmethod
    async def get(self, url: str, headers: Optional[Dict[str, str]] = None,
                  timeout: float = 10.0) -> httpx.Response:
        """
        Make a GET request to the specified URL.

        Args:
            url: The URL to make the request to
            headers: Optional headers to include with the request
            timeout: Request timeout in seconds

        Returns:
            HTTP response
        """
        pass

    @abstractmethod
    async def post(self, url: str, json: Optional[Dict[str, Any]] = None,
                   headers: Optional[Dict[str, str]] = None,
                   timeout: float = 10.0) -> httpx.Response:
        """
        Make a POST request to the specified URL.

        Args:
            url: The URL to make the request to
            json: JSON data to send in the request body
            headers: Optional headers to include with the request
            timeout: Request timeout in seconds

        Returns:
            HTTP response
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the client and release resources."""
        pass


class AsyncHTTPClient(HTTPClientInterface):
    """
    Implementation of the HTTP client interface using httpx.AsyncClient.
    """

    def __init__(self):
        """Initialize the HTTP client."""
        self._client = httpx.AsyncClient()

    async def get(self, url: str, headers: Optional[Dict[str, str]] = None,
                  timeout: float = 10.0) -> httpx.Response:
        """
        Make a GET request to the specified URL.

        Args:
            url: The URL to make the request to
            headers: Optional headers to include with the request
            timeout: Request timeout in seconds

        Returns:
            HTTP response
        """
        return await self._client.get(url, headers=headers, timeout=timeout)

    async def post(self, url: str, json: Optional[Dict[str, Any]] = None,
                   headers: Optional[Dict[str, str]] = None,
                   timeout: float = 10.0) -> httpx.Response:
        """
        Make a POST request to the specified URL.

        Args:
            url: The URL to make the request to
            json: JSON data to send in the request body
            headers: Optional headers to include with the request
            timeout: Request timeout in seconds

        Returns:
            HTTP response
        """
        return await self._client.post(url, json=json, headers=headers, timeout=timeout)

    async def close(self) -> None:
        """Close the HTTP client and release resources."""
        if not self._client.is_closed:
            await self._client.aclose()
