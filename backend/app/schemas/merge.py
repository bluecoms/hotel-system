# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/schemas/merge.py
# Version   : 2025.10-30 · v3.5 (SSOT Final · Banking/OTA Enhanced)
# Purpose   : Hotel Admin — Merge Schemas (Batch / ChangeLog / Planner)
# ----------------------------------------------------------------------------
# 목적:
#   • Alembic/ORM: merge_batches, merge_changelog 구조와 1:1 매핑
#   • Planner / DryRun / Execute 응답 스키마 제공
#   • Pydantic v2 호환 (from_attributes=True)
# ----------------------------------------------------------------------------
# 변경 로그:
#   v3.5 (2025-10-30)
#     ✅ MergeBatchBase: source_kind / session_id / version_no 필드 추가
#     ✅ mode 기본값 "snapshot", missing_policy "soft_delete" 기본값 명시
#     ✅ Pydantic v2 ConfigDict 적용
# ============================================================================
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# 1️⃣ MergeChangeLog (변경 로그)
# ----------------------------------------------------------------------------
class MergeChangeLogSchema(BaseModel):
    id: int
    batch_id: int
    dataset: Optional[str] = None
    property_code: Optional[str] = None
    business_date: Optional[str] = None
    key_hash: Optional[str] = None
    record_hash: Optional[str] = None
    action: Optional[str] = None              # INSERT / UPSERT / DELETE / NOOP
    payload: Optional[dict] = None
    reason: Optional[str] = None
    created_at: Optional[str] = None          # ISO8601 문자열 직렬화 (라이터에서 처리)

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# 2️⃣ MergeBatch (배치 메타)
# ----------------------------------------------------------------------------
class MergeBatchBase(BaseModel):
    id: Optional[int] = None
    dataset: str
    property_code: str
    business_date: str
    file_name: Optional[str] = None
    record_count: int = 0
    dry_run: bool = False
    status: str = "PENDING"                   # PENDING / DONE / FAILED
    mode: Optional[str] = "snapshot"          # append / snapshot
    missing_policy: Optional[str] = "soft_delete"
    source_kind: Optional[str] = "manual"     # manual / daily / weekly / full ...
    session_id: Optional[str] = None
    version_no: Optional[int] = 1
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# 3️⃣ MergeBatch + 변경내역 포함형
# ----------------------------------------------------------------------------
class MergeBatchWithChanges(BaseModel):
    id: int
    dataset: str
    property_code: str
    business_date: str
    record_count: int
    status: str
    notes: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    changes: List[MergeChangeLogSchema] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# 4️⃣ Planner / DryRun / Execute 응답
# ----------------------------------------------------------------------------
class MergePlanSummary(BaseModel):
    inserted: int = 0
    updated: int = 0
    deleted: int = 0
    noop: int = 0


class MergePlanDetails(BaseModel):
    inserted: List[str] = Field(default_factory=list)
    updated: List[str] = Field(default_factory=list)
    deleted: List[str] = Field(default_factory=list)
    noop: List[str] = Field(default_factory=list)


class MergeDryRunResp(BaseModel):
    ok: bool = True
    dataset: str
    property_code: str
    business_date: str
    summary: MergePlanSummary
    details: MergePlanDetails
    missing_result: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class MergeExecResp(BaseModel):
    ok: bool = True
    batch_id: int
    dataset: str
    property_code: str
    business_date: str
    summary: MergePlanSummary
    completed_at: datetime
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# 5️⃣ Export
# ----------------------------------------------------------------------------
__all__ = [
    "MergeChangeLogSchema",
    "MergeBatchBase",
    "MergeBatchWithChanges",
    "MergePlanSummary",
    "MergePlanDetails",
    "MergeDryRunResp",
    "MergeExecResp",
]

# ============================================================================
# 6️⃣ Aliases (backward compatibility)
# ----------------------------------------------------------------------------
MergeChangeLogBase = MergeChangeLogSchema
# 주의: MergeBatchBase는 동일 명칭 사용 중이므로 재할당 금지
