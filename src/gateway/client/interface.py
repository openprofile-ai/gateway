"""
MCP client interface and implementation for making requests to MCP-enabled services.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from fastmcp.server import FastMCP
from fastmcp import Client as FastMCPClient


class MCPClientInterface(ABC):
    """
    Interface for making MCP requests to external services.

    This abstraction allows for easier testing and mocking of MCP requests.
    """

    @abstractmethod
    async def call_tool(self, server_name: str, params: Dict[str, Any]) -> List[Any]:
        """
        Call a tool on an MCP server.

        Args:
            server_name: The name of the MCP server to call
            params: Parameters to pass to the tool

        Returns:
            List of tool response elements
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the client and release resources."""
        pass


class AsyncMCPClient(MCPClientInterface):
    """
    Implementation of the MCP client interface using FastMCP.
    """

    def __init__(self, mcp_instance: FastMCP):
        """
        Initialize the MCP client.

        Args:
            mcp_instance: The FastMCP instance to use for requests
        """
        self._mcp = mcp_instance
        self._client = None

    @property
    def client(self) -> FastMCPClient:
        """
        Get the FastMCP client.

        Returns:
            A FastMCPClient instance
        """
        if self._client is None:
            self._client = FastMCPClient(self._mcp)
        return self._client

    async def call_tool(self, server_name: str, params: Dict[str, Any]) -> List[Any]:
        """
        Call a tool on an MCP server.

        Args:
            server_name: The name of the MCP server to call
            params: Parameters to pass to the tool

        Returns:
            List of tool response elements
        """
        async with self.client as client:
            # Determine the tool name based on the path if specified
            tool_name = server_name
            if "path" in params:
                # For REST-like interfaces, we can use path-based routing
                # Call the appropriate handler based on the path
                # Note: This depends on how the target MCP server has registered its tools
                path = params.get("path", "")
                if path.startswith("/openprofile/oauth/register"):
                    tool_name = "RegisterClientHandler"
                elif path.startswith("/openprofile/oauth/jwks"):
                    tool_name = "JWKSHandler"

            return await client.call_tool(tool_name, params)

    async def close(self) -> None:
        """Close the MCP client and release resources."""
        if self._client is not None:
            await self._client.aclose()
