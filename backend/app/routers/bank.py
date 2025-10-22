# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/routers/bank.py
# Version   : 2025.10-31 · v2.2 (3.8 Safe · Partition Options · SSOT Stable)
# Purpose   : Hotel Admin — Bank Upload & Summary Router (/api/*)
# ----------------------------------------------------------------------------
# 목적:
#   • 은행 입·출금 업로드(입금=pay_settlement / 출금=expenses) 처리
#   • 업로드 파일 정규화(normalize_bank_csv) → bank_txns 기록
#   • 업로드 이력(uploaded_files) 저장 및 세션/버전 관리
#   • 대시보드용 간단 합계/잔액 요약 제공 (/api/bank/summary)
#   • ✅ 프런트 파티션 칩용 계좌 옵션 API 추가 (/api/bank/accounts/options)
#   • ✅ UploadedFile.part_key = account_code (기존 'expense' 오타 제거)
# ----------------------------------------------------------------------------
# 변경 사항(v2.2)
#   ✅ Python 3.8 호환: list[str] → List[str]
#   ✅ 주석/정렬 SSOT 규격화
#   ✅ 기존 동작 및 파라미터 100 % 유지 (비파괴)
# ----------------------------------------------------------------------------
# 권한 정책:
#   • 모든 엔드포인트 require_token_local
#   • 업로드/요약은 ADMIN 또는 SUPERADMIN 권한 필요
# ----------------------------------------------------------------------------
# 연계 모듈:
#   • app/models/bank.py          → BankAccount, BankTxn, BankDailyBalance
#   • app/models/closing.py       → UploadSession, UploadedFile
#   • app/core/normalize_bank.py  → read_bank_upload_to_csv_text, normalize_bank_csv
#   • app/core/settings.py        → UPLOAD_ROOT
# ============================================================================

from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import logging
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app.core.auth import require_roles, require_token_local
from app.db.session import get_db
from app.models.closing import UploadSession, UploadedFile
from app.models.bank import BankAccount, BankTxn, BankDailyBalance
from app.core.normalize_bank import read_bank_upload_to_csv_text, normalize_bank_csv
from app.core.settings import settings

# ─────────────────────────────────────────────
# Router & Logger
# ─────────────────────────────────────────────
router = APIRouter(prefix="/api", tags=["bank"])
log = logging.getLogger(__name__)

DATA_ROOT = Path(settings.UPLOAD_ROOT)
DATA_ROOT.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────
# helpers (공통)
# ─────────────────────────────────────────────
def _filter_by_model_columns(model, data: Dict) -> Dict:
    cols: List[str] = list(model.__table__.columns.keys())
    return {k: v for k, v in data.items() if k in cols}

def _get_or_create_session(db: Session, dataset: str, business_date: str, property_code: str) -> UploadSession:
    sess = (
        db.query(UploadSession)
        .filter(UploadSession.dataset == dataset)
        .filter(UploadSession.property_code == property_code)
        .filter(UploadSession.business_date == business_date)
        .first()
    )
    if not sess:
        payload = _filter_by_model_columns(
            UploadSession,
            dict(dataset=dataset, business_date=business_date, property_code=property_code, status="STORED"),
        )
        sess = UploadSession(**payload)
        db.add(sess)
        db.flush()
    return sess

def _next_version(db: Session, session_id: int) -> int:
    v = db.query(func.max(UploadedFile.version_no)).filter(UploadedFile.session_id == session_id).scalar()
    return int(v or 0) + 1

def _store_file(bin_file: UploadFile, dest_dir: Path, dest_name: str) -> Dict:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / dest_name
    size = 0
    with dest.open("wb") as fw:
        for chunk in iter(lambda: bin_file.file.read(1024 * 1024), b""):
            fw.write(chunk)
            size += len(chunk)
    return {"path": str(dest), "size": size, "filename": bin_file.filename or dest_name}

def _head_rows(text_: str, n: int = 5) -> List[str]:
    """CSV 텍스트의 상위 n 행만 미리보기용으로 반환"""
    rows = text_.splitlines()
    return rows[: min(len(rows), n)]

def _ensure_account(
    db: Session,
    property_code: str,
    account_code: str,
    bank_name: str = "",
    account_name: str = "",
) -> BankAccount:
    """계좌 기준정보가 없으면 최소 정보로 생성."""
    acc = (
        db.query(BankAccount)
        .filter(BankAccount.property_code == property_code)
        .filter(BankAccount.account_code == account_code)
        .first()
    )
    if not acc:
        acc = BankAccount(
            property_code=property_code,
            account_code=account_code,
            bank_name=bank_name,
            account_name=account_name,
        )
        db.add(acc)
        db.flush()
    return acc

