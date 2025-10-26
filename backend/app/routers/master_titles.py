# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/routers/master_titles.py
# Version   : 2025.10-30 · v4.3 (Options Endpoint + ModelDump Fix · SSOT Safe Final)
# Purpose   : Hotel Admin — Master Titles Router (/api/master/titles)
# ----------------------------------------------------------------------------
# 목적:
#   • 직책(Titles) 기준정보 CRUD 및 옵션 엔드포인트 제공
#   • SQLite / PostgreSQL 모두 호환
#   • SSOT Final 구조 완전 일치 — MasterTitles 모델 기반
# ----------------------------------------------------------------------------
# 변경 요약 (v4.3)
#   ✅ /options 엔드포인트 추가 (프런트 HR 모듈 호환)
#   ✅ Pydantic v2 대응 (.model_dump() 사용)
#   ✅ UTC created_at 중복 지정 제거 (모델 기본값 사용)
# ----------------------------------------------------------------------------
# ⚠️ 주의
#   • 모델 파일명은 복수형 "master_titles.py" 임.
#     → import 경로 반드시 “from app.models.master_titles import MasterTitle”
#   • 잘못된 import 시 라우터 자동 로드 스킵됨 (init 시 skip 로그 발생)
# ============================================================================

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.auth import require_user, require_roles

# ✅ 올바른 Import (복수형 모델 / 단수형 스키마)
from app.models.master_titles import MasterTitle
from app.schemas.master_title import MasterTitleIn, MasterTitleOut

# ============================================================================
# Router 설정
# ============================================================================
router = APIRouter(
    prefix="/api/master/titles",
    tags=["master-titles"],
    dependencies=[Depends(require_user)],
)

# ============================================================================
# 1️⃣ 목록 조회
# ----------------------------------------------------------------------------
# • 정렬: order_no → name
# • SQLite 호환: NULLS LAST 미지원 → 단순 asc() 사용
# • 응답 구조: {"ok": True, "items": [...]}
# ============================================================================
@router.get("", response_model=dict, summary="직책 목록 조회")
def list_titles(db: Session = Depends(get_db)):
    """직책 목록 조회 (SSOT 기준)"""
    items = (
        db.query(MasterTitle)
        .order_by(MasterTitle.order_no.asc(), MasterTitle.name.asc())
        .all()
    )
    return {
        "ok": True,
        "items": [MasterTitleOut.model_validate(x) for x in items],
    }

# ============================================================================
# 2️⃣ v-select 옵션용 간소 목록 (/options)
# ----------------------------------------------------------------------------
# • HR 프런트엔드에서 사용
# • 반환: [{"title": "직책명", "value": "코드"}]
# ============================================================================
@router.get("/options", summary="직책 옵션 목록 (v-select용)")
def list_title_options(db: Session = Depends(get_db)):
    """직책 옵션 목록 (활성 항목만)"""
    rows = (
        db.query(MasterTitle)
        .filter(MasterTitle.is_active == True)
        .order_by(MasterTitle.order_no.asc(), MasterTitle.name.asc())
        .all()
    )
    return [{"title": r.name, "value": r.code} for r in rows]

# ============================================================================
# 3️⃣ 신규 생성 (SUPERADMIN 전용)
# ----------------------------------------------------------------------------
# • 중복 code 방지
# • model_dump() 사용 (Pydantic v2 호환)
# ============================================================================
@router.post("", dependencies=[Depends(require_roles(["SUPERADMIN"]))])
def create_title(body: MasterTitleIn, db: Session = Depends(get_db)):
    """직책 신규 생성"""
    if db.query(MasterTitle).filter_by(code=body.code).first():
        raise HTTPException(status_code=400, detail="이미 존재하는 코드입니다.")

    rec = MasterTitle(**body.model_dump())
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return {"ok": True, "id": rec.id}

# ============================================================================
# 4️⃣ 수정 (SUPERADMIN 전용)
# ============================================================================
@router.put("/{id}", dependencies=[Depends(require_roles(["SUPERADMIN"]))])
def update_title(id: int, body: MasterTitleIn, db: Session = Depends(get_db)):
    """직책 정보 수정"""
    rec = db.get(MasterTitle, id)
    if not rec:
        raise HTTPException(status_code=404, detail="해당 직책을 찾을 수 없습니다.")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(rec, k, v)
    db.commit()
    db.refresh(rec)
    return {"ok": True, "id": id}

# ============================================================================
# 5️⃣ 삭제 (SUPERADMIN 전용)
# ============================================================================
@router.delete("/{id}", dependencies=[Depends(require_roles(["SUPERADMIN"]))])
def delete_title(id: int, db: Session = Depends(get_db)):
    """직책 정보 삭제"""
    rec = db.get(MasterTitle, id)
    if not rec:
        raise HTTPException(status_code=404, detail="해당 직책을 찾을 수 없습니다.")
    db.delete(rec)
    db.commit()
    return {"ok": True, "deleted": id}
