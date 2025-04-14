# Development & Production Setup Guide

This guide describes how to run the project in both development (localhost) and production (domain, HTTPS) modes using the `.env.dev` environment file and Caddy configuration.

## 1. Prerequisites
- Docker and Docker Compose installed
- Python 3.9+ (for local runs, optional)
- Git (for version control)

## 2. Environment Configuration

- All environment variables for the services are passed via the `environment` section in `docker-compose.yml`.
- The `.env` file is **not used** for variable substitution in the compose file itself.
- To run with your own environment variables, create or edit `.env.dev` in the project root (see example below).

## 3. Running with Docker Compose (Development: localhost)

By default, Caddy will serve the site on `http://localhost` (port 80) for local development.

Run all services using your environment file:

```powershell
docker-compose --env-file .env.dev up --build -d
```

This will start:
- MongoDB
- MinIO
- Caddy (serving on http://localhost)
- Admin App (FastAPI)

## 4. Running in Production (Domain & HTTPS)

To run with your own domain and enable HTTPS:

1. **Set the domain name in your environment file** (or export as an environment variable):
   ```dotenv
   CADDY_DOMAIN_NAME=yourdomain.com
   ```
2. **Edit `infrastructure/Caddyfile`:**
   - **Comment out or remove the line** `auto_https off` in the global options block at the top of the file. This enables automatic HTTPS via Let's Encrypt.
   - The Caddyfile already contains a block for `{$CADDY_DOMAIN_NAME}`. When this variable is set, Caddy will listen on your domain and obtain a certificate.
3. **Restart Caddy:**
   ```powershell
   docker-compose --env-file .env.dev up --build -d caddy
   ```
   (Or restart all services if needed)

**Note:** Your domain must point to your server's public IP address for HTTPS to work.

## 5. Accessing the Services

- **Admin Panel (Swagger UI):**
  - Dev: [http://localhost/admin/docs](http://localhost/admin/docs)
  - Prod: [https://yourdomain.com/admin/docs](https://yourdomain.com/admin/docs)
- **MinIO Console:**
  - Dev: [http://localhost:9001](http://localhost:9001)
  - Prod: [https://yourdomain.com:9001](https://yourdomain.com:9001) (if port is open)
- **Static Site:**
  - Dev: [http://localhost/](http://localhost/)
  - Prod: [https://yourdomain.com/](https://yourdomain.com/)

## 6. Useful Commands

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

## 7. Example .env.dev

```dotenv
# MongoDB
MONGO_URI=mongodb://mongo:27017/mydatabase
MONGO_DATABASE=mydatabase

# MinIO
MINIO_ENDPOINT_URL=http://minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=images
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin

# Admin App
ADMIN_APP_PORT=8000
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

# Caddy
CADDY_DOMAIN_NAME=localhost # For dev use 'localhost', for prod set your domain
CADDY_HTTP_PORT=80
CADDY_HTTPS_PORT=443
```

## 8. Notes
- Do not commit actual secrets in `.env.dev` to version control (`.gitignore` should prevent this).
- Use Swagger UI (`/admin/docs`) for testing API endpoints like image uploads.
- For production, ensure your domain's DNS is set up correctly and ports 80/443 are open.

---

For more details on the project structure and workflow, see the main [README.md](../README.md). 