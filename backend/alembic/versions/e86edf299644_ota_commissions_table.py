"""ota commissions table

Revision ID: e86edf299644
Revises: 2bf033a72e6e
Create Date: 2025-10-01 12:13:18.813552+00:00

"""
# -*- coding: utf-8 -*-
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "e86edf299644"
down_revision = "2bf033a72e6e"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "ota_commissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("channel_id", sa.Integer(), sa.ForeignKey("ota_channels.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_to", sa.Date(), nullable=False),
        sa.Column("rate", sa.Float(), nullable=False),  # 0.0~1.0
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("(CURRENT_TIMESTAMP)")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("(CURRENT_TIMESTAMP)")),
    )
    op.create_index("ix_ota_commissions_id", "ota_commissions", ["id"])
    op.create_index("ix_ota_commissions_channel_id", "ota_commissions", ["channel_id"])
    op.create_index("ix_ota_commissions_valid_from", "ota_commissions", ["valid_from"])
    op.create_index("ix_ota_commissions_valid_to", "ota_commissions", ["valid_to"])
    op.create_index("ix_ota_commissions_channel_period", "ota_commissions", ["channel_id", "valid_from", "valid_to"])

def downgrade():
    op.drop_index("ix_ota_commissions_channel_period", table_name="ota_commissions")
    op.drop_index("ix_ota_commissions_valid_to", table_name="ota_commissions")
    op.drop_index("ix_ota_commissions_valid_from", table_name="ota_commissions")
    op.drop_index("ix_ota_commissions_channel_id", table_name="ota_commissions")
    op.drop_index("ix_ota_commissions_id", table_name="ota_commissions")
    op.drop_table("ota_commissions")
