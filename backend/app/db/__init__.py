# app/db/__init__.py
# 패키지 초기화는 최소화: 모델 import 절대 금지(순환/중복등록 방지)

from .session import db_dep, engine, SessionLocal  # 선택적 re-export

__all__ = ["db_dep", "engine", "SessionLocal"]
