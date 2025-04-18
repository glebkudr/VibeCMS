import logging
from typing import List, Dict, Any, Optional

from admin_app.models import TagRead, ArticleRead # Assuming models are here
from motor.motor_asyncio import AsyncIOMotorDatabase

from generator.utils import get_published_articles_by_tag

logger = logging.getLogger(__name__)

# Define the slugs for the menu tags explicitly
MENU_TAG_SLUGS = ["menu1", "menu2", "menu3"]


async def fetch_menu_data(db: AsyncIOMotorDatabase, limit_articles: Optional[int] = 5) -> List[Dict[str, Any]]:
    """
    Fetches data required for rendering the dynamic menu.

    Queries the database for tags defined in MENU_TAG_SLUGS and then
    fetches a limited number of published articles for each tag.

    Args:
        db: The asynchronous MongoDB database connection.
        limit_articles: Max number of articles to fetch per menu tag.

    Returns:
        A list of dictionaries, where each dictionary represents a menu item
        containing the tag's name, slug, and a list of associated articles.
        Returns an empty list if errors occur or no menu tags are found.
        Example structure:
        [
            {
                'name': 'Menu Section 1',
                'slug': 'menu1',
                'articles': [ArticleRead(...), ...]
            },
            ...
        ]
    """
    menu_items: List[Dict[str, Any]] = []
    try:
        # Fetch the tag documents corresponding to the menu slugs
        tags_cursor = db.tags.find({"slug": {"$in": MENU_TAG_SLUGS}, "is_system": True})
        menu_tags_data = await tags_cursor.to_list(length=len(MENU_TAG_SLUGS))

        if not menu_tags_data:
            logger.warning(f"Did not find any system tags matching slugs: {MENU_TAG_SLUGS}")
            return []

        # Create TagRead objects for easier access
        menu_tags = {tag_data['slug']: TagRead(**tag_data) for tag_data in menu_tags_data}
        logger.debug(f"Constructed TagRead objects for slugs: {list(menu_tags.keys())}")

        # Fetch articles for each menu tag slug in the defined order
        for tag_slug in MENU_TAG_SLUGS:
            tag = menu_tags.get(tag_slug)
            if tag:
                logger.info(f"Fetching articles for menu tag: {tag.slug} ('{tag.name}')")
                articles = await get_published_articles_by_tag(
                    db,
                    tag.slug,
                    limit=limit_articles
                )
                menu_items.append({
                    "name": tag.name,
                    "slug": tag.slug,
                    "articles": articles
                })
            else:
                logger.warning(f"System tag with slug '{tag_slug}' defined in MENU_TAG_SLUGS not found in the database or not marked as system.")

        logger.info(f"Successfully prepared data for {len(menu_items)} menu items.")
        logger.debug(f"Returning menu_items structure: {menu_items}")
        return menu_items

    except Exception as e:
        logger.error(f"Error fetching menu data: {e}", exc_info=True)
        return [] # Return empty list on error 