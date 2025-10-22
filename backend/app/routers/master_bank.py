# ============================================================================
# File      : app/routers/master_bank.py
# Version   : 2025.10-22 v1.0 (Initial Create · SSOT Stable)
# Purpose   : Hotel Admin — Master Banks Router (/api/master/banks)
# ----------------------------------------------------------------------------
# 목적:
#   • 은행(Banks) 기준정보 CRUD 관리
#   • 은행코드(code), 은행명(name), 약칭(alias), 활성여부(is_active) 관리
#   • 향후 법인계좌(bank_accounts.bank_code FK) 및 직원계좌(bank_code) 참조 기반
# ----------------------------------------------------------------------------
# 권한:
#   • require_token_local 필수
#   • ADMIN / SUPERADMIN 권한 필요
# ============================================================================
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
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
    q = db.query(MasterBank)
    if int(only_active or 0) == 1:
        q = q.filter(MasterBank.is_active.is_(True))
    rows = q.order_by(MasterBank.name.asc()).all()
    return rows

# ─────────────────────────────────────────────
# 2️⃣ 단일 조회
# ─────────────────────────────────────────────
@router.get("/{bank_id}", response_model=MasterBankOut, summary="은행 상세 조회")
def get_bank(bank_id: int, db: Session = Depends(get_db)):
    row = db.query(MasterBank).get(bank_id)
    if not row:
        raise HTTPException(status_code=404, detail="은행 정보를 찾을 수 없습니다.")
    return row

# ─────────────────────────────────────────────
# 3️⃣ 신규 생성
# ─────────────────────────────────────────────
@router.post("", response_model=MasterBankOut, summary="은행 등록")
def create_bank(body: MasterBankIn, db: Session = Depends(get_db)):
    dup = db.query(MasterBank).filter(MasterBank.code == body.code).first()
    if dup:
        raise HTTPException(status_code=409, detail="이미 존재하는 은행코드입니다.")
    row = MasterBank(**body.dict())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

# ─────────────────────────────────────────────
# 4️⃣ 수정
# ─────────────────────────────────────────────
@router.patch("/{bank_id}", response_model=MasterBankOut, summary="은행 수정")
def update_bank(bank_id: int, body: MasterBankIn, db: Session = Depends(get_db)):
    row = db.query(MasterBank).get(bank_id)
    if not row:
        raise HTTPException(status_code=404, detail="은행 정보를 찾을 수 없습니다.")
    for k, v in body.dict().items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row

# ─────────────────────────────────────────────
# 5️⃣ 삭제
# ─────────────────────────────────────────────
@router.delete("/{bank_id}", summary="은행 삭제")
def delete_bank(bank_id: int, db: Session = Depends(get_db)):
    row = db.query(MasterBank).get(bank_id)
    if not row:
        raise HTTPException(status_code=404, detail="은행 정보를 찾을 수 없습니다.")
    db.delete(row)
    db.commit()
    return {"ok": True, "deleted_id": bank_id}
