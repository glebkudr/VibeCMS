# Dynamic Menu Generation Based on Tags Design

## 1. Problem Statement

Modify the `menu.html` microtemplate to dynamically generate menu items based on the system tags `menu1`, `menu2`, and `menu3`. On hovering over a menu item (tag name), a dropdown should appear listing published articles associated with that tag.

## 2. Requirements

-   **Dynamic Menu Items**: Fetch data for tags `menu1`, `menu2`, `menu3` (specifically their `name` for display).
-   **Dropdown Content**: For each of these tags, fetch a list of associated `published` articles.
-   **Rendering**:
    -   The top-level menu displays the tag names (`menu1.name`, `menu2.name`, `menu3.name`).
    -   Hovering over a tag name reveals a dropdown list.
    -   The dropdown lists article titles (`title`) which are links to the corresponding article pages (`/{lang}/{slug}/index.html`).
-   **Data Preparation**: The static site generator must fetch and prepare the necessary data (menu tags and their associated published articles) and pass it to the Jinja2 rendering context.
-   **Styling**: Implement CSS for the menu and dropdowns, including hover effects.

## 3. Implementation Plan

1.  **Create Utility Function (`generator/utils.py`)**:
    -   If `generator/utils.py` doesn't exist, create it.
    -   Define an async function `get_published_articles_by_tag(db: AsyncIOMotorDatabase, tag_slug: str, limit: Optional[int] = None) -> List[ArticleRead]`.
    -   This function will query the `articles` collection for documents with `status: "published"` and the given `tag_slug` in the `tags` array.
    -   Return a list of `ArticleRead` objects, sorted by `updated_at` (descending). Add error handling.

2.  **Create Menu Data Module (`generator/menu_data.py`)**:
    -   Create the new file `generator/menu_data.py`.
    -   Import `get_published_articles_by_tag`, `TagRead`, `ArticleRead`, `AsyncIOMotorDatabase`.
    -   Define an async function `async def fetch_menu_data(db: AsyncIOMotorDatabase) -> List[Dict]`:
        -   Define `menu_slugs = ["menu1", "menu2", "menu3"]`.
        -   Query the `tags` collection for documents matching these slugs.
        -   Initialize `menu_items = []`.
        -   For each found menu tag:
            -   Fetch associated articles: `articles = await get_published_articles_by_tag(db, tag.slug, limit=5)`.
            -   Construct a dictionary: `{'name': tag.name, 'slug': tag.slug, 'articles': articles}`. Store the full `ArticleRead` objects.
            -   Append the dictionary to `menu_items`.
        -   Return `menu_items`. Add error handling.

3.  **Update Main Generator (`generator/generate.py`)**:
    -   Import `fetch_menu_data` from `generator.menu_data`.
    -   In the main generation function, call `menu_data = await fetch_menu_data(db)`.
    -   Pass `menu_data` into the global Jinja2 context or the context of templates using the menu (e.g., `base.html`). Ensure the variable name is consistent (e.g., `MENU_DATA`).

4.  **Modify Microtemplate (`generator/templates/microtemplates/menu.html`)**:
    -   Access the `MENU_DATA` list from the context.
    -   Iterate through `MENU_DATA`.
    -   For each `item` in `MENU_DATA`:
        -   Display `item.name` as a menu item link (or placeholder if no articles).
        -   Add HTML structure for the dropdown (e.g., `<div class="dropdown-content">`).
        -   Inside the dropdown, iterate through `item.articles`.
        -   For each `article`, display `article.title` as a link (`<a>`) with `href="/{{ lang }}/{{ article.slug }}/"`. Ensure `lang` is available in the template's context.

5.  **Add CSS Styling (`generator/static/css/style.css`)**:
    -   Add CSS rules for `.menu-item`, `.dropdown`, `.dropdown-content`, etc.
    -   Implement the show/hide logic for the dropdown on hover (`.menu-item:hover .dropdown-content { display: block; }`).

6.  **Update Task List (`TASKS.md`)**:
    -   Add a new task describing this feature and its sub-steps.

7.  **Branching**:
    -   Create a new git branch for this feature (e.g., `feature/dynamic-menu`).

8.  **Testing**:
    -   Verify data fetching and context passing.
    -   Check the rendered HTML structure in the output files.
    -   Test hover effects and links on generated pages across different languages.
    -   Ensure graceful handling if a menu tag has no published articles.

## 4. Relevant Files

-   `generator/templates/microtemplates/menu.html` (Modify)
-   `generator/generate.py` (Modify)
-   `generator/utils.py` (Create/Modify)
-   `generator/menu_data.py` (Create)
-   `generator/static/css/style.css` (Modify)
-   `admin_app/models.py` (Reference - `ArticleRead`, `TagRead`)
-   `shared/system_tags.json` (Reference - menu tag slugs/names)
-   `TASKS.md` (Modify)
-   `design/dynamic_menu_design.md` (Create) 