def _insert_txns(
    db: Session,
    canon_csv: str,
    *,
    property_code: str,
    account_code: str,
    business_date: str,
    dataset: str,
    session_id: int,
    version_no: int,
) -> int:
    """정규화된 CSV → bank_txns 적재."""
    import csv, io, datetime as dt
    rdr = csv.DictReader(io.StringIO(canon_csv))
    count = 0
    for r in rdr:
        ds = (r.get("date") or "").strip()
        try:
            txn_date = dt.datetime.strptime(ds, "%Y-%m-%d").date() if ds else None
        except Exception:
            txn_date = None
        if not txn_date:
            continue
        try:
            amt = int(r.get("amount") or "0")
        except Exception:
            amt = 0

        bt = BankTxn(
            property_code=property_code,
            account_code=account_code,
            business_date=business_date,
            txn_date=txn_date,
            txn_time=(r.get("time") or "")[:8],
            direction=(r.get("direction") or "IN")[:3],
            amount=amt,
            balance=int(r.get("balance") or "0"),
            desc=(r.get("desc") or "")[:255],
            counterparty=(r.get("counterparty") or "")[:255],
            memo=(r.get("memo") or "")[:255],
            raw_ref=(r.get("raw_ref") or "")[:255],
            dataset=dataset,
            session_id=session_id,
            version_no=version_no,
        )
        db.add(bt)
        count += 1
    return count

# ─────────────────────────────────────────────
# 업로드: 입금(수입) → dataset = pay_settlement
# ─────────────────────────────────────────────
@router.post(
    "/upload/pay_settlement",
    name="Upload Bank Income (Deposits)",
    dependencies=[Depends(require_token_local), Depends(require_roles(["ADMIN", "SUPERADMIN"]))],
)
async def upload_bank_income(
    business_date: str = Form(..., description="YYYY-MM-DD"),
    property_code: str = Form("MOP"),
    account_code: str = Form("", description="은행 계좌 코드 (파티션)"),
    bank_name: str = Form("", description="표시용 은행명 (선택)"),
    account_name: str = Form("", description="표시용 계좌명 (선택)"),
    dry_run: int = Form(1),
    file: UploadFile = File(..., description="은행 입금 내역 (XLS/XLSX/CSV)"),
    db: Session = Depends(get_db),
):
    """은행 입금(수입) 내역 업로드"""
    if not business_date or len(business_date) != 10:
        raise HTTPException(422, "business_date required (YYYY-MM-DD)")

    csv_text, _ = read_bank_upload_to_csv_text(file)
    canon_csv, preview, stats = normalize_bank_csv(csv_text, default_direction="IN")

    try:
        file.file.seek(0)
    except Exception:
        pass

    acct = (account_code or "DEFAULT").strip()
    base = {
        "business_date": business_date,
        "property_code": property_code,
        "account_code": acct,
        "dataset": "pay_settlement",
        "counts": stats,
        "preview_head": ["date,time,direction,amount,balance,desc,counterparty,memo,raw_ref"] + preview,
    }

    if int(dry_run or 0) == 1:
        return {"ok": True, "dry_run": True, **base}

    dataset = "pay_settlement"
    sess = _get_or_create_session(db, dataset, business_date, property_code)
    version_no = _next_version(db, sess.id)
    dest_dir = DATA_ROOT / dataset / property_code / business_date / f"v{version_no}"
    meta = _store_file(file, dest_dir, file.filename or "income.xls")

    _ensure_account(db, property_code, acct, bank_name, account_name)

    rec = UploadedFile(
        **_filter_by_model_columns(
            UploadedFile,
            dict(
                session_id=sess.id,
                version_no=version_no,
                part_key=acct,
                filename=meta["filename"],
                stored_path=meta["path"],
                size=meta["size"],
                created_at=datetime.utcnow(),
            ),
        )
    )
    db.add(rec)

    inserted = _insert_txns(
        db,
        canon_csv,
        property_code=property_code,
        account_code=acct,
        business_date=business_date,
        dataset=dataset,
        session_id=sess.id,
        version_no=version_no,
    )
    db.commit()

    return {
        "ok": True,
        "dry_run": False,
        **base,
        "inserted": inserted,
        "session_id": sess.id,
        "version_no": version_no,
        "file": meta,
    }

