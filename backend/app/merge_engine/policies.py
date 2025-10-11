# app/merge_engine/policies.py
# -*- coding: utf-8 -*-
"""
Merge Engine 정책 정의 (Phase 2)
──────────────────────────────────────────────
- 중복 제거(Deduplication)
- 누락 레코드 처리(Missing Policy)
- 정책 이름별 callable registry
- 안전형 + 표준화된 반환 구조 적용
"""

import logging
from typing import List, Dict, Any, Tuple, Callable, Optional, TypedDict

log = logging.getLogger(__name__)


# ───────────────────────────────────────────────
# Typed Result
# ───────────────────────────────────────────────
class MergePolicyResult(TypedDict, total=False):
    policy: str
    count: int
    affected_keys: List[Any]
    notes: Optional[str]


# ───────────────────────────────────────────────
# Deduplication Policies
# ───────────────────────────────────────────────
def dedupe_first(records: List[Dict[str, Any]], key_fields: Tuple[str, ...]) -> List[Dict[str, Any]]:
    """동일 키의 첫 번째 레코드만 유지"""
    try:
        seen = set()
        out: List[Dict[str, Any]] = []
        for rec in records:
            key = tuple(rec.get(k) for k in key_fields)
            if key not in seen:
                out.append(rec)
                seen.add(key)
        log.debug(f"[POLICY] dedupe_first: {len(records)} → {len(out)}")
        return out
    except Exception as e:
        log.exception(f"[POLICY] dedupe_first failed: {e}")
        return records


def dedupe_last(records: List[Dict[str, Any]], key_fields: Tuple[str, ...]) -> List[Dict[str, Any]]:
    """동일 키의 마지막 레코드만 유지"""
    try:
        temp: Dict[Tuple[Any, ...], Dict[str, Any]] = {}
        for rec in records:
            key = tuple(rec.get(k) for k in key_fields)
            temp[key] = rec
        out = list(temp.values())
        log.debug(f"[POLICY] dedupe_last: {len(records)} → {len(out)}")
        return out
    except Exception as e:
        log.exception(f"[POLICY] dedupe_last failed: {e}")
        return records


def dedupe_latest(
    records: List[Dict[str, Any]],
    key_fields: Tuple[str, ...],
    ts_field: str = "updated_at",
) -> List[Dict[str, Any]]:
    """타임스탬프 기준 최신 레코드 유지"""
    try:
        grouped: Dict[Tuple[Any, ...], Dict[str, Any]] = {}
        for rec in records:
            key = tuple(rec.get(k) for k in key_fields)
            prev = grouped.get(key)
            cur_ts = str(rec.get(ts_field) or "")
            prev_ts = str(prev.get(ts_field) or "") if prev else ""
            if prev is None or cur_ts > prev_ts:
                grouped[key] = rec
        out = list(grouped.values())
        log.debug(f"[POLICY] dedupe_latest: {len(records)} → {len(out)} by {ts_field}")
        return out
    except Exception as e:
        log.exception(f"[POLICY] dedupe_latest failed: {e}")
        return records


# ───────────────────────────────────────────────
# Missing Record Policies
# ───────────────────────────────────────────────
def missing_ignore(existing_keys: List[Any], new_keys: List[Any]) -> MergePolicyResult:
    """누락 무시 (아무 조치 없음)"""
    try:
        ignored = set(existing_keys) - set(new_keys)
        log.debug(f"[POLICY] missing_ignore: ignored {len(ignored)} keys")
        return {
            "policy": "ignore",
            "count": len(ignored),
            "affected_keys": list(ignored),
            "notes": "no deletion",
        }
    except Exception as e:
        log.exception(f"[POLICY] missing_ignore failed: {e}")
        return {"policy": "ignore", "count": 0, "affected_keys": [], "notes": str(e)}


def missing_soft_delete(existing_keys: List[Any], new_keys: List[Any]) -> MergePolicyResult:
    """누락된 레코드의 is_deleted 플래그 설정"""
    try:
        to_delete = set(existing_keys) - set(new_keys)
        log.info(f"[POLICY] soft_delete: {len(to_delete)} rows flagged deleted")
        return {
            "policy": "soft_delete",
            "count": len(to_delete),
            "affected_keys": list(to_delete),
            "notes": "flagged is_deleted=1",
        }
    except Exception as e:
        log.exception(f"[POLICY] missing_soft_delete failed: {e}")
        return {"policy": "soft_delete", "count": 0, "affected_keys": [], "notes": str(e)}


def missing_hard_delete(existing_keys: List[Any], new_keys: List[Any]) -> MergePolicyResult:
    """누락된 레코드 실제 삭제"""
    try:
        to_delete = set(existing_keys) - set(new_keys)
        log.warning(f"[POLICY] hard_delete: {len(to_delete)} rows permanently removed")
        return {
            "policy": "hard_delete",
            "count": len(to_delete),
            "affected_keys": list(to_delete),
            "notes": "hard delete",
        }
    except Exception as e:
        log.exception(f"[POLICY] missing_hard_delete failed: {e}")
        return {"policy": "hard_delete", "count": 0, "affected_keys": [], "notes": str(e)}


# ───────────────────────────────────────────────
# Policy Registry
# ───────────────────────────────────────────────
DEDUPE_POLICIES: Dict[str, Callable[..., List[Dict[str, Any]]]] = {
    "first": dedupe_first,
    "last": dedupe_last,
    "latest": dedupe_latest,
}

MISSING_POLICIES: Dict[str, Callable[..., MergePolicyResult]] = {
    "ignore": missing_ignore,
    "soft_delete": missing_soft_delete,
    "hard_delete": missing_hard_delete,
}


# ───────────────────────────────────────────────
# Helper Accessors
# ───────────────────────────────────────────────
def get_dedupe_policy(name: Optional[str]) -> Callable[..., List[Dict[str, Any]]]:
    """이름으로 중복제거 정책 반환 (기본: first)"""
    policy = (name or "first").strip().lower()
    func = DEDUPE_POLICIES.get(policy)
    if not func:
        log.warning(f"[POLICY] Unknown dedupe policy '{name}', fallback=first")
        func = dedupe_first
    return func


def get_missing_policy(name: Optional[str]) -> Callable[..., MergePolicyResult]:
    """이름으로 누락처리 정책 반환 (기본: soft_delete)"""
    policy = (name or "soft_delete").strip().lower()
    func = MISSING_POLICIES.get(policy)
    if not func:
        log.warning(f"[POLICY] Unknown missing policy '{name}', fallback=soft_delete")
        func = missing_soft_delete
    return func


# ───────────────────────────────────────────────
# Default Export
# ───────────────────────────────────────────────
__all__ = [
    "MergePolicyResult",
    "dedupe_first",
    "dedupe_last",
    "dedupe_latest",
    "missing_ignore",
    "missing_soft_delete",
    "missing_hard_delete",
    "get_dedupe_policy",
    "get_missing_policy",
    "DEDUPE_POLICIES",
    "MISSING_POLICIES",
]
