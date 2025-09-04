"""
Models related to JSON Web Keys (JWK) and JSON Web Key Sets (JWKS).
"""

from typing import List
from pydantic import BaseModel


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
    n: str
    e: str


class JWKS(BaseModel):
    """
    Model representing a JSON Web Key Set (JWKS).

    Attributes:
        keys: List of JSON Web Keys
    """

    keys: List[JWKKey]
