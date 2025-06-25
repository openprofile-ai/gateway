import json
import pytest
from fastmcp.server import FastMCP
from fastmcp import Client

from gateway.handlers.disable_fact_pod_handler import DisableFactPodHandler


@pytest.fixture
def mcp_server():
    """Create a FastMCP server instance for testing."""
    server = FastMCP("TestServer")
    handler = DisableFactPodHandler(server)
    return server


@pytest.mark.asyncio
async def test_disable_fact_pod(mcp_server):
    """Test that the disable_fact_pod tool returns the expected structure."""
    async with Client(mcp_server) as client:
        pod_name = "test_pod"
        result = await client.call_tool("DisableFactPodHandler", {"pod_name": pod_name})
        # Parse the TextContent response
        response = json.loads(result[0].text)
        assert "status" in response
        assert response["status"] == "disabled"
        assert "pod_name" in response
        assert response["pod_name"] == pod_name
