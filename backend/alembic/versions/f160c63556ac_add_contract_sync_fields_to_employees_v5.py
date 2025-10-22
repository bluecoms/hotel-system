"""add contract sync fields to employees_v5

Revision ID: f160c63556ac
Revises: add_sales_front_table_v4
Create Date: 2025-10-19 09:45:49.419078+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f160c63556ac'
down_revision: Union[str, None] = 'add_sales_front_table_v4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('employees', sa.Column('contract_status', sa.String(length=20), nullable=False, server_default=''))
    op.add_column('employees', sa.Column('contract_start', sa.Date(), nullable=True))
    op.add_column('employees', sa.Column('contract_end', sa.Date(), nullable=True))

def downgrade() -> None:
    op.drop_column('employees', 'contract_status')
    op.drop_column('employees', 'contract_start')
    op.drop_column('employees', 'contract_end')
