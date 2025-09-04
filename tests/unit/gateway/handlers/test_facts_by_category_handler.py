import json
import pytest
from fastmcp import Client

from gateway.handlers.facts_by_category_handler import FactsByCategoryHandler


@pytest.fixture
def facts_by_category_handler(base_mcp_server):
    """Create a FactsByCategoryHandler instance for testing."""
    return FactsByCategoryHandler(base_mcp_server)


@pytest.mark.asyncio
async def test_facts_by_category(base_mcp_server, facts_by_category_handler):
    """Test that the facts_by_category tool returns the expected structure."""
    async with Client(base_mcp_server) as client:
        # Note: Tool name is the handler class name per project convention
        result = await client.call_tool(
            "FactsByCategoryHandler", {"category_name": "animals"}
        )
        # Use the structured response directly
        response = result.data
        assert "facts" in response
        assert isinstance(response["facts"], list)
