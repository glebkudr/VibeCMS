# Implementation Task Plan

This file contains the list of tasks for developing the static site generator with an admin panel.

## Phase 1: Infrastructure and Environment Setup

*   [x] Create basic project directory structure (`admin_app`, `generator`, `infrastructure`, `static_output`).
*   [x] Write `docker-compose.yml` to run:
    *   [x] MongoDB
    *   [x] MinIO (with bucket setup for images, e.g., `images`)
    *   [x] Admin App (FastAPI/Uvicorn) - basic Python image is fine for now
    *   [x] Caddy
*   [x] Write a basic `Caddyfile` with settings for:
    *   [x] Serving static files from `static_output` (with auto-HTTPS if domain is specified)
    *   [x] Proxying `/admin` to the Admin App
    *   [x] Proxying `/images` to MinIO
*   [x] Create `.env.example` file with necessary environment variables (MONGO_URI, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_ENDPOINT_URL, MINIO_BUCKET_NAME, CADDY_DOMAIN_NAME).
*   [x] Set up basic `requirements.txt` for `admin_app` and `generator`.
*   [ ] Verify all services start via `docker-compose up`.
*   [x] Update Caddyfile to support both localhost (:80) and domain (from CADDY_DOMAIN_NAME env), with correct global block and shared config.
*   [x] Update DEV_SETUP.md to document dev/prod Caddy usage, HTTPS, and environment variable setup. Ensure instructions and Caddyfile are consistent.

## Phase 2: Admin Panel Development (Admin App - FastAPI)

*   [x] Configure MongoDB connection (using `motor` or `pymongo`).
    _Done 2025-04-14: Async connection via motor, centralized in main.py._
*   [x] Define Pydantic models for articles (`ArticleCreate`, `ArticleRead`, `ArticleUpdate`, `ArticleInDB`).
    _Done 2025-04-14: admin_app/models.py, with documentation._
*   [x] Implement CRUD operations for articles (`/admin/articles`):
    _Done 2025-04-14: admin_app/routes/articles.py, tests — testing/test_articles_crud.py._
    *   [x] POST `/admin/articles`: Create a new article (default status `draft`).
    *   [x] GET `/admin/articles`: Get a list of articles (with pagination).
    *   [x] GET `/admin/articles/{article_id}`: Get a specific article.
    *   [x] PUT `/admin/articles/{article_id}`: Update an article (including status change).
    *   [x] DELETE `/admin/articles/{article_id}`: Delete an article.
*   [x] Configure MinIO connection (using `boto3`).
*   [x] Implement image upload endpoint (`/admin/images`):
    *   [x] POST `/admin/images`: Accepts a file, uploads to MinIO, returns image URL (via Caddy proxy).
*   [x] Add JWT authentication/authorization for the admin panel (FastAPI):
    *   [x] POST /admin/login — issue JWT on login/password (plain, no hash)
    *   [x] Require JWT for all protected endpoints (API and UI)
    *   [x] Integrate with Swagger UI (Authorize button)
    *   [x] Use JWT in cookie for UI, in header for API
    *   [x] Protect UI routes via cookie JWT (redirect to login if not authorized)
    *   [x] Add logout endpoint (clears cookie)
    *   [x] Add root redirect: / → /admin/articles (if logged in) or /admin/login (if not)
    *   [x] Remove conflicting API root route ("/")
    *   [x] Document async requirement for all UI routes using MongoDB
    *   [x] Refactor all UI routes to async def and use await with motor
*   [x] (Separate task) Switch password storage to hash (passlib) after basic JWT auth is ready.
*   [x] (Separate task) Allow admin to change password via UI (settings page, only for authorized user).
*   [x] (Separate task) Protect password change with current password check and require authorization.
*   [x] (Separate task) Update UI: move password change to settings, add visual separation.
*   [x] (Separate task) Update documentation and .env.example for new password management scheme.
*   [x] (Separate task) Add project rules and gotchas to design/projectrules.md (e.g., MongoDB bool check).
*   [ ] (Optional) Implement article versioning on update.
*   [ ] Add logging.

## Phase 2.5: Admin Panel UI (Server-side, FastAPI + Jinja2)

*   [x] Implement server-side admin interface (FastAPI + Jinja2):
    *   [x] Login page (form, JWT in cookie or session)
    *   [x] Logout endpoint
    *   [x] Article list page (CRUD)
    *   [x] Article view page (with "Edit" button)
    *   [x] Article delete endpoint (POST, CSRF)
    *   [x] Root redirect logic (see above)
    *   [x] Async refactor for all UI routes
    *   [x] Protect all UI routes via JWT in cookie
    *   [x] Remove API root route conflict
    *   [x] Document async requirement for UI
*   [ ] Implement article editor UI (separate task, not in scope for now)

## Phase 3: Static Site Generator Development (Generator)

*   [x] Configure MongoDB connection.
*   [x] Configure Jinja2 for templates in `generator/templates/`.
*   [x] Create base templates (`base.html`, `article.html`).
*   [x] Implement main logic in `generate.py`:
    *   [x] Fetch all articles with status `published` from MongoDB.
    *   [x] Clear the `static_output` directory before generation.
    *   [x] For each article:
        *   [x] Render HTML using Jinja2 template (`article.html`) with `content_html`.
        *   [x] Save the result to `static_output/{slug}/index.html`.
    *   [ ] (Optional) Generate an index page with a list of articles.
    *   [x] (Optional) Copy static assets (CSS, JS) to `static_output`.
*   [x] Add logging to the generation script.
*   [x] Add button in admin panel to trigger static site generation
*   [x] Add base CSS style for static site

