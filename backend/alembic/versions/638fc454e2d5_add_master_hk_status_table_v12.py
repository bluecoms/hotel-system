"""add master_hk_status table_v12

Revision ID: 638fc454e2d5
Revises: 2f9a11c962ff
Create Date: 2025-10-21 04:31:22.092142+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = '638fc454e2d5'
down_revision: Union[str, None] = '2f9a11c962ff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = '638fc454e2d5'
down_revision: Union[str, None] = '2f9a11c962ff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'master_hk_status',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text("(datetime('now'))")),
        sa.UniqueConstraint('code', name='uq_master_hk_status_code')
    )

def downgrade() -> None:
    op.drop_table('master_hk_status')
    # ### end Alembic commands ###