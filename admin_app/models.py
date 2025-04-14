"""
admin_app/models.py

Pydantic models for blog articles.
Purpose: Defines the data structure for CRUD operations with the articles collection in MongoDB.
Architectural Decisions:
- Separate models are used for creating, reading, updating, and internal storage of articles.
- Versioning is implemented through the 'versions' field (a list of dictionaries with change history).
- A string field 'id' is used for the MongoDB ObjectId (ObjectId as a string).
- created_at and updated_at are datetime objects (FastAPI handles serialization).
- status: Uses ArticleStatus enum (draft/published/archived, default is draft).
"""

from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class ArticleStatus(str, Enum):
    """Enum for article statuses."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class ArticleBase(BaseModel):
    """
    Base model for an article.
    Used for inheritance in other models.
    """
    title: str = Field(..., description="Article title")
    slug: str = Field(..., description="URL-friendly identifier (slug) for the article")
    content_md: str = Field(..., description="Markdown content of the article")
    status: ArticleStatus = Field(ArticleStatus.DRAFT, description="Article status: draft/published/archived")

class ArticleCreate(ArticleBase):
    """
    Model for creating a new article.
    All fields are required except status (defaults to draft).
    """
    # Inherits all fields from ArticleBase
    pass

class ArticleUpdate(BaseModel):
    """
    Model for updating an article.
    All fields are optional to support partial updates.
    """
    title: Optional[str] = Field(None, description="Article title")
    slug: Optional[str] = Field(None, description="URL-friendly identifier (slug) for the article")
    content_md: Optional[str] = Field(None, description="Markdown content of the article")
    status: Optional[ArticleStatus] = Field(None, description="Article status: draft/published/archived")

class ArticleRead(ArticleBase):
    """
    Model for reading an article (response to the client).
    Includes system fields like id, created_at, updated_at, versions.
    """
    id: str = Field(..., description="Article ObjectId as a string")
    created_at: datetime = Field(..., description="Creation timestamp (ISO8601 format handled by FastAPI)")
    updated_at: datetime = Field(..., description="Last update timestamp (ISO8601 format handled by FastAPI)")
    # Define the structure of a version entry for clarity
    class ArticleVersion(BaseModel):
        title: str
        slug: str
        content_md: str
        status: ArticleStatus
        updated_at: datetime

    versions: List[ArticleVersion] = Field(default_factory=list, description="History of article changes")

class ArticleInDB(ArticleRead):
    """
    Model representing an article as stored in the database.
    Can potentially include additional internal fields.
    """
    # Currently identical to ArticleRead, but provides a separation point
    # if DB structure diverges from API response in the future.
    pass
