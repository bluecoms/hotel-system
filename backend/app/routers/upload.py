# app/routers/upload.py
# -*- coding: utf-8 -*-
# version: 2025-10-12 Phase 3 Final
"""
Upload Router (Phase 3 Final)
──────────────────────────────────────────────
- SSOT Merge 기반 공통 업로드 엔드포인트
- 모든 dataset(fnb_items, fnb_tenders, rooms_status 등) 통합
- settings_merge 정책 + merge_service 연동
- 에러 포맷: merge-service-error / merge-engine-error 표준화
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    Form,
    HTTPException,
    Query,
)
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth import require_roles, require_token_local
from app.db.session import get_db
from app.models.closing import UploadedFile
from app.services.merge_service import run_merge_service

# Phase 3: SSOT 정책 기반
from app.core import settings_merge

log = logging.getLogger(__name__)

# 업로드 저장 루트 (레거시 fnb_sales에서만 실파일 저장)
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


def _head_rows(text_: str, n: int = 5) -> List[str]:
    """미리보기용 CSV 상단 5행"""
    rows = text_.splitlines()
    return rows[: min(len(rows), n)]


def _next_version_for(db: Session, dataset: str, business_date: str, property_code: str) -> int:
    """
    session_id 없이 dataset/property_code/business_date 기준으로 version_no 채번
    """
    sql = text("""
        SELECT COALESCE(MAX(version_no), 0) AS maxv
        FROM upload_files
        WHERE dataset=:dataset AND business_date=:biz AND property_code=:prop
    """)
    row = db.execute(sql, {"dataset": dataset, "biz": business_date, "prop": property_code}).fetchone()
    maxv = int((row or {}).get("maxv", 0)) if row is not None else 0
    return maxv + 1


# ──────────────────────────────────────────────
# ✅ Phase 3 Final: 공통 업로드 엔드포인트
#   - 드라이런은 저장/이력 기록 없음
#   - 실제 업로드 성공 시 upload_files에 "버전 이력"만 기록(파일 저장 X)
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
    """
    SSOT 기반 업로드 엔드포인트
    - 모든 데이터셋(rooms_status, fnb_items, fnb_tenders, sales_front, expenses, pay_settlement, bank_ledger 등) 통합 처리
    - settings_merge 정책 반영
    - merge_service 실행 및 결과 반환
    """
    form = {
        "business_date": business_date,
        "property_code": property_code,
        "dry_run": dry_run,
        "split_by_date": split_by_date,
        "source_kind": source_kind,
        "mode": mode,
    }

    # 파일 검증
    if not file:
        raise HTTPException(status_code=400, detail="file is required (multipart/form-data)")
    if not dataset:
        raise HTTPException(status_code=400, detail="dataset is required in URL path")

    # 전역 정책 주입
    policy = settings_merge.get_policy(dataset)
    form["_policy"] = policy

    try:
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="uploaded file is empty")

        log.info(
            "[UPLOAD] start dataset=%s dry_run=%s size=%sB policy=%s",
            dataset,
            dry_run,
            len(file_bytes),
            {k: v for k, v in policy.items() if k in ("merge_mode", "missing_policy")},
        )

        result = run_merge_service(dataset, form, file_bytes)

        if not isinstance(result, dict):
            raise HTTPException(status_code=500, detail="merge-service-error: invalid result type")

        if not result.get("ok", False):
            # merge 서비스에서 표준화된 메시지를 넣어줌
            raise HTTPException(status_code=500, detail=result.get("error", "merge-service-error: unknown"))

        # ── 드라이런이면 여기서 바로 리턴 (저장/이력 X)
        if int(dry_run or 0) == 1:
            return result

        # ── 실제 업로드 성공: 물리 파일 저장은 하지 않고, "버전 이력"만 기록
        try:
            v = _next_version_for(db, dataset, business_date, property_code)
            logical_path = f"ssot://{dataset}/{property_code}/{business_date}/v{v}"
            filename = file.filename or f"{dataset}.csv"
            size = len(file_bytes)

            rec = UploadedFile(
                **_filter_by_model_columns(
                    UploadedFile,
                    dict(
                        # session_id 없음 (NULL 허용)
                        session_id=None,
                        version_no=v,
                        filename=filename,
                        size=size,
                        stored_path=logical_path,   # 물리 저장 대신 논리 경로로 표기
                        created_at=datetime.utcnow(),
                        part_key="",
                        dataset=dataset,
                        property_code=property_code,
                        business_date=business_date,
                        upload_type="ssot",
                        remarks="merged",
                    ),
                )
            )
            db.add(rec)
            db.commit()
        except Exception as ie:
            log.exception("[UPLOAD] version-log insert failed: %s", ie)
            # 이력 기록 실패는 업로드 자체 실패로 보지 않고 warning 수준으로 보고
            # 결과는 그대로 반환
            pass

        return result

    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"[UPLOAD] dataset={dataset} failed: {e}")
        raise HTTPException(status_code=500, detail=f"merge-service-error: {e}")


# ──────────────────────────────────────────────
# (레거시) FNB Sales 복합 업로드 — Phase 3 제거 예정
#   - 기존과 동일 (실파일 저장 + 버전, part(pay/items) 기록)
//  필요 유틸 import
from app.core.normalize import read_upload_to_csv_text
from app.services.upload_service import (
    get_or_create_session as _get_or_create_session,
    next_version as _next_version,
    store_file as _store_file,
)

try:
    from app.core.normalize import normalize_fnb_tenders, normalize_fnb_items  # type: ignore
    _HAS_FNB = True
except Exception:
    _HAS_FNB = False


@router.post(
    "/fnb_sales",
    dependencies=[Depends(require_token_local), Depends(require_roles(["ADMIN", "SUPERADMIN"]))],
)
async def upload_fnb_sales(
    business_date: str = Form(...),
    property_code: str = Form("MOP"),
    dry_run: int = Form(1),
    file_pay: UploadFile = File(...),
    file_items: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    (레거시) FNB 복합 업로드
    - file_pay + file_items 두 파일 동시 업로드
    - 향후 fnb_items / fnb_tenders 개별 업로드로 대체 예정
    """
    pay_csv, _ = read_upload_to_csv_text(file_pay)
    items_csv, _ = read_upload_to_csv_text(file_items)
    for f in (file_pay, file_items):
        try:
            f.file.seek(0)
        except Exception:
            pass

    if _HAS_FNB:
        tenders_norm = normalize_fnb_tenders(pay_csv, business_date, property_code)
        items_norm = normalize_fnb_items(items_csv, business_date, property_code)
    else:
        tenders_norm, items_norm = pay_csv, items_csv

    base = {
        "business_date": business_date,
        "property_code": property_code,
        "counts": {
            "tenders_rows": max(0, tenders_norm.count("\n") - 1),
            "items_rows": max(0, items_norm.count("\n") - 1),
        },
        "preview": {
            "tenders_head": _head_rows(tenders_norm),
            "items_head": _head_rows(items_norm),
        },
    }

    # Dry-run
    if int(dry_run or 0) == 1:
        return {"ok": True, "dry_run": True, **base}

    # 실제 저장
    dataset = "fnb_sales"
    sess = _get_or_create_session(db, dataset, business_date, property_code)
    v = _next_version(db, sess.id)
    dest_dir = DATA_ROOT / dataset / property_code / business_date / f"v{v}"
    meta1 = _store_file(file_pay, dest_dir, file_pay.filename or "pay.csv")
    meta2 = _store_file(file_items, dest_dir, file_items.filename or "items.csv")

    for meta, part in [(meta1, "pay"), (meta2, "items")]:
        rec = UploadedFile(
            **_filter_by_model_columns(
                UploadedFile,
                dict(
                    session_id=sess.id,
                    version_no=v,
                    part_key=part,
                    filename=meta["filename"],
                    stored_path=meta["path"],
                    size=meta.get("size", 0),
                    created_at=datetime.utcnow(),
                    dataset=dataset,
                    property_code=property_code,
                    business_date=business_date,
                    upload_type="legacy",
                    remarks="",
                ),
            )
        )
        db.add(rec)
    db.commit()
    return {
        "ok": True,
        "dry_run": False,
        "dataset": dataset,
        "version_no": v,
        "files": [meta1, meta2],
        **base,
    }


# ──────────────────────────────────────────────
# ✅ 업로드 이력 조회 (항상 200, 빈 배열 허용)
#    - 프론트 UX를 위해 404 대신 빈 items
# ──────────────────────────────────────────────
@router.get(
    "/versions",
    dependencies=[Depends(require_token_local)],
)
def get_upload_versions(
    dataset: str = Query(...),
    business_date: str = Query(...),
    property_code: str = Query(...),
    db: Session = Depends(get_db),
):
    """
    업로드 이력 조회 (Phase 3 — Canon 기반)
    """
    sql = text("""
        SELECT version_no, filename, size,
               COALESCE(created_at, CURRENT_TIMESTAMP) AS uploaded_at,
               COALESCE(part_key, '') AS part_key
        FROM upload_files
        WHERE dataset=:dataset AND business_date=:biz AND property_code=:prop
        ORDER BY version_no DESC, part_key ASC
    """)
    rows = db.execute(sql, {
        "dataset": dataset,
        "biz": business_date,
        "prop": property_code,
    }).fetchall()

    items = [dict(r._mapping) if hasattr(r, "_mapping") else dict(r) for r in rows]  # SQLAlchemy 1/2 호환
    return {"items": items}
