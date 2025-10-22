# ============================================================================
# File      : app/schemas/bank.py
# Version   : 2025.10-23 · v2.0 (SSOT Stable / Ledger DTO 정비)
# Purpose   : Hotel Admin — Bank Ledger Schemas (회계/입출금 전송 객체)
# ----------------------------------------------------------------------------
# 목적:
#   • 은행 입출금 관련 API의 데이터 스키마 정의
#   • DB 모델(BankAccount / BankTxn)과 연동되는 I/O용 Pydantic 모델
#   • ✅ BankLedgerIn  : 프런트/업로드 입력용 DTO
#   • ✅ BankLedgerOut : 조회/응답용 DTO (from_attributes=True)
# ----------------------------------------------------------------------------
# 설계 원칙:
#   • 모든 필드명은 DB 컬럼명과 일치
#   • ORM 연동을 위해 from_attributes=True 지정
#   • timestamp(datetime) 필드는 ISO8601 문자열로 자동 직렬화
#   • SSOT(단일 소스) 구조 유지: router/model/schema 일치
# ============================================================================
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

# ─────────────────────────────────────────────
# 입력 DTO (입출금 기록 생성용)
# ─────────────────────────────────────────────
class BankLedgerIn(BaseModel):
    """입출금 생성 입력용 스키마"""
    account_code: str                   # 계좌 코드
    property_code: str                  # 지점 코드
    amount: float                       # 금액 (양수/음수 모두 허용)
    memo: Optional[str] = ""            # 비고 또는 메모


# ─────────────────────────────────────────────
# 출력 DTO (입출금 조회용)
# ─────────────────────────────────────────────
class BankLedgerOut(BankLedgerIn):
    """입출금 조회/응답용 스키마"""
    model_config = ConfigDict(from_attributes=True)
    id: int                             # 기본 키
    created_at: datetime                # 생성 일시 (ISO8601 직렬화)
