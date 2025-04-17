import logging
from typing import List, Optional

from admin_app.models import ArticleRead, ArticleStatus  # Assuming models are here
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


async def get_published_articles_by_tag(
    db: AsyncIOMotorDatabase, tag_slug: str, limit: Optional[int] = None
) -> List[ArticleRead]:
    """
    Fetches published articles associated with a specific tag slug.

    Args:
        db: The asynchronous MongoDB database connection.
        tag_slug: The slug of the tag to filter articles by.
        limit: Optional maximum number of articles to return.

    Returns:
        A list of ArticleRead objects matching the criteria, sorted by
        update date descending. Returns an empty list if errors occur.
    """
    try:
        query = {
            "status": ArticleStatus.PUBLISHED.value,
            "tags": tag_slug,
        }
        cursor = db.articles.find(query).sort("updated_at", -1) # -1 for descending

        if limit:
            cursor = cursor.limit(limit)

        articles_data = await cursor.to_list(length=limit or 100) # Fetch limited or up to 100

        # Validate data with Pydantic model
        articles = [ArticleRead(**article_data) for article_data in articles_data]
        logger.info(f"Fetched {len(articles)} published articles for tag '{tag_slug}'.")
        return articles

    except Exception as e:
        logger.error(f"Error fetching articles for tag '{tag_slug}': {e}", exc_info=True)
        return [] # Return empty list on error 