from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    MINIO_ENDPOINT_URL: str = "http://minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_NAME: str = "images"
    PUBLIC_BASE_URL: str = os.getenv("PUBLIC_BASE_URL", "http://localhost:8080")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings() 