# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/schemas/master_hk_unit_rule.py
# Version   : 2025-11-09 · v1.2 (order_no 확장 · SSOT 완전판)
# Purpose   : Hotel Admin — MasterHkUnitRule Pydantic 스키마
# ----------------------------------------------------------------------------
# 목적:
#   • 하우스키핑 유닛 계산 기준정보 스키마 정의
#   • 룸타입·업무 조건별 유닛 가중치 관리 (예: 객실청소=1.0, 재실청소=0.3 등)
#   • MasterTable의 드래그 정렬 기능(order_no)과 완전 호환
# ----------------------------------------------------------------------------
# 구성:
#   • HkUnitRuleBase   → 공통 필드 정의
#   • HkUnitRuleCreate → 신규 등록용
#   • HkUnitRuleUpdate → 수정용 (부분 업데이트)
#   • HkUnitRuleOut    → 출력용 (ORM 직렬화)
# ----------------------------------------------------------------------------
# 필드 설명:
#   - condition_code : 규칙 코드 (예: ROOM_STD, ROOM_DLX, MOVE_FLOOR)
#   - description    : 규칙 설명
#   - unit_value     : 단위 값 (기본 1.0)
#   - order_no       : 정렬 순서 (드래그 정렬용)
#   - is_active      : 활성 여부
# ----------------------------------------------------------------------------
# 연계:
#   • models.master_hk_unit_rule.MasterHkUnitRule
#   • routers.master_hk_unit_rule (CRUD + order_no)
#   • 프런트 MasterData.vue → 운영 기준정보 탭
# ============================================================================

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


# ─────────────────────────────────────────────
# 공통 필드 (Base)
# ─────────────────────────────────────────────
class HkUnitRuleBase(BaseModel):
    """공통 필드 — 입력/출력 공용"""

    model_config = ConfigDict(extra="ignore")

    condition_code: str = Field(..., description="규칙 코드 (예: ROOM_STD, ROOM_DLX, MOVE_FLOOR)")
    description: str = Field(..., description="규칙 설명 (예: 기본 객실 청소, 재실 청소 등)")
    unit_value: float = Field(1.0, description="유닛 단위 값 (예: 1.0, 0.3)")
    order_no: int = Field(0, description="정렬 순서 (드래그 정렬용)")
    is_active: bool = Field(True, description="활성 여부")


# ─────────────────────────────────────────────
# 신규 등록용 (POST)
# ─────────────────────────────────────────────
class HkUnitRuleCreate(HkUnitRuleBase):
    """신규 등록 입력용"""
    pass


# ─────────────────────────────────────────────
# 수정용 (PATCH/PUT)
# ─────────────────────────────────────────────
class HkUnitRuleUpdate(BaseModel):
    """부분 수정 입력용"""

    model_config = ConfigDict(extra="ignore")

    description: Optional[str] = Field(None, description="규칙 설명")
    unit_value: Optional[float] = Field(None, description="유닛 단위 값")
    order_no: Optional[int] = Field(None, description="정렬 순서")
    is_active: Optional[bool] = Field(None, description="활성 여부")


# ─────────────────────────────────────────────
# 출력용 (GET 응답)
# ─────────────────────────────────────────────
class HkUnitRuleOut(HkUnitRuleBase):
    """조회/출력용"""

    id: int = Field(..., description="고유 ID")
    created_at: datetime = Field(..., description="생성일시 (UTC)")
    updated_at: datetime = Field(..., description="수정일시 (UTC)")

    model_config = ConfigDict(from_attributes=True, extra="ignore")


# ============================================================================
# ✅ EOF — app/schemas/master_hk_unit_rule.py (v1.2 · order_no 확장판)
# ============================================================================
