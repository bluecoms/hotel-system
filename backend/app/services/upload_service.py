# -*- coding: utf-8 -*-
# app/services/upload_service.py
from __future__ import annotations
import io, csv
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from fastapi import UploadFile, HTTPException
from app.models.closing import UploadSession, UploadedFile
from app.core.normalize import bytes_to_text_guess

DATA_ROOT = Path("/volume1/web/hotel-system/backend/_uploads")
DATA_ROOT.mkdir(parents=True, exist_ok=True)

# ────────────── 기본 Helper ──────────────
def filter_by_model_columns(model, data: Dict) -> Dict:
    cols = list(model.__table__.columns.keys())
    return {k: v for k, v in data.items() if k in cols}

def get_or_create_session(db: Session, dataset: str, business_date: str, property_code: str) -> UploadSession:
    sess = (
        db.query(UploadSession)
        .filter_by(dataset=dataset, property_code=property_code, business_date=business_date)
        .first()
    )
    if not sess:
        payload = filter_by_model_columns(
            UploadSession,
            dict(dataset=dataset, business_date=business_date, property_code=property_code, status="STORED"),
        )
        sess = UploadSession(**payload)
        db.add(sess); db.flush()
    return sess

def next_version(db: Session, session_id: int) -> int:
    v = db.query(func.max(UploadedFile.version_no)).filter(UploadedFile.session_id == session_id).scalar()
    return int(v or 0) + 1

def store_file(src: UploadFile, dest_dir: Path, dest_name: str) -> Dict:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / dest_name
    size = 0
    with dest.open("wb") as fw:
        for chunk in iter(lambda: src.file.read(1024 * 1024), b""):
            fw.write(chunk); size += len(chunk)
    return {"path": str(dest), "size": size, "filename": src.filename or dest_name}

def store_text_file(dest_dir: Path, dest_name: str, text: str) -> Dict:
    dest_dir.mkdir(parents=True, exist_ok=True)
    data = text.encode("utf-8")
    dest = dest_dir / dest_name
    dest.write_bytes(data)
    return {"path": str(dest), "size": len(data), "filename": dest_name}

def load_raw(db: Session, dataset: str, business_date: str, property_code: str, version_no: Optional[int] = None, part: Optional[str] = None):
    q = (
        db.query(UploadedFile)
        .join(UploadSession, UploadSession.id == UploadedFile.session_id)
        .filter(UploadSession.dataset == dataset, UploadSession.business_date == business_date, UploadSession.property_code == property_code)
    )
    if part: q = q.filter(UploadedFile.part_key == part)
    if version_no: q = q.filter(UploadedFile.version_no == version_no)
    rec = q.order_by(UploadedFile.version_no.desc(), UploadedFile.id.desc()).first()
    if not rec: raise HTTPException(404, "not-found")
    p = Path(rec.stored_path)
    if not p.exists(): raise HTTPException(404, "file-missing")
    data = p.read_bytes()
    try: txt = bytes_to_text_guess(data)
    except Exception: txt = data.decode("utf-8", errors="ignore")
    return txt, rec
