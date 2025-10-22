# app/core/settings.py
# -*- coding: utf-8 -*-
from functools import lru_cache
from pydantic_settings import BaseSettings

class _Settings(BaseSettings):
    APP_ENV: str = "dev"   # "dev" | "prod"
    DEBUG: bool = True     # DEV 판별을 위한 추가 필드 (auth._is_dev_env 에서 사용)
    APP_DB_URL: str = "sqlite:////volume1/web/hotel-system/backend/hotel.db"
    INTERNAL_API_TOKEN: str = "dev-admin-token"

    # 업로드 루트 경로 (공통)
    UPLOAD_ROOT: str = "/volume1/web/hotel-system/backend/_uploads"

    # 권한 시스템 관련 글로벌 설정 (선택)
    DEFAULT_ROLE: str = "ADMIN"          # 토큰 미지정 시 기본 역할
    ROLE_ACCESS_CACHE_TTL: int = 300     # 초 단위 (권한 캐싱 시 사용 가능)

    class Config:
        env_file = "/volume1/web/hotel-system/backend/.env"
        env_file_encoding = "utf-8"

@lru_cache
def get_settings() -> _Settings:
    return _Settings()

settings = get_settings()
