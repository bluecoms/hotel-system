"""add updated_at to master_property_v23

Revision ID: 5004865355c9
Revises: 52d212b93e40
Create Date: 2025-10-26 09:47:47.043786+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5004865355c9'
down_revision: Union[str, None] = '52d212b93e40'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('master_property', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('(CURRENT_TIMESTAMP)'))
        )


def downgrade() -> None:
    with op.batch_alter_table('master_property', schema=None) as batch_op:
        batch_op.drop_column('updated_at')
