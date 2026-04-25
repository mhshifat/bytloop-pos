"""Supply chain — product suppliers + PO promise dates.

Revision ID: 20260501_0015
Revises: 20260501_0014
Create Date: 2026-05-01
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260501_0015"
down_revision: str | Sequence[str] | None = "20260501_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "product_suppliers",
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
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "supplier_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("suppliers.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("is_preferred", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("unit_cost_cents", sa.Integer, nullable=False, server_default="0"),
        sa.Column("lead_time_days", sa.Integer, nullable=False, server_default="7"),
        sa.Column("lead_time_std_days", sa.Integer, nullable=False, server_default="2"),
        sa.Column("min_order_qty", sa.Integer, nullable=False, server_default="1"),
        sa.Column("pack_size", sa.Integer, nullable=False, server_default="1"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "product_id", "supplier_id", name="uq_product_suppliers"),
    )
    op.create_index("ix_product_suppliers_tenant_id", "product_suppliers", ["tenant_id"])
    op.create_index("ix_product_suppliers_product_id", "product_suppliers", ["product_id"])
    op.create_index("ix_product_suppliers_supplier_id", "product_suppliers", ["supplier_id"])

    op.add_column(
        "purchase_orders",
        sa.Column("promise_date", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_purchase_orders_promise_date", "purchase_orders", ["promise_date"])


def downgrade() -> None:
    op.drop_index("ix_purchase_orders_promise_date", table_name="purchase_orders")
    op.drop_column("purchase_orders", "promise_date")

    op.drop_index("ix_product_suppliers_supplier_id", table_name="product_suppliers")
    op.drop_index("ix_product_suppliers_product_id", table_name="product_suppliers")
    op.drop_index("ix_product_suppliers_tenant_id", table_name="product_suppliers")
    op.drop_table("product_suppliers")

