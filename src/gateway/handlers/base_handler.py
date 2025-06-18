from abc import ABC, abstractmethod
from typing import Any

from fastmcp.server import FastMCP


class BaseHandler(ABC):
    def __init__(self, mcp_instance: FastMCP) -> None:
        # Register methods
        mcp_instance.tool(self.tool_method)

    @abstractmethod
    async def tool_method(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """
        Abstract method to be implemented by subclasses.
        This method should define the functionality of the tool.

        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments

        Returns:
            Dict[str, Any]: Response data from the tool
        """
        pass
