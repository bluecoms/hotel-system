"""add bank_code column to bank_accounts_v10

Revision ID: c458917d6ad5
Revises: a09f2f0a8d3d
Create Date: 2025-10-20 17:35:33.430688+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c458917d6ad5'
down_revision: Union[str, None] = 'a09f2f0a8d3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column("bank_accounts", sa.Column("bank_code", sa.String(length=20), nullable=True))

def downgrade():
    op.drop_column("bank_accounts", "bank_code")