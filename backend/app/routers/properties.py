# ============================================================================
# File      : app/routers/properties.py
# Version   : 2025.10-22 v1.0 (Stable / Property Master API)
# Purpose   : Hotel Admin — Property(지점) 마스터 라우터
# ----------------------------------------------------------------------------
# 목적:
#   • 호텔 시스템의 지점(Property) 정보를 관리하고 조회하는 API 제공
#   • 프런트엔드의 Property Selector(지점 선택 드롭다운) 데이터를 공급
# ----------------------------------------------------------------------------
# 설계 원칙:
#   • 지점 목록은 properties 테이블에 저장 (code, name, is_active)
#   • 일반 사용자는 GET 목록만 사용
#   • 슈퍼관리자(SUPERADMIN)만 신규 등록 가능
#   • Employee, Contract 등 주요 도메인은 property_code로 참조
# ----------------------------------------------------------------------------
# 연결 구조:
#   • models.property.Property
#   • main.py → app.include_router(properties.router)
# ----------------------------------------------------------------------------
# 엔드포인트:
#   ✅ GET  /api/properties?is_active=1   → 활성 지점 목록 조회
#   ✅ POST /api/properties                → 신규 지점 등록 (관리자용)
# ============================================================================
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.auth import require_roles
from app.models.property import Property

router = APIRouter(
    prefix="/api/properties",
    tags=["properties"],
)

# ─────────────────────────────────────────────
# 1️⃣ 지점 목록 조회
# ─────────────────────────────────────────────
@router.get("")
def list_properties(
    is_active: bool = Query(True, description="활성 지점만 조회 여부"),
    db: Session = Depends(get_db),
):
    """
    활성 지점 목록 조회 (프런트 Property Selector 용)
    """
    q = db.query(Property)
    if is_active:
        q = q.filter(Property.is_active.is_(True))
    rows = q.order_by(Property.code.asc()).all()

    return {
        "items": [
            {"code": r.code, "name": r.name, "is_active": bool(r.is_active)}
            for r in rows
        ],
        "total": len(rows),
    }

# ─────────────────────────────────────────────
# 2️⃣ 신규 지점 등록 (관리자 전용)
# ─────────────────────────────────────────────
@router.post("", dependencies=[Depends(require_roles(["SUPERADMIN"]))])
def create_property(
    code: str,
    name: str,
    is_active: bool = True,
    db: Session = Depends(get_db),
):
    """
    신규 지점 등록 (슈퍼관리자 전용)
    """
    if db.query(Property).filter(Property.code == code).first():
        raise HTTPException(status_code=400, detail="이미 존재하는 지점 코드입니다.")
    rec = Property(code=code.upper(), name=name.strip(), is_active=is_active)
    db.add(rec)
    db.commit()
    return {"ok": True, "code": rec.code, "name": rec.name}
