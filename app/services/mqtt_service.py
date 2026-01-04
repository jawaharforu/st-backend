import asyncio
import json
import logging
from typing import Any, Callable, Optional, Dict
import aiomqtt
from app.core.config import settings

logger = logging.getLogger(__name__)

class MQTTService:
    def __init__(self):
        self.client: Optional[aiomqtt.Client] = None
        self.is_connected = False

    async def start(self):
        self.client = aiomqtt.Client(
            hostname=settings.MQTT_BROKER,
            port=settings.MQTT_PORT,
            # username=settings.MQTT_USERNAME,
            # password=settings.MQTT_PASSWORD
        )
        try:
            await self.client.__aenter__()
            self.is_connected = True
            logger.info("Connected to MQTT Broker")
            # Start subscription loop in background
            asyncio.create_task(self._subscribe_loop())
        except Exception as e:
            logger.error(f"Failed to connect to MQTT: {e}")

    async def stop(self):
        if self.client:
            await self.client.__aexit__(None, None, None)
            self.is_connected = False
            logger.info("Disconnected from MQTT")

    async def publish(self, topic: str, payload: Any, qos: int = 0):
        if not self.is_connected or not self.client:
            logger.warning("MQTT not connected, cannot publish")
            return
        
        if isinstance(payload, dict) or isinstance(payload, list):
            payload = json.dumps(payload)
        
        await self.client.publish(topic, payload, qos=qos)

    async def _subscribe_loop(self):
        # Subscribe to all telemetry topics
        # Topic structure: incubators/{device_id}/telemetry
        topic = "incubators/+/telemetry"
        
        if not self.client:
            return

        await self.client.subscribe(topic, qos=1)
        logger.info(f"Subscribed to {topic}")

        async for message in self.client.messages:
            try:
                payload = message.payload.decode()
                topic_parts = message.topic.value.split("/") 
                # incubators, device_id, telemetry
                if len(topic_parts) == 3:
                    device_id = topic_parts[1]
                    await self.handle_telemetry(device_id, payload)
            except Exception as e:
                logger.error(f"Error processing MQTT message: {e}")

    async def handle_telemetry(self, device_id: str, payload: str):
        from app.services.ingestion import process_telemetry
        await process_telemetry(device_id, payload)

mqtt_service = MQTTService()
