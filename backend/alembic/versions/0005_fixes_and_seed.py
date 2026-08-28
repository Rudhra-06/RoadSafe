"""fix contact_phone nullable and seed default services

Revision ID: 0005_fixes_and_seed
Revises: 0004_billing_reviews
Create Date: 2026-09-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
import uuid
from datetime import datetime

revision = '0005_fixes_and_seed'
down_revision = '0004_billing_reviews'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make contact_phone nullable (was NOT NULL, schema has it Optional)
    op.alter_column('tickets', 'contact_phone',
                    existing_type=sa.String(length=50),
                    nullable=True)

    # Make score nullable in ticket_assignments (schema has Optional[float])
    op.alter_column('ticket_assignments', 'score',
                    existing_type=sa.Float(),
                    nullable=True)

    # Seed default RoadSafe services if table is empty
    services_table = table(
        'services',
        column('id', sa.String),
        column('name', sa.String),
        column('description', sa.Text),
        column('category', sa.String),
        column('base_price', sa.Numeric),
        column('estimated_duration_minutes', sa.Integer),
        column('features', sa.Text),
        column('included_items', sa.Text),
        column('possible_parts', sa.Text),
        column('is_active', sa.Boolean),
        column('created_at', sa.DateTime),
        column('updated_at', sa.DateTime),
    )

    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT COUNT(*) FROM services"))
    count = result.scalar()
    if count == 0:
        now = datetime.utcnow()
        default_services = [
            {
                "id": str(uuid.uuid4()),
                "name": "Towing Assistance",
                "description": "Professional vehicle towing to the nearest garage or your preferred location.",
                "category": "Towing",
                "base_price": 799.00,
                "estimated_duration_minutes": 30,
                "features": '["24/7 availability","GPS tracked tow truck","Safe vehicle handling"]',
                "included_items": '["Tow to nearest garage (up to 10km)"]',
                "possible_parts": '[]',
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Flat Tyre Assistance",
                "description": "On-site tyre change or repair by a certified roadside technician.",
                "category": "Tyre",
                "base_price": 299.00,
                "estimated_duration_minutes": 20,
                "features": '["Spare tyre fitting","Tyre puncture repair","Tyre pressure check"]',
                "included_items": '["Labour","Basic tyre repair kit"]',
                "possible_parts": '["Tyre","Valve stem","Wheel nut"]',
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Battery Assistance",
                "description": "Jump-start or battery replacement service at your location.",
                "category": "Battery",
                "base_price": 349.00,
                "estimated_duration_minutes": 15,
                "features": '["Jump-start service","Battery health check","Battery replacement"]',
                "included_items": '["Labour","Jump cables"]',
                "possible_parts": '["Car battery","Battery terminal clamps"]',
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Fuel Assistance",
                "description": "Emergency fuel delivery to get you back on the road.",
                "category": "Fuel",
                "base_price": 199.00,
                "estimated_duration_minutes": 25,
                "features": '["Petrol or diesel delivery","Up to 5 litres included","Safe fuel handling"]',
                "included_items": '["5 litres of fuel","Delivery to location"]',
                "possible_parts": '[]',
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Mechanical Breakdown",
                "description": "On-site diagnosis and repair for common mechanical failures.",
                "category": "Mechanical",
                "base_price": 499.00,
                "estimated_duration_minutes": 45,
                "features": '["On-site diagnosis","Minor repairs","Parts sourcing assistance"]',
                "included_items": '["Labour (up to 1 hour)","Basic diagnostic scan"]',
                "possible_parts": '["Fuses","Belts","Hoses","Spark plugs"]',
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Lockout Assistance",
                "description": "Professional vehicle lockout service — keys locked inside or lost.",
                "category": "Lockout",
                "base_price": 249.00,
                "estimated_duration_minutes": 20,
                "features": '["Non-destructive entry","Key duplication referral","24/7 service"]',
                "included_items": '["Labour","Lockout tools"]',
                "possible_parts": '[]',
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            },
        ]
        op.bulk_insert(services_table, default_services)


def downgrade() -> None:
    op.alter_column('ticket_assignments', 'score',
                    existing_type=sa.Float(),
                    nullable=False)
    op.alter_column('tickets', 'contact_phone',
                    existing_type=sa.String(length=50),
                    nullable=False)
