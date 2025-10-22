# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/core/hashing.py
# Version   : 2025.10-30 · v2.2 (SSOT Safe Hash Final)
# Purpose   : Hotel Admin — SSOT Merge Engine Hash Utilities
# ----------------------------------------------------------------------------
# 목적:
#   • SSOT Merge Engine 전역에서 사용하는 안전한 해시 유틸리티
#   • Canon/History/Batch/Adapter/Planner 등 모든 레이어 공용
# ----------------------------------------------------------------------------
# 기능:
#   ✅ make_key_hash     : 키 튜플 기반 SHA256 (고유 식별자)
#   ✅ make_record_hash  : payload(JSON) 기반 안정 해시
# ----------------------------------------------------------------------------
# 특징:
#   • None / NaN / Decimal / float 처리 안정화
#   • dict/list 중첩 구조에서도 재귀적 JSON 정렬 안정성 확보
#   • UTF-8 + ensure_ascii=False 로 한글 보존
#   • 모든 예외를 ValueError 로 래핑해 로그와 함께 던짐
# ============================================================================
import hashlib
import json
import logging
from decimal import Decimal
from typing import Any, Tuple, Dict

log = logging.getLogger("core.hashing")

# ============================================================================
# 1️⃣ make_key_hash — 고유 키 해시
# ----------------------------------------------------------------------------
def make_key_hash(key_tuple: Tuple[Any, ...]) -> str:
    """
    키 튜플을 SHA256 해시로 변환.
    - None, 공백은 '' 로 통일
    - 요소를 '|' 로 연결 후 UTF-8 인코딩
    """
    try:
        parts = ["" if v is None else str(v).strip() for v in key_tuple]
        s = "|".join(parts)
        return hashlib.sha256(s.encode("utf-8", errors="ignore")).hexdigest()
    except Exception as e:
        log.exception(f"[HASH] make_key_hash failed: {e}")
        raise ValueError(f"key_hash_error: {e}")


# ============================================================================
# 2️⃣ make_record_hash — payload 해시
# ----------------------------------------------------------------------------
def make_record_hash(payload: Dict[str, Any]) -> str:
    """
    payload(dict)를 SHA256 해시로 변환.
    - sort_keys=True 로 키 순서 고정
    - ensure_ascii=False 로 한글/유니코드 보존
    - None / NaN / Decimal / float 통일
    """
    try:
        def _normalize(v: Any) -> Any:
            """중첩 구조 포함 안전 정규화"""
            if v is None:
                return ""
            if isinstance(v, float):
                # NaN 방지
                if v != v:  # NaN 체크
                    return ""
                return round(v, 6)
            if isinstance(v, Decimal):
                return str(v)
            if isinstance(v, (list, tuple)):
                return [_normalize(x) for x in v]
            if isinstance(v, dict):
                return {k: _normalize(x) for k, x in v.items()}
            return v

        normalized = _normalize(payload)
        s = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(s.encode("utf-8", errors="ignore")).hexdigest()

    except Exception as e:
        log.exception(f"[HASH] make_record_hash failed: {e}")
        raise ValueError(f"record_hash_error: {e}")


# ============================================================================
# 3️⃣ Export
# ----------------------------------------------------------------------------
__all__ = ["make_key_hash", "make_record_hash"]
