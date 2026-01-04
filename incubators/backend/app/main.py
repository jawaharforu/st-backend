from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.redis import init_redis, close_redis
from app.services.mqtt_service import mqtt_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_redis()
    await mqtt_service.start()
    yield
    # Shutdown
    await mqtt_service.stop()
    await close_redis()

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.get("/")
async def root():
    return {"message": "Welcome to Smart Incubator API", "docs": "/docs"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

from app.api.api import api_router
app.include_router(api_router, prefix=settings.API_V1_STR)
