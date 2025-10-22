# app/schemas/auth.py
from pydantic import BaseModel
from typing import Optional

class ApproveBody(BaseModel):
    is_active: bool

class UserCreate(BaseModel):
    email: str
    name: str
    is_active: bool = True

class CreateFromEmpIn(BaseModel):
    """사원명부를 기준으로 앱 계정 생성할 때 사용"""
    emp_no: str
    email: str
    name: Optional[str] = None   # ← 변경
    is_active: bool = True
