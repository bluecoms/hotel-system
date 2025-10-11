# app/merge_engine/audit.py
# -*- coding: utf-8 -*-
"""
Merge Engine Audit (Phase 2)
──────────────────────────────────────────────
- 병합 수행 시 MergeBatch + MergeChangeLog 기록
- repository.py 의 MergeAuditRepository 래퍼
- 모든 변경 로그를 안전하게 커밋하고, 실패 시 rollback
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.audit import MergeBatch
from app.merge_engine.repository import MergeAuditRepository

log = logging.getLogger(__name__)


# ───────────────────────────────────────────────
# 메인 엔트리
# ───────────────────────────────────────────────
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
) -> MergeBatch:
    """
    병합 수행 결과를 감사 테이블에 기록합니다.
    - MergeBatch 1건 생성 + MergeChangeLog N건 추가
    - repository.safe_commit()으로 트랜잭션 보장
    - 오류 발생 시 전체 rollback

    Args:
        db: SQLAlchemy Session
        dataset: 데이터셋 명 (예: rooms_status, sales_front ...)
        property_code: 호텔 코드 (예: MOP)
        mode: append/snapshot
        missing_policy: 누락 정책 (ignore / soft_delete / hard_delete)
        source_kind: daily / weekly / monthly / full
        changes: [{action, key_hash, old_hash, new_hash, reason, payload}]
        session_id: 업로드 세션 ID (선택)
        version_no: 버전 번호 (선택)
    Returns:
        MergeBatch: 생성된 배치 ORM 객체
    """
    repo = MergeAuditRepository(db)
    try:
        # 1️⃣ 배치 생성
        batch = repo.create_batch(
            dataset=dataset,
            property_code=property_code,
            business_date=_infer_business_date(changes),
            mode=mode,
            missing_policy=missing_policy,
            source_kind=source_kind,
            session_id=session_id,
            version_no=version_no,
        )

        # 2️⃣ 변경 로그 기록
        for ch in changes:
            try:
                repo.log_change(
                    batch_id=batch.id,
                    action=ch.get("action", "UPSERT"),
                    key_hash=ch.get("key_hash"),
                    old_hash=ch.get("old_hash"),
                    new_hash=ch.get("new_hash"),
                    reason=ch.get("reason"),
                )
            except Exception as e:
                # 개별 로그 오류는 전체 배치 실패로 간주하지 않음
                log.warning(f"[AUDIT] skip bad change: {e}")

        # 3️⃣ 배치 완료 및 커밋
        repo.finalize_batch(
            batch,
            status="DONE",
            record_count=len(changes),
            notes=f"{mode} with {missing_policy} policy",
        )
        repo.safe_commit()
        log.info(f"[AUDIT] batch={batch.id} dataset={dataset} changes={len(changes)} complete")
        return batch

    except Exception as e:
        db.rollback()
        log.exception(f"[AUDIT] record_merge_audit failed: {e}")
        raise


# ───────────────────────────────────────────────
# 내부 유틸
# ───────────────────────────────────────────────
def _infer_business_date(changes: List[Dict[str, Any]]) -> str:
    """
    변경 목록에서 business_date 추출 (없으면 오늘 날짜로 대체)
    """
    for ch in changes:
        payload = ch.get("payload") or {}
        if isinstance(payload, dict):
            d = payload.get("business_date")
            if d:
                return str(d)
    return datetime.utcnow().strftime("%Y-%m-%d")


__all__ = ["record_merge_audit"]
