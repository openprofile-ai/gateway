from abc import ABC, abstractmethod
from typing import Any

from fastmcp.server import FastMCP

from gateway.config import settings
from gateway.db.dynamodb_repository import DynamoDBRepository


class BaseHandler(ABC):
    def __init__(self, mcp_instance: FastMCP) -> None:
        # Register methods
        mcp_instance.tool(self.tool_method, name=self.__class__.__name__)
        # Initialize repository with configuration from settings
        self.repository = DynamoDBRepository(
            table_name=settings.db_table_name, region_name=settings.db_region_name
        )

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
