"""customer service catalog and provider profile fields"""
from alembic import op
import sqlalchemy as sa

revision = '0003_customer_experience'
down_revision = '0002_parts_services'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('services', sa.Column('estimated_duration_minutes', sa.Integer(), nullable=True))
    op.add_column('services', sa.Column('features', sa.Text(), nullable=True))
    op.add_column('services', sa.Column('included_items', sa.Text(), nullable=True))
    op.add_column('services', sa.Column('possible_parts', sa.Text(), nullable=True))
    op.add_column('responders', sa.Column('shop_name', sa.String(length=255), nullable=True))
    op.add_column('responders', sa.Column('shop_address', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('responders', 'shop_address')
    op.drop_column('responders', 'shop_name')
    op.drop_column('services', 'possible_parts')
    op.drop_column('services', 'included_items')
    op.drop_column('services', 'features')
    op.drop_column('services', 'estimated_duration_minutes')
