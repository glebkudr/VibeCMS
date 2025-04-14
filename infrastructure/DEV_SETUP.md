# Development Setup Guide

This guide describes how to run the project in development mode using the `.env.dev` environment file.

## 1. Prerequisites
- Docker and Docker Compose installed
- Python 3.9+ (for local runs, optional)
- Git (for version control)

## 2. Environment Configuration

- Copy `.env.dev` to `.env` in the project root if you want to run locally:
  ```powershell
  # If .env already exists, you might want to back it up first
  Copy-Item .env.dev .env -Force
  ```
- Alternatively, Docker Compose typically automatically loads `.env` if present in the project root.

## 3. Running with Docker Compose

Ensure you have a `.env` file (either copied from `.env.dev` or `.env.example`) in the project root.

Then build and start all services:

```powershell
docker-compose up --build -d
```

This will start:
- MongoDB
- MinIO
- Caddy
- Admin App (FastAPI)

## 4. Accessing the Services

- **Admin Panel (Swagger UI):** [http://localhost/admin/docs](http://localhost/admin/docs)
- **MinIO Console:** [http://localhost:9001](http://localhost:9001) (Default login: `minioadmin` / `minioadmin` - as set in `.env`/`.env.dev`)
- **Static Site (served by Caddy):** [http://localhost/](http://localhost/)

## 5. Useful Commands

- Stop all services:
  ```powershell
  docker-compose down
  ```
- Stop and remove volumes (clears data):
  ```powershell
  docker-compose down -v
  ```
- Rebuild only the `admin_app` service:
  ```powershell
  docker-compose up --build -d admin_app
  ```
- View logs for all services:
  ```powershell
  docker-compose logs -f
  ```
- View logs for a specific service (e.g., `admin_app`):
  ```powershell
  docker-compose logs -f admin_app
  ```

## 6. Notes
- It is recommended to use `.env.dev` (copied to `.env`) for local development.
- Do not commit actual secrets in `.env` or `.env.dev` to version control (`.gitignore` should prevent this).
- Use Swagger UI (`/admin/docs`) for testing API endpoints like image uploads.

---

For more details on the project structure and workflow, see the main [README.md](../README.md). 