# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/schemas/roles_access.py
# Version   : 2025-11-02 · v3.8 (Datetime Auto Serialization Fix)
# Purpose   : Hotel Admin — DeptAccess / EffectiveDeptAccess Schema Definitions
# ----------------------------------------------------------------------------
# 목적:
#   • DeptAccess(부서 기반 접근권한) 데이터 입출력 스키마 정의
#   • /api/roles/access 및 /api/roles/access/effective 엔드포인트에서 사용
# ----------------------------------------------------------------------------
# 변경 요약 (v3.8)
#   ✅ created_at 타입을 datetime으로 복원 (데이터 정합 유지)
#   ✅ ConfigDict(ser_json_timedelta=True, ser_json_datetime=True) 추가
#      → FastAPI 응답 시 datetime을 ISO8601 문자열로 자동 직렬화
#   ✅ Pydantic v2 호환 / from_attributes=True 유지
#   ✅ 모든 주석·Docstring 정비 (SSOT Phase 3.5~3.8 규칙 일관)
# ----------------------------------------------------------------------------
# 설계 원칙:
#   • DeptAccess = 권한 SSOT 단일 스키마 (RoleAccess 완전 폐기)
#   • route_name 은 유일 식별자 (UniqueConstraint)
#   • access_scope 는 List[str] 형태(JSON ↔ Python)
#   • created_at 은 datetime으로 보관하되 JSON 직렬화 시 ISO8601 문자열 변환
#   • EffectiveDeptAccess 는 서버 계산 결과(권한맵) 반환용
# ----------------------------------------------------------------------------
# 연동 모듈:
#   • app/models/roles_access.py   → DeptAccess (SQLAlchemy Model)
#   • app/routers/roles_access.py  → CRUD + /effective
#   • src/services/auth.ts         → getEffectiveDeptAccess()
#   • src/stores/auth.ts           → bootstrap() 권한맵 계산
# ============================================================================
from __future__ import annotations
from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict

# ============================================================================
# DeptAccess Base
# ============================================================================
class DeptAccessBase(BaseModel):
    """DeptAccess 공통 필드 (route_name + access_scope)

    route_name:
        권한 판단용 유일 키 (예: 'dashboard-kpi', 'hr/employees')
    access_scope:
        허용된 접근 범위 코드 리스트 (예: ['ALL_EDIT', 'FR', 'HK'])
    """
    route_name: str = Field(
        ...,
        description="라우트명 (예: 'dashboard-kpi' 또는 'hr/employees')",
        examples=["dashboard-kpi", "hr/employees"],
    )
    access_scope: List[str] = Field(
        default_factory=list,
        description="접근 허용 범위 코드 리스트 (예: ['ALL_VIEW','FR','HK'])",
        examples=[["ALL_VIEW", "FR", "HK"]],
    )

# ============================================================================
# 입력 (IN)
# ============================================================================
class DeptAccessIn(DeptAccessBase):
    """DeptAccess 생성/수정 입력"""
    pass

# ============================================================================
# 출력 (OUT)
# ============================================================================
class DeptAccessOut(DeptAccessBase):
    """DeptAccess 출력 스키마 (응답 모델)

    created_at:
        - 내부 DB에서는 datetime으로 저장
        - JSON 직렬화 시 FastAPI/Pydantic이 ISO8601 문자열로 자동 변환
    """
    id: int = Field(..., description="PK (자동증가)", example=1)
    created_at: Optional[datetime] = Field(
        None,
        description="생성일시(UTC, ISO8601 직렬화됨)",
        example="2025-10-22T16:39:37",
    )

    # ORM 객체 직렬화 및 datetime 자동 변환 설정
    model_config = ConfigDict(
        from_attributes=True,
        ser_json_timedelta='iso8601',   # ✅ 문자열 지정
        ser_json_datetime='iso8601',    # ✅ 문자열 지정 
    )

# ============================================================================
# 서버 계산 기준 실효 권한 (EffectiveDeptAccess)
# ============================================================================
class EffectiveDeptAccess(BaseModel):
    """DeptAccess 실효 접근결과(서버 계산용)

    dept:
        기본 부서 코드 (토큰 또는 사용자 기반 추출, 기본 'MOP')
    access:
        route_name별 access_scope 매핑 결과 (권한맵)
    """
    dept: str = Field(
        default="MOP",
        description="기본 부서 코드 (예: 'MOP', 'FR', 'HK')",
        example="MOP",
    )
    access: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="route_name별 access_scope 매핑",
        example={
            "dashboard-kpi": ["ALL_VIEW", "FR"],
            "closing-calendar": ["ALL_EDIT", "MG"],
        },
    )

# ============================================================================
# End of File — app/schemas/roles_access.py (v3.8 Final)
# ============================================================================
