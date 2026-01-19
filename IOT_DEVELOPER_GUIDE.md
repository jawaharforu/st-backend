# IoT Developer Guide - Smart Incubator

## Overview

This guide explains how to integrate your ESP32/Arduino/IoT device with the Smart Incubator backend via MQTT.

---

## Connection Details

| Parameter | Value |
|-----------|-------|
| **MQTT Broker** | `api.eonoia.cloud` (or your server IP) |
| **Port** | `1883` (TCP) |
| **Protocol** | MQTT 3.1.1 / 5.0 |
| **Authentication** | Anonymous (enabled) |

---

## Topics

### Telemetry (Device → Server)
```
incubators/{device_id}/telemetry
```

### Commands (Server → Device)
```
incubators/{device_id}/cmd
```

> **Note:** `device_id` must match the ID registered in the database (e.g., `INC-001`)

---

## Telemetry Payload

Publish sensor data to: `incubators/{device_id}/telemetry`

```json
{
  "temp_c": 99.5,
  "hum_pct": 65.2,
  "primary_heater": true,
  "secondary_heater": false,
  "exhaust_fan": true,
  "fan": true,
  "sv_valve": false,
  "turning_motor": false,
  "limit_switch": true,
  "door_light": false,
  "motor_state": "idle",
  "uptime_s": 3600,
  "ip": "192.168.1.100"
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `temp_c` | float | Temperature in Fahrenheit (displayed as °F) |
| `hum_pct` | float | Humidity percentage (0-100) |
| `primary_heater` | bool | Primary heater ON/OFF state |
| `secondary_heater` | bool | Secondary heater ON/OFF state |
| `exhaust_fan` | bool | Exhaust fan ON/OFF state |
| `fan` | bool | Main fan ON/OFF state |
| `sv_valve` | bool | Solenoid valve ON/OFF state |
| `turning_motor` | bool | Egg turning motor ON/OFF state |
| `limit_switch` | bool | Limit switch triggered state |
| `door_light` | bool | Door light ON/OFF state |
| `motor_state` | string | Motor state: `idle`, `turning_left`, `turning_right` |
| `uptime_s` | int | Device uptime in seconds |
| `ip` | string | Device IP address |

---

## Command Payload

Subscribe to: `incubators/{device_id}/cmd`

```json
{
  "cmd_id": "550e8400-e29b-41d4-a716-446655440000",
  "cmd": "PRIMARY_HEATER",
  "params": { "state": true },
  "ts": "2026-01-04T14:05:00Z"
}
```

### Available Commands

| Command | Params | Description |
|---------|--------|-------------|
| `PRIMARY_HEATER` | `{ "state": true/false }` | Toggle primary heater |
| `SECONDARY_HEATER` | `{ "state": true/false }` | Toggle secondary heater |
| `DOOR_LIGHT` | `{ "state": true/false }` | Toggle door light |
| `SV_VALVE` | `{ "state": true/false }` | Toggle solenoid valve |
| `TURN_MOTOR` | `{ "dir": "left"/"right" }` | Rotate egg tray |
| `REBOOT` | `{}` | Reboot device |

---

## ESP32 Example (Arduino)

```cpp
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

const char* ssid = "YOUR_WIFI";
const char* password = "YOUR_PASSWORD";
const char* mqtt_server = "api.eonoia.cloud";
const char* device_id = "INC-001";

WiFiClient espClient;
PubSubClient client(espClient);

void setup_wifi() {
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
}

void callback(char* topic, byte* payload, unsigned int length) {
  StaticJsonDocument<256> doc;
  deserializeJson(doc, payload, length);
  
  const char* cmd = doc["cmd"];
  JsonObject params = doc["params"];
  
  if (strcmp(cmd, "PRIMARY_HEATER") == 0) {
    bool state = params["state"];
    digitalWrite(HEATER_PIN, state ? HIGH : LOW);
  }
  // Handle other commands...
}

void reconnect() {
  while (!client.connected()) {
    if (client.connect(device_id)) {
      char cmdTopic[50];
      sprintf(cmdTopic, "incubators/%s/cmd", device_id);
      client.subscribe(cmdTopic);
    } else {
      delay(5000);
    }
  }
}

void publishTelemetry() {
  StaticJsonDocument<512> doc;
  doc["temp_c"] = readTemperature();
  doc["hum_pct"] = readHumidity();
  doc["primary_heater"] = digitalRead(HEATER_PIN);
  doc["fan"] = digitalRead(FAN_PIN);
  doc["uptime_s"] = millis() / 1000;
  doc["ip"] = WiFi.localIP().toString();
  
  char buffer[512];
  serializeJson(doc, buffer);
  
  char topic[50];
  sprintf(topic, "incubators/%s/telemetry", device_id);
  client.publish(topic, buffer);
}

void loop() {
  if (!client.connected()) reconnect();
  client.loop();
  
  static unsigned long lastPublish = 0;
  if (millis() - lastPublish > 5000) {  // Every 5 seconds
    publishTelemetry();
    lastPublish = millis();
  }
}
```

---

## Testing with mosquitto_pub

```bash
# Publish test telemetry
mosquitto_pub -h api.eonoia.cloud -p 1883 \
  -t "incubators/INC-001/telemetry" \
  -m '{"temp_c":99.5,"hum_pct":65.2,"primary_heater":true,"fan":true}'

# Subscribe to commands
mosquitto_sub -h api.eonoia.cloud -p 1883 \
  -t "incubators/INC-001/cmd" -v
```

---

## Recommended Publishing Interval

- **Telemetry:** Every 5-10 seconds
- **On state change:** Immediate publish

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Connection refused | Check firewall, ensure port 1883 is open |
| No data in dashboard | Verify `device_id` matches database entry |
| Commands not received | Check subscription topic format |

---

## Support

- **EMQX Dashboard:** http://your-server:18083 (admin/public)
- **API Docs:** https://api.eonoia.cloud/docs
