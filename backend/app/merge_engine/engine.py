# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/merge_engine/engine.py
# Version   : 2025-10-31 · v3.6 (SSOT Stable)
# Purpose   : SSOT Merge Engine — Normalize → Parse → Persist (DryRun 지원)
# ----------------------------------------------------------------------------
# 목적:
#   • 업로드된 CSV를 Normalize → Parse → DB Merge하는 통합 엔진
#   • Adapter 기반 병합 정책(settings_merge) 반영
#   • Dry-run / 실제 반영 / 감사 로그(record_merge_audit) 연계
# ----------------------------------------------------------------------------
# 특징:
#   ✅ CSV BOM 제거 및 안전 디코딩
#   ✅ Dry-run 시 DB 영향 없음
#   ✅ 정책 기반 merge_mode / missing_policy 자동 결정
#   ✅ SQLite / PostgreSQL 호환
# ----------------------------------------------------------------------------
# 사용 예:
#   from app.merge_engine.engine import run_merge
#   run_merge(adapter, form, file_bytes)
# ============================================================================

from __future__ import annotations
from typing import Dict, Any, List, Optional
import logging
from sqlalchemy.orm import Session
from app.core.hashing import make_key_hash, make_record_hash
from app.db.session import get_db
from app.merge_engine.repository import persist_records, MergeAuditRepository
from app.merge_engine.audit import record_merge_audit
from app.core import settings_merge

log = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# 유틸: 디코딩 / 정리
# ─────────────────────────────────────────────
def _decode_bytes(data: bytes) -> str:
    """업로드된 바이트 데이터를 안전하게 문자열로 디코딩 (UTF-8 BOM 제거 포함)"""
    if not data:
        return ""
    try:
        txt = data.decode("utf-8", errors="ignore")
    except Exception as e:
        log.warning(f"[MERGE_ENGINE] decode failed: {e}")
        txt = ""
    if txt.startswith("\ufeff"):
        txt = txt.lstrip("\ufeff")
    return txt


def _sanitize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """record_hash 계산 시 제외할 메타 필드 제거"""
    if not isinstance(payload, dict):
        return {}
    meta_keys = {"key_hash", "record_hash"}
    return {k: v for k, v in payload.items() if k not in meta_keys}


def _preview_rows(records: List[Any]) -> List[Dict[str, Any]]:
    """Dry-run용 미리보기 데이터 구성 (최대 3건)"""
    out: List[Dict[str, Any]] = []
    for rec in records[:3]:
        payload = getattr(rec, "payload", {})
        key_tuple = getattr(rec, "key_tuple", [])
        payload_clean = _sanitize_payload(payload)
        key_hash = make_key_hash(tuple(key_tuple))
        record_hash = make_record_hash(payload_clean)
        out.append({
            "key_tuple": tuple(key_tuple),
            "key_hash": key_hash,
            "record_hash": record_hash,
            "payload": payload_clean,
        })
    return out


