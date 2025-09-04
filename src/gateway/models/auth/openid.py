"""
Models related to OpenID Connect configuration.
"""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class OpenIDConfiguration(BaseModel):
    """
    Model representing the OpenID Connect configuration from a fact pod.

    Based on the .well-known/openprofile.json specification.
    """

    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    registration_endpoint: str
    jwks_uri: str
    scopes_supported: List[str] = []
    response_types_supported: List[str] = ["code"]
    grant_types_supported: List[str] = ["authorization_code", "refresh_token"]
    token_endpoint_auth_methods_supported: List[str] = [
        "client_secret_basic",
        "client_secret_post",
    ]
    subject_types_supported: List[str] = ["public"]
    protocol: Optional[List[str]] = None
    model_config = ConfigDict(extra="allow")
