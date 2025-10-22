"""add master_ota_channels and fk to ota_channels_v13

Revision ID: 7e7c1582b61f
Revises: 638fc454e2d5
Create Date: 2025-10-21 09:32:21.064230+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7e7c1582b61f'
down_revision: Union[str, None] = '638fc454e2d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1️⃣ master_ota_channels 테이블 생성
    op.create_table(
        'master_ota_channels',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('code', sa.String(length=50), nullable=False, unique=True, index=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column('order_no', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )

    # 2️⃣ ota_channels 테이블에 master_id(FK) 추가
    with op.batch_alter_table('ota_channels', schema=None) as batch_op:
        batch_op.add_column(sa.Column('master_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_ota_channels_master',
            'master_ota_channels',
            ['master_id'],
            ['id'],
            ondelete='SET NULL',
        )


def downgrade():
    # FK 제거
    with op.batch_alter_table('ota_channels', schema=None) as batch_op:
        batch_op.drop_constraint('fk_ota_channels_master', type_='foreignkey')
        batch_op.drop_column('master_id')

    # master_ota_channels 테이블 제거
    op.drop_table('master_ota_channels')