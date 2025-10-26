# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/routers/master_bank.py
# Version   : 2025.11-04 · v1.1 (Options Safe · SSOT Compatible)
# Purpose   : Hotel Admin — Master Banks Router (/api/master/banks)
# ----------------------------------------------------------------------------
# 목적:
#   • 은행(Banks) 기준정보 CRUD + v-select 옵션 제공
#   • /options 엔드포인트는 property_code 없이도 호출 가능 (Optional 허용)
#   • 프런트엔드(DialogEmployeeForm.vue 등)와 완전 호환
# ----------------------------------------------------------------------------
# 주요 변경사항 (v1.1)
#   ✅ /options : property_code / only_active → Optional 처리
#   ✅ 422 Invalid Input 오류 제거
#   ✅ SQLite / PostgreSQL 완전 호환
# ============================================================================
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.master_bank import MasterBank
from app.schemas.master_bank import MasterBankIn, MasterBankOut
from app.core.auth import require_roles, require_token_local

# ─────────────────────────────────────────────
# Router 선언
# ─────────────────────────────────────────────
router = APIRouter(
    prefix="/api/master/banks",
    tags=["master-banks"],
    dependencies=[
        Depends(require_token_local),
        Depends(require_roles(["ADMIN", "SUPERADMIN"]))
    ],
)

# ─────────────────────────────────────────────
# 1️⃣ 목록 조회
# ─────────────────────────────────────────────
@router.get("", response_model=List[MasterBankOut], summary="은행 목록 조회")
def list_banks(
    db: Session = Depends(get_db),
    only_active: int = Query(0, description="1=활성만, 0=전체"),
):
    """은행 전체 목록 조회 (is_active=1 필터 선택적)"""
    q = db.query(MasterBank)
    if int(only_active or 0) == 1:
        q = q.filter(MasterBank.is_active.is_(True))
    rows = q.order_by(MasterBank.name.asc()).all()
    return rows

# ─────────────────────────────────────────────
# 2️⃣ 옵션 목록 (v-select용)
# ─────────────────────────────────────────────
@router.get("/options", summary="은행 옵션 목록(v-select용)")
def bank_options(
    db: Session = Depends(get_db),
    property_code: Optional[str] = Query(None, description="지점코드 (선택)"),
    only_active: Optional[int] = Query(1, description="1=활성만, 0=전체"),
):
    """
    은행 옵션 목록
    ----------------------------------------------------------------------------
    • /api/master/banks/options
    • property_code / only_active 는 선택 파라미터 (422 방지)
    • v-select 용 title/value 구조 반환
    """
    q = db.query(MasterBank)
    if property_code:
        q = q.filter(MasterBank.property_code == property_code)
    if int(only_active or 0) == 1:
        q = q.filter(MasterBank.is_active.is_(True))

    rows = q.order_by(MasterBank.order_no.asc().nulls_last(), MasterBank.name.asc()).all()
    return [{"title": r.name, "value": r.name} for r in rows]

# ─────────────────────────────────────────────
# 3️⃣ 단일 조회
# ─────────────────────────────────────────────
@router.get("/{bank_id}", response_model=MasterBankOut, summary="은행 상세 조회")
def get_bank(bank_id: int, db: Session = Depends(get_db)):
    """은행 상세 조회"""
    row = db.get(MasterBank, bank_id)
    if not row:
        raise HTTPException(status_code=404, detail="은행 정보를 찾을 수 없습니다.")
    return row

# ─────────────────────────────────────────────
# 4️⃣ 신규 생성
# ─────────────────────────────────────────────
@router.post("", response_model=MasterBankOut, summary="은행 등록")
def create_bank(body: MasterBankIn, db: Session = Depends(get_db)):
    """은행 신규 등록"""
    dup = db.query(MasterBank).filter(MasterBank.code == body.code).first()
    if dup:
        raise HTTPException(status_code=409, detail="이미 존재하는 은행코드입니다.")
    row = MasterBank(**body.dict())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

# ─────────────────────────────────────────────
# 5️⃣ 수정
# ─────────────────────────────────────────────
@router.patch("/{bank_id}", response_model=MasterBankOut, summary="은행 수정")
def update_bank(bank_id: int, body: MasterBankIn, db: Session = Depends(get_db)):
    """은행 정보 수정"""
    row = db.get(MasterBank, bank_id)
    if not row:
        raise HTTPException(status_code=404, detail="은행 정보를 찾을 수 없습니다.")
    for k, v in body.dict(exclude_unset=True).items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row

# ─────────────────────────────────────────────
# 6️⃣ 삭제
# ─────────────────────────────────────────────
@router.delete("/{bank_id}", summary="은행 삭제")
def delete_bank(bank_id: int, db: Session = Depends(get_db)):
    """은행 삭제"""
    row = db.get(MasterBank, bank_id)
    if not row:
        raise HTTPException(status_code=404, detail="은행 정보를 찾을 수 없습니다.")
    db.delete(row)
    db.commit()
    return {"ok": True, "deleted_id": bank_id}
