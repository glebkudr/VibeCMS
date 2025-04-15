// Frontend entry point (admin_app/frontend/src/main.ts)

import { Crepe } from "@milkdown/crepe";
import "@milkdown/crepe/theme/common/style.css";
// Дополнительная тема для Crepe (можно выбрать другую или убрать)
import "@milkdown/crepe/theme/frame.css";
// Импортируем getMarkdown из kit, т.к. crepe зависит от kit
import { getMarkdown } from '@milkdown/kit/utils';

console.log('Admin frontend entry point loaded.');

document.addEventListener('DOMContentLoaded', () => {
    const editorElement = document.getElementById('editor');
    const form = document.getElementById('article-form') as HTMLFormElement | null;
    const contentMdHiddenInput = document.getElementById('content_md_hidden') as HTMLInputElement | null;
    const initialMarkdownElement = document.getElementById('initial_markdown') as HTMLTextAreaElement | null;

    if (!editorElement || !form || !contentMdHiddenInput) {
        console.log('Required elements for Crepe editor not found on this page (editor, form, or hidden input).');
        return;
    }

    const initialContent = initialMarkdownElement?.value ?? ''; // Получаем начальное значение

    console.log('Initializing Crepe editor...');

    try {
        const crepe = new Crepe({
            root: editorElement, // Корневой элемент для редактора
            defaultValue: initialContent, // Начальное содержимое
            // Здесь можно добавить listener'ы, если нужно отслеживать изменения
            // listener: {
            //    markdownUpdated: (ctx, markdown, prevMarkdown) => {
            //        console.log('Markdown updated:', markdown);
            //    },
            // }
        });

        // Создаем редактор
        crepe.create().then(() => {
            console.log("Crepe editor created successfully.");

            // Добавляем обработчик отправки формы
            form.addEventListener('submit', (e) => {
                console.log('Form submit intercepted.');
                try {
                    // Получаем доступ к внутреннему редактору Milkdown
                    // Убедитесь, что свойство называется именно 'editor' (или проверьте API Crepe)
                    const editorInstance = crepe.editor; // <--- Предполагаемое свойство
                    if (!editorInstance) {
                        throw new Error("Crepe editor instance not available for getting markdown.");
                    }

                    // Используем стандартный способ Milkdown/kit для получения Markdown
                    const markdown = editorInstance.action(getMarkdown());

                    console.log('Saving markdown:', markdown);
                    contentMdHiddenInput.value = markdown;
                    console.log('Hidden input updated, allowing form submission.');
                } catch (error) {
                    console.error('Error getting Markdown from Crepe:', error);
                    e.preventDefault();
                    alert('Error saving content. Could not get Markdown from Crepe editor.');
                }
            });
        }).catch(error => {
            // Ошибка при создании Crepe
            console.error('Failed to create Crepe editor:', error);
            editorElement.innerHTML = '<p style="color: red;">Failed to load Crepe editor.</p>';
        });

    } catch (error) {
        // Ошибка при инстанцировании Crepe (маловероятно, но на всякий случай)
        console.error('Failed to instantiate Crepe:', error);
        editorElement.innerHTML = '<p style="color: red;">Failed to instantiate Crepe editor.</p>';
    }
}); 