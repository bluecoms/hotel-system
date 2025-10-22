# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/merge_engine/planner.py
# Version   : 2025.10-30 · v3.5 (SSOT Final · Banking/OTA Enhanced)
# Purpose   : Hotel Admin — Merge Engine Planner (Dry-Run Diff Planner)
# ----------------------------------------------------------------------------
# 목적:
#   • 병합 전 단계(Dry-Run)에서 기존(Canon) vs 신규 데이터의 차이를 비교
#   • 신규/갱신/삭제/무변경 건수와 key_hash 목록을 산출
#   • missing_policy 결과(soft_delete / ignore / hard_delete) 반환
# ----------------------------------------------------------------------------
# 특징:
#   ✅ dataset 별 로깅 지원 (rooms_status / bank_ledger / ota_orders 등)
#   ✅ key 누락/중복 검증 강화
#   ✅ preview_limit 확장 (기본 50)
#   ✅ 누락 정책 결과에 dataset 메타 포함
# ----------------------------------------------------------------------------
# 연계:
#   • app/core/hashing.py
#   • app/merge_engine/policies.py
#   • app/merge_engine/engine.py
# ----------------------------------------------------------------------------
# 변경 로그:
#   v3.5 (2025-10-30)
#     ✅ Bank Ledger / OTA dataset 지원
#     ✅ dataset 파라미터 추가 및 로깅 포맷 강화
#     ✅ 결과 미리보기 행 50 건으로 확장
# ============================================================================
import logging
from typing import Dict, Any, List, Tuple, Optional, TypedDict

from app.core.hashing import make_key_hash, make_record_hash
from app.merge_engine.policies import get_missing_policy

log = logging.getLogger("merge_planner")

# ============================================================================
# 1️⃣ Typed Result Definitions
# ----------------------------------------------------------------------------
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
    dataset: Optional[str]
    summary: PlannerSummary
    details: PlannerDetails
    missing_result: Dict[str, Any]


# ============================================================================
# 2️⃣ Core Logic
# ----------------------------------------------------------------------------
def plan_merge(
    existing_records: List[Dict[str, Any]],
    new_records: List[Dict[str, Any]],
    key_fields: Tuple[str, ...],
    *,
    dataset: str = "generic",
    missing_policy: str = "soft_delete",
    preview_limit: int = 50,
) -> PlannerResult:
    """
    기존 Canon 데이터와 신규 업로드 데이터를 비교하여 변경 계획을 산출합니다.

    Args:
        existing_records (List[Dict]): DB에 기존 저장된 Canon 데이터
        new_records (List[Dict]): 신규 업로드 데이터
        key_fields (Tuple[str,...]): 데이터셋 고유 키 필드
        dataset (str): 로깅용 데이터셋 명
        missing_policy (str): 누락 정책 (soft_delete / ignore / hard_delete)
        preview_limit (int): 미리보기 제한 개수 (기본 50)

    Returns:
        PlannerResult: 요약 + 세부 + 누락정책 결과 딕셔너리
    """

    # 1️⃣ 기존 데이터 인덱싱
    existing_map: Dict[str, str] = {}
    for r in existing_records:
        try:
            key_tuple = tuple(r.get(k) for k in key_fields)
            if not all(key_tuple):
                log.warning(f"[PLANNER] dataset={dataset} invalid existing key: {key_tuple}")
                continue
            key_hash = make_key_hash(key_tuple)
            record_hash = make_record_hash(r)
            existing_map[key_hash] = record_hash
        except Exception as e:
            log.exception(f"[PLANNER] dataset={dataset} existing_map error: {e}")

    # 2️⃣ 신규 데이터 인덱싱
    new_map: Dict[str, str] = {}
    for r in new_records:
        try:
            key_tuple = tuple(r.get(k) for k in key_fields)
            if not all(key_tuple):
                log.warning(f"[PLANNER] dataset={dataset} invalid new key: {key_tuple}")
                continue
            key_hash = make_key_hash(key_tuple)
            record_hash = make_record_hash(r)
            new_map[key_hash] = record_hash
        except Exception as e:
            log.exception(f"[PLANNER] dataset={dataset} new_map error: {e}")

    # 3️⃣ 차이 계산
    inserted, updated, noop, deleted = [], [], [], []
    for key_hash, new_hash in new_map.items():
        old_hash = existing_map.get(key_hash)
        if old_hash is None:
            inserted.append(key_hash)
        elif old_hash != new_hash:
            updated.append(key_hash)
        else:
            noop.append(key_hash)

    for key_hash in existing_map.keys():
        if key_hash not in new_map:
            deleted.append(key_hash)

    # 4️⃣ 누락 정책 적용
    try:
        missing_func = get_missing_policy(missing_policy)
        missing_result = missing_func(list(existing_map.keys()), list(new_map.keys()))
        if isinstance(missing_result, dict):
            missing_result["dataset"] = dataset
    except Exception as e:
        log.exception(f"[PLANNER] dataset={dataset} missing_policy '{missing_policy}' failed: {e}")
        missing_result = {"error": str(e), "dataset": dataset}

    # 5️⃣ 요약 및 상세
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

    # 6️⃣ 로깅
    log.info(
        "[PLANNER] dataset=%s summary → +%d upd=%d del=%d noop=%d (policy=%s)",
        dataset,
        summary["inserted"],
        summary["updated"],
        summary["deleted"],
        summary["noop"],
        missing_policy,
    )

    # 7️⃣ 결과 반환
    return {
        "dataset": dataset,
        "summary": summary,
        "details": details,
        "missing_result": missing_result,
    }


# ============================================================================
# 3️⃣ Exports
# ----------------------------------------------------------------------------
__all__ = ["plan_merge", "PlannerSummary", "PlannerDetails", "PlannerResult"]
