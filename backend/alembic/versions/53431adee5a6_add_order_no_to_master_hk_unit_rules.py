"""add order_no to master_hk_unit_rules

Revision ID: 53431adee5a6
Revises: c4ba0cb59598
Create Date: 2025-10-27 08:33:20.694315+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '53431adee5a6'
down_revision: Union[str, None] = 'c4ba0cb59598'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("master_hk_unit_rules", schema=None) as batch_op:
        batch_op.add_column(sa.Column("order_no", sa.Integer(), nullable=False, server_default="0"))
        batch_op.create_index("ix_master_hk_unit_rules_order_no", ["order_no"], unique=False)

def downgrade() -> None:
    with op.batch_alter_table("master_hk_unit_rules", schema=None) as batch_op:
        batch_op.drop_index("ix_master_hk_unit_rules_order_no")
        batch_op.drop_column("order_no")