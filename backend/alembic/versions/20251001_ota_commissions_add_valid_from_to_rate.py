"""ota commissions table

Revision ID: e86edf299644
Revises: 2bf033a72e6e
Create Date: 2025-10-01 12:13:18.813552+00:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251001_add_commission_period_rate"
down_revision = "e86edf299644"  # 예: "abcd1234efgh"
branch_labels = None
depends_on = None

def _has_column(table, column):
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return column in [c["name"] for c in insp.get_columns(table)]

def _has_index(table, index_name):
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return any(ix["name"] == index_name for ix in insp.get_indexes(table))

def upgrade():
    # — 컬럼 없으면 추가 (널 허용으로 추가 → 백필 → 필요시 널 금지로 전환도 가능)
    if not _has_column("ota_commissions", "valid_from"):
        op.add_column("ota_commissions", sa.Column("valid_from", sa.Date(), nullable=True))
    if not _has_column("ota_commissions", "valid_to"):
        op.add_column("ota_commissions", sa.Column("valid_to", sa.Date(), nullable=True))
    if not _has_column("ota_commissions", "rate"):
        op.add_column("ota_commissions", sa.Column("rate", sa.Float(), nullable=True))
    if not _has_column("ota_commissions", "note"):
        op.add_column("ota_commissions", sa.Column("note", sa.Text(), nullable=True))
    if not _has_column("ota_commissions", "updated_at"):
        op.add_column(
            "ota_commissions",
            sa.Column("updated_at", sa.DateTime(), nullable=True,
                      server_default=sa.text("(CURRENT_TIMESTAMP)"))
        )

    # — 기존 effective_date가 있다면 from/to로 백필 (선택적 호환)
    conn = op.get_bind()
    if _has_column("ota_commissions", "effective_date"):
        conn.execute(sa.text("""
            UPDATE ota_commissions
               SET valid_from = COALESCE(valid_from, effective_date),
                   valid_to   = COALESCE(valid_to,   effective_date)
            WHERE valid_from IS NULL OR valid_to IS NULL
        """))

    # — 널 기본값 보정
    conn.execute(sa.text("""
        UPDATE ota_commissions
           SET valid_from = COALESCE(valid_from, valid_to),
               valid_to   = COALESCE(valid_to, valid_from),
               rate       = COALESCE(rate, 0.0)
        WHERE valid_from IS NULL OR valid_to IS NULL OR rate IS NULL
    """))

    # — 인덱스 생성(존재하지 않을 때만)
    if not _has_index("ota_commissions", "ix_ota_commissions_channel_period"):
        op.create_index(
            "ix_ota_commissions_channel_period",
            "ota_commissions", ["channel_id", "valid_from", "valid_to"]
        )

    # (옵션) 널 금지 전환 — SQLite에선 간단치 않아 생략하거나 후속 마이그레이션에서 처리 권장
    # op.alter_column("ota_commissions", "valid_from", nullable=False)
    # op.alter_column("ota_commissions", "valid_to", nullable=False)
    # op.alter_column("ota_commissions", "rate", nullable=False)

def downgrade():
    # 안전을 위해 드롭은 생략 (운영 데이터 보호)
    pass
