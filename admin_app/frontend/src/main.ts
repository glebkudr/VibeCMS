// Frontend entry point (admin_app/frontend/src/main.ts)
import './style.css'; // Import general styles
import './toolbar.css'; // Import toolbar specific styles

// Remove Editor.js and old editor imports
// import EditorJS, { type OutputData } from '@editorjs/editorjs';
// import Header from '@editorjs/header';
// import List from '@editorjs/list';
// import Paragraph from '@editorjs/paragraph';
// import { MDParser, MDImporter } from 'editorjs-md-parser';

// Import Tiptap and necessary extensions/tools
import { Editor } from '@tiptap/core';
// Remove StarterKit import
// import StarterKit from '@tiptap/starter-kit';
import Blockquote from '@tiptap/extension-blockquote';
import Bold from '@tiptap/extension-bold';
import BulletList from '@tiptap/extension-bullet-list';
import Code from '@tiptap/extension-code';
import CodeBlockLowlight from '@tiptap/extension-code-block-lowlight';
import Document from '@tiptap/extension-document';
import Dropcursor from '@tiptap/extension-dropcursor';
import Gapcursor from '@tiptap/extension-gapcursor';
import HardBreak from '@tiptap/extension-hard-break';
import Heading from '@tiptap/extension-heading';
import History from '@tiptap/extension-history';
import HorizontalRule from '@tiptap/extension-horizontal-rule';
import Italic from '@tiptap/extension-italic';
import ListItem from '@tiptap/extension-list-item';
import OrderedList from '@tiptap/extension-ordered-list';
import Paragraph from '@tiptap/extension-paragraph';
import Strike from '@tiptap/extension-strike';
import Text from '@tiptap/extension-text';
// Import other necessary extensions based on design doc
import CharacterCount from '@tiptap/extension-character-count';
import Color from '@tiptap/extension-color';
import Focus from '@tiptap/extension-focus';
import FontFamily from '@tiptap/extension-font-family';
import Highlight from '@tiptap/extension-highlight';
import Image from '@tiptap/extension-image';
import Link from '@tiptap/extension-link';
import Placeholder from '@tiptap/extension-placeholder';
import Subscript from '@tiptap/extension-subscript';
import Superscript from '@tiptap/extension-superscript';
import Table from '@tiptap/extension-table';
import TableCell from '@tiptap/extension-table-cell';
import TableHeader from '@tiptap/extension-table-header';
import TableRow from '@tiptap/extension-table-row';
import TaskItem from '@tiptap/extension-task-item';
import TaskList from '@tiptap/extension-task-list';
import TextAlign from '@tiptap/extension-text-align';
import TextStyle from '@tiptap/extension-text-style';
import Typography from '@tiptap/extension-typography';
import Underline from '@tiptap/extension-underline';

// Import lowlight for code block syntax highlighting
// Try importing createLowlight if direct { lowlight } fails with TS
// import { lowlight } from 'lowlight';
import { createLowlight } from 'lowlight'
// Import specific languages using the lib path
import css from 'highlight.js/lib/languages/css';
import js from 'highlight.js/lib/languages/javascript';
import ts from 'highlight.js/lib/languages/typescript';
import html from 'highlight.js/lib/languages/xml'; // xml includes html
import python from 'highlight.js/lib/languages/python';
import bash from 'highlight.js/lib/languages/bash';

// Create lowlight instance
const lowlight = createLowlight()

// Register languages with lowlight instance
lowlight.register('html', html);
lowlight.register('css', css);
lowlight.register('js', js);
lowlight.register('ts', ts);
lowlight.register('python', python);
lowlight.register('bash', bash);

import { marked } from 'marked'; // Use named import if possible, check library export
import TurndownService from 'turndown'; // Use default import if that's how it's exported
import { log } from 'console';

console.log('Admin frontend entry point loaded.');

