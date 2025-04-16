// Frontend entry point (admin_app/frontend/src/main.ts)
import './style.css'; // Import general styles
import './toolbar.css'; // Import toolbar specific styles
import './tiptap-editor.css'; // Import Tiptap editor styles

// Remove Editor.js and old editor imports
// import EditorJS, { type OutputData } from '@editorjs/editorjs';
// import Header from '@editorjs/header';
// import List from '@editorjs/list';
// import Paragraph from '@editorjs/paragraph';
// import { MDParser, MDImporter } from 'editorjs-md-parser';

// Import Tiptap and necessary extensions/tools
import { Editor, Extension, Range } from '@tiptap/core';
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
// Import Suggestion utility and related types
import { Plugin, PluginKey } from '@tiptap/pm/state'; // Need PluginKey
import Suggestion, { type SuggestionOptions, type SuggestionProps, type SuggestionKeyDownProps } from '@tiptap/suggestion';
import tippy, { type Instance as TippyInstance, type Props as TippyProps } from 'tippy.js';
import 'tippy.js/dist/tippy.css'; // Import default tippy styles (can be customized later)

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

// Remove marked and Turndown imports
// import { marked } from 'marked';
// import TurndownService from 'turndown';
import { log } from 'console';

console.log('Admin frontend entry point loaded.');

// --- Define Slash Commands --- START ---
// Define the type for our command items
type CommandItem = {
  title: string;
  command: (props: { editor: Editor; range: Range }) => void;
  aliases?: string[];
  iconSVG?: string; // Optional SVG string for the icon
};

// Define the list of commands (example) with icons
// Using Feather Icons SVG strings
const slashCommands: CommandItem[] = [
  {
    title: 'Heading 1', command: ({ editor, range }) => editor.chain().focus().deleteRange(range).setNode('heading', { level: 1 }).run(), aliases: ['h1'],
    iconSVG: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-heading-1"><path d="M4 12h8"/><path d="M4 18V6"/><path d="M12 18V6"/><path d="M17 12h3"/><path d="m18.5 7 3 5 -3 5"/></svg>`
  },
  {
    title: 'Heading 2', command: ({ editor, range }) => editor.chain().focus().deleteRange(range).setNode('heading', { level: 2 }).run(), aliases: ['h2'],
    iconSVG: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-heading-2"><path d="M4 12h8"/><path d="M4 18V6"/><path d="M12 18V6"/><path d="M21 18h-4c0-4 4-3 4-6 0-1.5-2-2.5-4-1"/></svg>`
  },
  {
    title: 'Heading 3', command: ({ editor, range }) => editor.chain().focus().deleteRange(range).setNode('heading', { level: 3 }).run(), aliases: ['h3'],
    iconSVG: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-heading-3"><path d="M4 12h8"/><path d="M4 18V6"/><path d="M12 18V6"/><path d="M17.5 10.5c1.7-1 3.5-1 3.5 1.5a2 2 0 0 1-2 2"/><path d="M17 17.5c2 1.5 4 .3 4-1.5a2 2 0 0 0-2-2"/></svg>`
  },
  {
    title: 'Bullet List', command: ({ editor, range }) => editor.chain().focus().deleteRange(range).toggleBulletList().run(), aliases: ['ul'],
    iconSVG: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-list"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>`
  },
  {
    title: 'Numbered List', command: ({ editor, range }) => editor.chain().focus().deleteRange(range).toggleOrderedList().run(), aliases: ['ol'],
    iconSVG: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-list-ordered"><line x1="10" x2="21" y1="6" y2="6"/><line x1="10" x2="21" y1="12" y2="12"/><line x1="10" x2="21" y1="18" y2="18"/><path d="M4 6h1v4"/><path d="M4 10h2"/><path d="M6 18H4c0-1 2-2 2-3s-1-1.5-2-1"/></svg>`
  },
  {
    title: 'Task List', command: ({ editor, range }) => editor.chain().focus().deleteRange(range).toggleTaskList().run(), aliases: ['todo'],
    iconSVG: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-check-square"><polyline points="9 11 12 14 22 4"></polyline><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path></svg>`
  },
  {
    title: 'Blockquote', command: ({ editor, range }) => editor.chain().focus().deleteRange(range).setBlockquote().run(),
    iconSVG: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-chevrons-right"><polyline points="13 17 18 12 13 7"/><polyline points="6 17 11 12 6 7"/></svg>`
  },
  {
    title: 'Code Block', command: ({ editor, range }) => editor.chain().focus().deleteRange(range).setCodeBlock().run(),
    iconSVG: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-terminal"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>`
  },
  {
    title: 'Table', command: ({ editor, range }) => editor.chain().focus().deleteRange(range).insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run(),
    iconSVG: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-grid"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/><line x1="9" y1="3" x2="9" y2="21"/><line x1="15" y1="3" x2="15" y2="21"/></svg>`
  },
  {
    title: 'Image', command: ({ editor, range }) => {
      editor.chain().focus().deleteRange(range).run();
      const imageUploadInput = document.getElementById('image-upload-input') as HTMLInputElement | null;
      imageUploadInput?.click();
    }, aliases: ['img'],
    iconSVG: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-image"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>`
  },
  {
    title: 'Horizontal Rule', command: ({ editor, range }) => editor.chain().focus().deleteRange(range).setHorizontalRule().run(), aliases: ['hr'],
    iconSVG: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-minus"><line x1="5" y1="12" x2="19" y2="12"></line></svg>`
  },
];

