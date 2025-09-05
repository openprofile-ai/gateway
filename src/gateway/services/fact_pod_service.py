"""Service layer for Fact Pod operations."""

import logging
import uuid
import time
from typing import Any, Dict, List

from mcp.client import auth

from gateway.clients.openid_client import HttpOpenIDClient
from gateway.db.repository import Repository
from gateway.models.auth.oauth import ClientRegistrationResponse
from gateway.models.auth.openid import OpenIDConfiguration
from gateway.config import settings
from gateway.exceptions import (
    FactPodServiceError,
    GatewayError,
    RepositoryError,
    HTTPError,
)

logger = logging.getLogger(__name__)


class FactPodOAuthService:
    """Service for handling Fact Pod OAuth operations."""

    def __init__(
        self,
        openid_client: HttpOpenIDClient,
        repository: Repository,
        base_redirect_uri: str | None = None,
    ) -> None:
        """Initialize with dependencies."""
        self.openid_client = openid_client
        self.repository = repository
        self.base_redirect_uri = base_redirect_uri or settings.oauth_redirect_template
        self.mcp_auth = auth

    async def enable_fact_pod(self, user_id: str, site: str) -> Dict[str, Any]:
        """Enable Fact Pod for the user.

        Args:
            user_id: ID of the user
            site: Domain of the site

        Returns:
            Dict with status, message, and auth_url

        Raises:
            FactPodServiceError: If any step in the process fails
            HTTPError: If OpenID configuration retrieval fails
            HTTPError: If client registration fails
        """
        already_enabled = await self._validate_fact_pod_config(site, user_id)

        if already_enabled:
            # User already has this fact pod enabled, return success without proceeding
            return {
                "status": "enabled",
                "message": "Fact Pod was already enabled for this site",
                "auth_url": None,
            }

        try:
            # Check if we already have a configuration for this site
            existing_config = await self.repository.get_fact_pod_config(site)

            # Prepare redirect URIs
            redirect_uris = [self.base_redirect_uri.format(site=site)]
            redirect_uri = redirect_uris[0]

            # Get or fetch OpenID configuration
            if existing_config:
                # Use existing configuration from the database
                logger.info(f"Using existing fact pod configuration for site {site}")
                openid_config = OpenIDConfiguration(**existing_config["openid_config"])
            else:
                # Fetch configuration from the site
                logger.info(f"Fetching new fact pod configuration for site {site}")
                openid_config = await self.openid_client.get_openid_config(site)

                # Store the OpenID configuration in the database for future use
                config_dict = {
                    "site": site,
                    "enabled": True,
                    "openid_config": openid_config.model_dump(),
                    "created_at": int(time.time()),
                    "updated_at": int(time.time()),
                }
                await self.repository.store_fact_pod_config(config_dict)
                logger.info(f"Stored fact pod configuration for site {site}")

            # Register client with the site - done regardless of where the config came from
            registration = await self._register_client(
                openid_config, site, redirect_uris
            )

            # Store OAuth config
            await self.repository.store_oauth_config(
                user_id=user_id,
                site=site,
                client_id=registration.client_id,
                client_secret=registration.client_secret,
                redirect_url=redirect_uri,
            )

            # Generate state and auth URL
            state = str(uuid.uuid4())
            auth_url = await self._generate_auth_url(
                openid_config, registration, state, redirect_uri
            )

            # Store the OAuth state for CSRF protection
            await self.repository.store_oauth_state(state, user_id, site)

            # Return a simplified response format according to the documented interface
            return {
                "status": "enabled",
                "message": "Authorization URL generated successfully",
                "auth_url": auth_url,
            }

        except (GatewayError, RepositoryError, HTTPError):
            # Re-raise known errors
            raise
        except Exception as error:
            logger.error("Error enabling Fact Pod: %s", str(error), exc_info=True)
            raise FactPodServiceError(
                f"Failed to enable Fact Pod: {str(error)}"
            ) from error

    async def _validate_fact_pod_config(self, site: str, user_id: str) -> bool:
        """Validate if Fact Pod can be enabled for the user and site.

        Args:
            site: Domain of the site
            user_id: ID of the user

        Returns:
            Boolean indicating if user already has connection to the site

        Raises:
            RepositoryError: If repository operations fail
        """
        # Check if the user has already enabled this site's Fact Pod
        user_site_connection = await self.repository.get_user_site_connection(
            user_id, site
        )
        if user_site_connection:
            logger.info(f"User {user_id} already has connection to {site}")
            return True

        return False

    async def _register_client(
        self, openid_config: OpenIDConfiguration, site: str, redirect_uris: List[str]
    ) -> ClientRegistrationResponse:
        """Register OAuth client with the site.

        Args:
            openid_config: OpenID configuration
            site: Domain of the site
            redirect_uris: List of redirect URIs

        Returns:
            Client registration response
        """
        try:
            return await self.openid_client.register_client(
                registration_endpoint=openid_config.registration_endpoint,
                redirect_uris=redirect_uris,
                client_name=f"Gateway for {site}",
            )
        except Exception as error:
            logger.error("Failed to register client: %s", str(error))
            raise FactPodServiceError(
                f"Failed to register client for {site}: {str(error)}"
            ) from error

    async def _generate_auth_url(
        self,
        openid_config: OpenIDConfiguration,
        registration: ClientRegistrationResponse,
        state: str,
        redirect_uri: str,
    ) -> str:
        """Generate authorization URL.

        Args:
            openid_config: OpenID configuration
            registration: Client registration response
            state: OAuth state parameter
            redirect_uri: Redirect URI

        Returns:
            Authorization URL
        """
        try:
            # Build query parameters
            query_params = {
                "client_id": registration.client_id,
                "response_type": "code",
                "scope": "facts:read facts:make-irrelevant",
                "redirect_uri": redirect_uri,
                "state": state,
            }

            # Format query string
            query_string = "&".join(
                f"{key}={value}" for key, value in query_params.items()
            )

            # Return complete URL
            return f"{openid_config.authorization_endpoint}?{query_string}"
        except Exception as error:
            logger.error("Failed to generate auth URL: %s", str(error))
            raise FactPodServiceError(
                f"Failed to generate authorization URL: {str(error)}"
            ) from error
