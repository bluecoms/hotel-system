from typing import List
from pydantic import BaseModel, Field

class ClosingItem(BaseModel):
    date: str
    status: str

class ClosingCalendarResp(BaseModel):
    items: List[ClosingItem] = Field(default_factory=list)
