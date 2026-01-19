import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON, DateTime, func, String, Boolean, text
from pydantic import EmailStr

# Enums
class UserRole(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"

class CommandStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    ACKNOWLEDGED = "ack"
    FAILED = "failed"

# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True)
    full_name: Optional[str] = None
    # role: UserRole = Field(default=UserRole.OPERATOR)
    role: str

class User(UserBase, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    created_at: datetime = Field(sa_type=DateTime(timezone=True), sa_column_kwargs={"server_default": func.now()})
    
    farms: List["Farm"] = Relationship(back_populates="owner")

class FarmBase(SQLModel):
    name: str
    location: Optional[str] = None

class Farm(FarmBase, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_user_id: uuid.UUID = Field(foreign_key="user.id")
    created_at: datetime = Field(sa_type=DateTime(timezone=True), sa_column_kwargs={"server_default": func.now()})
    
    owner: User = Relationship(back_populates="farms")
    devices: List["Device"] = Relationship(back_populates="farm")

class DeviceBase(SQLModel):
    device_id: str = Field(unique=True, index=True, description="Physical Device ID (e.g. Serial Number)")
    model: str
    firmware_version: Optional[str] = None
    status: str = "offline"

class Device(DeviceBase, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    farm_id: Optional[uuid.UUID] = Field(default=None, foreign_key="farm.id")
    credentials: Optional[Dict[str, Any]] = Field(default=None, sa_type=JSON) # Store token or cert paths
    last_seen: Optional[datetime] = Field(default=None, sa_type=DateTime(timezone=True))
    created_at: datetime = Field(sa_type=DateTime(timezone=True), sa_column_kwargs={"server_default": func.now()})
    
    # Temperature Thresholds (°F)
    temp_high: Optional[float] = Field(default=None, description="High threshold - heaters OFF above this (°F)")
    temp_low: Optional[float] = Field(default=None, description="Low threshold - heaters ON below this (°F)")
    
    # Cooling Threshold (°F)
    humidity_temp: Optional[float] = Field(default=None, description="Sensor 2 threshold - cooling ON above this (°F)")
    
    # Sensor Calibration Offsets (°F)
    sensor1_offset: Optional[float] = Field(default=0.0, description="Sensor 1 calibration offset (°F)")
    sensor2_offset: Optional[float] = Field(default=0.0, description="Sensor 2 calibration offset (°F)")
    
    # Motor Control
    motor_mode: Optional[int] = Field(default=0, description="Motor mode: 0=Timer, 1=Always ON")
    timer_sec: Optional[int] = Field(default=None, description="Motor timer interval (seconds)")
    
    # Legacy fields (kept for backward compatibility)
    temp_x: Optional[float] = Field(default=None, description="Temperature X value (°F)")
    humidity: Optional[float] = Field(default=None, description="Target humidity (%)")
    
    farm: Optional[Farm] = Relationship(back_populates="devices")
    commands: List["Command"] = Relationship(back_populates="device")

class Telemetry(SQLModel, table=True):
    """
    TimescaleDB Hypertable
    Primary Key is (ts, device_id) usually for chunks, but SQLModel expects a PK.
    We will use composite PK (ts, device_id).
    """
    ts: datetime = Field(primary_key=True, sa_type=DateTime(timezone=True), index=True)
    device_id: uuid.UUID = Field(primary_key=True, foreign_key="device.id")
    farm_id: Optional[uuid.UUID] = Field(index=True)
    
    seq: Optional[int] = None
    
    # Current readings (temperatures in Fahrenheit from device)
    temp_c: Optional[float] = None  # Current temperature (kept as temp_c for backward compat, but device sends °F)
    hum_pct: Optional[float] = None  # Current humidity %
    
    # Actuator states (on/off)
    primary_heater: Optional[bool] = None  # Primary heater on/off
    secondary_heater: Optional[bool] = None  # Secondary heater on/off
    exhaust_fan: Optional[bool] = None  # Exhaust fan on/off
    sv_valve: Optional[bool] = None  # SV valve on/off
    fan: Optional[bool] = None  # Fan on/off
    turning_motor: Optional[bool] = None  # Turning motor on/off
    limit_switch: Optional[bool] = None  # Limit switch on/off
    door_light: Optional[bool] = None  # Door light on/off
    
    # Legacy fields (for backward compatibility)
    heater: Optional[bool] = None  # Kept for backward compatibility
    motor_state: Optional[str] = None
    uptime_s: Optional[int] = None
    rssi: Optional[int] = None
    
    # Device info
    ip: Optional[str] = None  # Device IP address
    
    payload: Optional[Dict[str, Any]] = Field(default=None, sa_type=JSON)

class CommandBase(SQLModel):
    cmd: str
    params: Optional[Dict[str, Any]] = Field(default=None, sa_type=JSON)

class Command(CommandBase, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    device_id: uuid.UUID = Field(foreign_key="device.id")
    farm_id: Optional[uuid.UUID] = None
    
    status: CommandStatus = Field(default=CommandStatus.PENDING)
    created_at: datetime = Field(sa_type=DateTime(timezone=True), sa_column_kwargs={"server_default": func.now()})
    sent_at: Optional[datetime] = Field(default=None, sa_type=DateTime(timezone=True))
    response: Optional[Dict[str, Any]] = Field(default=None, sa_type=JSON)
    
    device: Device = Relationship(back_populates="commands")

class FirmwareManifest(SQLModel, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    version: str = Field(unique=True)
    url: str
    sha256: str
    size: int
    required: bool = False
    created_at: datetime = Field(sa_type=DateTime(timezone=True), sa_column_kwargs={"server_default": func.now()})

# Pydantic schemas for API (Clean separation)
# We can use the Base classes or create new ones in schemas.py
# For now, models.py is serving as both DB and Pydantic base.
