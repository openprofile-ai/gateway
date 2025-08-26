import json
import pytest
from unittest.mock import AsyncMock, MagicMock, call
from fastmcp import Client

from gateway.handlers.enable_fact_pod_handler import EnableFactPodHandler
from gateway.http.client import HTTPClientInterface
from gateway.client.interface import MCPClientInterface


@pytest.fixture
def mock_repository():
    """Create a mock repository for testing."""
    mock = MagicMock()

    # Setup the async mock methods
    mock.get_fact_pod_config = AsyncMock(return_value={"enabled": True})
    mock.get_user_site_connection = AsyncMock(return_value=None)
    mock.store_oauth_config = AsyncMock()
    mock.store_oauth_state = AsyncMock()

    return mock


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client for testing."""
    client = MagicMock(spec=HTTPClientInterface)

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
        "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post"],
        "subject_types_supported": ["public"],
        "protocol": ["https"]
    }
    mock_openid_response = MagicMock()
    mock_openid_response.status_code = 200
    mock_openid_response.json.return_value = openid_config_data

    # Mock JWKS response
    jwks_data = {
        "keys": [
            {
                "kty": "RSA",
                "use": "sig",
                "kid": "abc123",
                "alg": "RS256",
                "n": "base64url-modulus",
                "e": "AQAB"
            }
        ]
    }
    mock_jwks_response = MagicMock()
    mock_jwks_response.status_code = 200
    mock_jwks_response.json.return_value = jwks_data

    # Mock client registration response
    client_registration_data = {
        "client_id": "test-client-id",
        "client_secret": "test-client-secret",
        "client_id_issued_at": 1624553600,
        "client_secret_expires_at": 0,
        "client_name": "OpenProfile Gateway",
        "redirect_uris": ["https://gateway.openprofile.ai/oauth/callback?site=example.com"],
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "client_secret_post",
        "scope": "facts:read facts:make-irrelevant"
    }
    mock_registration_response = MagicMock()
    mock_registration_response.status_code = 201
    mock_registration_response.json.return_value = client_registration_data

    # Configure mock client methods to return different responses based on URL
    def get_side_effect(*args, **kwargs):
        url = args[0]
        if "/.well-known/openprofile.json" in url:
            return mock_openid_response
        elif "/oauth/jwks" in url:
            return mock_jwks_response
        # Default fallback
        mock_default = MagicMock()
        mock_default.status_code = 404
        return mock_default

    client.get = AsyncMock(side_effect=get_side_effect)
    client.post = AsyncMock(return_value=mock_registration_response)
    client.close = AsyncMock()

    return client


@pytest.fixture
def mock_mcp_client():
    """Create a mock MCP client for testing."""
    client = MagicMock(spec=MCPClientInterface)

    # Mock responses for different calls
    # JWKS response
    jwks_data = {
        "keys": [
            {
                "kty": "RSA",
                "use": "sig",
                "kid": "mcp123",
                "alg": "RS256",
                "n": "base64url-modulus-mcp",
                "e": "AQAB"
            }
        ]
    }
    mock_jwks_response = MagicMock()
    mock_jwks_response.text = json.dumps(jwks_data)

    # Registration response
    registration_data = {
        "client_id": "mcp-client-id",
        "client_secret": "mcp-client-secret",
        "client_id_issued_at": 1624553600,
        "client_secret_expires_at": 0,
        "client_name": "OpenProfile Gateway",
        "redirect_uris": ["https://gateway.openprofile.ai/oauth/callback?site=example.com"],
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "client_secret_post",
        "scope": "facts:read facts:make-irrelevant"
    }
    mock_registration_response = MagicMock()
    mock_registration_response.text = json.dumps(registration_data)

    # Configure side effect for call_tool method
    async def call_tool_side_effect(server_name, params):
        if "path" in params:
            if params["path"] == "/openprofile/oauth/jwks":
                return [mock_jwks_response]
            elif params["path"] == "/openprofile/oauth/register":
                return [mock_registration_response]

        # Default response
        default_response = MagicMock()
        default_response.text = '{}'
        return [default_response]

    client.call_tool = AsyncMock(side_effect=call_tool_side_effect)
    client.close = AsyncMock()

    return client


@pytest.fixture
def enable_fact_pod_handler(base_mcp_server, mock_repository, mock_http_client, mock_mcp_client):
    """Create an EnableFactPodHandler instance for testing."""
    handler = EnableFactPodHandler(
        base_mcp_server,
        http_client=mock_http_client,
        mcp_client=mock_mcp_client
    )
    # Replace the repository with our mock
    handler.repository = mock_repository
    return handler


@pytest.mark.asyncio
async def test_enable_fact_pod_with_https_protocol(base_mcp_server, enable_fact_pod_handler, mock_repository, mock_http_client):
    """Test enabling a fact pod using HTTP client when protocol is https."""
    async with Client(base_mcp_server) as client:
        user_id = "test_user"
        site = "example.com"

        # Call the tool using the handler class name per project convention
        result = await client.call_tool("EnableFactPodHandler", {
            "user_id": user_id,
            "site": site
        })

        # Parse the TextContent response
        response = json.loads(result[0].text)

        # Assert expected results
        assert response["status"] == "enabled"
        assert "auth_url" in response
        assert "https://example.com/oauth/authorize" in response["auth_url"]
        assert "client_id=test-client-id" in response["auth_url"]
        assert "facts:read" in response["auth_url"]
        assert "supported_scopes" in response
        assert "facts:read" in response["supported_scopes"]
        assert response["protocol_used"] == "https"

        # Verify repository method calls
        mock_repository.get_fact_pod_config.assert_called_once_with(site)
        mock_repository.get_user_site_connection.assert_called_once_with(
            user_id, site)
        mock_repository.store_oauth_config.assert_called_once()
        mock_repository.store_oauth_state.assert_called_once()

        # Verify HTTP client calls - now we expect two GET calls
        expected_calls = [
            call(f"https://{site}/.well-known/openprofile.json"),
            call(f"https://{site}/oauth/jwks")
        ]
        mock_http_client.get.assert_has_calls(expected_calls, any_order=False)

        # Verify the POST request includes the correct data
        mock_http_client.post.assert_called_once()
        call_kwargs = mock_http_client.post.call_args.kwargs
        assert "redirect_uris" in call_kwargs["json"]
        assert site in call_kwargs["json"]["redirect_uris"][0]
        assert call_kwargs["json"]["token_endpoint_auth_method"] == "client_secret_post"
        assert "facts:read" in call_kwargs["json"]["scope"]


@pytest.mark.asyncio
async def test_enable_fact_pod_with_mcp_protocol(base_mcp_server, enable_fact_pod_handler, mock_repository, mock_http_client, mock_mcp_client):
    """Test enabling a fact pod using MCP client when protocol includes mcp."""
    # Update the OpenID config to include mcp protocol
    openid_config_with_mcp = {
        "issuer": "https://example.com",
        "authorization_endpoint": "https://example.com/oauth/authorize",
        "token_endpoint": "https://example.com/oauth/token",
        "jwks_uri": "https://example.com/oauth/jwks",
        "registration_endpoint": "https://example.com/oauth/register",
        "scopes_supported": ["facts:read", "facts:make-irrelevant"],
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post"],
        "subject_types_supported": ["public"],
        "protocol": ["mcp", "https"]
    }

    # Update the mock to return the MCP-enabled config
    mock_http_client.get.side_effect = None  # Reset the side effect
    mock_openid_response = MagicMock()
    mock_openid_response.status_code = 200
    mock_openid_response.json.return_value = openid_config_with_mcp
    mock_http_client.get.return_value = mock_openid_response

    async with Client(base_mcp_server) as client:
        user_id = "test_user"
        site = "example.com"

        # Call the tool using the handler class name per project convention
        result = await client.call_tool("EnableFactPodHandler", {
            "user_id": user_id,
            "site": site
        })

        # Parse the TextContent response
        response = json.loads(result[0].text)

        # Assert expected results
        assert response["status"] == "enabled"
        assert "auth_url" in response
        assert response["protocol_used"] == "mcp"

        # Verify repository method calls
        mock_repository.get_fact_pod_config.assert_called_with(site)
        mock_repository.get_user_site_connection.assert_called_with(
            user_id, site)
        mock_repository.store_oauth_config.assert_called()
        mock_repository.store_oauth_state.assert_called()

        # Verify MCP client was called
        mock_mcp_client.call_tool.assert_called()

        # Reset the mock for other tests
        mock_http_client.get.reset_mock()


@pytest.mark.asyncio
async def test_already_enabled_fact_pod(base_mcp_server, enable_fact_pod_handler, mock_repository):
    """Test handling when a user tries to enable an already enabled fact pod."""
    # Change the mock to return an existing user-site connection
    mock_repository.get_user_site_connection.return_value = {"enabled": True}

    async with Client(base_mcp_server) as client:
        user_id = "test_user"
        site = "example.com"

        # Call the tool
        result = await client.call_tool("EnableFactPodHandler", {
            "user_id": user_id,
            "site": site
        })

        # Parse the TextContent response
        response = json.loads(result[0].text)

        # Assert expected results
        assert response["status"] == "already_enabled"
        assert response["auth_url"] is None

        # Verify that only the connection check was called
        mock_repository.get_fact_pod_config.assert_called_once_with(site)
        mock_repository.get_user_site_connection.assert_called_once_with(
            user_id, site)
        mock_repository.store_oauth_config.assert_not_called()


@pytest.mark.asyncio
async def test_missing_fact_pod_config(base_mcp_server, enable_fact_pod_handler, mock_repository):
    """Test handling when a fact pod is not configured."""
    # Change the mock to return None for fact pod config
    mock_repository.get_fact_pod_config.return_value = None

    async with Client(base_mcp_server) as client:
        user_id = "test_user"
        site = "example.com"

        # Call the tool
        result = await client.call_tool("EnableFactPodHandler", {
            "user_id": user_id,
            "site": site
        })

        # Parse the TextContent response
        response = json.loads(result[0].text)

        # Assert expected results
        assert response["status"] == "error"
        assert "not configured" in response["message"]

        # Verify that only the config check was called
        mock_repository.get_fact_pod_config.assert_called_once_with(site)
        mock_repository.get_user_site_connection.assert_not_called()


@pytest.mark.asyncio
async def test_invalid_openid_response(base_mcp_server, enable_fact_pod_handler, mock_repository, mock_http_client):
    """Test handling when the OpenID configuration response is invalid."""
    # Change the mock response to be invalid
    invalid_response = MagicMock()
    invalid_response.status_code = 404

    # Override the side_effect to always return the invalid response
    mock_http_client.get.side_effect = None
    mock_http_client.get.return_value = invalid_response

    async with Client(base_mcp_server) as client:
        user_id = "test_user"
        site = "example.com"

        # Call the tool
        result = await client.call_tool("EnableFactPodHandler", {
            "user_id": user_id,
            "site": site
        })

        # Parse the TextContent response
        response = json.loads(result[0].text)

        # Assert expected results
        assert response["status"] == "error"
        assert "Failed to fetch OpenID configuration" in response["message"]

        # Verify repository and HTTP client calls
        mock_repository.get_fact_pod_config.assert_called_once_with(site)
        mock_repository.get_user_site_connection.assert_called_once_with(
            user_id, site)
        mock_http_client.get.assert_called_once()