// --- Define Slash Commands --- END ---

// --- Create Vanilla JS Menu Renderer --- START ---

class SlashCommandMenuRenderer {
    element: HTMLElement;
    tippyInstance: TippyInstance | null = null;
    props: SuggestionProps<CommandItem>;
    selectedIndex: number = 0;

    constructor(props: SuggestionProps<CommandItem>) {
        this.props = props;
        this.element = document.createElement('div');
        this.element.className = 'slash-command-menu'; // Add a class for styling
        this.renderItems();
        this.element.addEventListener('click', this.handleClick);
        // Initial selection
        this.updateSelection(0);
    }

    renderItems = () => {
        this.element.innerHTML = ''; // Clear previous items
        if (this.props.items.length === 0) {
            this.element.textContent = 'No commands found';
            return;
        }
        this.props.items.forEach((item, index) => {
            const button = document.createElement('button');
            button.className = 'slash-command-item';
            button.dataset.index = String(index);

            // Create icon element
            const iconSpan = document.createElement('span');
            iconSpan.className = 'slash-command-item-icon';
            if (item.iconSVG) {
                iconSpan.innerHTML = item.iconSVG; // Set SVG content
            }
            button.appendChild(iconSpan);

             // Create text element
             const textSpan = document.createElement('span');
             textSpan.className = 'slash-command-item-text';
             textSpan.textContent = item.title;
             button.appendChild(textSpan);

            this.element.appendChild(button);
        });
        // Ensure selectedIndex is valid
        this.selectedIndex = Math.max(0, Math.min(this.selectedIndex, this.props.items.length - 1));
        this.updateSelection(this.selectedIndex);
    };

    handleClick = (event: MouseEvent) => {
        const target = event.target as HTMLElement;
        const button = target.closest('.slash-command-item') as HTMLButtonElement | null;
        if (button && button.dataset.index !== undefined) {
            this.selectItem(parseInt(button.dataset.index, 10));
        }
    };

    updateProps = (props: SuggestionProps<CommandItem>) => {
        this.props = props;
        this.renderItems();
    };

    onKeyDown = ({ event }: SuggestionKeyDownProps): boolean => {
        if (event.key === 'ArrowUp') {
            this.selectedIndex = (this.selectedIndex + this.props.items.length - 1) % this.props.items.length;
            this.updateSelection(this.selectedIndex);
            return true; // Mark as handled
        }
        if (event.key === 'ArrowDown') {
            this.selectedIndex = (this.selectedIndex + 1) % this.props.items.length;
            this.updateSelection(this.selectedIndex);
            return true; // Mark as handled
        }
        if (event.key === 'Enter') {
            this.selectItem(this.selectedIndex);
            return true; // Mark as handled
        }
        // Escape is handled by onExit in suggestion options usually
        return false; // Let Tiptap/suggestion handle other keys
    };

