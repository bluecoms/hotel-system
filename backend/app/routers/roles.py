# ============================================================================
# File    : app/routers/roles.py
# Version : 2025-10-21 · v3.0 (DeptAccess Migration · SSOT)
# Purpose : Hotel Admin — 부서별 접근권한(DeptAccess) + 역할(Role) 관리 API
# ----------------------------------------------------------------------------
# 구성 목적:
#   • 역할(Role) 생성/삭제/조회 — 기존 유지
#   • 부서별 접근권한(DeptAccess) 관리 — 신규 구조 적용
# ----------------------------------------------------------------------------
# 변경 사항 (v3.0)
#   ✅ 기존 RoleAccess (role_code/access_level) → DeptAccess (route_name/access_scope)
#   ✅ access_scope : List[str] (예: ["ALL_VIEW","FR","HK"])
#   ✅ SUPERADMIN 은 전체 라우트 접근 보장
#   ✅ UI(RoleAccess.vue)와 연동 — 다중 선택형 부서 접근 제어
# ----------------------------------------------------------------------------
# 연결 프런트엔드:
#   • src/views/Admin/RoleAccess.vue
#   • /api/roles/access  (GET, PUT)
# ----------------------------------------------------------------------------
# 작성/관리 원칙:
#   • SUPERADMIN 전용 수정/삭제 권한
#   • 모든 변경 사항은 audit 로그 기록
# ============================================================================
from __future__ import annotations
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.auth import require_user, require_roles, current_user
from app.core.audit import write_audit
from app.db.session import get_db
from app.models.role import Role, RoleAccess    # RoleAccess → DeptAccess로 재활용
from app.schemas.role import RoleIn, RoleOut, DeptAccessOut as RoleAccessOut

# ─────────────────────────────────────────────
# Router 정의
# ─────────────────────────────────────────────
router = APIRouter(
    prefix="/api/roles",
    tags=["roles"],
    dependencies=[Depends(require_user)],
)

