# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/schemas/master_bank.py
# Version   : 2025.10-28 · v1.6 (Hotfix · country_code Optional · ValidationError Fix)
# Purpose   : Hotel Admin — Master Banks Schema (/api/master/banks)
# ----------------------------------------------------------------------------
# 목적:
#   • 은행(Bank) 기준정보용 Pydantic 스키마 정의 (SSOT 최종형)
#   • 업그레이드된 MasterBank 모델(order_no, country_code, meta)에 완전 대응
#   • Python 3.9 + Pydantic v2 완전 호환 (ClassVar + ConfigDict)
# ----------------------------------------------------------------------------
# 구성:
#   • MasterBankBase : 공통 필드(code, name, alias, country_code, order_no, is_active)
#   • MasterBankIn   : 생성/수정 입력용
#   • MasterBankOut  : 조회/응답용 (ORM 변환 지원)
#   • MasterBankOption : v-select 옵션용(title/value)
# ----------------------------------------------------------------------------
# 연계:
#   • Model : app/models/master_bank.MasterBank
#   • Router: app/routers/master_bank.py → /api/master/banks CRUD + /options
#   • Front : BankTable.vue, DialogEmployeeForm.vue 등 v-select 옵션 활용
# ----------------------------------------------------------------------------
# 변경 로그:
#   v1.3 (2025-10-24) · Initial Stable (ClassVar ConfigDict 적용)
#   v1.5 (2025-10-28) · Upgrade:
#       ✅ country_code / order_no / meta 필드 추가
#       ✅ MasterBankOption 스키마 추가
#       ✅ 주석/필드 설명 보강
#   v1.6 (2025-10-30) · Hotfix:
#       ✅ FastAPI ResponseValidationError 해결
#       ✅ country_code: Optional[str] = Field(None, ...) 로 변경
#       ✅ None 입력 허용 및 기본값 KR 유지
# ============================================================================
from datetime import datetime
from typing import Optional, ClassVar, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

# ─────────────────────────────────────────────
# 1️⃣ 기본 스키마 (공통 필드)
# ─────────────────────────────────────────────
class MasterBankBase(BaseModel):
    """은행 기준정보 공통 필드"""

    code: str = Field(..., description="은행 코드 (예: NH, WR, KB, IBK 등)")
    name: str = Field(..., description="은행명 (예: 농협은행, 국민은행 등)")
    alias: Optional[str] = Field("", description="약칭 또는 표시명 (예: 농협, 국민)")
    # ✅ None 허용으로 ResponseValidationError 방지
    country_code: Optional[str] = Field(
        "KR", description="국가 코드 (예: KR, JP, US). None 허용"
    )
    order_no: Optional[int] = Field(0, description="정렬 순서 (낮을수록 우선)")
    is_active: bool = Field(True, description="활성 여부 (False 시 /options에서 제외)")
    meta: Optional[Dict[str, Any]] = Field(
        None,
        description="부가정보(JSON) — 예: {'bic': 'KOEXKRSE', 'logo_url': '...'}",
    )


# ─────────────────────────────────────────────
# 2️⃣ 생성/수정 입력 스키마
# ─────────────────────────────────────────────
class MasterBankIn(MasterBankBase):
    """은행 생성/수정 입력 스키마"""
    pass


# ─────────────────────────────────────────────
# 3️⃣ 출력/응답 스키마 (ORM 변환 지원)
# ─────────────────────────────────────────────
class MasterBankOut(MasterBankBase):
    """은행 출력(조회) 스키마"""
    id: int = Field(..., description="PK")
    created_at: datetime = Field(..., description="등록일시 (UTC)")

    # ✅ Python 3.9 + Pydantic v2 완전 호환 (ClassVar 명시)
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────
# 4️⃣ v-select 옵션 스키마
# ─────────────────────────────────────────────
class MasterBankOption(BaseModel):
    """은행 옵션 (v-select용)"""
    value: str = Field(..., description="은행 코드")
    title: str = Field(..., description="은행명 또는 표시명")

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)