## Tiptap Block Editor Integration (Vanilla TS + CSS)

*   [x] Extract CSS styles for editor and toolbar from `tiptap-templates-main/templates/next-block-editor-app`.
*   [x] Create a dedicated CSS file (e.g., `admin_app/frontend/src/tiptap-editor.css`) for the styles.
*   [x] Import the `tiptap-editor.css` file in `admin_app/frontend/src/main.ts`.
*   [x] Apply appropriate CSS classes to editor container and toolbar elements in `admin_app/templates/edit_article.html`.
*   [x] Refine extracted CSS to match the project's structure and context.
*   [x] Install required Tiptap extensions (Link, Image, Table, Task List, Code Highlighting, etc.) and `lowlight`.
*   [x] Analyze Tiptap configuration in `next-block-editor-app` example.
*   [x] Update `main.ts`: Replace `StarterKit` with the detailed list of extensions from the example.
*   [x] Update `main.ts`: Configure extensions (Link, Image, Placeholder, Table, CodeBlockLowlight) based on the example.
*   [x] Update `edit_article.html`: Add HTML structure for the Tiptap toolbar (buttons, controls) based on the example.
*   [x] Update `main.ts`: Implement toolbar button event listeners and Tiptap command execution.
*   [x] Update `main.ts`: Implement toolbar button state updates (`is-active`) based on `editor.isActive()`.
*   [x] Update `main.ts`: Implement basic UI logic for link editing.
*   [x] Update `main.ts`: Implement basic UI logic for image insertion (using the already implemented upload).
*   [x] Update `main.ts`: Implement basic UI logic for table insertion/modification.
*   [ ] Implement missing toolbar buttons and logic (Highlight, Color, Align, Sub/Sup, etc.).
*   [ ] Improve UI logic for link and table insertion (e.g., use modals).
*   [x] Initialize Tippy.js tooltips for toolbar buttons.
*   [ ] Test all integrated Tiptap features (formatting, links, images, tables, tasks, code blocks).
*   [x] Verify HTML saving from Tiptap and usage in generator.
*   [ ] Test styling applied from the extracted CSS.

### Slash Command Menu
*   [x] Install `@tiptap/suggestion` and `tippy.js` dependencies.
*   [x] Create `SlashCommandExtension` extending `Tiptap Extension`.
*   [x] Define list of commands (`slashCommands`) in `main.ts`.
*   [x] Configure `Suggestion` utility within the extension.
*   [x] Create `SlashCommandMenuRenderer` class in `main.ts` to manage menu DOM/events.
*   [x] Integrate `SlashCommandMenuRenderer` and `tippy.js` in the extension's `render` function.
*   [x] Add basic CSS styles for the slash command menu and items to `tiptap-editor.css`.
*   [ ] Implement rendering of icons and descriptions in the menu items (optional).
*   [ ] Test slash command activation, filtering, keyboard navigation, and command execution.
*   [ ] Refine CSS styles for the slash command menu.

### Multilingual & Translation Pipeline (LLM)

*   [ ] Implement translation service for LLM API (translate_text, generate_slug)
*   [ ] Implement translation pipeline script:
    *   [ ] For each article and each supported language, check and generate missing translations (title, content_html, slug)
    *   [ ] Store translations in MongoDB under translations[lang]
    *   [ ] Mark machine-generated translations (optional)
    *   [ ] Support dry-run and verbose logging modes
    *   [ ] Ensure idempotency (do not overwrite manual edits)
*   [ ] Integrate translation pipeline as a pre-step in the static generator
*   [ ] Update static generator:
    *   [ ] For each article and each language, generate HTML in static_output/<lang>/<slug>/index.html
    *   [ ] Pass lang and hreflang links to Jinja2 templates
    *   [ ] Generate hreflang tags in <head> of each page
    *   [ ] (Optional) Generate index.html and sitemap for each language
*   [ ] Test translation pipeline and multilingual static generation
*   [ ] Update documentation and .env.example for LLM API and multilingual support

## Phase 4: Testing and Refinement

*   [ ] Test the full cycle: create article -> upload image -> publish -> run generator -> check static site and image accessibility.
*   [ ] Configure CORS in FastAPI if the admin panel will be a SPA.
*   [ ] Add error handling and validation to all components.
*   [ ] Verify Caddy proxy works correctly for all locations.
*   [ ] Write/update documentation in `README.md`.

## Phase 5: Deployment

*   [ ] Prepare deployment instructions for a server.
*   [ ] Set up CI/CD (optional).
*   [ ] Set up backups for MongoDB and MinIO.

## Phase X: Jinja2 Template Editor Integration (Tiptap + Micro-Templates)

*   [x] Create and populate `shared/jinja_microtemplates.json` as the single source of truth for all micro-templates (structure, parameters, template filename).
*   [x] Create Jinja2 template files for each micro-template in `generator/templates/microtemplates/` (filenames as specified in the registry).
*   [ ] Implement export of the registry for both Python (backend) and TypeScript (frontend) via `shared/` and `graphql-types/`.
*   [x] Implement a universal Tiptap extension that dynamically generates custom nodes and slash-menu commands based on the registry.
*   [x] Update the admin panel editor UI to use the new micro-template system (insertion, editing, validation, hints).
*   [x] Update the static site generator to parse span tags (`data-jinja-tag`, `data-jinja-params`) and render them using the corresponding Jinja2 templates and parameters.
*   [ ] Implement a validator script that checks correspondence between the registry and template files (existence, parameter match).
*   [ ] (Optional) Implement autogeneration of documentation for micro-templates from the registry (Markdown or HTML for editors/admins).
*   [ ] Document the process for adding new micro-templates in the project documentation.
