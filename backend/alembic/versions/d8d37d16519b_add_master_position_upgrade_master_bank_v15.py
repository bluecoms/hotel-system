"""add master_position / upgrade master_bank / drop master_ota_commission / add ota_channel.master_id_v15

Revision ID: d8d37d16519b
Revises: f5355da238b7
Create Date: 2025-10-21 19:18:24.832599+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision: str = 'd8d37d16519b'
down_revision: Union[str, None] = 'f5355da238b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # ─────────────────────────────────────────────
    # 1️⃣ master_positions — 신규 생성
    # ─────────────────────────────────────────────
    op.create_table(
        'master_positions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('code', sa.String(length=20), nullable=False, unique=True, index=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('order_no', sa.Integer(), default=0),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.UniqueConstraint('code', name='uq_master_positions_code'),
    )

    # ─────────────────────────────────────────────
    # 2️⃣ master_banks — alias / is_active / created_at 추가
    # ─────────────────────────────────────────────
    with op.batch_alter_table('master_banks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('alias', sa.String(length=50), nullable=True, server_default=''))
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'))
        batch_op.add_column(sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))

    # ─────────────────────────────────────────────
    # 3️⃣ master_ota_commissions — 삭제 (운영데이터로 분리)
    # ─────────────────────────────────────────────
    op.drop_table('master_ota_commissions')

    # ─────────────────────────────────────────────
    # 4️⃣ ota_channels — master_id FK 추가
    # ─────────────────────────────────────────────
    with op.batch_alter_table('ota_channels', schema=None) as batch_op:
        batch_op.add_column(sa.Column('master_id', sa.Integer(), sa.ForeignKey('master_ota_channels.id', ondelete='SET NULL'), nullable=True))
        batch_op.create_index('ix_ota_channels_master_id', ['master_id'], unique=False)


def downgrade():
    # ─────────────────────────────────────────────
    # downgrade 순서 (안전 역순)
    # ─────────────────────────────────────────────
    with op.batch_alter_table('ota_channels', schema=None) as batch_op:
        batch_op.drop_index('ix_ota_channels_master_id')
        batch_op.drop_column('master_id')

    op.create_table(
        'master_ota_commissions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('code', sa.String(length=50)),
        sa.Column('rate', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
    )

    with op.batch_alter_table('master_banks', schema=None) as batch_op:
        batch_op.drop_column('alias')
        batch_op.drop_column('is_active')
        batch_op.drop_column('created_at')

    op.drop_table('master_positions')