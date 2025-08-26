import json
import uuid
from typing import Any, Dict, Optional, List, Union

import httpx
from fastmcp.server import FastMCP
from fastmcp import Client as FastMCPClient

from gateway.handlers.base_handler import BaseHandler
from gateway.http.client import HTTPClientInterface, AsyncHTTPClient
from gateway.client.interface import MCPClientInterface, AsyncMCPClient
from gateway.models.oauth import (
    ClientRegistrationRequest,
    ClientRegistrationResponse,
    OpenIDConfiguration,
    JWKS
)


class EnableFactPodHandler(BaseHandler):
    """
    Handles the process of enabling a Fact Pod for a specific user and site.

    Ensures proper configuration, performs OpenID Connect Discovery, dynamically registers 
    the Gateway as an OAuth client, and checks if the Fact Pod is already enabled.
    """

    def __init__(self, mcp_instance: FastMCP,
                 http_client: Optional[HTTPClientInterface] = None,
                 mcp_client: Optional[MCPClientInterface] = None) -> None:
        """
        Initialize the handler with the MCP instance.

        Args:
            mcp_instance: The FastMCP instance to use for registration
            http_client: Optional HTTP client for making requests
            mcp_client: Optional MCP client for making requests
        """
        super().__init__(mcp_instance)
        self._http_client = http_client
        self._mcp_client = mcp_client

    @property
    def http_client(self) -> HTTPClientInterface:
        """
        Get the HTTP client for making requests.

        Returns:
            An HTTPClientInterface instance
        """
        if self._http_client is None:
            self._http_client = AsyncHTTPClient()
        return self._http_client

    @property
    def mcp_client(self) -> MCPClientInterface:
        """
        Get the MCP client for making requests.

        Returns:
            An MCPClientInterface instance
        """
        if self._mcp_client is None:
            self._mcp_client = AsyncMCPClient(self.mcp)
        return self._mcp_client

    async def tool_method(self, user_id: str, site: str) -> Dict[str, Any]:
        """
        Enable a Fact Pod for a specific user and site.

        Args:
            user_id: The ID of the LLM user
            site: The domain of the site

        Returns:
            Dict containing status and auth URL if successful
        """
        # 1. Check if Fact Pod is already configured
        pod_config = await self.repository.get_fact_pod_config(site)
        if not pod_config:
            return {
                "status": "error",
                "message": f"Fact Pod for {site} is not configured"
            }

        # 2. Check if Fact Pod is already enabled for this user
        user_connection = await self.repository.get_user_site_connection(user_id, site)
        if user_connection:
            return {
                "status": "already_enabled",
                "message": f"Fact Pod for {site} is already enabled for user {user_id}",
                "auth_url": None
            }

        # 3. Perform OpenID Connect Discovery
        try:
            openid_config = await self._fetch_openid_configuration(site)
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to fetch OpenID configuration: {str(e)}"
            }

        # Determine which client to use based on the protocol
        use_mcp_client = False
        if hasattr(openid_config, "protocol") and openid_config.protocol:
            use_mcp_client = "mcp" in openid_config.protocol

        # 4. Fetch JWKS if needed
        try:
            jwks = await self._fetch_jwks(openid_config.jwks_uri, use_mcp=use_mcp_client)
        except Exception as e:
            # Non-blocking error, we can continue without JWKS
            jwks = None

        # 5. Perform dynamic client registration
        try:
            client_config = await self._register_client(
                openid_config.registration_endpoint,
                site,
                use_mcp=use_mcp_client
            )
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to register client: {str(e)}"
            }

        # 6. Store OAuth configuration
        try:
            await self.repository.store_oauth_config(
                user_id=user_id,
                site=site,
                client_id=client_config.client_id,
                client_secret=client_config.client_secret,
                redirect_url=client_config.redirect_uris[0]
            )
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to store OAuth configuration: {str(e)}"
            }

        # 7. Generate Auth URL
        state = str(uuid.uuid4())
        auth_url = (
            f"{openid_config.authorization_endpoint}"
            f"?client_id={client_config.client_id}"
            f"&redirect_uri={client_config.redirect_uris[0]}"
            f"&scope={client_config.scope}"
            f"&response_type=code"
            f"&state={state}"
        )

        # 8. Store state for later verification
        await self.repository.store_oauth_state(state, user_id, site)

        # Include information about which client was used
        return {
            "status": "enabled",
            "message": f"Fact Pod for {site} has been enabled for user {user_id}",
            "auth_url": auth_url,
            "supported_scopes": openid_config.scopes_supported,
            "protocol_used": "mcp" if use_mcp_client else "https"
        }

    async def _fetch_openid_configuration(self, site: str) -> OpenIDConfiguration:
        """
        Fetch OpenID Connect configuration from the Fact Pod.

        Args:
            site: The domain of the site

        Returns:
            OpenIDConfiguration object containing the configuration

        Raises:
            Exception: If there's an error fetching or parsing the configuration
        """
        url = f"https://{site}/.well-known/openprofile.json"
        response = await self.http_client.get(url)

        if response.status_code != 200:
            raise Exception(
                f"Failed to fetch OpenID configuration: {response.status_code}")

        try:
            config_data = response.json()
            return OpenIDConfiguration(**config_data)
        except Exception as e:
            raise Exception(f"Invalid OpenID configuration format: {str(e)}")

    async def _fetch_jwks(self, jwks_uri: str, use_mcp: bool = False) -> Optional[JWKS]:
        """
        Fetch the JSON Web Key Set (JWKS) from the specified URI.

        Args:
            jwks_uri: URI pointing to the JWKS endpoint
            use_mcp: Whether to use MCP client instead of HTTP client

        Returns:
            JWKS object containing the keys or None if fetch fails

        Raises:
            Exception: If there's an error fetching or parsing the JWKS
        """
        try:
            if use_mcp:
                # Extract the server name and tool name from the URI
                # Example: https://example.com/openprofile/oauth/jwks
                # Server would be "example.com", tool would be the path component
                server_name = jwks_uri.split("//")[1].split("/")[0]
                path = "/" + "/".join(jwks_uri.split("//")[1].split("/")[1:])

                # Use MCP client to make the request
                result = await self.mcp_client.call_tool(server_name, {"path": path})
                jwks_data = json.loads(result[0].text)
            else:
                # Use HTTP client as before
                response = await self.http_client.get(jwks_uri)

                if response.status_code != 200:
                    return None

                jwks_data = response.json()

            return JWKS(**jwks_data)
        except Exception as e:
            # Log the error but don't fail the operation
            print(f"Failed to fetch JWKS: {str(e)}")
            return None

    async def _register_client(self, registration_endpoint: str, site: str, use_mcp: bool = False) -> ClientRegistrationResponse:
        """
        Register the Gateway as an OAuth client with the Fact Pod.

        Args:
            registration_endpoint: The registration endpoint from OpenID configuration
            site: The domain of the site
            use_mcp: Whether to use MCP client instead of HTTP client

        Returns:
            ClientRegistrationResponse object containing registration details

        Raises:
            Exception: If there's an error during registration or parsing the response
        """
        # Generate a unique redirect URI for this site
        redirect_uri = f"https://gateway.openprofile.ai/oauth/callback?site={site}"

        # Create the request body using the data model
        registration_request = ClientRegistrationRequest(
            client_name="OpenProfile Gateway",
            redirect_uris=[redirect_uri],
            grant_types=["authorization_code", "refresh_token"],
            response_types=["code"],
            token_endpoint_auth_method="client_secret_post",
            scope="facts:read facts:make-irrelevant"
        )

        try:
            if use_mcp:
                # Extract the server name from the URI
                server_name = registration_endpoint.split(
                    "//")[1].split("/")[0]

                # Use MCP client to make the request
                result = await self.mcp_client.call_tool(
                    server_name,
                    {
                        "path": "/openprofile/oauth/register",
                        "method": "POST",
                        "body": registration_request.dict()
                    }
                )
                response_data = json.loads(result[0].text)
            else:
                # Use HTTP client as before
                headers = {"Content-Type": "application/json"}
                response = await self.http_client.post(
                    url=registration_endpoint,
                    json=registration_request.dict(),
                    headers=headers
                )

                if response.status_code != 201 and response.status_code != 200:
                    raise Exception(
                        f"Failed to register client: {response.status_code}")

                response_data = response.json()

            return ClientRegistrationResponse(**response_data)
        except Exception as e:
            raise Exception(f"Client registration failed: {str(e)}")

    async def close(self) -> None:
        """Close any open resources."""
        if self._http_client is not None:
            await self._http_client.close()

        if self._mcp_client is not None:
            await self._mcp_client.close()
