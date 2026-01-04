from typing import Optional
from sqlmodel import SQLModel
from app.models import FirmwareManifest
import uuid
from datetime import datetime

class FirmwareCreate(SQLModel):
    version: str
    required: bool = False

class FirmwareResponse(FirmwareManifest):
    id: uuid.UUID
    created_at: datetime
