# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/models/audit.py
# Version   : 2025-10-31 · v3.6 (SSOT Stable)
# Purpose   : 감사 로그 모델 (AuditLog)
# ----------------------------------------------------------------------------
# 목적:
#   • 시스템 내 주요 행위(생성, 수정, 삭제, 승인 등)를 기록하는 감사 로그 테이블
#   • SSOT 원칙에 따라 append-only 구조로 동작
# ----------------------------------------------------------------------------
# 특징:
#   ✅ 순환참조 없음 (MergeBatch 등과 완전 분리)
#   ✅ actor/action/target/meta_json 구조 통일
#   ✅ created_at / updated_at 추가 (타임라인 정합성 확보)
# ----------------------------------------------------------------------------
# 사용 예:
#   from app.core.audit import write_audit
#   write_audit(db, actor="admin", action="user.create", target="user=5")
# ============================================================================

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.db.base_class import Base


class AuditLog(Base):
    """감사 로그 (append-only)"""
    __tablename__ = "audit_logs"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    ts = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    actor = Column(String(64), nullable=False, index=True)   # 실행 주체
    action = Column(String(128), nullable=False, index=True) # 수행된 액션 코드
    target = Column(String(255), nullable=False, index=True) # 대상 식별자 (예: user_id=5)
    meta_json = Column(Text, nullable=True)                  # 부가 정보(JSON 직렬화)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} actor={self.actor} action={self.action} target={self.target}>"
