"""
admin_app/core/system_tags.py

Logic for synchronizing system tags from the configuration file to the database.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
import os

from admin_app.models import TagInDB, TagCreate # Assuming models are in admin_app.models

logger = logging.getLogger(__name__)

# Determine paths relative to this file
# Moved path calculation outside the function for clarity, but it's static
try:
    CURRENT_FILE_PATH = os.path.abspath(__file__)
    logger.debug(f"Current file path (__file__): {CURRENT_FILE_PATH}") # Log current file path

    BASE_DIR = os.path.dirname(CURRENT_FILE_PATH) # admin_app/core
    logger.debug(f"Calculated BASE_DIR: {BASE_DIR}") # Log base dir

    # Go up two levels to project root, then shared
    SHARED_DIR = os.path.abspath(os.path.join(BASE_DIR, '../../shared'))
    logger.debug(f"Calculated SHARED_DIR: {SHARED_DIR}") # Log shared dir

    SYSTEM_TAGS_CONFIG_PATH = os.path.join(SHARED_DIR, 'system_tags.json')
    logger.debug(f"Calculated SYSTEM_TAGS_CONFIG_PATH: {SYSTEM_TAGS_CONFIG_PATH}") # Log final path
except Exception as e:
    logger.exception(f"Critical error calculating initial paths: {e}")
    # Set to a default/invalid path to prevent NameError later if needed
    SYSTEM_TAGS_CONFIG_PATH = "/invalid/path/due/to/error/system_tags.json"
    SHARED_DIR = "/invalid/path/due/to/error/shared"

async def sync_system_tags(db: AsyncIOMotorDatabase):
    """
    Synchronizes system tags from the configuration file with the database.

    - Reads system tags defined in `shared/system_tags.json`.
    - Reads all tags currently in the database.
    - Performs a one-way sync (config -> DB):
        - Adds system tags from the config if they don't exist in the DB.
        - Marks tags in the DB as system (`is_system=True`) if they are in the config.
        - Unmarks tags in the DB (`is_system=False`) if they are marked as system but no longer in the config.
    - Logs the synchronization results.
    """
    config_path_str = SYSTEM_TAGS_CONFIG_PATH
    config_path = Path(config_path_str) # Convert to Path object for exists check

    # --- Commented Out Debug Logging ---
    # logger.info(f"--- Debugging Paths ---")
    # logger.info(f"Running sync_system_tags.")
    # logger.info(f"Checking for config file at calculated path: {config_path_str}")
    # logger.info(f"Does the calculated SHARED_DIR exist? ({SHARED_DIR}): {os.path.exists(SHARED_DIR)}")
    # if os.path.exists(SHARED_DIR):
    #     try:
    #         shared_dir_contents = os.listdir(SHARED_DIR)
    #         logger.info(f"Contents of SHARED_DIR ({SHARED_DIR}): {shared_dir_contents}")
    #     except Exception as e:
    #         logger.error(f"Could not list contents of SHARED_DIR ({SHARED_DIR}): {e}")
    # else:
    #     logger.warning(f"SHARED_DIR does not exist: {SHARED_DIR}")
    # logger.info(f"Does the calculated config file path exist? ({config_path_str}): {config_path.exists()}")
    # logger.info(f"--- End Debugging Paths ---")
    # --- End Commented Out Debug Logging ---

    logger.info(f"Attempting to load system tags from: {config_path_str}") # Keep this one

    if not config_path.exists():
        logger.error(f"System tags configuration file not found: {config_path_str}")
        return

    try:
        with open(config_path_str, "r", encoding="utf-8") as f:
            system_tags_config: List[Dict[str, Any]] = json.load(f)
            # Validate basic structure (list of dicts with at least 'slug')
            if not isinstance(system_tags_config, list) or not all(isinstance(t, dict) and "slug" in t for t in system_tags_config):
                raise ValueError("Invalid format in system_tags.json")
        logger.info(f"Loaded {len(system_tags_config)} system tags from {config_path_str}")
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Error reading or parsing system tags configuration {config_path_str}: {e}")
        return

    tags_collection = db.get_collection("tags")
    existing_tags_cursor = tags_collection.find()
    existing_tags_list = await existing_tags_cursor.to_list(length=None) # Fetch all tags
    existing_tags_map: Dict[str, Dict[str, Any]] = {tag["slug"]: tag for tag in existing_tags_list}

    logger.info(f"Found {len(existing_tags_map)} tags in the database.")

    config_slugs = {tag_data["slug"] for tag_data in system_tags_config}
    db_slugs = set(existing_tags_map.keys())

    # --- Synchronization Logic --- #
    added_count = 0
    updated_to_system_count = 0
    updated_to_nonsystem_count = 0

    # 1. Add/Update system tags from config
    for tag_data in system_tags_config:
        slug = tag_data["slug"]
        tag_defaults = {
            "name": tag_data.get("name", slug), # Use slug as fallback name
            "description": tag_data.get("description"),
            "required_fields": tag_data.get("required_fields", []),
            "is_system": True
        }

        if slug not in existing_tags_map:
            # Tag doesn't exist, create it as system
            try:
                new_tag = TagCreate(**tag_defaults, slug=slug) # Use TagCreate model
                await tags_collection.insert_one(new_tag.model_dump(by_alias=True))
                logger.info(f"Added system tag '{slug}' to the database.")
                added_count += 1
            except Exception as e:
                logger.error(f"Failed to add system tag '{slug}': {e}")
        else:
            # Tag exists, ensure it's marked as system and update fields if necessary
            existing_tag = existing_tags_map[slug]
            update_needed = False
            update_payload = {}

            if not existing_tag.get("is_system", False):
                update_payload["is_system"] = True
                update_needed = True

            # Optionally, update name/description/required_fields from config
            # Decide if config should overwrite existing non-system tag data
            # For now, let's only update if it wasn't system before
            if update_needed:
                # If we just marked it as system, update other fields too
                update_payload["name"] = tag_defaults["name"]
                update_payload["description"] = tag_defaults["description"]
                update_payload["required_fields"] = tag_defaults["required_fields"]
                try:
                    result = await tags_collection.update_one(
                        {"slug": slug},
                        {"$set": update_payload}
                    )
                    if result.modified_count > 0:
                        logger.info(f"Updated tag '{slug}' to system and synced fields.")
                        updated_to_system_count += 1
                except Exception as e:
                    logger.error(f"Failed to update tag '{slug}' to system: {e}")
            # else: tag exists and is already system, do nothing for now
            #       or add logic here to force-update fields from config if desired

    # 2. Unmark system tags that are no longer in the config
    tags_to_unmark = []
    for slug, tag in existing_tags_map.items():
        if tag.get("is_system", False) and slug not in config_slugs:
            tags_to_unmark.append(slug)

    if tags_to_unmark:
        try:
            result = await tags_collection.update_many(
                {"slug": {"$in": tags_to_unmark}},
                {"$set": {"is_system": False}}
            )
            if result.modified_count > 0:
                logger.info(f"Unmarked {result.modified_count} tags as system: {tags_to_unmark}")
                updated_to_nonsystem_count = result.modified_count
        except Exception as e:
            logger.error(f"Failed to unmark system tags: {e}")

    logger.info(
        f"System tags synchronization complete. Added: {added_count}, "
        f"Marked as system: {updated_to_system_count}, "
        f"Unmarked as system: {updated_to_nonsystem_count}."
    ) 