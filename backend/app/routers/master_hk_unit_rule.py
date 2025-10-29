# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/routers/master_hk_unit_rule.py
# Version   : 2025-11-09 · v1.1 (SSOT Stable · CRUD + Filter)
# Purpose   : Hotel Admin — 하우스키핑 유닛 계산 기준정보 API
# ----------------------------------------------------------------------------
# 목적:
#   • 하우스키핑 업무의 유닛 계산 규칙(MasterHkUnitRule) CRUD 제공
#   • /api/master/hk-unit-rules
# ----------------------------------------------------------------------------
# 설계 원칙:
#   • MasterTable(SSOT) 규약에 맞춰 구성
#   • condition_code 는 유니크 키 (예: ROOM_STD, ROOM_DLX, MOVE_FLOOR 등)
#   • unit_value 는 float (예: 1.0, 0.3, 0.2)
#   • 사용 여부 is_active 로 제어
# ----------------------------------------------------------------------------
# 엔드포인트:
#   ✅ GET    /api/master/hk-unit-rules        → 전체 목록 조회
#   ✅ POST   /api/master/hk-unit-rules        → 신규 등록
#   ✅ PUT    /api/master/hk-unit-rules/{code} → 수정
#   ✅ DELETE /api/master/hk-unit-rules/{code} → 삭제
# ----------------------------------------------------------------------------
# 연계 구조:
#   • models.master_hk_unit_rule.MasterHkUnitRule
#   • schemas.master_hk_unit_rule.HkUnitRule{Create,Update,Out}
#   • 프런트엔드 MasterData.vue > “운영 기준정보” 탭에서 관리됨
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.master_hk_unit_rule import MasterHkUnitRule
from app.schemas.master_hk_unit_rule import (
    HkUnitRuleCreate,
    HkUnitRuleUpdate,
    HkUnitRuleOut,
)

# ─────────────────────────────────────────────
# Router 정의
# ─────────────────────────────────────────────
router = APIRouter(
    prefix="/api/master/hk-unit-rules",
    tags=["master-hk-unit-rules"],
)

# ============================================================================
# 1️⃣ 목록 조회 (필터 포함)
# ============================================================================
@router.get("", response_model=List[HkUnitRuleOut])
def list_unit_rules(
    is_active: bool = Query(None, description="활성 여부 필터 (True/False)"),
    db: Session = Depends(get_db),
):
    """
    하우스키핑 유닛 규칙 전체 조회
    - /api/master/hk-unit-rules?is_active=true
    """
    q = db.query(MasterHkUnitRule)
    if is_active is not None:
        q = q.filter(MasterHkUnitRule.is_active == is_active)
    return q.order_by(MasterHkUnitRule.order_no.asc(), MasterHkUnitRule.id.asc()).all()


# ============================================================================
# 2️⃣ 신규 등록
# ============================================================================
@router.post("", response_model=HkUnitRuleOut)
def create_unit_rule(
    body: HkUnitRuleCreate,
    db: Session = Depends(get_db),
):
    """
    하우스키핑 유닛 규칙 신규 등록
    - condition_code 중복 시 400 반환
    """
    if db.query(MasterHkUnitRule).filter(
        MasterHkUnitRule.condition_code == body.condition_code
    ).first():
        raise HTTPException(status_code=400, detail="이미 존재하는 규칙 코드입니다.")

    obj = MasterHkUnitRule(**body.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# ============================================================================
# 3️⃣ 수정
# ============================================================================
@router.put("/{condition_code}", response_model=HkUnitRuleOut)
def update_unit_rule(
    condition_code: str,
    body: HkUnitRuleUpdate,
    db: Session = Depends(get_db),
):
    """
    기존 하우스키핑 유닛 규칙 수정
    - 존재하지 않으면 404 반환
    """
    obj = (
        db.query(MasterHkUnitRule)
        .filter(MasterHkUnitRule.condition_code == condition_code)
        .first()
    )
    if not obj:
        raise HTTPException(status_code=404, detail="해당 규칙을 찾을 수 없습니다.")

    for k, v in body.dict(exclude_unset=True).items():
        setattr(obj, k, v)

    db.commit()
    db.refresh(obj)
    return obj


# ============================================================================
# 4️⃣ 삭제
# ============================================================================
@router.delete("/{condition_code}")
def delete_unit_rule(
    condition_code: str,
    db: Session = Depends(get_db),
):
    """
    하우스키핑 유닛 규칙 삭제
    - 존재하지 않으면 404 반환
    """
    obj = (
        db.query(MasterHkUnitRule)
        .filter(MasterHkUnitRule.condition_code == condition_code)
        .first()
    )
    if not obj:
        raise HTTPException(status_code=404, detail="해당 규칙을 찾을 수 없습니다.")

    db.delete(obj)
    db.commit()
    return {"ok": True, "deleted_code": condition_code}


# ============================================================================
# ✅ EOF — app/routers/master_hk_unit_rule.py (v1.1 · SSOT Stable)
# ============================================================================
