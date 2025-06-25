import pytest
from fastmcp.server import FastMCP

from gateway.main import create_application


@pytest.mark.asyncio
class TestHandlerRegistration:
    """Integration tests for handler registration."""
    
    async def test_handler_registration(self):
        """Test that handlers are registered with correct names."""
        # Create a real FastMCP instance for this test
        mcp = FastMCP("TestServer")
        
        # Mock the tool method to capture registrations
        original_tool = mcp.tool
        registered_names = []
        
        def mock_tool_registration(func, name=None):
            if name:
                registered_names.append(name)
            return original_tool(func, name=name)
        
        # Replace with our capturing function
        mcp.tool = mock_tool_registration
        
        # Call the create_application function with our MCP instance
        create_application(mcp)
        
        # Verify all expected handler names were registered
        assert "EnableFactPodHandler" in registered_names
        assert "DisableFactPodHandler" in registered_names  
        assert "ListOfCategoriesHandler" in registered_names
        assert "FactsByCategoryHandler" in registered_names
