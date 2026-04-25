"""Vertical depth pass — real-world operator features across all 11 verticals.

Adds the schema needed for:
  - Restaurant: KOT course, product_station_routes
  - Apparel: gender/fit/material + stock_quantity on variants
  - Pharmacy: drug metadata (controlled flag), prescriptions
  - Jewelry: metal/making/wastage/stone_value, daily metal rates
  - Salon: service catalog, service_id + order_id on appointment
  - Gym: plans catalog, classes, class bookings
  - Garage: job card lines (parts + labor)
  - Hotel: checked_in_at/checked_out_at, folio charges
  - Cinema: seat held_by/held_until/order_id
  - Rental: late_fee_cents, damage_fee_cents, damage_notes

Revision ID: 20260426_0008
Revises: 20260425_0007
Create Date: 2026-04-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260426_0008"
down_revision: str | Sequence[str] | None = "20260425_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── Restaurant ─────────────────────────────────────────────────────────
    op.add_column(
        "kot_tickets", sa.Column("course", sa.Integer(), nullable=False, server_default="1")
    )
    op.alter_column("kot_tickets", "course", server_default=None)

    op.create_table(
        "product_station_routes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("station", sa.String(16), nullable=False),
        sa.Column("course", sa.Integer(), nullable=False, server_default="1"),
        sa.UniqueConstraint("tenant_id", "product_id", name="uq_product_station_route"),
    )
    op.create_index("ix_product_station_routes_tenant_id", "product_station_routes", ["tenant_id"])
    op.create_index("ix_product_station_routes_product_id", "product_station_routes", ["product_id"])

    # ── Apparel ─────────────────────────────────────────────────────────────
    op.add_column("apparel_variants", sa.Column("gender", sa.String(8), nullable=True))
    op.add_column("apparel_variants", sa.Column("fit", sa.String(32), nullable=True))
    op.add_column("apparel_variants", sa.Column("material", sa.String(64), nullable=True))
    op.add_column("apparel_variants", sa.Column("stock_quantity", sa.Integer(), nullable=False, server_default="0"))
    op.alter_column("apparel_variants", "stock_quantity", server_default=None)

    # ── Pharmacy ────────────────────────────────────────────────────────────
    op.create_table(
        "pharmacy_drug_metadata",
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_controlled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("schedule", sa.String(16), nullable=True),
        sa.Column("dosage_form", sa.String(32), nullable=True),
        sa.Column("strength", sa.String(32), nullable=True),
    )
    op.create_index("ix_pharmacy_drug_metadata_tenant_id", "pharmacy_drug_metadata", ["tenant_id"])

    op.create_table(
        "pharmacy_prescriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orders.id", ondelete="SET NULL"), nullable=True),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("prescription_no", sa.String(64), nullable=False),
        sa.Column("doctor_name", sa.String(255), nullable=False),
        sa.Column("doctor_license", sa.String(64), nullable=True),
        sa.Column("issued_on", sa.Date(), nullable=False),
        sa.Column("notes", sa.String(2048), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_pharmacy_prescriptions_tenant_id", "pharmacy_prescriptions", ["tenant_id"])
    op.create_index("ix_pharmacy_prescriptions_order_id", "pharmacy_prescriptions", ["order_id"])
    op.create_index("ix_pharmacy_prescriptions_customer_id", "pharmacy_prescriptions", ["customer_id"])

    # ── Jewelry ─────────────────────────────────────────────────────────────
    op.add_column("jewelry_attributes", sa.Column("metal", sa.String(16), nullable=False, server_default="gold"))
    op.add_column("jewelry_attributes", sa.Column("making_charge_pct", sa.Numeric(5, 2), nullable=False, server_default="0"))
    op.add_column("jewelry_attributes", sa.Column("making_charge_per_gram_cents", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("jewelry_attributes", sa.Column("wastage_pct", sa.Numeric(5, 2), nullable=False, server_default="0"))
    op.add_column("jewelry_attributes", sa.Column("stone_value_cents", sa.Integer(), nullable=False, server_default="0"))
    for col in ("metal", "making_charge_pct", "making_charge_per_gram_cents", "wastage_pct", "stone_value_cents"):
        op.alter_column("jewelry_attributes", col, server_default=None)

    op.create_table(
        "jewelry_metal_rates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("metal", sa.String(16), nullable=False),
        sa.Column("karat", sa.Integer(), nullable=False, server_default="22"),
        sa.Column("rate_per_gram_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("effective_on", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "metal", "karat", "effective_on", name="uq_metal_rate_day"),
    )
    op.create_index("ix_jewelry_metal_rates_tenant_id", "jewelry_metal_rates", ["tenant_id"])

    # ── Salon ───────────────────────────────────────────────────────────────
    op.create_table(
        "salon_services",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("price_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="SET NULL"), nullable=True),
        sa.UniqueConstraint("tenant_id", "code", name="uq_salon_service_code"),
    )
    op.create_index("ix_salon_services_tenant_id", "salon_services", ["tenant_id"])

    op.add_column(
        "salon_appointments",
        sa.Column(
            "service_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("salon_services.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "salon_appointments",
        sa.Column(
            "order_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("orders.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_salon_appointments_order_id", "salon_appointments", ["order_id"])

    # ── Gym ─────────────────────────────────────────────────────────────────
    op.create_table(
        "gym_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("price_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("tenant_id", "code", name="uq_gym_plan_code"),
    )
    op.create_index("ix_gym_plans_tenant_id", "gym_plans", ["tenant_id"])

    op.create_table(
        "gym_classes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(128), nullable=False),
        sa.Column("trainer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="20"),
    )
    op.create_index("ix_gym_classes_tenant_id", "gym_classes", ["tenant_id"])

    op.create_table(
        "gym_class_bookings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("gym_classes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("membership_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("gym_memberships.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("class_id", "membership_id", name="uq_gym_class_booking_member"),
    )
    op.create_index("ix_gym_class_bookings_tenant_id", "gym_class_bookings", ["tenant_id"])
    op.create_index("ix_gym_class_bookings_class_id", "gym_class_bookings", ["class_id"])
    op.create_index("ix_gym_class_bookings_membership_id", "gym_class_bookings", ["membership_id"])

    # ── Garage ──────────────────────────────────────────────────────────────
    op.create_table(
        "job_card_lines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_card_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("job_cards.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="SET NULL"), nullable=True),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("unit_cost_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("line_total_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_job_card_lines_tenant_id", "job_card_lines", ["tenant_id"])
    op.create_index("ix_job_card_lines_job_card_id", "job_card_lines", ["job_card_id"])

    # ── Hotel ───────────────────────────────────────────────────────────────
    op.add_column(
        "hotel_reservations",
        sa.Column("checked_in_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "hotel_reservations",
        sa.Column("checked_out_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "hotel_folio_charges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reservation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("hotel_reservations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("posted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_hotel_folio_charges_tenant_id", "hotel_folio_charges", ["tenant_id"])
    op.create_index("ix_hotel_folio_charges_reservation_id", "hotel_folio_charges", ["reservation_id"])

    # ── Cinema ──────────────────────────────────────────────────────────────
    op.add_column("cinema_seats", sa.Column("held_by", sa.String(64), nullable=True))
    op.add_column(
        "cinema_seats",
        sa.Column("held_until", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "cinema_seats",
        sa.Column(
            "order_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("orders.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # ── Rental ──────────────────────────────────────────────────────────────
    op.add_column("rental_contracts", sa.Column("late_fee_cents", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("rental_contracts", sa.Column("damage_fee_cents", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("rental_contracts", sa.Column("damage_notes", sa.String(2048), nullable=True))
    op.alter_column("rental_contracts", "late_fee_cents", server_default=None)
    op.alter_column("rental_contracts", "damage_fee_cents", server_default=None)


def downgrade() -> None:
    # Rental
    op.drop_column("rental_contracts", "damage_notes")
    op.drop_column("rental_contracts", "damage_fee_cents")
    op.drop_column("rental_contracts", "late_fee_cents")

    # Cinema
    op.drop_column("cinema_seats", "order_id")
    op.drop_column("cinema_seats", "held_until")
    op.drop_column("cinema_seats", "held_by")

    # Hotel
    op.drop_index("ix_hotel_folio_charges_reservation_id", table_name="hotel_folio_charges")
    op.drop_index("ix_hotel_folio_charges_tenant_id", table_name="hotel_folio_charges")
    op.drop_table("hotel_folio_charges")
    op.drop_column("hotel_reservations", "checked_out_at")
    op.drop_column("hotel_reservations", "checked_in_at")

    # Garage
    op.drop_index("ix_job_card_lines_job_card_id", table_name="job_card_lines")
    op.drop_index("ix_job_card_lines_tenant_id", table_name="job_card_lines")
    op.drop_table("job_card_lines")

    # Gym
    op.drop_index("ix_gym_class_bookings_membership_id", table_name="gym_class_bookings")
    op.drop_index("ix_gym_class_bookings_class_id", table_name="gym_class_bookings")
    op.drop_index("ix_gym_class_bookings_tenant_id", table_name="gym_class_bookings")
    op.drop_table("gym_class_bookings")
    op.drop_index("ix_gym_classes_tenant_id", table_name="gym_classes")
    op.drop_table("gym_classes")
    op.drop_index("ix_gym_plans_tenant_id", table_name="gym_plans")
    op.drop_table("gym_plans")

    # Salon
    op.drop_index("ix_salon_appointments_order_id", table_name="salon_appointments")
    op.drop_column("salon_appointments", "order_id")
    op.drop_column("salon_appointments", "service_id")
    op.drop_index("ix_salon_services_tenant_id", table_name="salon_services")
    op.drop_table("salon_services")

    # Jewelry
    op.drop_index("ix_jewelry_metal_rates_tenant_id", table_name="jewelry_metal_rates")
    op.drop_table("jewelry_metal_rates")
    for col in ("stone_value_cents", "wastage_pct", "making_charge_per_gram_cents", "making_charge_pct", "metal"):
        op.drop_column("jewelry_attributes", col)

    # Pharmacy
    op.drop_index("ix_pharmacy_prescriptions_customer_id", table_name="pharmacy_prescriptions")
    op.drop_index("ix_pharmacy_prescriptions_order_id", table_name="pharmacy_prescriptions")
    op.drop_index("ix_pharmacy_prescriptions_tenant_id", table_name="pharmacy_prescriptions")
    op.drop_table("pharmacy_prescriptions")
    op.drop_index("ix_pharmacy_drug_metadata_tenant_id", table_name="pharmacy_drug_metadata")
    op.drop_table("pharmacy_drug_metadata")

    # Apparel
    op.drop_column("apparel_variants", "stock_quantity")
    op.drop_column("apparel_variants", "material")
    op.drop_column("apparel_variants", "fit")
    op.drop_column("apparel_variants", "gender")

    # Restaurant
    op.drop_index("ix_product_station_routes_product_id", table_name="product_station_routes")
    op.drop_index("ix_product_station_routes_tenant_id", table_name="product_station_routes")
    op.drop_table("product_station_routes")
    op.drop_column("kot_tickets", "course")
