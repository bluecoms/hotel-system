"""add is_active and version_no to upload_files (SSOT v3.6)_v17

Revision ID: 4fe94bf97fce
Revises: 026fb5831ec7
Create Date: 2025-10-22 08:13:28.366431+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4fe94bf97fce'
down_revision: Union[str, None] = '026fb5831ec7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    with op.batch_alter_table('uploaded_files', schema=None) as batch:
        batch.add_column(sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False))
        batch.add_column(sa.Column('version_no', sa.Integer(), server_default='1', nullable=False))

def downgrade():
    with op.batch_alter_table('uploaded_files', schema=None) as batch:
        batch.drop_column('is_active')
        batch.drop_column('version_no')