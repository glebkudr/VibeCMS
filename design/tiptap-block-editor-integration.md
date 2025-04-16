# Design Document: Tiptap Block Editor Integration

**1. Goal:**

*   Integrate a Tiptap-based WYSIWYG editor into the admin panel (`admin_app/frontend/src/main.ts`), replacing previous editor implementations.
*   Base the implementation on the features and appearance of the editor from `tiptap-templates-main/templates/next-block-editor-app`.
*   Utilize the existing Vanilla TS + Vite stack.
*   Use plain CSS for styling, extracting styles from the example project.
*   Exclude all paid `@tiptap-pro/*` extensions.
*   Retain `marked` (MD->HTML) and `turndown` (HTML->MD) for content conversion.

**2. Features to Replicate (from example, using free extensions):**

*   Core text formatting (bold, italic, headings, lists, etc.).
*   Code Blocks with Syntax Highlighting.
*   Link editing.
*   Image insertion (mocked initially).
*   Tables.
*   Task Lists (checkboxes).
*   A menu bar/toolbar similar to the example.
*   Editor styling based on the example, implemented with plain CSS extracted from the example.
*   *Note:* Block Drag & Drop from the example will **not** be implemented due to reliance on a paid extension.

**3. Dependencies:**

*   **Core:** `@tiptap/core`, `@tiptap/pm`, `@tiptap/starter-kit` (installed).
*   **Converters:** `marked`, `turndown`, `@types/turndown` (installed).
*   **Required Extensions (Based on Example & Confirmation):**
    *   `@tiptap/extension-link`
    *   `@tiptap/extension-image`
    *   `@tiptap/extension-placeholder`
    *   `@tiptap/extension-underline`
    *   `@tiptap/extension-highlight`
    *   `@tiptap/extension-color`
    *   `@tiptap/extension-text-style`
    *   `@tiptap/extension-text-align`
    *   `@tiptap/extension-subscript`
    *   `@tiptap/extension-superscript`
    *   `@tiptap/extension-typography`
    *   `@tiptap/extension-focus`
    *   `@tiptap/extension-character-count`
    *   `@tiptap/extension-dropcursor`
    *   `@tiptap/extension-font-family`
    *   `@tiptap/extension-table`
    *   `@tiptap/extension-table-row`
    *   `@tiptap/extension-table-header`
    *   `@tiptap/extension-table-cell`
    *   `@tiptap/extension-task-list`
    *   `@tiptap/extension-task-item`
    *   `@tiptap/extension-code-block-lowlight`
    *   `lowlight` (peer dependency for code highlighting)

**4. Implementation Plan:**

1.  **Install Dependencies:** Install all required Tiptap extensions via npm.
2.  **Analyze Example Config:** Find the Tiptap `Editor` configuration in `next-block-editor-app/src`, noting the `extensions` array and specific settings.
3.  **Update `main.ts` - Tiptap Extensions:** Replace `StarterKit` with the detailed list of required extensions, applying configurations from the example (e.g., for links, images, placeholders, tables, code blocks).
4.  **Define Toolbar HTML:** Create the necessary HTML structure for the toolbar in the Jinja2 template (`edit_article.html`), mirroring the example's buttons and controls.
5.  **Update `main.ts` - Toolbar Logic:** Add JS event listeners and handlers for toolbar buttons, executing Tiptap commands and updating button states (`is-active` class based on `editor.isActive(...)`).
6.  **Update `main.ts` - Link/Image/Table/etc. Logic:** Implement UI interactions for inserting/editing links, images (using existing upload), tables, toggling task lists, etc., corresponding to toolbar actions.
7.  **Extract & Apply CSS Styles:** Extract CSS styles for the editor and toolbar from the `next-block-editor-app` example project. Apply these styles using CSS classes in the Jinja2 template and a dedicated CSS file (e.g., `admin_app/frontend/src/tiptap-editor.css`).
8.  **Testing:** Thoroughly test all editor features, toolbar interactions, loading/saving content, and styling.

**5. Potential Challenges:**

*   Extracting and adapting CSS from the example project accurately.
*   Recreating the React-based UI logic (tooltips, modals, state management) in Vanilla JS.
*   Ensuring Markdown conversion fidelity with complex elements like tables and task lists. 