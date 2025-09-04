"""OpenID client implementation."""
import logging
from typing import List
from urllib.parse import urljoin

from gateway.clients.http_client import AsyncHTTPClient
from gateway.models.oauth import OpenIDConfiguration, ClientRegistrationResponse, ClientRegistrationRequest
from gateway.exceptions import GatewayError, HTTPError, FactPodServiceError

logger = logging.getLogger(__name__)


class HttpOpenIDClient:
    """HTTP implementation of OpenID client."""

    def __init__(self, http_client: AsyncHTTPClient) -> None:
        """
        Initialize with HTTP client.

        Args:
            http_client: HTTP client implementation
        """
        self.http_client = http_client

    async def get_openid_config(self, site: str) -> OpenIDConfiguration:
        """
        Fetch OpenID configuration from well-known endpoint.

        Args:
            site: The site domain

        Returns:
            OpenID configuration

        Raises:
            GatewayError: If configuration retrieval fails
            ValueError: If configuration is missing required fields
        """
        base_url = f"https://{site}" if "://" not in site else site
        config_url = urljoin(base_url, ".well-known/openprofile.json")

        try:
            response = await self.http_client.get(config_url)
            response.raise_for_status()
            config_data = response.json()

            required_fields = {
                "issuer", "authorization_endpoint", "token_endpoint",
                "registration_endpoint", "jwks_uri"
            }

            if missing:
                = required_fields - set(config_data):
                raise GatewayError(
                    f"Missing required fields in OpenID config: {missing}")

            return OpenIDConfiguration(**config_data)

        except HTTPError as error:
            logger.error(
                "HTTP error during OpenID configuration fetch: %s", str(error))
            raise FactPodServiceError(
                f"Failed to fetch OpenID configuration: {str(error)}") from error
        except Exception as error:
            logger.error(
                "Failed to fetch OpenID configuration: %s", str(error))
            raise GatewayError(
                f"Failed to fetch OpenID configuration: {str(error)}") from error

    async def register_client(
            self,
            registration_endpoint: str,
            redirect_uris: List[str],
            client_name: str
    ) -> ClientRegistrationResponse:
        """
        Register client with OpenID provider.

        Args:
            registration_endpoint: The registration endpoint URL
            redirect_uris: List of redirect URIs
            client_name: Name of the client

        Returns:
            Client registration response

        Raises:
            GatewayError: If registration fails
        """
        registration_request = ClientRegistrationRequest(
            client_name=client_name,
            redirect_uris=redirect_uris,
            grant_types=["authorization_code", "refresh_token"],
            response_types=["code"],
            token_endpoint_auth_method="client_secret_post",
            scope="facts:read facts:make-irrelevant",
        )

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            response = await self.http_client.post(
                url=registration_endpoint,
                json=registration_request.dict(),
                headers=headers
            )
            response.raise_for_status()
            return ClientRegistrationResponse(**response.json())
        except HTTPError as error:
            logger.error(
                "HTTP error during client registration: %s", str(error))
            raise FactPodServiceError from error
        except Exception as error:
            logger.error("Failed to register client: %s", str(error))
            raise GatewayError(
                f"Failed to register client: {str(error)}") from error
