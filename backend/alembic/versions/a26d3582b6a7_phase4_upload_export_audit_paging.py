"""phase4_upload_export_audit_paging

Revision ID: a26d3582b6a7
Revises: e4bd6009f95a
Create Date: 2025-10-02 14:33:14.005014+00:00

"""
# alembic/versions/<REV>_phase4_upload_export_audit_paging.py
from alembic import op

# revision identifiers, used by Alembic.
revision = "a26d3582b6a7"
down_revision = "e4bd6009f95a"  # alembic current 출력 확인 후 설정
branch_labels = None
depends_on = None

def upgrade():
    # sales_front
    op.execute("""
    CREATE TABLE IF NOT EXISTS sales_front(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      business_date TEXT NOT NULL,
      tag TEXT NOT NULL,
      amount INTEGER NOT NULL
    )
    """)
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_sales_front_date_tag ON sales_front(business_date, tag)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_sales_front_date ON sales_front(business_date)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_sales_front_tag_date ON sales_front(tag, business_date)")

    # audit_logs
    op.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      ts DATETIME NOT NULL,
      actor TEXT NOT NULL,
      action TEXT NOT NULL,
      target TEXT NOT NULL,
      meta_json TEXT
    )
    """)

def downgrade():
    # 운영 데이터 보호: 드롭하지 않음
    pass
