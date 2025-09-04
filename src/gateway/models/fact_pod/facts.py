"""
Models related to facts and categories from Fact Pods.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class Category(BaseModel):
    """
    Model representing a fact category.

    Contains information about a category that facts can belong to.
    """

    name: str
    description: Optional[str] = None
    count: Optional[int] = None


class Fact(BaseModel):
    """
    Model representing a fact from a Fact Pod.

    Contains the actual fact content and associated metadata.
    """

    fact_id: str
    content: str
    category: str
    created_at: datetime
    source_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    is_relevant: bool = True
