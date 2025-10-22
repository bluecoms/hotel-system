"""ensure ota_channels.master_id column and FK_v14

Revision ID: f5355da238b7
Revises: 7e7c1582b61f
Create Date: 2025-10-21 12:17:58.039840+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f5355da238b7'
down_revision: Union[str, None] = '7e7c1582b61f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = [c['name'] for c in insp.get_columns('ota_channels')]
    if 'master_id' not in cols:
        with op.batch_alter_table('ota_channels') as b:
            b.add_column(sa.Column('master_id', sa.Integer(), nullable=True))
            # SQLite에선 FK 생성이 실패할 수 있으므로 시도-무시
            try:
                b.create_foreign_key(
                    'fk_ota_channels_master',
                    'master_ota_channels',
                    ['master_id'], ['id'],
                    ondelete='SET NULL',
                )
            except Exception:
                pass

def downgrade():
    with op.batch_alter_table('ota_channels') as b:
        try:
            b.drop_constraint('fk_ota_channels_master', type_='foreignkey')
        except Exception:
            pass
        try:
            b.drop_column('master_id')
        except Exception:
            pass