"""Tests for the configuration management system."""

import os
import tempfile
from pathlib import Path
from unittest import mock
import pytest
import json
from pydantic import ValidationError

from gateway.config import GatewaySettings


def test_default_settings():
    """Test that default settings are loaded correctly."""
    settings = GatewaySettings()
    assert settings.db_table_name == "categories"
    assert settings.db_region_name == "us-east-1"
    assert settings.oauth_redirect_template == "https://{site}/oauth/callback"
    assert settings.log_level == "INFO"
    assert settings.server_port == 8080


def test_env_variable_override():
    """Test that environment variables properly override default settings."""
    with mock.patch.dict(os.environ, {
        "GATEWAY_DB_TABLE_NAME": "custom_table",
        "GATEWAY_SERVER_PORT": "9000",
        "GATEWAY_LOG_LEVEL": "DEBUG"
    }):
        settings = GatewaySettings()
        assert settings.db_table_name == "custom_table"
        assert settings.server_port == 9000
        assert settings.log_level == "DEBUG"
        # This one was not overridden, so should still be default
        assert settings.db_region_name == "us-east-1"


def test_cors_allow_origins_list():
    """Test that CORS origins can be provided as a comma-separated list."""
    with mock.patch.dict(os.environ, {
        "GATEWAY_CORS_ORIGINS_STR": "http://localhost:3000,https://app.example.com"
    }):
        settings = GatewaySettings()
        assert len(settings.cors_allow_origins) == 2
        assert "http://localhost:3000" in settings.cors_allow_origins
        assert "https://app.example.com" in settings.cors_allow_origins


def test_telemetry_settings():
    """Test that telemetry settings work correctly."""
    # Default is disabled
    settings = GatewaySettings()
    assert settings.telemetry_enabled is False
    assert settings.telemetry_endpoint is None
    
    # Enable with endpoint
    with mock.patch.dict(os.environ, {
        "GATEWAY_TELEMETRY_ENABLED": "true",
        "GATEWAY_TELEMETRY_ENDPOINT": "http://localhost:4317"
    }):
        settings = GatewaySettings()
        assert settings.telemetry_enabled is True
        assert settings.telemetry_endpoint == "http://localhost:4317"


def test_env_file_loading():
    """Test loading configuration from .env file."""
    # Create a temporary directory for our test
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a temporary .env file
        env_file_path = Path(temp_dir) / ".env"
        with open(env_file_path, "w") as env_file:
            env_file.write("GATEWAY_DB_TABLE_NAME=env_file_table\n")
            env_file.write("GATEWAY_LOG_LEVEL=DEBUG\n")
            env_file.write("GATEWAY_SERVER_PORT=9090\n")
        
        # Patch the settings to use our temporary directory
        with mock.patch("gateway.config.GatewaySettings.model_config", {
                "env_file": str(env_file_path),
                "env_file_encoding": "utf-8",
                "env_prefix": "GATEWAY_",
                "extra": "ignore"
            }):
            # Load settings which should read from our temp .env file
            settings = GatewaySettings()
            
            # Verify settings were loaded from .env file
            assert settings.db_table_name == "env_file_table"
            assert settings.log_level == "DEBUG"
            assert settings.server_port == 9090
            # Values not in .env file should still have defaults
            assert settings.db_region_name == "us-east-1"
