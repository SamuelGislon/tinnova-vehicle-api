"""create vehicles table

Revision ID: 20260314_0002
Revises: 20260314_0001
Create Date: 2026-03-14 00:10:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "20260314_0002"
down_revision: Union[str, None] = "20260314_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vehicles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("brand", sa.String(length=50), nullable=False),
        sa.Column("model", sa.String(length=80), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("color", sa.String(length=30), nullable=False),
        sa.Column("plate", sa.String(length=7), nullable=False),
        sa.Column("price_usd", sa.Numeric(12, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint("price_usd > 0", name=op.f("ck_vehicles_price_usd_positive")),
        sa.CheckConstraint("year >= 1900", name=op.f("ck_vehicles_year_min_check")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_vehicles")),
        sa.UniqueConstraint("plate", name=op.f("uq_vehicles_plate")),
    )

    op.create_index("ix_vehicles_brand", "vehicles", ["brand"], unique=False)
    op.create_index("ix_vehicles_year", "vehicles", ["year"], unique=False)
    op.create_index("ix_vehicles_color", "vehicles", ["color"], unique=False)
    op.create_index("ix_vehicles_price_usd", "vehicles", ["price_usd"], unique=False)
    op.create_index("ix_vehicles_is_active", "vehicles", ["is_active"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_vehicles_is_active", table_name="vehicles")
    op.drop_index("ix_vehicles_price_usd", table_name="vehicles")
    op.drop_index("ix_vehicles_color", table_name="vehicles")
    op.drop_index("ix_vehicles_year", table_name="vehicles")
    op.drop_index("ix_vehicles_brand", table_name="vehicles")
    op.drop_table("vehicles")
