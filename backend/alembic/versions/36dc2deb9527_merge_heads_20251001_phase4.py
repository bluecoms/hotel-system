"""merge heads: 20251001 + phase4

Revision ID: 36dc2deb9527
Revises: 20251001_add_commission_period_rate, 2322535ac344
Create Date: 2025-10-02 05:18:52.358223+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '36dc2deb9527'
down_revision: Union[str, None] = ('20251001_add_commission_period_rate', '2322535ac344')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
