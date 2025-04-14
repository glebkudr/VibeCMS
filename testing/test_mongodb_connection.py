"""
Тест подключения к MongoDB через motor.
- Проверяет возможность установить соединение и получить список баз данных.
- Использует переменные окружения из .env (MONGO_URI).
- Для запуска: python testing/test_mongodb_connection.py
"""

import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Загрузка переменных окружения из .env, если есть
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/mydatabase")

async def test_connection():
    """
    Проверяет подключение к MongoDB и выводит список баз данных.
    """
    client = AsyncIOMotorClient(MONGO_URI)
    try:
        dbs = await client.list_database_names()
        print("MongoDB доступен. Список баз данных:", dbs)
        print("Тест подключения к MongoDB: УСПЕХ")
    except Exception as e:
        print("Ошибка подключения к MongoDB:", e)
        print("Тест подключения к MongoDB: ОШИБКА")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(test_connection())
