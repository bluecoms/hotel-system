# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/core/locale.py
# Version   : 2025.10-30 · v1.2 (Robust Accept-Language · SSOT Ready)
# Purpose   : Hotel Admin — Locale / Language Middleware
# ----------------------------------------------------------------------------
# 목적:
#   • FastAPI Request 객체에 언어코드(request.state.lang)를 주입
#   • "Accept-Language" 헤더 또는 쿼리/기본값 기반으로 간단한 다국어 처리
# ----------------------------------------------------------------------------
# 특징:
#   ✅ Accept-Language 헤더 파싱 ("ko", "ko-KR;q=0.9" → ko)
#   ✅ 쿼리파라미터 lang=ko|en 지원 (우선순위 높음)
#   ✅ 기본값은 en (비한글 요청)
# ----------------------------------------------------------------------------
# 예시:
#   GET /api/...   Accept-Language: ko        → request.state.lang = "ko"
#   GET /api/...   ?lang=en                   → request.state.lang = "en"
#   GET /api/...   Accept-Language: fr,ko;q=0.8 → request.state.lang = "ko"
# ============================================================================

from typing import Optional
from fastapi import Header, Request


def _extract_lang(accept_language: Optional[str]) -> str:
    """
    HTTP Accept-Language 헤더에서 언어코드 추출
    - "ko-KR, en;q=0.8" → "ko"
    - "en-US" → "en"
    """
    if not accept_language:
        return "en"
    try:
        parts = accept_language.split(",")
        for p in parts:
            code = p.strip().split(";")[0]
            if code.lower().startswith("ko"):
                return "ko"
            if code.lower().startswith("en"):
                return "en"
    except Exception:
        pass
    return "en"


def set_lang(
    request: Request,
    accept_language: Optional[str] = Header(None, alias="Accept-Language"),
):
    """
    요청에서 언어 감지 및 주입
    - 쿼리스트링(lang=ko|en)이 있으면 우선 적용
    - 없으면 Accept-Language 헤더 기반으로 결정
    """
    # 쿼리 파라미터(lang) 우선
    query_lang = request.query_params.get("lang", "").lower().strip()
    if query_lang in ("ko", "en"):
        lang = query_lang
    else:
        lang = _extract_lang(accept_language)

    # FastAPI state에 저장
    request.state.lang = lang
    return lang