document.addEventListener('DOMContentLoaded', async () => { // Keep async for marked.parse
    const editorElement = document.getElementById('editor');
    const form = document.getElementById('article-form') as HTMLFormElement | null;
    const contentMdHiddenInput = document.getElementById('content_md_hidden') as HTMLInputElement | null;
    const initialMarkdownElement = document.getElementById('initial_markdown') as HTMLTextAreaElement | null;
    const imageUploadInput = document.getElementById('image-upload-input') as HTMLInputElement | null; // Get the file input

    // Check if the editor container exists on the page
    if (!editorElement) {
         console.log('Tiptap editor container (#editor) not found on this page.');
         // Don't return if form/hidden input exist, might be other forms on the page
         // Only proceed if editorElement is present.
         return
    }

     // Ensure other required elements are present only if the editor container is found
     if (!form || !contentMdHiddenInput) {
         console.warn('Required elements for Tiptap integration (form or hidden input) not found, though #editor exists.');
         // Allow editor initialization, but saving might fail.
     }

    const initialContentMd = initialMarkdownElement?.value ?? ''; // Get initial markdown

    console.log('Initializing Tiptap editor...');

    let initialContentHtml = '';
    if (initialContentMd) {
        try {
            // Use marked to convert initial Markdown to HTML
            // Make sure marked is configured to handle potential security risks if needed
            // Using await as marked.parse might be async
            initialContentHtml = await marked.parse(initialContentMd);
            console.log('Initial Markdown converted to HTML for Tiptap.');
        } catch (error) {
            console.error("Error converting initial Markdown to HTML:", error);
            // Initialize Tiptap with empty content in case of error
        }
    }

    try {
        // Initialize Tiptap Editor
        const editor = new Editor({
            element: editorElement, // Bind to the #editor div
            extensions: [
                // Instead of StarterKit, list extensions individually
                // Core Nodes
                Document,
                Paragraph,
                Text,
                Blockquote,
                CodeBlockLowlight.configure({
                    lowlight,
                    defaultLanguage: 'plaintext', // Or another default
                    // You might need to configure language mapping if class names differ
                }),
                HardBreak,
                Heading.configure({ levels: [1, 2, 3, 4, 5, 6] }),
                HorizontalRule,
                ListItem,
                BulletList,
                OrderedList,
                // Core Marks
                Bold,
                Code,
                Italic,
                Strike,
                Underline,
                // Other extensions from the list
                CharacterCount, // No specific config needed for basic count
                Color, // Allows setting text color
                TextStyle, // Required by Color, FontFamily, etc.
                Dropcursor, // Visual feedback for drag/drop
                Focus.configure({ // Style for focused state
                    className: 'has-focus', // Add custom class
                }),
                FontFamily, // Allows changing font
                Gapcursor, // For navigating between nodes
                Highlight.configure({ multicolor: true }), // Allow multiple highlight colors
                History, // Undo/redo functionality
                Image.configure({
                    inline: false, // Allow images to be block elements
                    allowBase64: false, // Disallow base64 images for security/performance
                    // We'll need custom logic later to handle uploads and insert URLs
                    HTMLAttributes: {
                        class: 'content-image', // Add a class for styling
                    },
                }),
                Link.configure({
                    openOnClick: false, // Don't open links immediately on click in the editor
                    autolink: true, // Automatically detect links as users type
                    linkOnPaste: true, // Detect links on paste
                    HTMLAttributes: {
                        target: '_blank', // Open links in new tab by default
                        rel: 'noopener noreferrer nofollow', // Security and SEO best practices
                    },
                }),
                Placeholder.configure({
                    placeholder: 'Начните писать здесь...', // Customize placeholder text
                }),
                Subscript,
                Superscript,
                Table.configure({
                    resizable: true, // Allow resizing table columns
                }),
                TableRow,
                TableHeader,
                TableCell,
                TaskList, // Container for TaskItems
                TaskItem.configure({
                    nested: true, // Allow nested task lists
                }),
                TextAlign.configure({ // Configure alignment options
                    types: ['heading', 'paragraph'], // Apply alignment to headings and paragraphs
                    alignments: ['left', 'center', 'right', 'justify'],
                    defaultAlignment: 'left',
                }),
                Typography, // Apply typographic enhancements (e.g., smart quotes)

                // Note: Some extensions might have interdependencies or require specific order.
                // Review Tiptap docs if issues arise.
            ],
            content: initialContentHtml, // Set initial content (HTML)
            // autofocus: true, // Optional
            // editable: true, // Default
            // Add other Tiptap options here
        });

        console.log("Tiptap editor instance created with detailed extensions.");

        // --- Toolbar Logic --- START ---
        const toolbar = document.getElementById('tiptap-toolbar');

        // Helper function to update button active state
        const updateToolbarButtons = () => {
            if (!toolbar) return;
            // Basic formatting
            toolbar.querySelector('#toolbar-bold')?.classList.toggle('is-active', editor.isActive('bold'));
            toolbar.querySelector('#toolbar-italic')?.classList.toggle('is-active', editor.isActive('italic'));
            toolbar.querySelector('#toolbar-underline')?.classList.toggle('is-active', editor.isActive('underline'));
            toolbar.querySelector('#toolbar-strike')?.classList.toggle('is-active', editor.isActive('strike'));
            toolbar.querySelector('#toolbar-code')?.classList.toggle('is-active', editor.isActive('code'));
            // Headings & Paragraph
            toolbar.querySelector('#toolbar-h1')?.classList.toggle('is-active', editor.isActive('heading', { level: 1 }));
            toolbar.querySelector('#toolbar-h2')?.classList.toggle('is-active', editor.isActive('heading', { level: 2 }));
            toolbar.querySelector('#toolbar-h3')?.classList.toggle('is-active', editor.isActive('heading', { level: 3 }));
            toolbar.querySelector('#toolbar-p')?.classList.toggle('is-active', editor.isActive('paragraph'));
            // Lists
            toolbar.querySelector('#toolbar-ul')?.classList.toggle('is-active', editor.isActive('bulletList'));
            toolbar.querySelector('#toolbar-ol')?.classList.toggle('is-active', editor.isActive('orderedList'));
            toolbar.querySelector('#toolbar-task')?.classList.toggle('is-active', editor.isActive('taskList'));
            // Other blocks
            toolbar.querySelector('#toolbar-blockquote')?.classList.toggle('is-active', editor.isActive('blockquote'));
            toolbar.querySelector('#toolbar-codeblock')?.classList.toggle('is-active', editor.isActive('codeBlock'));
            toolbar.querySelector('#toolbar-link')?.classList.toggle('is-active', editor.isActive('link'));
            toolbar.querySelector('#toolbar-table')?.classList.toggle('is-active', editor.isActive('table'));
            // Add more checks for other buttons (image, hr, highlight, color, text-align, sub/sup, font-family, etc.)
        };

        // Add event listeners to toolbar buttons
        if (toolbar) {
            toolbar.querySelector('#toolbar-bold')?.addEventListener('click', () => editor.chain().focus().toggleBold().run());
            toolbar.querySelector('#toolbar-italic')?.addEventListener('click', () => editor.chain().focus().toggleItalic().run());
            toolbar.querySelector('#toolbar-underline')?.addEventListener('click', () => editor.chain().focus().toggleUnderline().run());
            toolbar.querySelector('#toolbar-strike')?.addEventListener('click', () => editor.chain().focus().toggleStrike().run());
            toolbar.querySelector('#toolbar-code')?.addEventListener('click', () => editor.chain().focus().toggleCode().run());

            toolbar.querySelector('#toolbar-h1')?.addEventListener('click', () => editor.chain().focus().toggleHeading({ level: 1 }).run());
            toolbar.querySelector('#toolbar-h2')?.addEventListener('click', () => editor.chain().focus().toggleHeading({ level: 2 }).run());
            toolbar.querySelector('#toolbar-h3')?.addEventListener('click', () => editor.chain().focus().toggleHeading({ level: 3 }).run());
            toolbar.querySelector('#toolbar-p')?.addEventListener('click', () => editor.chain().focus().setParagraph().run());

            toolbar.querySelector('#toolbar-ul')?.addEventListener('click', () => editor.chain().focus().toggleBulletList().run());
            toolbar.querySelector('#toolbar-ol')?.addEventListener('click', () => editor.chain().focus().toggleOrderedList().run());
            toolbar.querySelector('#toolbar-task')?.addEventListener('click', () => editor.chain().focus().toggleTaskList().run());
            toolbar.querySelector('#toolbar-blockquote')?.addEventListener('click', () => editor.chain().focus().toggleBlockquote().run());
            toolbar.querySelector('#toolbar-codeblock')?.addEventListener('click', () => editor.chain().focus().toggleCodeBlock().run());

            // Link - Requires custom logic (prompt for URL)
            toolbar.querySelector('#toolbar-link')?.addEventListener('click', () => {
                const previousUrl = editor.getAttributes('link').href;
                const url = window.prompt('URL', previousUrl);
                // cancelled
                if (url === null) {
                    return;
                }
                // empty url - remove link
                if (url === '') {
                    editor.chain().focus().extendMarkRange('link').unsetLink().run();
                    return;
                }
                // update link
                editor.chain().focus().extendMarkRange('link').setLink({ href: url }).run();
            });

            // Image - Trigger hidden file input
            const imageButton = toolbar.querySelector('#toolbar-image');
            if (imageButton && imageUploadInput) {
                imageButton.addEventListener('click', () => {
                    imageUploadInput.click(); // Trigger file selection dialog
                });
            } else {
                console.warn("Image button or file input not found, image upload disabled.");
            }

            // Table - Requires custom logic (prompt for rows/cols or menu)
            toolbar.querySelector('#toolbar-table')?.addEventListener('click', () => {
                // Basic table insertion, can be expanded with prompts or menu
                editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run();
            });

            toolbar.querySelector('#toolbar-hr')?.addEventListener('click', () => editor.chain().focus().setHorizontalRule().run());
            toolbar.querySelector('#toolbar-undo')?.addEventListener('click', () => editor.chain().focus().undo().run());
            toolbar.querySelector('#toolbar-redo')?.addEventListener('click', () => editor.chain().focus().redo().run());

             // Add listeners for other buttons...
        }

        // Update button states on transaction/selection change
        editor.on('transaction', updateToolbarButtons);
        editor.on('selectionUpdate', updateToolbarButtons);

        // Initial button state check
        updateToolbarButtons();

        // --- Toolbar Logic --- END ---

        // --- Image Upload Logic --- START ---
        if (imageUploadInput) {
            imageUploadInput.addEventListener('change', async (event) => {
                const files = (event.target as HTMLInputElement).files;
                if (!files || files.length === 0) {
                    return; // No file selected
                }
                const file = files[0];

                // Optional: Add file size/type validation here if needed

                const formData = new FormData();
                formData.append('file', file); // Key 'file' must match FastAPI endpoint parameter name

                // Display some loading indication (optional)
                console.log('Uploading image...');
                // You could disable the image button here

                try {
                    const response = await fetch('/api/admin/images', {
                        method: 'POST',
                        // Headers are not usually needed for FormData with fetch,
                        // and cookies should be sent automatically for auth.
                        body: formData,
                    });

                    if (response.ok) {
                        const result = await response.json();
                        if (result.image_url) {
                            editor.chain().focus().setImage({ src: result.image_url }).run();
                            console.log('Image uploaded and inserted:', result.image_url);
                        } else {
                            console.error('Image upload failed: URL not found in response.', result);
                            alert('Image upload failed: Could not get image URL.');
                        }
                    } else {
                        const errorText = await response.text();
                        console.error('Image upload failed:', response.status, errorText);
                        alert(`Image upload failed: ${response.status} ${errorText}`);
                    }
                } catch (error) {
                    console.error('Image upload request failed:', error);
                    alert('Image upload request failed. See console for details.');
                } finally {
                    // Reset the input value to allow selecting the same file again
                    imageUploadInput.value = '';
                    // Hide loading indication (optional)
                    // Re-enable the image button here
                }
            });
        }
        // --- Image Upload Logic --- END ---

        // Add form submit handler only if form and hidden input are valid
        if (form && contentMdHiddenInput) {
            form.addEventListener('submit', (e) => {
                // Don't preventDefault initially, let Turndown run first
                console.log('Form submit intercepted for Tiptap.');
                try {
                    const htmlContent = editor.getHTML(); // Get HTML from Tiptap
                    console.log('Tiptap HTML output:', htmlContent);

                    // Initialize Turndown service to convert HTML back to Markdown
                    // Configure Turndown options if needed (e.g., headingStyle, bulletListMarker)
                    const turndownService = new TurndownService({ headingStyle: 'atx', bulletListMarker: '-' });

                    const markdownContent = turndownService.turndown(htmlContent); // Convert
                    console.log('Converted Tiptap HTML to Markdown:', markdownContent);

                    contentMdHiddenInput.value = markdownContent; // Update hidden input
                    console.log('Hidden input updated with Markdown.');
                    // Now allow the form submission to proceed naturally
                    // If we prevented default: form.submit();

                } catch (error) {
                    console.error('Error processing Tiptap content for submission:', error);
                    alert('Error saving content: Could not process editor content.');
                    e.preventDefault(); // Prevent submission ONLY if an error occurs
                }
            });
        } else {
             console.warn("Form or hidden input not found. Content saving via Tiptap is disabled.");
        }

        // Optional: Handle editor destruction on page unload
        window.addEventListener('beforeunload', () => {
            editor.destroy();
        });

    } catch (error) {
        console.error('Failed to initialize Tiptap editor:', error);
        if (editorElement) {
             editorElement.innerHTML = '<p style="color: red;">Failed to load Tiptap editor.</p>';
        }
    }
}); 