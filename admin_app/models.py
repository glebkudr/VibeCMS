"""
admin_app/models.py

Pydantic-модели для статей блога.
Назначение: определяют структуру данных для CRUD-операций с коллекцией статей в MongoDB.
Архитектурные решения:
- Используются отдельные модели для создания, чтения, обновления и внутреннего хранения статьи.
- Версионирование реализовано через поле versions (список словарей с историей изменений).
- Для MongoDB id используется строковое поле id (ObjectId в виде строки).
- created_at и updated_at — ISO8601-строки (FastAPI автоматически сериализует datetime).
- status: draft/published/archived (по умолчанию draft).
"""

from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime

class ArticleBase(BaseModel):
    """
    Базовая модель статьи.
    Используется для наследования в других моделях.
    """
    title: str = Field(..., description="Заголовок статьи")
    slug: str = Field(..., description="URL-идентификатор (slug) статьи")
    content_md: str = Field(..., description="Markdown-контент статьи")
    status: str = Field("draft", description="Статус статьи: draft/published/archived")

class ArticleCreate(ArticleBase):
    """
    Модель для создания новой статьи.
    Все поля обязательны, кроме status (по умолчанию draft).
    """
    pass

class ArticleUpdate(BaseModel):
    """
    Модель для обновления статьи.
    Все поля опциональны, чтобы поддерживать частичное обновление.
    """
    title: Optional[str] = Field(None, description="Заголовок статьи")
    slug: Optional[str] = Field(None, description="URL-идентификатор (slug) статьи")
    content_md: Optional[str] = Field(None, description="Markdown-контент статьи")
    status: Optional[str] = Field(None, description="Статус статьи: draft/published/archived")

class ArticleRead(ArticleBase):
    """
    Модель для чтения статьи (ответ клиенту).
    Содержит служебные поля id, created_at, updated_at, versions.
    """
    id: str = Field(..., description="ObjectId статьи в виде строки")
    created_at: datetime = Field(..., description="Дата создания (ISO8601)")
    updated_at: datetime = Field(..., description="Дата последнего обновления (ISO8601)")
    versions: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="История изменений статьи")

class ArticleInDB(ArticleRead):
    """
    Модель для внутреннего хранения в базе данных.
    Может содержать дополнительные служебные поля.
    """
    # Здесь можно добавить внутренние поля, если потребуется.
    pass
