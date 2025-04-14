# Static Site Generator with Admin Panel

> **Note:** All documentation, code comments, and commit messages in this project are written in **English**.

This project implements a static website generator with a web-based admin panel for content management.

## 1. Core Idea and Data Flow

*   **Admin Panel (FastAPI)**:
    *   Allows creating and editing articles in Markdown format.
    *   Stores articles, their status (`draft`, `published`), and versions in a MongoDB database.
    *   Handles image uploads and saves them to a MinIO (S3-compatible) storage.
*   **Static Site Generator (Python Script)**:
    *   Fetches all articles marked as `published` from MongoDB.
    *   Converts Markdown content to HTML using `markdown-it-py`.
    *   Renders the HTML content using Jinja2 templates.
    *   Outputs the final static `.html` files to the `static_output/` directory.
*   **Caddy (Web Server)**:
    *   Serves the contents of `static_output/` as the main public website (e.g., `https://example.com`), automatically handling HTTPS.
    *   Proxies requests to `/admin` (or `admin.example.com`) to the FastAPI admin application.
    *   Proxies requests to `/images` (or `images.example.com`) to the MinIO storage for serving images.
*   **MinIO (Self-hosted S3)**:
    *   Receives image uploads from the admin panel via the S3 API.
    *   Allows read access to images, served through the Caddy proxy.
*   **MongoDB (Database)**:
    *   Stores article data, including `title`, `slug`, `content_md`, `status`, `versions`, `created_at`, `updated_at`.

## 2. Directory Structure

```
my_project/
│
├── admin_app/                   # FastAPI application code (admin panel)
│   ├── main.py                  # Application entry point (run with uvicorn)
│   ├── models.py                # Pydantic/MongoEngine models
│   ├── routes/                  # API route definitions
│   │   ├── articles.py          # CRUD endpoints for articles
│   │   └── images.py            # Image upload endpoint (to MinIO)
│   └── requirements.txt         # Dependencies (fastapi, motor, boto3, etc.)
│
├── generator/                   # Static site generation script
│   ├── generate.py              # Main generation script
│   ├── templates/               # Jinja2 templates
│   │   ├── base.html
│   │   └── article.html
│   └── requirements.txt         # Dependencies (markdown-it-py, jinja2, pymongo)
│
├── static_output/               # Output directory for generated static files
│   └── ... (HTML files, assets)
│
├── infrastructure/              # Configuration files (Caddy, MinIO, Docker)
│   ├── Caddyfile                # Caddy configuration for serving static files and proxying
│   ├── docker-compose.yml       # Docker Compose setup (MinIO, MongoDB, Caddy, Admin)
│   └── minio_config/            # (Optional) MinIO server config/data
│
├── README.md                    # This file
├── TASKS.md                     # Implementation task list (in Russian)
└── .env.example                 # Example environment variables
```

## 3. Technology Stack

*   **Backend**: Python 3.9+, FastAPI
*   **Database**: MongoDB
*   **File Storage**: MinIO (S3-compatible)
*   **Web Server/Proxy**: Caddy v2
*   **Templating**: Jinja2
*   **Markdown Parsing**: `markdown-it-py`
*   **Containerization**: Docker, Docker Compose
*   **Python Libraries**: `fastapi`, `uvicorn`, `pydantic`, `motor` (async MongoDB driver) or `pymongo`, `boto3` (for S3), `python-multipart` (for file uploads), `jinja2`, `markdown-it-py`.

## 4. Workflow Scenario

1.  An authorized user accesses the admin panel (e.g., `https://example.com/admin`).
2.  The user creates or edits an article using a Markdown editor.
3.  When saving, the article data (Markdown content, title, slug, status `draft`) is sent to the FastAPI backend and stored in MongoDB.
4.  If the user uploads an image, the admin backend uploads it to MinIO via the S3 API.
5.  The backend receives the image URL (proxied through Caddy, e.g., `https://example.com/images/bucket_name/image.jpg`) and potentially stores it within the article content or metadata.
6.  Once the article is ready, the user changes its status to `published` via the admin panel.
7.  The `generator/generate.py` script is executed (manually or via cron job).
8.  The script fetches all `published` articles from MongoDB.
9.  For each article, it converts the Markdown content to HTML and renders it using the Jinja2 `article.html` template.
10. The resulting HTML file is saved to `static_output/slug/index.html`.
11. Caddy serves the static files from `static_output/` to public visitors, automatically handling HTTPS if a domain name is configured.
12. Visitors access the website (e.g., `https://example.com`) and see the static HTML pages.
13. Image URLs within the HTML content point to the Caddy `/images` reverse proxy, which serves them from MinIO.

## 5. Running the Project (General Steps)

See [infrastructure/DEV_SETUP.md](infrastructure/DEV_SETUP.md) for detailed development setup instructions.

1.  **Clone the repository.**
2.  **Configure Environment Variables**: Copy `.env.example` to `.env` and fill in the necessary values (database URI, MinIO credentials, domain name for Caddy if using HTTPS, etc.).
3.  **Build and Run Containers**: Use `docker-compose up --build -d` to start MongoDB, MinIO, Caddy, and the Admin application.
4.  **Access Admin**: Navigate to the admin URL defined by the Caddy proxy (e.g., `http://localhost/admin` or `https://yourdomain.com/admin`).
5.  **Generate Static Site**: Run the generation script (potentially inside the generator container or locally if dependencies are installed): `python generator/generate.py`.
6.  **Access Public Site**: Navigate to the main URL (e.g., `http://localhost` or `https://yourdomain.com`).

*(Detailed setup instructions will depend on the final `docker-compose.yml`, `Caddyfile`, and script configurations.)*

## Design Documents

- [JWT Authentication Design](design/jwt_auth_design.md) — authentication and authorization for the admin panel using JWT (in English)
- [Admin Panel UI Design](design/admin_ui_design.md) — web interface (SPA) for admin panel (in English)
- [Admin Panel UI Design (Jinja2/FastAPI)](design/admin_ui_jinja_design.md) — server-side web interface for admin panel (in English) 