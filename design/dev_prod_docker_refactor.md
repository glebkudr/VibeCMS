# Dev/Prod Docker Refactor Design Doc

## Problem Statement

Currently, changes to Python (.py) and TypeScript (.ts) source files are not reflected in the running application without rebuilding Docker images. This slows down development and is not aligned with best practices for local development environments.

## Goals

- Enable hot-reload for backend (FastAPI) and frontend (Vite) in development mode.
- Allow source code changes to be immediately reflected without rebuilding containers.
- Keep production configuration immutable and optimized.
- Minimize changes to the existing structure and Dockerfiles.

## Proposed Solution

### 1. Add `.dockerignore`
Exclude unnecessary files and directories from Docker build context:
```
__pycache__
node_modules
*.pyc
*.pyo
*.pyd
.env
```

### 2. Add `docker-compose.override.yml` for Development
This override file will:
- Mount the project source code into the `admin_app` container.
- Override the backend command to use `uvicorn` with `--reload`.
- Optionally, expose the Vite dev server port (5173) if frontend is run inside Docker.

**Example `docker-compose.override.yml`:**
```yaml
version: '3.8'
services:
  admin_app:
    volumes:
      - ./admin_app:/app/admin_app
      - ./admin_app/frontend:/app/admin_app/frontend
      - ./admin_app/static:/app/admin_app/static
    command: >
      uvicorn admin_app.main:app --host 0.0.0.0 --port 8000 --reload
    environment:
      - ADMIN_APP_PORT=8000
      # (other envs as needed)
    # Optionally, expose Vite port if running frontend dev server in container
    # ports:
    #   - "5173:5173"
```

### 3. Frontend Development
- Recommended: Run `npm run dev` locally for the frontend (outside Docker) for best HMR experience.
- Alternatively: Add a frontend service to the override file to run Vite dev server in Docker.

### 4. Production (No Change)
- Continue to use the main `docker-compose.yml` and `Dockerfile` for production builds.
- No source code mounting, no hot-reload, only built static assets are served.

## Usage Instructions

**Development:**
1. `docker-compose up` (with override file present, this is automatic)
2. In a separate terminal: `cd admin_app/frontend && npm install && npm run dev`
   - Or run Vite dev server in Docker if desired.

**Production:**
- Use only `docker-compose.yml` (no override), build images as before.

## Notes
- Do not mount `node_modules` or `__pycache__` from host to container to avoid dependency conflicts.
- Adjust `.dockerignore` as needed to keep build context clean.

## Rollout Plan
- Implement `.dockerignore` and `docker-compose.override.yml`.
- Update documentation (README) with new dev/prod instructions.
- Test both dev and prod flows. 