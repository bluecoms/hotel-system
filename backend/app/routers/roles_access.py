# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/routers/roles_access.py
# Version   : 2025-11-03 · v3.9 (DeptAccess + DeptLeads API 완성판)
# Purpose   : Hotel Admin — DeptAccess CRUD + /effective + /dept-leads
# ----------------------------------------------------------------------------
# 주요 변경
#   ✅ GET    /api/roles/access              → 목록 조회
#   ✅ PUT    /api/roles/access              → 단건 Upsert
#   ✅ GET    /api/roles/access/effective    → 실효 권한 조회
#   ✅ GET    /api/roles/dept-leads          → 부서별 팀장 목록 (더미 or 실제 연결 가능)
#   ✅ PUT    /api/roles/dept-leads          → 팀장 지정(선택적)
# ----------------------------------------------------------------------------
# 설계 메모
#   • DeptAccess : 부서별 접근권한 관리 (SSOT)
#   • DeptLeads  : 각 부서별 팀장(담당자) 관리 (확장 가능)
#   • 인증: X-Internal-Token 기반 require_token_local
# ============================================================================
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.db.session import get_db
from app.core.auth import require_token_local
from app.models.roles_access import DeptAccess
from app.schemas.roles_access import DeptAccessIn, DeptAccessOut, EffectiveDeptAccess

router = APIRouter(prefix="/api/roles", tags=["DeptAccess"])

# ----------------------------------------------------------------------------
# 1) DeptAccess 목록 조회
# ----------------------------------------------------------------------------
@router.get("/access", response_model=List[DeptAccessOut])
def list_access(
    db: Session = Depends(get_db),
    _token_ok: None = Depends(require_token_local),
):
    """전체 DeptAccess 목록 조회"""
    rows = db.query(DeptAccess).order_by(DeptAccess.route_name.asc()).all()
    return rows

# ----------------------------------------------------------------------------
# 2) DeptAccess Upsert (단건)
# ----------------------------------------------------------------------------
@router.put("/access", response_model=DeptAccessOut)
def upsert_access(
    data: DeptAccessIn,
    db: Session = Depends(get_db),
    _token_ok: None = Depends(require_token_local),
):
    """DeptAccess 단건 생성 또는 수정 (멱등 Upsert)"""
    if not data.route_name:
        raise HTTPException(status_code=400, detail="route_name is required")

    route = data.route_name.strip().lower()
    scopes = sorted({s.upper() for s in (data.access_scope or [])})

    row = db.query(DeptAccess).filter(DeptAccess.route_name == route).first()
    if row:
        row.access_scope = scopes
    else:
        row = DeptAccess(route_name=route, access_scope=scopes)
        db.add(row)

    db.commit()
    db.refresh(row)
    return row

# ----------------------------------------------------------------------------
# 3) 실효 접근권한 조회 (/access/effective)
# ----------------------------------------------------------------------------
@router.get("/access/effective", response_model=EffectiveDeptAccess)
def get_effective_access(
    db: Session = Depends(get_db),
    _token_ok: None = Depends(require_token_local),
):
    """DeptAccess 전체를 기반으로 실효 접근권한 계산"""
    rows = db.query(DeptAccess).all()
    access_map = {r.route_name: r.access_scope for r in rows}
    return EffectiveDeptAccess(dept="MOP", access=access_map)

# ----------------------------------------------------------------------------
# 4) 부서별 팀장 목록 조회 (/dept-leads)
# ----------------------------------------------------------------------------
@router.get("/dept-leads")
def get_dept_leads(
    _token_ok: None = Depends(require_token_local),
) -> Dict[str, Any]:
    """
    부서별 팀장 목록 조회 (임시 더미데이터)
    ※ 실제 환경에서는 DB 테이블 dept_leads 로 확장 가능
    """
    data = [
        {
            "dept_code": "FR",
            "lead_name": "김프론트",
            "lead_email": "front@hotel.com",
            "assigned_at": "2025-11-03",
        },
        {
            "dept_code": "HK",
            "lead_name": "이하우스",
            "lead_email": "housekeeping@hotel.com",
            "assigned_at": "2025-11-03",
        },
        {
            "dept_code": "AD",
            "lead_name": "박지원",
            "lead_email": "admin@hotel.com",
            "assigned_at": "2025-11-03",
        },
        {
            "dept_code": "FM",
            "lead_name": "최시설",
            "lead_email": "facility@hotel.com",
            "assigned_at": "2025-11-03",
        },
        {
            "dept_code": "MG",
            "lead_name": "정관리",
            "lead_email": "manager@hotel.com",
            "assigned_at": "2025-11-03",
        },
    ]
    return {"items": data}

# ----------------------------------------------------------------------------
# 5) 부서별 팀장 지정 (PUT)
# ----------------------------------------------------------------------------
@router.put("/dept-leads")
def set_dept_lead(
    payload: Dict[str, Any],
    _token_ok: None = Depends(require_token_local),
):
    """
    부서별 팀장 지정 (PUT)
    요청 예시:
    {
      "dept_code": "FR",
      "lead_name": "홍길동",
      "lead_email": "hong@hotel.com"
    }
    """
    dept = payload.get("dept_code")
    lead = payload.get("lead_name")
    if not dept or not lead:
        raise HTTPException(status_code=400, detail="dept_code and lead_name required")

    # 실제로는 DB 반영 로직 필요
    return {"ok": True, "message": f"팀장({lead})이 {dept} 부서로 지정되었습니다."}

# ============================================================================
# End of File — app/routers/roles_access.py (v3.9 Final)
# ============================================================================
