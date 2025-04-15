# Milkdown/Crepe Image Upload Integration Design

## 1. Overview

This document describes the architecture and implementation plan for enabling image uploads from the Crepe (Milkdown) editor in the admin panel. Uploaded images will be stored in MinIO (S3-compatible storage) and served via the Caddy proxy. The integration ensures secure, authenticated uploads and seamless user experience in the Markdown editor.

## 2. Requirements

- Image uploads from the Crepe editor must be sent to the backend and stored in MinIO.
- Public URLs for images must be returned and inserted into the Markdown content.
- Authentication: Only authorized users (JWT) can upload images.
- File validation: Only image files are accepted.
- Logging and error handling at all stages.
- No string constants for types/statuses—use ENUMs.
- Reuse existing dependencies; discuss before adding new ones.
- Type hints, docstrings, and logging in all new code.
- Documentation for API and integration.

## 3. Architecture

### 3.1. Backend (FastAPI)

- **Endpoint:**  
  `POST /api/admin/milkdown/upload_image`
  - Accepts: `multipart/form-data` with an image file.
  - Requires: JWT authentication.
  - Validates: File type (image only, using MIME and extension).
  - Stores: File in MinIO bucket (using existing S3 client).
  - Returns: JSON `{ "url": "<public_image_url>" }` (Caddy-proxied).
  - Logs: All actions and errors.
  - Uses: ENUM for file type validation and error codes.

### 3.2. Frontend (Crepe/Milkdown)

- **Custom image upload handler:**
  - On image insert (paste, drag'n'drop, toolbar), intercept and upload file to backend endpoint.
  - On success, insert `![alt](url)` into Markdown.
  - Handles errors (shows alert/log).
  - Sends JWT (from cookie or header) for authentication.

### 3.3. Security

- Only authenticated users can upload.
- File type and size validation.
- No direct MinIO access from frontend.

### 3.4. Serving Images

- Images are served via Caddy proxy at `/images/<bucket>/<filename>`.
- URLs returned by backend are already proxied.

## 4. API Specification

### 4.1. Upload Image

- **URL:** `/api/admin/milkdown/upload_image`
- **Method:** `POST`
- **Auth:** JWT (cookie or header)
- **Request:** `multipart/form-data`  
  - Field: `file` (image)
- **Response:**  
  - `200 OK`: `{ "url": "<public_image_url>" }`
  - `4xx/5xx`: Error code and message (ENUM for error codes)

## 5. File Changes

- `admin_app/routes/images.py` (or new `milkdown_upload.py`)
- `admin_app/models.py` (ENUMs for file types/errors)
- `admin_app/frontend/src/main.ts` (Crepe upload handler)
- `shared/enums.py` (if needed)
- `README.md` and `design/milkdown_integration_design.md` (update)
- (Optional) Jinja2 templates for token/config passing

## 6. Error Handling & Logging

- All backend actions are logged (success, error, file info).
- Frontend shows user-friendly error messages.
- ENUMs for error codes.

## 7. Testing

- Manual: Upload images via editor, check MinIO and static site.
- Automated: Backend endpoint tests (file type, auth, error cases).
- Static site generator: Ensure images render in output HTML.

## 8. Security Considerations

- Max file size limit (configurable).
- Only image MIME types/extensions allowed.
- JWT required for upload.
- No direct MinIO credentials exposed to frontend.

## 9. Documentation

- API endpoint usage.
- Editor integration for admin users.
- Image URL format and serving. 