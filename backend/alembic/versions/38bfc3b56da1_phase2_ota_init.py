# -*- coding: utf-8 -*-
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "38bfc3b56da1"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "ota_channels",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_table(
        "ota_commissions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("channel_id", sa.Integer, sa.ForeignKey("ota_channels.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rate", sa.Float, nullable=False),  # 0~1
        sa.Column("effective_date", sa.Date, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_ota_commissions_channel_date", "ota_commissions", ["channel_id", "effective_date"], unique=False)

def downgrade():
    op.drop_index("ix_ota_commissions_channel_date", table_name="ota_commissions")
    op.drop_table("ota_commissions")
    op.drop_table("ota_channels")
