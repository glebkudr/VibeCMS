# Static Site Generator with Admin Panel

> **Note:** All documentation, code comments, and commit messages in this project are written in **English**.

## Target Audience and Use Cases

This project is ideal for:

*   **Individuals or small teams** who need a simple, self-hostable solution to manage content for a static website (like a blog, portfolio, or documentation site).
*   **Developers** looking for a starting point or example of a Python/FastAPI-based content management system combined with a static site generator.
*   Users who prefer a straightforward **WYSIWYG editor** experience (Tiptap) for content creation over writing Markdown directly.
*   Situations where the **performance, security, and simplicity of a static website** are desired, but a dynamic admin interface is needed for content updates.

It provides a balance between the ease of content management typically found in dynamic CMS platforms and the benefits of a static website architecture.

This project implements a static website generator with a web-based admin panel for content management.

## 1. Core Idea and Data Flow

*   **Admin Panel (FastAPI)**:
    *   Allows creating and editing articles using a **Tiptap-based WYSIWYG editor**.
    *   Stores articles, their status (`draft`, `published`), **HTML content (`content_html`)**, and versions in a MongoDB database.
    *   Handles image uploads and saves them to a MinIO (S3-compatible) storage.
    *   **API endpoints are available under `/api/admin/...` (e.g., `/api/admin/login`, `/api/admin/articles`).**
    *   **Server-side HTML admin UI is available under `/admin/...` (e.g., `/admin/login`, `/admin/articles`).**
*   **Static Site Generator (Python Script)**:
    *   Fetches all articles marked as `published` from MongoDB.
    *   Uses the pre-rendered **HTML content (`content_html`)** from the database.
    *   Renders the complete article page using Jinja2 templates and the fetched HTML content.
    *   Outputs the final static `.html` files to the `static_output/` directory.
*   **Caddy (Web Server)**:
    *   Serves the contents of `static_output/` as the main public website (e.g., `https://example.com`), automatically handling HTTPS.
    *   Proxies requests to `/admin` (or `admin.example.com`) to the FastAPI admin application.
    *   Proxies requests to `/images` (or `images.example.com`) to the MinIO storage for serving images.
*   **MinIO (Self-hosted S3)**:
    *   Receives image uploads from the admin panel via the S3 API.
    *   Allows read access to images, served through the Caddy proxy.
*   **MongoDB (Database)**:
    *   Stores article data, including `title`, `slug`, **`content_html` (generated by Tiptap)**, `status`, `versions`, `created_at`, `updated_at`.

## 2. Directory Structure

The project is organized into the following main components:

**1. Admin Panel (`admin_app/`)**
*   `admin_app/`: Contains the FastAPI backend code for the admin web interface and API.

**2. Static Site Generator (`generator/`)**
*   `generator/`: Holds the Python script and Jinja2 templates responsible for generating the static website from database content.

**3. Static Site Output (`static_output/`)**
*   `static_output/`: The target directory where the generated static HTML files are placed. This directory is served by Caddy to the public.

**4. Infrastructure & Configuration (`infrastructure/`, Docker, Env)**
*   `infrastructure/`: Stores configuration files, primarily the `Caddyfile`.
*   `docker-compose.yml`: Defines the services (Admin, Caddy, MinIO, MongoDB) and their orchestration.
*   `docker-compose.override.yml`: Provides development-specific overrides for the Docker Compose setup.
*   `.env.example`, `.env.dev`: Environment variable configuration files.
*   `.dockerignore`: Specifies files to exclude from Docker builds.

**5. Development & Project Files**
*   `design/`: Contains design documents related to architecture and features.
*   `prompt/`: Files related to prompt engineering (if applicable).
*   `scripts/`: Utility and helper scripts for development or deployment tasks.
*   `specification/`: Project requirements and specifications.
*   `testing/`: Contains tests for the project components.
*   `node_modules/`, `package.json`, `package-lock.json`: Node.js related files (potentially for frontend assets or build tools).
*   `.github/`: Configuration for GitHub Actions or other repository settings (optional).
*   `.gitignore`: Specifies intentionally untracked files that Git should ignore.
*   `LICENSE.md`: Project license information.
*   `README.md`: This main documentation file.
*   `TASKS.md`: List of development tasks.

## 3. Technology Stack

*   **Backend**: Python 3.9+, FastAPI
*   **Database**: MongoDB
*   **File Storage**: MinIO (S3-compatible)
*   **Web Server/Proxy**: Caddy v2
*   **Templating**: Jinja2
*   **Markdown Parsing**: `markdown-it-py` (No longer used for article content rendering)
*   **Containerization**: Docker, Docker Compose
*   **Python Libraries**: `fastapi`, `uvicorn`, `pydantic`, `motor` (async MongoDB driver) or `pymongo`, `boto3` (for S3), `python-multipart` (for file uploads), `jinja2`.
*   **Frontend Editor**: Tiptap (Vanilla TS)

**Important:**
- All admin panel (FastAPI) routes that interact with MongoDB **must be implemented as asynchronous handlers** (`async def`).
- This is required for correct operation with the Motor async MongoDB driver and to avoid runtime errors.

## 4. Workflow Scenario

