"""add indexes to employee_contracts for latest/status/start_date

Revision ID: 2f9a11c962ff
Revises: c458917d6ad5
Create Date: 2025-10-20 18:37:31.069576+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f9a11c962ff'
down_revision: Union[str, None] = 'c458917d6ad5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_index('ix_emp_contract_latest', 'employee_contracts', ['employee_id', 'is_latest'])
    op.create_index('ix_emp_contract_start',  'employee_contracts', ['employee_id', 'start_date'])
    op.create_index('ix_emp_contract_status', 'employee_contracts', ['status'])

def downgrade():
    op.drop_index('ix_emp_contract_status', table_name='employee_contracts')
    op.drop_index('ix_emp_contract_start',  table_name='employee_contracts')
    op.drop_index('ix_emp_contract_latest', table_name='employee_contracts')