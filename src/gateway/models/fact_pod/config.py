"""
Models related to Fact Pod configuration.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel


class FactPodConfig(BaseModel):
    """
    Model representing a Fact Pod configuration for a site.

    Contains configuration details needed to interact with a Fact Pod.
    """

    site: str
    enabled: bool
    created_at: str
    config_version: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
