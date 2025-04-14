"""
admin_app/routes/articles.py

CRUD-роуты для статей блога (FastAPI + MongoDB).
Назначение: реализует эндпоинты для создания, получения, обновления и удаления статей.
Архитектурные решения:
- Асинхронный доступ к MongoDB через motor.
- Использование Pydantic-моделей из admin_app/models.py.
- Пагинация реализована через параметры limit/offset.
- Версионирование: при обновлении статья сохраняет предыдущую версию в поле versions.
- Все операции требуют базовой авторизации (будет добавлено позже).
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query, Request
from typing import List, Optional, Any
from datetime import datetime
from bson import ObjectId
from admin_app.models import ArticleCreate, ArticleRead, ArticleUpdate, ArticleInDB

router = APIRouter(prefix="/admin/articles", tags=["articles"])

def to_article_read(doc: dict) -> ArticleRead:
    """
    Преобразует MongoDB-документ в ArticleRead.
    """
    return ArticleRead(
        id=str(doc["_id"]),
        title=doc["title"],
        slug=doc["slug"],
        content_md=doc["content_md"],
        status=doc.get("status", "draft"),
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
        versions=doc.get("versions", [])
    )

@router.post(
    "",
    response_model=ArticleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новую статью"
)
async def create_article(
    article: ArticleCreate,
    request: Request
):
    """
    Создание новой статьи.
    Статус по умолчанию — draft.
    """
    db = request.app.state.mongo_db
    now = datetime.utcnow()
    doc = article.dict()
    doc["created_at"] = now
    doc["updated_at"] = now
    doc["versions"] = []
    result = await db.articles.insert_one(doc)
    doc["_id"] = result.inserted_id
    return to_article_read(doc)

@router.get(
    "",
    response_model=dict,
    summary="Получить список статей с пагинацией"
)
async def list_articles(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Получение списка статей с пагинацией.
    """
    db = request.app.state.mongo_db
    cursor = db.articles.find().skip(offset).limit(limit).sort("created_at", -1)
    items = [to_article_read(doc) async for doc in cursor]
    total = await db.articles.count_documents({})
    return {"items": items, "total": total, "limit": limit, "offset": offset}

@router.get(
    "/{article_id}",
    response_model=ArticleRead,
    summary="Получить статью по id"
)
async def get_article(
    article_id: str,
    request: Request
):
    """
    Получение статьи по id.
    """
    db = request.app.state.mongo_db
    try:
        oid = ObjectId(article_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Некорректный id")
    doc = await db.articles.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Статья не найдена")
    return to_article_read(doc)

@router.put(
    "/{article_id}",
    response_model=ArticleRead,
    summary="Обновить статью по id"
)
async def update_article(
    article_id: str,
    article: ArticleUpdate,
    request: Request
):
    """
    Обновление статьи по id.
    Предыдущее состояние сохраняется в versions.
    """
    db = request.app.state.mongo_db
    try:
        oid = ObjectId(article_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Некорректный id")
    doc = await db.articles.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Статья не найдена")
    prev_version = {
        "title": doc["title"],
        "slug": doc["slug"],
        "content_md": doc["content_md"],
        "status": doc.get("status", "draft"),
        "updated_at": doc["updated_at"]
    }
    update_data = {k: v for k, v in article.dict(exclude_unset=True).items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    update = {
        "$set": update_data,
        "$push": {"versions": prev_version}
    }
    await db.articles.update_one({"_id": oid}, update)
    doc = await db.articles.find_one({"_id": oid})
    return to_article_read(doc)

@router.delete(
    "/{article_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить статью по id"
)
async def delete_article(
    article_id: str,
    request: Request
):
    """
    Удаление статьи по id.
    """
    db = request.app.state.mongo_db
    try:
        oid = ObjectId(article_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Некорректный id")
    result = await db.articles.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Статья не найдена")
    return
