# ===========================================================
# Hotel Admin — app/routers/auth.py (2025-10-15 복구판)
# -----------------------------------------------------------
# 목적:
#   - 로그인, 세션 확인, 비밀번호 변경 등 인증 관련 API 라우터
#   - app/core/auth.py 내부 로직을 라우터 형태로 노출
# ===========================================================
from fastapi import APIRouter, Depends
from app.core import auth

router = auth.router  # core/auth.py 안의 router 객체 그대로 가져옴
