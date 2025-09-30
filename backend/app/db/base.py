# app/db/base.py
from .base_class import Base

# 모델들을 메타데이터에 등록하기 위한 '사이드이펙트 import'
from app import models  # noqa: F401

__all__ = ["Base"]
