# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/routers/master_titles.py
# Version   : 2025.10-30 · v4.2 (Import Fix · SSOT Safe Final)
# Purpose   : Hotel Admin — Master Titles Router (/api/master/titles)
# ----------------------------------------------------------------------------
# 목적:
#   • 직책(Titles) 기준정보 CRUD 라우터
#   • SQLite / PostgreSQL 모두 호환
#   • SSOT Final 구조 완전 일치 — MasterTitles 모델 기반
# ----------------------------------------------------------------------------
# ⚠️ 중요 (2025-10-30 Import 오류 관련)
#   • 모델 파일명은 복수형 "master_titles.py" 임.
#     → 절대 단수형 master_title 로 import 하지 말 것.
#   • FastAPI 라우터 초기화 시, 내부 import 에러가 발생하면
#     __init__.py 의 _load_router() 가 try/except 로 스킵 처리되어
#     “[routers:init] skip master_titles: No module named …” 로그가 남고
#     /api/master/titles 엔드포인트가 자동으로 등록되지 않음.
#   • 따라서 import 경로는 반드시 아래처럼 “복수형”으로 유지해야 함.
# ============================================================================
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.auth import require_user, require_roles

# ✅ 올바른 Import (복수형 파일명)
#    - 모델 파일명: app/models/master_titles.py
#    - 스키마 파일명: app/schemas/master_title.py (단수형)
from app.models.master_titles import MasterTitle
from app.schemas.master_title import MasterTitleIn, MasterTitleOut

# ============================================================================
# Router 정의
#   • prefix : /api/master/titles
#   • tags   : master-titles
#   • 인증   : require_user (기본 보호)
# ============================================================================
router = APIRouter(
    prefix="/api/master/titles",
    tags=["master-titles"],
    dependencies=[Depends(require_user)],
)

# ============================================================================
# 목록 조회 (SQLite 호환)
#   • 정렬: order_no → name
#   • SQLite는 NULLS LAST 미지원 → 단순 asc() 사용
# ============================================================================
@router.get("", response_model=dict, summary="직책 목록 조회")
def list_titles(db: Session = Depends(get_db)):
    """
    직책 목록 조회 (SSOT 기준)
    ----------------------------------------------------------------------------
    • SQLite / PostgreSQL 공통 호환
    • 응답 구조: {"ok": True, "items": [ ... ]}
    """
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
# 신규 생성 (SUPERADMIN 전용)
#   • 중복 code 방지
# ============================================================================
@router.post("", dependencies=[Depends(require_roles(["SUPERADMIN"]))])
def create_title(body: MasterTitleIn, db: Session = Depends(get_db)):
    """직책 신규 생성"""
    if db.query(MasterTitle).filter_by(code=body.code).first():
        raise HTTPException(status_code=400, detail="이미 존재하는 코드입니다.")

    rec = MasterTitle(**body.dict(), created_at=datetime.utcnow())
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return {"ok": True, "id": rec.id}

# ============================================================================
# 수정 (SUPERADMIN 전용)
# ============================================================================
@router.put("/{id}", dependencies=[Depends(require_roles(["SUPERADMIN"]))])
def update_title(id: int, body: MasterTitleIn, db: Session = Depends(get_db)):
    """직책 정보 수정"""
    rec = db.get(MasterTitle, id)
    if not rec:
        raise HTTPException(status_code=404, detail="해당 직책을 찾을 수 없습니다.")
    for k, v in body.dict(exclude_unset=True).items():
        setattr(rec, k, v)
    db.commit()
    db.refresh(rec)
    return {"ok": True, "id": id}

# ============================================================================
# 삭제 (SUPERADMIN 전용)
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
