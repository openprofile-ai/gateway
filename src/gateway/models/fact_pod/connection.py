"""
Models related to user-site connections for Fact Pods.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class UserSiteConnection(BaseModel):
    """
    Model representing a connection between a user and a site's Fact Pod.

    Contains information about the established connection and its status.
    """

    user_id: str
    site: str
    connected_at: datetime
    last_accessed: Optional[datetime] = None
    status: str  # 'active', 'disabled', 'revoked', etc.
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    settings: Optional[Dict[str, Any]] = None
