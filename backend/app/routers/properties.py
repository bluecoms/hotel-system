# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/routers/properties.py
# Version   : 2025.10-31 · v1.1 (SSOT Stable · MasterProperty 적용)
# Purpose   : Hotel Admin — Property(지점) 기준정보 라우터 (/api/properties)
# ----------------------------------------------------------------------------
# 목적:
#   • 호텔 시스템의 지점(Property) 기준정보 관리 및 조회
#   • 프런트엔드의 Property Selector(지점 선택 드롭다운) 데이터 제공
# ----------------------------------------------------------------------------
# 설계 원칙:
#   • 지점 정보는 master_property 테이블에 저장 (code, name, is_active)
#   • 일반 사용자는 GET 목록만 호출 가능
#   • SUPERADMIN만 신규 등록 가능
#   • 모든 도메인은 property_code로 참조 (Employee, Contract 등)
# ----------------------------------------------------------------------------
# 연결 구조:
#   • models.master_property.MasterProperty
#   • main.py → app.include_router(properties.router)
# ----------------------------------------------------------------------------
# 엔드포인트:
#   ✅ GET  /api/properties?is_active=1   → 활성 지점 목록 조회
#   ✅ POST /api/properties                → 신규 지점 등록 (관리자 전용)
# ============================================================================

from __future__ import annotations
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.auth import require_roles
from app.models.master_property import MasterProperty

# ─────────────────────────────────────────────
# Router 정의
# ─────────────────────────────────────────────
router = APIRouter(
    prefix="/api/properties",
    tags=["properties"],
)

# ============================================================================
# 1️⃣ 지점 목록 조회
# ============================================================================
@router.get("")
def list_properties(
    is_active: bool = Query(True, description="활성 지점만 조회 여부"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """활성 지점 목록 조회 (Property Selector 용)"""
    q = db.query(MasterProperty)
    if is_active:
        q = q.filter(MasterProperty.is_active.is_(True))
    rows = q.order_by(MasterProperty.code.asc()).all()

    return {
        "items": [
            {"code": r.code, "name": r.name, "is_active": bool(r.is_active)}
            for r in rows
        ],
        "total": len(rows),
    }

# ============================================================================
# 2️⃣ 신규 지점 등록 (SUPERADMIN 전용)
# ============================================================================
@router.post("", dependencies=[Depends(require_roles(["SUPERADMIN"]))])
def create_property(
    code: str,
    name: str,
    is_active: bool = True,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """신규 지점 등록 (SUPERADMIN 전용)"""
    code_up = code.strip().upper()
    if db.query(MasterProperty).filter(MasterProperty.code == code_up).first():
        raise HTTPException(status_code=400, detail="이미 존재하는 지점 코드입니다.")

    rec = MasterProperty(code=code_up, name=name.strip(), is_active=is_active)
    db.add(rec)
    db.commit()
    return {"ok": True, "code": rec.code, "name": rec.name, "is_active": rec.is_active}
