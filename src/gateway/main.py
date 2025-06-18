from fastmcp.server import FastMCP

from gateway.handlers.disable_fact_pod_handler import DisableFactPodHandler
from gateway.handlers.enable_fact_pod_handler import EnableFactPodHandler
from gateway.handlers.facts_by_category_handler import FactsByCategoryHandler
from gateway.handlers.list_of_categories_handler import ListOfCategoriesHandler

mcp = FastMCP("OpenProfile.AI")
# The methods are automatically registered when creating the instance
enable_fact_pod_handler = EnableFactPodHandler(mcp)
disable_fact_pod_handler = DisableFactPodHandler(mcp)
list_of_categories_handler = ListOfCategoriesHandler(mcp)
factsByCategoryHandler = FactsByCategoryHandler(mcp)

if __name__ == "__main__":
    mcp.run()
