from fastmcp.server import FastMCP

from tools.disable_fact_pod_handler import DisableFactPodHandler
from tools.enable_fact_pod_handler import EnableFactPodHandler
from tools.facts_by_category_handler import FactsByCategoryHandler
from tools.list_of_categories_handler import ListOfCategoriesHandler


def create_application(mcp_instance: FastMCP = None) -> FastMCP:
    """Create and configure the FastMCP application.

    Args:
        mcp_instance: Optional FastMCP instance (creates one if not provided)

    Returns:
        Configured FastMCP instance with all handlers registered
    """
    # Create a new instance if none is provided, or use the provided one
    # This pattern is primarily useful for testing, where a test-specific
    # instance can be passed in
    mcp = mcp_instance if mcp_instance is not None else FastMCP("OpenProfile.AI")

    # Initialize and register all handlers
    EnableFactPodHandler(mcp)
    DisableFactPodHandler(mcp)
    ListOfCategoriesHandler(mcp)
    FactsByCategoryHandler(mcp)

    return mcp


# Create the main application instance with default configuration
mcp = create_application()

if __name__ == "__main__":
    mcp.run()
