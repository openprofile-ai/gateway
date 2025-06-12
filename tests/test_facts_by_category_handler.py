import json
import pytest
from fastmcp.server import FastMCP
from fastmcp import Client

from handlers.facts_by_category_handler import FactsByCategoryHandler


@pytest.fixture
def mcp_server():
    """Create a FastMCP server instance for testing."""
    server = FastMCP("TestServer")
    handler = FactsByCategoryHandler(server)
    return server


@pytest.mark.asyncio
async def test_facts_by_category(mcp_server):
    """Test that the facts_by_category tool returns the expected structure."""
    async with Client(mcp_server) as client:
        result = await client.call_tool("tool_method", {"category_name": "animals"})
        # Parse the TextContent response
        response = json.loads(result[0].text)
        assert "facts" in response
        assert isinstance(response["facts"], list)
