# app/routers/merge.py
# -*- coding: utf-8 -*-
# version: 2025-10-12 Phase 3 Final
"""
Merge API (Phase 3)
──────────────────────────────────────────────
- /api/merge/batches           : 배치 목록 조회 (필터/페이지네이션)
- /api/merge/logs/{batch_id}   : 특정 배치의 변경 로그 조회
- ADMIN / SUPERADMIN 접근 권한 요구
- ISO8601 문자열 직렬화 (created_at, completed_at)
"""
from __future__ import annotations

import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder

from app.db.session import get_db
from app.models.merge import MergeBatch, MergeChangeLog
from app.schemas.merge import (
    MergeBatchBase,
    MergeChangeLogBase,
    MergeBatchWithChanges,
)
from app.core.auth import require_roles, require_token_local

log = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/merge",
    tags=["merge"],
    dependencies=[
        Depends(require_token_local),              # ⬅ 내부 토큰 허용
        Depends(require_roles(["ADMIN","SUPERADMIN"])),  # ⬅ 롤 체크
    ],
)

# ──────────────────────────────────────────────────────────────
# GET /api/merge/batches — 배치 목록
# ──────────────────────────────────────────────────────────────
@router.get("/batches", response_model=List[MergeBatchBase])
def list_merge_batches(
    db: Session = Depends(get_db),
    dataset: Optional[str] = Query(None, description="데이터셋 (예: rooms_status)"),
    property_code: Optional[str] = Query(None, description="호텔 코드 (예: MOP)"),
    status: Optional[str] = Query(None, description="PENDING / DONE / FAILED"),
    mode: Optional[str] = Query(None, description="append / snapshot 등"),
    date_from: Optional[str] = Query(None, description="YYYY-MM-DD (created_at 하한)"),
    date_to: Optional[str] = Query(None, description="YYYY-MM-DD (created_at 상한, 당일 23:59:59)"),
    limit: int = Query(100, ge=1, le=200, description="최대 200"),
    offset: int = Query(0, ge=0, description="페이지 오프셋"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="정렬 방향 (asc/desc)"),
):
    """
    병합 배치 목록 조회 (필터/페이지네이션)
    created_at/완료일 기준 정렬 및 ISO8601 직렬화 포함
    """
    q = db.query(MergeBatch)

    # 필터 적용
    if dataset:
        q = q.filter(MergeBatch.dataset == dataset)
    if property_code:
        q = q.filter(MergeBatch.property_code == property_code)
    if status:
        q = q.filter(MergeBatch.status == status)
    if mode:
        q = q.filter(MergeBatch.mode == mode)

    # 날짜 범위 필터
    conds = []
    try:
        if date_from:
            dt_from = datetime.strptime(date_from, "%Y-%m-%d")
            conds.append(MergeBatch.created_at >= dt_from)
        if date_to:
            dt_to = datetime.strptime(date_to, "%Y-%m-%d")
            dt_to = dt_to.replace(hour=23, minute=59, second=59, microsecond=999999)
            conds.append(MergeBatch.created_at <= dt_to)
    except Exception as e:
        log.warning(f"[MERGE] invalid date filter: {e}")
    if conds:
        q = q.filter(and_(*conds))

    # 정렬
    if order.lower() == "asc":
        q = q.order_by(MergeBatch.created_at.asc(), MergeBatch.id.asc())
    else:
        q = q.order_by(MergeBatch.created_at.desc(), MergeBatch.id.desc())

    rows = q.offset(offset).limit(limit).all()

    # datetime → ISO 문자열 직렬화
    encoded = jsonable_encoder(rows)
    for r in encoded:
        if r.get("created_at"):
            r["created_at"] = datetime.fromisoformat(str(r["created_at"])).isoformat()
        if r.get("completed_at"):
            try:
                r["completed_at"] = datetime.fromisoformat(str(r["completed_at"])).isoformat()
            except Exception:
                pass

    return encoded


# ──────────────────────────────────────────────────────────────
# GET /api/merge/logs/{batch_id} — 변경 로그 + 배치 메타
# ──────────────────────────────────────────────────────────────
@router.get("/logs/{batch_id}", response_model=MergeBatchWithChanges)
def get_merge_logs(
    batch_id: int,
    db: Session = Depends(get_db),
    limit: int = Query(1000, ge=1, le=5000, description="로그 최대 5000"),
    offset: int = Query(0, ge=0),
):
    """
    특정 배치의 MergeChangeLog 목록을 배치 메타와 함께 반환
    (datetime → ISO8601 문자열 변환 포함)
    """
    batch = db.query(MergeBatch).filter(MergeBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    changes = (
        db.query(MergeChangeLog)
        .filter(MergeChangeLog.batch_id == batch_id)
        .order_by(MergeChangeLog.id.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    # 직렬화 (datetime → str)
    batch_data = jsonable_encoder(batch)
    changes_data = jsonable_encoder(changes)

    for c in changes_data:
        if c.get("created_at"):
            try:
                c["created_at"] = datetime.fromisoformat(str(c["created_at"])).isoformat()
            except Exception:
                pass

    if batch_data.get("created_at"):
        batch_data["created_at"] = datetime.fromisoformat(str(batch_data["created_at"])).isoformat()
    if batch_data.get("completed_at"):
        try:
            batch_data["completed_at"] = datetime.fromisoformat(str(batch_data["completed_at"])).isoformat()
        except Exception:
            pass

    batch_obj = MergeBatchWithChanges(**batch_data, changes=changes_data)
    log.info(f"[MERGE] fetched logs batch_id={batch_id} changes={len(changes_data)}")
    return batch_obj


__all__ = ["router", "list_merge_batches", "get_merge_logs"]
