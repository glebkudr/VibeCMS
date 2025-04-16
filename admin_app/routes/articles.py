"""
admin_app/routes/articles.py

CRUD routes for blog articles (FastAPI + MongoDB).
Purpose: Implements endpoints for creating, retrieving, updating, and deleting articles.
Architectural Decisions:
- Async access to MongoDB via motor.
- Uses Pydantic models from admin_app/models.py.
- Pagination implemented using limit/offset parameters.
- Versioning: On update, the previous state of the article is saved in the 'versions' field.
- All operations will require authentication (to be added later).
"""

import logging
from fastapi import APIRouter, HTTPException, status, Depends, Query, Request
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
# Remove bleach import
# import bleach
# Import Sanitizer and constants
from html_sanitizer import Sanitizer
from admin_app.core.html_sanitizer import ALLOWED_TAGS, ALLOWED_ATTRIBUTES
from admin_app.models import ArticleCreate, ArticleRead, ArticleUpdate, ArticleInDB, ArticleStatus
from admin_app.core.auth import get_current_user

logger = logging.getLogger(__name__)

# Remove prefix and tags here, they will be applied in main.py
router = APIRouter()

# Create a reusable sanitizer instance with dynamically built attributes
dynamic_attributes_api = ALLOWED_ATTRIBUTES.copy()
for tag in ALLOWED_TAGS:
    allowed_for_tag = set(dynamic_attributes_api.get(tag, []))
    allowed_for_tag.update(['class', 'style'])
    dynamic_attributes_api[tag] = list(allowed_for_tag)

sanitizer_config_api = {
    'tags': set(ALLOWED_TAGS),
    'attributes': dynamic_attributes_api,
}
sanitizer_api = Sanitizer(sanitizer_config_api)

def get_db(request: Request):
    """Dependency to get the database client from the request state."""
    db = request.app.state.mongo_db
    if db is None:
        logger.error("Database connection not available")
        raise HTTPException(status_code=503, detail="Database connection not available")
    return db

def to_article_read(doc: dict) -> ArticleRead:
    """Converts a MongoDB document to an ArticleRead Pydantic model."""
    # Ensure required fields are present, provide defaults for optional ones
    # Use 'content_html' instead of 'content_md'
    if not all(k in doc for k in ["_id", "title", "slug", "content_html", "created_at", "updated_at"]):
        logger.error(f"Document missing required fields for ArticleRead conversion: {doc.get('_id', 'N/A')}")
        # Depending on strictness, either raise an error or return a partial/default object
        # For now, let it potentially fail if pydantic validation fails later
        pass

    return ArticleRead(
        id=str(doc["_id"]),
        title=doc["title"],
        slug=doc["slug"],
        content_html=doc["content_html"], # Changed from content_md
        status=ArticleStatus(doc.get("status", ArticleStatus.DRAFT)), # Use Enum
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
        versions=doc.get("versions", []) # Handle missing versions field gracefully
    )

