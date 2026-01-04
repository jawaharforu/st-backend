from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, delete
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

from app.api import deps
from app.models import Device, Command, CommandStatus, Farm
from app.schemas.device import DeviceResponse, DeviceUpdate
from app.schemas.command import CommandCreate, CommandResponse
from app.services.mqtt_service import mqtt_service

router = APIRouter()

@router.get("/", response_model=List[DeviceResponse])
async def list_devices(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """
    List devices.
    Admin: All devices.
    Operator: Devices in owned farms.
    """
    if current_user.role == "admin":
        query = select(Device).offset(skip).limit(limit)
    else:
        # Join with Farm to check ownership
        # Device -> Farm -> Owner
        # But Device has farm_id. Farm has owner_user_id.
        # So we need to join Device and Farm.
        # select(Device).join(Farm).where(Farm.owner_user_id == current_user.id)
        # select(Device).join(Farm).where(Farm.owner_user_id == current_user.id)
        from app.models import Farm
        query = select(Device).join(Farm).where(Farm.owner_user_id == current_user.id).offset(skip).limit(limit)
    
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

@router.get("/{device_id}", response_model=DeviceResponse)
async def read_device(
    device_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalars().first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
        
    # Fetch latest telemetry
    from app.models import Telemetry
    t_query = select(Telemetry).where(Telemetry.device_id == device_id).order_by(Telemetry.ts.desc()).limit(1)
    t_result = await db.execute(t_query)
    latest_telemetry = t_result.scalars().first()
    
    device_dict = device.model_dump()
    if latest_telemetry:
        device_dict["latest_telemetry"] = latest_telemetry.model_dump()
        
    return device_dict

@router.post("/{device_id}/cmd", response_model=CommandResponse)
async def send_command(
    device_id: uuid.UUID,
    cmd_in: CommandCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    import traceback
    try:
        result = await db.execute(select(Device).where(Device.id == device_id))
        device = result.scalars().first()
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Create command record
        command = Command(
            device_id=device_id,
            farm_id=device.farm_id,
            cmd=cmd_in.cmd,
            params=cmd_in.params,
            status=CommandStatus.PENDING
        )
        db.add(command)
        await db.commit()
        await db.refresh(command)
        
        # Publish to MQTT
        # Topic: incubators/{device_id}/cmd
        topic = f"incubators/{device.device_id}/cmd"
        
        payload = {
            "cmd_id": str(command.id),
            "cmd": command.cmd,
            "params": command.params,
            "ts": datetime.utcnow().isoformat()
        }
        
        # Try to publish to MQTT, but don't fail the whole request if MQTT is down
        try:
            if mqtt_service.is_connected:
                await mqtt_service.publish(topic, payload, qos=1)
                command.status = CommandStatus.SENT
                command.sent_at = datetime.utcnow()
            else:
                # MQTT not connected, command stays PENDING
                logger.warning(f"MQTT not connected, command {command.id} stays PENDING")
        except Exception as e:
            logger.error(f"Failed to publish MQTT command: {e}")
            command.status = CommandStatus.FAILED
        
        db.add(command)
        await db.commit()
        await db.refresh(command)

        # Return as dict to avoid pydantic validation issues
        return {
            "id": command.id,
            "device_id": command.device_id,
            "cmd": command.cmd,
            "params": command.params,
            "status": command.status,
            "created_at": command.created_at,
            "sent_at": command.sent_at,
            "response": command.response
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"send_command error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Command error: {str(e)}")

@router.get("/{device_id}/cmds", response_model=List[CommandResponse])
async def read_commands(
    device_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    query = select(Command).where(Command.device_id == device_id).order_by(Command.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: uuid.UUID,
    device_in: DeviceUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    # Check device exists
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalars().first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
        
    # Check permissions (Admin or Owner of Farm)
    farm_res = await db.execute(select(Farm).where(Farm.id == device.farm_id))
    farm = farm_res.scalars().first()
    
    if current_user.role != "admin":
         if not farm or farm.owner_user_id != current_user.id:
             raise HTTPException(status_code=403, detail="Not authorized")

    if device_in.model is not None:
        device.model = device_in.model
    if device_in.firmware_version is not None:
        device.firmware_version = device_in.firmware_version
    if device_in.status is not None:
        device.status = device_in.status
    if device_in.farm_id is not None:
        # Check if target farm exists and owned by user
        new_farm_res = await db.execute(select(Farm).where(Farm.id == device_in.farm_id))
        new_farm = new_farm_res.scalars().first()
        if not new_farm:
             raise HTTPException(status_code=404, detail="Target farm not found")
        if current_user.role != "admin" and new_farm.owner_user_id != current_user.id:
             raise HTTPException(status_code=403, detail="Not authorized to move to this farm")
        device.farm_id = device_in.farm_id
    
    # Device Type 3 Configuration Fields
    if device_in.temp_high is not None:
        device.temp_high = device_in.temp_high
    if device_in.temp_low is not None:
        device.temp_low = device_in.temp_low
    if device_in.temp_x is not None:
        device.temp_x = device_in.temp_x
    if device_in.humidity is not None:
        device.humidity = device_in.humidity
    if device_in.humidity_temp is not None:
        device.humidity_temp = device_in.humidity_temp
    if device_in.timer_sec is not None:
        device.timer_sec = device_in.timer_sec

    db.add(device)
    await db.commit()
    await db.refresh(device)
    return device

@router.delete("/{device_id}", response_model=DeviceResponse)
async def delete_device(
    device_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    # Check device exists
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalars().first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
        
    # Check permissions
    farm_res = await db.execute(select(Farm).where(Farm.id == device.farm_id))
    farm = farm_res.scalars().first()
    
    if current_user.role != "admin":
         if not farm or farm.owner_user_id != current_user.id:
             raise HTTPException(status_code=403, detail="Not authorized")

    # Manually cascade delete (Telemetry and Commands)
    from app.models import Telemetry
    # Delete Telemetry
    await db.execute(delete(Telemetry).where(Telemetry.device_id == device_id))
    # Delete Commands
    await db.execute(delete(Command).where(Command.device_id == device_id))

    await db.delete(device)
    await db.commit()
    return device


from app.services.ai_service import ai_service
from app.schemas.device import DeviceAnalysisResponse

@router.post("/{device_id}/analyze", response_model=DeviceAnalysisResponse)
async def analyze_device(
    device_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """
    Analyze device telemetry using AI.
    """
    # Check device exists
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalars().first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
        
    # Check permissions
    farm_res = await db.execute(select(Farm).where(Farm.id == device.farm_id))
    farm = farm_res.scalars().first()
    
    if current_user.role != "admin":
         if not farm or farm.owner_user_id != current_user.id:
             raise HTTPException(status_code=403, detail="Not authorized")

    # Fetch last 50 minutes of telemetry (approx 50 records if 1/min)
    # Using limit=50 for simplicity as per user request "last 50 telemetry data"
    from app.models import Telemetry
    t_query = select(Telemetry).where(Telemetry.device_id == device_id).order_by(Telemetry.ts.desc()).limit(50)
    t_result = await db.execute(t_query)
    telemetry_data = [t.model_dump() for t in t_result.scalars().all()]
    
    if not telemetry_data:
         return {
             "status": "UNKNOWN",
             "temperature_status": "UNKNOWN", 
             "humidity_status": "UNKNOWN",
             "summary_for_farmer": "No telemetry data available for analysis.",
             "recommended_action": "Ensure device is online and sending data."
         }

    # Call AI Service
    # Note: Telemetry is sorted desc (newest first). AI Service might expect chronological? 
    # The prompt says "analyze... telemetry data". Usually chronological is better for time series.
    # Let's reverse it to be chronological.
    telemetry_data.reverse()
    
    analysis = ai_service.analyze_incubator_telemetry(telemetry_data)
    
    return analysis

from sqlalchemy import func
from app.schemas.device import DeviceStatsResponse

@router.get("/{device_id}/stats", response_model=DeviceStatsResponse)
async def get_device_stats(
    device_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """
    Get aggregated temperature and humidity statistics.
    """
    # Check device permissions (borrowing logic from read_device)
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalars().first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
        
    # Check permissions
    farm_res = await db.execute(select(Farm).where(Farm.id == device.farm_id))
    farm = farm_res.scalars().first()
    
    if current_user.role != "admin":
         if not farm or farm.owner_user_id != current_user.id:
             raise HTTPException(status_code=403, detail="Not authorized")

    # Calculate stats
    from app.models import Telemetry
    query = select(
        func.max(Telemetry.temp_c), 
        func.avg(Telemetry.temp_c), 
        func.max(Telemetry.hum_pct), 
        func.avg(Telemetry.hum_pct)
    ).where(Telemetry.device_id == device_id)
    
    stats_res = await db.execute(query)
    # result is a single row with 4 columns
    row = stats_res.first()
    
    if not row:
        return {}
    
    return {
        "max_temp_c": row[0],
        "avg_temp_c": row[1],
        "max_hum_pct": row[2],
        "avg_hum_pct": row[3]
    }
