# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/core/normalize.py
# Version   : 2025.10-30 · v1.4 (Keep-Logic · Safer · SSOT Helpers)
# Purpose   : Hotel Admin — Generic CSV Normalizers (간이 Canon 전처리)
# ----------------------------------------------------------------------------
# 목적:
#   • 업로드 원본(csv/html 텍스트)를 간이 Canon CSV로 정규화
#   • SalesFront / RoomsStatus / BankLedger / Reservations 지원
#   • SSOT Merge Engine 이전 단계(업로드 처리)에 쓰는 경량 유틸
# ----------------------------------------------------------------------------
# 변경 로그:
#   v1.4 (2025-10-30)
#     ✅ HTML 감지 보완(<table> … </table>) 및 헤더 승격 개선
#     ✅ 날짜/금액/부호/공백 파서 안정화 (한국어/기호 혼재 방어)
#     ✅ 0행 결과 시 422 오류 반환 (사용자 피드백 명확화)
#     ✅ rooms_status 들여쓰기 버그 수정
#     ✅ 주석/도큐먼트 보강(SSOT 스타일)
# ============================================================================

import csv
import io
import re
from typing import Optional, List, Tuple
from fastapi import HTTPException

_SF_CANON_FIELDS = ["business_date", "property_code", "tag", "amount"]

# ============================================================================
# 공통 CSV 유틸
# ----------------------------------------------------------------------------
def strip_bom_text(s: str) -> str:
    """UTF-8 BOM 제거"""
    return s.lstrip("\ufeff")


def bytes_to_text_guess(raw: bytes) -> str:
    """
    업로드 바이트 → 텍스트 (인코딩 추정)
    - utf-8-sig / cp949 / euc-kr 순으로 시도 후 fallback=‘utf-8 ignore’
    """
    for enc in ("utf-8-sig", "cp949", "euc-kr", "ms949"):
        try:
            return raw.decode(enc)
        except Exception:
            pass
    return raw.decode("utf-8", errors="ignore")


def promote_header(csv_text: str) -> str:
    """
    CSV 헤더 추정 후 최상단 승격:
    - 앞 50줄 내에서 '문자열 컬럼 수' 가 많은 라인을 헤더로 간주
    """
    rows = csv_text.splitlines()
    if not rows:
        return csv_text
    best_i, best_score = 0, -10**9
    for i, line in enumerate(rows[:50]):
        if not line.strip():
            continue
        parts = [c.strip() for c in line.split(",")]
        nonnum = sum(1 for c in parts if not c.replace(".", "", 1).isdigit())
        score = len(parts) + nonnum * 2
        if score > best_score:
            best_i, best_score = i, score
    out = "\n".join([rows[best_i]] + rows[best_i + 1 :])
    return out if out.endswith("\n") else (out + "\n")


def read_upload_to_csv_text(file) -> Tuple[str, str]:
    """
    업로드 파일(UploadFile-like) → 텍스트 CSV
    - HTML table 감지 시 헤더 승격 없이 원문 반환
    - 일반 텍스트는 헤더 승격(promote_header) 적용
    """
    raw = file.file.read()
    text = bytes_to_text_guess(raw)
    low = text.lower()
    is_html_table = ("<table" in low and "</table" in low)
    csv_text = text if is_html_table else promote_header(text)
    if not csv_text.endswith("\n"):
        csv_text += "\n"
    return csv_text, ".csv"


def norm_amount(x: str) -> float:
    """
    통화 문자열 → 실수
    - 콤마/원화/공백 제거
    - (1,234) → -1234 / 1,234- → -1234
    - ‘−’/‘–’ → ‘-’ 치환
    """
    s = (x or "")
    s = (
        s.replace(",", "")
        .replace("₩", "")
        .replace("￦", "")
        .replace("원", "")
        .replace("\u00a0", "")
        .replace("\u2009", "")
        .replace(" ", "")
    )
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]
    if s.endswith("-") and s[:-1].replace(".", "", 1).isdigit():
        s = "-" + s[:-1]
    s = s.replace("−", "-").replace("–", "-")
    try:
        return float(s or 0)
    except Exception:
        return 0.0


def is_summary_row(r: dict) -> bool:
    """합계/총계/잔액 등 요약 라인 또는 전부 공백 라인 감지"""
    try:
        text = " ".join([str(v or "") for v in r.values()]).lower()
    except Exception:
        return False
    return any(word in text for word in ["합계", "총계", "잔액", "이월", "소계", "총합", "누계"]) or not any(
        str(v or "").strip() for v in r.values()
    )


