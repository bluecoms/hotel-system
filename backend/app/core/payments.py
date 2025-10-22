# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/core/payments.py
# Version   : 2025.10-30 · v1.3 (Robust Mapping · SSOT Unified)
# Purpose   : Hotel Admin — 결제수단 명칭 표준화 유틸리티
# ----------------------------------------------------------------------------
# 목적:
#   • 업로드·매출·FNB·OTA 등 다양한 원천에서 들어오는 결제수단 명칭을 통일
#   • 프런트/정산/리포트 모두 동일한 코드체계(CASH/CARD/WALLET/...)로 정규화
# ----------------------------------------------------------------------------
# 특징:
#   ✅ 한글·영문·복합 문자열 대응 ("카드결제", "신용(카드)", "KAKAOPAY" 등)
#   ✅ 부분 매칭 기반 자동 인식 (공백/기호 무시)
#   ✅ 결과는 항상 대문자 코드 반환, 미매칭 시 "OTHER"
# ----------------------------------------------------------------------------
# 예시:
#   canon_pay_method("카드")        → CARD
#   canon_pay_method("신용(카드)")  → CARD
#   canon_pay_method("kakaopay")    → KAKAO_PAY
#   canon_pay_method("외상")        → HOUSE
#   canon_pay_method("미등록")      → OTHER
# ============================================================================

import re

PAY_METHOD_ALIASES = {
    # 기본
    "현금": "CASH",
    "카드": "CARD",
    "신용카드": "CARD",
    "체크카드": "CARD",
    "간편": "WALLET",
    "간편결제": "WALLET",
    # 브랜드
    "네이버": "NAVER_PAY",
    "네이버페이": "NAVER_PAY",
    "카카오": "KAKAO_PAY",
    "카카오페이": "KAKAO_PAY",
    "payco": "WALLET",
    "제로": "ZEROPAY",
    "제로페이": "ZEROPAY",
    # 기타
    "상품권": "GIFT",
    "포인트": "POINT",
    "외상": "HOUSE",
    "하우스": "HOUSE",
    "기타": "OTHER",
    "etc": "OTHER",
}


def canon_pay_method(name: str) -> str:
    """
    결제수단 명칭을 표준 코드로 정규화
    (입력 문자열이 비어 있거나 미매칭이면 "OTHER" 반환)
    """
    s = (name or "").strip()
    if not s:
        return "OTHER"

    s_norm = re.sub(r"[\s\-/()]+", "", s).lower()

    # 1️⃣ 직접 키 일치 (완전 매칭)
    for k, v in PAY_METHOD_ALIASES.items():
        if s_norm == k.lower():
            return v

    # 2️⃣ 부분 매칭 (in)
    for k, v in PAY_METHOD_ALIASES.items():
        if k.lower() in s_norm:
            return v

    # 3️⃣ 영문 전용 키워드
    if any(x in s_norm for x in ["card", "visa", "master", "amex"]):
        return "CARD"
    if any(x in s_norm for x in ["cash"]):
        return "CASH"
    if "kakao" in s_norm:
        return "KAKAO_PAY"
    if "naver" in s_norm:
        return "NAVER_PAY"
    if "zero" in s_norm:
        return "ZEROPAY"
    if "gift" in s_norm or "voucher" in s_norm:
        return "GIFT"

    # 4️⃣ 기본값
    return "OTHER"
