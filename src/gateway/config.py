"""Configuration management for the Gateway service.

This module provides centralized configuration management with environment variable
support using Pydantic Settings.
"""

from typing import Optional, List
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class GatewaySettings(BaseSettings):
    """Gateway service configuration.

    All settings can be overridden by environment variables with the prefix GATEWAY_.
    For example, GATEWAY_DB_TABLE_NAME will override db_table_name.
    """

    # Database settings
    db_table_name: str = "gateway-table"
    db_region_name: str = "us-east-1"
    fact_pod_config_table_name: str = "fact-pod-config-table"

    # OAuth settings
    oauth_redirect_template: str = "https://{site}/oauth/callback"
    oauth_state_ttl_seconds: int = 600  # 10 minutes
    openid_well_known_path: str = Field(
        default=".well-known/openprofile.json",
        description="Path to the OpenID configuration file",
    )

    # Service settings
    log_level: str = Field("INFO", description="Logging level")
    # Store as string in the configuration - no alias needed anymore
    cors_origins_str: str = Field(
        default="*", description="Comma-separated list of allowed CORS origins"
    )

    # FastMCP server settings
    server_host: str = "0.0.0.0"
    server_port: int = 8080

    # Optional OpenTelemetry settings
    telemetry_enabled: bool = False
    telemetry_endpoint: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="GATEWAY_",
        extra="ignore",
    )

    @computed_field
    @property
    def cors_allow_origins(self) -> List[str]:
        """Get the CORS origins as a list."""
        if self.cors_origins_str == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins_str.split(",")]


# Create a singleton instance of the settings
settings = GatewaySettings()