def pick(row: dict, candidates: List[str]) -> str:
    """여러 헤더 후보 중 첫 번째 비어있지 않은 값을 선택"""
    for k in candidates:
        if k in row and row[k] is not None:
            v = str(row[k]).strip()
            if v != "":
                return v
    return ""


def _parse_date_to_ymd(s: str) -> str:
    """자유형 날짜 문자열 → YYYY-MM-DD 변환 (최대한 완화된 파서)"""
    import datetime as dt
    if not s:
        return ""
    s = str(s).strip()
    cand = s[:10]
    for sep in ("-", ".", "/"):
        try:
            return dt.datetime.strptime(cand, f"%Y{sep}%m{sep}%d").date().isoformat()
        except Exception:
            pass
    try:
        return dt.datetime.strptime(s.split()[0], "%m/%d/%Y").date().isoformat()
    except Exception:
        pass
    m = re.fullmatch(r"(\d{4})(\d{2})(\d{2})", re.sub(r"\D", "", s))
    if m:
        y, mth, d = m.groups()
        try:
            return dt.date(int(y), int(mth), int(d)).isoformat()
        except Exception:
            return ""
    m = re.search(r"\b(\d{4})[-./](\d{1,2})[-./](\d{1,2})\b", s)
    if m:
        y, mth, d = m.groups()
        try:
            return dt.date(int(y), int(mth), int(d)).isoformat()
        except Exception:
            return ""
    return ""


def _clean_room_no(s: str) -> str:
    """객실번호 추출: 영숫자/하이픈만 남김"""
    if not s:
        return ""
    s = str(s).strip()
    m = re.search(r"[A-Za-z0-9\-]+", s.replace(" ", ""))
    return m.group(0) if m else s


# ============================================================================
# Sales Front
# ----------------------------------------------------------------------------
def normalize_sales_front_to_canon(
    raw_csv_text: str,
    fallback_business_date: Optional[str],
    fallback_property_code: str,
):
    sio = io.StringIO(raw_csv_text)
    dr = csv.DictReader(sio)
    if not dr.fieldnames:
        raise HTTPException(422, "invalid-csv")

    rows = list(dr)
    date_keys = ["business_date", "date", "biz_date", "입실일시", "매출일자", "일자"]

    def row_date(r):
        for k in date_keys:
            if k in r and (r.get(k) or "").strip():
                dd = _parse_date_to_ymd(str(r.get(k)))
                if dd:
                    return dd
        return ""

    bd = (fallback_business_date or "").strip()
    if not bd:
        for r in rows:
            dd = row_date(r)
            if dd:
                bd = dd
                break
    if not bd:
        raise HTTPException(422, "business_date required")

    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=_SF_CANON_FIELDS, lineterminator="\n")
    w.writeheader()

    n_rows = 0
    for r in rows:
        d = row_date(r) or bd
        w.writerow(
            {
                "business_date": d,
                "property_code": (r.get("property_code") or fallback_property_code or "MOP").strip().upper(),
                "tag": (r.get("tag") or r.get("folio_no") or r.get("적요") or r.get("비고") or "").strip(),
                "amount": str(int(round(norm_amount(r.get("amount") or r.get("매출금액") or r.get("금액") or "0")))),
            }
        )
        n_rows += 1

    if n_rows == 0:
        raise HTTPException(422, "no-rows")
    return out.getvalue(), bd


# ============================================================================
# Bank Ledger (board.py와 서명/필드 호환)
# ----------------------------------------------------------------------------
_BANK_FIELDS = [
    "business_date",
    "property_code",
    "account_code",
    "direction",
    "amount",
    "balance_after",
    "note",
    "branch",
    "txn_time",
]

