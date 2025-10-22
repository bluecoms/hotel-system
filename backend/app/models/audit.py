# app/models/audit.py
# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from app.db.base_class import Base

# ──────────────────────────────────────────────────────────────
# 기존 감사 로그 (AuditLog만 유지)
# ──────────────────────────────────────────────────────────────
class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    ts = Column(DateTime, default=datetime.utcnow, nullable=False)
    actor = Column(String, nullable=False)
    action = Column(String, nullable=False)
    target = Column(String, nullable=False)
    meta_json = Column(Text)