# ─────────────────────────────────────────────
# 업로드: 출금(지출) → dataset = expenses
# ─────────────────────────────────────────────
@router.post(
    "/upload/expenses",
    name="Upload Bank Expense (Withdrawals)",
    dependencies=[Depends(require_token_local), Depends(require_roles(["ADMIN", "SUPERADMIN"]))],
)
async def upload_bank_expense(
    business_date: str = Form(..., description="YYYY-MM-DD"),
    property_code: str = Form("MOP"),
    account_code: str = Form("", description="은행 계좌 코드 (파티션)"),
    bank_name: str = Form("", description="표시용 은행명 (선택)"),
    account_name: str = Form("", description="표시용 계좌명 (선택)"),
    dry_run: int = Form(1),
    file: UploadFile = File(..., description="은행 출금 내역 (XLS/XLSX/CSV)"),
    db: Session = Depends(get_db),
):
    """은행 출금(지출) 내역 업로드"""
    if not business_date or len(business_date) != 10:
        raise HTTPException(422, "business_date required (YYYY-MM-DD)")

    csv_text, _ = read_bank_upload_to_csv_text(file)
    canon_csv, preview, stats = normalize_bank_csv(csv_text, default_direction="OUT")

    try:
        file.file.seek(0)
    except Exception:
        pass

    acct = (account_code or "DEFAULT").strip()
    base = {
        "business_date": business_date,
        "property_code": property_code,
        "account_code": acct,
        "dataset": "expenses",
        "counts": stats,
        "preview_head": ["date,time,direction,amount,balance,desc,counterparty,memo,raw_ref"] + preview,
    }

    if int(dry_run or 0) == 1:
        return {"ok": True, "dry_run": True, **base}

    dataset = "expenses"
    sess = _get_or_create_session(db, dataset, business_date, property_code)
    version_no = _next_version(db, sess.id)
    dest_dir = DATA_ROOT / dataset / property_code / business_date / f"v{version_no}"
    meta = _store_file(file, dest_dir, file.filename or "expense.xls")

    _ensure_account(db, property_code, acct, bank_name, account_name)

    rec = UploadedFile(
        **_filter_by_model_columns(
            UploadedFile,
            dict(
                session_id=sess.id,
                version_no=version_no,
                part_key=acct,
                filename=meta["filename"],
                stored_path=meta["path"],
                size=meta["size"],
                created_at=datetime.utcnow(),
            ),
        )
    )
    db.add(rec)

    inserted = _insert_txns(
        db,
        canon_csv,
        property_code=property_code,
        account_code=acct,
        business_date=business_date,
        dataset=dataset,
        session_id=sess.id,
        version_no=version_no,
    )
    db.commit()

    return {
        "ok": True,
        "dry_run": False,
        **base,
        "inserted": inserted,
        "session_id": sess.id,
        "version_no": version_no,
        "file": meta,
    }

# ─────────────────────────────────────────────
# 조회: 잔액/요약 (대시보드용 간단 합계)
# ─────────────────────────────────────────────
@router.get(
    "/bank/summary",
    dependencies=[Depends(require_token_local), Depends(require_roles(["ADMIN", "SUPERADMIN"]))],
)
def bank_summary(
    property_code: str = Query("MOP"),
    date: Optional[str] = Query(None, description="YYYY-MM-DD (없으면 전체)"),
    db: Session = Depends(get_db),
):
    """계좌별 입·출 합계 및 최대 잔액 요약"""
    params: Dict[str, any] = {"pc": property_code}
    where = "property_code = :pc"
    if date:
        where += " AND business_date = :bd"
        params["bd"] = date

    sql = f"""
      SELECT account_code,
             SUM(CASE WHEN direction='IN'  THEN amount ELSE 0 END) as sum_in,
             SUM(CASE WHEN direction='OUT' THEN amount ELSE 0 END) as sum_out,
             MAX(balance) as max_balance
        FROM bank_txns
       WHERE {where}
       GROUP BY account_code
       ORDER BY account_code
    """
    rows = db.execute(text(sql), params).fetchall()
    items = []
    total_in = total_out = 0
    for account_code, s_in, s_out, max_bal in rows:
        s_in = int(s_in or 0)
        s_out = int(s_out or 0)
        total_in += s_in
        total_out += s_out
        items.append({
            "account_code": account_code,
            "sum_in": s_in,
            "sum_out": s_out,
            "est_balance": int(max_bal or 0),
        })

    return {
        "property_code": property_code,
        "date": date,
        "items": items,
        "total_in": total_in,
        "total_out": total_out,
        "net": total_in - total_out,
    }

# ─────────────────────────────────────────────
# 조회: 파티션 칩 옵션 (프런트 DatasetCard 용)
# ─────────────────────────────────────────────
@router.get(
    "/bank/accounts/options",
    dependencies=[Depends(require_token_local), Depends(require_roles(["ADMIN", "SUPERADMIN"]))],
    summary="계좌 파티션 칩 옵션 (활성 계좌)",
)
def bank_account_options(
    property_code: str = Query("MOP"),
    only_active: int = Query(1, description="1=활성만, 0=전체"),
    db: Session = Depends(get_db),
):
    """프런트 탭 파티션 칩용 계좌 옵션 목록 (value=account_code)"""
    q = db.query(BankAccount).filter(BankAccount.property_code == property_code)
    if int(only_active or 0) == 1:
        q = q.filter(BankAccount.is_active.is_(True))
    rows = q.order_by(BankAccount.account_code.asc()).all()
    return {
        "ok": True,
        "items": [
            {
                "title": f"{r.account_code} · {r.bank_name or ''}".strip(),
                "value": r.account_code,
            }
            for r in rows
        ],
    }
