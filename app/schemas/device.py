from typing import Optional, Dict, Any
from sqlmodel import SQLModel
from app.models import DeviceBase
from datetime import datetime
import uuid

class DeviceCreate(DeviceBase):
    farm_id: Optional[uuid.UUID] = None
    # Temperature Thresholds (°F)
    temp_high: Optional[float] = None  # High threshold - heaters OFF above this
    temp_low: Optional[float] = None   # Low threshold - heaters ON below this
    # Cooling Threshold (°F)
    humidity_temp: Optional[float] = None  # Sensor 2 threshold - cooling ON above this
    # Sensor Calibration Offsets (°F)
    sensor1_offset: Optional[float] = 0.0  # Sensor 1 calibration offset
    sensor2_offset: Optional[float] = 0.0  # Sensor 2 calibration offset
    # Motor Control
    motor_mode: Optional[int] = 0  # 0=Timer, 1=Always ON
    timer_sec: Optional[int] = None  # Motor timer interval (seconds)
    # Legacy fields
    temp_x: Optional[float] = None
    humidity: Optional[float] = None

class DeviceUpdate(SQLModel):
    model: Optional[str] = None
    firmware_version: Optional[str] = None
    status: Optional[str] = None
    farm_id: Optional[uuid.UUID] = None
    # Temperature Thresholds (°F)
    temp_high: Optional[float] = None
    temp_low: Optional[float] = None
    # Cooling Threshold (°F)
    humidity_temp: Optional[float] = None
    # Sensor Calibration Offsets (°F)
    sensor1_offset: Optional[float] = None
    sensor2_offset: Optional[float] = None
    # Motor Control
    motor_mode: Optional[int] = None
    timer_sec: Optional[int] = None
    # Legacy fields
    temp_x: Optional[float] = None
    humidity: Optional[float] = None

class DeviceResponse(DeviceBase):
    id: uuid.UUID
    farm_id: Optional[uuid.UUID] = None
    last_seen: Optional[datetime] = None
    credentials: Optional[Dict[str, Any]] = None
    latest_telemetry: Optional[Dict[str, Any]] = None
    # Temperature Thresholds
    temp_high: Optional[float] = None
    temp_low: Optional[float] = None
    # Cooling Threshold
    humidity_temp: Optional[float] = None
    # Sensor Calibration Offsets
    sensor1_offset: Optional[float] = None
    sensor2_offset: Optional[float] = None
    # Motor Control
    motor_mode: Optional[int] = None
    timer_sec: Optional[int] = None
    # Legacy fields
    temp_x: Optional[float] = None
    humidity: Optional[float] = None

class DeviceAnalysisResponse(SQLModel):
    status: str
    temperature_status: Optional[str] = None
    humidity_status: Optional[str] = None
    summary_for_farmer: str
    recommended_action: str

class DeviceStatsResponse(SQLModel):
    max_temp_c: Optional[float] = None
    avg_temp_c: Optional[float] = None
    max_hum_pct: Optional[float] = None
    avg_hum_pct: Optional[float] = None
