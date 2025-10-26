# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/schemas/master_title.py
# Version   : 2025.10-30 · v2.1 (Pydantic v2 Final · ORM 변환/주석 정비)
# Purpose   : Hotel Admin — Master Titles Schema (/api/master/titles)
# ----------------------------------------------------------------------------
# 목적:
#   • 관리자 화면에서 직책(Titles) 기준정보를 CRUD 관리
#   • 부서(Departments), 직급(Ranks), 직위(Positions) 등과 함께
#     /api/master 네임스페이스 하위 통합 관리
# ----------------------------------------------------------------------------
# 주요 필드:
#   • code       : 직책 코드 (unique)
#   • name       : 직책명 (예: 프런트매니저, 하우스키퍼)
#   • salary     : 기본급 (Numeric 12,2)
#   • order_no   : 정렬 순서 (UI 정렬용)
#   • is_active  : 사용 여부
#   • created_at : 생성 시각 (UTC)
# ----------------------------------------------------------------------------
# 스키마 구성:
#   • MasterTitleBase    : 공통 필드 정의
#   • MasterTitleIn      : 생성/수정 입력 스키마
#   • MasterTitleOut     : 조회/응답 스키마 (ORM 변환 허용)
#   • MasterTitleReorder : 순서 재정렬 요청용
# ----------------------------------------------------------------------------
# 변경 내역 (v2.1)
#   ✅ Pydantic v2 대응 — .model_config / from_attributes 적용
#   ✅ Field 설명 추가 및 기본값 명시
#   ✅ ORM 변환 안정화 (SQLAlchemy 호환 검증)
#   ✅ 타입 힌트 명확화 (Optional / List)
# ============================================================================

from datetime import datetime
from typing import Optional, List, ClassVar
from pydantic import BaseModel, Field, ConfigDict

# ============================================================================
# 1️⃣ 공통 스키마
# ============================================================================
class MasterTitleBase(BaseModel):
    """직책 기준정보 공통 필드"""

    code: str = Field(..., description="직책 코드 (unique)")
    name: str = Field(..., description="직책명 (예: 프런트매니저, 하우스키퍼)")
    salary: Optional[float] = Field(None, description="기본급 (원 단위)")
    order_no: Optional[int] = Field(0, description="정렬 순서 (낮을수록 상단)")
    is_active: bool = Field(True, description="활성 여부(True=사용중)")

# ============================================================================
# 2️⃣ 생성/수정 입력용
# ============================================================================
class MasterTitleIn(MasterTitleBase):
    """직책 생성/수정 입력 스키마"""
    pass

# ============================================================================
# 3️⃣ 조회/응답용 (ORM 변환 지원)
# ============================================================================
class MasterTitleOut(MasterTitleBase):
    """직책 조회/응답용 스키마"""

    id: int = Field(..., description="직책 PK")
    created_at: Optional[datetime] = Field(None, description="생성일시 (UTC)")

    # ✅ ORM 변환 허용 (SQLAlchemy → Pydantic)
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

# ============================================================================
# 4️⃣ 정렬(Reorder) 요청용
# ============================================================================
class MasterTitleReorderIn(BaseModel):
    """직책 순서 재정렬 단일 항목"""
    id: int = Field(..., description="직책 ID")
    order_no: int = Field(..., description="정렬 순서")

class MasterTitleReorderBody(BaseModel):
    """직책 일괄 순서 재정렬 요청 바디"""
    items: List[MasterTitleReorderIn] = Field(..., description="직책 재정렬 항목 목록")

    # ✅ ORM 변환 불필요 — 단순 입력용
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=False)
