# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/models/canon.py
# Version   : 2025.10-30 · v3.6 (SSOT Final · Banking/OTA Extended)
# Purpose   : Hotel Admin — Canon/History Models (단일 진실 원천 · SSOT)
# ----------------------------------------------------------------------------
# 목적:
#   • 데이터 정제/병합 엔진(SSOT Merge Engine)의 Canon·History 모델 정의
#   • Canon: 최신 상태(Last Snapshot)
#   • History: Append-only 변경 이력(불변성 보장)
# ----------------------------------------------------------------------------
# 구성:
#   ① 공통 베이스 믹스인 (CanonBase / HistoryBase)
#   ② RoomsStatusCanon / History      → 객실 상태
#   ③ FnbItemsCanon / History         → FNB 상품별 매출
#   ④ FnbTendersCanon / History       → FNB 결제수단별 매출
#   ⑤ SalesFrontCanon / History       → 전면 매출
#   ⑥ ExpensesCanon / History         → 지출 내역
#   ⑦ BankLedgerCanon / History       → 입출금 내역
#   ⑧ OtaOrdersCanon / History        → OTA 예약 내역
# ----------------------------------------------------------------------------
# 특징:
#   ✅ dataset 이름으로 자동 탐색 (엔진 자동 매핑)
#   ✅ key_hash / record_hash 기반 무결성 보장
#   ✅ MergeBatch(FK) 연계로 감사 추적 지원
# ============================================================================
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Date, DateTime, Text,
    ForeignKey, Index, UniqueConstraint,
)
from app.db.base_class import Base


