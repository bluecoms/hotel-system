# -*- coding: utf-8 -*-
# ============================================================================
# File    : app/routers/upload.py
# Version : 2025-10-31 · v3.7 (SSOT Hotfix · UploadedFiles Table Fix)
# Purpose : Hotel Admin — 공통 업로드 라우터 (/api/upload)
# ----------------------------------------------------------------------------
# 변경 요약:
#   ✅ upload_files → uploaded_files 로 테이블명 일원화
#   ✅ UploadedFile.is_active 필드 기반 soft-delete 반영
#   ✅ merge-engine-error 포맷 일관화
#   ✅ SQLAlchemy 2.x 호환 (text + _mapping)
#   ✅ 레거시 FNB 업로드는 deprecated로 유지
# ============================================================================

from __future__ import annotations
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from fastapi import (
    APIRouter, Depends, UploadFile, File, Form, HTTPException, Query,
)
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.auth import require_roles, require_token_local
from app.db.session import get_db
from app.models.closing import UploadedFile
from app.services.merge_service import run_merge_service
from app.core import settings_merge

log = logging.getLogger(__name__)
DATA_ROOT = Path("/volume1/web/hotel-system/backend/_uploads")
DATA_ROOT.mkdir(parents=True, exist_ok=True)

router = APIRouter(prefix="/api/upload", tags=["upload"])


# ──────────────────────────────────────────────
# 내부 유틸
# ──────────────────────────────────────────────
def _filter_by_model_columns(model, data: Dict) -> Dict:
    """모델 컬럼에 존재하는 키만 필터링"""
    cols = list(model.__table__.columns.keys())
    return {k: v for k, v in data.items() if k in cols}


def _next_version_for(db: Session, dataset: str, business_date: str, property_code: str) -> int:
    """dataset/property_code/business_date 기준 version_no 채번"""
    sql = text("""
        SELECT COALESCE(MAX(version_no), 0) AS maxv
        FROM uploaded_files
        WHERE dataset=:dataset AND business_date=:biz AND property_code=:prop
    """)
    row = db.execute(sql, {"dataset": dataset, "biz": business_date, "prop": property_code}).fetchone()
    maxv = int((row._mapping.get("maxv", 0)) if row else 0)
    return maxv + 1


# ──────────────────────────────────────────────
# ✅ 공통 업로드 엔드포인트
# ──────────────────────────────────────────────
@router.post(
    "/{dataset}",
    dependencies=[Depends(require_token_local), Depends(require_roles(["ADMIN", "SUPERADMIN"]))],
)
async def upload_dataset(
    dataset: str,
    business_date: str = Form(...),
    property_code: str = Form("MOP"),
    dry_run: int = Form(1),
    split_by_date: int = Form(0),
    source_kind: str = Form("daily"),
    mode: str = Form(""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """SSOT 기반 업로드 엔드포인트"""
    if not file or not dataset:
        raise HTTPException(status_code=400, detail="file and dataset required")

    form = {
        "business_date": business_date,
        "property_code": property_code,
        "dry_run": dry_run,
        "split_by_date": split_by_date,
        "source_kind": source_kind,
        "mode": mode,
    }
    policy = settings_merge.get_policy(dataset)
    form["_policy"] = policy

    try:
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="uploaded file is empty")

        result = run_merge_service(dataset, form, file_bytes)
        if not isinstance(result, dict):
            raise HTTPException(status_code=500, detail="merge-engine-error: invalid result type")

        if not result.get("ok"):
            raise HTTPException(status_code=500, detail=f"merge-engine-error: {result.get('error')}")

        # ── Dry-run → 저장 X
        if int(dry_run or 0) == 1:
            return result

        # ── 실제 업로드 → 이력 기록
        v = _next_version_for(db, dataset, business_date, property_code)
        logical_path = f"ssot://{dataset}/{property_code}/{business_date}/v{v}"
        rec = UploadedFile(
            **_filter_by_model_columns(
                UploadedFile,
                dict(
                    session_id=None,
                    version_no=v,
                    filename=file.filename or f"{dataset}.csv",
                    size=len(file_bytes),
                    stored_path=logical_path,
                    created_at=datetime.utcnow(),
                    part_key="",
                    dataset=dataset,
                    property_code=property_code,
                    business_date=business_date,
                    upload_type="ssot",
                    remarks="merged",
                    is_active=True,
                ),
            )
        )
        db.add(rec)
        db.commit()
        return result

    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"[UPLOAD] dataset={dataset} failed: {e}")
        raise HTTPException(status_code=500, detail=f"merge-engine-error: {e}")


# ──────────────────────────────────────────────
# ✅ 업로드 이력 조회
# ──────────────────────────────────────────────
@router.get("/versions", dependencies=[Depends(require_token_local)])
def get_upload_versions(
    dataset: str = Query(...),
    business_date: str = Query(...),
    property_code: str = Query(...),
    db: Session = Depends(get_db),
):
    """업로드 이력 조회 (Phase 6 — Canon 기반)"""
    sql = text("""
        SELECT version_no, filename, size, 
               COALESCE(created_at, CURRENT_TIMESTAMP) AS uploaded_at,
               COALESCE(part_key, '') AS part_key,
               COALESCE(is_active, 1) AS is_active
        FROM uploaded_files
        WHERE dataset=:dataset AND business_date=:biz AND property_code=:prop
        ORDER BY version_no DESC, part_key ASC
    """)
    rows = db.execute(sql, {"dataset": dataset, "biz": business_date, "prop": property_code}).fetchall()
    items = [dict(r._mapping) if hasattr(r, "_mapping") else dict(r) for r in rows]
    return {"items": items}
