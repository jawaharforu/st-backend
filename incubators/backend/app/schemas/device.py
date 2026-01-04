from typing import Optional, Dict, Any
from sqlmodel import SQLModel
from app.models import DeviceBase
from datetime import datetime
import uuid

class DeviceCreate(DeviceBase):
    farm_id: Optional[uuid.UUID] = None
    # Device Type 3 Configuration Fields (temperatures in Fahrenheit)
    temp_high: Optional[float] = None  # High temperature threshold (°F)
    temp_low: Optional[float] = None   # Low temperature threshold (°F)
    temp_x: Optional[float] = None     # Temperature X value (°F)
    humidity: Optional[float] = None   # Target humidity (%)
    humidity_temp: Optional[float] = None  # Humidity temperature (°F)
    timer_sec: Optional[int] = None    # Timer duration (seconds)

class DeviceUpdate(SQLModel):
    model: Optional[str] = None
    firmware_version: Optional[str] = None
    status: Optional[str] = None
    farm_id: Optional[uuid.UUID] = None
    # Device Type 3 Configuration Fields (temperatures in Fahrenheit)
    temp_high: Optional[float] = None
    temp_low: Optional[float] = None
    temp_x: Optional[float] = None
    humidity: Optional[float] = None
    humidity_temp: Optional[float] = None
    timer_sec: Optional[int] = None

class DeviceResponse(DeviceBase):
    id: uuid.UUID
    farm_id: Optional[uuid.UUID] = None
    last_seen: Optional[datetime] = None
    credentials: Optional[Dict[str, Any]] = None
    latest_telemetry: Optional[Dict[str, Any]] = None
    # Device Type 3 Configuration Fields
    temp_high: Optional[float] = None
    temp_low: Optional[float] = None
    temp_x: Optional[float] = None
    humidity: Optional[float] = None
    humidity_temp: Optional[float] = None
    timer_sec: Optional[int] = None

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

