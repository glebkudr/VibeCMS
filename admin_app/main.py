from fastapi import FastAPI
import os
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager

"""
Архитектурное решение:
- Подключение к MongoDB реализовано через motor (асинхронный драйвер).
- Клиент MongoDB создаётся при запуске приложения и закрывается при завершении.
- Используются переменные окружения для URI и имени БД.
- Клиент экспортируется через app.state для использования в роутерах.
- Все параметры подключения централизованы и документированы.
"""

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/mydatabase")
MONGO_DATABASE = os.getenv("MONGO_DATABASE", "mydatabase")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Контекст жизненного цикла приложения FastAPI.
    Инициализирует и закрывает MongoDB клиент.
    """
    app.state.mongo_client = AsyncIOMotorClient(MONGO_URI)
    app.state.mongo_db = app.state.mongo_client[MONGO_DATABASE]
    print("MongoDB подключение установлено.")
    yield
    app.state.mongo_client.close()
    print("MongoDB подключение закрыто.")

app = FastAPI(
    title="Admin Panel API",
    description="API for managing articles and images.",
    version="0.1.0",
    lifespan=lifespan
)

@app.get("/", tags=["Root"])
async def read_root():
    """ Basic root endpoint to check if the API is running. """
    return {"message": "Admin Panel API is running!"}

"""
Централизованное подключение роутов:
- CRUD-роуты для статей подключаются из admin_app/routes/articles.py.
- Эндпоинты для изображений будут добавлены позже.
"""
from admin_app.routes import articles
app.include_router(articles.router)
# from admin_app.routes import images
# app.include_router(images.router)

# Пример использования клиента в эндпоинтах:
# db = request.app.state.mongo_db

if __name__ == "__main__":
    import uvicorn
    # This part is mainly for local development without docker/uvicorn command
    uvicorn.run(app, host="0.0.0.0", port=8000)
