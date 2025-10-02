# app/core/audit.py
from sqlalchemy import text
import json

def write_audit(db, actor: str, action: str, target: str, meta: dict = None):
    """
    감사 로그 기록 유틸.
    - actor: 실행 주체 (토큰, 시스템명 등)
    - action: 수행한 액션 코드
    - target: 대상 식별자 (예: "commission_id=5")
    - meta: 부가 정보(JSON 직렬화)
    """
    db.execute(
        text("""
            INSERT INTO audit_logs(ts, actor, action, target, meta_json)
            VALUES(datetime('now'), :actor, :action, :target, :meta)
        """),
        {
            "actor": actor or "system",
            "action": action,
            "target": target,
            "meta": json.dumps(meta or {}, ensure_ascii=False),
        },
    )