# ─────────────────────────────────────────────
# 메인 엔진
# ─────────────────────────────────────────────
def run_merge(adapter, form: Dict[str, Any], file_bytes: bytes) -> Dict[str, Any]:
    """
    SSOT Merge Engine (Phase 6)
    - normalize → parse → (dry_run ? preview : persist)
    - 정책(settings_merge) 및 감사 로그(record_merge_audit) 반영
    """
    if adapter is None:
        log.error("[MERGE_ENGINE] adapter is None")
        return {"ok": False, "error": "merge-engine-error: adapter not provided"}

    dataset = getattr(adapter, "dataset", form.get("dataset") or "")
    policy = form.get("_policy") or settings_merge.get_policy(dataset or "rooms_status")

    # 1️⃣ CSV Normalize
    raw_text = _decode_bytes(file_bytes)
    try:
        canon_csv = adapter.normalize(
            raw_csv_text=raw_text,
            fallback_business_date=form.get("business_date", ""),
            property_code=form.get("property_code", "MOP"),
        )
    except Exception as e:
        log.exception(f"[MERGE_ENGINE] normalize error: {e}")
        return {"ok": False, "error": f"merge-engine-error: normalize error: {e}"}

    # 2️⃣ Parse normalized CSV → record objects
    try:
        records = list(adapter.parse(canon_csv))
    except Exception as e:
        log.exception(f"[MERGE_ENGINE] parse error: {e}")
        return {"ok": False, "error": f"merge-engine-error: parse error: {e}"}

    # 3️⃣ 실행 모드 결정
    mode = (
        str(form.get("mode") or "").strip().lower()
        or adapter.merge_mode(form)
        or policy.get("merge_mode", "snapshot")
    )
    is_dry_run = str(form.get("dry_run", "1")) == "1"
    property_code = form.get("property_code", "MOP")
    business_date = form.get("business_date")
    dataset = dataset or adapter.dataset

    # Dry-run
    if is_dry_run:
        log.info(f"[MERGE_ENGINE] Dry-run ({len(records)} rows, mode={mode}, dataset={dataset})")
        return {
            "ok": True,
            "dry_run": True,
            "dataset": dataset,
            "mode": mode,
            "policy": {k: policy.get(k) for k in ("merge_mode", "missing_policy")},
            "counts": {"rows": len(records)},
            "preview": _preview_rows(records),
        }

    # 4️⃣ 실제 DB 반영
    db: Optional[Session] = None
    try:
        db = next(get_db())
    except Exception as e:
        log.exception(f"[MERGE_ENGINE] DB session acquire failed: {e}")
        return {"ok": False, "error": f"merge-engine-error: db-session error: {e}"}

    try:
        audit_repo = MergeAuditRepository(db)
        batch = audit_repo.create_batch(
            dataset=dataset,
            property_code=property_code,
            business_date=business_date,
            mode=mode,
            missing_policy=policy.get("missing_policy", getattr(adapter, "default_missing_policy", "soft_delete")),
            source_kind=form.get("source_kind", "daily"),
            session_id=form.get("session_id"),
            version_no=form.get("version_no"),
        )

        result = persist_records(db, dataset, batch.id, [r.payload for r in records])
        total_rows = sum(result.get(k, 0) for k in ("inserted", "upserted", "noop"))
        notes = f"inserted={result.get('inserted',0)}, upserted={result.get('upserted',0)}, noop={result.get('noop',0)}"

        audit_repo.finalize_batch(batch, status="DONE", record_count=total_rows, notes=notes)

        # 감사 로그 기록
        try:
            record_merge_audit(
                db=db,
                dataset=dataset,
                property_code=property_code,
                mode=mode,
                missing_policy=policy.get("missing_policy", getattr(adapter, "default_missing_policy", "soft_delete")),
                source_kind=form.get("source_kind", "daily"),
                changes=result.get("changes", []),
                session_id=form.get("session_id"),
                version_no=form.get("version_no"),
                dry_run=False,
            )
        except Exception as e:
            log.warning(f"[MERGE_ENGINE] record_merge_audit failed: {e}")

        log.info(
            "[MERGE_ENGINE] Applied dataset=%s rows=%s (inserted=%s, upserted=%s, noop=%s) batch_id=%s",
            dataset, total_rows,
            result.get("inserted", 0),
            result.get("upserted", 0),
            result.get("noop", 0),
            batch.id,
        )

        return {
            "ok": True,
            "dry_run": False,
            "dataset": dataset,
            "mode": mode,
            "batch_id": batch.id,
            "result": result,
            "counts": {"rows": total_rows},
        }

    except Exception as e:
        log.exception(f"[MERGE_ENGINE] persist error: {e}")
        return {"ok": False, "error": f"merge-engine-error: persist error: {e}"}
    finally:
        try:
            if db:
                db.close()
        except Exception as e:
            log.debug(f"[MERGE_ENGINE] DB close ignored: {e}")
