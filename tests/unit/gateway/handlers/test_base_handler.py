import json
import pytest
from fastmcp import Client

from gateway.handlers.base_handler import BaseHandler


class ConcreteHandler(BaseHandler):
    """A concrete implementation of BaseHandler for testing purposes."""
    
    async def tool_method(self, name: str) -> dict:
        """Concrete implementation of the abstract method."""
        return {"message": f"Hello, {name}!"}


@pytest.fixture
def concrete_handler(base_mcp_server):
    """Create a ConcreteHandler instance for testing."""
    return ConcreteHandler(base_mcp_server)


@pytest.mark.asyncio
async def test_base_handler_registration(base_mcp_server, concrete_handler):
    """Test that the handler's tool method is properly registered with the server."""
    async with Client(base_mcp_server) as client:
        # Note: We call the tool using the handler class name, not the method name
        result = await client.call_tool("ConcreteHandler", {"name": "World"})
        # Parse the TextContent response
        response = json.loads(result[0].text)
        assert response["message"] == "Hello, World!"
