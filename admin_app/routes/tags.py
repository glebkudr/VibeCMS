"""
admin_app/routes/tags.py

API endpoints for managing tags.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from admin_app.models import (
    TagCreate,
    TagInDB,
    TagRead,
    TagUpdate,
    ArticleRead,
    # UserInDB # Assuming UserInDB or similar model for authenticated user
)
# Import UserInDB from auth module instead
from admin_app.core.auth import get_current_user #, UserInDB # Corrected function name, UserInDB does not exist here
from admin_app.core.utils import convert_objectid_to_str # Utility to handle ObjectId

logger = logging.getLogger(__name__)
router = APIRouter()

# --- Helper Functions (Database Access) ---

def get_database(request: Request) -> AsyncIOMotorDatabase:
    db = request.app.state.mongo_db
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    return db

# --- API Endpoints --- #

@router.get("/tags", response_model=List[TagRead])
async def list_tags(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: str = Depends(get_current_user), # Expecting str (username)
):
    """List all tags."""
    logger.info(f"User '{current_user}' requested to list all tags.") # Use current_user directly
    tags_cursor = db.get_collection("tags").find()
    tags = await tags_cursor.to_list(length=None)
    # Convert ObjectId before returning
    return [convert_objectid_to_str(tag, TagRead) for tag in tags]

@router.post("/tags", response_model=TagRead, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag: TagCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: str = Depends(get_current_user), # Expecting str (username)
):
    """Create a new non-system tag."""
    logger.info(f"User '{current_user}' requested to create tag with slug '{tag.slug}'.") # Use current_user directly
    tags_collection = db.get_collection("tags")

    # Check if slug already exists
    existing_tag = await tags_collection.find_one({"slug": tag.slug})
    if existing_tag:
        logger.warning(f"Attempt to create tag with existing slug '{tag.slug}'.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tag with slug '{tag.slug}' already exists."
        )

    # Ensure it's created as non-system
    tag_data = tag.model_dump(exclude_unset=True)
    tag_data["is_system"] = False # Explicitly set as non-system

    try:
        result = await tags_collection.insert_one(tag_data)
        created_tag = await tags_collection.find_one({"_id": result.inserted_id})
        if created_tag:
             logger.info(f"Successfully created tag '{tag.slug}'.")
             return convert_objectid_to_str(created_tag, TagRead)
        else:
             # This case should ideally not happen if insert succeeds
             logger.error(f"Failed to retrieve tag '{tag.slug}' immediately after creation.")
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create tag")
    except Exception as e:
        logger.error(f"Error creating tag '{tag.slug}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error creating tag")

@router.get("/tags/{tag_slug}", response_model=TagRead)
async def get_tag(
    tag_slug: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: str = Depends(get_current_user), # Expecting str (username)
):
    """Get a specific tag by slug."""
    logger.info(f"User '{current_user}' requested tag '{tag_slug}'.") # Use current_user directly
    tag = await db.get_collection("tags").find_one({"slug": tag_slug})
    if not tag:
        logger.warning(f"Tag '{tag_slug}' not found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tag '{tag_slug}' not found")
    return convert_objectid_to_str(tag, TagRead)

@router.put("/tags/{tag_slug}", response_model=TagRead)
async def update_tag(
    tag_slug: str,
    tag_update: TagUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: str = Depends(get_current_user), # Expecting str (username)
):
    """Update a non-system tag's name or description."""
    logger.info(f"User '{current_user}' requested to update tag '{tag_slug}'.") # Use current_user directly
    tags_collection = db.get_collection("tags")
    existing_tag = await tags_collection.find_one({"slug": tag_slug})

    if not existing_tag:
        logger.warning(f"Attempt to update non-existent tag '{tag_slug}'.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tag '{tag_slug}' not found")

    if existing_tag.get("is_system", False):
        logger.warning(f"Attempt to update system tag '{tag_slug}'.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"System tag '{tag_slug}' cannot be modified."
        )

    update_data = tag_update.model_dump(exclude_unset=True)
    if not update_data:
        logger.info(f"No update data provided for tag '{tag_slug}'.")
        return convert_objectid_to_str(existing_tag, TagRead) # Return existing if no changes

    try:
        result = await tags_collection.update_one(
            {"slug": tag_slug},
            {"$set": update_data}
        )
        if result.matched_count == 0:
             # Should not happen due to check above, but handle defensively
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tag '{tag_slug}' not found during update")

        updated_tag = await tags_collection.find_one({"slug": tag_slug})
        if updated_tag:
            logger.info(f"Successfully updated tag '{tag_slug}'.")
            return convert_objectid_to_str(updated_tag, TagRead)
        else:
            logger.error(f"Failed to retrieve tag '{tag_slug}' after update.")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve updated tag")
    except Exception as e:
        logger.error(f"Error updating tag '{tag_slug}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error updating tag")


