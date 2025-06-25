from typing import List

from gateway.db.repository import Repository


class DynamoDBRepository(Repository):
    """Repository implementation using AWS DynamoDB for data storage."""

    def __init__(self, table_name: str = "categories", region_name: str = "us-east-1"):
        """Initialize the DynamoDB repository.

        Args:
            table_name: Name of the DynamoDB table to use
            region_name: AWS region where the table is located
        """
        self.table_name = table_name
        self.region_name = region_name
        self._dynamodb = None
        self._table = None

    async def get_categories(self) -> List[str]:
        """
        Fetch all categories from the DynamoDB table.

        Returns:
            List of category names as strings.

        Raises:
            Exception: If there's an error accessing DynamoDB
        """
        # In a real implementation, this would make an async call to DynamoDB
        # For now, we'll return mock data
        return ["Category1", "Category2", "Category3"]
