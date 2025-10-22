"""add sales_front table_v4

Revision ID: 522efcdb9e1a
Revises: 2ebccedd1011
Create Date: 2025-10-19 04:42:55.197077+00:00

"""
# ============================================================================
# File      : alembic/versions/v4_add_sales_front_table.py
# Version   : 2025.10-20
# Purpose   : sales_front 테이블 신규 생성 (Dashboard / Reports용)
# ----------------------------------------------------------------------------
# 변경사항
#   ✅ 신규 테이블 sales_front 생성
#   ✅ 컬럼: id, property_code, business_date, tag, amount
#   ✅ Alembic head 기준 (down_revision='2ebccedd1011')
# ----------------------------------------------------------------------------
# 실행 명령:
#   alembic upgrade head
# ============================================================================
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_sales_front_table_v4'
down_revision = '2ebccedd1011'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'sales_front',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('property_code', sa.String(50), nullable=False),
        sa.Column('business_date', sa.String(10), nullable=False),
        sa.Column('tag', sa.String(100)),
        sa.Column('amount', sa.Integer, nullable=False, server_default='0'),
    )


def downgrade():
    op.drop_table('sales_front')
