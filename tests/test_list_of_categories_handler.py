import json
import pytest
from fastmcp.server import FastMCP
from fastmcp import Client

from gateway.handlers.list_of_categories_handler import ListOfCategoriesHandler


@pytest.fixture
def mcp_server():
    """Create a FastMCP server instance for testing."""
    server = FastMCP("TestServer")
    handler = ListOfCategoriesHandler(server)
    return server


@pytest.mark.asyncio
async def test_list_of_categories(mcp_server):
    """Test that the list_of_categories tool returns the expected structure."""
    async with Client(mcp_server) as client:
        result = await client.call_tool("tool_method")
        # Parse the TextContent response
        response = json.loads(result[0].text)
        assert "categories" in response
        assert isinstance(response["categories"], list)
