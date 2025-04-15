# Design Document: Replace Editor with Tiptap

**1. Problem Statement (Updated):**

The previous attempts to integrate `Crepe`/`Milkdown` and `Editor.js`/`editorjs-md-parser` were unsuccessful or problematic. We will now replace the content editor with Tiptap (`tiptap.dev`). The goal is to provide a stable and maintainable WYSIWYG editing experience that loads existing Markdown content and saves the edited content back as Markdown.

**2. Plan (Updated for Tiptap):**

*   **Goal:** Integrate Tiptap editor into `admin_app/frontend/src/main.ts`.
*   **Branch:** `master` (as requested by user)
*   **Dependencies:**
    *   Remove: `@editorjs/editorjs`, `editorjs-md-parser`, `@editorjs/paragraph`, `@editorjs/header`, `@editorjs/list`, `@milkdown/crepe`, `@milkdown/kit` (ensure all previous editor dependencies are removed).
    *   Add: `@tiptap/core`, `@tiptap/pm` (ProseMirror core), `@tiptap/starter-kit` (basic nodes/marks), `marked` (Markdown -> HTML converter), `turndown` (HTML -> Markdown converter), `@types/marked`, `@types/turndown` (for TypeScript support).
*   **Implementation Steps:**
    1.  Update `npm` dependencies (install new, remove old).
    2.  Modify `admin_app/frontend/src/main.ts`:
        *   Remove all imports and logic related to `Editor.js` and `Crepe`/`Milkdown`.
        *   Import `Editor` from `@tiptap/core`, `StarterKit` from `@tiptap/starter-kit`.
        *   Import `marked` and `TurndownService`.
        *   **Initial Data Loading:**
            *   Get `initialContentMd` from the `#initial_markdown` textarea.
            *   If `initialContentMd` is not empty, convert it to HTML using `await marked.parse(initialContentMd)`.
            *   Initialize the Tiptap `Editor` instance, targeting the `#editor` element.
            *   Pass the generated HTML (or an empty string) to the `content` option during initialization.
            *   Use `StarterKit` in the `extensions` array for basic formatting support.
        *   **Saving:** In the form `submit` event handler:
            *   Get the current HTML content from the editor using `editor.getHTML()`.
            *   Initialize a `TurndownService` instance.
            *   Convert the HTML to Markdown using `turndownService.turndown(htmlContent)`.
            *   Write the resulting Markdown string to the `#content_md_hidden` input field.
            *   Allow the form submission to proceed.
    3.  **HTML/CSS:**
        *   Ensure the template (`admin_app/templates/admin/edit_article.html` or similar) has the required elements: `<div id="editor"></div>`, `<form id="article-form">...`, `<input type="hidden" id="content_md_hidden" name="content_md">`, `<textarea id="initial_markdown" style="display: none;">{{ article.content_md }}</textarea>`.
        *   Add basic CSS for Tiptap's default appearance if needed (or customize later). StarterKit provides minimal styling; more might be desired.
    4.  **Testing:** Thoroughly test loading existing Markdown, editing content (various formatting), and saving back to Markdown.

*   **Potential Challenges:**
    *   Ensuring Markdown -> HTML -> Markdown conversion fidelity (especially for complex Markdown). `marked` and `turndown` are generally good but might have edge cases.
    *   Styling Tiptap to fit the admin panel's design.
    *   Integrating image uploads will be a separate step, likely requiring a custom Tiptap extension. 