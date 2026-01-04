"""Add device config and telemetry fields

Revision ID: 002_device_telemetry_fields
Revises: 001_initial
Create Date: 2026-01-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_device_telemetry_fields'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add Device Type 3 Configuration Fields to device table
    op.add_column('device', sa.Column('temp_high', sa.Float(), nullable=True))
    op.add_column('device', sa.Column('temp_low', sa.Float(), nullable=True))
    op.add_column('device', sa.Column('temp_x', sa.Float(), nullable=True))
    op.add_column('device', sa.Column('humidity', sa.Float(), nullable=True))
    op.add_column('device', sa.Column('humidity_temp', sa.Float(), nullable=True))
    op.add_column('device', sa.Column('timer_sec', sa.Integer(), nullable=True))
    
    # Add new telemetry fields to telemetry table
    op.add_column('telemetry', sa.Column('primary_heater', sa.Boolean(), nullable=True))
    op.add_column('telemetry', sa.Column('secondary_heater', sa.Boolean(), nullable=True))
    op.add_column('telemetry', sa.Column('exhaust_fan', sa.Boolean(), nullable=True))
    op.add_column('telemetry', sa.Column('sv_valve', sa.Boolean(), nullable=True))
    op.add_column('telemetry', sa.Column('turning_motor', sa.Boolean(), nullable=True))
    op.add_column('telemetry', sa.Column('limit_switch', sa.Boolean(), nullable=True))
    op.add_column('telemetry', sa.Column('door_light', sa.Boolean(), nullable=True))
    op.add_column('telemetry', sa.Column('ip', sa.String(), nullable=True))
    
    # Make existing telemetry fields nullable for backward compatibility
    op.alter_column('telemetry', 'seq', existing_type=sa.Integer(), nullable=True)
    op.alter_column('telemetry', 'temp_c', existing_type=sa.Float(), nullable=True)
    op.alter_column('telemetry', 'hum_pct', existing_type=sa.Float(), nullable=True)
    op.alter_column('telemetry', 'heater', existing_type=sa.Boolean(), nullable=True)
    op.alter_column('telemetry', 'fan', existing_type=sa.Boolean(), nullable=True)
    op.alter_column('telemetry', 'rssi', existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    # Remove telemetry fields
    op.drop_column('telemetry', 'ip')
    op.drop_column('telemetry', 'door_light')
    op.drop_column('telemetry', 'limit_switch')
    op.drop_column('telemetry', 'turning_motor')
    op.drop_column('telemetry', 'sv_valve')
    op.drop_column('telemetry', 'exhaust_fan')
    op.drop_column('telemetry', 'secondary_heater')
    op.drop_column('telemetry', 'primary_heater')
    
    # Remove device config fields
    op.drop_column('device', 'timer_sec')
    op.drop_column('device', 'humidity_temp')
    op.drop_column('device', 'humidity')
    op.drop_column('device', 'temp_x')
    op.drop_column('device', 'temp_low')
    op.drop_column('device', 'temp_high')
    
    # Revert nullable changes (note: this may fail if null data exists)
    op.alter_column('telemetry', 'rssi', existing_type=sa.Integer(), nullable=False)
    op.alter_column('telemetry', 'fan', existing_type=sa.Boolean(), nullable=False)
    op.alter_column('telemetry', 'heater', existing_type=sa.Boolean(), nullable=False)
    op.alter_column('telemetry', 'hum_pct', existing_type=sa.Float(), nullable=False)
    op.alter_column('telemetry', 'temp_c', existing_type=sa.Float(), nullable=False)
    op.alter_column('telemetry', 'seq', existing_type=sa.Integer(), nullable=False)
