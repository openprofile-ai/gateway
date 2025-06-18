import json
import pytest
from fastmcp.server import FastMCP
from fastmcp import Client

from gateway.handlers.enable_fact_pod_handler import EnableFactPodHandler


@pytest.fixture
def mcp_server():
    """Create a FastMCP server instance for testing."""
    server = FastMCP("TestServer")
    handler = EnableFactPodHandler(server)
    return server


@pytest.mark.asyncio
async def test_enable_fact_pod(mcp_server):
    """Test that the enable_fact_pod tool returns the expected structure."""
    async with Client(mcp_server) as client:
        pod_name = "test_pod"
        result = await client.call_tool("tool_method", {"pod_name": pod_name})
        # Parse the TextContent response
        response = json.loads(result[0].text)
        assert "status" in response
        assert response["status"] == "enabled"
        assert "pod_name" in response
        assert response["pod_name"] == pod_name
