"""
Shared test fixtures for all tests.
"""

import pytest
from fastmcp.server import FastMCP


@pytest.fixture
def base_mcp_server():
    """Create a base FastMCP server instance that can be used in multiple tests."""
    return FastMCP("TestServer")
