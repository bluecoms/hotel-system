"""unique sales_front(business_date, tag)

Revision ID: e4bd6009f95a
Revises: 36dc2deb9527
Create Date: 2025-10-02 08:44:17.351531+00:00
"""
from alembic import op
from sqlalchemy import text

# ---- Alembic identifiers (단일 선언) ----
revision = "e4bd6009f95a"
down_revision = "36dc2deb9527"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    dialect = conn.dialect.name.lower()

    # 0) NULL 정리: 유니크 인덱스 전 가능한 문제 레코드 제거
    conn.execute(text("""
        DELETE FROM sales_front
        WHERE business_date IS NULL OR tag IS NULL
    """))

    # 1) 중복 정리: (business_date, tag) 동일한 중복은 하나만 남김
    #    SQLite 환경 가정 — rowid 활용 (우리가 실제로 SQLite 쓰고 있음)
    if dialect == "sqlite":
        conn.execute(text("""
            DELETE FROM sales_front
            WHERE rowid NOT IN (
                SELECT MIN(rowid)
                FROM sales_front
                GROUP BY business_date, tag
            )
        """))
        # 2) 유니크 인덱스 생성 (SQLite는 UNIQUE CONSTRAINT 추가가 제한적 → 인덱스로 보장)
        conn.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS ux_sales_front_date_tag
            ON sales_front(business_date, tag)
        """))
    else:
        # 다른 DB인 경우에도 동일 이름의 유니크 인덱스로 처리
        op.create_index(
            "ux_sales_front_date_tag",
            "sales_front",
            ["business_date", "tag"],
            unique=True,
        )


def downgrade():
    conn = op.get_bind()
    dialect = conn.dialect.name.lower()

    if dialect == "sqlite":
        conn.execute(text("DROP INDEX IF EXISTS ux_sales_front_date_tag"))
    else:
        op.drop_index("ux_sales_front_date_tag", table_name="sales_front")
