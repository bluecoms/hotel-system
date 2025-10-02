# app/core/i18n.py
from typing import Dict

MESSAGES: Dict[str, Dict[str, str]] = {
    "ko": {
        "error.rate_range": "요금률은 0~100%여야 합니다.",
        "error.date_invert": "기간이 올바르지 않습니다.",
        "error.duplicate": "중복 데이터입니다.",
        "error.csv_required": "CSV 파일이 필요합니다.",
        "error.csv_headers": "CSV 헤더가 올바르지 않습니다.",
        "error.not_found": "대상이 없습니다.",
        "error.forbidden": "권한이 없습니다.",
        "error.validation": "입력값이 올바르지 않습니다.",
    },
    "en": {
        "error.rate_range": "Rate must be between 0 and 100.",
        "error.date_invert": "Invalid date range.",
        "error.duplicate": "Duplicate data.",
        "error.csv_required": "CSV required.",
        "error.csv_headers": "Invalid CSV headers.",
        "error.not_found": "Not found.",
        "error.forbidden": "Forbidden.",
        "error.validation": "Validation error.",
    },
}

def t(key: str, lang: str = "en") -> str:
    return MESSAGES.get(lang, MESSAGES["en"]).get(key, key)
