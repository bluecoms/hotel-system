# ============================================================================
# File      : app/schemas/master_position.py
# Version   : 2025.10-28 · v1.0 (Initial Create)
# Purpose   : Hotel Admin — Master Position Schema (직위 기준정보)
# ----------------------------------------------------------------------------
# 목적:
#   • MasterPosition ORM ↔ API 직렬화/역직렬화용 Pydantic 스키마 정의
#   • 기준정보(Master) 공통 CRUD 규격을 따름
# ----------------------------------------------------------------------------
# 구조:
#   - MasterPositionBase : 공통 필드 정의
#   - MasterPositionIn   : 생성/수정 입력용
#   - MasterPositionOut  : 조회/출력용
#   - MasterPositionOption : 프런트 v-select 옵션용(title/value)
# ----------------------------------------------------------------------------
# 연계:
#   • Model : app.models.master_position.MasterPosition
#   • Router: /api/master/positions
# ============================================================================
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

# ─────────────────────────────────────────────
# 공통 Base
# ─────────────────────────────────────────────
class MasterPositionBase(BaseModel):
    code: str = Field(..., description="직위 코드 (예: DIR, MGR)")
    name: str = Field(..., description="직위명 (예: 부장, 과장)")
    order_no: Optional[int] = Field(0, description="정렬 순서 (낮을수록 위)")
    is_active: bool = Field(True, description="활성 여부")

# ─────────────────────────────────────────────
# 입력 (생성/수정용)
# ─────────────────────────────────────────────
class MasterPositionIn(MasterPositionBase):
    pass

# ─────────────────────────────────────────────
# 출력 (조회용)
# ─────────────────────────────────────────────
class MasterPositionOut(MasterPositionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
        orm_mode = True

# ─────────────────────────────────────────────
# v-select 옵션용
# ─────────────────────────────────────────────
class MasterPositionOption(BaseModel):
    value: str
    title: str

    class Config:
        orm_mode = True
