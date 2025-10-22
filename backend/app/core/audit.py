# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/core/audit.py
# Version   : 2025-10-31 · v3.6 (SSOT Stable)
# Purpose   : 감사 로그 기록 유틸리티
# ----------------------------------------------------------------------------
# 목적:
#   • 시스템 내 모든 주요 동작(생성·수정·삭제 등)을 audit_logs 테이블에 기록
#   • SSOT 정책(append-only, immutable) 기반 감사 이력 관리
# ----------------------------------------------------------------------------
# 특징:
#   ✅ DB 타입 자동 감지 (SQLite ↔ PostgreSQL)
#   ✅ 실패 시 서비스 흐름 방해 없이 경고 로그만 출력
#   ✅ JSON 직렬화 시 ensure_ascii=False → 한글 깨짐 방지
# ----------------------------------------------------------------------------
# 사용 예:
#   from app.core.audit import write_audit
#   write_audit(db, actor="admin", action="user.create", target="user=5")
# ============================================================================

import json
import logging
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db.session import is_sqlite

log = logging.getLogger(__name__)


def write_audit(
    db: Session,
    actor: str,
    action: str,
    target: str,
    meta: dict | None = None,
) -> None:
    """
    감사 로그 기록 함수.
    - actor : 실행 주체 (예: admin, system, token 등)
    - action: 수행한 액션 코드 (예: user.create)
    - target: 대상 식별자 (예: user_id=5)
    - meta  : 부가정보 dict → JSON 직렬화
    """
    try:
        ts_expr = "datetime('now')" if is_sqlite() else "NOW()"

        db.execute(
            text(f"""
                INSERT INTO audit_logs(ts, actor, action, target, meta_json)
                VALUES({ts_expr}, :actor, :action, :target, :meta)
            """),
            {
                "actor": actor or "system",
                "action": action,
                "target": target or "",
                "meta": json.dumps(meta or {}, ensure_ascii=False),
            },
        )
        db.flush()  # 세션 즉시 반영 (commit 전 안전)
    except Exception as e:
        log.warning(f"[AUDIT] write_audit failed: {e}")
