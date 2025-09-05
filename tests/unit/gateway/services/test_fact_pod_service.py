import time
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, call, patch

from gateway.services.fact_pod_service import FactPodOAuthService, OpenIDConfiguration
from gateway.db.repository import Repository
from gateway.clients.openid_client import HttpOpenIDClient
from gateway.models.auth.oauth import ClientRegistrationResponse
from gateway.exceptions import GatewayError


@pytest.fixture
def mock_repository():
    """Create a mock repository for testing."""
    mock = MagicMock(spec=Repository)
    
    # Setup the async mock methods
    mock.get_fact_pod_config = AsyncMock(return_value=None)
    mock.get_user_site_connection = AsyncMock(return_value=None)
    mock.store_fact_pod_config = AsyncMock()
    mock.store_oauth_config = AsyncMock()
    mock.store_oauth_state = AsyncMock()
    
    return mock


@pytest.fixture
def mock_openid_client():
    """Create a mock OpenID client for testing."""
    mock = MagicMock(spec=HttpOpenIDClient)
    
    # Mock the OpenID configuration
    mock_config = MagicMock(spec=OpenIDConfiguration)
    mock_config.authorization_endpoint = "https://example.com/oauth/authorize"
    mock_config.registration_endpoint = "https://example.com/oauth/register"
    mock_config.jwks_uri = "https://example.com/oauth/jwks"
    mock_config.model_dump = MagicMock(return_value={
        "issuer": "https://example.com",
        "authorization_endpoint": "https://example.com/oauth/authorize",
        "token_endpoint": "https://example.com/oauth/token",
        "jwks_uri": "https://example.com/oauth/jwks",
        "registration_endpoint": "https://example.com/oauth/register",
        "scopes_supported": ["facts:read"],
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
    })
    
    mock.get_openid_config = AsyncMock(return_value=mock_config)
    
    # Mock the HTTP client
    mock_http_client = MagicMock()
    mock_http_client.get = AsyncMock()
    mock_http_client.post = AsyncMock(return_value=MagicMock(
        json=MagicMock(return_value={
            "client_id": "test_client_id",
            "client_secret": "test_client_secret"
        })
    ))
    
    mock.http_client = mock_http_client
    
    return mock


@pytest.fixture
def fact_pod_service(mock_repository, mock_openid_client):
    """Create a FactPodOAuthService for testing."""
    service = FactPodOAuthService(
        repository=mock_repository,
        openid_client=mock_openid_client,
        base_redirect_uri="http://gateway.example.com/callback?site={site}"
    )
    return service


