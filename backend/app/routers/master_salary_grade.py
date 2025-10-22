# -*- coding: utf-8 -*-
# version: 2025-10-18 v1.1 (Master Salary Grades Router — Stable)
"""
Hotel Admin — Master Salary Grades Router
──────────────────────────────────────────────────────────────────────────────
PATH      : /api/master/salary-grades
PURPOSE   : 급여 등급(Salary Grade) 기준정보 CRUD + 정렬 재배치
USAGE     : HR/Users 모듈의 SalaryGradeTable.vue 및 계약 폼(직급→연봉→월급 계산)과 연동

권한
  • 모든 엔드포인트는 내부 토큰 + 역할 기반 접근 제어
  • ADMIN / SUPERADMIN / HRADMIN 허용

응답 규약
  • 목록(list): {"ok": True, "items": [MasterSalaryGradeOut, ...]}
  • 생성/수정:  MasterSalaryGradeOut
  • 삭제/재정렬: {"ok": True, ...}

비고
  • 연봉(annual_salary)은 "연 기준"으로 저장
  • 계약 등록 폼에서는 연봉/12 → 월 급여로 환산하여 salary(월급)를 산출
  • 프런트 ContractForm에서는 '직급(급여 등급)' 선택 시 이 라우터의 데이터를 사용
──────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from app.core.auth import require_roles, require_token_local
from app.db.session import get_db
from app.models import MasterSalaryGrade
from app.schemas import (
    MasterSalaryGradeIn,
    MasterSalaryGradeOut,
    MasterSalaryGradeReorderBody,
)

# ─────────────────────────────────────────────────────────────
# Router 기본 설정
#  - prefix는 반드시 '/api/master/salary-grades'
#  - tags는 OpenAPI 문서 그룹
#  - dependencies로 공통 권한 체인을 한 번만 지정
# ─────────────────────────────────────────────────────────────
router = APIRouter(
    prefix="/api/master/salary-grades",
    tags=["master-salary-grades"],
    dependencies=[
        Depends(require_token_local),
        Depends(require_roles(["ADMIN", "SUPERADMIN", "HRADMIN"])),
    ],
)


# ─────────────────────────────────────────────────────────────
# 목록 조회
# ─────────────────────────────────────────────────────────────
@router.get("", response_model=dict, summary="급여 등급 목록 조회")
def list_salary_grades(db: Session = Depends(get_db)):
    """
    급여 등급 전체 목록을 정렬 순서(order_no ASC, NULL LAST) → 이름 ASC 로 반환한다.

    반환 형태:
      {
        "ok": True,
        "items": [MasterSalaryGradeOut, ...]
      }
    """
    # 정렬: NULL LAST + 이름 ASC
    items = (
        db.query(MasterSalaryGrade)
        .order_by(
            MasterSalaryGrade.order_no.asc().nulls_last(),
            MasterSalaryGrade.name.asc(),
        )
        .all()
    )
    return {
        "ok": True,
        "items": [MasterSalaryGradeOut.model_validate(x) for x in items],
    }


# ─────────────────────────────────────────────────────────────
# 생성
# ─────────────────────────────────────────────────────────────
@router.post("", response_model=MasterSalaryGradeOut, summary="급여 등급 생성")
def create_salary_grade(body: MasterSalaryGradeIn, db: Session = Depends(get_db)):
    """
    새로운 급여 등급을 생성한다.

    유효성:
      • code(고유) 중복 시 409(CONFLICT)

    반환: 생성된 등급 레코드(MasterSalaryGradeOut)
    """
    # 코드 중복 확인
    exists = (
        db.query(MasterSalaryGrade)
        .filter(MasterSalaryGrade.code == body.code)
        .first()
    )
    if exists:
        raise HTTPException(status_code=409, detail=f"이미 존재하는 코드: {body.code}")

    row = MasterSalaryGrade(**body.dict())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


# ─────────────────────────────────────────────────────────────
# 수정
# ─────────────────────────────────────────────────────────────
@router.patch("/{gid}", response_model=MasterSalaryGradeOut, summary="급여 등급 수정")
def update_salary_grade(gid: int, body: MasterSalaryGradeIn, db: Session = Depends(get_db)):
    """
    급여 등급 정보를 수정한다.

    경로 파라미터:
      • gid: 대상 등급의 PK

    반환: 갱신된 등급 레코드(MasterSalaryGradeOut)
    """
    row = db.query(MasterSalaryGrade).get(gid)
    if not row:
        raise HTTPException(status_code=404, detail="급여 등급을 찾을 수 없습니다.")

    # body는 Pydantic v2 기준 — dict(exclude_unset=True)로 부분 갱신 지원
    for k, v in body.dict(exclude_unset=True).items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row


# ─────────────────────────────────────────────────────────────
# 삭제
# ─────────────────────────────────────────────────────────────
@router.delete("/{gid}", response_model=dict, summary="급여 등급 삭제")
def delete_salary_grade(gid: int, db: Session = Depends(get_db)):
    """
    급여 등급 레코드를 삭제한다.

    경로 파라미터:
      • gid: 대상 등급의 PK

    반환: {"ok": True}
    """
    row = db.query(MasterSalaryGrade).get(gid)
    if not row:
        raise HTTPException(status_code=404, detail="급여 등급을 찾을 수 없습니다.")
    db.delete(row)
    db.commit()
    return {"ok": True}


# ─────────────────────────────────────────────────────────────
# 정렬 순서 변경 (일괄)
# ─────────────────────────────────────────────────────────────
@router.put("/reorder", response_model=dict, summary="급여 등급 순서 재정렬")
def reorder_salary_grades(
    body: MasterSalaryGradeReorderBody = Body(..., description="[{id, order_no}, ...]"),
    db: Session = Depends(get_db),
):
    """
    급여 등급의 정렬 순서를 일괄 업데이트한다.

    요청 Body 예:
      {
        "items": [
          {"id": 10, "order_no": 1},
          {"id": 11, "order_no": 2}
        ]
      }

    반환:
      {"ok": True, "count": <갱신 건수>}
    """
    count = 0
    for item in (body.items or []):
        # 존재 확인 후 업데이트
        affected = (
            db.query(MasterSalaryGrade)
            .filter(MasterSalaryGrade.id == item.id)
            .update({"order_no": item.order_no})
        )
        count += int(affected or 0)

    db.commit()
    return {"ok": True, "count": count}
    
@router.put("/{gid}", response_model=MasterSalaryGradeOut, summary="급여 등급 수정 (PUT 허용)")
def put_salary_grade(gid: int, body: MasterSalaryGradeIn, db: Session = Depends(get_db)):
    """PUT 요청도 PATCH와 동일하게 처리"""
    row = db.query(MasterSalaryGrade).get(gid)
    if not row:
        raise HTTPException(status_code=404, detail="급여 등급을 찾을 수 없습니다.")
    for k, v in body.dict(exclude_unset=True).items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row
