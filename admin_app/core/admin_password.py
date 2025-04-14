import os
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from passlib.hash import bcrypt

ADMIN_SETTINGS_COLLECTION = "admin_settings"
ADMIN_SETTINGS_ID = "admin"

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

async def get_admin_password_hash(db: AsyncIOMotorDatabase) -> Optional[str]:
    """
    Get the admin password hash from the database. Returns None if not set.
    """
    doc = await db[ADMIN_SETTINGS_COLLECTION].find_one({"_id": ADMIN_SETTINGS_ID})
    if doc and "password_hash" in doc:
        return doc["password_hash"]
    return None

async def set_admin_password_hash(db: AsyncIOMotorDatabase, password_hash: str) -> None:
    """
    Set (or update) the admin password hash in the database.
    """
    await db[ADMIN_SETTINGS_COLLECTION].update_one(
        {"_id": ADMIN_SETTINGS_ID},
        {"$set": {"password_hash": password_hash}},
        upsert=True
    )

async def delete_admin_password_hash(db: AsyncIOMotorDatabase) -> None:
    """
    Remove the admin password hash from the database (reset to env password).
    """
    await db[ADMIN_SETTINGS_COLLECTION].delete_one({"_id": ADMIN_SETTINGS_ID})

async def verify_admin_password(db: AsyncIOMotorDatabase, password: str) -> bool:
    """
    Verify the admin password: first check hash in DB, fallback to env password.
    """
    hash_in_db = await get_admin_password_hash(db)
    if hash_in_db:
        return bcrypt.verify(password, hash_in_db)
    return password == ADMIN_PASSWORD

async def change_admin_password(db: AsyncIOMotorDatabase, current_password: str, new_password: str) -> bool:
    """
    Change admin password: verify current, then set new hash. Returns True if changed.
    """
    if not await verify_admin_password(db, current_password):
        return False
    new_hash = bcrypt.hash(new_password)
    await set_admin_password_hash(db, new_hash)
    return True 