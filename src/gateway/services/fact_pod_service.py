"""Service layer for Fact Pod operations."""

import logging
import uuid
from typing import Dict, List, Any

from mcp.client import auth

from gateway.clients.openid_client import HttpOpenIDClient
from gateway.db.repository import Repository
from gateway.models.oauth import ClientRegistrationResponse, OpenIDConfiguration
from gateway.exceptions import (
    FactPodServiceError,
    GatewayError,
    RepositoryError,
    HTTPError
)

logger = logging.getLogger(__name__)


class FactPodOAuthService:
    """Service for handling Fact Pod OAuth operations."""

    def __init__(
            self,
            openid_client: HttpOpenIDClient,
            repository: Repository,
            base_redirect_uri: str = "https://{site}/oauth/callback",
    ) -> None:
        """Initialize with dependencies."""
        self.openid_client = openid_client
        self.repository = repository
        self.base_redirect_uri = base_redirect_uri
        self.mcp_auth = auth

    async def enable_fact_pod(self, site: str, user_id: str) -> Dict[str, Any]:
        """Enable Fact Pod for a user and site.

        Args:
            site: The site domain
            user_id: The user ID

        Returns:
            Dictionary with status, message, and auth URL if successful

        Raises:
            FactPodServiceError: If any step in the process fails
            GatewayError: If Fact Pod is not configured or already enabled
            HTTPError: If OpenID configuration retrieval fails
            HTTPError: If client registration fails
        """
        await self._validate_fact_pod_config(site, user_id)

        try:
            openid_config = await self.openid_client.get_openid_config(site)
            redirect_uris = [self.base_redirect_uri.format(site=site)]

            # Fetch JWKS - required for token validation
            await self.openid_client.http_client.get(openid_config.jwks_uri)

            registration = await self._register_client(openid_config, site, redirect_uris)
            await self._store_oauth_config(user_id, site, registration, openid_config)
            state = str(uuid.uuid4())
            auth_url = await self._generate_auth_url(openid_config, registration, state, redirect_uris[0])

            # Store the OAuth state for CSRF protection
            await self.repository.store_oauth_state(state, user_id, site)

            # Determine the protocol used based on the OpenID config
            protocol_used = "https"
            if openid_config.protocol and "mcp" in openid_config.protocol:
                protocol_used = "mcp"

            return {
                "status": "enabled",
                "message": "Authorization URL generated successfully",
                "auth_url": auth_url,
                "supported_scopes": ["facts:read", "facts:make-irrelevant"],
                "protocol_used": protocol_used,
            }

        except (GatewayError, RepositoryError, HTTPError):
            # Re-raise known errors
            raise
        except Exception as error:
            logger.error("Error enabling Fact Pod: %s",
                         str(error), exc_info=True)
            raise FactPodServiceError(
                f"Failed to enable Fact Pod: {str(error)}") from error

    async def _validate_fact_pod_config(self, site: str, user_id: str) -> None:
        """Validate if Fact Pod can be enabled.

        Args:
            site: Domain of the site
            user_id: ID of the user
        """
        try:
            config = await self.repository.get_fact_pod_config(site)
            if not config:
                raise GatewayError(f"Fact Pod for {site} is not configured")

            connection = await self.repository.get_user_site_connection(user_id, site)
            if connection:
                raise GatewayError(
                    f"Fact Pod for {site} is already enabled for user {user_id}")
        except (GatewayError, RepositoryError, HTTPError):
            # Re-raise known errors
            raise
        except Exception as error:
            logger.error("Error validating Fact Pod config: %s",
                         str(error), exc_info=True)
            raise FactPodServiceError(
                f"Failed to validate Fact Pod config: {str(error)}") from error

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
                client_name=f"Gateway for {site}"
            )
        except Exception as error:
            logger.error("Failed to register client: %s", str(error))
            raise FactPodServiceError(
                f"Failed to register client for {site}: {str(error)}") from error

    async def _store_oauth_config(
            self, user_id: str, site: str, registration: ClientRegistrationResponse,
            openid_config: OpenIDConfiguration
    ) -> None:
        """Store OAuth configuration for user and site.

        Args:
            user_id: ID of the user
            site: Domain of the site
            registration: Client registration response
            openid_config: OpenID configuration
        """
        try:
            await self.repository.store_oauth_config(
                user_id=user_id,
                site=site,
                client_id=registration.client_id,
                client_secret=registration.client_secret,
                token_endpoint=openid_config.token_endpoint
            )
        except Exception as error:
            logger.error("Failed to store OAuth config: %s", str(error))
            raise RepositoryError(
                f"Failed to store OAuth configuration: {str(error)}") from error

    async def _generate_auth_url(
            self, openid_config: OpenIDConfiguration, registration: ClientRegistrationResponse,
            state: str, redirect_uri: str
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
                "state": state
            }

            # Format query string
            query_string = "&".join(
                f"{key}={value}" for key, value in query_params.items())

            # Return complete URL
            return f"{openid_config.authorization_endpoint}?{query_string}"
        except Exception as error:
            logger.error("Failed to generate auth URL: %s", str(error))
            raise FactPodServiceError(
                f"Failed to generate authorization URL: {str(error)}") from error
