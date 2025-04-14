from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MINIO_ENDPOINT_URL: str = "http://minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_NAME: str = "images"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings() 