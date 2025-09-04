"""
Models related to OAuth authentication and client registration.
"""

from typing import List, Optional
from pydantic import BaseModel


class OAuthConfig(BaseModel):
    """OAuth configuration data model for user-site connections."""

    user_id: str
    site: str
    client_id: str
    client_secret: str
    redirect_url: str


class OAuthState(BaseModel):
    """OAuth state data model for maintaining state during authorization flow."""

    state: str
    user_id: str
    site: str


class ClientRegistrationRequest(BaseModel):
    """
    Model representing the request body for registering a client with an OpenProfile fact pod.
    """

    client_name: str
    redirect_uris: List[str]
    grant_types: List[str] = ["authorization_code", "refresh_token"]
    response_types: List[str] = ["code"]
    token_endpoint_auth_method: str = "client_secret_post"
    scope: str = "facts:read facts:make-irrelevant"


class ClientRegistrationResponse(BaseModel):
    """
    Model representing the response from registering a client with an OpenProfile fact pod.
    """

    client_id: str
    client_secret: str
    client_id_issued_at: Optional[int] = None
    client_secret_expires_at: int = 0
    client_name: str
    redirect_uris: List[str]
    grant_types: List[str]
    response_types: List[str]
    token_endpoint_auth_method: str
    scope: str
