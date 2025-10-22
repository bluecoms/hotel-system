"""sync employees model v3 (SQLite-safe)

Revision ID: 2ebccedd1011
Revises: 71b209ce71aa
Create Date: 2025-10-18 14:17:44.789248+00:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = "2ebccedd1011"
down_revision: Union[str, None] = "71b209ce71aa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add new fields to employees table (SQLite-safe version)."""
    conn = op.get_bind()

    # ─────────────────────────────────────────────
    # 1️⃣ 컬럼 추가 (단일 ALTER TABLE)
    # ─────────────────────────────────────────────
    op.execute("ALTER TABLE employees ADD COLUMN birth_date DATE NULL;")
    op.execute("ALTER TABLE employees ADD COLUMN bank_name VARCHAR(60) DEFAULT '' NOT NULL;")
    op.execute("ALTER TABLE employees ADD COLUMN account_mask VARCHAR(60) DEFAULT '' NOT NULL;")
    op.execute("ALTER TABLE employees ADD COLUMN account_last4 VARCHAR(8) DEFAULT '' NOT NULL;")

    # ─────────────────────────────────────────────
    # 2️⃣ NULL → DEFAULT 보정
    # ─────────────────────────────────────────────
    conn.execute(sa.text("""
        UPDATE employees
        SET bank_name = COALESCE(bank_name, ''),
            account_mask = COALESCE(account_mask, ''),
            account_last4 = COALESCE(account_last4, '')
    """))


def downgrade() -> None:
    """SQLite does not support DROP COLUMN; manual revert required."""
    # SQLite에서는 DROP COLUMN을 지원하지 않으므로 경고만 표시
    print("[WARN] SQLite에서는 DROP COLUMN을 지원하지 않습니다. 수동 복원 필요.")
