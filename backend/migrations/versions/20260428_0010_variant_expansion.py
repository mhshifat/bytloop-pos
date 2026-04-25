"""55-variant expansion — 15 new verticals across retail/F&B/services/specialty.

Adds the `tenants.vertical_profile` column plus 30 new tables shipped by the
parallel-agent batch (Electronics, Age-restricted, Consignment, Cannabis,
Modifiers, Preorders, Bar tabs, Deliveries, RFID memberships, Gas station,
Laundry, Patient records, Tickets, Donations, Wholesale).

Revision ID: 20260428_0010
Revises: 20260427_0009
Create Date: 2026-04-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260428_0010"
down_revision: str | Sequence[str] | None = "20260427_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# ──────────────────────────────────────────────────────────────────────────
# Helpers — keep column lists readable
# ──────────────────────────────────────────────────────────────────────────

_PK = sa.Column(
    "id",
    postgresql.UUID(as_uuid=True),
    primary_key=True,
    server_default=sa.text("gen_random_uuid()"),
)


def _tenant_fk():
    return sa.Column(
        "tenant_id",
        postgresql.UUID(as_uuid=True),
        sa.ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )


def _fk(name: str, target: str, *, nullable: bool = True, ondelete: str = "SET NULL"):
    return sa.Column(
        name,
        postgresql.UUID(as_uuid=True),
        sa.ForeignKey(target, ondelete=ondelete),
        nullable=nullable,
    )


def _created_at(name: str = "created_at"):
    return sa.Column(
        name, sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )


def upgrade() -> None:
    # ── Tenants: vertical_profile column ───────────────────────────────
    op.add_column(
        "tenants",
        sa.Column(
            "vertical_profile",
            sa.String(32),
            nullable=False,
            server_default="retail_general",
        ),
    )
    op.alter_column("tenants", "vertical_profile", server_default=None)

    # ── Electronics ────────────────────────────────────────────────────
    op.create_table(
        "electronics_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        _tenant_fk(),
        _fk("product_id", "products.id", nullable=False, ondelete="CASCADE"),
        sa.Column("serial_no", sa.String(128), nullable=False),
        sa.Column("imei", sa.String(32), nullable=True),
        sa.Column("warranty_months", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("purchased_on", sa.Date(), nullable=True),
        _fk("sold_order_id", "orders.id"),
        sa.Column("sold_at", sa.DateTime(timezone=True), nullable=True),
        _created_at(),
        sa.UniqueConstraint("tenant_id", "serial_no", name="uq_electronics_items_tenant_serial"),
        sa.UniqueConstraint("tenant_id", "imei", name="uq_electronics_items_tenant_imei"),
    )
    op.create_index("ix_electronics_items_tenant_id", "electronics_items", ["tenant_id"])
    op.create_index("ix_electronics_items_product_id", "electronics_items", ["product_id"])
    op.create_index("ix_electronics_items_serial_no", "electronics_items", ["serial_no"])
    op.create_index("ix_electronics_items_imei", "electronics_items", ["imei"])
    op.create_index("ix_electronics_items_sold_order_id", "electronics_items", ["sold_order_id"])

    # ── Age-restricted retail ──────────────────────────────────────────
    op.create_table(
        "age_restricted_products",
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        _tenant_fk(),
        sa.Column("min_age_years", sa.Integer(), nullable=False, server_default="18"),
        _created_at(),
    )
    op.create_index("ix_age_restricted_products_tenant_id", "age_restricted_products", ["tenant_id"])

    op.create_table(
        "age_verification_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        _tenant_fk(),
        sa.Column("customer_dob", sa.Date(), nullable=False),
        _fk("order_id", "orders.id"),
        _fk("verified_by_user_id", "users.id"),
        sa.Column("min_age_required", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("verified_age_years", sa.Integer(), nullable=False, server_default="0"),
        _created_at(),
    )
    op.create_index("ix_age_verification_logs_tenant_id", "age_verification_logs", ["tenant_id"])
    op.create_index("ix_age_verification_logs_order_id", "age_verification_logs", ["order_id"])
    op.create_index("ix_age_verification_logs_verified_by_user_id", "age_verification_logs", ["verified_by_user_id"])

    # ── Consignment ────────────────────────────────────────────────────
    op.create_table(
        "consignors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        _tenant_fk(),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(32), nullable=True),
        sa.Column("payout_rate_pct", sa.Numeric(5, 2), nullable=False, server_default="50.0"),
        sa.Column("balance_cents", sa.Integer(), nullable=False, server_default="0"),
        _created_at(),
    )
    op.create_index("ix_consignors_tenant_id", "consignors", ["tenant_id"])

    op.create_table(
        "consignment_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        _tenant_fk(),
        _fk("consignor_id", "consignors.id", nullable=False, ondelete="CASCADE"),
        _fk("product_id", "products.id", nullable=False, ondelete="CASCADE"),
        sa.Column("status", sa.String(16), nullable=False, server_default="listed"),
        sa.Column("listed_price_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("listed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("sold_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sold_price_cents", sa.Integer(), nullable=True),
        sa.Column("consignor_share_cents", sa.Integer(), nullable=True),
        _fk("sold_order_id", "orders.id"),
    )
    op.create_index("ix_consignment_items_tenant_id", "consignment_items", ["tenant_id"])
    op.create_index("ix_consignment_items_consignor_id", "consignment_items", ["consignor_id"])
    op.create_index("ix_consignment_items_product_id", "consignment_items", ["product_id"])
    op.create_index("ix_consignment_items_sold_order_id", "consignment_items", ["sold_order_id"])

    op.create_table(
        "consignor_payouts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        _tenant_fk(),
        _fk("consignor_id", "consignors.id", nullable=False, ondelete="CASCADE"),
        sa.Column("amount_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("balance_after_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("note", sa.String(255), nullable=True),
        _created_at(),
    )
    op.create_index("ix_consignor_payouts_tenant_id", "consignor_payouts", ["tenant_id"])
    op.create_index("ix_consignor_payouts_consignor_id", "consignor_payouts", ["consignor_id"])

    # ── Cannabis ───────────────────────────────────────────────────────
    op.create_table(
        "cannabis_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        _tenant_fk(),
        sa.Column("batch_id", sa.String(64), nullable=False),
        _fk("product_id", "products.id", nullable=False, ondelete="CASCADE"),
        sa.Column("strain_name", sa.String(128), nullable=False),
        sa.Column("harvested_on", sa.Date(), nullable=False),
        sa.Column("expires_on", sa.Date(), nullable=False),
        sa.Column("quantity_grams", sa.Numeric(12, 3), nullable=False),
        sa.Column("thc_pct", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("cbd_pct", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("state", sa.String(16), nullable=False, server_default="received"),
        _created_at(),
        sa.UniqueConstraint("tenant_id", "batch_id", name="uq_cannabis_batch_tag"),
    )
    op.create_index("ix_cannabis_batches_tenant_id", "cannabis_batches", ["tenant_id"])
    op.create_index("ix_cannabis_batches_product_id", "cannabis_batches", ["product_id"])

    op.create_table(
        "cannabis_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        _tenant_fk(),
        _fk("batch_id", "cannabis_batches.id", nullable=False, ondelete="CASCADE"),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("grams_delta", sa.Numeric(12, 3), nullable=False),
        _fk("order_id", "orders.id"),
        _fk("customer_id", "customers.id"),
        sa.Column("reason", sa.String(512), nullable=True),
        _fk("recorded_by_user_id", "users.id"),
        sa.Column("metrc_sync_status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("metrc_sync_error", sa.String(1024), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_cannabis_transactions_tenant_id", "cannabis_transactions", ["tenant_id"])
    op.create_index("ix_cannabis_transactions_batch_id", "cannabis_transactions", ["batch_id"])
    op.create_index("ix_cannabis_transactions_order_id", "cannabis_transactions", ["order_id"])
    op.create_index("ix_cannabis_transactions_customer_id", "cannabis_transactions", ["customer_id"])
    op.create_index("ix_cannabis_transactions_metrc_sync_status", "cannabis_transactions", ["metrc_sync_status"])

    op.create_table(
        "cannabis_purchase_limits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        _tenant_fk(),
        _fk("customer_id", "customers.id", nullable=False, ondelete="CASCADE"),
        sa.Column("day_date", sa.Date(), nullable=False),
        sa.Column("grams_purchased", sa.Numeric(12, 3), nullable=False, server_default="0"),
        sa.UniqueConstraint("tenant_id", "customer_id", "day_date", name="uq_cannabis_daily_limit"),
    )
    op.create_index("ix_cannabis_purchase_limits_tenant_id", "cannabis_purchase_limits", ["tenant_id"])
    op.create_index("ix_cannabis_purchase_limits_customer_id", "cannabis_purchase_limits", ["customer_id"])

    # ── Modifiers ──────────────────────────────────────────────────────
    op.create_table(
        "modifier_groups",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        _tenant_fk(),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("min_selections", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_selections", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.false()),
        _created_at(),
        sa.UniqueConstraint("tenant_id", "code", name="uq_modifier_group_code"),
    )
    op.create_index("ix_modifier_groups_tenant_id", "modifier_groups", ["tenant_id"])

    op.create_table(
        "modifier_options",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        _tenant_fk(),
        _fk("group_id", "modifier_groups.id", nullable=False, ondelete="CASCADE"),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("price_cents_delta", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_modifier_options_tenant_id", "modifier_options", ["tenant_id"])
    op.create_index("ix_modifier_options_group_id", "modifier_options", ["group_id"])

    op.create_table(
        "product_modifier_links",
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "modifier_group_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("modifier_groups.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        _tenant_fk(),
    )
    op.create_index("ix_product_modifier_links_tenant_id", "product_modifier_links", ["tenant_id"])

    # ── Preorders ──────────────────────────────────────────────────────
    op.create_table(
        "preorders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        _tenant_fk(),
        _fk("customer_id", "customers.id"),
        sa.Column("pickup_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        _fk("order_id", "orders.id"),
        sa.Column("notes", sa.String(1024), nullable=True),
        sa.Column("total_cents", sa.Integer(), nullable=False, server_default="0"),
        _created_at(),
    )
    op.create_index("ix_preorders_tenant_id", "preorders", ["tenant_id"])
    op.create_index("ix_preorders_customer_id", "preorders", ["customer_id"])
    op.create_index("ix_preorders_pickup_at", "preorders", ["pickup_at"])
    op.create_index("ix_preorders_order_id", "preorders", ["order_id"])

    op.create_table(
        "preorder_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        _tenant_fk(),
        _fk("preorder_id", "preorders.id", nullable=False, ondelete="CASCADE"),
        _fk("product_id", "products.id", nullable=False, ondelete="RESTRICT"),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("unit_price_cents", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_preorder_items_tenant_id", "preorder_items", ["tenant_id"])
    op.create_index("ix_preorder_items_preorder_id", "preorder_items", ["preorder_id"])

    # ── Bar tabs ───────────────────────────────────────────────────────
    op.create_table(
        "bar_tabs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        _tenant_fk(),
        _fk("customer_id", "customers.id"),
        _fk("opened_by_user_id", "users.id"),
        sa.Column("status", sa.String(16), nullable=False, server_default="open"),
        sa.Column("preauth_reference", sa.String(128), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        _fk("order_id", "orders.id"),
        sa.Column("total_cents", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_bar_tabs_tenant_id", "bar_tabs", ["tenant_id"])
    op.create_index("ix_bar_tabs_customer_id", "bar_tabs", ["customer_id"])
    op.create_index("ix_bar_tabs_order_id", "bar_tabs", ["order_id"])

    op.create_table(
        "bar_tab_lines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        _tenant_fk(),
        _fk("tab_id", "bar_tabs.id", nullable=False, ondelete="CASCADE"),
        _fk("product_id", "products.id", nullable=False, ondelete="RESTRICT"),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("unit_price_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_bar_tab_lines_tenant_id", "bar_tab_lines", ["tenant_id"])
    op.create_index("ix_bar_tab_lines_tab_id", "bar_tab_lines", ["tab_id"])

    # ── Delivery schedules ─────────────────────────────────────────────
    op.create_table(
        "delivery_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        _tenant_fk(),
        _fk("order_id", "orders.id", nullable=False, ondelete="CASCADE"),
        sa.Column("address_line1", sa.String(255), nullable=False),
        sa.Column("address_line2", sa.String(255), nullable=True),
        sa.Column("city", sa.String(128), nullable=False),
        sa.Column("postal_code", sa.String(32), nullable=False),
        sa.Column("country", sa.String(64), nullable=False),
        sa.Column("recipient_name", sa.String(128), nullable=False),
        sa.Column("recipient_phone", sa.String(32), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivery_fee_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(24), nullable=False, server_default="scheduled"),
        sa.Column("notes", sa.String(1024), nullable=True),
        _created_at(),
    )
    op.create_index("ix_delivery_schedules_tenant_id", "delivery_schedules", ["tenant_id"])
    op.create_index("ix_delivery_schedules_order_id", "delivery_schedules", ["order_id"])
    op.create_index("ix_delivery_schedules_scheduled_for", "delivery_schedules", ["scheduled_for"])

    # ── RFID memberships ───────────────────────────────────────────────
    op.create_table(
        "rfid_passes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        _tenant_fk(),
        sa.Column("rfid_tag", sa.String(64), nullable=False),
        _fk("customer_id", "customers.id"),
        sa.Column("plan_code", sa.String(64), nullable=False, server_default=""),
        sa.Column("balance_uses", sa.Integer(), nullable=True),
        sa.Column("expires_on", sa.Date(), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        _created_at(),
        sa.UniqueConstraint("tenant_id", "rfid_tag", name="uq_rfid_pass_tag"),
    )
    op.create_index("ix_rfid_passes_tenant_id", "rfid_passes", ["tenant_id"])
    op.create_index("ix_rfid_passes_customer_id", "rfid_passes", ["customer_id"])

    op.create_table(
        "rfid_pass_uses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        _tenant_fk(),
        _fk("pass_id", "rfid_passes.id", nullable=False, ondelete="CASCADE"),
        sa.Column("location", sa.String(64), nullable=False, server_default=""),
        sa.Column("used_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_rfid_pass_uses_tenant_id", "rfid_pass_uses", ["tenant_id"])
    op.create_index("ix_rfid_pass_uses_pass_id", "rfid_pass_uses", ["pass_id"])

    # ── Gas station ────────────────────────────────────────────────────
    op.create_table(
        "fuel_dispensers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        _tenant_fk(),
        sa.Column("label", sa.String(32), nullable=False),
        sa.Column("fuel_type", sa.String(16), nullable=False),
        sa.Column("price_per_liter_cents", sa.Integer(), nullable=False, server_default="0"),
        _fk("product_id", "products.id"),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.UniqueConstraint("tenant_id", "label", name="uq_fuel_dispenser_label"),
    )
    op.create_index("ix_fuel_dispensers_tenant_id", "fuel_dispensers", ["tenant_id"])

    op.create_table(
        "fuel_dispenser_readings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        _tenant_fk(),
        _fk("dispenser_id", "fuel_dispensers.id", nullable=False, ondelete="CASCADE"),
        sa.Column("totalizer_reading", sa.Numeric(14, 3), nullable=False),
        sa.Column("liters_dispensed", sa.Numeric(14, 3), nullable=False, server_default="0"),
        _fk("order_id", "orders.id"),
        sa.Column("taken_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_fuel_dispenser_readings_tenant_id", "fuel_dispenser_readings", ["tenant_id"])
    op.create_index("ix_fuel_dispenser_readings_dispenser_id", "fuel_dispenser_readings", ["dispenser_id"])

    # ── Laundry ────────────────────────────────────────────────────────
    op.create_table(
        "laundry_tickets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        _tenant_fk(),
        _fk("customer_id", "customers.id"),
        sa.Column("ticket_no", sa.String(32), nullable=False, server_default=""),
        sa.Column("item_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(16), nullable=False, server_default="received"),
        _fk("order_id", "orders.id"),
        sa.Column("dropped_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("promised_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "ticket_no", name="uq_laundry_ticket_no"),
    )
    op.create_index("ix_laundry_tickets_tenant_id", "laundry_tickets", ["tenant_id"])
    op.create_index("ix_laundry_tickets_customer_id", "laundry_tickets", ["customer_id"])

    op.create_table(
        "laundry_ticket_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        _tenant_fk(),
        _fk("ticket_id", "laundry_tickets.id", nullable=False, ondelete="CASCADE"),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("service_type", sa.String(64), nullable=False, server_default=""),
        sa.Column("price_cents", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_laundry_ticket_items_tenant_id", "laundry_ticket_items", ["tenant_id"])
    op.create_index("ix_laundry_ticket_items_ticket_id", "laundry_ticket_items", ["ticket_id"])

    # ── Patient records ────────────────────────────────────────────────
    op.create_table(
        "patients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        _tenant_fk(),
        _fk("customer_id", "customers.id"),
        sa.Column("kind", sa.String(16), nullable=False, server_default="person"),
        sa.Column("first_name", sa.String(80), nullable=True),
        sa.Column("pet_name", sa.String(80), nullable=True),
        sa.Column("dob_or_birth_year", sa.String(16), nullable=True),
        sa.Column("species", sa.String(64), nullable=True),
        sa.Column("breed", sa.String(64), nullable=True),
        sa.Column("allergies", sa.String(2048), nullable=True),
        sa.Column("notes", sa.String(2048), nullable=True),
        _created_at(),
    )
    op.create_index("ix_patients_tenant_id", "patients", ["tenant_id"])
    op.create_index("ix_patients_customer_id", "patients", ["customer_id"])

    op.create_table(
        "patient_visits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        _tenant_fk(),
        _fk("patient_id", "patients.id", nullable=False, ondelete="CASCADE"),
        sa.Column("visit_date", sa.Date(), nullable=False),
        sa.Column("chief_complaint", sa.String(2048), nullable=False),
        _fk("attending_user_id", "users.id"),
        sa.Column("diagnosis", sa.String(2048), nullable=True),
        sa.Column("treatment_notes", sa.String(4096), nullable=True),
        _fk("order_id", "orders.id"),
        sa.Column("follow_up_on", sa.Date(), nullable=True),
        _created_at(),
    )
    op.create_index("ix_patient_visits_tenant_id", "patient_visits", ["tenant_id"])
    op.create_index("ix_patient_visits_patient_id", "patient_visits", ["patient_id"])
    op.create_index("ix_patient_visits_order_id", "patient_visits", ["order_id"])

    op.create_table(
        "patient_prescriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        _tenant_fk(),
        _fk("patient_id", "patients.id", nullable=False, ondelete="CASCADE"),
        sa.Column("medication_name", sa.String(255), nullable=False),
        sa.Column("dosage", sa.String(128), nullable=False),
        sa.Column("frequency", sa.String(128), nullable=False),
        _fk("visit_id", "patient_visits.id"),
        sa.Column("duration_days", sa.Integer(), nullable=False, server_default="0"),
        _fk("prescribed_by_user_id", "users.id"),
        _created_at(),
    )
    op.create_index("ix_patient_prescriptions_tenant_id", "patient_prescriptions", ["tenant_id"])
    op.create_index("ix_patient_prescriptions_patient_id", "patient_prescriptions", ["patient_id"])
    op.create_index("ix_patient_prescriptions_visit_id", "patient_prescriptions", ["visit_id"])

    # ── Tickets ────────────────────────────────────────────────────────
    op.create_table(
        "ticket_event_instances",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        _tenant_fk(),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("venue", sa.String(255), nullable=False, server_default=""),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
    )
    op.create_index("ix_ticket_event_instances_tenant_id", "ticket_event_instances", ["tenant_id"])

    op.create_table(
        "ticket_types",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        _tenant_fk(),
        _fk("event_id", "ticket_event_instances.id", nullable=False, ondelete="CASCADE"),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("price_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("quota", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sold_count", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("event_id", "code", name="uq_ticket_type_event_code"),
    )
    op.create_index("ix_ticket_types_tenant_id", "ticket_types", ["tenant_id"])
    op.create_index("ix_ticket_types_event_id", "ticket_types", ["event_id"])

    op.create_table(
        "ticket_issued",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        _tenant_fk(),
        _fk("ticket_type_id", "ticket_types.id", nullable=False, ondelete="CASCADE"),
        _fk("order_id", "orders.id"),
        sa.Column("holder_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("serial_no", sa.String(64), nullable=False, server_default=""),
        sa.Column("status", sa.String(16), nullable=False, server_default="issued"),
        sa.Column("scanned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "serial_no", name="uq_issued_ticket_serial"),
    )
    op.create_index("ix_ticket_issued_tenant_id", "ticket_issued", ["tenant_id"])
    op.create_index("ix_ticket_issued_ticket_type_id", "ticket_issued", ["ticket_type_id"])

    # ── Donations ──────────────────────────────────────────────────────
    op.create_table(
        "donation_campaigns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        _tenant_fk(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("goal_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("starts_on", sa.Date(), nullable=True),
        sa.Column("ends_on", sa.Date(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("tenant_id", "code", name="uq_donation_campaign_code"),
    )
    op.create_index("ix_donation_campaigns_tenant_id", "donation_campaigns", ["tenant_id"])

    op.create_table(
        "donations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        _tenant_fk(),
        _fk("customer_id", "customers.id"),
        sa.Column("amount_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="BDT"),
        sa.Column("campaign", sa.String(64), nullable=True),
        sa.Column("donor_name_override", sa.String(255), nullable=True),
        sa.Column("is_anonymous", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("tax_deductible", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("receipt_no", sa.String(32), nullable=False, server_default=""),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "receipt_no", name="uq_donation_receipt_no"),
    )
    op.create_index("ix_donations_tenant_id", "donations", ["tenant_id"])
    op.create_index("ix_donations_customer_id", "donations", ["customer_id"])
    op.create_index("ix_donations_campaign", "donations", ["campaign"])

    # ── Wholesale ──────────────────────────────────────────────────────
    op.create_table(
        "wholesale_tiers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        _tenant_fk(),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("discount_pct", sa.Numeric(5, 2), nullable=False, server_default="0"),
        _created_at(),
        sa.UniqueConstraint("tenant_id", "code", name="uq_wholesale_tier_code"),
    )
    op.create_index("ix_wholesale_tiers_tenant_id", "wholesale_tiers", ["tenant_id"])

    op.create_table(
        "wholesale_customers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        _tenant_fk(),
        _fk("customer_id", "customers.id", nullable=False, ondelete="CASCADE"),
        sa.Column("tier_code", sa.String(32), nullable=True),
        sa.Column("credit_limit_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("credit_balance_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("net_terms_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("tax_exempt", sa.Boolean(), nullable=False, server_default=sa.false()),
        _created_at(),
        sa.UniqueConstraint("tenant_id", "customer_id", name="uq_wholesale_customer_ref"),
    )
    op.create_index("ix_wholesale_customers_tenant_id", "wholesale_customers", ["tenant_id"])
    op.create_index("ix_wholesale_customers_customer_id", "wholesale_customers", ["customer_id"])

    op.create_table(
        "wholesale_invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        _tenant_fk(),
        _fk("wholesale_customer_id", "wholesale_customers.id", nullable=False, ondelete="RESTRICT"),
        _fk("order_id", "orders.id", nullable=False, ondelete="RESTRICT"),
        sa.Column("invoice_no", sa.String(64), nullable=False),
        sa.Column("issued_on", sa.Date(), nullable=False),
        sa.Column("due_on", sa.Date(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="open"),
        sa.Column("amount_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("paid_cents", sa.Integer(), nullable=False, server_default="0"),
        _created_at(),
        sa.UniqueConstraint("tenant_id", "invoice_no", name="uq_wholesale_invoice_no"),
    )
    op.create_index("ix_wholesale_invoices_tenant_id", "wholesale_invoices", ["tenant_id"])
    op.create_index("ix_wholesale_invoices_wholesale_customer_id", "wholesale_invoices", ["wholesale_customer_id"])
    op.create_index("ix_wholesale_invoices_order_id", "wholesale_invoices", ["order_id"])

    op.create_table(
        "wholesale_invoice_payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        _tenant_fk(),
        _fk("invoice_id", "wholesale_invoices.id", nullable=False, ondelete="CASCADE"),
        sa.Column("paid_on", sa.Date(), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reference", sa.String(128), nullable=True),
        _created_at(),
    )
    op.create_index("ix_wholesale_invoice_payments_tenant_id", "wholesale_invoice_payments", ["tenant_id"])
    op.create_index("ix_wholesale_invoice_payments_invoice_id", "wholesale_invoice_payments", ["invoice_id"])


def downgrade() -> None:
    # Reverse order of creation — children before parents.
    for tbl in (
        "wholesale_invoice_payments",
        "wholesale_invoices",
        "wholesale_customers",
        "wholesale_tiers",
        "donations",
        "donation_campaigns",
        "ticket_issued",
        "ticket_types",
        "ticket_event_instances",
        "patient_prescriptions",
        "patient_visits",
        "patients",
        "laundry_ticket_items",
        "laundry_tickets",
        "fuel_dispenser_readings",
        "fuel_dispensers",
        "rfid_pass_uses",
        "rfid_passes",
        "delivery_schedules",
        "bar_tab_lines",
        "bar_tabs",
        "preorder_items",
        "preorders",
        "product_modifier_links",
        "modifier_options",
        "modifier_groups",
        "cannabis_purchase_limits",
        "cannabis_transactions",
        "cannabis_batches",
        "consignor_payouts",
        "consignment_items",
        "consignors",
        "age_verification_logs",
        "age_restricted_products",
        "electronics_items",
    ):
        op.drop_table(tbl)

    op.drop_column("tenants", "vertical_profile")