@router.post(
    "/articles", # Relative path to the router prefix
    response_model=ArticleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new article"
)
async def create_article(
    article: ArticleCreate,
    db = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Creates a new article.
    Default status is 'draft'.
    Sanitizes HTML content before saving.
    """
    now = datetime.utcnow()
    article_doc = article.dict()

    # Sanitize HTML content before saving
    try:
        # Use html-sanitizer
        sanitized_html = sanitizer_api.sanitize(article_doc.get('content_html', ''))
        # sanitized_html = bleach.clean(
        #     article_doc.get('content_html', ''),
        #     tags=ALLOWED_TAGS,
        #     attributes=ALLOWED_ATTRIBUTES,
        #     # styles=ALLOWED_STYLES, # Removed
        #     strip=True # Remove disallowed tags instead of escaping
        # )
        article_doc['content_html'] = sanitized_html
    except Exception as e:
        logger.error(f"Error sanitizing HTML content during article creation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process article content")

    article_doc["status"] = ArticleStatus.DRAFT # Set default status
    article_doc["created_at"] = now
    article_doc["updated_at"] = now
    article_doc["versions"] = [] # Initialize versions list

    try:
        result = await db.articles.insert_one(article_doc)
        logger.info(f"Article created with ID: {result.inserted_id}")
        # Fetch the created document to return it
        created_doc = await db.articles.find_one({"_id": result.inserted_id})
        if created_doc:
            return to_article_read(created_doc)
        else:
            # This case should ideally not happen if insert succeeded
            logger.error(f"Failed to fetch created article with ID: {result.inserted_id}")
            raise HTTPException(status_code=500, detail="Failed to retrieve created article")
    except Exception as e:
        logger.error(f"Error creating article: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create article")

@router.get(
    "/articles",
    response_model=dict, # Consider a dedicated ListResponse model
    summary="Get a list of articles with pagination"
)
async def list_articles(
    db = Depends(get_db),
    limit: int = Query(20, ge=1, le=100, description="Number of articles to return"),
    offset: int = Query(0, ge=0, description="Number of articles to skip"),
    user = Depends(get_current_user)
):
    """Retrieves a list of articles with pagination."""
    try:
        cursor = db.articles.find().skip(offset).limit(limit).sort("created_at", -1)
        items = [to_article_read(doc) async for doc in cursor]
        total = await db.articles.count_documents({}) # Consider filtering if needed
        logger.info(f"Listed {len(items)} articles (total: {total}, limit: {limit}, offset: {offset})")
        return {"items": items, "total": total, "limit": limit, "offset": offset}
    except Exception as e:
        logger.error(f"Error listing articles: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list articles")

@router.get(
    "/articles/{article_id}",
    response_model=ArticleRead,
    summary="Get an article by ID"
)
async def get_article(
    article_id: str,
    db = Depends(get_db),
    user = Depends(get_current_user)
):
    """Retrieves a specific article by its ID."""
    try:
        oid = ObjectId(article_id)
    except Exception:
        logger.warning(f"Invalid article ID format received: {article_id}")
        raise HTTPException(status_code=400, detail=f"Invalid article ID format: {article_id}")

    try:
        doc = await db.articles.find_one({"_id": oid})
        if not doc:
            logger.warning(f"Article not found with ID: {article_id}")
            raise HTTPException(status_code=404, detail=f"Article not found: {article_id}")
        logger.info(f"Retrieved article with ID: {article_id}")
        return to_article_read(doc)
    except Exception as e:
        logger.error(f"Error retrieving article {article_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve article")

@router.put(
    "/articles/{article_id}",
    response_model=ArticleRead,
    summary="Update an article by ID"
)
async def update_article(
    article_id: str,
    article_update: ArticleUpdate,
    db = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Updates an article by its ID.
    The previous state is saved in the 'versions' list.
    Sanitizes HTML content if provided.
    """
    try:
        oid = ObjectId(article_id)
    except Exception:
        logger.warning(f"Invalid article ID format received for update: {article_id}")
        raise HTTPException(status_code=400, detail=f"Invalid article ID format: {article_id}")

    try:
        # Find the existing document first to save its state
        existing_doc = await db.articles.find_one({"_id": oid})
        if not existing_doc:
            logger.warning(f"Article not found for update with ID: {article_id}")
            raise HTTPException(status_code=404, detail=f"Article not found: {article_id}")

        # Create the previous version entry (using content_html)
        prev_version = {
            "title": existing_doc["title"],
            "slug": existing_doc["slug"],
            "content_html": existing_doc.get("content_html", ""), # Use content_html
            "status": existing_doc.get("status", ArticleStatus.DRAFT),
            "updated_at": existing_doc["updated_at"]
        }

        # Prepare update data: only include fields that were actually sent
        update_data = article_update.dict(exclude_unset=True)
        if not update_data:
            logger.info(f"No update data provided for article {article_id}. Returning current state.")
            return to_article_read(existing_doc) # Or raise 400 Bad Request?

        # Sanitize HTML content if it's being updated
        if 'content_html' in update_data:
            try:
                # Use html-sanitizer (reuse the same instance)
                sanitized_html = sanitizer_api.sanitize(update_data['content_html'])
                # sanitized_html = bleach.clean(
                #     update_data['content_html'],
                #     tags=ALLOWED_TAGS,
                #     attributes=ALLOWED_ATTRIBUTES,
                #     # styles=ALLOWED_STYLES, # Removed
                #     strip=True
                # )
                update_data['content_html'] = sanitized_html
            except Exception as e:
                logger.error(f"Error sanitizing HTML content during article update {article_id}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Failed to process article content")

        update_data["updated_at"] = datetime.utcnow()

        # Perform the update
        update_operation = {
            "$set": update_data,
            "$push": {"versions": prev_version}
        }
        result = await db.articles.update_one({"_id": oid}, update_operation)

        if result.matched_count == 0:
             # Should not happen if find_one succeeded, but check just in case
            logger.error(f"Update failed: Article {article_id} found but not matched for update.")
            raise HTTPException(status_code=404, detail=f"Article not found during update: {article_id}")

        # Fetch the updated document to return
        updated_doc = await db.articles.find_one({"_id": oid})
        if not updated_doc:
            logger.error(f"Failed to fetch updated article {article_id} after successful update.")
            raise HTTPException(status_code=500, detail="Failed to retrieve updated article")

        logger.info(f"Article updated successfully: {article_id}")
        return to_article_read(updated_doc)

    except HTTPException as http_exc:
        raise http_exc # Re-raise client errors (400, 404)
    except Exception as e:
        logger.error(f"Error updating article {article_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update article")


@router.delete(
    "/articles/{article_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an article by ID"
)
async def delete_article(
    article_id: str,
    db = Depends(get_db),
    user = Depends(get_current_user)
):
    """Deletes an article by its ID."""
    try:
        oid = ObjectId(article_id)
    except Exception:
        logger.warning(f"Invalid article ID format received for delete: {article_id}")
        raise HTTPException(status_code=400, detail=f"Invalid article ID format: {article_id}")

    try:
        result = await db.articles.delete_one({"_id": oid})
        if result.deleted_count == 0:
            logger.warning(f"Article not found for deletion with ID: {article_id}")
            raise HTTPException(status_code=404, detail=f"Article not found: {article_id}")

        logger.info(f"Article deleted successfully: {article_id}")
        # No content to return for 204
        return
    except Exception as e:
        logger.error(f"Error deleting article {article_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete article")
