"""add leader_emp_id to departments_7v

Revision ID: 14794aadded8
Revises: 2dde730c823f
Create Date: 2025-10-19 17:35:47.667236+00:00

"""
# ============================================================================
# Alembic Migration — Add leader_emp_id Column to departments
# ----------------------------------------------------------------------------
# 목적:
#   • departments 테이블에 부서 팀장 지정용 leader_emp_id 컬럼 추가
#   • employees.id FK 연결 (SET NULL on delete)
# 변경 내용:
#   ✅ 컬럼 추가 → leader_emp_id (nullable)
#   ✅ FK 제약 → fk_departments_leader_emp → employees.id
#   ✅ 롤백 시 FK 및 컬럼 제거
# ============================================================================
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# ─────────────────────────────
# Revision identifiers
# ─────────────────────────────
revision: str = '14794aadded8'
down_revision: Union[str, None] = '2dde730c823f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ─────────────────────────────
# Upgrade
# ─────────────────────────────
def upgrade() -> None:
    with op.batch_alter_table('departments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('leader_emp_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_departments_leader_emp',
            'employees',
            ['leader_emp_id'],
            ['id'],
            ondelete='SET NULL'
        )

# ─────────────────────────────
# Downgrade
# ─────────────────────────────
def downgrade() -> None:
    with op.batch_alter_table('departments', schema=None) as batch_op:
        batch_op.drop_constraint('fk_departments_leader_emp', type_='foreignkey')
        batch_op.drop_column('leader_emp_id')