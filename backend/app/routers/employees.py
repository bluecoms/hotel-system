# ============================================================================
# File      : app/routers/employees.py
# Version   : 2025.10-22 Final Stable (v3.6-FIX3 · SSOT Property Sync + Status/Filters)
# Purpose   : Hotel Admin — Employees Domain Router (Property 기반 구조 + DeptName)
# ----------------------------------------------------------------------------
# 목적:
#   • 직원(사원) 데이터의 CRUD 및 계약 상태/지점 관리 API
#   • property_code(지점) 단위로 직원 목록 필터링
#   • dept_name/title_name 자동 매핑으로 UI 표시 일원화
#   • ✅ v3.6-FIX3: 계약상태 기본값 및 목록 필터/정렬 정합성 개선
# ----------------------------------------------------------------------------
# 변경사항 (v3.6-FIX3)
#   ✅ 직원 신규 생성 시 contract_status 기본값 'none' 명시 (미계약 상태)
#   ✅ 목록 조회에 dept / status / sort 파라미터 정식 지원
#      - status: none | active | terminated
#      - sort:   key:order (예: name:asc, hire_date:desc)
#   ✅ Employees.vue와 파라미터 정합성 일치 (dept/status/sort 반영)
#   ✅ 기존 응답 구조 및 jsonable_encoder 직렬화 유지
# ----------------------------------------------------------------------------
# 엔드포인트:
#   • GET    /api/employees                     → 목록 조회(계약 상태 포함)
#   • GET    /api/employees/me                  → 로그인 사용자 인사정보
#   • GET    /api/employees/{id}                → 단건 조회
#   • POST   /api/employees                     → 생성 (property_code 포함)
#   • PUT    /api/employees/{id}                → 수정
#   • DELETE /api/employees/{id}                → 삭제(Soft Delete)
#   • GET    /api/employees/{id}/contract-context → 계약 입력 컨텍스트
#   • GET    /api/employees/by-department/{dept_code} → 부서별 직원(팀장관리 전용)
# ============================================================================

from __future__ import annotations
from typing import Optional, Dict, Any
from datetime import date, datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, or_, func
from sqlalchemy.orm import Session

from app.core.locale import set_lang
from app.core.auth import require_user, require_roles, current_user
from app.db.session import get_db
from app.models.employee import Employee, UserEmployeeMap
from app.models.user import User
from app.models import MasterTitle, MasterEmpNoPolicy, MasterDepartment
from app.schemas.employees import EmployeeIn, EmployeeDetailOut, EmployeeUpdate, EmployeeListOut

router = APIRouter(
    prefix="/api/employees",
    tags=["employees"],
    dependencies=[Depends(set_lang), Depends(require_user)],
)

# ─────────────────────────────────────────────
# 내부 유틸
# ─────────────────────────────────────────────
def _birth_from_rrn_mask(rrn_mask: str) -> str:
    """주민번호 마스킹값에서 YYYY-MM-DD 추정(계약서용 표시)"""
    if not rrn_mask:
        return ""
    s = rrn_mask.replace("-", "").replace(" ", "")
    if len(s) < 7:
        return ""
    yy, mm, dd = s[:2], s[2:4], s[4:6]
    try:
        y2 = int(yy)
        year = 2000 + y2 if 0 <= y2 <= 22 else 1900 + y2
        date(year, int(mm), int(dd))
        return f"{year:04d}-{int(mm):02d}-{int(dd):02d}"
    except Exception:
        return ""

