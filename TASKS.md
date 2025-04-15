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

*   [ ] Configure MongoDB connection.
*   [ ] Configure Jinja2 for templates in `generator/templates/`.
*   [ ] Create base templates (`base.html`, `article.html`).
*   [ ] Implement main logic in `generate.py`:
    *   [ ] Fetch all articles with status `published` from MongoDB.
    *   [ ] Clear the `static_output` directory before generation.
    *   [ ] For each article:
        *   [ ] Convert `content_md` to HTML using `markdown-it-py`.
        *   [ ] Render HTML using Jinja2 template (`article.html`).
        *   [ ] Save the result to `static_output/{slug}/index.html`.
    *   [ ] (Optional) Generate an index page with a list of articles.
    *   [ ] (Optional) Copy static assets (CSS, JS) to `static_output`.
*   [ ] Add logging to the generation script.

### Multilingual & Translation Pipeline (LLM)

*   [ ] Implement translation service for LLM API (translate_text, generate_slug)
*   [ ] Implement translation pipeline script:
    *   [ ] For each article and each supported language, check and generate missing translations (title, content_md, slug)
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
