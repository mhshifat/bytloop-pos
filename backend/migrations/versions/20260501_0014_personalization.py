"""Personalization — segments + campaign triggers.

Revision ID: 20260501_0014
Revises: 20260501_0013
Create Date: 2026-05-01
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260501_0014"
down_revision: str | Sequence[str] | None = "20260501_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "customer_segments",
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
        sa.Column("kind", sa.String(32), nullable=False, server_default="cluster"),
        sa.Column(
            "definition",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "name", name="uq_customer_segments_tenant_name"),
    )
    op.create_index("ix_customer_segments_tenant_id", "customer_segments", ["tenant_id"])

    op.create_table(
        "segment_memberships",
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
            "segment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("customer_segments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "customer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("customers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("score", sa.Float, nullable=False, server_default="0"),
        sa.Column(
            "meta",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("refreshed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("segment_id", "customer_id", name="uq_segment_membership"),
    )
    op.create_index("ix_segment_memberships_tenant_id", "segment_memberships", ["tenant_id"])
    op.create_index("ix_segment_memberships_segment_id", "segment_memberships", ["segment_id"])
    op.create_index("ix_segment_memberships_customer_id", "segment_memberships", ["customer_id"])

    op.create_table(
        "campaign_triggers",
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
            "segment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("customer_segments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("channel", sa.String(16), nullable=False, server_default="email"),
        sa.Column("threshold", sa.Float, nullable=False, server_default="0.6"),
        sa.Column("subject", sa.String(255), nullable=False, server_default=""),
        sa.Column("html_template", sa.String(8000), nullable=False, server_default=""),
        sa.Column("discount_code", sa.String(64), nullable=True),
        sa.Column("cooldown_days", sa.Integer, nullable=False, server_default="14"),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_campaign_triggers_tenant_id", "campaign_triggers", ["tenant_id"])
    op.create_index("ix_campaign_triggers_segment_id", "campaign_triggers", ["segment_id"])

    op.create_table(
        "campaign_deliveries",
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
            "trigger_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("campaign_triggers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "customer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("customers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("last_sent_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint(
            "trigger_id",
            "customer_id",
            name="uq_campaign_delivery_trigger_customer",
        ),
    )
    op.create_index("ix_campaign_deliveries_tenant_id", "campaign_deliveries", ["tenant_id"])
    op.create_index("ix_campaign_deliveries_trigger_id", "campaign_deliveries", ["trigger_id"])
    op.create_index("ix_campaign_deliveries_customer_id", "campaign_deliveries", ["customer_id"])


def downgrade() -> None:
    op.drop_index("ix_campaign_deliveries_customer_id", table_name="campaign_deliveries")
    op.drop_index("ix_campaign_deliveries_trigger_id", table_name="campaign_deliveries")
    op.drop_index("ix_campaign_deliveries_tenant_id", table_name="campaign_deliveries")
    op.drop_table("campaign_deliveries")

    op.drop_index("ix_campaign_triggers_segment_id", table_name="campaign_triggers")
    op.drop_index("ix_campaign_triggers_tenant_id", table_name="campaign_triggers")
    op.drop_table("campaign_triggers")

    op.drop_index("ix_segment_memberships_customer_id", table_name="segment_memberships")
    op.drop_index("ix_segment_memberships_segment_id", table_name="segment_memberships")
    op.drop_index("ix_segment_memberships_tenant_id", table_name="segment_memberships")
    op.drop_table("segment_memberships")

    op.drop_index("ix_customer_segments_tenant_id", table_name="customer_segments")
    op.drop_table("customer_segments")

