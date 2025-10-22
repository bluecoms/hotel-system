# app/core/snapshot.py
# -*- coding: utf-8 -*-
"""
일일 스냅샷 재생성(rebuild_daily_snapshot)
- PMS / Front / F&B / Expenses / Settlement / Bank 데이터 합산
- 키워드 엔진(app/core/keywords.py)으로 룸온리/패키지 분류
- daily_snapshot 테이블 upsert
"""

from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.keywords import apply_keywords_and_summarize


def rebuild_daily_snapshot(db: Session, date: str, property_code: str) -> None:
    """
    ETL / 업로드 이후 호출됨.
    일자별 매출 요약 스냅샷(daily_snapshot) 재생성.
    """
    result = apply_keywords_and_summarize(db=db, date=date, property_code=property_code)

    sql = text("""
        INSERT INTO daily_snapshot(
            property_code, business_date,
            room_only_amt, package_amt, other_amt,
            front_cash, front_card, front_gross,
            fb_gross
        ) VALUES (:prop, :dt, :ro, :pk, :ot, :fc, :fd, :fg, :fb)
        ON CONFLICT(property_code, business_date)
        DO UPDATE SET
            room_only_amt=:ro, package_amt=:pk, other_amt=:ot,
            front_cash=:fc, front_card=:fd, front_gross=:fg,
            fb_gross=:fb
    """)

    params = {
        "prop": property_code,
        "dt": date,
        "ro": result["rooms"]["room_only"],
        "pk": result["rooms"]["package"],
        "ot": result["rooms"]["other"],
        "fc": result["front"]["cash"],
        "fd": result["front"]["card"],
        "fg": result["front"]["gross"],
        "fb": result["fb"]["gross"],
    }

    db.execute(sql, params)
    db.commit()