def normalize_bank_ledger_to_canon(
    raw_csv_text: str,
    fallback_business_date: Optional[str],
    fallback_property_code: str,
    account_code: str = "NH-UNKNOWN",
) -> Tuple[str, str]:
    import re

    # 1) 숫자 3자리 콤마 엉킴 방지(1,234,56 → 1234,56 같은 경우)
    cleaned = re.sub(r"(?<=\d),(?=\d{3}\b)", "", raw_csv_text)

    rdr = csv.DictReader(io.StringIO(cleaned))
    if not rdr.fieldnames:
        raise HTTPException(422, "invalid-csv")

    rows = list(rdr)

    # 2) 대표 business_date 결정
    bd = (fallback_business_date or "").strip()
    if not bd:
        for r in rows:
            bd = (r.get("business_date") or r.get("거래일자") or r.get("date") or "").strip()
            if bd:
                bd = _parse_date_to_ymd(bd)
            if bd:
                break
    if not bd:
        raise HTTPException(422, "business_date required")

    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=_BANK_FIELDS, lineterminator="\n")
    w.writeheader()

    def _amt(x: Optional[str]) -> float:
        s = (x or "").replace(",", "").replace("원", "").replace(" ", "").strip()
        if s.startswith("(") and s.endswith(")"):
            s = "-" + s[1:-1]
        try:
            return float(s or 0)
        except Exception:
            return 0.0

    n_rows = 0
    for r in rows:
        txt = " ".join(str(v or "") for v in r.values()).strip()
        if not txt or any(k in txt for k in ["합계", "총계", "조회 결과"]):
            continue

        out_amt = _amt(r.get("출금금액(원)") or r.get("출금금액") or r.get("출금") or r.get("out"))
        in_amt = _amt(r.get("입금금액(원)") or r.get("입금금액") or r.get("입금") or r.get("in"))
        bal = _amt(r.get("거래 후 잔액(원)") or r.get("거래후잔액(원)") or r.get("잔액") or r.get("balance"))

        if out_amt == 0 and in_amt == 0:
            continue

        direction = "OUT" if out_amt else "IN"
        amount = abs(out_amt or in_amt)

        memo = (r.get("이체메모") or r.get("이체 메모") or "").strip()
        note = " / ".join(
            [
                (r.get("거래내용") or "").strip(),
                (r.get("거래기록사항") or "").strip(),
                memo,
            ]
        ).strip(" /")

        w.writerow(
            {
                "business_date": bd,
                "property_code": (fallback_property_code or "MOP").strip().upper(),
                "account_code": account_code,
                "direction": direction,
                "amount": str(int(amount)) if amount else "0",
                "balance_after": str(int(bal)) if bal else "",
                "note": note,
                "branch": (r.get("거래점") or "").strip(),
                "txn_time": (r.get("거래시간") or "").strip(),
            }
        )
        n_rows += 1

    if n_rows == 0:
        raise HTTPException(422, "no-rows")
    return out.getvalue(), bd


# ============================================================================
# Rooms Status
# ----------------------------------------------------------------------------
_RS_CANON_FIELDS = ["business_date", "property_code", "room_no", "status_code", "is_dirty", "hk_note"]

def normalize_rooms_status_to_canon(
    raw_csv_text: str,
    fallback_business_date: Optional[str],
    fallback_property_code: str,
) -> Tuple[str, str]:
    sio = io.StringIO(raw_csv_text)
    dr = csv.DictReader(sio)
    if not dr.fieldnames:
        raise HTTPException(422, "invalid-csv")
    rows = list(dr)

    # ▼ 행별 날짜 계산기: 가능한 모든 헤더명+자유 텍스트에서 YYYY-MM-DD 추출
    def row_date(r: dict) -> str:
        # 1) 흔한 컬럼명 우선 시도
        cand_keys = [
            "business_date",
            "date",
            "biz_date",
            "입실일시",
            "입실일",
            "체크인",
            "체크인일시",
            "예약일시",
            "예약일",
            "checkin",
            "CHECKIN",
            "일자",
            # 추가 변형
            "입실일자",
            "체크인일자",
            "투숙시작",
            "투숙시작일",
            "투숙일자",
            "도착일",
            "도착일자",
            "Arrival",
            "ARRIVAL",
            "Check In",
            "CheckIn",
        ]
        for k in cand_keys:
            v = (r.get(k) or "").strip()
            if v:
                d = _parse_date_to_ymd(v)
                if d:
                    return d
                v2 = v.replace(".", "-").replace("/", "-")[:10]
                if len(v2) == 10 and v2[4] == "-" and v2[7] == "-":
                    return v2

        # 2) 행 전체에서 첫 날짜 패턴 스캔
        joined = " ".join(str(x or "") for x in r.values())
        d = _parse_date_to_ymd(joined)
        if d:
            return d
        return ""

    bd = (fallback_business_date or "").strip()
    if not bd:
        for r in rows:
            dd = row_date(r)
            if dd:
                bd = dd
                break
    if not bd:
        raise HTTPException(422, "business_date required")

    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=_RS_CANON_FIELDS, lineterminator="\n")
    w.writeheader()

    n_rows = 0
    for r in rows:
        d = row_date(r) or bd
        w.writerow(
            {
                "business_date": d,
                "property_code": (r.get("property_code") or fallback_property_code or "MOP").strip().upper(),
                "room_no": (r.get("room_no") or r.get("객실번호") or r.get("객실") or "").strip(),
                "status_code": (r.get("status_code") or r.get("상태") or r.get("room_status") or r.get("예약상태") or "").strip(),
                "is_dirty": (r.get("is_dirty") or r.get("청소") or r.get("청소상태") or "").strip(),
                "hk_note": (r.get("hk_note") or r.get("비고") or r.get("note") or "").strip(),
            }
        )
        n_rows += 1

    if n_rows == 0:
        raise HTTPException(422, "no-rows")
    return out.getvalue(), bd


