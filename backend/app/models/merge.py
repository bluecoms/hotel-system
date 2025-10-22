# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/models/merge.py
# Version   : 2025.10-30 · v3.5 (SSOT Final · Banking/OTA Enhanced)
# Purpose   : Hotel Admin — Merge Engine Log Models (Batch / ChangeLog)
# ----------------------------------------------------------------------------
# 목적:
#   • 병합(merge) 엔진의 실행 로그 및 변경 내역을 ORM으로 관리
#   • MergeBatch: 병합 실행 단위 메타데이터
#   • MergeChangeLog: 각 배치 내 개별 레코드 변경 상세 내역
# ----------------------------------------------------------------------------
# 특징:
#   ✅ SSOT Phase 3.5 기준 dataset별 로그 일원화
#   ✅ OTA / Bank Ledger / Expenses 등 다양한 데이터셋 통합 지원
#   ✅ 변경 내역(JSON payload) 저장 및 key_hash 기반 추적
# ----------------------------------------------------------------------------
# 연계:
#   • app/merge_engine/repository.py → MergeAuditRepository
#   • app/merge_engine/audit.py      → record_merge_audit()
#   • app/schemas/merge.py           → MergeBatchBase / MergeChangeLogSchema
#   • Alembic: merge_batches / merge_changelog 테이블 관리
# ----------------------------------------------------------------------------
# 변경 로그:
#   v3.5 (2025-10-30)
#     ✅ mode 기본값 snapshot (엔진 표준 반영)
#     ✅ OTA/BankLedger 등 다중 데이터셋 확장 대응
#     ✅ created_at/completed_at UTC 고정
# ============================================================================
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    JSON,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from app.db.base_class import Base


# ============================================================================
# 1️⃣ MergeBatch — 병합 실행 단위 메타데이터
# ----------------------------------------------------------------------------
class MergeBatch(Base):
    __tablename__ = "merge_batches"
    __table_args__ = (
        Index("ix_merge_batches_dataset_property", "dataset", "property_code"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True)
    dataset = Column(String(50), nullable=False, index=True)           # ex) rooms_status / bank_ledger / ota_orders
    property_code = Column(String(20), nullable=False, index=True)     # ex) MOP
    business_date = Column(String(10), nullable=False, index=True)     # ex) 2025-10-30
    file_name = Column(String(255), nullable=True)
    record_count = Column(Integer, default=0)
    dry_run = Column(String(5), default="0")                           # "1" or "0"
    status = Column(String(20), default="PENDING")                     # PENDING / DONE / FAILED
    mode = Column(String(20), default="snapshot", nullable=False)      # append | snapshot
    missing_policy = Column(String(20), default="soft_delete", nullable=False)
    source_kind = Column(String(30), default="manual", nullable=False) # manual / daily / weekly ...
    session_id = Column(String(50), nullable=True, index=True)
    version_no = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    # 관계 설정 (1:N)
    changes = relationship(
        "MergeChangeLog",
        back_populates="batch",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return (
            f"<MergeBatch id={self.id} dataset={self.dataset} "
            f"property={self.property_code} mode={self.mode} status={self.status}>"
        )


# ============================================================================
# 2️⃣ MergeChangeLog — 병합 변경 상세 내역
# ----------------------------------------------------------------------------
class MergeChangeLog(Base):
    __tablename__ = "merge_changelog"
    __table_args__ = (
        Index("ix_merge_changelog_dataset_property", "dataset", "property_code"),
        Index("ix_merge_changelog_batch_id", "batch_id"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True)
    batch_id = Column(Integer, ForeignKey("merge_batches.id"), nullable=False)
    dataset = Column(String(50), nullable=False)           # ex) bank_ledger, ota_orders
    property_code = Column(String(20), nullable=True)
    business_date = Column(String(20), nullable=True)
    key_hash = Column(String(128), nullable=True)
    record_hash = Column(String(128), nullable=True)
    action = Column(String(20), nullable=False)            # INSERT / UPSERT / DELETE / NOOP
    old_hash = Column(String(128), nullable=True)
    new_hash = Column(String(128), nullable=True)
    payload = Column(JSON, nullable=True)                  # 변경된 payload (최대 1건)
    reason = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 관계 설정
    batch = relationship("MergeBatch", back_populates="changes")

    def __repr__(self):
        return (
            f"<MergeChangeLog id={self.id} dataset={self.dataset} "
            f"action={self.action} key={self.key_hash}>"
        )


# ============================================================================
# 3️⃣ Export 목록
# ----------------------------------------------------------------------------
__all__ = ["MergeBatch", "MergeChangeLog"]
