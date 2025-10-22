# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/core/settings.py
# Version   : 2025.11-01 · v3.7 (SSOT Final Stable · DB Auto-Safe)
# Purpose   : Hotel Admin — Global Settings (FastAPI · Pydantic v2)
# ----------------------------------------------------------------------------
# 목적:
#   • FastAPI 및 모든 서브모듈(app/*)이 공통 참조하는 설정 단일화
#   • APP_ENV(dev/prod), DB URL, TOKEN 등 환경 변수를 중앙 관리
#   • .env 자동 감지 + SQLite 경로 자동 생성 (운영/개발 모두 호환)
# ----------------------------------------------------------------------------
# 개선사항 (v3.7)
#   ✅ APP_ENV / DEBUG 자동 감지 (미설정 시 안전 기본값)
#   ✅ DB URL 자동 검증 + SQLite 경로 자동 생성
#   ✅ INTERNAL_API_TOKEN 기본값(dev-admin-token) 보정
#   ✅ env_file 누락 시에도 런타임 오류 방지
#   ✅ is_dev() / db_exists() 헬퍼 제공 (core.auth, db.session 등에서 활용)
# ----------------------------------------------------------------------------
# 사용 예시:
#   from app.core.settings import settings
#   print(settings.APP_ENV, settings.APP_DB_URL)
# ----------------------------------------------------------------------------
# FastAPI 통합 구조:
#   app/
#     ├── core/
#     │    └── settings.py   ← 현재 파일 (SSOT 설정)
#     ├── db/
#     │    └── session.py    ← settings.APP_DB_URL 참조
#     ├── routers/
#     │    └── *.py          ← settings.is_dev(), settings.INTERNAL_API_TOKEN 사용
# ============================================================================
import os
from functools import lru_cache
from pydantic_settings import BaseSettings


# ============================================================================
# 1️⃣ Settings 클래스 정의 (Pydantic v2 기반)
# ============================================================================
class _Settings(BaseSettings):
    # ─────────────────────────────────────────────
    # 기본 환경 (APP_ENV / DEBUG / TOKEN)
    # ─────────────────────────────────────────────
    APP_ENV: str = os.getenv("APP_ENV", "dev").lower()  # dev | prod
    DEBUG: bool = bool(str(os.getenv("DEBUG", "1")).lower() in {"1", "true", "yes"})
    INTERNAL_API_TOKEN: str = os.getenv("INTERNAL_API_TOKEN", "dev-admin-token")

    # ─────────────────────────────────────────────
    # DB 및 파일 경로
    # ─────────────────────────────────────────────
    APP_DB_URL: str = os.getenv(
        "APP_DB_URL",
        "sqlite:////volume1/web/hotel-system/backend/hotel.db"
    )

    UPLOAD_ROOT: str = os.getenv(
        "UPLOAD_ROOT",
        "/volume1/web/hotel-system/backend/_uploads"
    )

    # ─────────────────────────────────────────────
    # 권한 시스템 글로벌 설정
    # ─────────────────────────────────────────────
    DEFAULT_ROLE: str = os.getenv("DEFAULT_ROLE", "ADMIN")
    ROLE_ACCESS_CACHE_TTL: int = int(os.getenv("ROLE_ACCESS_CACHE_TTL", "300"))

    # ─────────────────────────────────────────────
    # .env 파일 감지 (없어도 무시)
    # ─────────────────────────────────────────────
    class Config:
        env_file = os.getenv("ENV_FILE", "/volume1/web/hotel-system/backend/.env")
        env_file_encoding = "utf-8"

    # ─────────────────────────────────────────────
    # 헬퍼 메서드
    # ─────────────────────────────────────────────
    def is_dev(self) -> bool:
        """
        개발 환경 여부 반환.
        DEBUG=True 또는 APP_ENV in {dev, development, local} 이면 True
        """
        return self.DEBUG or self.APP_ENV in {"dev", "development", "local"}

    def db_exists(self) -> bool:
        """
        현재 DB 경로가 존재하는지 검사 (SQLite만 대상).
        PostgreSQL 등 외부 DB는 항상 True 반환.
        """
        if self.APP_DB_URL.startswith("sqlite:///"):
            path = self.APP_DB_URL.replace("sqlite:///", "")
            return os.path.exists(path)
        return True


# ============================================================================
# 2️⃣ 전역 설정 인스턴스 (Singleton + Lazy Cache)
# ============================================================================
@lru_cache
def get_settings() -> _Settings:
    """
    전역 settings 객체를 반환.
    FastAPI, Alembic, Router 등에서 공용 사용.
    """
    s = _Settings()

    # INTERNAL_API_TOKEN 누락 시 자동 보정 (dev 환경 전용)
    if not s.INTERNAL_API_TOKEN:
        s.INTERNAL_API_TOKEN = "dev-admin-token"

    # SQLite 경로 자동 생성 (파일/디렉터리 모두 보장)
    if s.APP_DB_URL.startswith("sqlite:///"):
        db_path = s.APP_DB_URL.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        try:
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
            if not os.path.exists(db_path):
                open(db_path, "a").close()
        except Exception as e:
            print(f"[Settings] ⚠️ SQLite DB 경로 생성 실패 → {e}")

    return s


# ============================================================================
# 3️⃣ settings 전역 객체 (SSOT)
# ----------------------------------------------------------------------------
# import 시 즉시 settings 로 접근 가능:
#   from app.core.settings import settings
# ============================================================================
settings = get_settings()


# ============================================================================
# 4️⃣ (선택) 단독 실행 테스트
# ============================================================================
if __name__ == "__main__":
    print(" ENV:", settings.APP_ENV)
    print(" DEBUG:", settings.DEBUG)
    print("️ TOKEN:", settings.INTERNAL_API_TOKEN)
    print("️ DB URL:", settings.APP_DB_URL)
    print(" UPLOAD ROOT:", settings.UPLOAD_ROOT)
    print(" DB Exists:", settings.db_exists())
