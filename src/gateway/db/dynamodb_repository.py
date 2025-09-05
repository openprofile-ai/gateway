from typing import Dict, Any, Optional, List
import time
import logging
import aioboto3
from boto3.dynamodb.conditions import Key
from gateway.db.repository import Repository
from gateway.exceptions import RepositoryError
from gateway.config import settings


logger = logging.getLogger(__name__)


class DynamoDBRepository(Repository):
    """Repository implementation using AWS DynamoDB for data storage."""

    def __init__(
        self,
        table_name: str = None,
        region_name: str = None,
        fact_pod_config_table_name: str = None,
    ):
        """Initialize the DynamoDB repository.

        Args:
            table_name: Name of the primary DynamoDB table to use (defaults to config setting)
            region_name: AWS region where the tables are located (defaults to config setting)
            fact_pod_config_table_name: Name of the table for fact pod configs (defaults to config setting)
        """
        self.table_name = (
            table_name if table_name is not None else settings.db_table_name
        )
        self.fact_pod_config_table_name = (
            fact_pod_config_table_name
            if fact_pod_config_table_name is not None
            else settings.fact_pod_config_table_name
        )
        self.region_name = (
            region_name if region_name is not None else settings.db_region_name
        )
        self._session = None
        self._resource = None
        self._tables = {}

    async def _get_table(self, table_name: str = None):
        """Get or create a DynamoDB table resource.

        Args:
            table_name: Name of the table to get, defaults to primary table

        Returns:
            The DynamoDB table resource

        Raises:
            RepositoryError: If unable to connect to DynamoDB
        """
        if table_name is None:
            table_name = self.table_name

        if table_name not in self._tables:
            try:
                # Create a new session if one doesn't exist
                if self._session is None:
                    self._session = aioboto3.Session()

                # Create a DynamoDB resource using the session if not already created
                if self._resource is None:
                    self._resource = await self._session.resource(
                        "dynamodb", region_name=self.region_name
                    ).__aenter__()

                # Get a reference to the requested table
                self._tables[table_name] = await self._resource.Table(table_name)
                logger.debug(
                    f"Connected to DynamoDB table {table_name} in {self.region_name}"
                )
            except Exception as error:
                logger.error(
                    f"Failed to connect to DynamoDB table {table_name}: {str(error)}"
                )
                raise RepositoryError(
                    f"Failed to connect to DynamoDB: {str(error)}"
                ) from error

        return self._tables[table_name]

    async def close(self):
        """Close the DynamoDB resource connection."""
        if self._resource:
            try:
                await self._resource.__aexit__(None, None, None)
                self._resource = None
                self._tables = {}
                logger.debug("Closed DynamoDB resource connection")
            except Exception as error:
                logger.error(f"Error closing DynamoDB connection: {str(error)}")

    async def get_categories(self) -> List[str]:
        """
        Fetch all categories from the DynamoDB table.

        Returns:
            List of category names as strings.

        Raises:
            RepositoryError: If there's an error accessing DynamoDB
        """
        try:
            table = await self._get_table()

            # Scan the table with a filter for item_type = 'category'
            response = await table.scan(
                FilterExpression=Key("item_type").eq("category")
            )

            # Extract category names from items
            categories = [item["name"] for item in response.get("Items", [])]

            # Handle pagination if there are more results
            while "LastEvaluatedKey" in response:
                response = await table.scan(
                    FilterExpression=Key("item_type").eq("category"),
                    ExclusiveStartKey=response["LastEvaluatedKey"],
                )
                categories.extend([item["name"] for item in response.get("Items", [])])

            logger.debug(f"Retrieved {len(categories)} categories")
            return categories

        except Exception as error:
            logger.error(f"Failed to fetch categories: {str(error)}")
            raise RepositoryError(
                f"Failed to fetch categories: {str(error)}"
            ) from error

    async def get_fact_pod_config(self, site: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a fact pod site from the fact pod config DynamoDB table.

        Args:
            site: Domain of the site

        Returns:
            Configuration dictionary or None if not found

        Raises:
            RepositoryError: If there's an error accessing DynamoDB
        """
        try:
            # Use the dedicated fact pod config table
            table = await self._get_table(self.fact_pod_config_table_name)

            # Query for the site configuration
            response = await table.get_item(Key={"site": site})

            # Return the item if found, otherwise None
            if "Item" in response:
                return response["Item"]
            return None

        except Exception as error:
            logger.error(
                f"Failed to get fact pod configuration for site {site}: {str(error)}"
            )
            raise RepositoryError(
                f"Failed to get fact pod configuration for site {site}: {str(error)}"
            ) from error

    async def store_fact_pod_config(self, config: Dict[str, Any]) -> None:
        """
        Store or update configuration for a fact pod site in the fact pod config DynamoDB table.

        Args:
            config: Configuration dictionary (must contain 'site' key)

        Raises:
            RepositoryError: If there's an error accessing DynamoDB or config is invalid
        """
        if "site" not in config:
            raise RepositoryError("Fact pod config must contain 'site' key")

        try:
            # Use the dedicated fact pod config table
            table = await self._get_table(self.fact_pod_config_table_name)

            # Add timestamp if not present
            if "updated_at" not in config:
                config["updated_at"] = int(time.time())
            if "created_at" not in config:
                config["created_at"] = config["updated_at"]

            # Store the configuration
            await table.put_item(Item=config)
            logger.debug(f"Stored fact pod config for site {config['site']}")

        except Exception as error:
            logger.error(
                f"Failed to store fact pod config for site {config.get('site', 'unknown')}: {str(error)}"
            )
            raise RepositoryError(
                f"Failed to store fact pod configuration: {str(error)}"
            ) from error

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
            table = await self._get_table()

            # Query for the user-site connection
            response = await table.get_item(
                Key={"pk": f"USER#{user_id}", "sk": f"SITE#{site}"}
            )

            # Return the item if found, otherwise None
            if "Item" in response:
                return response["Item"]
            return None

        except Exception as error:
            logger.error(
                f"Failed to get user-site connection for user {user_id} and site {site}: {str(error)}"
            )
            raise RepositoryError(
                f"Failed to get user-site connection for user {user_id} and site {site}: {str(error)}"
            ) from error

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
            table = await self._get_table()

            # Create item for user-site connection with OAuth config
            current_time = int(time.time())
            item = {
                "pk": f"USER#{user_id}",
                "sk": f"SITE#{site}",
                "user_id": user_id,
                "site": site,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_url": redirect_url,
                "created_at": current_time,
                "updated_at": current_time,
                "item_type": "oauth_config",
            }

            # Store the item in DynamoDB
            await table.put_item(Item=item)
            logger.debug(f"Stored OAuth config for user {user_id} and site {site}")

        except Exception as error:
            logger.error(
                f"Failed to store OAuth configuration for user {user_id} and site {site}: {str(error)}"
            )
            raise RepositoryError(
                f"Failed to store OAuth configuration for user {user_id} and site {site}: {str(error)}"
            ) from error

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
            table = await self._get_table()

            # Calculate expiration time based on TTL setting
            current_time = int(time.time())
            expiration_time = current_time + settings.oauth_state_ttl_seconds

            # Create item for OAuth state with TTL
            item = {
                "pk": f"STATE#{state}",
                "sk": "STATE",
                "state": state,
                "user_id": user_id,
                "site": site,
                "created_at": current_time,
                "expires_at": expiration_time,
                "item_type": "oauth_state",
                "ttl": expiration_time,  # DynamoDB TTL attribute
            }

            # Store the item in DynamoDB
            await table.put_item(Item=item)
            logger.debug(
                f"Stored OAuth state {state} for user {user_id} and site {site} with TTL {expiration_time}"
            )

        except Exception as error:
            logger.error(
                f"Failed to store OAuth state for user {user_id} and site {site}: {str(error)}"
            )
            raise RepositoryError(
                f"Failed to store OAuth state for user {user_id} and site {site}: {str(error)}"
            ) from error

    async def verify_oauth_state(self, state: str) -> Optional[Dict[str, Any]]:
        """
        Verify an OAuth state and return associated data if valid.

        Args:
            state: The state string to verify

        Returns:
            Dictionary with user_id and site if state is valid, otherwise None

        Raises:
            RepositoryError: If there's an error accessing DynamoDB
        """
        try:
            table = await self._get_table()

            # Get the state item from DynamoDB
            response = await table.get_item(Key={"pk": f"STATE#{state}", "sk": "STATE"})

            # Check if state exists and is not expired
            if "Item" in response:
                item = response["Item"]
                current_time = int(time.time())

                if item.get("expires_at", 0) > current_time:
                    # State is valid, return user_id and site
                    return {"user_id": item["user_id"], "site": item["site"]}

                # State is expired, clean it up
                await table.delete_item(Key={"pk": f"STATE#{state}", "sk": "STATE"})
                logger.debug(f"Removed expired OAuth state {state}")

            return None

        except Exception as error:
            logger.error(f"Failed to verify OAuth state {state}: {str(error)}")
            raise RepositoryError(
                f"Failed to verify OAuth state: {str(error)}"
            ) from error