1.  An authorized user accesses the admin panel (e.g., `https://example.com/admin`).
2.  The user creates or edits an article using the **Tiptap WYSIWYG editor**.
3.  When saving, the article data (**HTML content from Tiptap**, title, slug, status `draft`) is sent to the FastAPI backend and stored in MongoDB (in the `content_html` field).
4.  If the user uploads an image within the editor, the admin backend uploads it to MinIO via the S3 API.
5.  The backend receives the image URL (proxied through Caddy, e.g., `https://example.com/images/bucket_name/image.jpg`) and the Tiptap editor inserts this URL into the `content_html`.
6.  Once the article is ready, the user changes its status to `published` via the admin panel.
7.  The `generator/generate.py` script is executed (manually or via cron job).
8.  The script fetches all `published` articles from MongoDB.
9.  For each article, it takes the pre-rendered **`content_html`** and renders the full page using the Jinja2 `article.html` template.
10. The resulting HTML file is saved to `static_output/slug/index.html`.
11. Caddy serves the static files from `static_output/` to public visitors, automatically handling HTTPS if a domain name is configured.
12. Visitors access the website (e.g., `https://example.com`) and see the static HTML pages.
13. Image URLs within the HTML content point to the Caddy `/images` reverse proxy, which serves them from MinIO.

## 5. Microtemplates

This project supports "microtemplates" – reusable Jinja2 components that can be embedded directly into the article content via the text editor. This allows for dynamic content sections within static pages, such as menus, footers, call-to-action blocks, or other frequently used elements.

**How it Works:**

1.  **Registry:** A central registry file `shared/jinja_microtemplates.json` defines all available microtemplates, including their unique tag name, expected parameters, and the corresponding Jinja2 template file.
2.  **Template Files:** The actual Jinja2 template files for each microtemplate are located in `generator/templates/microtemplates/`.
3.  **Embedding in Editor:** Users can insert microtemplates into the article content (currently via raw HTML, editor integration planned) using a specific `<span>` tag format:
    ```html
    <span data-jinja-tag="your_template_tag" data-jinja-params='{"param1": "value1", "param2": 123}'></span>
    ```
    - `data-jinja-tag`: The unique name of the microtemplate as defined in the registry.
    - `data-jinja-params`: A JSON string containing the parameters to pass to the Jinja2 template.
4.  **Generation:** During the static site generation process (`generator/generate.py`):
    - The script fetches the published article's `content_html`.
    - It scans the HTML for `span[data-jinja-tag]` elements.
    - For each found span, it looks up the tag in the registry.
    - It loads the corresponding Jinja2 template from `generator/templates/microtemplates/`.
    - It renders the template using the parameters provided in `data-jinja-params`.
    - The original `<span>` tag is replaced with the rendered HTML output of the microtemplate.
    - The final processed HTML is then used to render the complete article page.

**Use Cases:**

-   Consistent headers/footers across specific article types.
-   Embedding dynamic lists (e.g., related articles, latest posts).
-   Reusable content blocks or call-to-action sections.
-   Inserting interactive elements requiring specific backend logic during generation.

For technical details, see [Jinja2 Template Editor Architecture](design/jinja2_template_editor_architecture.md).

## 6. Running the Project (General Steps)

See [infrastructure/DEV_SETUP.md](infrastructure/DEV_SETUP.md) for detailed development setup instructions.

1.  **Clone the repository.**
2.  **Configure Environment Variables**: Copy `.env.example` to `.env` and fill in the necessary values (database URI, MinIO credentials, domain name for Caddy if using HTTPS, etc.).
3.  **Build and Run Containers**: Use `docker-compose up --build -d` to start MongoDB, MinIO, Caddy, and the Admin application.
4.  **Access Admin**: Navigate to the admin URL defined by the Caddy proxy (e.g., `http://localhost/admin` or `https://yourdomain.com/admin`).
    - **API endpoints:**
        - `POST http://localhost/api/admin/login` — obtain JWT token (for API/Swagger)
        - `GET http://localhost/api/admin/articles` — list articles (JSON)
        - `POST http://localhost/api/admin/images` — upload image (JSON)
    - **Admin UI (HTML):**
        - `http://localhost/admin/login` — login page (form, sets cookie)
        - `http://localhost/admin/articles` — article list (HTML)
5.  **Generate Static Site**: Run the generation script (potentially inside the generator container or locally if dependencies are installed): `python generator/generate.py`.
6.  **Access Public Site**: Navigate to the main URL (e.g., `http://localhost` or `https://yourdomain.com`).

*(Detailed setup instructions will depend on the final `docker-compose.yml`, `Caddyfile`, and script configurations.)*

## License

This project is licensed under the terms described in the [LICENSE.md](LICENSE.md) file.

## Design Documents

- [JWT Authentication Design](design/jwt_auth_design.md) — authentication and authorization for the admin panel using JWT (in English)
- [Admin Panel UI Design](design/admin_ui_design.md) — web interface (SPA) for admin panel (in English)
- [Admin Panel UI Design (Jinja2/FastAPI)](design/admin_ui_jinja_design.md) — server-side web interface for admin panel (in English)
- [Tiptap Block Editor Integration](design/tiptap-block-editor-integration.md) — architecture and plan for Tiptap WYSIWYG editor integration (in English)

## Admin Password Management

- On first launch, the admin password is taken from the environment variable (`ADMIN_PASSWORD`).
- After changing the password (via UI or API), the new password is stored as a hash in MongoDB and only the hash is used for authentication.
- If the hash is deleted from the database, the system falls back to using the environment variable password.
- Password can be changed via:
  - The admin UI: "Change Password" link on the login page
  - The API: `POST /api/admin/change-password` with `{ "current_password": ..., "new_password": ... }`
- Changing the password always requires entering the current password.
- For security, set a strong initial password in the environment variable and change it after first login.

## Project Rules

- See [Project Rules and Gotchas](design/projectrules.md) for important implementation notes and pitfalls (e.g., MongoDB bool check). 