    updateSelection = (index: number) => {
        this.selectedIndex = index;
        const items = this.element.querySelectorAll('.slash-command-item');
        items.forEach((item, i) => {
            item.classList.toggle('is-selected', i === index);
        });
        // Scroll into view if needed
        const selectedButton = items[index];
        if (selectedButton) {
             selectedButton.scrollIntoView({ block: 'nearest' });
        }
    };

    selectItem = (index: number) => {
        const item = this.props.items[index];
        if (item) {
            console.log(`Executing command: ${item.title}`);
            this.props.command(item); // Pass the whole item to the command handler
        }
        // Tippy instance hiding should be handled by the onExit callback
    };

    destroy = () => {
        console.log("Destroying SlashCommandMenuRenderer");
        this.element.removeEventListener('click', this.handleClick);
        // Tippy instance should be destroyed in onExit
        if (this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
    };
}

// --- Create Vanilla JS Menu Renderer --- END ---

// --- Create Custom Slash Command Extension --- START ---

// Define any options we might want to configure later (optional)
// interface SlashCommandExtensionOptions {
//   suggestionOptions?: Partial<SuggestionOptions<CommandItem>>;
// }

const SlashCommandExtension = Extension.create<any>({
// const SlashCommandExtension = Extension.create<SlashCommandExtensionOptions>({
  name: 'slashCommand',

  // Remove addOptions if we don't have configurable options for now
  // addOptions() {
  //   return {
  //     suggestionOptions: {}, // Default empty config
  //   };
  // },

  addProseMirrorPlugins() {
    let menuRenderer: SlashCommandMenuRenderer | null = null;
    let tippyPopup: TippyInstance | null = null;

    // Helper function to safely get ClientRect or a default Rect
    const getClientRect = (clientRectFunc: (() => DOMRect | null) | null | undefined): DOMRect => {
         if (!clientRectFunc) {
            // Fallback if clientRect function is not available
            console.warn('SlashCommand: clientRect function unavailable');
            return new DOMRect(0, 0, 0, 0);
        }
        const rect = clientRectFunc();
        if (!rect) {
             // Fallback if clientRect() returns null
             console.warn('SlashCommand: clientRect() returned null');
             return new DOMRect(0, 0, 0, 0);
        }
        return rect;
    };

    const suggestionOptions: Omit<SuggestionOptions<CommandItem>, 'editor'> = {
        items: ({ query }) => {
            return slashCommands
                .filter(item => {
                    const titleMatch = item.title.toLowerCase().startsWith(query.toLowerCase());
                    const aliasMatch = item.aliases?.some(alias => alias.toLowerCase().startsWith(query.toLowerCase()));
                    return titleMatch || aliasMatch;
                })
                .slice(0, 10);
        },
        render: () => {
            return {
                onStart: (props: SuggestionProps<CommandItem>) => {
                    console.log('Slash Command Suggestion started (Vanilla):', props);
                    menuRenderer = new SlashCommandMenuRenderer(props);

                    const tippyOptions: Partial<TippyProps> = {
                         // Use the helper function to ensure a valid Rect is always returned
                        getReferenceClientRect: () => getClientRect(props.clientRect),
                        appendTo: () => document.body,
                        content: menuRenderer.element,
                        showOnCreate: true,
                        interactive: true,
                        trigger: 'manual',
                        placement: 'bottom-start',
                        theme: 'slash-command',
                        maxWidth: '16rem',
                        offset: [0, 8],
                        popperOptions: {
                            strategy: 'fixed',
                            modifiers: [{ name: 'flip', enabled: false }],
                        },
                    };
                    tippyPopup = tippy('body', tippyOptions)[0];

                     if (!tippyPopup) {
                        console.error("Failed to create Tippy instance for slash commands.");
                    }
                },
                onUpdate(props: SuggestionProps<CommandItem>) {
                    console.log('Slash Command Suggestion updated (Vanilla):', props);
                    menuRenderer?.updateProps(props);
                    // Use the helper function here as well
                    tippyPopup?.setProps({ getReferenceClientRect: () => getClientRect(props.clientRect) });
                },
                onKeyDown(props: SuggestionKeyDownProps): boolean {
                    console.log('Slash Command Suggestion keydown (Vanilla):', props.event.key);
                    if (props.event.key === 'Escape') {
                        tippyPopup?.hide();
                        return true;
                    }
                    return menuRenderer?.onKeyDown(props) ?? false;
                },
                onExit() {
                    console.log('Slash Command Suggestion exited (Vanilla)');
                    tippyPopup?.destroy();
                    menuRenderer?.destroy();
                    tippyPopup = null;
                    menuRenderer = null;
                },
            };
        },
        char: '/',
        allowSpaces: false,
        startOfLine: true,
        command: ({ editor, range, props }) => {
            const selectedItemCommand = props.command as (props: { editor: Editor; range: Range }) => void;
            selectedItemCommand({ editor, range });
        },
        pluginKey: new PluginKey('slashCommand')
        // Allow overriding parts via extension options if needed
        // ...this.options.suggestionOptions,
    };

    return [
      // Pass the editor instance along with the defined options
      Suggestion({
        editor: this.editor,
        ...suggestionOptions,
      }),
    ];
  },
});

// --- Create Custom Slash Command Extension --- END ---

document.addEventListener('DOMContentLoaded', async () => { // Keep async just in case, though marked is removed
    const editorElement = document.getElementById('editor');
    const form = document.getElementById('article-form') as HTMLFormElement | null;
    // Change hidden input ID and name
    const contentHtmlHiddenInput = document.getElementById('content_html_hidden') as HTMLInputElement | null;
    // Remove initial markdown textarea element reference
    // const initialMarkdownElement = document.getElementById('initial_markdown') as HTMLTextAreaElement | null;
    // Get initial HTML from a hidden div instead
    const initialHtmlContentElement = document.getElementById('initial_html_content') as HTMLDivElement | null;
    const imageUploadInput = document.getElementById('image-upload-input') as HTMLInputElement | null; // Get the file input

    // Check if the editor container exists on the page
    if (!editorElement) {
         console.log('Tiptap editor container (#editor) not found on this page.');
         return
    }

     // Ensure other required elements are present only if the editor container is found
     // Update check for the new hidden input ID
     if (!form || !contentHtmlHiddenInput) {
         console.warn('Required elements for Tiptap integration (form or content_html_hidden input) not found, though #editor exists.');
         // Allow editor initialization, but saving might fail.
     }

    // Get initial HTML from the hidden div
    const initialContentHtml = initialHtmlContentElement?.innerHTML ?? '';
    console.log('Initial HTML for Tiptap editor:', initialContentHtml);

    console.log('Initializing Tiptap editor...');

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
                // Add the custom SlashCommandExtension
                SlashCommandExtension, // No .configure() needed if using default options
            ],
            content: initialContentHtml, // Set initial content (HTML)
            // autofocus: true, // Optional
            // editable: true, // Default
            // Add other Tiptap options here
        });

        console.log("Tiptap editor instance created with SlashCommandExtension.");

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
                        if (result.url) {
                            editor.chain().focus().setImage({ src: result.url }).run();
                            console.log('Image uploaded and inserted:', result.url);
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
        if (form && contentHtmlHiddenInput) {
            form.addEventListener('submit', (e) => {
                console.log('Form submit intercepted for Tiptap.');
                try {
                    const htmlContent = editor.getHTML(); // Get HTML from Tiptap
                    console.log('Tiptap HTML output for submission:', htmlContent);

                    

                    // Remove Turndown conversion
                    /*
                    const turndownService = new TurndownService({ headingStyle: 'atx', bulletListMarker: '-' });
                    const markdownContent = turndownService.turndown(htmlContent); // Convert
                    console.log('Converted Tiptap HTML to Markdown:', markdownContent);
                    */

                    // Update the correct hidden input
                    contentHtmlHiddenInput.value = htmlContent; // Update hidden input with HTML
                    console.log('Hidden input (content_html_hidden) updated with HTML.');

                } catch (error) {
                    console.error('Error processing Tiptap content for submission:', error);
                    alert('Error saving content: Could not process editor content.');
                    e.preventDefault(); // Prevent submission ONLY if an error occurs
                }
            });
        } else {
             // Update warning message
             console.warn("Form or content_html_hidden input not found. Content saving via Tiptap is disabled.");
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