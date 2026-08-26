"""initial_schema

Revision ID: 0001
Revises: 
Create Date: 2026-03-30 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as me

revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users Table
    op.create_table(
        'users',
        me.Column('id', me.String(length=36), nullable=False),
        me.Column('email', me.String(length=255), nullable=False),
        me.Column('hashed_password', me.String(length=255), nullable=False),
        me.Column('full_name', me.String(length=255), nullable=False),
        me.Column('phone_number', me.String(length=50), nullable=False),
        me.Column('role', me.Enum('CUSTOMER', 'RESPONDER', 'MANAGER', 'ADMIN', name='userrole'), nullable=False),
        me.Column('is_active', me.Boolean(), nullable=False, server_default='true'),
        me.Column('created_at', me.DateTime(), nullable=False),
        me.Column('updated_at', me.DateTime(), nullable=False),
        me.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Responders Table
    op.create_table(
        'responders',
        me.Column('id', me.String(length=36), nullable=False),
        me.Column('user_id', me.String(length=36), nullable=False),
        me.Column('type', me.Enum('CAR_MECHANIC', 'BIKE_MECHANIC', 'PARAMEDIC', 'TOWING_OPERATOR', 'ROADSIDE_TECHNICIAN', name='respondertype'), nullable=False),
        me.Column('is_available', me.Boolean(), nullable=False, server_default='true'),
        me.Column('is_online', me.Boolean(), nullable=False, server_default='false'),
        me.Column('created_at', me.DateTime(), nullable=False),
        me.Column('updated_at', me.DateTime(), nullable=False),
        me.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        me.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_responders_user_id'), 'responders', ['user_id'], unique=True)

    # Responder Skills Table
    op.create_table(
        'responder_skills',
        me.Column('id', me.String(length=36), nullable=False),
        me.Column('responder_id', me.String(length=36), nullable=False),
        me.Column('skill_name', me.String(length=100), nullable=False),
        me.Column('created_at', me.DateTime(), nullable=False),
        me.ForeignKeyConstraint(['responder_id'], ['responders.id'], ondelete='CASCADE'),
        me.PrimaryKeyConstraint('id')
    )

    # Responder Locations Table
    op.create_table(
        'responder_locations',
        me.Column('id', me.String(length=36), nullable=False),
        me.Column('responder_id', me.String(length=36), nullable=False),
        me.Column('latitude', me.Float(), nullable=False),
        me.Column('longitude', me.Float(), nullable=False),
        me.Column('created_at', me.DateTime(), nullable=False),
        me.ForeignKeyConstraint(['responder_id'], ['responders.id'], ondelete='CASCADE'),
        me.PrimaryKeyConstraint('id')
    )

    # Tickets Table
    op.create_table(
        'tickets',
        me.Column('id', me.String(length=36), nullable=False),
        me.Column('customer_id', me.String(length=36), nullable=False),
        me.Column('vehicle_type', me.String(length=100), nullable=False),
        me.Column('service_type', me.Enum('CAR_MECHANIC', 'BIKE_MECHANIC', 'PARAMEDIC', 'TOWING_OPERATOR', 'ROADSIDE_TECHNICIAN', name='respondertype'), nullable=False),
        me.Column('description', me.Text(), nullable=True),
        me.Column('latitude', me.Float(), nullable=False),
        me.Column('longitude', me.Float(), nullable=False),
        me.Column('priority', me.Enum('LOW', 'MEDIUM', 'HIGH', 'EMERGENCY', name='ticketpriority'), nullable=False),
        me.Column('status', me.Enum('REQUESTED', 'DISPATCHING', 'ASSIGNED', 'ACCEPTED', 'EN_ROUTE', 'ARRIVED', 'IN_SERVICE', 'COMPLETED', 'CANCELLED', 'NO_RESPONDER', 'REASSIGN', 'FAILED', name='ticketstatus'), nullable=False),
        me.Column('contact_phone', me.String(length=50), nullable=False),
        me.Column('created_at', me.DateTime(), nullable=False),
        me.Column('updated_at', me.DateTime(), nullable=False),
        me.ForeignKeyConstraint(['customer_id'], ['users.id'], ondelete='CASCADE'),
        me.PrimaryKeyConstraint('id')
    )

    # Ticket Assignments Table
    op.create_table(
        'ticket_assignments',
        me.Column('id', me.String(length=36), nullable=False),
        me.Column('ticket_id', me.String(length=36), nullable=False),
        me.Column('responder_id', me.String(length=36), nullable=False),
        me.Column('status', me.Enum('OFFERED', 'ACCEPTED', 'REJECTED', 'CANCELLED', 'EXPIRED', name='assignmentstatus'), nullable=False),
        me.Column('score', me.Float(), nullable=False),
        me.Column('created_at', me.DateTime(), nullable=False),
        me.Column('updated_at', me.DateTime(), nullable=False),
        me.ForeignKeyConstraint(['responder_id'], ['responders.id'], ondelete='CASCADE'),
        me.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], ondelete='CASCADE'),
        me.PrimaryKeyConstraint('id')
    )

    # Ticket Status Logs Table
    op.create_table(
        'ticket_status_logs',
        me.Column('id', me.String(length=36), nullable=False),
        me.Column('ticket_id', me.String(length=36), nullable=False),
        me.Column('previous_status', me.Enum('REQUESTED', 'DISPATCHING', 'ASSIGNED', 'ACCEPTED', 'EN_ROUTE', 'ARRIVED', 'IN_SERVICE', 'COMPLETED', 'CANCELLED', 'NO_RESPONDER', 'REASSIGN', 'FAILED', name='ticketstatus'), nullable=True),
        me.Column('new_status', me.Enum('REQUESTED', 'DISPATCHING', 'ASSIGNED', 'ACCEPTED', 'EN_ROUTE', 'ARRIVED', 'IN_SERVICE', 'COMPLETED', 'CANCELLED', 'NO_RESPONDER', 'REASSIGN', 'FAILED', name='ticketstatus'), nullable=False),
        me.Column('changed_by_user_id', me.String(length=36), nullable=True),
        me.Column('reason', me.String(length=255), nullable=True),
        me.Column('created_at', me.DateTime(), nullable=False),
        me.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], ondelete='CASCADE'),
        me.PrimaryKeyConstraint('id')
    )

    # Idempotency Records Table
    op.create_table(
        'idempotency_records',
        me.Column('id', me.String(length=36), nullable=False),
        me.Column('idempotency_key', me.String(length=255), nullable=False),
        me.Column('user_id', me.String(length=36), nullable=False),
        me.Column('action_type', me.String(length=100), nullable=False),
        me.Column('response_payload', me.JSON(), nullable=True),
        me.Column('created_at', me.DateTime(), nullable=False),
        me.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_idempotency_records_idempotency_key'), 'idempotency_records', ['idempotency_key'], unique=True)


def downgrade() -> None:
    op.drop_table('idempotency_records')
    op.drop_table('ticket_status_logs')
    op.drop_table('ticket_assignments')
    op.drop_table('tickets')
    op.drop_table('responder_locations')
    op.drop_table('responder_skills')
    op.drop_table('responders')
    op.drop_table('users')
