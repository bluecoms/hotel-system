"""unique ota_channels.code

Revision ID: 2bf033a72e6e
Revises: 38bfc3b56da1
Create Date: 2025-10-01 05:17:20.100361+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2bf033a72e6e'
down_revision: Union[str, None] = '38bfc3b56da1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
