# app/core/keywords.py
# -*- coding: utf-8 -*-
"""
키워드 매칭 / 매출 정규화 / 스냅샷 요약 로직
(services/etl 대체용 — 신규 파일)
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text


def normalize_records(records: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    간단 키워드 분류: '패키지', '룸온리' 등의 문자열 포함 시 구분
    """
    agg = {"room_only": 0, "package": 0, "other": 0}
    for r in records:
        name = (r.get("name") or "").lower()
        amt = int(r.get("amount") or 0)
        if "package" in name or "패키" in name:
            agg["package"] += amt
        elif "room" in name or "룸" in name or "숙박" in name:
            agg["room_only"] += amt
        else:
            agg["other"] += amt
    return agg


def apply_keywords_and_summarize(db: Session, date: str, property_code: str) -> Dict[str, Any]:
    """
    일자별 원천 데이터 정규화 후 합산 (daily_snapshot upsert 용)
    property_code 필터를 반드시 포함한다.
    """
    # --- 1) 원천 데이터 로드 (property_code 포함) ---
    front_rows = db.execute(text("""
        SELECT tag, SUM(amount) AS amt
        FROM sales_front
        WHERE business_date = :dt
          AND property_code  = :pc
        GROUP BY tag
    """), {"dt": date, "pc": property_code}).mappings().all()

    # --- 2) 키워드 매칭 후 카테고리별 합산 ---
    rooms = {"room_only": 0, "package": 0, "other": 0}
    for r in front_rows or []:
        tag = (r["tag"] or "").lower()
        amt = int(r["amt"] or 0)
        if "package" in tag or "패키" in tag:
            rooms["package"] += amt
        elif "room" in tag or "룸" in tag or "숙박" in tag:
            rooms["room_only"] += amt
        else:
            rooms["other"] += amt

    # --- 3) 예시 요약(프론트/FB 더미 유지) ---
    result = {
        "rooms": rooms,
        "front": {"cash": rooms["room_only"], "card": rooms["package"], "gross": sum(rooms.values())},
        "fb": {"gross": 0},
    }
    return result
