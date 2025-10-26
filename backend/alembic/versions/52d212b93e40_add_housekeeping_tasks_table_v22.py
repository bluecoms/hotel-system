"""add housekeeping_tasks table_v22

Revision ID: 52d212b93e40
Revises: 36ff2dcdae4d
Create Date: 2025-10-23 07:23:30.636240+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '52d212b93e40'
down_revision: Union[str, None] = '36ff2dcdae4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    with op.batch_alter_table("housekeeping_tasks") as batch:
        batch.drop_column("staff_name")
        batch.add_column(
            sa.Column(
                "employee_id",
                sa.Integer(),
                sa.ForeignKey("employees.id", name="fk_housekeeping_tasks_employee_id")
            )
        )
        batch.add_column(sa.Column("department_code", sa.String(length=10)))


def downgrade():
    with op.batch_alter_table("housekeeping_tasks") as batch:
        batch.drop_column("department_code")
        batch.drop_column("employee_id")
        batch.add_column(sa.Column("staff_name", sa.String(length=50)))