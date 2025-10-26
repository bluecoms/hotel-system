# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/schemas/master_ota_channel.py
# Version   : 2025.10-31 · v1.2 (SSOT Final · Stable Config)
# Purpose   : Hotel Admin — Master OTA Channel Schema
# ----------------------------------------------------------------------------
# 목적:
#   • OTA 채널(Booking.com, Agoda, Expedia 등) 기준정보 데이터 검증/직렬화
#   • 입력용(In)과 출력용(Out)을 분리하여 CRUD 안정성 확보
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
#   • Pydantic v2 대응 — orm_mode → from_attributes (ConfigDict 기반)
#   • 코드/필드 들여쓰기 및 타입 주석 일원화 (SSOT 형식 통일)
# ============================================================================
from __future__ import annotations
from typing import Optional, ClassVar
from datetime import datetime
from pydantic import BaseModel, Field, constr, ConfigDict


# ─────────────────────────────────────────────
# 1️⃣ Base (공통 필드)
# ─────────────────────────────────────────────
class MasterOtaChannelBase(BaseModel):
    """OTA 채널 공통 필드"""
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
    """OTA 채널 생성/수정 입력 스키마"""
    pass


# ─────────────────────────────────────────────
# 3️⃣ 출력용 (조회/응답)
# ─────────────────────────────────────────────
class MasterOtaChannelOut(MasterOtaChannelBase):
    """OTA 채널 조회/응답 스키마"""
    id: int = Field(..., description="PK")
    created_at: Optional[datetime] = Field(None, description="생성일시")
    updated_at: Optional[datetime] = Field(None, description="수정일시")

    # ✅ ORM 변환 지원
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)
