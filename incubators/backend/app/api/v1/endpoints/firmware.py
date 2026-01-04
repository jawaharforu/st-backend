from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
import hashlib
import uuid

from app.api import deps
from app.models import FirmwareManifest, Device, User
from app.schemas.firmware import FirmwareResponse
from app.services.storage import storage_service

router = APIRouter()

@router.post("/", response_model=FirmwareResponse)
async def upload_firmware(
    file: UploadFile = File(...),
    version: str = Form(...),
    required: bool = Form(False),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_admin),
) -> Any:
    # Check if version exists
    result = await db.execute(select(FirmwareManifest).where(FirmwareManifest.version == version))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Version already exists")

    # Read file content to calc hash and upload
    content = await file.read()
    sha256_hash = hashlib.sha256(content).hexdigest()
    size = len(content)
    
    # Upload to MinIO
    filename = f"firmware_{version}.bin"
    url = await storage_service.upload_file(filename, content)
    
    # Create record
    fw = FirmwareManifest(
        version=version,
        url=url,
        sha256=sha256_hash,
        size=size,
        required=required
    )
    db.add(fw)
    await db.commit()
    await db.refresh(fw)
    return fw

@router.get("/", response_model=List[FirmwareResponse])
async def list_firmware(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    query = select(FirmwareManifest).order_by(FirmwareManifest.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/devices/{device_id}/ota", response_model=FirmwareResponse)
async def get_device_ota(
    device_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    # Device might call this using token usually.
    # If using current_user, it means Admin/Operator checks.
    # If device is calling, we need a separate Auth dependency for devices 
    # or use the token logic (not implemented fully).
    # For now, let's assume valid Auth (User or Device Token mapped to User or separate scope).
    # We'll use get_db for now.
) -> Any:
    # Logic: Get latest firmware. 
    # Optional logic: constraints by model.
    query = select(FirmwareManifest).order_by(FirmwareManifest.created_at.desc())
    result = await db.execute(query)
    latest = result.scalars().first()
    
    if not latest:
        raise HTTPException(status_code=404, detail="No firmware found")
        
    return latest
