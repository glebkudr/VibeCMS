"""
admin_app/models.py

Pydantic models for blog articles and tags.
Purpose: Defines the data structure for CRUD operations with the articles and tags collections in MongoDB.
Architectural Decisions:
- Separate models are used for creating, reading, updating, and internal storage.
- Versioning is implemented through the 'versions' field in Article.
- A string field 'id' is used for the MongoDB ObjectId (ObjectId as a string).
- created_at and updated_at are datetime objects (FastAPI handles serialization).
- status: Uses ArticleStatus enum (draft/published/archived, default is draft).
- tags: Articles have a list of tag slugs. Tags have a list of required fields and a system flag.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

# --- Article Models --- #

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
    # Make content_html optional to handle older articles potentially missing this field
    content_html: Optional[str] = Field(None, description="HTML content of the article from Tiptap editor")
    status: ArticleStatus = Field(ArticleStatus.DRAFT, description="Article status: draft/published/archived")
    tags: List[str] = Field(default_factory=list, description="List of tag slugs associated with the article")
    cover_image: Optional[str] = Field(None, description="URL of the cover image")
    headline: Optional[str] = Field(None, description="Short headline or summary")

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
    content_html: Optional[str] = Field(None, description="HTML content of the article from Tiptap editor")
    status: Optional[ArticleStatus] = Field(None, description="Article status: draft/published/archived")
    tags: Optional[List[str]] = Field(None, description="List of tag slugs associated with the article")
    cover_image: Optional[str] = Field(None, description="URL of the cover image")
    headline: Optional[str] = Field(None, description="Short headline or summary")

class ArticleRead(ArticleBase):
    """
    Model for reading an article (response to the client).
    Includes system fields like id, created_at, updated_at, versions.
    """
    id: str = Field(..., alias='_id', description="Article ObjectId as a string")
    created_at: datetime = Field(..., description="Creation timestamp (ISO8601 format handled by FastAPI)")
    updated_at: datetime = Field(..., description="Last update timestamp (ISO8601 format handled by FastAPI)")
    # Define the structure of a version entry for clarity
    class ArticleVersion(BaseModel):
        title: str
        slug: str
        content_html: str
        status: ArticleStatus
        updated_at: datetime
        tags: Optional[List[str]] = None # Make tags optional in version history
        cover_image: Optional[str] = None # Explicitly default to None
        headline: Optional[str] = None # Explicitly default to None

    versions: List[ArticleVersion] = Field(default_factory=list, description="History of article changes")

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }

class ArticleInDB(ArticleRead):
    """
    Model representing an article as stored in the database.
    Can potentially include additional internal fields.
    """
    # Currently identical to ArticleRead, but provides a separation point
    # if DB structure diverges from API response in the future.
    pass

# --- Tag Models --- #

class TagBase(BaseModel):
    """Base model for a tag."""
    slug: str = Field(..., description="Unique, URL-friendly identifier for the tag")
    name: str = Field(..., description="Human-readable name of the tag")
    description: Optional[str] = Field(None, description="Optional description of the tag")
    required_fields: List[str] = Field(default_factory=list, description="List of fields required by articles with this tag")

class TagCreate(TagBase):
    """Model for creating a new tag (only non-system tags)."""
    # Inherits all fields from TagBase
    pass

class TagUpdate(BaseModel):
    """Model for updating a tag (only non-system tags)."""
    name: Optional[str] = Field(None, description="Human-readable name of the tag")
    description: Optional[str] = Field(None, description="Optional description of the tag")
    # Slug and required_fields cannot be updated for system tags,
    # and should not be updated for non-system tags via this model
    # (slug update is complex, required_fields are system-defined or rarely changed)

class TagRead(TagBase):
    """Model for reading a tag (response to the client)."""
    id: str = Field(..., alias='_id', description="Tag ObjectId as a string")
    is_system: bool = Field(False, description="Indicates if the tag is managed by the system config")

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }

class TagInDB(TagRead):
    """Model representing a tag as stored in the database."""
    # Currently identical to TagRead, but provides a separation point
    pass
