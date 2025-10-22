# ============================================================================
# File      : app/routers/reports_bank.py
# Version   : 2025.10-20 (Final Stable)
# Purpose   : Bank Ledger Reports API — Dashboard 연동용
# ----------------------------------------------------------------------------
# 주요 변경사항 (v2025.10-20)
#   ✅ 프런트 요청 파라미터명 `business_date` 지원 (기존 alias="date" 제거)
#   ✅ 하위호환 유지: `date` 파라미터도 허용하며, 둘 다 없으면 422 반환
#   ✅ 내부 변수명 `biz_date`로 통일 (FastAPI 검증 충돌 방지)
#   ✅ 주석 및 코드 정리, 명시적 타입/패턴 지정
# ----------------------------------------------------------------------------
# 요청 예시:
#   GET /api/reports/bank_ledger?property_code=MOP&business_date=2025-10-19&account_code=NH-301-xxxx
# 응답 예시:
#   { ok: true, business_date: "2025-10-19", property_code: "MOP", ... }
# ============================================================================

from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

import csv, io
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.auth import require_roles, require_token_local
from app.db.session import get_db
from app.models.closing import UploadSession, UploadedFile
from app.core.normalize import normalize_bank_ledger_to_canon

# ─────────────────────────────────────────────────────────────
# Router 설정
# ─────────────────────────────────────────────────────────────
router = APIRouter(
    prefix="/api",
    tags=["reports"],
)

# ─────────────────────────────────────────────────────────────
# 내부 유틸
# ─────────────────────────────────────────────────────────────
def _latest_file(
    db: Session,
    property_code: str,
    business_date: str,
    dataset: str = "bank_ledger",
    account_code: Optional[str] = None,
) -> Optional[UploadedFile]:
    """지정된 일자/자산코드의 최신 업로드 파일 조회"""
    sess = (
        db.query(UploadSession)
        .filter(
            UploadSession.dataset == dataset,
            UploadSession.property_code == property_code,
            UploadSession.business_date == business_date,
        )
        .first()
    )
    if not sess:
        return None

    v = db.query(func.max(UploadedFile.version_no)).filter(
        UploadedFile.session_id == sess.id
    ).scalar()
    if not v:
        return None

    q = db.query(UploadedFile).filter(
        UploadedFile.session_id == sess.id,
        UploadedFile.version_no == int(v),
    )
    if account_code:
        q = q.filter(UploadedFile.part_key == account_code)

    return q.order_by(UploadedFile.id.desc()).first()


def _canon_rows(text: str, bd: str, pc: str, account_code: str) -> List[Dict[str, Any]]:
    """CSV 텍스트 → Canon 포맷 Dict 리스트"""
    canon_csv, _ = normalize_bank_ledger_to_canon(
        text,
        fallback_business_date=bd,
        fallback_property_code=pc,
        account_code=account_code,
    )
    rdr = csv.DictReader(io.StringIO(canon_csv))
    return [dict(r) for r in rdr]


# ─────────────────────────────────────────────────────────────
#  /api/reports/bank_ledger — Dashboard Summary API
# ─────────────────────────────────────────────────────────────
@router.get(
    "/reports/bank_ledger",
    dependencies=[Depends(require_token_local), Depends(require_roles(["ADMIN", "SUPERADMIN"]))],
)
def report_bank_ledger(
    business_date: Optional[str] = Query(
        None,
        description="사업일자 (YYYY-MM-DD)",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    ),
    date: Optional[str] = Query(
        None,
        description="호환용 date 파라미터 (YYYY-MM-DD)",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    ),
    property_code: str = Query("MOP", description="자산 코드"),
    account_code: Optional[str] = Query(None, description="계좌 코드"),
    db: Session = Depends(get_db),
):
    """
    은행입출금 리포트 (Dashboard Bank Summary)
    - business_date가 우선, 없을 경우 date 파라미터 사용
    - 업로드된 최신 bank_ledger CSV를 Canon으로 변환하여 합계 반환
    """
    biz_date = business_date or date
    if not biz_date:
        raise HTTPException(422, "business_date required (YYYY-MM-DD)")

    # 최신 업로드 파일 조회
    rec = _latest_file(db, property_code, biz_date, account_code=account_code)
    if not rec:
        return {
            "ok": True,
            "business_date": biz_date,
            "property_code": property_code,
            "account_code": account_code or "",
            "rows": [],
            "totals": {"in": 0, "out": 0, "net": 0},
            "balance_after": None,
        }

    p = Path(rec.stored_path)
    if not p.exists():
        raise HTTPException(404, f"stored file not found: {p}")

    raw = p.read_text(encoding="utf-8", errors="ignore")
    rows = _canon_rows(raw, biz_date, property_code, account_code or (rec.part_key or "NH-UNKNOWN"))

    tot_in = tot_out = 0
    last_bal = None
    for r in rows:
        amt = int(float(r.get("amount") or 0))
        if (r.get("direction") or "").upper() == "IN":
            tot_in += amt
        else:
            tot_out += amt
        bal = (r.get("balance_after") or "").strip()
        if bal:
            try:
                last_bal = int(float(bal))
            except Exception:
                pass

    return {
        "ok": True,
        "business_date": biz_date,
        "property_code": property_code,
        "account_code": account_code or (rec.part_key or ""),
        "version_no": rec.version_no,
        "file": {"filename": rec.filename, "path": rec.stored_path, "size": rec.size},
        "rows": rows,
        "totals": {"in": tot_in, "out": tot_out, "net": (tot_in - tot_out)},
        "balance_after": last_bal,
    }


