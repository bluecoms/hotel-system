# app/merge_engine/diff.py
# -*- coding: utf-8 -*-
"""
SSOT Diff Engine (Phase 2)
────────────────────────────────────────
- Canon(기존) vs New(업로드) 레코드의 차이를 key_hash 기준으로 산출
- INSERT / UPSERT / NOOP / DELETE 분류
- dedupe_policy, missing_policy 적용
- 엔진/서비스에서 dry_run 프리뷰 및 실반영 전 계획 수립에 사용
"""

from __future__ import annotations
from typing import Dict, Any, List, Tuple
import logging

from app.core.hashing import make_key_hash, make_record_hash
from app.merge_engine.policies import get_dedupe_policy, get_missing_policy

log = logging.getLogger(__name__)


# ───────────────────────────────────────────────
# 내부 유틸
# ───────────────────────────────────────────────
def _index_records(
    records: List[Dict[str, Any]],
    key_fields: Tuple[str, ...],
) -> Dict[str, Dict[str, Any]]:
    """
    레코드를 key_hash → {payload, record_hash} 로 매핑
    - key_fields 값 튜플을 해시하여 key_hash 생성
    - record_hash 는 payload 전체(메타 제외) 기준
    """
    idx: Dict[str, Dict[str, Any]] = {}
    for r in records:
        try:
            key_tuple = tuple(r.get(k) for k in key_fields)
            if not all(key_tuple):
                log.warning(f"[DIFF] invalid key tuple: {key_tuple}")
                continue
            key_hash = make_key_hash(key_tuple)
            record_hash = make_record_hash(r)
            idx[key_hash] = {"payload": r, "record_hash": record_hash}
        except Exception as e:
            log.exception(f"[DIFF] index error on record: {e}")
    return idx


# ───────────────────────────────────────────────
# 공개 API
# ───────────────────────────────────────────────
def compute_diff(
    existing_records: List[Dict[str, Any]],
    new_records: List[Dict[str, Any]],
    key_fields: Tuple[str, ...],
    *,
    dedupe_policy: str = "first",         # first | last | latest
    missing_policy: str = "soft_delete",  # ignore | soft_delete | hard_delete
    preview_limit: int = 10,
) -> Dict[str, Any]:
    """
    Canon(기존) ↔ New(업로드) 차이 계산
    Returns:
        {
          "counts": {"inserted": n, "upserted": n, "deleted": n, "noop": n},
          "details": {...},
          "missing_result": {...},
          "dedupe_applied": {"policy": str, "before": int, "after": int},
          "actions": [...]
        }
    """
    # 1️⃣ 신규 데이터 중복 제거 (dedupe_policy)
    deduper = get_dedupe_policy(dedupe_policy)
    before_cnt = len(new_records)
    try:
        new_records = deduper(new_records, key_fields)
    except Exception as e:
        log.exception(f"[DIFF] dedupe_policy({dedupe_policy}) failed: {e}")
    after_cnt = len(new_records)

    # 2️⃣ 인덱싱
    existing_idx = _index_records(existing_records, key_fields)
    new_idx = _index_records(new_records, key_fields)

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
                    "action": "UPSERT",
                    "key_hash": key_hash,
                    "old_hash": e_hash,
                    "new_hash": n_hash,
                    "payload": n_payload,
                })
            else:
                noop.append(key_hash)
                actions.append({
                    "action": "NOOP",
                    "key_hash": key_hash,
                    "old_hash": e_hash,
                    "new_hash": n_hash,
                    "payload": n_payload,
                })

    # 4️⃣ 누락 레코드 → 삭제 후보 (missing_policy)
    missing_keys = [k for k in existing_keys if k not in new_idx]
    missing_handler = get_missing_policy(missing_policy)
    try:
        missing_result = missing_handler(existing_keys, new_keys)
    except Exception as e:
        log.exception(f"[DIFF] missing_policy({missing_policy}) failed: {e}")
        missing_result = {"error": str(e)}

    if missing_policy != "ignore":
        for key_hash in missing_keys:
            e_hash = existing_idx[key_hash]["record_hash"]
            deleted.append(key_hash)
            actions.append({
                "action": "DELETE",
                "key_hash": key_hash,
                "old_hash": e_hash,
                "new_hash": None,
                "payload": None,
            })

    # 5️⃣ 집계/샘플
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
        "[DIFF] result: +%s up=%s del=%s noop=%s (dedupe=%s %s→%s, missing=%s)",
        counts["inserted"],
        counts["upserted"],
        counts["deleted"],
        counts["noop"],
        dedupe_policy,
        before_cnt,
        after_cnt,
        missing_policy,
    )

    return {
        "counts": counts,
        "details": details,
        "missing_result": missing_result,
        "dedupe_applied": {"policy": dedupe_policy, "before": before_cnt, "after": after_cnt},
        "actions": actions,
    }
