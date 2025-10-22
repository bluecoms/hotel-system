# app/routers/templates.py
# -*- coding: utf-8 -*-
# version: 2025-10-12 Phase 3 Final
"""
Templates Router (Phase 3)
──────────────────────────────────────────────
- CSV 템플릿 다운로드용 라우터
- 단, 현재 시스템은 "원본데이터 업로드" 구조이므로
  정적 템플릿은 의미 없음.
- 향후 필요 시 dataset 스키마에서 동적으로 헤더 생성 예정.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from app.core.locale import set_lang
from app.core.auth import require_user
from app.datasets import schemas as ds_schemas

router = APIRouter(
    prefix="/api/templates",
    tags=["templates"],
    dependencies=[Depends(set_lang), Depends(require_user)],
)

# ─────────────────────────────────────────────
# 공통: dataset 스키마 기반 헤더 자동 추출
# ─────────────────────────────────────────────
def _get_csv_header(dataset: str) -> str:
    """
    datasets.schemas.<dataset> 모듈에서 BaseModel 필드명을 추출하여
    CSV 헤더로 반환.
    """
    schema_cls = getattr(ds_schemas, f"{dataset.title().replace('_', '')}Row", None)
    if not schema_cls:
        raise HTTPException(status_code=404, detail=f"unknown dataset: {dataset}")
    fields = list(schema_cls.model_fields.keys())
    return ",".join(fields) + "\n"


# ─────────────────────────────────────────────
# 엔드포인트: /api/templates/{dataset}.csv
# ─────────────────────────────────────────────
@router.get("/{dataset}.csv", response_class=PlainTextResponse)
def get_dataset_template(dataset: str):
    """
    Dataset 스키마 기반 CSV 헤더 반환
    (예: /api/templates/rooms_status.csv)
    """
    try:
        header_line = _get_csv_header(dataset)
        return PlainTextResponse(header_line, media_type="text/csv; charset=utf-8")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"template-error: {e}")


# ─────────────────────────────────────────────
# Phase 3 요약
# ─────────────────────────────────────────────
# - 정적 템플릿 제거 (employees.csv 등)
# - 향후 dataset별 스키마 기반으로 자동 헤더 반환
# - 프런트엔드는 필요 시 /api/templates/{dataset}.csv 호출로 동적 생성
