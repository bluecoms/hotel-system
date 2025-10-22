# app/services/merge_service.py
# -*- coding: utf-8 -*-
# version: 2025-10-12 Phase 3 Final (settings_merge integration)
"""
Merge Service (Phase 3 Final)
──────────────────────────────────────────────
- routers → services → merge_engine 브리지
- adapter 로드, 폼 정규화, 정책 주입(settings_merge)
- 표준화된 로그 및 에러 포맷
"""

from __future__ import annotations
import logging
from typing import Dict, Any
from fastapi import HTTPException

from app.datasets.adapters import get_adapter
from app.merge_engine import engine
from app.core import settings_merge

__all__ = ["run_merge_service"]

log = logging.getLogger("merge_service")

# ───────────────────────────────────────────────
# 내부 헬퍼: form 정규화
# ───────────────────────────────────────────────
def _normalize_form(form: Dict[str, Any]) -> Dict[str, Any]:
    """
    폼 데이터 정규화 및 필수 기본값 주입
    """
    f = dict(form or {})

    # 필수 필드 검증
    if not f.get("business_date"):
        raise HTTPException(status_code=400, detail="business_date is required (YYYY-MM-DD)")

    if not f.get("property_code"):
        f["property_code"] = "MOP"

    # dry_run 보정 (문자/불리언 혼용 처리)
    dr = f.get("dry_run", "1")
    if isinstance(dr, bool):
        dr = "1" if dr else "0"
    else:
        dr = "1" if str(dr).strip() == "1" else "0"
    f["dry_run"] = dr

    # source_kind 기본값
    if not f.get("source_kind"):
        f["source_kind"] = "daily"

    # mode 기본값(snapshot/append)
    if not f.get("mode"):
        f["mode"] = "snapshot"

    return f


# ───────────────────────────────────────────────
# 공개 API: Merge 엔진 브리지
# ───────────────────────────────────────────────
def run_merge_service(dataset: str, form: Dict[str, Any], file_bytes: bytes) -> Dict[str, Any]:
    """
    Merge 엔진 실행 브리지
    - adapter 로드 → 정책 주입(settings_merge.get_policy)
    - engine.run_merge(adapter, form, file_bytes)
    - 결과 검증 및 표준화된 에러/로그
    """
    try:
        if not dataset:
            raise HTTPException(status_code=400, detail="dataset is required")

        if not file_bytes:
            raise HTTPException(status_code=400, detail="file is required")

        # 1️⃣ 정책 로드 및 폼 정규화
        policy = settings_merge.get_policy(dataset)
        norm_form = _normalize_form(form)
        norm_form["_policy"] = policy  # 엔진으로 전달되는 내부 메타 정보

        log.info(
            "[MERGE_SERVICE] start dataset=%s dry_run=%s mode=%s bytes=%s policy=%s",
            dataset,
            norm_form.get("dry_run"),
            norm_form.get("mode"),
            len(file_bytes) if file_bytes else 0,
            {k: v for k, v in policy.items() if k in ('merge_mode', 'missing_policy')},
        )

        # 2️⃣ 어댑터 로드
        adapter = get_adapter(dataset)
        if adapter is None:
            raise HTTPException(status_code=400, detail=f"adapter not found for dataset={dataset}")

        # 3️⃣ 엔진 실행
        result = engine.run_merge(adapter, norm_form, file_bytes)

        # 4️⃣ 결과 검증
        if not isinstance(result, dict):
            raise HTTPException(status_code=500, detail="merge-engine returned invalid result")

        if not result.get("ok", False):
            err = result.get("error") or "merge-engine returned ok=False"
            raise HTTPException(status_code=500, detail=f"merge-engine-error: {err}")

        counts = result.get("counts", {})
        rows = counts.get("rows") if isinstance(counts, dict) else None

        # 5️⃣ 완료 로그
        log.info(
            "[MERGE_SERVICE] done ok=%s dry_run=%s rows=%s batch_id=%s dataset=%s",
            result.get("ok"),
            result.get("dry_run"),
            rows,
            result.get("batch_id"),
            dataset,
        )

        return result

    except HTTPException:
        raise

    except Exception as e:
        # 예기치 않은 에러 → 표준 포맷으로 래핑
        log.exception("[MERGE_SERVICE] unexpected failure: %s", e)
        raise HTTPException(status_code=500, detail=f"merge-service-error: {e}")
