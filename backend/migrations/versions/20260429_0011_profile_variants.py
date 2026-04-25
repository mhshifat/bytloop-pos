"""Profile-only variants → dedicated modules (the last 15).

Adds 28 new tables covering Furniture custom orders, Florist bouquet
builder, Pet-store metadata, Hardware quantity breaks, Retail departments,
Cafe loyalty punch cards, QSR drive-thru queue, Cloud-kitchen virtual
brands, Cafeteria meal plans, Food-truck locations + daily menus, Resort
packages, Pop-up events + stalls, Self-checkout sessions + scans, and
SoftPOS readers + tap events. Bookstore ships as a lookup-only module
with no new tables.

Revision ID: 20260429_0011
Revises: 20260428_0010
Create Date: 2026-04-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260429_0011"
down_revision: str | Sequence[str] | None = "20260428_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# ──────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────


def _uuid_pk():
    return sa.Column(
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
    # ── Furniture custom orders ────────────────────────────────────────
    op.create_table(
        "furniture_custom_orders",
        _uuid_pk(),
        _tenant_fk(),
        _fk("product_id", "products.id", nullable=False, ondelete="RESTRICT"),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("quoted_price_cents", sa.Integer(), nullable=False, server_default="0"),
        _fk("customer_id", "customers.id"),
        sa.Column("dimensions_cm", sa.String(64), nullable=True),
        sa.Column("material", sa.String(128), nullable=True),
        sa.Column("finish", sa.String(128), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="quoted"),
        sa.Column("estimated_ready_on", sa.Date(), nullable=True),
        _fk("order_id", "orders.id"),
        _created_at(),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_furniture_custom_orders_tenant_id", "furniture_custom_orders", ["tenant_id"])
    op.create_index("ix_furniture_custom_orders_product_id", "furniture_custom_orders", ["product_id"])
    op.create_index("ix_furniture_custom_orders_customer_id", "furniture_custom_orders", ["customer_id"])
    op.create_index("ix_furniture_custom_orders_status", "furniture_custom_orders", ["status"])
    op.create_index("ix_furniture_custom_orders_order_id", "furniture_custom_orders", ["order_id"])

    # ── Florist ────────────────────────────────────────────────────────
    op.create_table(
        "bouquet_templates",
        _uuid_pk(),
        _tenant_fk(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("base_price_cents", sa.Integer(), nullable=False, server_default="0"),
        _created_at(),
        sa.UniqueConstraint("tenant_id", "code", name="uq_bouquet_templates_tenant_code"),
    )
    op.create_index("ix_bouquet_templates_tenant_id", "bouquet_templates", ["tenant_id"])

    op.create_table(
        "bouquet_components",
        _uuid_pk(),
        _tenant_fk(),
        _fk("template_id", "bouquet_templates.id", nullable=False, ondelete="CASCADE"),
        sa.Column("component_name", sa.String(128), nullable=False),
        sa.Column("default_quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("unit_price_cents", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_bouquet_components_tenant_id", "bouquet_components", ["tenant_id"])
    op.create_index("ix_bouquet_components_template_id", "bouquet_components", ["template_id"])

    op.create_table(
        "bouquet_instances",
        _uuid_pk(),
        _tenant_fk(),
        sa.Column("total_price_cents", sa.Integer(), nullable=False, server_default="0"),
        _fk("template_id", "bouquet_templates.id"),
        _fk("order_id", "orders.id"),
        sa.Column("wrap_style", sa.String(64), nullable=True),
        sa.Column("card_message", sa.Text(), nullable=True),
        _fk("delivery_schedule_id", "delivery_schedules.id"),
        _created_at(),
    )
    op.create_index("ix_bouquet_instances_tenant_id", "bouquet_instances", ["tenant_id"])
    op.create_index("ix_bouquet_instances_template_id", "bouquet_instances", ["template_id"])
    op.create_index("ix_bouquet_instances_order_id", "bouquet_instances", ["order_id"])
    op.create_index("ix_bouquet_instances_delivery_schedule_id", "bouquet_instances", ["delivery_schedule_id"])

    op.create_table(
        "bouquet_instance_items",
        _uuid_pk(),
        _tenant_fk(),
        _fk("instance_id", "bouquet_instances.id", nullable=False, ondelete="CASCADE"),
        sa.Column("component_name", sa.String(128), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("unit_price_cents", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_bouquet_instance_items_tenant_id", "bouquet_instance_items", ["tenant_id"])
    op.create_index("ix_bouquet_instance_items_instance_id", "bouquet_instance_items", ["instance_id"])

    # ── Pet store metadata ─────────────────────────────────────────────
    op.create_table(
        "pet_product_metadata",
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        _tenant_fk(),
        sa.Column("target_species", sa.String(32), nullable=True),
        sa.Column("target_breed", sa.String(128), nullable=True),
        sa.Column("life_stage", sa.String(32), nullable=True),
        sa.Column("weight_range_lbs", sa.String(32), nullable=True),
        sa.Column("is_prescription_food", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_pet_product_metadata_tenant_id", "pet_product_metadata", ["tenant_id"])
    op.create_index("ix_pet_product_metadata_target_species", "pet_product_metadata", ["target_species"])
    op.create_index("ix_pet_product_metadata_is_prescription_food", "pet_product_metadata", ["is_prescription_food"])

    # ── Hardware quantity breaks ───────────────────────────────────────
    op.create_table(
        "quantity_breaks",
        _uuid_pk(),
        _tenant_fk(),
        _fk("product_id", "products.id", nullable=False, ondelete="CASCADE"),
        sa.Column("min_quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price_cents", sa.Integer(), nullable=False),
        _created_at(),
        sa.UniqueConstraint(
            "tenant_id", "product_id", "min_quantity",
            name="uq_quantity_breaks_tenant_product_min",
        ),
    )
    op.create_index("ix_quantity_breaks_tenant_id", "quantity_breaks", ["tenant_id"])
    op.create_index("ix_quantity_breaks_product_id", "quantity_breaks", ["product_id"])

    # ── Retail departments ─────────────────────────────────────────────
    op.create_table(
        "departments",
        _uuid_pk(),
        _tenant_fk(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        _fk("parent_id", "departments.id"),
        _created_at(),
        sa.UniqueConstraint("tenant_id", "code", name="uq_departments_tenant_code"),
    )
    op.create_index("ix_departments_tenant_id", "departments", ["tenant_id"])
    op.create_index("ix_departments_parent_id", "departments", ["parent_id"])

    op.create_table(
        "product_departments",
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        _tenant_fk(),
        _fk("department_id", "departments.id", nullable=False, ondelete="CASCADE"),
        _created_at(),
    )
    op.create_index("ix_product_departments_tenant_id", "product_departments", ["tenant_id"])
    op.create_index("ix_product_departments_department_id", "product_departments", ["department_id"])

    # ── Cafe loyalty ───────────────────────────────────────────────────
    op.create_table(
        "cafe_loyalty_cards",
        _uuid_pk(),
        _tenant_fk(),
        _fk("customer_id", "customers.id", nullable=False, ondelete="CASCADE"),
        sa.Column("card_code", sa.String(64), nullable=False),
        sa.Column("punches_current", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("punches_required", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("free_items_earned", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_punches_lifetime", sa.Integer(), nullable=False, server_default="0"),
        _created_at(),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "card_code", name="uq_cafe_loyalty_tenant_card_code"),
    )
    op.create_index("ix_cafe_loyalty_cards_tenant_id", "cafe_loyalty_cards", ["tenant_id"])
    op.create_index("ix_cafe_loyalty_cards_customer_id", "cafe_loyalty_cards", ["customer_id"])
    op.create_index("ix_cafe_loyalty_cards_card_code", "cafe_loyalty_cards", ["card_code"])

    # ── QSR drive-thru ─────────────────────────────────────────────────
    op.create_table(
        "drive_thru_tickets",
        _uuid_pk(),
        _tenant_fk(),
        _fk("order_id", "orders.id", nullable=False, ondelete="CASCADE"),
        sa.Column("call_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="ordering"),
        sa.Column("lane", sa.String(32), nullable=True),
        sa.Column("estimated_ready_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("called_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("served_at", sa.DateTime(timezone=True), nullable=True),
        _created_at(),
    )
    op.create_index("ix_drive_thru_tickets_tenant_id", "drive_thru_tickets", ["tenant_id"])
    op.create_index("ix_drive_thru_tickets_order_id", "drive_thru_tickets", ["order_id"])

    # ── Cloud kitchen ──────────────────────────────────────────────────
    op.create_table(
        "virtual_brands",
        _uuid_pk(),
        _tenant_fk(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("logo_url", sa.String(512), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        _created_at(),
        sa.UniqueConstraint("tenant_id", "code", name="uq_virtual_brands_tenant_code"),
    )
    op.create_index("ix_virtual_brands_tenant_id", "virtual_brands", ["tenant_id"])

    op.create_table(
        "brand_products",
        _tenant_fk(),
        sa.Column(
            "brand_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("virtual_brands.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        _created_at(),
    )
    op.create_index("ix_brand_products_tenant_id", "brand_products", ["tenant_id"])

    op.create_table(
        "brand_orders",
        _uuid_pk(),
        _tenant_fk(),
        _fk("order_id", "orders.id", nullable=False, ondelete="CASCADE"),
        _fk("brand_id", "virtual_brands.id", nullable=False, ondelete="RESTRICT"),
        sa.Column("external_order_ref", sa.String(128), nullable=True),
        _created_at(),
        sa.UniqueConstraint("tenant_id", "order_id", name="uq_brand_orders_tenant_order"),
    )
    op.create_index("ix_brand_orders_tenant_id", "brand_orders", ["tenant_id"])
    op.create_index("ix_brand_orders_order_id", "brand_orders", ["order_id"])
    op.create_index("ix_brand_orders_brand_id", "brand_orders", ["brand_id"])

    # ── Cafeteria meal plans ───────────────────────────────────────────
    op.create_table(
        "meal_plans",
        _uuid_pk(),
        _tenant_fk(),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("meals_per_period", sa.Integer(), nullable=False),
        sa.Column("period_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("price_cents", sa.Integer(), nullable=False, server_default="0"),
        _created_at(),
        sa.UniqueConstraint("tenant_id", "code", name="uq_meal_plans_tenant_code"),
    )
    op.create_index("ix_meal_plans_tenant_id", "meal_plans", ["tenant_id"])

    op.create_table(
        "meal_plan_subscriptions",
        _uuid_pk(),
        _tenant_fk(),
        _fk("customer_id", "customers.id", nullable=False, ondelete="CASCADE"),
        sa.Column("plan_code", sa.String(32), nullable=False),
        sa.Column("meals_remaining", sa.Integer(), nullable=False),
        sa.Column("period_ends_on", sa.Date(), nullable=False),
        sa.Column("auto_renew", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        _created_at(),
    )
    op.create_index("ix_meal_plan_subscriptions_tenant_id", "meal_plan_subscriptions", ["tenant_id"])
    op.create_index("ix_meal_plan_subscriptions_customer_id", "meal_plan_subscriptions", ["customer_id"])

    op.create_table(
        "meal_redemptions",
        _uuid_pk(),
        _tenant_fk(),
        _fk("subscription_id", "meal_plan_subscriptions.id", nullable=False, ondelete="CASCADE"),
        _fk("order_id", "orders.id"),
        sa.Column("meals_used", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("redeemed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_meal_redemptions_tenant_id", "meal_redemptions", ["tenant_id"])
    op.create_index("ix_meal_redemptions_subscription_id", "meal_redemptions", ["subscription_id"])
    op.create_index("ix_meal_redemptions_order_id", "meal_redemptions", ["order_id"])

    # ── Food truck ─────────────────────────────────────────────────────
    op.create_table(
        "truck_locations",
        _uuid_pk(),
        _tenant_fk(),
        sa.Column("location_name", sa.String(128), nullable=False),
        sa.Column("latitude", sa.Numeric(10, 7), nullable=False),
        sa.Column("longitude", sa.Numeric(10, 7), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.String(1024), nullable=True),
        _created_at(),
    )
    op.create_index("ix_truck_locations_tenant_id", "truck_locations", ["tenant_id"])
    op.create_index("ix_truck_locations_starts_at", "truck_locations", ["starts_at"])
    op.create_index("ix_truck_locations_ends_at", "truck_locations", ["ends_at"])

    op.create_table(
        "daily_menu",
        _uuid_pk(),
        _tenant_fk(),
        sa.Column("menu_date", sa.Date(), nullable=False),
        sa.Column("notes", sa.String(1024), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "menu_date", name="uq_daily_menu_tenant_date"),
    )
    op.create_index("ix_daily_menu_tenant_id", "daily_menu", ["tenant_id"])
    op.create_index("ix_daily_menu_menu_date", "daily_menu", ["menu_date"])

    op.create_table(
        "daily_menu_items",
        _uuid_pk(),
        _tenant_fk(),
        _fk("menu_id", "daily_menu.id", nullable=False, ondelete="CASCADE"),
        _fk("product_id", "products.id", nullable=False, ondelete="CASCADE"),
        sa.Column("daily_price_cents_override", sa.Integer(), nullable=True),
        sa.Column("sold_out", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("menu_id", "product_id", name="uq_daily_menu_items_menu_product"),
    )
    op.create_index("ix_daily_menu_items_tenant_id", "daily_menu_items", ["tenant_id"])
    op.create_index("ix_daily_menu_items_menu_id", "daily_menu_items", ["menu_id"])

    # ── Resort ─────────────────────────────────────────────────────────
    op.create_table(
        "resort_packages",
        _uuid_pk(),
        _tenant_fk(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("per_night_price_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("includes_meals", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("includes_drinks", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("includes_spa", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("includes_activities", sa.Boolean(), nullable=False, server_default=sa.false()),
        _created_at(),
        sa.UniqueConstraint("tenant_id", "code", name="uq_resort_packages_tenant_code"),
    )
    op.create_index("ix_resort_packages_tenant_id", "resort_packages", ["tenant_id"])

    op.create_table(
        "resort_package_bookings",
        _uuid_pk(),
        _tenant_fk(),
        _fk("reservation_id", "hotel_reservations.id", nullable=False, ondelete="CASCADE"),
        sa.Column("package_code", sa.String(64), nullable=False),
        sa.Column("nights", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("total_package_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("attached_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_resort_package_bookings_tenant_id", "resort_package_bookings", ["tenant_id"])
    op.create_index("ix_resort_package_bookings_reservation_id", "resort_package_bookings", ["reservation_id"])

    # ── Pop-up events ──────────────────────────────────────────────────
    op.create_table(
        "popup_events",
        _uuid_pk(),
        _tenant_fk(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("venue", sa.String(255), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("location_notes", sa.String(1024), nullable=True),
        sa.UniqueConstraint("tenant_id", "code", name="uq_popup_events_tenant_code"),
    )
    op.create_index("ix_popup_events_tenant_id", "popup_events", ["tenant_id"])

    op.create_table(
        "popup_stalls",
        _uuid_pk(),
        _tenant_fk(),
        _fk("event_id", "popup_events.id", nullable=False, ondelete="CASCADE"),
        sa.Column("stall_label", sa.String(64), nullable=False),
        _fk("operator_user_id", "users.id"),
    )
    op.create_index("ix_popup_stalls_tenant_id", "popup_stalls", ["tenant_id"])
    op.create_index("ix_popup_stalls_event_id", "popup_stalls", ["event_id"])
    op.create_index("ix_popup_stalls_operator_user_id", "popup_stalls", ["operator_user_id"])

    op.create_table(
        "popup_inventory_snapshots",
        _uuid_pk(),
        _tenant_fk(),
        _fk("event_id", "popup_events.id", nullable=False, ondelete="CASCADE"),
        _fk("product_id", "products.id", nullable=False, ondelete="CASCADE"),
        sa.Column("opening_stock", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("closing_stock", sa.Integer(), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("event_id", "product_id", name="uq_popup_snapshot_event_product"),
    )
    op.create_index("ix_popup_inventory_snapshots_tenant_id", "popup_inventory_snapshots", ["tenant_id"])
    op.create_index("ix_popup_inventory_snapshots_event_id", "popup_inventory_snapshots", ["event_id"])
    op.create_index("ix_popup_inventory_snapshots_product_id", "popup_inventory_snapshots", ["product_id"])

    # ── Self-checkout ──────────────────────────────────────────────────
    op.create_table(
        "self_checkout_sessions",
        _uuid_pk(),
        _tenant_fk(),
        sa.Column("station_label", sa.String(64), nullable=False),
        sa.Column("customer_identifier", sa.String(128), nullable=True),
        sa.Column("status", sa.String(24), nullable=False, server_default="scanning"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        _fk("order_id", "orders.id"),
    )
    op.create_index("ix_self_checkout_sessions_tenant_id", "self_checkout_sessions", ["tenant_id"])
    op.create_index("ix_self_checkout_sessions_order_id", "self_checkout_sessions", ["order_id"])

    op.create_table(
        "self_checkout_scans",
        _uuid_pk(),
        _tenant_fk(),
        _fk("session_id", "self_checkout_sessions.id", nullable=False, ondelete="CASCADE"),
        sa.Column("barcode", sa.String(64), nullable=False),
        _fk("product_id", "products.id"),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("unit_price_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("scanned_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("flagged_for_staff", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("flag_reason", sa.String(64), nullable=True),
    )
    op.create_index("ix_self_checkout_scans_tenant_id", "self_checkout_scans", ["tenant_id"])
    op.create_index("ix_self_checkout_scans_session_id", "self_checkout_scans", ["session_id"])
    op.create_index("ix_self_checkout_scans_product_id", "self_checkout_scans", ["product_id"])

    # ── SoftPOS ────────────────────────────────────────────────────────
    op.create_table(
        "softpos_readers",
        _uuid_pk(),
        _tenant_fk(),
        sa.Column("device_label", sa.String(128), nullable=False),
        sa.Column("device_fingerprint", sa.String(128), nullable=False),
        sa.Column("is_certified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("certified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        _created_at(),
        sa.UniqueConstraint(
            "tenant_id", "device_fingerprint",
            name="uq_softpos_readers_tenant_fingerprint",
        ),
    )
    op.create_index("ix_softpos_readers_tenant_id", "softpos_readers", ["tenant_id"])

    op.create_table(
        "softpos_tap_events",
        _uuid_pk(),
        _tenant_fk(),
        _fk("reader_id", "softpos_readers.id", nullable=False, ondelete="CASCADE"),
        sa.Column("card_bin", sa.String(6), nullable=False),
        sa.Column("outcome", sa.String(16), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("provider_reference", sa.String(128), nullable=True),
        sa.Column("tapped_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_softpos_tap_events_tenant_id", "softpos_tap_events", ["tenant_id"])
    op.create_index("ix_softpos_tap_events_reader_id", "softpos_tap_events", ["reader_id"])


def downgrade() -> None:
    # Children before parents.
    for tbl in (
        "softpos_tap_events",
        "softpos_readers",
        "self_checkout_scans",
        "self_checkout_sessions",
        "popup_inventory_snapshots",
        "popup_stalls",
        "popup_events",
        "resort_package_bookings",
        "resort_packages",
        "daily_menu_items",
        "daily_menu",
        "truck_locations",
        "meal_redemptions",
        "meal_plan_subscriptions",
        "meal_plans",
        "brand_orders",
        "brand_products",
        "virtual_brands",
        "drive_thru_tickets",
        "cafe_loyalty_cards",
        "product_departments",
        "departments",
        "quantity_breaks",
        "pet_product_metadata",
        "bouquet_instance_items",
        "bouquet_instances",
        "bouquet_components",
        "bouquet_templates",
        "furniture_custom_orders",
    ):
        op.drop_table(tbl)
