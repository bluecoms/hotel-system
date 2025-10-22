"""recreate master_property table_v19

Revision ID: 78aa3e91389e
Revises: 422b0f637db2
Create Date: 2025-10-22 08:57:03.374283+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '78aa3e91389e'
down_revision: Union[str, None] = '422b0f637db2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        'master_property',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('code', sa.String(16), unique=True, nullable=False, index=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('address', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

def downgrade():
    op.drop_table('master_property')