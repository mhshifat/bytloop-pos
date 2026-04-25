"""AI analytics — campaign touch tracking for multi-touch attribution.

The other 7 AI features (forecasting, anomaly, churn, LTV, NL-QA, cohort,
benchmark) are purely read-paths against existing tables. Only attribution
(#8) needs new schema: every inbound visit writes a ``campaign_touches``
row so we can replay the touch-path of each completed order.

Revision ID: 20260430_0012
Revises: 20260429_0011
Create Date: 2026-04-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260430_0012"
down_revision: str | Sequence[str] | None = "20260429_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "campaign_touches",
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
            "customer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("customers.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("channel", sa.String(64), nullable=False),
        sa.Column("source", sa.String(64), nullable=True),
        sa.Column("medium", sa.String(64), nullable=True),
        sa.Column("campaign", sa.String(128), nullable=True),
        sa.Column("landing_page", sa.String(255), nullable=True),
        sa.Column(
            "touched_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_campaign_touches_tenant_id", "campaign_touches", ["tenant_id"])
    op.create_index("ix_campaign_touches_customer_id", "campaign_touches", ["customer_id"])
    op.create_index("ix_campaign_touches_channel", "campaign_touches", ["channel"])
    # Composite index tuned for the attribution query — it scans per customer
    # filtered to the lookback window.
    op.create_index(
        "ix_campaign_touches_customer_touched_at",
        "campaign_touches",
        ["customer_id", "touched_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_campaign_touches_customer_touched_at", table_name="campaign_touches")
    op.drop_index("ix_campaign_touches_channel", table_name="campaign_touches")
    op.drop_index("ix_campaign_touches_customer_id", table_name="campaign_touches")
    op.drop_index("ix_campaign_touches_tenant_id", table_name="campaign_touches")
    op.drop_table("campaign_touches")
