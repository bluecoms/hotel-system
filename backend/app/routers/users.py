# 무인증 임시 Users API
from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])

@router.get("")
def list_users():
    return {
        "items": [
            {"id": 1, "name": "Admin", "email": "admin@example.com", "role": "owner"},
            {"id": 2, "name": "Staff", "email": "staff@example.com", "role": "staff"},
        ]
    }
