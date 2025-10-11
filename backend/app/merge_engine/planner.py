# app/merge_engine/planner.py
# -*- coding: utf-8 -*-
"""
Merge Engine Planner (Phase 2)
──────────────────────────────────────────────
- 드라이런(dry-run)에서 변경 계획 산출
- 신규/갱신/삭제/무변경 수량 및 키 해시 목록 반환
- 누락 정책 적용 결과 포함
"""

import logging
from typing import Dict, Any, List, Tuple, Optional, TypedDict
from app.core.hashing import make_key_hash, make_record_hash
from app.merge_engine.policies import get_missing_policy

log = logging.getLogger("app.merge_engine.planner")


# ───────────────────────────────────────────────
# Typed Results
# ───────────────────────────────────────────────
class PlannerSummary(TypedDict):
    inserted: int
    updated: int
    deleted: int
    noop: int


class PlannerDetails(TypedDict):
    inserted: List[str]
    updated: List[str]
    deleted: List[str]
    noop: List[str]


class PlannerResult(TypedDict, total=False):
    summary: PlannerSummary
    details: PlannerDetails
    missing_result: Dict[str, Any]


# ───────────────────────────────────────────────
# Core Logic
# ───────────────────────────────────────────────
def plan_merge(
    existing_records: List[Dict[str, Any]],
    new_records: List[Dict[str, Any]],
    key_fields: Tuple[str, ...],
    missing_policy: str = "soft_delete",
    preview_limit: int = 10,
) -> PlannerResult:
    """
    기존 Canon과 신규 데이터 비교하여 변경 계획을 산출한다.
    - key_fields 기준으로 inserted/updated/deleted/noop 구분
    - missing_policy 적용 결과를 함께 반환
    """

    # 1️⃣ 안전한 key-hash / record-hash 매핑
    existing_map: Dict[str, str] = {}
    for r in existing_records:
        try:
            key_tuple = tuple(r.get(k) for k in key_fields)
            if not all(key_tuple):
                log.warning(f"[PLANNER] invalid existing key tuple: {key_tuple}")
                continue
            key_hash = make_key_hash(key_tuple)
            record_hash = make_record_hash(r)
            existing_map[key_hash] = record_hash
        except Exception as e:
            log.exception(f"[PLANNER] error building existing_map: {e}")

    new_map: Dict[str, str] = {}
    for r in new_records:
        try:
            key_tuple = tuple(r.get(k) for k in key_fields)
            if not all(key_tuple):
                log.warning(f"[PLANNER] invalid new key tuple: {key_tuple}")
                continue
            key_hash = make_key_hash(key_tuple)
            record_hash = make_record_hash(r)
            new_map[key_hash] = record_hash
        except Exception as e:
            log.exception(f"[PLANNER] error building new_map: {e}")

    # 2️⃣ 결과 집계용 리스트
    inserted, updated, noop, deleted = [], [], [], []

    # 3️⃣ 신규/갱신/무변경 판별
    for key_hash, new_hash in new_map.items():
        old_hash = existing_map.get(key_hash)
        if old_hash is None:
            inserted.append(key_hash)
        elif old_hash != new_hash:
            updated.append(key_hash)
        else:
            noop.append(key_hash)

    # 4️⃣ 삭제 후보 판별
    for key_hash in existing_map.keys():
        if key_hash not in new_map:
            deleted.append(key_hash)

    # 5️⃣ 누락 정책 적용
    try:
        missing_func = get_missing_policy(missing_policy)
        missing_result = missing_func(list(existing_map.keys()), list(new_map.keys()))
    except Exception as e:
        log.exception(f"[PLANNER] missing policy '{missing_policy}' failed: {e}")
        missing_result = {"error": str(e)}

    # 6️⃣ 결과 집계
    summary: PlannerSummary = {
        "inserted": len(inserted),
        "updated": len(updated),
        "deleted": len(deleted) if missing_policy != "ignore" else 0,
        "noop": len(noop),
    }

    details: PlannerDetails = {
        "inserted": inserted[:preview_limit],
        "updated": updated[:preview_limit],
        "deleted": deleted[:preview_limit],
        "noop": noop[:preview_limit],
    }

    log.info(
        "[PLANNER] merge plan summary: +%d upd=%d del=%d noop=%d (policy=%s)",
        summary["inserted"],
        summary["updated"],
        summary["deleted"],
        summary["noop"],
        missing_policy,
    )

    return {
        "summary": summary,
        "details": details,
        "missing_result": missing_result,
    }


# ───────────────────────────────────────────────
# Default Export
# ───────────────────────────────────────────────
__all__ = ["plan_merge", "PlannerSummary", "PlannerDetails", "PlannerResult"]
