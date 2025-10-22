# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/merge_engine/diff.py
# Version   : 2025.10-30 · v3.5 (SSOT Final · Banking/OTA Enhanced)
# Purpose   : Hotel Admin — SSOT Diff Engine (Canon vs Upload)
# ----------------------------------------------------------------------------
# 목적:
#   • Canon(기존) vs New(업로드) 데이터 간 차이 비교
#   • key_hash 기준으로 INSERT / UPSERT / NOOP / DELETE 분류
#   • dedupe_policy, missing_policy 적용 (first, latest 등)
#   • OTA·Bank Ledger·SalesFront 등 대용량 dataset 호환
# ----------------------------------------------------------------------------
# 주요 기능:
#   ✅ 중복 제거 정책(dedupe_policy) 적용
#   ✅ 누락 정책(missing_policy) 반영
#   ✅ Dry-run 프리뷰 및 Merge Plan 사전 산출
#   ✅ dataset 식별자 기반 로깅 강화
# ----------------------------------------------------------------------------
# 변경 로그:
#   v3.5 (2025-10-30)
#     ✅ dataset 파라미터 추가 및 로깅 개선
#     ✅ dedupe/missing 결과에 dataset 필드 포함
#     ✅ preview_limit 10 → 50 확장
# ============================================================================
from __future__ import annotations
from typing import Dict, Any, List, Tuple
import logging

from app.core.hashing import make_key_hash, make_record_hash
from app.merge_engine.policies import get_dedupe_policy, get_missing_policy

log = logging.getLogger("merge_diff")


# ============================================================================
# 1️⃣ 내부 유틸: 인덱싱
# ----------------------------------------------------------------------------
def _index_records(
    records: List[Dict[str, Any]],
    key_fields: Tuple[str, ...],
    dataset: str = "generic",
) -> Dict[str, Dict[str, Any]]:
    """
    레코드를 key_hash → {payload, record_hash} 로 매핑
    - key_fields 튜플을 해시하여 key_hash 생성
    - record_hash 는 payload 전체(메타 제외) 기준
    """
    idx: Dict[str, Dict[str, Any]] = {}
    for r in records:
        try:
            key_tuple = tuple(r.get(k) for k in key_fields)
            if not all(key_tuple):
                log.warning(f"[DIFF] dataset={dataset} invalid key tuple: {key_tuple}")
                continue
            key_hash = make_key_hash(key_tuple)
            record_hash = make_record_hash(r)
            idx[key_hash] = {"payload": r, "record_hash": record_hash}
        except Exception as e:
            log.exception(f"[DIFF] dataset={dataset} index error: {e}")
    return idx


# ============================================================================
# 2️⃣ 공개 API: Diff 계산
# ----------------------------------------------------------------------------
def compute_diff(
    existing_records: List[Dict[str, Any]],
    new_records: List[Dict[str, Any]],
    key_fields: Tuple[str, ...],
    *,
    dataset: str = "generic",
    dedupe_policy: str = "first",         # first | last | latest
    missing_policy: str = "soft_delete",  # ignore | soft_delete | hard_delete
    preview_limit: int = 50,
) -> Dict[str, Any]:
    """
    Canon(기존) ↔ New(업로드) 차이 계산

    Args:
        existing_records: Canon 레코드 목록
        new_records: 업로드 레코드 목록
        key_fields: 데이터셋 고유 키 튜플
        dataset: 데이터셋 식별자 (예: bank_ledger, ota_orders)
        dedupe_policy: 중복 제거 정책
        missing_policy: 누락 처리 정책
        preview_limit: 미리보기 제한 행 수

    Returns:
        {
          "dataset": str,
          "counts": {...},
          "details": {...},
          "missing_result": {...},
          "dedupe_applied": {...},
          "actions": [...]
        }
    """

    # 1️⃣ 신규 데이터 중복 제거
    before_cnt = len(new_records)
    deduper = get_dedupe_policy(dedupe_policy)
    try:
        new_records = deduper(new_records, key_fields)
    except Exception as e:
        log.exception(f"[DIFF] dataset={dataset} dedupe_policy({dedupe_policy}) failed: {e}")
    after_cnt = len(new_records)

    # 2️⃣ 인덱싱
    existing_idx = _index_records(existing_records, key_fields, dataset)
    new_idx = _index_records(new_records, key_fields, dataset)

    existing_keys = list(existing_idx.keys())
    new_keys = list(new_idx.keys())

    inserted, upserted, noop, deleted = [], [], [], []
    actions: List[Dict[str, Any]] = []

    # 3️⃣ 신규 데이터 기준: INSERT / UPSERT / NOOP
    for key_hash, n in new_idx.items():
        n_hash = n["record_hash"]
        n_payload = n["payload"]
        if key_hash not in existing_idx:
            inserted.append(key_hash)
            actions.append({
                "dataset": dataset,
                "action": "INSERT",
                "key_hash": key_hash,
                "old_hash": None,
                "new_hash": n_hash,
                "payload": n_payload,
            })
        else:
            e_hash = existing_idx[key_hash]["record_hash"]
            if e_hash != n_hash:
                upserted.append(key_hash)
                actions.append({
                    "dataset": dataset,
                    "action": "UPSERT",
                    "key_hash": key_hash,
                    "old_hash": e_hash,
                    "new_hash": n_hash,
                    "payload": n_payload,
                })
            else:
                noop.append(key_hash)
                actions.append({
                    "dataset": dataset,
                    "action": "NOOP",
                    "key_hash": key_hash,
                    "old_hash": e_hash,
                    "new_hash": n_hash,
                    "payload": n_payload,
                })

    # 4️⃣ 누락 레코드 → 삭제 후보
    missing_keys = [k for k in existing_keys if k not in new_idx]
    missing_handler = get_missing_policy(missing_policy)
    try:
        missing_result = missing_handler(existing_keys, new_keys)
        if isinstance(missing_result, dict):
            missing_result["dataset"] = dataset
    except Exception as e:
        log.exception(f"[DIFF] dataset={dataset} missing_policy({missing_policy}) failed: {e}")
        missing_result = {"error": str(e), "dataset": dataset}

    if missing_policy != "ignore":
        for key_hash in missing_keys:
            e_hash = existing_idx[key_hash]["record_hash"]
            deleted.append(key_hash)
            actions.append({
                "dataset": dataset,
                "action": "DELETE",
                "key_hash": key_hash,
                "old_hash": e_hash,
                "new_hash": None,
                "payload": None,
            })

    # 5️⃣ 집계 / 샘플
    counts = {
        "inserted": len(inserted),
        "upserted": len(upserted),
        "deleted": len(deleted) if missing_policy != "ignore" else 0,
        "noop": len(noop),
    }

    details = {
        "inserted": inserted[:preview_limit],
        "upserted": upserted[:preview_limit],
        "deleted": deleted[:preview_limit],
        "noop": noop[:preview_limit],
    }

    log.info(
        "[DIFF] dataset=%s result → +%d up=%d del=%d noop=%d "
        "(dedupe=%s %s→%s, missing=%s)",
        dataset,
        counts["inserted"],
        counts["upserted"],
        counts["deleted"],
        counts["noop"],
        dedupe_policy,
        before_cnt,
        after_cnt,
        missing_policy,
    )

    # 6️⃣ 결과 반환
    return {
        "dataset": dataset,
        "counts": counts,
        "details": details,
        "missing_result": missing_result,
        "dedupe_applied": {"policy": dedupe_policy, "before": before_cnt, "after": after_cnt},
        "actions": actions,
    }
