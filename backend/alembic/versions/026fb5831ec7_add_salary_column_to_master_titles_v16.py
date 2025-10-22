"""add salary column to master_titles_v16

Revision ID: 026fb5831ec7
Revises: d8d37d16519b
Create Date: 2025-10-22 03:44:13.778772+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = '026fb5831ec7'
down_revision: Union[str, None] = 'd8d37d16519b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('master_titles', sa.Column('salary', sa.Numeric(12, 2), nullable=True))

    # ### end Alembic commands ###


def downgrade() -> None:
    op.drop_column('master_titles', 'salary')

    # ### end Alembic commands ###
