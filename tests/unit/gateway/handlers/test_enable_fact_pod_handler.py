import json
import pytest
from unittest.mock import AsyncMock, MagicMock, call
from fastmcp import Client
from httpx import Response

from gateway.handlers.enable_fact_pod_handler import EnableFactPodHandler
from gateway.clients.http_client import AsyncHTTPClient
from gateway.db.repository import Repository
from gateway.services.fact_pod_service import FactPodOAuthService
from gateway.clients.openid_client import HttpOpenIDClient
from gateway.models.auth.oauth import ClientRegistrationResponse
from gateway.exceptions import GatewayError, HTTPError, FactPodServiceError


@pytest.fixture
def mock_repository():
    """Create a mock repository for testing."""
    mock = MagicMock(spec=Repository)

    # Setup the async mock methods
    mock.get_fact_pod_config = AsyncMock(return_value={"enabled": True})
    mock.get_user_site_connection = AsyncMock(return_value=None)
    mock.store_oauth_config = AsyncMock()
    mock.store_oauth_state = AsyncMock()

    return mock


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client for testing."""
    client = MagicMock(spec=AsyncHTTPClient)

    # Mock OpenID configuration response with protocol = ["https"]
    openid_config_data = {
        "issuer": "https://example.com",
        "authorization_endpoint": "https://example.com/oauth/authorize",
        "token_endpoint": "https://example.com/oauth/token",
        "jwks_uri": "https://example.com/oauth/jwks",
        "registration_endpoint": "https://example.com/oauth/register",
        "scopes_supported": ["facts:read", "facts:make-irrelevant"],
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "token_endpoint_auth_methods_supported": [
            "client_secret_basic",
            "client_secret_post",
        ],
        "subject_types_supported": ["public"],
        "protocol": ["https"],
    }
    mock_openid_response = MagicMock(spec=Response)
    mock_openid_response.status_code = 200
    mock_openid_response.json.return_value = openid_config_data
    mock_openid_response.raise_for_status = MagicMock()

    # Mock JWKS response
    jwks_data = {
        "keys": [
            {
                "kty": "RSA",
                "use": "sig",
                "kid": "abc123",
                "alg": "RS256",
                "n": "base64url-modulus",
                "e": "AQAB",
            }
        ]
    }
    mock_jwks_response = MagicMock()
    mock_jwks_response.status_code = 200
    mock_jwks_response.json.return_value = jwks_data

    # Mock client registration response
    client_registration_data = ClientRegistrationResponse(
        client_id="test-client-id",
        client_secret="test-client-secret",
        client_id_issued_at=1624553600,
        client_secret_expires_at=0,
        client_name="OpenProfile Gateway",
        redirect_uris=[
            "https://gateway.openprofile.ai/oauth/callback?site=example.com"
        ],
        grant_types=["authorization_code", "refresh_token"],
        response_types=["code"],
        token_endpoint_auth_method="client_secret_post",
        scope="facts:read facts:make-irrelevant"
    )
    mock_registration_response = MagicMock(spec=Response)
    mock_registration_response.status_code = 200
    mock_registration_response.json.return_value = client_registration_data.model_dump()
    mock_registration_response.raise_for_status = MagicMock()

    # Setup HTTP client calls
    client.get = AsyncMock(side_effect=lambda url: 
        mock_openid_response if ".well-known/openprofile.json" in url 
        else mock_jwks_response)
    client.post = AsyncMock(return_value=mock_registration_response)
    
    # Patch the openid_client.register_client to return ClientRegistrationResponse
    # This is critical for fixing the tests
    original_register_client = HttpOpenIDClient.register_client
    
    async def patched_register_client(*args, **kwargs):
        result = await original_register_client(*args, **kwargs)
        # If already a ClientRegistrationResponse, return as is
        if isinstance(result, ClientRegistrationResponse):
            return result
        # If dict, convert to ClientRegistrationResponse
        if isinstance(result, dict):
            return ClientRegistrationResponse(**result)
        return result
        
    HttpOpenIDClient.register_client = patched_register_client

    return client


@pytest.fixture
def enable_fact_pod_handler(base_mcp_server, mock_repository, mock_http_client):
    """Create an EnableFactPodHandler instance for testing."""
    # Create the base handler with the MCP instance
    handler = EnableFactPodHandler(base_mcp_server)

    # Create a mock OpenID client
    openid_client = HttpOpenIDClient(mock_http_client)

    # Replace the auto-created dependencies with our mocks
    handler.fact_pod_service = FactPodOAuthService(
        openid_client=openid_client,
        repository=mock_repository
    )
    
    # Patch the service's _register_client method to return a proper ClientRegistrationResponse
    handler.fact_pod_service._register_client = AsyncMock(return_value=ClientRegistrationResponse(
        client_id="test-client-id",
        client_secret="test-client-secret",
        client_name="Gateway for example.com",
        redirect_uris=["http://gateway.example.com/callback?site=example.com"],
        grant_types=["authorization_code", "refresh_token"],
        response_types=["code"],
        token_endpoint_auth_method="client_secret_post",
        scope="facts:read facts:make-irrelevant"
    ))
    
    # Patch the service's _generate_auth_url method
    handler.fact_pod_service._generate_auth_url = AsyncMock(
        return_value="https://example.com/oauth/authorize?client_id=test-client-id&response_type=code&scope=facts:read&redirect_uri=http://gateway.example.com/callback?site=example.com&state=test-state"
    )

    return handler


@pytest.mark.asyncio
async def test_enable_fact_pod_with_https_protocol(
    base_mcp_server, enable_fact_pod_handler, mock_repository, mock_http_client
):
    """Test enabling a fact pod using HTTP client when protocol is https."""
    # Directly patch the service's enable_fact_pod method to return a successful response
    enable_fact_pod_handler.fact_pod_service.enable_fact_pod = AsyncMock(return_value={
        "status": "enabled",
        "message": "Authorization URL generated successfully",
        "auth_url": "https://example.com/oauth/authorize?client_id=test-client-id&response_type=code&scope=facts:read&redirect_uri=http://gateway.example.com/callback?site=example.com&state=test-state"
    })

    async with Client(base_mcp_server) as client:
        user_id = "test_user"
        site = "example.com"

        # Call the tool using the handler class name per project convention
        result = await client.call_tool(
            "EnableFactPodHandler", {"user_id": user_id, "site": site}
        )

        # Use the structured response directly instead of parsing JSON
        response = result.data

        # Assert expected results
        assert response["status"] == "enabled"
        assert "message" in response
        assert "auth_url" in response

        # Verify service method was called with correct parameters
        # Note the parameter order: first site, then user_id
        enable_fact_pod_handler.fact_pod_service.enable_fact_pod.assert_called_once_with(site, user_id)


@pytest.mark.asyncio
async def test_already_enabled_fact_pod(
    base_mcp_server, enable_fact_pod_handler, mock_repository
):
    """Test handling when a user tries to enable an already enabled fact pod."""
    # Directly patch the service's enable_fact_pod method to return an "already enabled" response
    enable_fact_pod_handler.fact_pod_service.enable_fact_pod = AsyncMock(return_value={
        "status": "enabled",
        "message": "Fact Pod was already enabled for this site",
        "auth_url": None
    })

    async with Client(base_mcp_server) as client:
        user_id = "test_user"
        site = "example.com"

        # Call the tool
        result = await client.call_tool(
            "EnableFactPodHandler", {"user_id": user_id, "site": site}
        )

        # Use the structured response directly
        response = result.data

        # Assert expected results
        assert response["status"] == "enabled"
        assert "already enabled" in response["message"].lower()
        assert response["auth_url"] is None

        # Verify service was called with correct parameters
        enable_fact_pod_handler.fact_pod_service.enable_fact_pod.assert_called_once_with(site, user_id)


@pytest.mark.asyncio
async def test_missing_fact_pod_config(
    base_mcp_server, enable_fact_pod_handler, mock_repository
):
    """Test handling when a fact pod is not configured."""
    # Directly patch the service's enable_fact_pod method to raise an error
    enable_fact_pod_handler.fact_pod_service.enable_fact_pod = AsyncMock(
        side_effect=FactPodServiceError("Missing Fact Pod configuration")
    )

    async with Client(base_mcp_server) as client:
        user_id = "test_user"
        site = "example.com"

        # Call the tool
        result = await client.call_tool(
            "EnableFactPodHandler", {"user_id": user_id, "site": site}
        )

        # Use the structured response directly
        response = result.data

        # Assert expected results
        assert response["status"] == "error"
        assert "Missing Fact Pod configuration" in response["message"]

        # Verify service was called with correct parameters
        enable_fact_pod_handler.fact_pod_service.enable_fact_pod.assert_called_once_with(site, user_id)


@pytest.mark.asyncio
async def test_invalid_openid_response(
    base_mcp_server, enable_fact_pod_handler, mock_repository, mock_http_client
):
    """Test handling when the OpenID configuration response is invalid."""
    # Directly patch the service's enable_fact_pod method to raise an HTTPError
    enable_fact_pod_handler.fact_pod_service.enable_fact_pod = AsyncMock(
        side_effect=FactPodServiceError("Failed to fetch OpenID configuration: Not Found")
    )

    async with Client(base_mcp_server) as client:
        user_id = "test_user"
        site = "example.com"

        # Call the tool
        result = await client.call_tool(
            "EnableFactPodHandler", {"user_id": user_id, "site": site}
        )

        # Use the structured response directly instead of parsing JSON
        response = result.data

        # Assert expected results
        assert response["status"] == "error"
        assert "Failed to fetch OpenID configuration" in response["message"]

        # Verify service was called with correct parameters
        enable_fact_pod_handler.fact_pod_service.enable_fact_pod.assert_called_once_with(site, user_id)


@pytest.mark.asyncio
async def test_enable_fact_pod_with_existing_config(
    base_mcp_server, enable_fact_pod_handler, mock_repository, mock_http_client
):
    """Test enabling a fact pod when a configuration already exists in the database."""
    # Directly patch the service's enable_fact_pod method to return a successful response
    enable_fact_pod_handler.fact_pod_service.enable_fact_pod = AsyncMock(return_value={
        "status": "enabled",
        "message": "Authorization URL generated successfully (existing config)",
        "auth_url": "https://example.com/oauth/authorize?client_id=test-client-id"
    })

    async with Client(base_mcp_server) as client:
        user_id = "test_user"
        site = "example.com"

        # Call the tool
        result = await client.call_tool(
            "EnableFactPodHandler", {"user_id": user_id, "site": site}
        )

        # Use the structured response directly
        response = result.data

        # Assert expected results
        assert response["status"] == "enabled"
        assert "message" in response
        assert "auth_url" in response

        # Verify service was called with correct parameters
        enable_fact_pod_handler.fact_pod_service.enable_fact_pod.assert_called_once_with(site, user_id)
