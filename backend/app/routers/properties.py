# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/routers/properties.py
# Version   : 2025.10-26 · v2.0 (SSOT Final · 운영 전용 조회 API)
# Purpose   : Hotel Admin — Property(지점) 운영용 기준정보 라우터 (/api/properties)
# ----------------------------------------------------------------------------
# 목적:
#   • 호텔 시스템 전역에서 사용하는 지점(Property) 목록 조회 API
#   • 프런트엔드 Property Selector(지점 선택기) 및 각 도메인(property_code 참조)에 사용
# ----------------------------------------------------------------------------
# 설계 원칙:
#   • 운영용 Property 테이블(app/models/property.py) 기반 (Master와 분리)
#   • CRUD는 마스터 라우터(/api/master/properties)에서만 수행
#   • 운영 라우터는 GET 조회 전용으로 제한 (읽기 전용)
# ----------------------------------------------------------------------------
# 연결 구조:
#   • models.property.Property
#   • main.py → app.include_router(properties.router)
# ----------------------------------------------------------------------------
# 엔드포인트:
#   ✅ GET  /api/properties?is_active=1   → 활성 지점 목록 조회
# ----------------------------------------------------------------------------
# 사용처:
#   • 프런트엔드 전역 Property Selector
#   • Employees / Contracts / Closing / Upload 등 모든 운영 도메인
# ============================================================================

from __future__ import annotations
from typing import Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.property import Property

# ─────────────────────────────────────────────
# Router 정의
# ─────────────────────────────────────────────
router = APIRouter(
    prefix="/api/properties",
    tags=["properties"],
)

# ============================================================================
# 1️⃣ 지점 목록 조회 (운영 전용)
# ============================================================================
@router.get("", summary="운영용 지점 목록 조회")
def list_properties(
    is_active: bool = Query(True, description="활성 지점만 조회 여부"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    운영용 Property 테이블에서 지점 목록을 조회한다.
    - SSOT(MasterProperty)에서 동기화된 데이터 기준
    - 활성 지점만 필터링 가능
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
