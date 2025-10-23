"""add country_code to master_banks

Revision ID: 36ff2dcdae4d
Revises: 61bd61581ace
Create Date: 2025-10-23 06:13:42.844836+00:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "36ff2dcdae4d"
down_revision: Union[str, None] = "61bd61581ace"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add new columns to master_banks table."""
    with op.batch_alter_table("master_banks", schema=None) as batch_op:
        # ✅ 새 컬럼 추가 (nullable=True로 안전하게)
        batch_op.add_column(sa.Column("country_code", sa.String(length=5), nullable=True))
        batch_op.add_column(sa.Column("order_no", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("meta", sa.JSON(), nullable=True))


def downgrade() -> None:
    """Rollback newly added columns."""
    with op.batch_alter_table("master_banks", schema=None) as batch_op:
        batch_op.drop_column("meta")
        batch_op.drop_column("order_no")
        batch_op.drop_column("country_code")
