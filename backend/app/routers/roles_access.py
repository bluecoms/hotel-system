# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/routers/roles_access.py
# Version   : 2025-10-31 · v3.6 (SSOT Phase 3.5 Final · DeptAccess Unified)
# Purpose   : Hotel Admin — DeptAccess 기반 RoleAccess API (/api/roles/access)
# ----------------------------------------------------------------------------
# 목적:
#   • 구 users/roles/access 구조를 완전히 폐기하고,
#     route_name + access_scope 기반 DeptAccess 테이블로 단일화.
#   • 모든 요청은 X-Internal-Token 헤더를 이용해 검증 (require_token_local).
#
# 제공 엔드포인트:
#   GET    /api/roles/access            → DeptAccess 전체 목록
#   PUT    /api/roles/access            → DeptAccess Upsert(단건)
#   DELETE /api/roles/access/{route}    → DeptAccess 단건 삭제
#   GET    /api/roles/access/effective  → 서버 계산 기준 실효 권한
#
# 응답 스키마:
#   • app.schemas.roles_access.DeptAccessOut
#   • app.schemas.roles_access.EffectiveDeptAccess
#
# 주요 특징:
#   ✅ DeptAccess 테이블 CRUD 제공 (멱등 Upsert)
#   ✅ /effective: route_name → access_scope 매핑 제공
#   ✅ route_name 정규화 및 access_scope 대문자/중복 제거
#   ✅ 엄격한 4xx/5xx 예외 처리 및 메시지 일관화
#   ✅ 감사로그(write_audit)가 있으면 기록 (없어도 안전하게 동작)
#
# 연계:
#   - Model : app.models.roles_access.DeptAccess
#   - Schema: app.schemas.roles_access.DeptAccessIn / DeptAccessOut / EffectiveDeptAccess
#   - Auth  : app.core.auth.require_token_local (X-Internal-Token)
# ============================================================================

from __future__ import annotations

from typing import List, Dict, Any, Optional, Callable
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.auth import require_token_local
from app.models.roles_access import DeptAccess
from app.schemas.roles_access import (
    DeptAccessIn,
    DeptAccessOut,
    EffectiveDeptAccess,
)

# 감사로그는 선택사항: 없으면 no-op으로 처리
try:
    from app.core.audit import write_audit  # type: ignore
except Exception:  # pragma: no cover
    def write_audit(*args, **kwargs):  # type: ignore
        return None


# ─────────────────────────────────────────────
# Router
# ─────────────────────────────────────────────
router = APIRouter(
    prefix="/api/roles/access",
    tags=["roles-access", "dept-access"],
)


# ─────────────────────────────────────────────
# 유틸: route_name 정규화 & scope 정리
# ─────────────────────────────────────────────
def _normalize_route_name(raw: str) -> str:
    """
    라우트 이름 정규화 규칙 (프런트/백엔드 SSOT):
      - /api/ 프리픽스 제거
      - 선행 슬래시 제거
      - /, . → '-' 치환
      - 중복 '-' 축약
      - 소문자화
    """
    if not raw:
        return ""
    s = raw.strip()
    if s.lower().startswith("/api/"):
        s = s[5:]
    if s.startswith("/"):
        s = s[1:]
    s = s.replace("/", "-").replace(".", "-")
    while "--" in s:
        s = s.replace("--", "-")
    return s.lower()


def _normalize_scopes(scopes: Optional[List[str]]) -> List[str]:
    """
    access_scope 정리:
      - None → []
      - 각 항목 공백 제거, 대문자화
      - 빈 문자열 제거
      - 중복 제거 + 정렬
    """
    if not scopes:
        return []
    cleaned = { (s or "").strip().upper() for s in scopes if (s or "").strip() }
    return sorted(cleaned)


# ─────────────────────────────────────────────
# 1) DeptAccess 목록 조회
#    GET /api/roles/access
# ─────────────────────────────────────────────
@router.get("", response_model=List[DeptAccessOut])
def list_access(
    db: Session = Depends(get_db),
    _token_ok: None = Depends(require_token_local),
):
    """
    DeptAccess 전체 목록 조회
    """
    rows = db.query(DeptAccess).order_by(DeptAccess.route_name.asc()).all()
    return rows


