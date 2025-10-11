# app/merge_engine/repository.py
# -*- coding: utf-8 -*-
"""
Merge Engine Repository Layer (Phase 2)
──────────────────────────────────────────────
- Canon / History CRUD
- MergeBatch, MergeChangeLog 기록 관리
- SSOT 통합 반영: Canon 최신화 + History append-only + ChangeLog 로깅
"""
import json
import logging
from datetime import datetime, date
from typing import Any, Dict, List, Tuple, Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.canon import RoomsStatusCanon, RoomsStatusHistory
from app.models.audit import MergeBatch, MergeChangeLog
from app.core.hashing import make_key_hash, make_record_hash

log = logging.getLogger(__name__)


# ───────────────────────────────────────────────
# Canon / History 레코드 Upsert
# ───────────────────────────────────────────────
class CanonRepository:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _to_date(value: Any) -> Optional[date]:
        """문자열 YYYY-MM-DD → datetime.date 변환"""
        if isinstance(value, date):
            return value
        if isinstance(value, str) and len(value) == 10:
            try:
                return datetime.strptime(value, "%Y-%m-%d").date()
            except Exception:
                return None
        return None

    def upsert_record(self, payload: Dict[str, Any], batch_id: int) -> Tuple[str, str]:
        """
        Canon 테이블에 UPSERT 수행
        - payload_json 기반 비교
        """
        key_tuple = (
            payload.get("business_date"),
            payload.get("property_code"),
            payload.get("room_no"),
        )
        key_hash = make_key_hash(key_tuple)
        record_hash = make_record_hash(payload)
        payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        valid_on = self._to_date(payload.get("business_date"))

        if not valid_on:
            log.warning(f"[REPO] invalid business_date: {payload.get('business_date')}")
            raise ValueError("invalid business_date format")

        existing = self.db.query(RoomsStatusCanon).filter_by(key_hash=key_hash).first()
        action = "NOOP"

        try:
            if existing:
                if existing.record_hash == record_hash:
                    action = "NOOP"
                else:
                    existing.record_hash = record_hash
                    existing.payload_json = payload_json
                    existing.updated_at = datetime.utcnow()
                    existing.last_batch_id = batch_id
                    action = "UPSERT"
            else:
                obj = RoomsStatusCanon(
                    key_hash=key_hash,
                    record_hash=record_hash,
                    valid_on=valid_on,
                    payload_json=payload_json,
                    last_batch_id=batch_id,
                    updated_at=datetime.utcnow(),
                )
                self.db.add(obj)
                action = "INSERT"

            # History append-only
            hist = RoomsStatusHistory(
                key_hash=key_hash,
                record_hash=record_hash,
                valid_on=valid_on,
                payload_json=payload_json,
                source_batch_id=batch_id,
                created_at=datetime.utcnow(),
            )
            self.db.add(hist)

        except Exception as e:
            log.exception(f"[REPO] upsert_record failed: {e}")
            self.db.rollback()
            raise

        return (action, key_hash)


# ───────────────────────────────────────────────
# Merge Batch + ChangeLog Repository
# ───────────────────────────────────────────────
class MergeAuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_batch(
        self,
        dataset: str,
        property_code: str,
        business_date: str,
        mode: str,
        missing_policy: str,
        source_kind: str,
        session_id: Optional[int] = None,
        version_no: Optional[int] = None,
    ) -> MergeBatch:
        """배치 헤더 생성"""
        try:
            batch = MergeBatch(
                dataset=dataset,
                property_code=property_code,
                business_date=business_date,
                mode=mode,
                missing_policy=missing_policy,
                source_kind=source_kind,
                session_id=session_id,
                version_no=version_no,
                status="PENDING",
                created_at=datetime.utcnow(),
            )
            self.db.add(batch)
            self.db.flush()
            log.info(f"[REPO] created batch id={batch.id} dataset={dataset}")
            return batch
        except Exception as e:
            log.exception(f"[REPO] create_batch failed: {e}")
            self.db.rollback()
            raise

    def log_change(
        self,
        batch_id: int,
        action: str,
        key_hash: str,
        old_hash: Optional[str] = None,
        new_hash: Optional[str] = None,
        reason: Optional[str] = None,
    ):
        """변경 로그 1건 기록"""
        try:
            rec = MergeChangeLog(
                batch_id=batch_id,
                action=action,
                key_hash=key_hash,
                old_hash=old_hash,
                new_hash=new_hash,
                reason=reason,
                created_at=datetime.utcnow(),
            )
            self.db.add(rec)
        except Exception as e:
            log.exception(f"[REPO] log_change failed: {e}")
            self.db.rollback()
            raise

    def finalize_batch(
        self,
        batch: MergeBatch,
        *,
        status: str = "DONE",
        record_count: int = 0,
        notes: Optional[str] = None,
    ):
        """배치 완료 + 상태/건수/노트 병합 후 커밋"""
        batch.status = status
        batch.record_count = record_count
        if notes:
            batch.notes = (batch.notes + "\n" if batch.notes else "") + str(notes)
        batch.completed_at = datetime.utcnow()
        try:
            self.db.commit()
            log.info(f"[REPO] finalize_batch id={batch.id} status={status}")
        except SQLAlchemyError as e:
            self.db.rollback()
            log.exception(f"[REPO] finalize_batch failed: {e}")
            raise

    def safe_commit(self):
        try:
            self.db.commit()
        except SQLAlchemyError as e:
            self.db.rollback()
            log.exception(f"[REPO] DB Commit failed: {e}")
            raise


# ───────────────────────────────────────────────
# 고수준 헬퍼: Canon/History + ChangeLog 통합
# ───────────────────────────────────────────────
def persist_records(db: Session, batch_id: int, records: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    CanonRepository + MergeAuditRepository 통합 적용
    - INSERT / UPSERT / NOOP 모두 처리
    - ChangeLog 자동 추가
    """
    canon_repo = CanonRepository(db)
    audit_repo = MergeAuditRepository(db)

    inserted = 0
    upserted = 0
    noop = 0

    for rec in records:
        try:
            action, key_hash = canon_repo.upsert_record(rec, batch_id)
            if action == "INSERT":
                inserted += 1
                audit_repo.log_change(batch_id, "INSERT", key_hash, None, make_record_hash(rec))
            elif action == "UPSERT":
                upserted += 1
                audit_repo.log_change(batch_id, "UPSERT", key_hash, None, make_record_hash(rec))
            else:
                noop += 1
        except Exception as e:
            log.exception(f"[REPO] persist_records failed on record: {e}")
            db.rollback()
            raise

    try:
        audit_repo.safe_commit()
        log.info(
            "[REPO] persist_records summary: inserted=%s upserted=%s noop=%s",
            inserted,
            upserted,
            noop,
        )
    except Exception as e:
        db.rollback()
        log.exception("[REPO] persist_records commit failed")
        raise

    return {"inserted": inserted, "upserted": upserted, "noop": noop}
