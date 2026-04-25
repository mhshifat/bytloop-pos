"""Phase 3 — restaurant (tables, KOT), apparel variants, grocery (PLU, weighables).

Revision ID: 20260424_0004
Revises: 20260424_0003
Create Date: 2026-04-24
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260424_0004"
down_revision: str | Sequence[str] | None = "20260424_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Restaurant
    op.create_table(
        "restaurant_tables",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "location_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("locations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(16), nullable=False),
        sa.Column("label", sa.String(64), nullable=False),
        sa.Column("seats", sa.Integer, nullable=False, server_default="4"),
        sa.Column("status", sa.String(16), nullable=False, server_default="available"),
        sa.Column(
            "current_order_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("orders.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "code", name="uq_tables_tenant_code"),
    )
    op.create_index("ix_restaurant_tables_tenant_id", "restaurant_tables", ["tenant_id"])

    op.create_table(
        "kot_tickets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "order_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("station", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="new"),
        sa.Column("number", sa.String(16), nullable=False),
        sa.Column("fired_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("ready_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_kot_tickets_tenant_id", "kot_tickets", ["tenant_id"])
    op.create_index("ix_kot_tickets_order_id", "kot_tickets", ["order_id"])
    op.create_index("ix_kot_tickets_number", "kot_tickets", ["number"])

    op.create_table(
        "kot_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "ticket_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("kot_tickets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("products.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("name_snapshot", sa.String(255), nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False, server_default="1"),
        sa.Column("modifier_notes", sa.String(512), nullable=True),
    )
    op.create_index("ix_kot_items_tenant_id", "kot_items", ["tenant_id"])
    op.create_index("ix_kot_items_ticket_id", "kot_items", ["ticket_id"])

    # Apparel
    op.create_table(
        "apparel_variants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sku", sa.String(64), nullable=False),
        sa.Column("barcode", sa.String(64), nullable=True),
        sa.Column("size", sa.String(16), nullable=False),
        sa.Column("color", sa.String(32), nullable=False),
        sa.Column("price_cents_override", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "sku", name="uq_apparel_variants_tenant_sku"),
        sa.UniqueConstraint(
            "product_id", "size", "color", name="uq_apparel_variants_product_size_color"
        ),
    )
    op.create_index("ix_apparel_variants_tenant_id", "apparel_variants", ["tenant_id"])
    op.create_index("ix_apparel_variants_product_id", "apparel_variants", ["product_id"])
    op.create_index("ix_apparel_variants_barcode", "apparel_variants", ["barcode"])

    # Grocery
    op.create_table(
        "grocery_skus",
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sell_unit", sa.String(8), nullable=False, server_default="each"),
        sa.Column("price_per_unit_cents", sa.Integer, nullable=False, server_default="0"),
        sa.Column("tare_grams", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_grocery_skus_tenant_id", "grocery_skus", ["tenant_id"])

    op.create_table(
        "plu_codes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(8), nullable=False),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.UniqueConstraint("tenant_id", "code", name="uq_plu_tenant_code"),
    )
    op.create_index("ix_plu_codes_tenant_id", "plu_codes", ["tenant_id"])
    op.create_index("ix_plu_codes_product_id", "plu_codes", ["product_id"])


def downgrade() -> None:
    for table in (
        "plu_codes",
        "grocery_skus",
        "apparel_variants",
        "kot_items",
        "kot_tickets",
        "restaurant_tables",
    ):
        op.drop_table(table)
