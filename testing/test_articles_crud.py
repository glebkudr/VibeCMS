"""
testing/test_articles_crud.py

Тесты для CRUD-операций со статьями через API FastAPI.
Назначение: гарантировать корректную работу эндпоинтов /admin/articles (создание, получение, обновление, удаление).
Архитектурные решения:
- Используется httpx.AsyncClient для асинхронного тестирования FastAPI.
- Тесты не зависят от реального фронтенда, работают через API.
- Для изоляции тестов рекомендуется использовать отдельную тестовую БД или мок-объекты (в данной версии используется основная БД, требуется доработка для полной изоляции).
"""

import pytest
from httpx import AsyncClient
from admin_app.main import app

@pytest.mark.asyncio
async def test_crud_article():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 1. Создание статьи
        article_data = {
            "title": "Тестовая статья",
            "slug": "test-article",
            "content_md": "# Markdown",
            "status": "draft"
        }
        resp = await ac.post("/admin/articles", json=article_data)
        assert resp.status_code == 201
        created = resp.json()
        article_id = created["id"]

        # 2. Получение списка статей
        resp = await ac.get("/admin/articles")
        assert resp.status_code == 200
        assert any(a["id"] == article_id for a in resp.json()["items"])

        # 3. Получение конкретной статьи
        resp = await ac.get(f"/admin/articles/{article_id}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Тестовая статья"

        # 4. Обновление статьи
        update_data = {"title": "Обновлённая статья", "status": "published"}
        resp = await ac.put(f"/admin/articles/{article_id}", json=update_data)
        assert resp.status_code == 200
        assert resp.json()["title"] == "Обновлённая статья"
        assert resp.json()["status"] == "published"

        # 5. Удаление статьи
        resp = await ac.delete(f"/admin/articles/{article_id}")
        assert resp.status_code == 204

        # 6. Проверка, что статья удалена
        resp = await ac.get(f"/admin/articles/{article_id}")
        assert resp.status_code == 404
