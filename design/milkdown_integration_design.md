# Milkdown Integration Design (WYSIWYG Markdown Editor with MinIO)

## Problem Statement

Enable users to create and edit articles in the admin panel using a modern WYSIWYG editor that directly works with Markdown (Milkdown) and supports image uploads to MinIO. The editor must allow seamless editing of both new and existing articles stored as Markdown, and all images inserted via the editor should be stored in MinIO and served via Caddy proxy. The solution must be robust, user-friendly, and maintainable, minimizing backend complexity by working directly with Markdown.

## Requirements

- Integrate Milkdown editor into the article create/edit UI in the admin panel.
- Load existing Markdown articles directly into Milkdown for editing.
- Save content directly as Markdown from Milkdown for storage and static generation (no server-side JSON conversion needed).
- Allow users to insert images via Milkdown, uploading them to MinIO through a FastAPI backend endpoint.
- Serve images via Caddy proxy (e.g., `/images/bucket_name/filename.jpg`).
- Use the core Milkdown library and relevant official plugins (e.g., for image upload handling).
- Configure Milkdown with necessary ProseMirror/Remark plugins for common Markdown features (headings, lists, bold, italic, code blocks, images).
- Ensure the image upload backend endpoint is async and follows project conventions (type hints, enums, docstrings, logging).
- Requires frontend build setup (NPM/Yarn + bundler like Vite/Parcel) as Milkdown is typically not used via simple CDN scripts.
- Provide fallback editing (plain textarea) if Milkdown fails to load or is not supported.

## Architecture Overview

- **Frontend (Admin Panel):**
    - Requires a build system (e.g., Vite) to bundle Milkdown and its dependencies.
    - Milkdown editor is embedded in the article create/edit page, replacing the `<textarea>`.
    - Milkdown is configured with necessary ProseMirror/Remark plugins (commonmark, gfm, image upload handler).
    - On load: Existing Markdown content is passed directly to Milkdown.
    - On save: Milkdown provides the updated Markdown content, which is sent to the backend.
    - Image uploads are handled by a Milkdown plugin:
        - Plugin intercepts image insertion.
        - Sends image file to the FastAPI backend endpoint.
        - Receives the public image URL from the backend.
        - Inserts the correct Markdown image syntax (`![alt](url)`) into the editor content.

- **Backend (FastAPI):**
    - New async endpoint for image upload (e.g., `/api/admin/milkdown/upload_image`):
        - Receives image file from Milkdown uploader plugin.
        - Uploads to MinIO (using boto3).
        - Returns a JSON response containing the Caddy-proxied image URL (e.g., `{"url": "YOUR_CADDY_PROXIED_IMAGE_URL"}`).
    - Existing article CRUD endpoints (`create_article`, `update_article`) continue to receive and save `content_md` (no changes needed for content handling itself, as Milkdown provides Markdown directly).
    - Image upload endpoint uses type hints, enums, docstrings, and logging.

- **MinIO & Caddy:**
    - MinIO stores all uploaded images in a dedicated bucket (e.g., `images`).
    - Caddy proxies `/images` requests to MinIO for public access.

## Implementation Plan

1.  **Frontend Build Setup**
    - Integrate a Javascript build tool (e.g., Vite) into the `admin_app` if not already present.
    - Configure it to handle TypeScript/JavaScript bundling and static asset generation.

2.  **Milkdown Installation & Configuration**
    - Install Milkdown core, theme (e.g., `theme-nord`), and necessary plugins (`@milkdown/preset-commonmark`, `@milkdown/preset-gfm`, potentially custom image uploader logic) via npm/yarn.
    - Configure Milkdown editor instance with desired plugins and theme.

3.  **Frontend Integration**
    - In the Jinja2 template (`article_create.html`, `article_edit.html`), replace `<textarea>` with a container div for Milkdown (`<div id="editor">`).
    - Add JavaScript/TypeScript code (managed by the build tool) to:
        - Initialize Milkdown in the container div.
        - Pass existing `content_md` (from backend) to Milkdown on load.
        - Configure an image uploader plugin/listener:
            - On image insertion, prevent default behavior.
            - Send the image file to the backend API (`/api/admin/milkdown/upload_image`).
            - On successful upload, get the URL from the response.
            - Use Milkdown's commands to insert the Markdown image syntax (`![alt](url)`) at the correct position.
        - Before form submission, get the current Markdown content from Milkdown (`editor.action(getMarkdown())`).
        - Put the Markdown content into a hidden input field (`<input type="hidden" name="content_md">`) for form submission.

4.  **Backend Image Upload Endpoint**
    - Implement the async FastAPI endpoint (`POST /api/admin/milkdown/upload_image`).
    - Accept `UploadFile`.
    - Upload to MinIO.
    - Return JSON `{"url": "caddy_proxied_url"}` on success.
    - Handle potential errors (upload failure, invalid file type) gracefully.
    - Ensure the endpoint requires authentication.

5.  **Testing**
    - Test the frontend build process.
    - Test loading, editing, and saving articles with various Markdown features.
    - Test image upload workflow (selecting file, uploading, inserting Markdown syntax, verifying image on static site).
    - Test fallback textarea.

6.  **Documentation**
    - Document editor usage for admin users.
    - Document image upload API endpoint.
    - Document frontend build process requirements.

## References
- [Milkdown Documentation](https://milkdown.dev/)
- [Milkdown GitHub](https://github.com/Milkdown/milkdown)
- [ProseMirror Documentation](https://prosemirror.net/docs/)
- [Remark Documentation](https://github.com/remarkjs/remark)
- [MinIO Documentation](https://min.io/docs/minio/linux/index.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

*This document describes the design and implementation plan for integrating Milkdown as a WYSIWYG Markdown editor with MinIO image support. All implementation should follow this design for consistency and maintainability.* 