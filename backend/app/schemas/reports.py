# backend/app/schemas/reports.py
# Python 3.8+ / Pydantic v2
from pydantic import BaseModel, Field, ConfigDict

class SalesTagRow(BaseModel):
    tag: str
    sales_amount: int = Field(default=0, ge=0)
    count: int = Field(default=0, ge=0)

    # v2 권장 설정
    model_config = ConfigDict(from_attributes=True)
