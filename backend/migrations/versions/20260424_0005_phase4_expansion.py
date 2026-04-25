"""Phase 4 — expansion vertical scaffolds.

Revision ID: 20260424_0005
Revises: 20260424_0004
Create Date: 2026-04-24
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260424_0005"
down_revision: str | Sequence[str] | None = "20260424_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _uuid_pk() -> sa.Column:
    return sa.Column(
        "id",
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )


def _tenant_fk() -> sa.Column:
    return sa.Column(
        "tenant_id",
        postgresql.UUID(as_uuid=True),
        sa.ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )


def upgrade() -> None:
    # Pharmacy
    op.create_table(
        "pharmacy_batches",
        _uuid_pk(),
        _tenant_fk(),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("batch_no", sa.String(64), nullable=False),
        sa.Column("expiry_date", sa.Date, nullable=False),
        sa.Column("quantity_remaining", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "product_id", "batch_no", name="uq_pharmacy_batch"),
    )
    op.create_index("ix_pharmacy_batches_tenant_id", "pharmacy_batches", ["tenant_id"])
    op.create_index("ix_pharmacy_batches_product_id", "pharmacy_batches", ["product_id"])

    # Garage
    op.create_table(
        "vehicles",
        _uuid_pk(),
        _tenant_fk(),
        sa.Column(
            "customer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("customers.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("plate", sa.String(16), nullable=False),
        sa.Column("make", sa.String(64), nullable=False),
        sa.Column("model", sa.String(64), nullable=False),
        sa.Column("year", sa.Integer, nullable=True),
        sa.Column("vin", sa.String(32), nullable=True),
        sa.UniqueConstraint("tenant_id", "plate", name="uq_vehicles_tenant_plate"),
    )
    op.create_index("ix_vehicles_tenant_id", "vehicles", ["tenant_id"])

    op.create_table(
        "job_cards",
        _uuid_pk(),
        _tenant_fk(),
        sa.Column(
            "vehicle_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("vehicles.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "order_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("orders.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "technician_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(16), nullable=False, server_default="open"),
        sa.Column("description", sa.String(2048), nullable=False, server_default=""),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_job_cards_tenant_id", "job_cards", ["tenant_id"])
    op.create_index("ix_job_cards_vehicle_id", "job_cards", ["vehicle_id"])

    # Gym
    op.create_table(
        "gym_memberships",
        _uuid_pk(),
        _tenant_fk(),
        sa.Column(
            "customer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("customers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("plan_code", sa.String(32), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("starts_on", sa.Date, nullable=False),
        sa.Column("ends_on", sa.Date, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_gym_memberships_tenant_id", "gym_memberships", ["tenant_id"])

    op.create_table(
        "gym_checkins",
        _uuid_pk(),
        _tenant_fk(),
        sa.Column(
            "membership_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("gym_memberships.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("checked_in_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Salon
    op.create_table(
        "salon_appointments",
        _uuid_pk(),
        _tenant_fk(),
        sa.Column(
            "customer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("customers.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "staff_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("service_name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="booked"),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_salon_appointments_tenant_id", "salon_appointments", ["tenant_id"])

    # Hotel
    op.create_table(
        "hotel_rooms",
        _uuid_pk(),
        _tenant_fk(),
        sa.Column("number", sa.String(16), nullable=False),
        sa.Column("category", sa.String(32), nullable=False, server_default="standard"),
        sa.Column("nightly_rate_cents", sa.Integer, nullable=False, server_default="0"),
        sa.UniqueConstraint("tenant_id", "number", name="uq_rooms_tenant_number"),
    )

    op.create_table(
        "hotel_reservations",
        _uuid_pk(),
        _tenant_fk(),
        sa.Column(
            "room_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("hotel_rooms.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "customer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("customers.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(16), nullable=False, server_default="booked"),
        sa.Column("check_in", sa.Date, nullable=False),
        sa.Column("check_out", sa.Date, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Cinema
    op.create_table(
        "cinema_shows",
        _uuid_pk(),
        _tenant_fk(),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("screen", sa.String(32), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ticket_price_cents", sa.Integer, nullable=False, server_default="0"),
    )

    op.create_table(
        "cinema_seats",
        _uuid_pk(),
        _tenant_fk(),
        sa.Column(
            "show_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cinema_shows.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("label", sa.String(8), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="available"),
        sa.UniqueConstraint("show_id", "label", name="uq_cinema_seat"),
    )

    # Rental
    op.create_table(
        "rental_assets",
        _uuid_pk(),
        _tenant_fk(),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("label", sa.String(128), nullable=False),
        sa.Column("hourly_rate_cents", sa.Integer, nullable=False, server_default="0"),
        sa.Column("daily_rate_cents", sa.Integer, nullable=False, server_default="0"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_rental_asset_code"),
    )

    op.create_table(
        "rental_contracts",
        _uuid_pk(),
        _tenant_fk(),
        sa.Column(
            "asset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("rental_assets.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "customer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("customers.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(16), nullable=False, server_default="reserved"),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("returned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deposit_cents", sa.Integer, nullable=False, server_default="0"),
    )

    # Jewelry
    op.create_table(
        "jewelry_attributes",
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        _tenant_fk(),
        sa.Column("karat", sa.Integer, nullable=False, server_default="22"),
        sa.Column("gross_grams", sa.Numeric(10, 3), nullable=False, server_default="0"),
        sa.Column("net_grams", sa.Numeric(10, 3), nullable=False, server_default="0"),
        sa.Column("certificate_no", sa.String(64), nullable=True),
    )


def downgrade() -> None:
    for table in (
        "jewelry_attributes",
        "rental_contracts",
        "rental_assets",
        "cinema_seats",
        "cinema_shows",
        "hotel_reservations",
        "hotel_rooms",
        "salon_appointments",
        "gym_checkins",
        "gym_memberships",
        "job_cards",
        "vehicles",
        "pharmacy_batches",
    ):
        op.drop_table(table)