# ============================================================================
# 1️⃣ 역할(Role) 목록 조회
# ============================================================================
@router.get("", dependencies=[Depends(require_roles(["ADMIN", "SUPERADMIN"]))])
def list_roles(
    include_inactive: bool = Query(False, description="비활성 포함 여부"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    역할 목록 조회 — 기존 구조 유지
    """
    q = db.query(Role)
    if not include_inactive:
        q = q.filter(Role.is_active.is_(True))
    roles = q.order_by(Role.code.asc()).all()
    items = [RoleOut.model_validate(r).model_dump() for r in roles]
    return {"ok": True, "items": items, "total": len(items)}

# ============================================================================
# 2️⃣ 부서별 접근권한(DeptAccess) 목록 조회
# ============================================================================
@router.get("/access", dependencies=[Depends(require_roles(["ADMIN", "SUPERADMIN"]))])
def list_dept_access(
    route_name: Optional[str] = Query(None, description="특정 Route만 조회할 경우"),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """
    부서별 접근권한 목록 조회
    """
    q = db.query(RoleAccess)
    if route_name:
        q = q.filter(RoleAccess.route_name == route_name)
    rows = q.order_by(RoleAccess.route_name.asc()).all()
    return [RoleAccessOut.model_validate(r).model_dump() for r in rows]

# ============================================================================
# 3️⃣ 부서별 접근권한(DeptAccess) Upsert
# ============================================================================
@router.put("/access", dependencies=[Depends(require_roles(["SUPERADMIN"]))])
def upsert_dept_access(
    body: Dict[str, Any],
    db: Session = Depends(get_db),
):
    """
    부서별 접근권한 단건 저장 (Upsert)
    - 요청 예시:
        {
          "route_name": "dashboard-kpi",
          "access_scope": ["ALL_VIEW","FR","HK"]
        }
    """
    route_name = (body.get("route_name") or "").strip()
    scopes = body.get("access_scope") or []
    if not route_name:
        raise HTTPException(status_code=422, detail="route_name required")

    # 중복제거 및 정리
    scopes = list(sorted(set([s.strip().upper() for s in scopes if s])))

    rec = db.query(RoleAccess).filter(RoleAccess.route_name == route_name).first()
    if rec:
        rec.access_scope = scopes
        write_audit(db, "system", "deptaccess.update", f"route={route_name}", {"scope": scopes})
    else:
        rec = RoleAccess(route_name=route_name, access_scope=scopes)
        db.add(rec)
        write_audit(db, "system", "deptaccess.create", f"route={route_name}", {"scope": scopes})

    db.commit()
    db.refresh(rec)
    return {"ok": True, "access": RoleAccessOut.model_validate(rec).model_dump()}

# ============================================================================
# 4️⃣ 부서별 접근권한(DeptAccess) 삭제
# ============================================================================
@router.delete("/access", dependencies=[Depends(require_roles(["SUPERADMIN"]))])
def delete_dept_access(
    route: str = Query(..., description="삭제할 route_name"),
    db: Session = Depends(get_db),
):
    """
    특정 Route의 부서 접근권한 삭제
    """
    deleted = db.query(RoleAccess).filter(RoleAccess.route_name == route).delete(synchronize_session=False)
    db.commit()
    if deleted:
        write_audit(db, "system", "deptaccess.delete", f"route={route}")
    return {"ok": True, "deleted": deleted}

# ============================================================================
# 5️⃣ 실효 접근권한 계산 (Effective DeptAccess)
# ============================================================================
@router.get("/access/effective", dependencies=[Depends(require_roles(["ADMIN", "SUPERADMIN"]))])
def effective_dept_access(
    route: Optional[str] = Query(None, description="특정 라우트만 계산할 경우"),
    db: Session = Depends(get_db),
    user = Depends(current_user),
):
    """
    로그인한 사용자 기준의 실제 접근권한 계산
    - SUPERADMIN → 모든 Route 접근 가능
    - 일반사용자 → 본인 부서 코드 포함 여부로 접근 판정
    """
    roles = [r.upper() for r in (user.get("roles") or [])]
    dept = (user.get("dept") or "").upper()

    # SUPERADMIN 전부 허용
    if "SUPERADMIN" in roles:
        if route:
            return {"route": route, "access_scope": ["ALL_EDIT"], "dept": dept}
        return {"ok": True, "access": {"*": ["ALL_EDIT"]}}

    q = db.query(RoleAccess.route_name, RoleAccess.access_scope).all()
    access_map: Dict[str, List[str]] = {}
    for rname, scopes in q:
        if not scopes:
            continue
        scopes = [s.upper() for s in scopes]
        if "ALL_VIEW" in scopes or "ALL_EDIT" in scopes or dept in scopes:
            access_map[rname] = scopes

    if route:
        scopes = access_map.get(route, [])
        return {"route": route, "access_scope": scopes, "dept": dept}

    return {"ok": True, "dept": dept, "access": access_map}

# ============================================================================
# (참고) 기존 Role CRUD 유지 — DeptAccess와 별개
# ============================================================================
@router.post("", dependencies=[Depends(require_roles(["SUPERADMIN"]))])
def create_role(body: RoleIn, db: Session = Depends(get_db)):
    code = (body.code or "").strip().upper()
    if not code:
        raise HTTPException(status_code=422, detail="code required")
    has = db.query(Role).filter(Role.code == code).first()
    if has:
        raise HTTPException(status_code=400, detail="duplicate role code")

    r = Role(code=code, name=body.name or code, is_active=bool(body.is_active))
    db.add(r)
    db.commit()
    db.refresh(r)
    write_audit(db, "system", "role.create", f"code={r.code}", {"name": r.name})
    return {"ok": True, "role": RoleOut.model_validate(r).model_dump()}

@router.delete("/{code}", dependencies=[Depends(require_roles(["SUPERADMIN"]))])
def delete_role(code: str, db: Session = Depends(get_db)):
    code = code.strip().upper()
    r = db.query(Role).filter(Role.code == code).first()
    if not r:
        raise HTTPException(status_code=404, detail="role not found")
    db.delete(r)
    db.commit()
    write_audit(db, "system", "role.delete", f"code={code}")
    return {"ok": True}
