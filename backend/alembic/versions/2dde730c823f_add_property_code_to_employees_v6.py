"""add property_code to employees_v6

Revision ID: 2dde730c823f
Revises: f160c63556ac
Create Date: 2025-10-19 10:52:15.141774+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2dde730c823f'
down_revision: Union[str, None] = 'f160c63556ac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('employees', sa.Column('property_code', sa.String(length=10), nullable=False, server_default='MOP'))
    op.create_index('ix_employees_property_code', 'employees', ['property_code'])

def downgrade():
    op.drop_index('ix_employees_property_code', table_name='employees')
    op.drop_column('employees', 'property_code')
