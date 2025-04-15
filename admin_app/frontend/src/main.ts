// Frontend entry point (admin_app/frontend/src/main.ts)

// Remove Editor.js and old editor imports
// import EditorJS, { type OutputData } from '@editorjs/editorjs';
// import Header from '@editorjs/header';
// import List from '@editorjs/list';
// import Paragraph from '@editorjs/paragraph';
// import { MDParser, MDImporter } from 'editorjs-md-parser';

// Import Tiptap and necessary extensions/tools
import { Editor } from '@tiptap/core';
import StarterKit from '@tiptap/starter-kit';
import { marked } from 'marked'; // Use named import if possible, check library export
import TurndownService from 'turndown'; // Use default import if that's how it's exported

console.log('Admin frontend entry point loaded.');

document.addEventListener('DOMContentLoaded', async () => { // Keep async for marked.parse
    const editorElement = document.getElementById('editor');
    const form = document.getElementById('article-form') as HTMLFormElement | null;
    const contentMdHiddenInput = document.getElementById('content_md_hidden') as HTMLInputElement | null;
    const initialMarkdownElement = document.getElementById('initial_markdown') as HTMLTextAreaElement | null;

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
                StarterKit, // Base extensions (paragraph, bold, italic, heading, etc.)
                // Add other Tiptap extensions here if needed (e.g., images, tables)
            ],
            content: initialContentHtml, // Set initial content (HTML)
            // autofocus: true, // Optional
            // editable: true, // Default
            // Add other Tiptap options here
        });

        console.log("Tiptap editor instance created.");

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