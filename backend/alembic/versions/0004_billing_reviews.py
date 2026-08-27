"""billing, payment and review records"""
from alembic import op
import sqlalchemy as sa

revision = '0004_billing_reviews'
down_revision = '0003_customer_experience'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('invoices', sa.Column('id',sa.String(36),primary_key=True), sa.Column('invoice_number',sa.String(40),nullable=False,unique=True), sa.Column('ticket_id',sa.String(36),sa.ForeignKey('tickets.id'),nullable=False,unique=True), sa.Column('customer_id',sa.String(36),sa.ForeignKey('users.id'),nullable=False), sa.Column('service_total',sa.Numeric(10,2),nullable=False), sa.Column('parts_total',sa.Numeric(10,2),nullable=False), sa.Column('fees_total',sa.Numeric(10,2),nullable=False), sa.Column('tax_total',sa.Numeric(10,2),nullable=False), sa.Column('grand_total',sa.Numeric(10,2),nullable=False), sa.Column('status',sa.String(20),nullable=False), sa.Column('created_at',sa.DateTime,nullable=False), sa.Column('updated_at',sa.DateTime,nullable=False))
    op.create_table('invoice_lines', sa.Column('id',sa.String(36),primary_key=True), sa.Column('invoice_id',sa.String(36),sa.ForeignKey('invoices.id'),nullable=False), sa.Column('part_id',sa.String(36),sa.ForeignKey('parts.id'),nullable=True), sa.Column('description',sa.String(255),nullable=False), sa.Column('quantity',sa.Integer,nullable=False), sa.Column('unit_price',sa.Numeric(10,2),nullable=False), sa.Column('line_total',sa.Numeric(10,2),nullable=False), sa.Column('line_type',sa.String(20),nullable=False), sa.Column('created_at',sa.DateTime,nullable=False), sa.Column('updated_at',sa.DateTime,nullable=False))
    op.create_table('payments', sa.Column('id',sa.String(36),primary_key=True), sa.Column('invoice_id',sa.String(36),sa.ForeignKey('invoices.id'),nullable=False), sa.Column('provider',sa.String(30),nullable=False), sa.Column('provider_order_id',sa.String(100),nullable=False,unique=True), sa.Column('provider_payment_id',sa.String(100),nullable=True,unique=True), sa.Column('amount',sa.Numeric(10,2),nullable=False), sa.Column('currency',sa.String(8),nullable=False), sa.Column('status',sa.String(20),nullable=False), sa.Column('created_at',sa.DateTime,nullable=False), sa.Column('updated_at',sa.DateTime,nullable=False))
    op.create_table('reviews', sa.Column('id',sa.String(36),primary_key=True), sa.Column('ticket_id',sa.String(36),sa.ForeignKey('tickets.id'),nullable=False,unique=True), sa.Column('customer_id',sa.String(36),sa.ForeignKey('users.id'),nullable=False), sa.Column('responder_id',sa.String(36),sa.ForeignKey('responders.id'),nullable=True), sa.Column('rating',sa.Integer,nullable=False), sa.Column('comment',sa.Text,nullable=True), sa.Column('created_at',sa.DateTime,nullable=False), sa.Column('updated_at',sa.DateTime,nullable=False))

def downgrade():
    op.drop_table('reviews'); op.drop_table('payments'); op.drop_table('invoice_lines'); op.drop_table('invoices')
