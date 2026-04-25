"""Planograms — expected shelf layouts + scan results.

Revision ID: 20260501_0013
Revises: 20260430_0012
Create Date: 2026-05-01
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260501_0013"
down_revision: str | Sequence[str] | None = "20260430_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "planograms",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("location_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("expected", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_planograms_tenant_id", "planograms", ["tenant_id"])

    op.create_table(
        "planogram_scans",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "planogram_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("planograms.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("image_public_id", sa.String(512), nullable=False),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_planogram_scans_tenant_id", "planogram_scans", ["tenant_id"])
    op.create_index("ix_planogram_scans_planogram_id", "planogram_scans", ["planogram_id"])


def downgrade() -> None:
    op.drop_index("ix_planogram_scans_planogram_id", table_name="planogram_scans")
    op.drop_index("ix_planogram_scans_tenant_id", table_name="planogram_scans")
    op.drop_table("planogram_scans")

    op.drop_index("ix_planograms_tenant_id", table_name="planograms")
    op.drop_table("planograms")

