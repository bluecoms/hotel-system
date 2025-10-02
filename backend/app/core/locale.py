# app/core/locale.py
from typing import Optional
from fastapi import Header, Request

def set_lang(
    request: Request,
    accept_language: Optional[str] = Header(None, alias="Accept-Language"),
):
    # 아주 단순: "ko"로 시작하면 ko, 아니면 en
    lang = "ko" if (accept_language or "").lower().startswith("ko") else "en"
    request.state.lang = lang
    return lang
