"""add_parts_and_services_tables

Revision ID: 0002_parts_services
Revises: 0001
Create Date: 2026-08-25 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '0002_parts_services'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'services',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('base_price', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_services_name'), 'services', ['name'], unique=False)
    op.create_index(op.f('ix_services_category'), 'services', ['category'], unique=False)

    op.create_table(
        'parts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('part_number', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('unit_price', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'),
        sa.Column('stock_quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_parts_name'), 'parts', ['name'], unique=False)
    op.create_index(op.f('ix_parts_part_number'), 'parts', ['part_number'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_parts_part_number'), table_name='parts')
    op.drop_index(op.f('ix_parts_name'), table_name='parts')
    op.drop_table('parts')
    op.drop_index(op.f('ix_services_category'), table_name='services')
    op.drop_index(op.f('ix_services_name'), table_name='services')
    op.drop_table('services')
