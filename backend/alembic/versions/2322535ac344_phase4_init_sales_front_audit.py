"""phase4_init_sales_front_audit

Revision ID: 2322535ac344
Revises: 20251001_add_commission_period_rate
Create Date: 2025-10-02 04:49:15.108851+00:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2322535ac344'
down_revision = 'e86edf299644'
branch_labels = None
depends_on = None


def upgrade():
    # A) sales_front (없으면 생성)
    op.execute("""
    CREATE TABLE IF NOT EXISTS sales_front (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      business_date TEXT NOT NULL,
      tag TEXT NOT NULL,
      amount INTEGER NOT NULL
    )
    """)

    op.execute("CREATE INDEX IF NOT EXISTS idx_sales_front_date ON sales_front(business_date)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_sales_front_tag_date ON sales_front(tag, business_date)")

    # B) 감사로그 (존재 확인 후 생성)
    op.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      ts DATETIME NOT NULL,
      actor TEXT NOT NULL,
      action TEXT NOT NULL,
      target TEXT NOT NULL,
      meta_json TEXT
    )
    """)


def downgrade():
    # 롤백 시엔 안전하게 IF EXISTS 로 제거
    op.execute("DROP INDEX IF EXISTS idx_sales_front_tag_date")
    op.execute("DROP INDEX IF EXISTS idx_sales_front_date")
    op.execute("DROP TABLE IF EXISTS sales_front")
    op.execute("DROP TABLE IF EXISTS audit_logs")
