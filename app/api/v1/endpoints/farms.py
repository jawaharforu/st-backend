from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
import uuid

from app.api import deps
from app.models import Farm, User, Device, UserRole
from app.schemas.farm import FarmCreate, FarmResponse, FarmUpdate
from app.schemas.device import DeviceResponse, DeviceCreate

router = APIRouter()

@router.get("/", response_model=List[FarmResponse])
async def read_farms(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    # Operators see only their farms, Admins see all?
    # Requirement: "farms: id, name, owner_user_id"
    # Assuming operators manage their own farms
    if current_user.role == "admin":
        query = select(Farm).offset(skip).limit(limit)
    else:
        query = select(Farm).where(Farm.owner_user_id == current_user.id).offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/", response_model=FarmResponse)
async def create_farm(
    *,
    db: AsyncSession = Depends(deps.get_db),
    farm_in: FarmCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    # distinct check for email
    # Check if user with email exists
    result = await db.execute(select(User).where(User.email == farm_in.email))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    from app.core.security import get_password_hash
    
    # Create User
    new_user = User(
        email=farm_in.email,
        hashed_password=get_password_hash(farm_in.password),
        full_name=farm_in.name, # Use farm name as user name essentially
        role=UserRole.OPERATOR
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Create Farm linked to new user
    farm = Farm(
        name=farm_in.name,
        location=farm_in.location,
        owner_user_id=new_user.id
    )
    db.add(farm)
    await db.commit()
    await db.refresh(farm)
    return farm

@router.get("/{farm_id}/devices", response_model=List[DeviceResponse])
async def read_farm_devices(
    farm_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    # Verify farm ownership or admin
    farm_res = await db.execute(select(Farm).where(Farm.id == farm_id))
    farm = farm_res.scalars().first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    if current_user.role != "admin" and farm.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    query = select(Device).where(Device.farm_id == farm_id).offset(skip).limit(limit)
    result = await db.execute(query)
    devices = result.scalars().all()

    # Fetch latest telemetry for these devices
    if devices:
        device_ids = [d.id for d in devices]
        from app.models import Telemetry
        
        # Select distinct latest telemetry for each device
        t_query = select(Telemetry).distinct(Telemetry.device_id).where(Telemetry.device_id.in_(device_ids)).order_by(Telemetry.device_id, Telemetry.ts.desc())
        t_result = await db.execute(t_query)
        telemetry_map = {t.device_id: t for t in t_result.scalars().all()}
        
        response = []
        for d in devices:
            d_dict = d.model_dump()
            t = telemetry_map.get(d.id)
            if t:
                d_dict["latest_telemetry"] = t.model_dump()
            response.append(d_dict)
            
        return response

    return devices

@router.post("/{farm_id}/devices", response_model=DeviceResponse)
async def create_device_for_farm(
    farm_id: uuid.UUID,
    device_in: DeviceCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    farm_res = await db.execute(select(Farm).where(Farm.id == farm_id))
    farm = farm_res.scalars().first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    if current_user.role != "admin" and farm.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Generate creds/token?
    # Simple token generation mapping
    token_data = {"token": str(uuid.uuid4())}
    
    device = Device(
        farm_id=farm_id,
        device_id=device_in.device_id,
        model=device_in.model,
        firmware_version=device_in.firmware_version,
        # Temperature Thresholds
        temp_high=device_in.temp_high,
        temp_low=device_in.temp_low,
        # Cooling Threshold
        humidity_temp=device_in.humidity_temp,
        # Sensor Calibration Offsets
        sensor1_offset=device_in.sensor1_offset,
        sensor2_offset=device_in.sensor2_offset,
        # Motor Control
        motor_mode=device_in.motor_mode,
        timer_sec=device_in.timer_sec,
        # Legacy fields
        temp_x=device_in.temp_x,
        humidity=device_in.humidity,
        status="registered",
        credentials=token_data
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return device

@router.put("/{farm_id}", response_model=FarmResponse)
async def update_farm(
    farm_id: uuid.UUID,
    farm_in: FarmUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    farm_res = await db.execute(select(Farm).where(Farm.id == farm_id))
    farm = farm_res.scalars().first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    if current_user.role != "admin" and farm.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if farm_in.name is not None:
        farm.name = farm_in.name
    if farm_in.location is not None:
        farm.location = farm_in.location
    
    db.add(farm)
    await db.commit()
    await db.refresh(farm)
    return farm

@router.delete("/{farm_id}", response_model=FarmResponse)
async def delete_farm(
    farm_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    farm_res = await db.execute(select(Farm).where(Farm.id == farm_id))
    farm = farm_res.scalars().first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    if current_user.role != "admin" and farm.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    await db.delete(farm)
    await db.commit()
    return farm
