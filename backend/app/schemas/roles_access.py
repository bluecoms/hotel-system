# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/schemas/roles_access.py
# Version   : 2025-10-31 · v3.6 (SSOT Phase 3.5 Final · DeptAccess Unified)
# Purpose   : Hotel Admin — DeptAccess / EffectiveDeptAccess Schema Definitions
# ----------------------------------------------------------------------------
# 목적:
#   • DeptAccess(부서 기반 접근권한) 데이터 입출력 스키마 정의
#   • /api/roles/access 및 /api/roles/access/effective 엔드포인트에서 사용
# ----------------------------------------------------------------------------
# 설계 원칙:
#   ✅ DeptAccess = 권한 SSOT 단일 스키마
#   ✅ route_name 은 유일 식별자
#   ✅ access_scope 는 List[str] 형태(JSON ↔ Python)
#   ✅ EffectiveDeptAccess 는 서버 계산 결과(권한맵) 반환용
# ----------------------------------------------------------------------------
# 연동 모듈:
#   • app/models/roles_access.py   → DeptAccess (SQLAlchemy Model)
#   • app/routers/roles_access.py  → CRUD + /effective
#   • src/services/auth.ts         → getEffectiveDeptAccess()
#   • src/stores/auth.ts           → bootstrap() 권한맵 계산
# ============================================================================
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional

# ============================================================================
# DeptAccess Base
# ============================================================================
class DeptAccessBase(BaseModel):
    """DeptAccess 공통 필드 (route_name + access_scope)"""
    route_name: str = Field(..., description="라우트명 (예: hr/employees)")
    access_scope: List[str] = Field(
        default_factory=list,
        description="접근 범위 목록 (예: ['ALL_VIEW','FR','HK'])",
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
    """DeptAccess 출력"""
    id: int = Field(..., description="PK (자동증가)")
    created_at: Optional[str] = Field(None, description="생성일시(UTC)")
    model_config = ConfigDict(from_attributes=True)

# ============================================================================
# 서버 계산 기준 실효 권한 (EffectiveDeptAccess)
# ============================================================================
class EffectiveDeptAccess(BaseModel):
    """DeptAccess 실효 접근결과"""
    dept: str = Field(default="MOP", description="기본 부서 코드", example="MOP")
    access: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="route_name별 access_scope 매핑",
        example={"hr/employees": ["ALL_EDIT"], "dashboard-kpi": ["ALL_VIEW","FR"]},
    )

# ============================================================================
# End of File — app/schemas/roles_access.py
# ============================================================================
