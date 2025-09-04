"""
Data models for OAuth client registration and authentication.
"""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict


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


class JWKKey(BaseModel):
    """
    Model representing a single JSON Web Key in a JWKS set.

    Attributes:
        kty: Key type (e.g. "RSA")
        use: Key use (e.g. "sig" for signature)
        kid: Key ID used in JWT header
        alg: Algorithm (e.g. "RS256")
        n: Base64url-encoded modulus (for RSA keys)
        e: Base64url-encoded exponent (for RSA keys)
    """

    kty: str
    use: str
    kid: str
    alg: str
    n: str  # Base64url-encoded modulus
    e: str  # Base64url-encoded exponent


class JWKS(BaseModel):
    """
    Model representing a JSON Web Key Set (JWKS).

    Attributes:
        keys: List of JSON Web Keys
    """

    keys: List[JWKKey]


class OpenIDConfiguration(BaseModel):
    """
    Model representing the OpenID Connect configuration from a fact pod.

    Based on the .well-known/openprofile.json specification.
    """

    # Required fields
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    registration_endpoint: str
    jwks_uri: str

    # Optional fields with detailed types
    scopes_supported: List[str] = []
    response_types_supported: List[str] = ["code"]
    grant_types_supported: List[str] = ["authorization_code", "refresh_token"]
    token_endpoint_auth_methods_supported: List[str] = [
        "client_secret_basic",
        "client_secret_post",
    ]
    subject_types_supported: List[str] = ["public"]

    # Additional fields
    protocol: Optional[List[str]] = None

    # Use model_config with ConfigDict instead of class-based config
    # Allow additional fields not specified in the model
    model_config = ConfigDict(extra="allow")
