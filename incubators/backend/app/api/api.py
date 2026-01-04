from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, farms, devices, telemetry, websocket, firmware

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(farms.router, prefix="/farms", tags=["farms"])
api_router.include_router(devices.router, prefix="/devices", tags=["devices"]) 
api_router.include_router(telemetry.router, tags=["telemetry"])
api_router.include_router(websocket.router, tags=["websocket"])
api_router.include_router(firmware.router, prefix="/firmware", tags=["firmware"])
