import asyncio
import json
import random
import time
from datetime import datetime
import aiomqtt

BROKER = "localhost"
PORT = 1883

FARM_ID = "FARM-1"
DEVICE_ID = "INC-0001"

async def main():
    try:
        async with aiomqtt.Client(BROKER, PORT) as client:
            print(f"Connected to MQTT Broker at {BROKER}:{PORT}")
            
            while True:
                # Simulate telemetry
                payload = {
                    "ts": datetime.utcnow().isoformat() + "Z",
                    "seq": int(time.time()),
                    "temp_c": round(random.uniform(36.0, 38.0), 2),
                    "hum_pct": round(random.uniform(50.0, 60.0), 1),
                    "heater": random.choice([True, False]),
                    "fan": random.choice([True, False]),
                    "rssi": random.randint(-80, -40)
                }
                
                topic = f"incubators/{FARM_ID}/{DEVICE_ID}/telemetry"
                print(f"Publishing to {topic}: {payload}")
                
                await client.publish(topic, json.dumps(payload), qos=1)
                
                await asyncio.sleep(2)
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
