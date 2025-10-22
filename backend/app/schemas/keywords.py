# app/schemas/keywords.py
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class KeywordIn(BaseModel):
    group_name: str
    k: str
    v: str = ""
    weight: int = 0
    is_active: bool = True

class KeywordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    group_name: str
    k: str
    v: str
    weight: int
    is_active: bool
    created_at: datetime
