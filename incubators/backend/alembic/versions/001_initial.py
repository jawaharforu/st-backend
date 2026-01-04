"""initial migration

Revision ID: 001
Revises: 
Create Date: 2025-12-09 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Enable timescale extension
    # op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;") 
    # Note: You usually need superuser or database owner permissions. 
    # Should work in the docker container.
    
    # Create tables
    op.create_table('user',
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('role', sa.Enum('ADMIN', 'OPERATOR', name='userrole'), nullable=False),
        sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)
    
    op.create_table('farm',
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('owner_user_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['owner_user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('device',
        sa.Column('device_id', sa.String(), nullable=False),
        sa.Column('model', sa.String(), nullable=False),
        sa.Column('firmware_version', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('farm_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
        sa.Column('credentials', sa.JSON(), nullable=True),
        sa.Column('last_seen', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['farm_id'], ['farm.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_device_device_id'), 'device', ['device_id'], unique=True)
    
    op.create_table('command',
        sa.Column('cmd', sa.String(), nullable=False),
        sa.Column('params', sa.JSON(), nullable=True),
        sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('device_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('farm_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'SENT', 'ACKNOWLEDGED', 'FAILED', name='commandstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('response', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['device_id'], ['device.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('firmwaremanifest',
        sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('version', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('sha256', sa.String(), nullable=False),
        sa.Column('size', sa.Integer(), nullable=False),
        sa.Column('required', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('version')
    )
    
    op.create_table('telemetry',
        sa.Column('ts', sa.DateTime(timezone=True), nullable=False),
        sa.Column('device_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('farm_id', sqlmodel.sql.sqltypes.GUID(), nullable=True),
        sa.Column('seq', sa.Integer(), nullable=False),
        sa.Column('temp_c', sa.Float(), nullable=False),
        sa.Column('hum_pct', sa.Float(), nullable=False),
        sa.Column('heater', sa.Boolean(), nullable=False),
        sa.Column('fan', sa.Boolean(), nullable=False),
        sa.Column('rssi', sa.Integer(), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['device_id'], ['device.id'], ),
        sa.PrimaryKeyConstraint('ts', 'device_id')
    )
    op.create_index(op.f('ix_telemetry_ts'), 'telemetry', ['ts'], unique=False)
    op.create_index(op.f('ix_telemetry_farm_id'), 'telemetry', ['farm_id'], unique=False)

    # Convert telemetry to hypertable
    # op.execute("SELECT create_hypertable('telemetry', 'ts');")
    # Using execute with a textual statement for safety if extension might not exist or already hypertable
    # Use plpgsql block to ignore if extension missing? No, we should fail if requirement not met.
    # But for now, wrap in try/catch usually, but let's assume Happy Path for this docker stack.
    op.execute("SELECT create_hypertable('telemetry', 'ts');")


def downgrade():
    op.drop_index(op.f('ix_telemetry_farm_id'), table_name='telemetry')
    op.drop_index(op.f('ix_telemetry_ts'), table_name='telemetry')
    op.drop_table('telemetry')
    op.drop_table('firmwaremanifest')
    op.drop_table('command')
    op.drop_index(op.f('ix_device_device_id'), table_name='device')
    op.drop_table('device')
    op.drop_table('farm')
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_table('user')
