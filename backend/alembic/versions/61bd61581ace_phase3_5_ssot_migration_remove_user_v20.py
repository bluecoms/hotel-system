"""Phase3.5 SSOT Migration: remove user_roles & role_access, add dept_access_v20

Revision ID: 61bd61581ace
Revises: 78aa3e91389e
Create Date: 2025-10-22 12:40:08.926486+00:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '61bd61581ace'
down_revision: Union[str, None] = '78aa3e91389e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ----------------------------------------------------------------------------
# UPGRADE
# ----------------------------------------------------------------------------
def upgrade() -> None:
    """Upgrade — Phase3.5 SSOT Migration"""
    # 1️⃣ 기존 user_roles / role_access 제거 (존재 시만)
    try:
        op.drop_table('user_roles')
        print(" Dropped table user_roles")
    except Exception:
        print("⚠️ user_roles table not found — skip")

    try:
        op.drop_table('role_access')
        print(" Dropped table role_access")
    except Exception:
        print("⚠️ role_access table not found — skip")

    # 2️⃣ DeptAccess 테이블 신규 생성 (이미 있으면 skip)
    try:
        op.create_table(
            'dept_access',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('route_name', sa.String(length=120), nullable=False, unique=True),
            sa.Column('access_scope', sa.JSON(), nullable=False, server_default='[]'),
            sa.Column(
                'created_at',
                sa.DateTime(timezone=True),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=False,
            ),
        )
        print("✅ Created table dept_access")
    except Exception as e:
        print(f"⚠️ dept_access already exists — skipping create_table() ({e})")

    print("✅ Phase3.5 SSOT Migration upgrade complete.")


# ----------------------------------------------------------------------------
# DOWNGRADE
# ----------------------------------------------------------------------------
def downgrade() -> None:
    """Downgrade — Rollback Phase3.5"""
    # DeptAccess 제거
    try:
        op.drop_table('dept_access')
        print(" Dropped table dept_access")
    except Exception:
        print("⚠️ dept_access not found — skip")

    # 기존 RoleAccess / UserRole 복원
    try:
        op.create_table(
            'role_access',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('route_name', sa.String(length=120), nullable=False),
            sa.Column('access_scope', sa.JSON(), nullable=True, server_default='[]'),
            sa.Column(
                'created_at',
                sa.DateTime(),
                server_default=sa.text('(CURRENT_TIMESTAMP)'),
                nullable=False,
            ),
            sa.UniqueConstraint('route_name', name='uq_role_access_route'),
        )
        print("✅ Recreated table role_access")
    except Exception:
        print("⚠️ role_access already exists — skip")

    try:
        op.create_table(
            'user_roles',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('role_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['role_id'], ['roles.id']),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.UniqueConstraint('user_id', 'role_id', name='uq_user_role'),
        )
        print("✅ Recreated table user_roles")
    except Exception:
        print("⚠️ user_roles already exists — skip")

    print("✅ Phase3.5 SSOT Migration downgrade complete.")
