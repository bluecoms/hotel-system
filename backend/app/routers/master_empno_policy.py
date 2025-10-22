# -*- coding: utf-8 -*-
# version: 2025-10-18 v1.2 (Stable — Optional business_date + Validation 강화)
"""
Hotel Admin — Master EmpNoPolicy Router (/api/master/empno-policy)
──────────────────────────────────────────────────────────────────────────────
목적:
  • 호텔 인사 시스템의 사번(직원번호) 정책 CRUD 관리
  • prefix, start_no, auto_increment, memo 필드 관리
  • 단일 정책 행만 유지 (업데이트 시 갱신)
  • 프런트엔드 자동 사번 생성 로직에서 호출 가능하도록 business_date 옵션 허용
──────────────────────────────────────────────────────────────────────────────
기능:
  • GET    /api/master/empno-policy        → 단일 정책 조회 (business_date optional)
  • PUT    /api/master/empno-policy        → 생성/갱신 (ADMIN, SUPERADMIN)
  • DELETE /api/master/empno-policy        → 초기화 (관리자용)
──────────────────────────────────────────────────────────────────────────────
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import MasterEmpNoPolicy
from app.schemas import MasterEmpNoPolicyIn, MasterEmpNoPolicyOut
from app.core.auth import require_roles, require_token_local

# ─────────────────────────────────────────────
# Router 정의
# ─────────────────────────────────────────────
router = APIRouter(
    prefix="/api/master/empno-policy",
    tags=["master-empno-policy"],
    dependencies=[
        Depends(require_token_local),
        Depends(require_roles(["ADMIN", "SUPERADMIN"]))
    ],
)

# ─────────────────────────────────────────────
# 조회 (business_date 선택적)
# ─────────────────────────────────────────────
@router.get("", response_model=MasterEmpNoPolicyOut, summary="사번 정책 조회")
def get_empno_policy(
    business_date: str = Query(None, description="기준일 (선택; 자동사번생성 시 사용)"),
    db: Session = Depends(get_db)
):
    """
    현재 사번 정책 1건을 조회한다.
    - business_date는 선택적이며 실제 정책 조회에는 영향을 주지 않는다.
    """
    row = db.query(MasterEmpNoPolicy).order_by(MasterEmpNoPolicy.id.desc()).first()
    if not row:
        raise HTTPException(status_code=404, detail="사번 정책이 존재하지 않습니다.")

    # business_date가 들어올 경우 단순 로그용 처리 가능 (현재 미사용)
    # 예: print(f"[EmpNoPolicy] 조회 기준일: {business_date}")

    return row


# ─────────────────────────────────────────────
# 생성 또는 수정 (단일 정책만 유지)
# ─────────────────────────────────────────────
@router.put("", response_model=MasterEmpNoPolicyOut, summary="사번 정책 저장/갱신")
def upsert_empno_policy(payload: MasterEmpNoPolicyIn, db: Session = Depends(get_db)):
    """
    사번 정책을 생성하거나 갱신한다.
    - 기존 정책이 존재하면 UPDATE
    - 없으면 INSERT
    """
    row = db.query(MasterEmpNoPolicy).order_by(MasterEmpNoPolicy.id.desc()).first()

    if row:
        # 업데이트
        row.prefix = payload.prefix
        row.start_no = payload.start_no
        row.auto_increment = payload.auto_increment
        row.memo = payload.memo
    else:
        # 신규 생성
        row = MasterEmpNoPolicy(**payload.dict())
        db.add(row)

    db.commit()
    db.refresh(row)
    return row


# ─────────────────────────────────────────────
# 초기화 (선택적) — 관리자 전용
# ─────────────────────────────────────────────
@router.delete("", summary="사번 정책 초기화", response_model=dict)
def reset_empno_policy(db: Session = Depends(get_db)):
    """
    사번 정책을 완전히 초기화합니다.
    (경고: 실제 운영에서는 거의 사용되지 않습니다)
    """
    rows = db.query(MasterEmpNoPolicy).all()
    if not rows:
        raise HTTPException(status_code=404, detail="삭제할 정책이 없습니다.")
    for r in rows:
        db.delete(r)
    db.commit()
    return {"ok": True, "deleted": len(rows)}


# ─────────────────────────────────────────────
# [보충 기능] — 다음 사번 생성 (선택)
# ─────────────────────────────────────────────
@router.get("/next", summary="다음 사번 미리보기", response_model=dict)
def preview_next_empno(db: Session = Depends(get_db)):
    """
    현재 정책 기준 다음 사번을 미리 생성해 반환한다.
    실제 DB에는 반영하지 않으며 미리보기 용도이다.
    """
    row = db.query(MasterEmpNoPolicy).order_by(MasterEmpNoPolicy.id.desc()).first()
    if not row:
        raise HTTPException(status_code=404, detail="사번 정책이 존재하지 않습니다.")

    prefix = row.prefix or "EMP"
    start_no = row.start_no or 1

    # 현재 직원 수 조회하여 다음 번호 계산
    from app.models.employee import Employee
    total = db.query(Employee).count()
    next_no = start_no + total
    emp_no = f"{prefix}{next_no:03d}"
    return {"ok": True, "next_emp_no": emp_no, "policy_prefix": prefix, "policy_start": start_no}
