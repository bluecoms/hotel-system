# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/models/bank.py
# Version   : 2025.10-26 · v2.3 (Fix FK → properties.code · SSOT Final)
# Purpose   : Hotel Admin — Bank Models (회계/입출금/계좌/잔액)
# ----------------------------------------------------------------------------
# 목적:
#   • 은행 관련 모든 ORM 모델 정의 (계좌 · 거래 · 일마감 잔액)
#   • MasterBank(은행 코드) 및 MasterProperty(지점 코드)와 연결
#   • UploadSession / UploadedFile 기반 업로드 기록과 연동
# ----------------------------------------------------------------------------
# 구성:
#   ① BankAccount      : 계좌 기준정보 (FK → properties.code, master_banks.code)
#   ② BankTxn          : 입출금 거래 이력
#   ③ BankDailyBalance : 일자별 잔액 스냅샷
# ----------------------------------------------------------------------------
# 변경 로그:
#   v2.0 (2025-10-18)
#     ✅ 기본 ORM 구조 정비 및 SQLite 호환 인덱스 보강
#   v2.1 (2025-10-22)
#     ✅ UploadSession / UploadedFile 연계 확인 완료
#   v2.2 (2025-10-23)
#     ✅ MasterBank 연동: bank_code FK 추가 (기준정보 일원화)
#   v2.3 (2025-10-26)
#     ✅ FK 수정: master_properties → properties.code (전역 Property 기준)
#     ✅ 전역화 구조 주석 반영 (MasterProperty 전역 엔드포인트 일원화)
# ============================================================================
from __future__ import annotations
from datetime import datetime, date
from sqlalchemy import (
    Integer,
    String,
    Boolean,
    DateTime,
    Date,
    UniqueConstraint,
    Index,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base_class import Base


# ============================================================================
# ① 계좌 기준정보 (BankAccount)
# ----------------------------------------------------------------------------
#  • property_code → FK(properties.code)
#  • bank_code → FK(master_banks.code)
#  • 계좌명/은행명은 표시용이며 기준정보 테이블에서 참조됨
# ============================================================================
class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_code: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("properties.code"),  # ✅ 전역화된 MasterProperty(FK 수정)
        index=True,
        default="MOP",
        comment="지점 코드 (FK: properties.code)",
    )
    account_code: Mapped[str] = mapped_column(
        String(64),
        index=True,
        nullable=False,
        comment="계좌 코드 (예: NH-301-XXXX-XXXX)",
    )
    bank_code: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("master_banks.code"),
        index=True,
        nullable=True,
        comment="은행 코드 (FK: master_banks.code)",
    )
    bank_name: Mapped[str] = mapped_column(String(64), default="", comment="표시용 은행명")
    account_name: Mapped[str] = mapped_column(String(128), default="", comment="표시용 계좌명")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="활성 여부")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True, comment="등록일시 (UTC)"
    )

    __table_args__ = (
        UniqueConstraint("property_code", "account_code", name="uq_bank_account"),
        {"extend_existing": True},
    )

    def __repr__(self):
        return f"<BankAccount(code={self.account_code}, bank={self.bank_code or self.bank_name})>"


# ============================================================================
# ② 거래 이력 (BankTxn)
# ----------------------------------------------------------------------------
#  • upload_sessions와 간접 연계 (session_id)
#  • business_date = 업로드 기준일
#  • direction = IN(입금)/OUT(출금)
# ============================================================================
class BankTxn(Base):
    __tablename__ = "bank_txns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_code: Mapped[str] = mapped_column(String(20), index=True, default="MOP")
    account_code: Mapped[str] = mapped_column(String(64), index=True)
    business_date: Mapped[str] = mapped_column(String(10), index=True, comment="업로드 기준일 (YYYY-MM-DD)")
    txn_date: Mapped[Date] = mapped_column(Date, index=True, comment="거래일자")
    txn_time: Mapped[str] = mapped_column(String(8), default="", comment="거래시간 (HH:MM:SS)")
    direction: Mapped[str] = mapped_column(String(3), index=True, comment="거래 방향 (IN/OUT)")
    amount: Mapped[int] = mapped_column(Integer, index=True, default=0, comment="거래 금액 (원화)")
    balance: Mapped[int] = mapped_column(Integer, default=0, comment="잔액 (파일 기반)")
    desc: Mapped[str] = mapped_column(String(255), default="", comment="적요")
    counterparty: Mapped[str] = mapped_column(String(255), default="", comment="거래처/상대계좌명")
    memo: Mapped[str] = mapped_column(String(255), default="", comment="메모")
    raw_ref: Mapped[str] = mapped_column(String(255), default="", comment="거래번호/문서번호 등")
    dataset: Mapped[str] = mapped_column(String(40), index=True, default="", comment="데이터셋 태그 (예: pay_settlement)")
    session_id: Mapped[int] = mapped_column(Integer, index=True, default=0, comment="업로드 세션 ID (upload_sessions.id)")
    version_no: Mapped[int] = mapped_column(Integer, index=True, default=0, comment="버전 번호")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True, comment="등록일시 (UTC)")

    __table_args__ = (
        Index(
            "ix_bank_txn_key",
            "property_code",
            "account_code",
            "txn_date",
            "direction",
        ),
        {"extend_existing": True},
    )

    def __repr__(self):
        return f"<BankTxn(date={self.txn_date}, acct={self.account_code}, amt={self.amount})>"


# ============================================================================
# ③ 일자별 잔액 스냅샷 (BankDailyBalance)
# ----------------------------------------------------------------------------
#  • property_code + account_code + date = 유니크 키
#  • closing_balance = 일마감 기준 잔액
# ============================================================================
class BankDailyBalance(Base):
    __tablename__ = "bank_daily_balances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_code: Mapped[str] = mapped_column(String(20), index=True, default="MOP", comment="지점 코드")
    account_code: Mapped[str] = mapped_column(String(64), index=True, comment="계좌 코드")
    date: Mapped[date] = mapped_column(Date, index=True, comment="일자 (YYYY-MM-DD)")
    closing_balance: Mapped[int] = mapped_column(Integer, default=0, comment="일마감 잔액 (파일 잔액 기준 또는 산출)")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True, comment="등록일시 (UTC)")

    __table_args__ = (
        UniqueConstraint(
            "property_code", "account_code", "date", name="uq_bank_daily_balance"
        ),
        {"extend_existing": True},
    )

    def __repr__(self):
        return f"<BankDailyBalance({self.date}, acct={self.account_code}, bal={self.closing_balance})>"