# ─────────────────────────────────────────────
# 1️⃣ 직원 목록 조회 (Property 기준)
#   - dept / status / sort 파라미터 정식 지원
# ─────────────────────────────────────────────
@router.get("")
def list_employees(
    q: Optional[str] = Query("", description="검색어(name/emp_no/dept/title)"),
    property_code: str = Query("MOP", description="지점 코드 (예: MOP)"),
    dept: Optional[str] = Query(None, description="부서 코드 필터 (예: FR/HK/FB...)"),
    status: Optional[str] = Query(None, description="계약 상태(none|active|terminated)"),
    sort: Optional[str] = Query("", description="정렬 key:order (예: name:asc, hire_date:desc)"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """직원 목록 조회 — property_code, 계약 상태, 부서/직책명 포함"""
    conds = [Employee.deleted_at.is_(None), Employee.property_code == property_code]

    # dept 코드 필터 (정확히 일치)
    if dept:
        conds.append(Employee.dept == dept)

    # status 필터 (none | active | terminated)
    if status:
        s = status.strip().lower()
        if s in {"none", "active", "terminated"}:
            conds.append(Employee.contract_status == s)

    # keyword like 검색
    if q:
        like = f"%{q}%"
        conds.append(or_(
            Employee.emp_no.ilike(like),
            Employee.name.ilike(like),
            Employee.dept.ilike(like),
            Employee.title.ilike(like),
        ))

    # 정렬 파싱
    order_col = Employee.id
    order_desc = True
    if sort:
        try:
            k, o = (sort.split(":", 1) + ["asc"])[:2]
            k = (k or "").strip().lower()
            o = (o or "asc").strip().lower()
            order_desc = (o == "desc")
            # 지원 컬럼 최소화(안전)
            if k == "name":
                order_col = Employee.name
            elif k == "emp_no":
                order_col = Employee.emp_no
            elif k == "hire_date":
                order_col = Employee.hire_date
            elif k == "contract_start":
                order_col = Employee.contract_start
            elif k == "contract_end":
                order_col = Employee.contract_end
            elif k == "dept":
                order_col = Employee.dept
            elif k == "title":
                order_col = Employee.title
            else:
                order_col = Employee.id
        except Exception:
            order_col = Employee.id
            order_desc = True

    base = select(Employee).where(*conds)
    total = db.execute(select(func.count()).select_from(base.subquery())).scalar() or 0
    qset = base.order_by(order_col.desc() if order_desc else order_col.asc())
    rows = db.execute(qset.offset((page - 1) * size).limit(size)).scalars().all()

    # ✅ 직책/부서명 매핑 (실제 컬럼 기준)
    title_map = {
        (t.code or "").upper(): t.name
        for t in db.query(MasterTitle.code, MasterTitle.name).all()
    }
    dept_map = {
        (d.dept_code or "").upper(): d.dept_name
        for d in db.query(MasterDepartment.dept_code, MasterDepartment.dept_name).all()
    }

    items = []
    for r in rows:
        data = {
            "id": r.id,
            "emp_no": r.emp_no,
            "name": r.name,
            "property_code": r.property_code,
            "dept": r.dept or "",
            "dept_name": dept_map.get((r.dept or "").upper(), ""),
            "title": r.title or "",
            "title_name": title_map.get((r.title or "").upper(), ""),
            "hire_date": r.hire_date,
            "leave_date": r.leave_date,
            "phone": r.phone or "",
            "email": r.email or "",
            "contract_status": (r.contract_status or "") if hasattr(r, "contract_status") else "",
            "contract_start": getattr(r, "contract_start", None),
            "contract_end": getattr(r, "contract_end", None),
        }
        items.append(EmployeeListOut.model_validate(data).model_dump())

    return JSONResponse(jsonable_encoder({
        "items": items,
        "page": page,
        "size": size,
        "total": int(total),
    }))

# ─────────────────────────────────────────────
# 2️⃣ 내 정보 (로그인 사용자 인사 정보)
# ─────────────────────────────────────────────
@router.get("/me", response_model=EmployeeDetailOut)
def get_my_employee(user=Depends(current_user), db: Session = Depends(get_db)):
    """로그인한 사용자의 직원(Employee) 정보 반환"""
    email = (user or {}).get("email")
    if not email:
        raise HTTPException(status_code=401, detail="invalid user context")

    u = db.query(User).filter(User.email == email).first()
    if not u:
        raise HTTPException(status_code=404, detail="user not found")

    mapping = db.query(UserEmployeeMap).filter(UserEmployeeMap.user_id == u.id).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="no employee linked to this user")

    e = db.query(Employee).filter(Employee.id == mapping.employee_id).first()
    if not e or getattr(e, "deleted_at", None):
        raise HTTPException(status_code=404, detail="employee not found")

    return EmployeeDetailOut.model_validate(e)

# ─────────────────────────────────────────────
# 3️⃣ 단건 조회
# ─────────────────────────────────────────────
@router.get("/{emp_id}", response_model=EmployeeDetailOut)
def get_employee(emp_id: int, db: Session = Depends(get_db)):
    """직원 단건 조회"""
    e = db.get(Employee, emp_id)
    if not e or getattr(e, "deleted_at", None):
        raise HTTPException(status_code=404, detail="not found")
    return EmployeeDetailOut.model_validate(e)

# ─────────────────────────────────────────────
# 4️⃣ 신규 직원 생성 (Property 포함)
#   - 계약상태 기본값을 명시적으로 'none'으로 설정
# ─────────────────────────────────────────────
@router.post("", dependencies=[Depends(require_roles(["ADMIN", "SUPERADMIN"]))])
def create_employee(body: EmployeeIn, db: Session = Depends(get_db)):
    """신규 직원 생성 — property_code 기본값 MOP 포함"""
    emp_no = (body.emp_no or "").strip()
    if not emp_no:
        policy = db.query(MasterEmpNoPolicy).first()
        if policy:
            prefix = (policy.prefix or "EMP").upper()
            start_no = int(policy.start_no or 1)
            emp_no = f"{prefix}{start_no:03d}"
            if policy.auto_increment:
                policy.start_no = start_no + 1
                db.commit()
        else:
            emp_no = f"EMP{int(datetime.utcnow().timestamp()) % 10000:04d}"

    # ✅ 계약 상태/기간 기본값을 명시 (UI 일관성)
    e = Employee(
        property_code=body.property_code or "MOP",
        emp_no=emp_no,
        contract_status="none",          # ← 미계약 명시
        contract_start=None,
        contract_end=None,
        **body.model_dump(exclude={"emp_no", "property_code"}),
    )
    db.add(e)
    db.commit()
    db.refresh(e)
    return {"ok": True, "id": e.id, "emp_no": e.emp_no, "property_code": e.property_code}

# ─────────────────────────────────────────────
# 5️⃣ 계약 입력 컨텍스트
# ─────────────────────────────────────────────
@router.get("/{emp_id}/contract-context")
def get_contract_context(emp_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """계약서 자동입력용 컨텍스트(생년월일 추정, 직책/부서명 매핑 포함)"""
    e = db.get(Employee, emp_id)
    if not e or getattr(e, "deleted_at", None):
        raise HTTPException(status_code=404, detail="not found")

    # 직책/부서명 매핑
    title_name, dept_name = "", ""
    if e.title:
        rec = db.query(MasterTitle).filter(MasterTitle.code == e.title).first()
        if rec:
            title_name = rec.name
    if e.dept:
        rec = db.query(MasterDepartment).filter(MasterDepartment.dept_code == e.dept).first()
        if rec:
            dept_name = rec.dept_name

    # 주민번호 마스킹에서 생년월일 추정
    birth = _birth_from_rrn_mask(e.rrn_mask or "")

    return {
        "employee_id": e.id,
        "property_code": e.property_code,
        "emp_no": e.emp_no,
        "name": e.name,
        "birth_date": birth,
        "phone": e.phone or "",
        "address": e.address or "",
        "bank_name": e.bank_name or "",
        "account_mask": e.account_mask or "",
        "account_last4": e.account_last4 or "",
        "dept": e.dept or "",
        "dept_name": dept_name,
        "title": e.title or "",
        "title_name": title_name,
        "rank": getattr(e, "rank", "") or "",
        "position": e.position or "",
    }

# ─────────────────────────────────────────────
# 6️⃣ 수정 (부분 갱신)
# ─────────────────────────────────────────────
@router.put("/{emp_id}", dependencies=[Depends(require_roles(["ADMIN", "SUPERADMIN"]))])
def update_employee(emp_id: int, body: EmployeeUpdate, db: Session = Depends(get_db)):
    """직원 정보 수정(부분 갱신 허용, property_code 포함)"""
    e = db.get(Employee, emp_id)
    if not e or getattr(e, "deleted_at", None):
        raise HTTPException(status_code=404, detail="not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(e, k, v if v is not None else getattr(e, k))
    db.commit()
    db.refresh(e)
    return {"ok": True, "id": e.id, "property_code": e.property_code}

# ─────────────────────────────────────────────
# 7️⃣ 삭제 (Soft Delete)
# ─────────────────────────────────────────────
@router.delete("/{emp_id}", dependencies=[Depends(require_roles(["SUPERADMIN"]))])
def soft_delete_employee(emp_id: int, db: Session = Depends(get_db)):
    """직원 정보 삭제(Soft Delete)"""
    e = db.get(Employee, emp_id)
    if not e:
        raise HTTPException(status_code=404, detail="not found")
    if getattr(e, "deleted_at", None):
        return {"ok": True, "already_deleted": True}
    e.deleted_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "deleted": emp_id}

# ─────────────────────────────────────────────
# 부서별 직원 목록 조회 (팀장관리 전용)
# ─────────────────────────────────────────────
@router.get("/by-department/{dept_code}")
def list_by_department(
    dept_code: str,
    property_code: str = Query("MOP"),
    db: Session = Depends(get_db),
):
    """특정 부서 코드(dept_code)에 속한 직원 목록 반환"""
    rows = (
        db.query(Employee)
        .filter(
            Employee.deleted_at.is_(None),
            Employee.property_code == property_code,
            Employee.dept == dept_code,  # ← 코드 직접 비교
        )
        .order_by(Employee.id.desc())
        .all()
    )
    items = [EmployeeListOut.model_validate(r).model_dump() for r in rows]
    return {"ok": True, "items": items, "total": len(items)}
