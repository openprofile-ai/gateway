import json
import pytest
from fastmcp import Client

from gateway.handlers.disable_fact_pod_handler import DisableFactPodHandler


@pytest.fixture
def disable_fact_pod_handler(base_mcp_server):
    """Create a DisableFactPodHandler instance for testing."""
    return DisableFactPodHandler(base_mcp_server)


@pytest.mark.asyncio
async def test_disable_fact_pod(base_mcp_server, disable_fact_pod_handler):
    """Test that the disable_fact_pod tool returns the expected structure."""
    async with Client(base_mcp_server) as client:
        pod_name = "test_pod"
        # Note: Tool name is the handler class name per project convention
        result = await client.call_tool("DisableFactPodHandler", {"pod_name": pod_name})
        # Parse the TextContent response
        response = json.loads(result[0].text)
        assert "status" in response
        assert response["status"] == "disabled"
        assert "pod_name" in response
        assert response["pod_name"] == pod_name
