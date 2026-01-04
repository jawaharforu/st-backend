import asyncio
import aiomqtt

BROKER = "localhost"
PORT = 1883

FARM_ID = "+" # Wildcard or specific
DEVICE_ID = "+" # Wildcard or specific

async def main():
    try:
        async with aiomqtt.Client(BROKER, PORT) as client:
            print(f"Connected to MQTT Broker. Subscribing to commands...")
            
            topic = f"incubators/{FARM_ID}/{DEVICE_ID}/cmd"
            await client.subscribe(topic)
            print(f"Subscribed to {topic}")
            
            async with client.messages() as messages:
                async for message in messages:
                    print(f"\n[RECEIVED] Topic: {message.topic}")
                    print(f"Payload: {message.payload.decode()}")
                    
                    # Here a real device would parse JSON and execute action
                    # And potentially ack back on another topic
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
