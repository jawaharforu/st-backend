from typing import Optional
from sqlmodel import SQLModel
from app.models import FarmBase
import uuid

class FarmCreate(FarmBase):
    email: str
    password: str

class FarmUpdate(SQLModel):
    name: Optional[str] = None
    location: Optional[str] = None

class FarmResponse(FarmBase):
    id: uuid.UUID
    owner_user_id: uuid.UUID