@router.delete("/tags/{tag_slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_slug: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: str = Depends(get_current_user), # Expecting str (username)
):
    """Delete a non-system tag and remove it from all articles."""
    logger.info(f"User '{current_user}' requested to delete tag '{tag_slug}'.") # Use current_user directly
    tags_collection = db.get_collection("tags")
    existing_tag = await tags_collection.find_one({"slug": tag_slug})

    if not existing_tag:
        logger.warning(f"Attempt to delete non-existent tag '{tag_slug}'.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tag '{tag_slug}' not found")

    if existing_tag.get("is_system", False):
        logger.warning(f"Attempt to delete system tag '{tag_slug}'.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"System tag '{tag_slug}' cannot be deleted."
        )

    # Delete the tag itself
    try:
        delete_result = await tags_collection.delete_one({"slug": tag_slug})
        if delete_result.deleted_count == 0:
            # Should not happen based on check above
            logger.error(f"Tag '{tag_slug}' found but failed to delete.")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete tag")
        logger.info(f"Successfully deleted tag document '{tag_slug}'.")
    except Exception as e:
        logger.error(f"Error deleting tag document '{tag_slug}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error deleting tag document")

    # Remove the tag slug from all articles
    articles_collection = db.get_collection("articles")
    try:
        update_result = await articles_collection.update_many(
            {"tags": tag_slug}, # Find articles containing the tag slug
            {"$pull": {"tags": tag_slug}} # Remove the slug from the tags array
        )
        logger.info(f"Removed tag '{tag_slug}' from {update_result.modified_count} articles.")
    except Exception as e:
        # Log the error but don't necessarily fail the request, as the tag doc is deleted.
        # Consider transactionality if atomicity is critical.
        logger.error(f"Error removing tag '{tag_slug}' from articles: {e}", exc_info=True)

    return # Return 204 No Content

@router.get("/tags/{tag_slug}/articles", response_model=List[ArticleRead])
async def get_articles_by_tag(
    tag_slug: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: str = Depends(get_current_user), # Expecting str (username)
):
    """List articles associated with a specific tag."""
    logger.info(f"User '{current_user}' requested articles for tag '{tag_slug}'.") # Use current_user directly
    # First, check if tag exists
    tag_exists = await db.get_collection("tags").find_one({"slug": tag_slug}, {"_id": 1})
    if not tag_exists:
        logger.warning(f"Tag '{tag_slug}' not found when requesting associated articles.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tag '{tag_slug}' not found")

    articles_cursor = db.get_collection("articles").find({"tags": tag_slug})
    articles = await articles_cursor.to_list(length=None) # Adjust length limit if needed
    logger.info(f"Found {len(articles)} articles associated with tag '{tag_slug}'.")
    return [convert_objectid_to_str(article, ArticleRead) for article in articles]


# TODO: Add endpoints or logic for assigning/unassigning tags to articles
# This might be better handled within the article update endpoint or dedicated endpoints
# e.g., POST /articles/{article_id}/tags/{tag_slug} and DELETE /articles/{article_id}/tags/{tag_slug} 