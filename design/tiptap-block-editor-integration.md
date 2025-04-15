# Design Document: Tiptap Block Editor Integration

**1. Goal:**

*   Integrate a Tiptap-based WYSIWYG editor into the admin panel (`admin_app/frontend/src/main.ts`), replacing previous editor implementations.
*   Base the implementation on the features and appearance of the editor from `tiptap-templates-main/templates/next-block-editor-app`.
*   Utilize the existing Vanilla TS + Vite stack.
*   Integrate Tailwind CSS for styling across the entire `admin_app/frontend`.
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
*   Editor styling based on the example, implemented with Tailwind CSS.
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
*   **Styling:**
    *   `tailwindcss`
    *   `postcss`
    *   `autoprefixer`

**4. Implementation Plan:**

1.  **Setup Tailwind CSS:** Configure Tailwind CSS for the `admin_app/frontend` project (create `tailwind.config.js`, `postcss.config.js`, update main CSS file to include Tailwind directives).
2.  **Install Dependencies:** Install all required Tiptap extensions and Tailwind dependencies via npm.
3.  **Analyze Example Config:** Find the Tiptap `Editor` configuration in `next-block-editor-app/src`, noting the `extensions` array and specific settings.
4.  **Update `main.ts` - Tiptap Extensions:** Replace `StarterKit` with the detailed list of required extensions, applying configurations from the example (e.g., for links, images, placeholders, tables, code blocks).
5.  **Define Toolbar HTML:** Create the necessary HTML structure for the toolbar in the Jinja2 template (`edit_article.html`), mirroring the example's buttons and controls.
6.  **Update `main.ts` - Toolbar Logic:** Add JS event listeners and handlers for toolbar buttons, executing Tiptap commands and updating button states (`is-active` class based on `editor.isActive(...)`).
7.  **Update `main.ts` - Link/Image/Table/etc. Logic:** Implement UI interactions for inserting/editing links, images (mock), tables, toggling task lists, etc., corresponding to toolbar actions.
8.  **Apply Tailwind Styles:** Style the editor container and toolbar elements using Tailwind utility classes, referencing the example's appearance.
9.  **Testing:** Thoroughly test all editor features, toolbar interactions, loading/saving content, and styling.

**5. Potential Challenges:**

*   Configuring Tailwind CSS within the existing Vite setup.
*   Recreating the React-based UI logic (tooltips, modals, state management) in Vanilla JS.
*   Ensuring Markdown conversion fidelity with complex elements like tables and task lists. 