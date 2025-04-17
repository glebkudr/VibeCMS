import { Node, mergeAttributes } from '@tiptap/core';
// Важно: Уточните правильный путь к вашему файлу реестра JSON
// Возможно, потребуется настроить module resolution или использовать относительный путь
// Предполагаем, что сборщик настроен на разрешение путей от корня проекта или src/
// import microTemplates from '@/shared/jinja_microtemplates.json'; // Пример для Vue/React CLI
import microTemplates from '../../../../../shared/jinja_microtemplates.json'; // Пример относительного пути

// --- Вспомогательные типы (в идеале импортировать из shared/graphql-types) ---
type AttributeDefinition = {
  type: string;
  default: any;
  description: string;
};
type MicroTemplateDefinition = {
  displayName: string;
  description: string;
  type: 'block' | 'inline';
  attributes: Record<string, AttributeDefinition>;
  template: string;
};
type MicroTemplatesRegistry = Record<string, MicroTemplateDefinition>;

// --- Tiptap Node Extension ---
export const JinjaTag = Node.create({
  name: 'jinjaTag',

  // Определяем как inline, но с atom: true, чтобы работал как единый блок
  group: 'inline',
  inline: true,
  atom: true, // Важно: Обрабатывается как единое целое, неразрывное
  draggable: true, // Позволяет перетаскивать

  addAttributes() {
    return {
      tagName: {
        default: null,
        // Как парсить из HTML
        parseHTML: element => element.getAttribute('data-jinja-tag'),
        // Как рендерить в HTML
        renderHTML: attributes => ({ 'data-jinja-tag': attributes.tagName }),
      },
      params: {
        default: {},
        // Парсим JSON-строку из атрибута
        parseHTML: element => {
          try {
            // Используем || '{}' для случая, если атрибут отсутствует
            return JSON.parse(element.getAttribute('data-jinja-params') || '{}');
          } catch (e) {
            console.error("Error parsing jinja params attribute", element.getAttribute('data-jinja-params'), e);
            return {}; // Возвращаем пустой объект в случае ошибки
          }
        },
        // Рендерим объект параметров обратно в JSON-строку
        renderHTML: attributes => {
          // Не рендерим атрибут, если объект параметров пустой
          if (Object.keys(attributes.params || {}).length === 0) {
            return {};
          }
          return { 'data-jinja-params': JSON.stringify(attributes.params) };
        },
      },
    };
  },

  parseHTML() {
    return [
      {
        // Ищем тег span с нашим data-атрибутом
        tag: 'span[data-jinja-tag]',
      },
    ];
  },

  renderHTML({ node, HTMLAttributes }) {
    // Рендерим внешний span с data-атрибутами.
    // Для atom: true узлов НЕЛЬЗЯ использовать content hole (0).
    // NodeView отвечает за отображение в редакторе.
    // renderHTML отвечает за сериализацию (как будет сохранено).
    return ['span', mergeAttributes(HTMLAttributes, { 'data-drag-handle': '' })]; // Убрали , 0
  },

  addNodeView() {
    // Используем Vanilla JS NodeView, как указано в README
    return ({ node, getPos, editor }) => {
      const dom = document.createElement('span');
      dom.setAttribute('data-drag-handle', ''); // Метка для перетаскивания
      dom.contentEditable = 'false'; // Запрещаем редактирование содержимого
      // Стили для визуального отображения
      dom.style.backgroundColor = '#f0f0f0'; // Светло-серый фон
      dom.style.padding = '0.2em 0.5em';
      dom.style.borderRadius = '4px';
      dom.style.fontFamily = 'monospace';
      dom.style.border = '1px solid #ccc';
      dom.style.display = 'inline-block'; // Чтобы фон и рамка применялись корректно
      dom.style.whiteSpace = 'nowrap'; // Предотвращаем перенос строки внутри тега
      dom.style.cursor = 'default'; // Стандартный курсор
      dom.classList.add('jinja-tag-node'); // Класс для возможной CSS-стилизации

      const tagName = node.attrs.tagName as string;
      const params = node.attrs.params as Record<string, any> || {}; // Убедимся, что params это объект

      // Получаем описание из реестра
      // Примечание: Убедитесь, что microTemplates импортирован корректно
      const registry = microTemplates as MicroTemplatesRegistry;
      const definition = registry[tagName];

      // Формируем строку параметров для отображения
      const displayParams = Object.entries(params)
        .map(([key, value]) => `${key}=${JSON.stringify(value)}`) // Отображаем параметры как key="value"
        .join(', ');

      // Устанавливаем текстовое содержимое NodeView
      dom.textContent = `{${definition?.displayName || tagName}${displayParams ? ': ' + displayParams : ''}}`;

      // Возвращаем DOM-узел и методы управления
      return {
        dom,
        // update: (updatedNode) => { ... } // Можно добавить логику обновления
        // destroy: () => { ... } // Можно добавить логику очистки
      };
    };
  },

  // Команда для вставки нашего узла
  addCommands() {
    return {
      insertJinjaTag: (options) => ({ commands }) => {
        const { name, params = {} } = options; // Ожидаем имя тега и объект параметров

        // Проверяем, есть ли такой тег в реестре
        const registry = microTemplates as MicroTemplatesRegistry;
        if (!registry[name]) {
            console.warn(`[JinjaTag] Попытка вставить неизвестный тег: "${name}"`);
            return false; // Прерываем команду, если тег не найден
        }

        const definition = registry[name];
        const defaultParams: Record<string, any> = {};

        // Собираем дефолтные параметры из реестра
        if (definition.attributes) {
          for (const attrName in definition.attributes) {
            if (definition.attributes[attrName].default !== undefined) {
              defaultParams[attrName] = definition.attributes[attrName].default;
            }
          }
        }

        const finalParams = { ...defaultParams, ...params };

        // Удаляем параметры, которых нет в реестре (опционально, для чистоты)
        for (const paramName in finalParams) {
           if (!(definition.attributes && definition.attributes[paramName])) {
               // delete finalParams[paramName]; // Раскомментируйте, если нужно удалять лишние параметры
           }
        }


        // Вставляем контент с типом нашего узла и атрибутами
        return commands.insertContent({
          type: this.name, // Имя нашего Node ('jinjaTag')
          attrs: {
            tagName: name, // Имя конкретного микрошаблона (e.g., 'menu')
            params: finalParams, // Параметры для этого экземпляра (с дефолтами)
          },
        });
      },
    };
  },

  // Добавляем возможность расширить типизацию редактора (для TypeScript)
  // Это позволит использовать editor.commands.insertJinjaTag(...) с автодополнением
  addGlobalAttributes() {
    return [
        {
            types: [], // Не добавляем глобальные атрибуты к другим типам
            attributes: {
                // Это поле не используется напрямую, но нужно для TS
                insertJinjaTag: {
                    default: null,
                    rendered: false,
                }
            }
        }
    ]
  }

});

// Расширение для TypeScript, чтобы команда была типизирована
declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    jinjaTag: {
      /**
       * Вставляет Jinja2 микрошаблон
       * @param options Опции для вставки: имя тега и параметры.
       * @example editor.commands.insertJinjaTag({ name: 'menu', params: { type: 'secondary' } })
       */
      insertJinjaTag: (options: { name: string, params?: Record<string, any> }) => ReturnType;
    }
  }
} 