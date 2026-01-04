from typing import Optional, Dict, Any
from sqlmodel import SQLModel
from app.models import CommandBase, CommandStatus
from datetime import datetime
import uuid

class CommandCreate(CommandBase):
    pass

class CommandResponse(CommandBase):
    id: uuid.UUID
    device_id: uuid.UUID
    status: CommandStatus
    created_at: datetime
    sent_at: Optional[datetime] = None
    response: Optional[Dict[str, Any]] = None
