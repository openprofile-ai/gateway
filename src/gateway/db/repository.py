# db/repository.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class Repository(ABC):
    @abstractmethod
    async def get_categories(self) -> list[str]:
        """
        Fetch all categories.

        Returns:
            List of category names
        """
        pass

    @abstractmethod
    async def get_fact_pod_config(self, site: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a fact pod site.

        Args:
            site: Domain of the site

        Returns:
            Configuration dictionary or None if not found
        """
        pass

    @abstractmethod
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
        """
        pass

    @abstractmethod
    async def store_oauth_config(
        self,
        user_id: str,
        site: str,
        client_id: str,
        client_secret: str,
        redirect_url: str,
    ) -> None:
        """
        Store OAuth configuration for a user-site connection.

        Args:
            user_id: ID of the user
            site: Domain of the site
            client_id: OAuth client ID
            client_secret: OAuth client secret
            redirect_url: OAuth redirect URL
        """
        pass

    @abstractmethod
    async def store_oauth_state(self, state: str, user_id: str, site: str) -> None:
        """
        Store OAuth state for CSRF protection.

        Args:
            state: Random state string
            user_id: ID of the user
            site: Domain of the site
        """
        pass
