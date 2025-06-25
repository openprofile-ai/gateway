import json
import pytest
from fastmcp import Client

from gateway.handlers.enable_fact_pod_handler import EnableFactPodHandler


@pytest.fixture
def enable_fact_pod_handler(base_mcp_server):
    """Create a EnableFactPodHandler instance for testing."""
    return EnableFactPodHandler(base_mcp_server)


@pytest.mark.asyncio
async def test_enable_fact_pod(base_mcp_server, enable_fact_pod_handler):
    """Test that the enable_fact_pod tool returns the expected structure."""
    async with Client(base_mcp_server) as client:
        pod_name = "test_pod"
        # Note: Tool name is the handler class name per project convention
        result = await client.call_tool("EnableFactPodHandler", {"pod_name": pod_name})
        # Parse the TextContent response
        response = json.loads(result[0].text)
        assert "status" in response
        assert response["status"] == "enabled"
        assert "pod_name" in response
        assert response["pod_name"] == pod_name
