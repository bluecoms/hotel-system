# app/routers/upload.py
from typing import List, Tuple, Optional
from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException, status, Header, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
import csv, io, json

from app.core.auth import require_roles
from app.db.session import get_db
from app.core.locale import set_lang
from app.core.i18n import t as _t  # i18n helper
from app.core.audit import write_audit

router = APIRouter(
    prefix="/api/upload",
    tags=["upload"],
    # 언어 세팅 + 권한 체크 (router 레벨 공통 의존성)
    dependencies=[Depends(set_lang), Depends(require_roles(["ADMIN"]))],
)

@router.post("/sales_front")
def upload_sales_front(
    request: Request,
    file: UploadFile = File(...),
    dry_run: bool = Form(False),
    db=Depends(get_db),
    x_internal_token: Optional[str] = Header(None, alias="X-Internal-Token"),
):
    lang = getattr(request.state, "lang", "en")

    # 1) CSV 확장자 검증 → 400
    fn = (file.filename or "").lower()
    if not fn.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_t("error.csv_required", lang),
        )

    # 2) 파일 로드/인코딩 (국내 인코딩 폴백 포함)
    raw = file.file.read()
    content = None
    for enc in ("utf-8-sig", "cp949", "euc-kr"):
        try:
            content = raw.decode(enc)
            break
        except Exception:
            pass
    if content is None:
        try:
            content = raw.decode("utf-8", errors="ignore")
        except Exception:
            raise HTTPException(status_code=400, detail=_t("error.validation", lang))

    # 3) CSV 헤더 검증 → 400
    reader = csv.DictReader(io.StringIO(content))
    required = {"business_date", "tag", "amount"}
    if not required.issubset(set(reader.fieldnames or [])):
        raise HTTPException(status_code=400, detail=_t("error.csv_headers", lang))

    # 4) 레코드 파싱
    received, inserted = 0, 0
    errors: List[dict] = []
    rows: List[Tuple[str, str, int]] = []

    # 헤더가 1행 → 데이터는 2행부터 시작
    for i, row in enumerate(reader, start=2):
        received += 1
        try:
            d = (row.get("business_date") or "").strip()
            tag_ = (row.get("tag") or "").strip()   # 변수명 충돌 방지
            a_raw = (row.get("amount") or "").strip()
            a = int(a_raw.replace(",", "")) if a_raw else 0

            if not d or not tag_:
                raise ValueError("business_date/tag required")
            if a < 0:
                raise ValueError("amount<0")

            # (선택) 날짜 포맷 엄격 체크가 필요하면 아래 주석 해제
            # import re
            # if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
            #     raise ValueError("invalid business_date (YYYY-MM-DD)")

            rows.append((d, tag_, a))
        except Exception as e:
            errors.append({"row": i, "message": str(e)})

    # 5) DB 적용 (dry_run이 아니고, 오류가 없을 때만)
    if not dry_run and not errors and rows:
        try:
            # 본문 insert (배치 파라미터)
            db.execute(
                text("INSERT INTO sales_front(business_date,tag,amount) VALUES (:d,:t,:a)"),
                [{"d": d, "t": t, "a": a} for (d, t, a) in rows],
            )

            write_audit(
                db,
                x_internal_token or "system/upload",
                "SALES_FRONT_UPLOAD",
                f"rows={len(rows)}",
                {"lang": lang, "dry_run": False},
            )

            db.commit()
            inserted = len(rows)

        except IntegrityError:
            db.rollback()
            # UNIQUE 충돌 → 409
            raise HTTPException(status_code=409, detail=_t("error.duplicate", lang))
        except Exception as e:
            db.rollback()
            # 기타 예외는 400으로 회수
            raise HTTPException(status_code=400, detail=str(e))

    # 6) 응답 포맷 (권장)
    return {
        "dry_run": dry_run,
        "received": received,
        "inserted": (inserted if not dry_run else 0),
        "errors": errors,
    }
