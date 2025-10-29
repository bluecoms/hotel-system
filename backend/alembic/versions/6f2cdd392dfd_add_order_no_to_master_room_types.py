"""add order_no to master_room_types

Revision ID: 6f2cdd392dfd
Revises: 53431adee5a6
Create Date: 2025-10-27 08:37:02.857425+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6f2cdd392dfd'
down_revision: Union[str, None] = '53431adee5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("master_room_types", schema=None) as batch_op:
        batch_op.add_column(sa.Column("order_no", sa.Integer(), nullable=False, server_default="0"))
        batch_op.create_index("ix_master_room_types_order_no", ["order_no"], unique=False)

def downgrade() -> None:
    with op.batch_alter_table("master_room_types", schema=None) as batch_op:
        batch_op.drop_index("ix_master_room_types_order_no")
        batch_op.drop_column("order_no")