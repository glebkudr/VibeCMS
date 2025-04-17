# Article Tag System Design

This document describes the design for the article tagging system, used for flexible placement of articles on the website (e.g., homepage headliner, suggested articles, menu categories).

## Problem Statement

To enable flexible placement of articles on the main page and other sections, we introduce a tag system. Each article can have zero, one, or multiple tags. Tags are managed via the admin panel and are also synchronized with a system configuration file to ensure consistency with template logic.

## Requirements
- Tags are a separate entity, editable in the admin panel (CRUD, except for protected/system tags).
- Each article can be assigned multiple tags (many-to-many relationship).
- Tags are used in templates to select which articles appear in specific sections (e.g., headliner, suggested_articles).
- System tags (used in templates) are defined in a config file (`shared/system_tags.json`).
- System tags cannot be deleted or renamed from the UI unless removed from the config.
- Synchronization is one-way: from config to DB (never from DB to config).

## Data Model
- **Tag**
  - `id` (ObjectId)
  - `slug` (unique, used in code/templates)
  - `name` (human-readable)
  - `description` (optional)
  - `is_system` (bool, set via sync)
  - `required_fields`: List[str] (list of field names required by articles with this tag)
- **Article**
  - `tags: List[str]` (list of tag slugs)
  - `cover_image: Optional[str]` (Example field that might be required by a tag)
  - `headline: Optional[str]` (Example field that might be required by a tag)

## Synchronization Logic
1. On admin panel startup:
    - Read system tags from `shared/system_tags.json` (including `name`, `slug`, `description`, `required_fields`).
    - Read all tags from the database.
    - For each system tag in config:
        - If not in DB, create it (with `is_system=True` and other fields from config).
        - If in DB but not marked as system, set `is_system=True` and update other fields from config.
        - If in DB and already marked as system, update `name`, `description`, `required_fields` from config to ensure they are in sync.
    - For tags in DB that are not in config but marked as system, set `is_system=False` (do not delete).
    - **Tags are never deleted automatically.**
2. Deletion of tags is only possible via the admin UI and only if the tag is not system (`is_system=False`).

## Admin UI
- **Tags List Page (`/admin/tags`)**: CRUD for tags, list of articles per tag, ability to add/remove article-tag relations. System tags are visually marked and protected from deletion/renaming.
- **Article Editor (`/admin/articles/edit/{id}`)**: Assign one or more tags to an article (multi-select). Display non-blocking warnings if an assigned tag has `required_fields` that are missing/empty in the current article.

## Static Generation
- When generating the main page or other sections, select articles by tag (e.g., all with `headliner` tag for the main block) using MongoDB queries (`{"tags": "headliner"}`).
- Optionally, provide a generic Jinja2 microtemplate for rendering article lists by tag.

## Required Fields for Tags

Some tags may require that articles assigned to them have specific fields filled (e.g., a cover image for headliner articles). Not all articles have all possible fields, so this requirement is enforced as an admin UI warning, not as a hard constraint.

### Tag Structure Extension
- The `required_fields: List[str]` property is part of the Tag model (in `system_tags.json` and the DB model).
- Example `system_tags.json`:
```json
[
  {"slug": "headliner", "name": "Headliner", "description": "Main page headliner article", "required_fields": ["cover_image", "headline"]},
  {"slug": "suggested_articles", "name": "Suggested Articles", "description": "Articles suggested on the main page", "required_fields": ["cover_image"]}
]
```

### Admin UI Logic (Required Fields)
- When displaying the tag selection in the article editor:
    - For each assigned tag, check the article's data against the tag's `required_fields`.
    - If any required field is missing or empty in the article, display a warning near the tag selector or the specific tag.
- When viewing the list of articles associated with a specific tag (`/admin/tags/{slug}/articles`), display a warning icon/text next to articles that are missing required fields for that tag.
- Warnings **do not block** saving or generation but serve as a reminder to the editor.

### Benefits
- Flexible, scalable placement of articles in any section.
- System tags are protected and always in sync with template logic.
- Editors can manage both tags and article placement without code changes.
- Required fields mechanism helps ensure content quality for specific placements.

### Risks
- Requires careful sync logic to avoid accidental loss of system tag status.
- UI must clearly indicate which tags are system and protect them from deletion.
- If required fields change in the config, existing articles assigned to that tag may become non-compliant; UI must update warnings accordingly.
- Editors may ignore required field warnings, so periodic review might be needed for critical sections. 