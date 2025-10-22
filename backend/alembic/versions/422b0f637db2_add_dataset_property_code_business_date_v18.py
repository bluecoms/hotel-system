"""add dataset, property_code, business_date to uploaded_files_v18

Revision ID: 422b0f637db2
Revises: 4fe94bf97fce
Create Date: 2025-10-22 08:47:40.074286+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '422b0f637db2'
down_revision: Union[str, None] = '4fe94bf97fce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    with op.batch_alter_table('uploaded_files', schema=None) as batch:
        batch.add_column(sa.Column('dataset', sa.String(64), nullable=True))
        batch.add_column(sa.Column('property_code', sa.String(32), nullable=True))
        batch.add_column(sa.Column('business_date', sa.String(16), nullable=True))

def downgrade():
    with op.batch_alter_table('uploaded_files', schema=None) as batch:
        batch.drop_column('dataset')
        batch.drop_column('property_code')
        batch.drop_column('business_date')