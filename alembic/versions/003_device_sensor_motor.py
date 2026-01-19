"""Add sensor calibration and motor control fields to device

Revision ID: 003_device_sensor_motor
Revises: 002_device_telemetry_fields
Create Date: 2026-01-18

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003_device_sensor_motor'
down_revision = '002_device_telemetry_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Add sensor calibration offset fields
    op.add_column('device', sa.Column('sensor1_offset', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('device', sa.Column('sensor2_offset', sa.Float(), nullable=True, server_default='0.0'))
    
    # Add motor control mode field
    op.add_column('device', sa.Column('motor_mode', sa.Integer(), nullable=True, server_default='0'))


def downgrade():
    op.drop_column('device', 'motor_mode')
    op.drop_column('device', 'sensor2_offset')
    op.drop_column('device', 'sensor1_offset')
