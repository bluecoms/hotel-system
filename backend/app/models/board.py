# app/models/board.py
# -*- coding: utf-8 -*-
"""
Shim module: 과거 import 호환용.
여기서는 어떤 SQLAlchemy 테이블도 선언하지 않습니다.
모든 모델은 app.models.closing 한 곳에서만 정의합니다.
"""
from app.models.closing import ClosingDay, UploadSession, UploadedFile

__all__ = ["ClosingDay", "UploadSession", "UploadedFile"]