# ============================================================================
# 1️⃣ 공통 베이스 믹스인
# ----------------------------------------------------------------------------
class CanonBase:
    """SSOT Canon (최신 상태) 기본 필드 정의"""
    id = Column(Integer, primary_key=True)
    key_hash = Column(String(64), unique=True, nullable=False, index=True)
    record_hash = Column(String(64), nullable=False, index=True)
    valid_on = Column(Date, nullable=False)  # business_date
    payload_json = Column(Text, nullable=False)

    last_batch_id = Column(
        Integer,
        ForeignKey("merge_batches.id", ondelete="SET NULL"),
        nullable=True,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class HistoryBase:
    """SSOT History (변경 이력) 기본 필드 정의"""
    id = Column(Integer, primary_key=True)
    key_hash = Column(String(64), nullable=False, index=True)
    record_hash = Column(String(64), nullable=False, index=True)
    valid_on = Column(Date, nullable=False)
    payload_json = Column(Text, nullable=False)

    source_batch_id = Column(
        Integer,
        ForeignKey("merge_batches.id", ondelete="CASCADE"),
        nullable=True,
    )

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


# ============================================================================
# 2️⃣ Rooms Status
# ============================================================================
class RoomsStatusCanon(Base, CanonBase):
    __tablename__ = "rooms_status_canon"
    __table_args__ = (
        UniqueConstraint("key_hash", name="uq_rooms_status_canon_key_hash"),
        Index("ix_rooms_status_canon_valid_on", "valid_on"),
    )


class RoomsStatusHistory(Base, HistoryBase):
    __tablename__ = "rooms_status_history"
    __table_args__ = (
        Index("ix_rooms_status_history_valid_on", "valid_on"),
        Index("ix_rooms_status_history_batch", "source_batch_id"),
    )


# ============================================================================
# 3️⃣ FNB Items
# ============================================================================
class FnbItemsCanon(Base, CanonBase):
    __tablename__ = "fnb_items_canon"
    __table_args__ = (
        UniqueConstraint("key_hash", name="uq_fnb_items_canon_key_hash"),
        Index("ix_fnb_items_canon_valid_on", "valid_on"),
    )


class FnbItemsHistory(Base, HistoryBase):
    __tablename__ = "fnb_items_history"
    __table_args__ = (
        Index("ix_fnb_items_history_valid_on", "valid_on"),
        Index("ix_fnb_items_history_batch", "source_batch_id"),
    )


# ============================================================================
# 4️⃣ FNB Tenders
# ============================================================================
class FnbTendersCanon(Base, CanonBase):
    __tablename__ = "fnb_tenders_canon"
    __table_args__ = (
        UniqueConstraint("key_hash", name="uq_fnb_tenders_canon_key_hash"),
        Index("ix_fnb_tenders_canon_valid_on", "valid_on"),
    )


class FnbTendersHistory(Base, HistoryBase):
    __tablename__ = "fnb_tenders_history"
    __table_args__ = (
        Index("ix_fnb_tenders_history_valid_on", "valid_on"),
        Index("ix_fnb_tenders_history_batch", "source_batch_id"),
    )


# ============================================================================
# 5️⃣ Sales Front (전면 매출)
# ============================================================================
class SalesFrontCanon(Base, CanonBase):
    __tablename__ = "sales_front_canon"
    __table_args__ = (
        UniqueConstraint("key_hash", name="uq_sales_front_canon_key_hash"),
        Index("ix_sales_front_canon_valid_on", "valid_on"),
    )


class SalesFrontHistory(Base, HistoryBase):
    __tablename__ = "sales_front_history"
    __table_args__ = (
        Index("ix_sales_front_history_valid_on", "valid_on"),
        Index("ix_sales_front_history_batch", "source_batch_id"),
    )


# ============================================================================
# 6️⃣ Expenses (지출 내역)
# ============================================================================
class ExpensesCanon(Base, CanonBase):
    __tablename__ = "expenses_canon"
    __table_args__ = (
        UniqueConstraint("key_hash", name="uq_expenses_canon_key_hash"),
        Index("ix_expenses_canon_valid_on", "valid_on"),
    )


class ExpensesHistory(Base, HistoryBase):
    __tablename__ = "expenses_history"
    __table_args__ = (
        Index("ix_expenses_history_valid_on", "valid_on"),
        Index("ix_expenses_history_batch", "source_batch_id"),
    )


# ============================================================================
# 7️⃣ Bank Ledger (입출금 내역)
# ============================================================================
class BankLedgerCanon(Base, CanonBase):
    __tablename__ = "bank_ledger_canon"
    __table_args__ = (
        UniqueConstraint("key_hash", name="uq_bank_ledger_canon_key_hash"),
        Index("ix_bank_ledger_canon_valid_on", "valid_on"),
    )


class BankLedgerHistory(Base, HistoryBase):
    __tablename__ = "bank_ledger_history"
    __table_args__ = (
        Index("ix_bank_ledger_history_valid_on", "valid_on"),
        Index("ix_bank_ledger_history_batch", "source_batch_id"),
    )


# ============================================================================
# 8️⃣ OTA Orders (OTA 예약 내역)
# ============================================================================
class OtaOrdersCanon(Base, CanonBase):
    __tablename__ = "ota_orders_canon"
    __table_args__ = (
        UniqueConstraint("key_hash", name="uq_ota_orders_canon_key_hash"),
        Index("ix_ota_orders_canon_valid_on", "valid_on"),
    )


class OtaOrdersHistory(Base, HistoryBase):
    __tablename__ = "ota_orders_history"
    __table_args__ = (
        Index("ix_ota_orders_history_valid_on", "valid_on"),
        Index("ix_ota_orders_history_batch", "source_batch_id"),
    )


# ============================================================================
# 9️⃣ Export 목록
# ============================================================================
__all__ = [
    "RoomsStatusCanon", "RoomsStatusHistory",
    "FnbItemsCanon", "FnbItemsHistory",
    "FnbTendersCanon", "FnbTendersHistory",
    "SalesFrontCanon", "SalesFrontHistory",
    "ExpensesCanon", "ExpensesHistory",
    "BankLedgerCanon", "BankLedgerHistory",
    "OtaOrdersCanon", "OtaOrdersHistory",
]
