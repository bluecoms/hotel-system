# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/models/roles_access.py
# Version   : 2025-10-31 · v3.6 (SSOT Phase 3.5 Final · DeptAccess Unified)
# Purpose   : Hotel Admin — DeptAccess 모델 정의 (route_name + access_scope 기반)
# ----------------------------------------------------------------------------
# 목적:
#   • 부서(Dept) 기반 접근권한 관리의 단일 테이블 정의.
#   • 각 페이지(라우트)별 접근 가능한 부서코드 목록(JSON) 저장.
# ----------------------------------------------------------------------------
# 설계 원칙:
#   ✅ route_name 은 유일(UniqueConstraint)해야 하며 식별자로 사용.
#   ✅ access_scope 는 항상 List[str] JSON 형태 (예: ["ALL_VIEW","FR","HK"])
#   ✅ created_at 은 UTC 기준 자동기록.
#   ✅ SUPERADMIN 은 별도 정책으로 전체 허용 처리.
# ----------------------------------------------------------------------------
# 연동 모듈:
#   • app/schemas/roles_access.py  → DeptAccessIn / DeptAccessOut / EffectiveDeptAccess
#   • app/routers/roles_access.py  → CRUD + /effective API
#   • src/stores/auth.ts           → bootstrap() 권한맵 계산
#   • src/services/auth.ts         → getEffectiveDeptAccess()
# ----------------------------------------------------------------------------
# 주의:
#   • 구 RoleAccess / UserRole / role_map 구조는 모두 폐기됨.
#   • DeptAccess 만이 공식 권한 원천(SSOT)이다.
# ============================================================================

from sqlalchemy import Column, Integer, String, JSON, DateTime, func
from app.db.base_class import Base

# ============================================================================
# DeptAccess 모델
# ============================================================================
class DeptAccess(Base):
    """
    DeptAccess (부서 기반 접근권한 테이블)
    ───────────────────────────────────────────────
    route_name   : 라우트(페이지) 식별자 (예: dashboard-kpi, hr/employees)
    access_scope : 접근 가능한 부서코드 리스트(JSON)
                   예: ["ALL_VIEW", "FR", "HK", "AD"]
    created_at   : 레코드 생성 시각(UTC)
    """

    __tablename__ = "dept_access"

    # 기본키
    id = Column(Integer, primary_key=True, index=True, doc="PK (자동증가)")

    # 라우트명 (식별자)
    route_name = Column(
        String(120),
        unique=True,
        nullable=False,
        index=True,
        doc="라우트 이름 (예: dashboard-kpi, hr/employees)",
    )

    # 접근허용 부서코드 리스트
    access_scope = Column(
        JSON,
        default=list,
        nullable=False,
        doc='접근허용 부서코드 리스트(JSON, 예: ["ALL_VIEW","FR","HK"])',
    )

    # 생성일시
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        doc="생성일시(UTC 기준 자동기록)",
    )

    def __repr__(self) -> str:
        """디버그 출력용"""
        return f"<DeptAccess route='{self.route_name}' scopes={self.access_scope}>"

# ============================================================================
# End of File — app/models/roles_access.py
# ============================================================================
