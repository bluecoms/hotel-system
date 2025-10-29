"""add housekeeping assignment tables

Revision ID: d935a356aeb4
Revises: 6f2cdd392dfd
Create Date: 2025-10-29 19:02:32.825910+00:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd935a356aeb4'
down_revision: Union[str, None] = '6f2cdd392dfd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========================================================================
    # ✅ housekeeping_assignments — 하우스키핑 정비 배정 테이블
    # ------------------------------------------------------------------------
    # 목적:
    #   • 업무일자별 객실 정비 담당자 배정 관리
    #   • employee_id (직원 FK) + room_no + property_code 단위로 유니크
    # ========================================================================
    op.create_table(
        'housekeeping_assignments',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('business_date', sa.String(length=10), nullable=False, comment='업무일자 (YYYY-MM-DD)'),
        sa.Column('property_code', sa.String(length=10), nullable=False, comment='지점 코드 (예: MOP)'),
        sa.Column('room_no', sa.String(length=20), nullable=False, comment='객실 번호'),
        sa.Column('room_type', sa.String(length=20), nullable=True, comment='객실 타입 코드'),
        sa.Column('employee_id', sa.Integer(), sa.ForeignKey('employees.id', ondelete='SET NULL'), nullable=True, comment='배정된 직원 ID'),
        sa.Column('memo', sa.String(length=255), nullable=True, comment='비고'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text("(DATETIME('now'))")),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text("(DATETIME('now'))")),
        sa.UniqueConstraint('business_date', 'property_code', 'room_no', name='uq_hk_assign_unique'),
    )

    # 인덱스 추가
    op.create_index('ix_housekeeping_assignments_date', 'housekeeping_assignments', ['business_date'])
    op.create_index('ix_housekeeping_assignments_property', 'housekeeping_assignments', ['property_code'])
    op.create_index('ix_housekeeping_assignments_room', 'housekeeping_assignments', ['room_no'])
    op.create_index('ix_housekeeping_assignments_employee', 'housekeeping_assignments', ['employee_id'])


def downgrade() -> None:
    # Rollback: 테이블 삭제
    op.drop_index('ix_housekeeping_assignments_employee', table_name='housekeeping_assignments')
    op.drop_index('ix_housekeeping_assignments_room', table_name='housekeeping_assignments')
    op.drop_index('ix_housekeeping_assignments_property', table_name='housekeeping_assignments')
    op.drop_index('ix_housekeeping_assignments_date', table_name='housekeeping_assignments')
    op.drop_table('housekeeping_assignments')
