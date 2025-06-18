import json
import pytest
from fastmcp.server import FastMCP
from fastmcp import Client

from gateway.handlers.base_handler import BaseHandler


class ConcreteHandler(BaseHandler):
    """A concrete implementation of BaseHandler for testing purposes."""
    
    async def tool_method(self, name: str) -> dict:
        """Concrete implementation of the abstract method."""
        return {"message": f"Hello, {name}!"}


@pytest.fixture
def mcp_server():
    """Create a FastMCP server instance for testing."""
    server = FastMCP("TestServer")
    handler = ConcreteHandler(server)
    return server


@pytest.mark.asyncio
async def test_base_handler_registration(mcp_server):
    """Test that the handler's tool method is properly registered with the server."""
    async with Client(mcp_server) as client:
        result = await client.call_tool("tool_method", {"name": "World"})
        # Parse the TextContent response
        response = json.loads(result[0].text)
        assert response["message"] == "Hello, World!"
