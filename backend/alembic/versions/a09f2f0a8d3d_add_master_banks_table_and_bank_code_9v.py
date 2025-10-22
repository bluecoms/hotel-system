"""add master_banks table and bank_code column_v9

Revision ID: a09f2f0a8d3d
Revises: dc31ef4ad1b2
Create Date: 2025-10-20 17:04:06.292275+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a09f2f0a8d3d'
down_revision: Union[str, None] = 'dc31ef4ad1b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1️⃣ master_banks 테이블 생성
    op.create_table(
        'master_banks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('code', sa.String(length=20), nullable=False, unique=True, index=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('alias', sa.String(length=50), nullable=True, server_default=""),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text("(datetime('now'))")),
        sa.UniqueConstraint('code', name='uq_master_bank_code')
    )

    # 2️⃣ bank_accounts 테이블에 bank_code 컬럼 추가
    with op.batch_alter_table('bank_accounts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('bank_code', sa.String(length=20), nullable=True))
        batch_op.create_foreign_key(
            'fk_bank_accounts_bank_code',
            'master_banks',
            ['bank_code'],
            ['code'],
        )


def downgrade():
    # FK / 컬럼 삭제
    with op.batch_alter_table('bank_accounts', schema=None) as batch_op:
        batch_op.drop_constraint('fk_bank_accounts_bank_code', type_='foreignkey')
        batch_op.drop_column('bank_code')

    # 테이블 삭제
    op.drop_table('master_banks')