class TestFactPodOAuthService:
    """Tests for the FactPodOAuthService."""
    
    @pytest.mark.asyncio
    @patch('uuid.uuid4')
    async def test_enable_fact_pod_with_new_config(self, mock_uuid, fact_pod_service, mock_repository, mock_openid_client):
        """Test enabling a fact pod with a new configuration."""
        # Mock UUID generation
        mock_uuid.return_value = MagicMock(__str__=lambda _: "test-uuid")
        
        # Set up the mocks
        mock_repository.get_fact_pod_config.return_value = None
        
        # Mock the register client method
        fact_pod_service._register_client = AsyncMock(return_value=ClientRegistrationResponse(
            client_id="test_client_id",
            client_secret="test_client_secret",
            client_name="Gateway for example.com",
            redirect_uris=["http://gateway.example.com/callback?site=example.com"],
            grant_types=["authorization_code", "refresh_token"],
            response_types=["code"],
            token_endpoint_auth_method="client_secret_post",
            scope="facts:read facts:make-irrelevant"
        ))
        fact_pod_service._generate_auth_url = AsyncMock(return_value="https://example.com/auth?client_id=test")
        fact_pod_service._store_oauth_config = AsyncMock()
        
        # Enable the fact pod
        result = await fact_pod_service.enable_fact_pod("user123", "example.com")
        
        # Verify the result
        assert result["status"] == "enabled"
        assert result["auth_url"] == "https://example.com/auth?client_id=test"
        
        # Verify the OpenID configuration was fetched
        mock_openid_client.get_openid_config.assert_called_once_with("example.com")
        
        # Verify the configuration was stored in the database
        mock_repository.store_fact_pod_config.assert_called_once()
        config_arg = mock_repository.store_fact_pod_config.call_args.args[0]
        assert config_arg["site"] == "example.com"
        assert config_arg["enabled"] is True
        assert "openid_config" in config_arg
        assert "created_at" in config_arg
        assert "updated_at" in config_arg
        
        # Verify client registration was called
        fact_pod_service._register_client.assert_called_once()
        
        # Verify OAuth state was stored
        mock_repository.store_oauth_state.assert_called_once_with(
            "test-uuid", "user123", "example.com"
        )
        
    @pytest.mark.asyncio
    @patch('uuid.uuid4')
    async def test_enable_fact_pod_with_existing_config(self, mock_uuid, fact_pod_service, mock_repository, mock_openid_client):
        """Test enabling a fact pod with an existing configuration."""
        # Mock UUID generation
        mock_uuid.return_value = MagicMock(__str__=lambda _: "test-uuid")
        
        # Set up existing configuration in the mock repository
        existing_config = {
            "site": "example.com",
            "enabled": True,
            "openid_config": {
                "issuer": "https://example.com",
                "authorization_endpoint": "https://example.com/oauth/authorize",
                "token_endpoint": "https://example.com/oauth/token",
                "jwks_uri": "https://example.com/oauth/jwks",
                "registration_endpoint": "https://example.com/oauth/register",
                "scopes_supported": ["facts:read"],
                "response_types_supported": ["code"],
                "grant_types_supported": ["authorization_code"],
            }
        }
        mock_repository.get_fact_pod_config.return_value = existing_config
        
        # Mock the methods
        fact_pod_service._register_client = AsyncMock(return_value=ClientRegistrationResponse(
            client_id="test_client_id",
            client_secret="test_client_secret",
            client_name="Gateway for example.com",
            redirect_uris=["http://gateway.example.com/callback?site=example.com"],
            grant_types=["authorization_code", "refresh_token"],
            response_types=["code"],
            token_endpoint_auth_method="client_secret_post",
            scope="facts:read facts:make-irrelevant"
        ))
        fact_pod_service._generate_auth_url = AsyncMock(return_value="https://example.com/auth?client_id=test")
        fact_pod_service._store_oauth_config = AsyncMock()
        
        # Enable the fact pod
        result = await fact_pod_service.enable_fact_pod("user123", "example.com")
        
        # Verify the result
        assert result["status"] == "enabled"
        assert result["auth_url"] == "https://example.com/auth?client_id=test"
        
        # Verify the OpenID configuration was NOT fetched (reused from DB)
        mock_openid_client.get_openid_config.assert_not_called()
        
        # Verify the configuration was NOT stored in the database again
        mock_repository.store_fact_pod_config.assert_not_called()
        
        # Verify client registration was still called
        fact_pod_service._register_client.assert_called_once()
        
        # Verify OAuth state was stored
        mock_repository.store_oauth_state.assert_called_once_with(
            "test-uuid", "user123", "example.com"
        )
        
    @pytest.mark.asyncio
    async def test_enable_fact_pod_already_enabled(self, fact_pod_service, mock_repository):
        """Test enabling a fact pod that is already enabled for the user."""
        # Set up the mock to show that user already has connection to the site
        mock_repository.get_user_site_connection.return_value = {
            "user_id": "user123", 
            "site": "example.com"
        }
        
        # Enable the fact pod (should return already enabled message)
        result = await fact_pod_service.enable_fact_pod("user123", "example.com")
        
        # Verify the result
        assert result["status"] == "enabled"
        assert result["message"] == "Fact Pod was already enabled for this site"
        assert result["auth_url"] is None
        
        # Verify that no further processing was done
        mock_repository.get_fact_pod_config.assert_not_called()
        
    @pytest.mark.asyncio
    async def test_enable_fact_pod_no_jwks_call(self, fact_pod_service, mock_repository, mock_openid_client):
        """Test that JWKS URI is not fetched when enabling a fact pod with a new configuration."""
        # Set up the mocks
        mock_repository.get_fact_pod_config.return_value = None
        
        # Mock the methods
        fact_pod_service._register_client = AsyncMock(return_value=ClientRegistrationResponse(
            client_id="test_client_id",
            client_secret="test_client_secret",
            client_name="Gateway for example.com",
            redirect_uris=["http://gateway.example.com/callback?site=example.com"],
            grant_types=["authorization_code", "refresh_token"],
            response_types=["code"],
            token_endpoint_auth_method="client_secret_post",
            scope="facts:read facts:make-irrelevant"
        ))
        fact_pod_service._generate_auth_url = AsyncMock(return_value="https://example.com/auth?client_id=test")
        fact_pod_service._store_oauth_config = AsyncMock()
        
        # Enable the fact pod
        await fact_pod_service.enable_fact_pod("user123", "example.com")
        
        # Verify JWKS was NOT fetched
        mock_openid_client.http_client.get.assert_not_called()
        
    @pytest.mark.asyncio
    async def test_validate_fact_pod_config_already_enabled(self, fact_pod_service, mock_repository):
        """Test validation returns True if fact pod is already enabled for the user."""
        # Set up the mock to return an existing connection
        mock_repository.get_user_site_connection.return_value = {
            "user_id": "user123",
            "site": "example.com"
        }
        
        # Validate
        result = await fact_pod_service._validate_fact_pod_config("example.com", "user123")
        
        # Should return True for already enabled
        assert result is True
        
    @pytest.mark.asyncio
    async def test_validate_fact_pod_config_not_enabled(self, fact_pod_service, mock_repository):
        """Test validation returns False when fact pod is not already enabled."""
        # Set up the mock to return no existing connection
        mock_repository.get_user_site_connection.return_value = None
        
        # Validate
        result = await fact_pod_service._validate_fact_pod_config("example.com", "user123")
        
        # Should return False since it's not already enabled
        assert result is False
        
        # Verify the repository was called with the correct arguments
        mock_repository.get_user_site_connection.assert_called_once_with("user123", "example.com")

    @pytest.mark.asyncio
    async def test_enable_fact_pod_with_existing_config(self, fact_pod_service, mock_repository, mock_openid_client):
        """Test enabling a fact pod with an existing configuration."""
        # Set up the mocks
        mock_repository.get_fact_pod_config.return_value = {
            "site": "example.com",
            "enabled": True,
            "openid_config": {
                "issuer": "https://example.com",
                "authorization_endpoint": "https://example.com/oauth/authorize",
                "token_endpoint": "https://example.com/oauth/token",
                "registration_endpoint": "https://example.com/oauth/register",
                "jwks_uri": "https://example.com/oauth/jwks",
            }
        }
        
        # Mock the methods
        fact_pod_service._register_client = AsyncMock(return_value=ClientRegistrationResponse(
            client_id="test_client_id",
            client_secret="test_client_secret",
            client_name="Gateway for example.com",
            redirect_uris=["http://gateway.example.com/callback?site=example.com"],
            grant_types=["authorization_code", "refresh_token"],
            response_types=["code"],
            token_endpoint_auth_method="client_secret_post",
            scope="facts:read facts:make-irrelevant"
        ))
        fact_pod_service._generate_auth_url = AsyncMock(return_value="https://example.com/auth?client_id=test")

        # Enable the fact pod
        result = await fact_pod_service.enable_fact_pod("user123", "example.com")
        
        # Verify the result
        assert result["status"] == "enabled"
        assert "auth_url" in result
        
        # Verify the repository calls
        mock_repository.store_oauth_config.assert_called_once()
        mock_repository.store_oauth_state.assert_called_once()
        mock_repository.store_fact_pod_config.assert_not_called()  # Should not be called for existing config
        
    @pytest.mark.asyncio
    async def test_enable_fact_pod_already_enabled(self, fact_pod_service, mock_repository):
        """Test enabling a fact pod that is already enabled for the user."""
        # Set up the mock to return a connection
        mock_repository.get_user_site_connection.return_value = {
            "user_id": "user123",
            "site": "example.com",
            "enabled": True,
        }
        
        # Enable the fact pod
        result = await fact_pod_service.enable_fact_pod("user123", "example.com")
        
        # Verify the result indicates already enabled
        assert result["status"] == "enabled"
        assert "already enabled" in result["message"].lower()
        assert result["auth_url"] is None
        
        # Verify no repository calls were made
        mock_repository.store_oauth_config.assert_not_called()
        mock_repository.store_oauth_state.assert_not_called()
        mock_repository.store_fact_pod_config.assert_not_called()

    @pytest.mark.asyncio
    async def test_enable_fact_pod_no_jwks_call(self, fact_pod_service, mock_repository, mock_openid_client):
        """Test that JWKS URI is not fetched when enabling a fact pod with a new configuration."""
        # Set up the mocks
        mock_repository.get_fact_pod_config.return_value = None
        
        # Mock the methods
        fact_pod_service._register_client = AsyncMock(return_value=ClientRegistrationResponse(
            client_id="test_client_id",
            client_secret="test_client_secret",
            client_name="Gateway for example.com",
            redirect_uris=["http://gateway.example.com/callback?site=example.com"],
            grant_types=["authorization_code", "refresh_token"],
            response_types=["code"],
            token_endpoint_auth_method="client_secret_post",
            scope="facts:read facts:make-irrelevant"
        ))
        fact_pod_service._generate_auth_url = AsyncMock(return_value="https://example.com/auth?client_id=test")
        fact_pod_service._store_oauth_config = AsyncMock()
        
        # Enable the fact pod
        await fact_pod_service.enable_fact_pod("user123", "example.com")
        
        # Verify JWKS URI was not called
        for call_args in mock_openid_client.http_client.get.call_args_list:
            url = call_args[0][0]
            assert "jwks" not in url.lower()
