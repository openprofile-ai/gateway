"""
HTTP client implementation for making requests to external services.
"""

from typing import Any, Dict, Optional

import httpx


class AsyncHTTPClient:
    """
    HTTP client implementation using httpx.AsyncClient.
    """

    def __init__(self):
        """Initialize the HTTP client."""
        self._client = httpx.AsyncClient()

    async def get(
        self, url: str, headers: Optional[Dict[str, str]] = None, timeout: float = 10.0
    ) -> httpx.Response:
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

    async def post(
        self,
        url: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 10.0,
    ) -> httpx.Response:
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
