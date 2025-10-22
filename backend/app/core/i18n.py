# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/core/i18n.py
# Version   : 2025-10-31 · v3.6 (SSOT Stable)
# Purpose   : 국제화(i18n) 메시지 관리 유틸
# ----------------------------------------------------------------------------
# 목적:
#   • 다국어 메시지 사전 관리 (ko / en)
#   • 백엔드 전체 공통 에러/알림 메시지 키 일원화
#   • 라우터, 서비스, 정책 등에서 t(key, lang) 형태로 사용
# ----------------------------------------------------------------------------
# 특징:
#   ✅ 안전한 Fallback (요청 언어 → 영어 → 키 자체)
#   ✅ SSOT 통합 키 네이밍 규칙 적용 (error.*, info.*, warn.*)
#   ✅ Python 3.8/3.9 호환
# ----------------------------------------------------------------------------
# 사용 예:
#   from app.core.i18n import t
#   raise HTTPException(status_code=400, detail=t("error.validation", "ko"))
# ============================================================================

from typing import Dict


# ─────────────────────────────────────────────
# 다국어 메시지 사전
# ─────────────────────────────────────────────
MESSAGES: Dict[str, Dict[str, str]] = {
    "ko": {
        # 오류 메시지
        "error.rate_range": "요금률은 0~100%여야 합니다.",
        "error.date_invert": "기간이 올바르지 않습니다.",
        "error.duplicate": "중복 데이터입니다.",
        "error.csv_required": "CSV 파일이 필요합니다.",
        "error.csv_headers": "CSV 헤더가 올바르지 않습니다.",
        "error.not_found": "대상이 없습니다.",
        "error.forbidden": "권한이 없습니다.",
        "error.validation": "입력값이 올바르지 않습니다.",
        "error.internal": "서버 내부 오류가 발생했습니다.",
        "error.merge_engine": "머지 엔진 처리 중 오류가 발생했습니다.",

        # 안내 메시지
        "info.success": "요청이 성공적으로 처리되었습니다.",
        "info.saved": "저장되었습니다.",
        "info.deleted": "삭제되었습니다.",

        # 경고 메시지
        "warn.deprecated": "이 기능은 더 이상 지원되지 않습니다.",
    },

    "en": {
        # Error
        "error.rate_range": "Rate must be between 0 and 100.",
        "error.date_invert": "Invalid date range.",
        "error.duplicate": "Duplicate data.",
        "error.csv_required": "CSV file is required.",
        "error.csv_headers": "Invalid CSV headers.",
        "error.not_found": "Target not found.",
        "error.forbidden": "Forbidden.",
        "error.validation": "Invalid input values.",
        "error.internal": "Internal server error.",
        "error.merge_engine": "An error occurred in the merge engine.",

        # Info
        "info.success": "Request completed successfully.",
        "info.saved": "Saved successfully.",
        "info.deleted": "Deleted successfully.",

        # Warning
        "warn.deprecated": "This feature is deprecated.",
    },
}


# ─────────────────────────────────────────────
# 번역 헬퍼
# ─────────────────────────────────────────────
def t(key: str, lang: str = "en") -> str:
    """
    다국어 메시지 조회 함수.
    - 요청 언어(lang)에서 검색 → en → key 순으로 fallback.
    """
    lang = (lang or "en").lower()
    lang_table = MESSAGES.get(lang, MESSAGES["en"])
    return lang_table.get(key) or MESSAGES["en"].get(key) or key
