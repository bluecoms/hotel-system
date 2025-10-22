# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/routers/roles_access.py
# Version   : 2025-11-02 · v3.8 (DeptAccess Upsert 안정판 · SSOT 완성)
# Purpose   : Hotel Admin — DeptAccess CRUD + /effective API
# ----------------------------------------------------------------------------
# 목적:
#   • 부서 기반 접근권한(DeptAccess) CRUD 및 실효 권한 계산 API
#   • /api/roles/access, /api/roles/access/effective 경로를 처리
# ----------------------------------------------------------------------------
# 변경 요약 (v3.8)
#   ✅ GET    /api/roles/access              → DeptAccess 목록 조회
#   ✅ PUT    /api/roles/access              → DeptAccess 단건 Upsert (멱등)
#   ✅ GET    /api/roles/access/effective    → 실효 권한맵 조회
#   ✅ 모든 엔드포인트에 require_token_local 인증 적용
#   ✅ SQLAlchemy ORM + Pydantic v2 완전 호환
# ----------------------------------------------------------------------------
# 설계 원칙:
#   • DeptAccess = 권한 SSOT 단일 진실 원천 (Single Source of Truth)
#   • route_name 은 Unique Key
#   • access_scope 는 JSON(List[str]) 컬럼, Python 리스트 ↔ JSON 자동 매핑
#   • PUT 메서드는 멱등(idempotent)하도록 설계 (동일 요청 시 상태 불변)
# ----------------------------------------------------------------------------
# 연동 모듈:
#   • app/models/roles_access.py   → DeptAccess (SQLAlchemy Model)
#   • app/schemas/roles_access.py  → DeptAccessIn / DeptAccessOut / EffectiveDeptAccess
#   • src/services/auth.ts         → getEffectiveDeptAccess()
#   • src/stores/auth.ts           → bootstrap() 권한맵 로드
#   • src/views/Admin/RoleAccess.vue → 프런트 권한관리 화면
# ============================================================================
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.core.auth import require_token_local
from app.models.roles_access import DeptAccess
from app.schemas.roles_access import DeptAccessIn, DeptAccessOut, EffectiveDeptAccess

# ============================================================================
# Router 설정
# ============================================================================
router = APIRouter(
    prefix="/api/roles/access",
    tags=["DeptAccess"],
    responses={404: {"description": "Not found"}},
)

# ============================================================================
# 1) DeptAccess 목록 조회
# ============================================================================
@router.get("", response_model=List[DeptAccessOut])
def list_access(
    db: Session = Depends(get_db),
    _token_ok: None = Depends(require_token_local),
):
    """
    DeptAccess 전체 목록 조회

    반환 예시:
    [
      {
        "id": 1,
        "route_name": "dashboard-kpi",
        "access_scope": ["ALL_EDIT","MG"],
        "created_at": "2025-10-22T16:39:37"
      },
      ...
    ]
    """
    rows = db.query(DeptAccess).order_by(DeptAccess.route_name.asc()).all()
    return rows

# ============================================================================
# 2) DeptAccess Upsert (단건)
# ============================================================================
@router.put("", response_model=DeptAccessOut)
def upsert_access(
    data: DeptAccessIn,
    db: Session = Depends(get_db),
    _token_ok: None = Depends(require_token_local),
):
    """
    DeptAccess 단건 생성 또는 수정 (멱등 Upsert)

    요청 예시:
    {
      "route_name": "closing-calendar",
      "access_scope": ["ALL_EDIT", "MG"]
    }

    동작:
      • 동일 route_name 존재 시 → access_scope 갱신
      • 존재하지 않으면 → 신규 생성
      • 항상 커밋 후 최신 객체 반환
    """
    if not data.route_name:
        raise HTTPException(status_code=400, detail="route_name is required")

    route = data.route_name.strip().lower()
    scopes = sorted({s.upper() for s in (data.access_scope or [])})

    # 기존 존재여부 확인
    row = db.query(DeptAccess).filter(DeptAccess.route_name == route).first()
    if row:
        row.access_scope = scopes
    else:
        row = DeptAccess(route_name=route, access_scope=scopes)
        db.add(row)

    db.commit()
    db.refresh(row)
    return row

# ============================================================================
# 3) 실효 접근권한 조회 (/effective)
# ============================================================================
@router.get("/effective", response_model=EffectiveDeptAccess)
def get_effective_access(
    db: Session = Depends(get_db),
    _token_ok: None = Depends(require_token_local),
):
    """
    DeptAccess 전체를 기반으로 실효 접근권한 계산

    반환 예시:
    {
      "dept": "MOP",
      "access": {
        "dashboard-kpi": ["ALL_VIEW","FR"],
        "closing-calendar": ["ALL_EDIT","MG"]
      }
    }
    """
    rows = db.query(DeptAccess).all()
    access_map = {r.route_name: r.access_scope for r in rows}
    return EffectiveDeptAccess(dept="MOP", access=access_map)

# ============================================================================
# End of File — app/routers/roles_access.py (v3.8 Final · Full SSOT Edition)
# ============================================================================
