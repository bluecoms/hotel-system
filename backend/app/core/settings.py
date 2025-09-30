# app/core/settings.py
from functools import lru_cache
from pydantic_settings import BaseSettings

class _Settings(BaseSettings):
    APP_ENV: str = "dev"
    APP_DB_URL: str = "sqlite:////volume1/web/hotel-system/backend/hotel.db"
    INTERNAL_API_TOKEN: str = "dev-admin-token"

    class Config:
        env_file = "/volume1/web/hotel-system/backend/.env"
        env_file_encoding = "utf-8"

@lru_cache
def get_settings() -> _Settings:
    return _Settings()

settings = get_settings()
