# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/schemas/master_ota_channel.py
# Version   : 2025.10-26 · v1.1 (Fixed Config · SSOT Verified)
# Purpose   : Hotel Admin — Master OTA Channel Schema
# ----------------------------------------------------------------------------
# 목적:
#   • OTA 채널(Booking.com, Agoda, Expedia 등) 기준정보 데이터 검증/직렬화
#   • 입력용(In)과 출력용(Out)을 명확히 분리하여 CRUD 안정성 확보
# ----------------------------------------------------------------------------
# 모델 대응:
#   • app/models/master_ota_channel.py → MasterOtaChannel
# ----------------------------------------------------------------------------
# 필드 정의:
#   - id          : Primary Key (출력 전용)
#   - code        : 채널 코드(대문자 영문, 유니크)
#   - name        : 채널 이름(표시용)
#   - is_active   : 활성 상태
#   - order_no    : 정렬 순서(선택)
#   - created_at  : 생성일시(출력 전용)
#   - updated_at  : 수정일시(출력 전용)
# ----------------------------------------------------------------------------
# 참고:
#   • Pydantic v2 대응 — orm_mode 대신 from_attributes 사용
#   • Config 클래스 들여쓰기 주의 (IndentError 방지)
# ============================================================================
from __future__ import annotations

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, constr


# ─────────────────────────────────────────────
# 1️⃣ Base (공통 필드)
# ─────────────────────────────────────────────
class MasterOtaChannelBase(BaseModel):
    code: constr(strip_whitespace=True, min_length=2, max_length=50) = Field(
        ..., description="채널 코드 (대문자 영문, 유니크)"
    )
    name: constr(strip_whitespace=True, min_length=1, max_length=100) = Field(
        ..., description="채널 이름 (표시용)"
    )
    is_active: bool = Field(True, description="활성 여부")
    order_no: Optional[int] = Field(None, description="정렬 순서 (선택)")


# ─────────────────────────────────────────────
# 2️⃣ 입력용 (Create / Update)
# ─────────────────────────────────────────────
class MasterOtaChannelIn(MasterOtaChannelBase):
    """입력용 스키마"""
    pass


# ─────────────────────────────────────────────
# 3️⃣ 출력용 (Read)
# ─────────────────────────────────────────────
class MasterOtaChannelOut(MasterOtaChannelBase):
    """출력용 스키마"""
    id: int = Field(..., description="PK")
    created_at: Optional[datetime] = Field(None, description="생성일시")
    updated_at: Optional[datetime] = Field(None, description="수정일시")

    class Config:
        from_attributes = True