# ============================================================================
# Reservations
# ----------------------------------------------------------------------------
_RES_CANON_FIELDS = [
    "business_date",
    "property_code",
    "stay_type",
    "channel",
    "room_no",
    "room_type",
    "checkin",
    "checkout",
    "nights",
    "book_id",
    "ota_id",
    "guest_name",
    "phone",
    "amount",
    "balance",
    "memo",
    "booked_at",
]

def normalize_reservations_to_canon(
    raw_csv_text: str,
    fallback_business_date: Optional[str],
    fallback_property_code: str,
) -> Tuple[str, str]:
    sio = io.StringIO(raw_csv_text)
    dr = csv.DictReader(sio)
    if not dr.fieldnames:
        raise HTTPException(422, "invalid-csv")
    rows = list(dr)

    bd = (fallback_business_date or "").strip()
    if not bd:
        for r in rows:
            cand = (r.get("입실일시") or r.get("예약일시") or "")
            bd = _parse_date_to_ymd(cand)
            if bd:
                break
    if not bd:
        raise HTTPException(422, "business_date required")

    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=_RES_CANON_FIELDS, lineterminator="\n")
    w.writeheader()

    n_rows = 0
    for r in rows:
        chk_in = _parse_date_to_ymd(r.get("입실일시") or "")
        chk_out = _parse_date_to_ymd(r.get("퇴실일시") or "")
        row_bd = chk_in or _parse_date_to_ymd(r.get("예약일시") or "") or bd

        nights_m = re.search(r"\d+", str(r.get("투숙기간") or ""))
        nights = nights_m.group(0) if nights_m else ""

        w.writerow(
            {
                "business_date": row_bd,
                "property_code": (r.get("property_code") or fallback_property_code or "MOP").strip().upper(),
                "stay_type": (r.get("예약타입") or r.get("stay_type") or "").strip(),
                "channel": (r.get("예약처") or r.get("channel") or "").strip().upper(),
                "room_no": _clean_room_no(r.get("배정객실") or r.get("room_no") or ""),
                "room_type": (r.get("객실타입") or r.get("room_type") or "").strip(),
                "checkin": chk_in,
                "checkout": chk_out,
                "nights": nights,
                "book_id": (r.get("예약번호") or r.get("book_id") or "").strip(),
                "ota_id": (r.get("OTA예약번호") or r.get("ota_id") or "").strip(),
                "guest_name": (r.get("예약자명") or r.get("guest_name") or "").strip(),
                "phone": (r.get("연락처") or r.get("phone") or "").strip(),
                "amount": str(int(round(norm_amount(r.get("결제금액") or r.get("amount") or "0")))),
                "balance": str(int(round(norm_amount(r.get("미수금") or r.get("balance") or "0")))),
                "memo": (r.get("메모") or r.get("memo") or "").strip(),
                "booked_at": _parse_date_to_ymd(r.get("예약일시") or ""),
            }
        )
        n_rows += 1

    if n_rows == 0:
        raise HTTPException(422, "no-rows")
    return out.getvalue(), bd


# ============================================================================
# 선택 헬퍼
# ----------------------------------------------------------------------------
def get_normalizer(dataset: str):
    """
    데이터셋 문자열 → 정규화 함수(resolve)
    - 없는 데이터셋이면 422 반환
    """
    m = {
        "sales_front": normalize_sales_front_to_canon,
        "rooms_status": normalize_rooms_status_to_canon,
        "bank_ledger": normalize_bank_ledger_to_canon,
        # F&B 추후 필요 시 추가 연결
        # "fnb_sales_pay": ...,
        # "fnb_sales_items": ...,
        "reservations": normalize_reservations_to_canon,
    }
    fn = m.get(dataset)
    if not fn:
        raise HTTPException(422, f"unknown-dataset:{dataset}")
    return fn
