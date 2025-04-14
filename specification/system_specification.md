# Спецификация системы: Статический генератор сайта с админкой

## Архитектура

- **Admin Panel (FastAPI)**: Управление статьями (Markdown), хранение в MongoDB, загрузка изображений в MinIO.
- **Static Site Generator (Python script)**: Получение опубликованных статей из MongoDB, генерация HTML через Jinja2, вывод в static_output.
- **Caddy (Web Server)**: Раздача статики, проксирование /admin на FastAPI, /images на MinIO.
- **MinIO (S3)**: Хранение и отдача изображений.
- **MongoDB**: Хранение статей (title, slug, content_md, status, versions, created_at, updated_at).

## Директории

- admin_app/ — FastAPI backend
- generator/ — генератор статики
- infrastructure/ — docker-compose, Caddyfile и пр.
- static_output/ — результат генерации
- prompt/ — фиксация пользовательских запросов
- specification/ — спецификации системы и изменений
- testing/ — тесты

## Переменные окружения

- MONGO_URI, MONGO_DATABASE, MINIO_ROOT_USER, MINIO_ROOT_PASSWORD, MINIO_ENDPOINT_URL, MINIO_BUCKET_NAME, ADMIN_APP_PORT, CADDY_DOMAIN_NAME и др.

## Основные workflow

1. Создание/редактирование статьи в админке.
2. Загрузка изображений через админку в MinIO.
3. Публикация статьи (статус published).
4. Генерация статики скриптом generator/generate.py.
5. Раздача сайта и изображений через Caddy.

## Новые артефакты и изменения (14.04.2025)

- Добавлен тест подключения к MongoDB: testing/test_mongodb_connection.py (асинхронный, motor, использует .env).
- Введён файл admin_app/version.py для хранения версии backend-админки.
- В admin_app/main.py реализовано асинхронное подключение к MongoDB через motor с подробной документацией архитектурных решений (инициализация и закрытие клиента, использование app.state).
- Реализованы Pydantic-модели для статей: ArticleCreate, ArticleRead, ArticleUpdate, ArticleInDB (admin_app/models.py).
- Реализованы CRUD-роуты для статей (admin_app/routes/articles.py), подключены к FastAPI (admin_app/main.py).
- Создан тест для CRUD-операций со статьями: testing/test_articles_crud.py.

## Текущий этап

Следующий шаг — реализовать подключение к MinIO, эндпоинт для загрузки изображений и добавить базовую аутентификацию/авторизацию.
