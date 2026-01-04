from typing import Any, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
import uuid
from datetime import datetime

from app.api import deps
from app.models import Telemetry
from app.schemas.farm import FarmResponse # reuse or create specific

router = APIRouter()

@router.get("/devices/{device_id}/telemetry")
async def read_device_telemetry(
    device_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    start_time: datetime = Query(None),
    end_time: datetime = Query(None),
) -> Any:
    # Build query
    query = select(Telemetry).where(Telemetry.device_id == device_id)
    if start_time:
        query = query.where(Telemetry.ts >= start_time)
    if end_time:
        query = query.where(Telemetry.ts <= end_time)
        
    query = query.order_by(Telemetry.ts.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/farms/{farm_id}/telemetry/latest")
async def read_farm_latest_telemetry(
    farm_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    # Advanced: usage of distinct on connection to get latest per device
    # PostgreSQL DISTINCT ON (device_id) ORDER BY device_id, ts DESC
    
    query = select(Telemetry).distinct(Telemetry.device_id).where(Telemetry.farm_id == farm_id).order_by(Telemetry.device_id, Telemetry.ts.desc())
    result = await db.execute(query)
    return result.scalars().all()
