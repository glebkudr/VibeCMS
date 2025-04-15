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
  - Dev: [http://localhost:8000/docs](http://localhost:8000/docs)
  - Prod: [https://yourdomain.com/admin/docs](https://yourdomain.com/admin/docs) *(see note below)*
  - **API endpoints:**
    - `POST http://localhost/api/admin/login` — obtain JWT token (for API/Swagger)
    - `GET http://localhost/api/admin/articles` — list articles (JSON)
    - `POST http://localhost/api/admin/images` — upload image (JSON)
  - **Admin UI (HTML):**
    - `http://localhost/admin/login` — login page (form, sets cookie)
    - `http://localhost/admin/articles` — article list (HTML)
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
- Use Swagger UI (`/docs` on port 8000) for testing API endpoints like image uploads in development mode. All API endpoints are now under `/api/admin/...`.
- For production, if you want Swagger UI at `/admin/docs`, set `root_path="/admin"` in your FastAPI app.
- Ensure your domain's DNS is set up correctly and ports 80/443 are open.

### Environment Variables (`.env` / `.env.dev`)

Key environment variables you'll need to configure:

*   `MONGO_URI`: Connection string for MongoDB.
*   `MONGO_DATABASE`: Database name.
*   `MINIO_ENDPOINT_URL`: URL for MinIO (e.g., `http://minio:9000` inside docker, `http://localhost:9000` from host).
*   `MINIO_ACCESS_KEY`: MinIO root user.
*   `MINIO_SECRET_KEY`: MinIO root password.
*   `MINIO_BUCKET_NAME`: Bucket for image uploads (e.g., `images`).
*   `ADMIN_USERNAME`: Initial admin username.
*   `ADMIN_PASSWORD`: Initial admin password (hashed after first change).
*   `JWT_SECRET_KEY`: Secret key for JWT tokens (generate a strong random key).
*   `CADDY_DOMAIN_NAME`: Domain name for Caddy (e.g., `yourdomain.com` for prod, `localhost` for dev).
*   `CADDY_HTTP_PORT`: Port Caddy listens on for HTTP (e.g., `80`).
*   `CADDY_HTTPS_PORT`: Port Caddy listens on for HTTPS (e.g., `443`).
*   **`VITE_DEV_MODE`**: Set to `true` **only for frontend development** with the Vite dev server. For production builds/runs, leave it unset or set to `false`.
*   **`VITE_DEV_SERVER_URL`**: (Optional) Override the default Vite dev server URL (`http://localhost:5173`) if needed.

## Frontend Development (Vite + Milkdown)

This project uses Vite for frontend asset bundling (specifically for the Milkdown editor in the admin panel).

**Two main modes:**

1.  **Production Mode (Default with `docker-compose up --build`)**
    *   When you build the `admin_app` Docker image (using `docker-compose up --build`), the `Dockerfile` runs `npm install --omit=dev` and `npm run build --prefix ./admin_app/frontend`.
    *   This creates optimized, static JS/CSS assets inside the image (`admin_app/static/admin_dist/`).
    *   FastAPI serves these pre-built assets.
    *   Ensure `VITE_DEV_MODE` is **not** set to `true` in your `.env` file for this mode.

2.  **Development Mode (with Hot Module Replacement - HMR)**
    *   This allows you to see changes to frontend code (e.g., Milkdown setup in `admin_app/frontend/src/main.ts`) instantly in the browser without rebuilding the Docker image.
    *   **Steps:**
        1.  **Set Environment:** In your `.env.dev` file, add or set `VITE_DEV_MODE=true`.
        2.  **Run Backend:** Start the backend services: `docker-compose --env-file .env.dev up -d` (you can omit `--build` if the image is already built and backend code hasn't changed significantly).
        3.  **Run Vite Dev Server:** In a **separate terminal**, navigate to the frontend directory and start the Vite dev server:
            ```powershell
            cd admin_app/frontend
            npm install # Run this once initially or after changing dependencies
            npm run dev
            ```
        4.  **Access Admin Panel:** Open the admin panel in your browser (e.g., `http://localhost/admin/articles/create`). FastAPI (thanks to `VITE_DEV_MODE=true`) will now load assets directly from the Vite dev server (`http://localhost:5173` by default).
    *   **Note:** The Vite dev server (`npm run dev`) runs on your **host machine**, not inside the Docker container in this setup. FastAPI inside the container fetches assets from `http://localhost:5173` (which resolves correctly due to Docker's networking). Ensure port 5173 is free on your host.

---

For more details on the project structure and workflow, see the main [README.md](../README.md). 