import json
import pytest
from fastmcp import Client

from gateway.handlers.list_of_categories_handler import ListOfCategoriesHandler


@pytest.fixture
def list_of_categories_handler(base_mcp_server):
    """Create a ListOfCategoriesHandler instance for testing."""
    return ListOfCategoriesHandler(base_mcp_server)


@pytest.mark.asyncio
async def test_list_of_categories(base_mcp_server, list_of_categories_handler):
    """Test that the list_of_categories tool returns the expected structure."""
    async with Client(base_mcp_server) as client:
        # Note: We call the tool using the handler class name per project convention
        result = await client.call_tool("ListOfCategoriesHandler")
        # Parse the TextContent response
        response = json.loads(result[0].text)
        assert "categories" in response
        assert isinstance(response["categories"], list)
