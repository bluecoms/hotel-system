# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/merge_engine/repository.py
# Version   : 2025-10-31 · v3.6 (SSOT Canon Map + MergeAudit Stable)
# Purpose   : Hotel Admin — Merge Engine Repository Layer
# ----------------------------------------------------------------------------
# 목적:
#   • Canon / History 테이블에 대한 CRUD 및 병합 기록 관리
#   • MergeBatch / MergeChangeLog 감사 로그 통합
#   • SSOT 엔진 기반 Canon 최신화 + History append-only 구조 유지
#   • dataset 키 기준으로 Canon/History 모델 자동 매핑
# ----------------------------------------------------------------------------
# 주요 기능:
#   ✅ CanonRepository — Canon/History UPSERT + append-only History 기록
#   ✅ MergeAuditRepository — MergeBatch, MergeChangeLog 관리
#   ✅ persist_records() — Canon + Audit 통합 반영
# ----------------------------------------------------------------------------
# 연계 모듈:
#   • app/core/settings_merge.py   → 병합 정책 조회
#   • app/core/hashing.py          → key_hash, record_hash 생성
#   • app/models/{canon,merge}.py  → ORM 정의
#   • app/merge_engine/engine.py   → 엔진 실행부
# ============================================================================

import json
import logging
from datetime import datetime, date
from typing import Any, Dict, List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

# ✅ MergeBatch / ChangeLog 은 merge.py 에서 import (순환참조 방지)
from app.models.merge import MergeBatch, MergeChangeLog
from app.models.canon import (
    RoomsStatusCanon,
    RoomsStatusHistory,
    FnbItemsCanon,
    FnbItemsHistory,
    FnbTendersCanon,
    FnbTendersHistory,
    # SalesFrontCanon, SalesFrontHistory,
    # OtaOrdersCanon, OtaOrdersHistory,
)
from app.core.hashing import make_key_hash, make_record_hash
from app.core import settings_merge

log = logging.getLogger("merge_repository")

# ============================================================================
# 1️⃣ Canon / History 모델 매핑 (dataset 기준)
# ============================================================================
CANON_MODELS: Dict[str, Tuple[Any, Any]] = {
    "rooms_status": (RoomsStatusCanon, RoomsStatusHistory),
    "fnb_items": (FnbItemsCanon, FnbItemsHistory),
    "fnb_tenders": (FnbTendersCanon, FnbTendersHistory),
    # "sales_front": (SalesFrontCanon, SalesFrontHistory),
    # "ota_orders": (OtaOrdersCanon, OtaOrdersHistory),
}

# ============================================================================
# 2️⃣ CanonRepository — Canon / History 관리
# ============================================================================
class CanonRepository:
    """Canon/History CRUD 관리 + UPSERT + append-only History 기록"""

    def __init__(self, db: Session, dataset: str = "rooms_status"):
        self.db = db
        self.dataset = dataset
        if dataset not in CANON_MODELS:
            log.warning(f"[REPO] dataset={dataset} not mapped → fallback=rooms_status")
            self.dataset = "rooms_status"
        self.CanonModel, self.HistoryModel = CANON_MODELS[self.dataset]

    # ─────────────────────────────────────────────
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

    # ─────────────────────────────────────────────
    def upsert_record(self, payload: Dict[str, Any], batch_id: int) -> Tuple[str, str]:
        """
        Canon 테이블에 UPSERT 수행
        - payload_json 비교를 통해 UPSERT / NOOP 결정
        - History는 append-only로 모든 변경 내역 보존
        """
        if self.dataset == "rooms_status":
            key_fields = ("business_date", "property_code", "room_no")
        elif self.dataset == "fnb_items":
            key_fields = ("business_date", "property_code", "item_code")
        elif self.dataset == "fnb_tenders":
            key_fields = ("business_date", "property_code", "tender_code")
        elif self.dataset == "sales_front":
            key_fields = ("business_date", "property_code", "tag")
        elif self.dataset == "ota_orders":
            key_fields = ("business_date", "property_code", "order_code")
        else:
            key_fields = ("business_date", "property_code")

        key_tuple = tuple(payload.get(k) for k in key_fields)
        key_hash = make_key_hash(key_tuple)
        record_hash = make_record_hash(payload)
        payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        valid_on = self._to_date(payload.get("business_date"))

        if not valid_on:
            raise ValueError(f"invalid business_date format: {payload.get('business_date')}")

        CanonModel, HistoryModel = self.CanonModel, self.HistoryModel
        existing = self.db.query(CanonModel).filter_by(key_hash=key_hash).first()
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
                obj = CanonModel(
                    key_hash=key_hash,
                    record_hash=record_hash,
                    valid_on=valid_on,
                    payload_json=payload_json,
                    last_batch_id=batch_id,
                    updated_at=datetime.utcnow(),
                )
                self.db.add(obj)
                action = "INSERT"

            # ✅ append-only History 기록
            hist = HistoryModel(
                key_hash=key_hash,
                record_hash=record_hash,
                valid_on=valid_on,
                payload_json=payload_json,
                source_batch_id=batch_id,
                created_at=datetime.utcnow(),
            )
            self.db.add(hist)

        except Exception as e:
            log.exception(f"[REPO] upsert_record failed (dataset={self.dataset}): {e}")
            self.db.rollback()
            raise

        return (action, key_hash)

# ============================================================================
# 3️⃣ MergeAuditRepository — MergeBatch / ChangeLog 관리
# ============================================================================
class MergeAuditRepository:
    """MergeBatch / MergeChangeLog 관리용 리포지토리"""

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
            self.db.rollback()
            log.exception(f"[REPO] create_batch failed: {e}")
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
            self.db.rollback()
            log.exception(f"[REPO] log_change failed: {e}")
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
        """안전 커밋 (에러시 rollback)"""
        try:
            self.db.commit()
        except SQLAlchemyError as e:
            self.db.rollback()
            log.exception(f"[REPO] DB Commit failed: {e}")
            raise

# ============================================================================
# 4️⃣ persist_records — Canon + Audit 통합 적용
# ============================================================================
def persist_records(db: Session, dataset: str, batch_id: int, records: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    CanonRepository + MergeAuditRepository 통합 적용
    - INSERT / UPSERT / NOOP 처리
    - ChangeLog 자동 추가
    - settings_merge 정책 반영
    """
    canon_repo = CanonRepository(db, dataset)
    audit_repo = MergeAuditRepository(db)
    policy = settings_merge.get_policy(dataset)
    missing_policy = policy.get("missing_policy", "soft_delete")

    inserted = upserted = noop = 0

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
            db.rollback()
            log.exception(f"[REPO] persist_records failed: {e}")
            raise

    if missing_policy not in ("ignore", ""):
        log.info(f"[REPO] missing_policy={missing_policy} applied (dataset={dataset})")

    try:
        audit_repo.safe_commit()
        log.info(
            "[REPO] persist_records summary dataset=%s inserted=%s upserted=%s noop=%s",
            dataset,
            inserted,
            upserted,
            noop,
        )
    except Exception:
        db.rollback()
        log.exception("[REPO] persist_records commit failed")
        raise

    return {"inserted": inserted, "upserted": upserted, "noop": noop}