# ─────────────────────────────────────────────────────────────
#  /api/bank_ledger — Preview (하위호환)
# ─────────────────────────────────────────────────────────────
DATA_ROOT = Path("/volume1/web/hotel-system/uploads")


def _latest_version(
    db: Session,
    dataset: str,
    business_date: str,
    property_code: str,
    part: Optional[str] = None,
) -> Tuple[int, UploadedFile]:
    sess = (
        db.query(UploadSession)
        .filter(
            UploadSession.dataset == dataset,
            UploadSession.property_code == property_code,
            UploadSession.business_date == business_date,
        )
        .first()
    )
    if not sess:
        raise HTTPException(404, "no-session")

    q = db.query(UploadedFile).filter(UploadedFile.session_id == sess.id)
    if part:
        q = q.filter(UploadedFile.part_key == part)
    rec = q.order_by(UploadedFile.version_no.desc()).first()
    if not rec:
        raise HTTPException(404, "no-file")
    return rec.version_no, rec


@router.get("/bank_ledger")
async def report_bank_ledger_preview(
    business_date: Optional[str] = Query(
        None,
        description="사업일자 (YYYY-MM-DD)",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    ),
    date: Optional[str] = Query(
        None,
        description="호환용 date 파라미터 (YYYY-MM-DD)",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    ),
    property_code: str = Query("MOP"),
    account_code: str = Query(...),
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """은행입출금 미리보기 (기존 경로 하위호환용)"""
    biz_date = business_date or date
    if not biz_date:
        raise HTTPException(422, "business_date required (YYYY-MM-DD)")

    try:
        ver, rec = _latest_version(db, "bank_ledger", biz_date, property_code, part=account_code)
    except HTTPException:
        ver, rec = _latest_version(db, "bank_ledger", biz_date, property_code, part=None)

    p = Path(rec.stored_path)
    if not p.exists():
        raise HTTPException(404, "file-missing")

    raw = p.read_bytes()
    text = raw.decode("utf-8", errors="ignore")

    canon_csv, _ = normalize_bank_ledger_to_canon(
        text,
        fallback_business_date=biz_date,
        fallback_property_code=property_code,
        account_code=account_code,
    )

    rdr = csv.DictReader(io.StringIO(canon_csv))
    rows = []
    in_amt = out_amt = 0.0
    last_balance = None

    for r in rdr:
        direction = (r.get("direction") or "").upper()
        amt = float(r.get("amount") or 0)
        bal = r.get("balance_after")
        if bal not in (None, "", "0"):
            try:
                last_balance = float(bal)
            except Exception:
                pass

        if direction == "IN":
            in_amt += amt
        elif direction == "OUT":
            out_amt += amt

        rows.append(
            {
                "direction": direction,
                "amount": int(amt),
                "note": r.get("note") or "",
                "branch": r.get("branch") or "",
                "txn_time": r.get("txn_time") or "",
            }
        )

    rows_preview = rows[: max(0, int(limit or 0))] if limit else rows

    return {
        "ok": True,
        "property_code": property_code,
        "business_date": biz_date,
        "account_code": account_code,
        "version_no": ver,
        "in_amount": int(in_amt),
        "out_amount": int(out_amt),
        "net_amount": int(in_amt - out_amt),
        "last_balance": int(last_balance or 0),
        "items": rows_preview,
    }
