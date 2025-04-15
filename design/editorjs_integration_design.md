# Editor.js Integration Design (Block Editor with Markdown & MinIO)

## Problem Statement

Enable users to create and edit articles in the admin panel using a modern block-based editor (Editor.js) with support for Markdown import/export and image uploads to MinIO. The editor must allow seamless editing of both new and existing articles (stored as Markdown), and all images inserted via the editor should be stored in MinIO and served via Caddy proxy. The solution must be robust, user-friendly, and maintainable.

## Requirements

- Integrate Editor.js into the article create/edit UI in the admin panel.
- Support import of existing Markdown articles into Editor.js for editing.
- Support export of Editor.js content back to Markdown for storage and static generation.
- Allow users to insert images via Editor.js, uploading them to MinIO through a FastAPI backend endpoint.
- Serve images via Caddy proxy (e.g., `/images/bucket_name/filename.jpg`).
- Use only well-maintained Editor.js plugins for Markdown and image support.
- Ensure all backend endpoints are async and follow project conventions (type hints, enums, docstrings, logging).
- Do not introduce new dependencies unless necessary; confirm with the team before adding any.
- Provide fallback editing (textarea) if Editor.js is not supported.

## Architecture Overview

- **Frontend (Admin Panel):**
    - Editor.js is embedded in the article create/edit page.
    - Uses plugins:
        - Markdown parser/exporter (for Markdown ↔ Editor.js JSON conversion)
        - Image Tool (with custom uploader for MinIO backend)
    - On load: Markdown is converted to Editor.js JSON for editing.
    - On save: Editor.js JSON is converted back to Markdown for storage.
    - Image uploads are sent to the FastAPI backend, which stores them in MinIO and returns a public URL.

- **Backend (FastAPI):**
    - New async endpoint for image upload:
        - Receives image file from Editor.js
        - Uploads to MinIO (using boto3)
        - Returns Caddy-proxied image URL
    - Existing article CRUD endpoints are updated to support Editor.js JSON and Markdown conversion as needed.
    - All endpoints use type hints, enums, docstrings, and logging.

- **MinIO & Caddy:**
    - MinIO stores all uploaded images in a dedicated bucket (e.g., `images`).
    - Caddy proxies `/images` requests to MinIO for public access.

## Implementation Plan

1. **Plugin Research & Selection**
    - Identify and test Editor.js plugins for Markdown import/export.
    - Select and configure Image Tool plugin with custom uploader.

2. **Frontend Integration**
    - Install Editor.js and required plugins.
    - Embed Editor.js in the article editor page.
    - Implement Markdown → Editor.js JSON conversion on load.
    - Implement Editor.js JSON → Markdown conversion on save.
    - Configure Image Tool to upload images to backend endpoint.
    - Display uploaded images in the editor.
    - Provide fallback textarea for unsupported browsers.

3. **Backend Integration**
    - Implement async FastAPI endpoint for image upload to MinIO.
    - Return Caddy-proxied image URL to frontend.
    - Update article CRUD endpoints to handle Editor.js JSON and Markdown conversion.
    - Add logging and docstrings to all new/modified endpoints.

4. **Migration of Existing Articles**
    - Implement conversion of existing Markdown articles to Editor.js JSON for editing.
    - Implement conversion of Editor.js JSON back to Markdown for storage and static generation.

5. **Testing**
    - Test full workflow: create/edit/save/generate articles with text, images, and blocks.
    - Test image upload and display.
    - Test Markdown ↔ Editor.js JSON conversion.
    - Test fallback editing mode.

6. **Documentation**
    - Document editor usage for admin users.
    - Document image upload API for developers.

## References
- [Editor.js documentation](https://editorjs.io/)
- [Editor.js GitHub](https://github.com/codex-team/editor.js)
- [Editor.js Image Tool](https://github.com/editor-js/image)
- [Editor.js Markdown Parser (example)](https://github.com/IlyaShirko/editorjs-parser)
- [MinIO documentation](https://min.io/docs/minio/linux/index.html)
- [FastAPI documentation](https://fastapi.tiangolo.com/)

---

*This document describes the design and implementation plan for integrating Editor.js as a block-based article editor with Markdown and MinIO image support. All implementation should follow this design for consistency and maintainability.* 