# ─────────────────────────────────────────────
# 2) DeptAccess Upsert (단건)
#    PUT /api/roles/access
# ─────────────────────────────────────────────
@router.put("", response_model=DeptAccessOut)
def upsert_access(
    data: DeptAccessIn,
    db: Session = Depends(get_db),
    _token_ok: None = Depends(require_token_local),
):
    """
    DeptAccess 레코드 생성 또는 수정 (멱등 Upsert)

    요청 예시:
    {
      "route_name": "hr/employees",
      "access_scope": ["ALL_VIEW","FR","HK"]
    }
    """
    route_name = _normalize_route_name(data.route_name)
    if not route_name:
        raise HTTPException(status_code=422, detail="route_name required")

    scope = _normalize_scopes(data.access_scope)

    # Upsert
    row: Optional[DeptAccess] = (
        db.query(DeptAccess).filter(DeptAccess.route_name == route_name).first()
    )
    if row:
        row.access_scope = scope
        action = "deptaccess.update"
    else:
        row = DeptAccess(route_name=route_name, access_scope=scope)
        db.add(row)
        action = "deptaccess.create"

    try:
        db.commit()
        db.refresh(row)
    except Exception as e:  # pragma: no cover
        db.rollback()
        raise HTTPException(status_code=500, detail=f"DB error: {e}")

    # 감사 로그
    try:
        write_audit(db, actor="system", action=action, target=f"route={route_name}", meta={"scope": scope})
    except Exception:
        pass

    return row  # response_model이 DeptAccessOut이므로 자동 직렬화


# ─────────────────────────────────────────────
# 3) DeptAccess 삭제 (단건)
#    DELETE /api/roles/access/{route_name}
# ─────────────────────────────────────────────
@router.delete("/{route_name}", response_model=Dict[str, Any])
def delete_access(
    route_name: str = Path(..., description="삭제할 route_name"),
    db: Session = Depends(get_db),
    _token_ok: None = Depends(require_token_local),
):
    """
    DeptAccess 단일 삭제
    """
    rn = _normalize_route_name(route_name)
    if not rn:
        raise HTTPException(status_code=422, detail="route_name required")

    row: Optional[DeptAccess] = (
        db.query(DeptAccess).filter(DeptAccess.route_name == rn).first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="대상이 없습니다.")

    try:
        db.delete(row)
        db.commit()
    except Exception as e:  # pragma: no cover
        db.rollback()
        raise HTTPException(status_code=500, detail=f"DB error: {e}")

    # 감사 로그
    try:
        write_audit(db, actor="system", action="deptaccess.delete", target=f"route={rn}")
    except Exception:
        pass

    return {"ok": True, "deleted": rn}


# ─────────────────────────────────────────────
# 4) 서버 계산 기준 실효 권한
#    GET /api/roles/access/effective
# ─────────────────────────────────────────────
@router.get("/effective", response_model=EffectiveDeptAccess)
def get_effective_access(
    db: Session = Depends(get_db),
    _token_ok: None = Depends(require_token_local),
):
    """
    서버 계산 기준 실효 접근 권한
    - 모든 DeptAccess 레코드를 가져와 route_name별 access_scope 병합
    - dept는 Phase 3.5 표준으로 "MOP" 기본값 사용
      (※ 향후 토큰/세션에서 사용자 부서를 추출하도록 확장 가능)
    """
    rows: List[DeptAccess] = db.query(DeptAccess).all()

    access_map: Dict[str, List[str]] = {}
    for r in rows:
        rn = _normalize_route_name(r.route_name or "")
        if not rn:
            # route_name 비정상 레코드는 스킵
            continue
        scopes = _normalize_scopes(r.access_scope or [])
        access_map[rn] = scopes

    # SUPERADMIN 토큰 식별로 전체 허용을 주고 싶다면 이곳에서 확장:
    # if is_superadmin(token): access_map = {"*": ["ALL_EDIT"]}

    return EffectiveDeptAccess(dept="MOP", access=access_map)
