"""deptaccess migration_v8

Revision ID: dc31ef4ad1b2
Revises: 14794aadded8
Create Date: 2025-10-19 20:24:03.369282+00:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = "dc31ef4ad1b2"
down_revision: Union[str, None] = "14794aadded8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    DeptAccess Migration — 기존 role_access 테이블 구조 변경
      • role_code, access_level 제거
      • access_scope(JSON) 신규 컬럼으로 대체
      • SUPERADMIN → ["ALL_EDIT"]
      • ADMIN → ["ALL_VIEW"]
      • 기타 → [role_code]
    """
    conn = op.get_bind()

    # 1️⃣ 임시 테이블 생성 (신규 구조)
    op.create_table(
        "role_access_tmp",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("route_name", sa.String(120), nullable=False, index=True),
        sa.Column("access_scope", sa.JSON, nullable=True, server_default="[]"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    # 2️⃣ 기존 role_access 데이터 로드 (role_code 기반 변환)
    try:
        old_rows = conn.execute(text("SELECT route_name, role_code, access_level FROM role_access")).fetchall()
    except Exception:
        old_rows = []

    for r in old_rows:
        role_code = (r.role_code or "").upper()
        route_name = (r.route_name or "").strip()

        # scope 변환 규칙
        if role_code == "SUPERADMIN":
            scopes = ["ALL_EDIT"]
        elif role_code == "ADMIN":
            scopes = ["ALL_VIEW"]
        elif role_code:
            scopes = [role_code]
        else:
            scopes = []

        conn.execute(
            text(
                "INSERT INTO role_access_tmp (route_name, access_scope, created_at) "
                "VALUES (:route_name, :access_scope, CURRENT_TIMESTAMP)"
            ),
            {"route_name": route_name, "access_scope": str(scopes)},
        )

    # 3️⃣ 기존 테이블 제거 및 교체
    op.drop_table("role_access")
    op.rename_table("role_access_tmp", "role_access")

    # 4️⃣ 유니크 제약 추가
    with op.batch_alter_table("role_access") as batch_op:
        batch_op.create_unique_constraint("uq_role_access_route", ["route_name"])

    print("✅ DeptAccess migration complete: role_access now uses access_scope (JSON).")


def downgrade() -> None:
    """
    복원 불가 (논리적 변경)
    """
    print("⚠️ Downgrade not supported for DeptAccess migration.")
