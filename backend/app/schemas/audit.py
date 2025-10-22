# app/schemas/audit.py
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Any, Optional

class AuditLogIn(BaseModel):
    action: str
    user: str
    meta: Optional[Any] = None

class AuditLogOut(AuditLogIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ts: datetime
