import json
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.core.db import engine
from app.models import Telemetry, Device
from app.core.redis import get_redis
from sqlmodel import select

logger = logging.getLogger(__name__)

async def process_telemetry(device_id_str: str, payload_str: str):
    """
    Validate, Store to DB, Publish to Redis
    """
    try:
        data = json.loads(payload_str)
    except json.JSONDecodeError:
        logger.error("Invalid JSON telemetry")
        return

    # Extract fields
    # Expected format: { ts, seq, temp_c, hum_pct, heater, fan, rssi, ... }
    # ts might be ISO string or absent (use now)
    ts_val = datetime.utcnow()
    if "ts" in data:
        try:
            ts_val = datetime.fromisoformat(data["ts"].replace('Z', '+00:00'))
        except:
            pass
            
    # We need to find the internal UUID IDs for device and farm?
    # Or we assume device_id_str is the physical ID (serial) and we map it.
    # Topic has physical ID? Or UUID?
    # User Request: "Topics: incubators/{farm_id}/{device_id}/telemetry"
    # User Example: "device_id": "INC-0001", "farm_id": "FARM-1"
    # These are likely string IDs. We need to look up the UUIDs in Postgres.
    
    async with AsyncSession(engine) as session:
        # Cache this lookup? For now, DB lookup.
        # Find device by physical ID (device_id_str)
        # Note: farm_id_str might be physical farm name or ID.
        # Let's assume device lookup is enough if device_id is unique.
        
        # If the topic sends UUIDs, we can use them directly.
        # But usually MQTT topics use human readable or serials.
        # Let's try to map `device_id` (string) to `Device` record.
        
        stmt = select(Device).where(Device.device_id == device_id_str)
        result = await session.execute(stmt)
        device = result.scalars().first()
        
        if not device:
            logger.warning(f"Unknown device: {device_id_str}")
            return
            
        # Create Telemetry Record
        telemetry = Telemetry(
            ts=ts_val,
            device_id=device.id,
            farm_id=device.farm_id, # Use the DB relation
            seq=data.get("seq", 0),
            temp_c=data.get("temp_c") or data.get("current_temp", 0.0),
            hum_pct=data.get("hum_pct") or data.get("current_humidity", 0.0),
            # New actuator state fields
            primary_heater=data.get("primary_heater"),
            secondary_heater=data.get("secondary_heater"),
            exhaust_fan=data.get("exhaust_fan"),
            sv_valve=data.get("sv_valve"),
            fan=data.get("fan"),
            turning_motor=data.get("turning_motor"),
            limit_switch=data.get("limit_switch"),
            door_light=data.get("door_light"),
            ip=data.get("ip"),
            # Legacy fields
            heater=data.get("heater") or data.get("primary_heater", False),
            motor_state=data.get("motor_state"),
            uptime_s=data.get("uptime_s"),
            rssi=data.get("rssi", 0),
            payload=data
        )
        session.add(telemetry)
        
        # Update Device Last Seen
        device.last_seen = ts_val
        session.add(device)
        
        # Cache IDs before commit (commit expires objects)
        device_uuid = str(device.id)
        farm_uuid = str(device.farm_id) if device.farm_id else None
        device_serial = device.device_id
        
        try:
            await session.commit()
        except IntegrityError:
            logger.warning(f"Duplicate telemetry received for {device_id_str} at {ts_val}")
            await session.rollback()
            return
        
        # Publish to Redis for WebSockets
        # Channel: telemetry:{farm_id} using UUID
        if farm_uuid:
            redis = await get_redis()
            # Publish the enriched data (including internal UUIDs if needed by frontend)
            # Or just forward the payload with some metadata
            msg = {
                "type": "telemetry",
                "device_id": device_uuid,
                "device_serial": device_serial,
                "farm_id": farm_uuid,
                "data": json.loads(telemetry.model_dump_json())
            }
            # redis.publish is async in aioredis/redis-py 4.2+?
            await redis.publish(f"telemetry:{farm_uuid}", json.dumps(msg))
            
            logger.info(f"Ingested telemetry for {device_id_str}")

