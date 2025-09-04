"""Models related to Fact Pod functionality."""
from pydantic import BaseModel, HttpUrl


class OAuthConfig(BaseModel):
    """OAuth configuration data model."""

    user_id: str
    site: str
    client_id: str
    client_secret: str
    redirect_url: str


class OAuthState(BaseModel):
    """OAuth state data model."""

    state: str
    user_id: str
    site: str
