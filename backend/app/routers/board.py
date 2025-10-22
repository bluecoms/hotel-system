# app/routers/board.py
# -*- coding: utf-8 -*-
from __future__ import annotations
import logging
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.auth import require_roles, require_token_local
from app.db.session import get_db
from app.models.closing import UploadSession, UploadedFile

router = APIRouter(prefix="/api", tags=["board"])
log = logging.getLogger(__name__)

def _get_session(db: Session, dataset: str, business_date: str, property_code: str):
    return (
        db.query(UploadSession)
        .filter(
            UploadSession.dataset == dataset,
            UploadSession.business_date == business_date,
            UploadSession.property_code == property_code,
        ).first()
    )

def _get_latest_file_record(db: Session, session_id: int, version_no: Optional[int], part: Optional[str]):
    q = db.query(UploadedFile).filter(UploadedFile.session_id == session_id)
    if part not in (None, ""):
        q = q.filter(UploadedFile.part_key == part)
    if version_no is not None:
        q = q.filter(UploadedFile.version_no == int(version_no))
    return q.order_by(UploadedFile.version_no.desc(), UploadedFile.id.desc()).first()

@router.get("/download/versions",
    dependencies=[Depends(require_token_local), Depends(require_roles(["ADMIN","SUPERADMIN"]))])
def list_upload_versions(
    dataset: str = Query(...),
    business_date: str = Query(...),
    property_code: str = Query("MOP"),
    db: Session = Depends(get_db),
):
    sess = _get_session(db, dataset, business_date, property_code)
    if not sess:
        return {"dataset": dataset, "business_date": business_date, "property_code": property_code, "items": []}
    rows = (
        db.query(UploadedFile)
        .filter(UploadedFile.session_id == sess.id)
        .order_by(UploadedFile.version_no.desc(), UploadedFile.id.desc())
        .all()
    )
    items = [{
        "version_no": int(r.version_no or 0),
        "part_key": r.part_key or "",
        "filename": r.filename or "",
        "size": int(getattr(r, "size", 0) or 0),
        "uploaded_at": getattr(r, "created_at", None),
    } for r in rows]
    return {"dataset": dataset, "business_date": business_date, "property_code": property_code, "items": items}

@router.get("/download/file",
    dependencies=[Depends(require_token_local), Depends(require_roles(["ADMIN","SUPERADMIN"]))])
def download_file(
    dataset: str = Query(...),
    business_date: str = Query(...),
    property_code: str = Query("MOP"),
    version_no: Optional[int] = Query(None),
    part: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    sess = _get_session(db, dataset, business_date, property_code)
    if not sess:
        raise HTTPException(status_code=404, detail="not-found")
    rec = _get_latest_file_record(db, session_id=sess.id, version_no=version_no, part=part)
    if not rec:
        raise HTTPException(status_code=404, detail="not-found")
    p = Path(rec.stored_path or "")
    if (not p.exists()) or (not p.is_file()):
        log.warning("download_file: file missing on disk: %s", p)
        raise HTTPException(status_code=404, detail="file-missing")
    return FileResponse(path=str(p), media_type="text/csv; charset=utf-8", filename=rec.filename or f"{dataset}.csv")
