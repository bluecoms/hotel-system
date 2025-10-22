# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/merge_engine/audit.py
# Version   : 2025-10-31 · v3.6 (SSOT Stable · Hotfix MergeBatch Import)
# Purpose   : Hotel Admin — Merge Engine Audit Logger
# ----------------------------------------------------------------------------
# 목적:
#   • 병합(merge) 실행 시 MergeBatch + MergeChangeLog 감사기록 생성
#   • settings_merge 정책 및 dataset별 감사 옵션 반영
#   • OTA / BankLedger / SalesFront 등 멀티데이터셋 SSOT 호환
# ----------------------------------------------------------------------------
# 특징:
#   ✅ dry_run 모드 안전 스킵
#   ✅ dataset별 로그 구분
#   ✅ action 대소문자 표준화
#   ✅ summary 자동 계산
#   ✅ MergeBatch import 경로 수정(app.models.merge)
# ----------------------------------------------------------------------------
# 연계:
#   • app/merge_engine/repository.py → MergeAuditRepository
#   • app/core/settings_merge.py     → 병합 정책 조회
#   • app/models/merge.py            → MergeBatch / MergeChangeLog ORM
# ----------------------------------------------------------------------------
# 변경 로그:
#   v3.6 (2025-10-31)
#     ✅ MergeBatch import hotfix (audit→merge)
#     ✅ 로그 메시지 일관성 개선
# ============================================================================

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

# ✅ MergeBatch import hotfix
from app.models.merge import MergeBatch
from app.merge_engine.repository import MergeAuditRepository
from app.core import settings_merge

log = logging.getLogger("merge_audit")


# ============================================================================
# 1️⃣ 메인 엔트리
# ----------------------------------------------------------------------------
def record_merge_audit(
    db: Session,
    dataset: str,
    property_code: str,
    mode: str,
    missing_policy: str,
    source_kind: str,
    changes: List[Dict[str, Any]],
    session_id: Optional[int] = None,
    version_no: Optional[int] = None,
    dry_run: bool = False,
) -> Optional[MergeBatch]:
    """
    병합 결과를 감사 테이블에 기록합니다.
    ──────────────────────────────────────────────
    • MergeBatch 1건 + MergeChangeLog N건 생성
    • dry_run=True → 기록 스킵
    • settings_merge 정책(audit_enabled) 반영
    • 실패 시 rollback 보장
    """
    # 0️⃣ Dry-run 모드: 스킵
    if dry_run:
        log.info("[AUDIT] dry_run → skip audit (dataset=%s)", dataset)
        return None

    # 1️⃣ 정책 확인
    policy = settings_merge.get_policy(dataset)
    if not policy.get("audit_enabled", True):
        log.info("[AUDIT] audit disabled by settings (dataset=%s)", dataset)
        return None

    repo = MergeAuditRepository(db)
    batch: Optional[MergeBatch] = None

    try:
        # 2️⃣ Batch 생성
        business_date = _infer_business_date(changes)
        batch = repo.create_batch(
            dataset=dataset,
            property_code=property_code,
            business_date=business_date,
            mode=mode,
            missing_policy=missing_policy,
            source_kind=source_kind,
            session_id=session_id,
            version_no=version_no,
        )

        # 3️⃣ 변경 로그 추가
        for ch in changes:
            try:
                action = (ch.get("action") or "UPSERT").upper()
                repo.log_change(
                    batch_id=batch.id,
                    action=action,
                    key_hash=ch.get("key_hash"),
                    old_hash=ch.get("old_hash"),
                    new_hash=ch.get("new_hash"),
                    reason=ch.get("reason"),
                )
            except Exception as e:
                log.warning(f"[AUDIT] skip bad change (dataset={dataset}): {e}")

        # 4️⃣ 요약 계산
        summary = _summarize_changes(changes)

        # 5️⃣ 완료/커밋
        repo.finalize_batch(
            batch,
            status="DONE",
            record_count=summary["total"],
            notes=f"{mode} / {missing_policy} / {summary['summary']}",
        )
        repo.safe_commit()

        log.info(
            "[AUDIT] batch=%s dataset=%s property=%s total=%s DONE",
            batch.id,
            dataset,
            property_code,
            summary["total"],
        )
        return batch

    except Exception as e:
        try:
            db.rollback()
        except Exception:
            pass
        log.exception(f"[AUDIT] dataset={dataset} failed: {e}")
        raise


# ============================================================================
# 2️⃣ 내부 유틸리티
# ----------------------------------------------------------------------------
def _infer_business_date(changes: List[Dict[str, Any]]) -> str:
    """변경 목록에서 business_date 추출 (없으면 오늘 UTC)"""
    for ch in changes or []:
        payload = ch.get("payload") or {}
        if isinstance(payload, dict):
            d = payload.get("business_date")
            if d:
                return str(d)
    return datetime.utcnow().strftime("%Y-%m-%d")


def _summarize_changes(changes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """action별 insert/update/delete/noop 집계"""
    def _count(name: str) -> int:
        return len([c for c in changes if (c.get("action") or "").lower() == name])

    inserted = _count("insert")
    updated = _count("update") + _count("upsert")
    deleted = _count("delete")
    noop = _count("noop")
    total = len(changes or [])

    summary_text = (
        f"{total} changes (insert={inserted}, update={updated}, "
        f"delete={deleted}, noop={noop})"
    )
    return {
        "inserted": inserted,
        "updated": updated,
        "deleted": deleted,
        "noop": noop,
        "total": total,
        "summary": summary_text,
    }


# ============================================================================
# 3️⃣ Export
# ----------------------------------------------------------------------------
__all__ = ["record_merge_audit"]
