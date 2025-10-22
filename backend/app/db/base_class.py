# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/db/base_class.py
# Version   : 2025-10-31 · v3.6 (SSOT Stable)
# Purpose   : SQLAlchemy Declarative Base 정의
# ----------------------------------------------------------------------------
# 목적:
#   • 모든 ORM 모델이 상속하는 공용 Base 클래스 선언
#   • SQLAlchemy 2.x DeclarativeBase 사용 (v1.x의 declarative_base() 대체)
#   • Alembic, ORM, 모델 간 메타데이터 일원화(SSOT 구조)
# ----------------------------------------------------------------------------
# 사용 예:
#   from app.db.base_class import Base
#   class User(Base):
#       __tablename__ = "users"
#       id = mapped_column(Integer, primary_key=True)
# ----------------------------------------------------------------------------
# 주의:
#   ✅ Base 클래스는 단일 정의만 존재해야 함
#   ✅ 중복 Base 정의 시 Alembic 마이그레이션 충돌 발생
#   ✅ Base.metadata 는 app/db/base.py 에서 models import 로 등록됨
# ============================================================================

from sqlalchemy.orm import DeclarativeBase

# ─────────────────────────────────────────────
# Declarative Base (SSOT 단일 소스)
# ─────────────────────────────────────────────
class Base(DeclarativeBase):
    """모든 ORM 모델의 공용 Declarative Base"""
    pass
