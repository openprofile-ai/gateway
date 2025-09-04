from typing import Dict, Any, Optional, List
from gateway.db.repository import Repository
from gateway.exceptions import RepositoryError


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
            RepositoryError: If there's an error accessing DynamoDB
        """
        try:
            # In a real implementation, this would make an async call to DynamoDB
            # For now, we'll return mock data
            return ["Category1", "Category2", "Category3"]
        except Exception as error:
            raise RepositoryError(
                f"Failed to fetch categories: {str(error)}") from error

    async def get_fact_pod_config(self, site: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a fact pod site from DynamoDB.

        Args:
            site: Domain of the site

        Returns:
            Configuration dictionary or None if not found

        Raises:
            RepositoryError: If there's an error accessing DynamoDB
        """
        try:
            # In a real implementation, this would query DynamoDB for the site configuration
            # For now, return mock data for known sites or None for unknown sites
            if site == "example.com":
                return {"site": site, "enabled": True, "created_at": "2025-06-25T12:00:00Z"}
            return None
        except Exception as error:
            raise RepositoryError(
                f"Failed to get fact pod configuration for site {site}: {str(error)}") from error

    async def get_user_site_connection(
        self, user_id: str, site: str
    ) -> Optional[Dict[str, Any]]:
        """
        Check if a user has already enabled a site's fact pod.

        Args:
            user_id: ID of the user
            site: Domain of the site

        Returns:
            Connection details if exists, otherwise None

        Raises:
            RepositoryError: If there's an error accessing DynamoDB
        """
        try:
            # In a real implementation, this would query DynamoDB for the user-site connection
            # For now, return None to indicate no existing connection
            return None
        except Exception as error:
            raise RepositoryError(
                f"Failed to get user-site connection for user {user_id} and site {site}: {str(error)}") from error

    async def store_oauth_config(
        self,
        user_id: str,
        site: str,
        client_id: str,
        client_secret: str,
        redirect_url: str,
    ) -> None:
        """
        Store OAuth configuration for a user-site connection in DynamoDB.

        Args:
            user_id: ID of the user
            site: Domain of the site
            client_id: OAuth client ID
            client_secret: OAuth client secret
            redirect_url: OAuth redirect URL

        Raises:
            RepositoryError: If there's an error accessing DynamoDB
        """
        try:
            # In a real implementation, this would store the OAuth config in DynamoDB
            # For now, just log the operation
            print(f"Storing OAuth config for user {user_id} and site {site}")
            # Item would be created with user_id and site as keys, plus the OAuth details
            # self._table.put_item(Item={...})
        except Exception as error:
            raise RepositoryError(
                f"Failed to store OAuth configuration for user {user_id} and site {site}: {str(error)}") from error

    async def store_oauth_state(self, state: str, user_id: str, site: str) -> None:
        """
        Store OAuth state for CSRF protection in DynamoDB.

        Args:
            state: Random state string
            user_id: ID of the user
            site: Domain of the site

        Raises:
            RepositoryError: If there's an error accessing DynamoDB
        """
        try:
            # In a real implementation, this would store the state in DynamoDB with TTL
            # For now, just log the operation
            print(
                f"Storing OAuth state {state} for user {user_id} and site {site}")
            # Item would be created with state as key, plus user_id, site, and expiration timestamp
            # self._table.put_item(Item={...})
        except Exception as error:
            raise RepositoryError(
                f"Failed to store OAuth state for user {user_id} and site {site}: {str(error)}") from error
