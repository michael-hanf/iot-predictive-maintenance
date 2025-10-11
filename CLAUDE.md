# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Real-time IoT predictive maintenance platform with ML-based failure prediction, interactive sensor control, and live monitoring dashboard. The system simulates industrial sensor data via MQTT, processes it for anomaly detection, and provides real-time visualization.

## Architecture

The project follows a multi-component architecture:

- **simulator/** - Python-based MQTT sensor simulator that generates temperature, vibration, and pressure readings
- **backend/** - (Planned) Backend service for data ingestion, processing, and API endpoints
- **frontend/** - (Planned) Real-time monitoring dashboard
- **ml/** - (Planned) Machine learning models for predictive maintenance

### Sensor Simulator

The simulator (`simulator/sensor_simulator.py`) is the core component currently implemented:

- Publishes sensor data to MQTT topics: `sensors/{machine_id}/data`
- Subscribes to control commands on: `control/{machine_id}`
- Simulates gradual machine degradation with configurable speed
- Supports manual override of sensor values (temperature, pressure, vibration)
- Two operation modes:
  - **Auto mode**: Simulates natural degradation over time
  - **Manual mode**: Allows external control via MQTT messages

**Control Commands Structure** (published to `control/{machine_id}`):
```json
{
  "temperature": 85.0,      // Optional: override temperature
  "pressure": 105.0,        // Optional: override pressure
  "vibration": 0.9,         // Optional: override vibration
  "degradation_speed": 1.0, // Optional: control degradation rate
  "reset": true             // Optional: reset to normal operation
}
```

**Sensor Data Structure** (published to `sensors/{machine_id}/data`):
```json
{
  "machine_id": "machine_001",
  "timestamp": "ISO-8601",
  "temperature": 72.5,
  "vibration": 0.6,
  "pressure": 98.3,
  "status": "normal|warning|critical",
  "degradation": 25.0,
  "mode": "auto|manual"
}
```

## Running the Simulator

```bash
# Start the simulator (requires MQTT broker running on localhost:1883)
python simulator/sensor_simulator.py
```

The simulator expects an MQTT broker (e.g., Mosquitto) running on `localhost:1883`. It will:
- Connect to the broker
- Start publishing sensor data every 2 seconds
- Listen for control commands
- Gradually increase degradation until reset or manually controlled

## Development Requirements

The simulator requires:
- Python 3.x
- `paho-mqtt` - MQTT client library
- `numpy` - Numerical computations

Install with: `pip install paho-mqtt numpy`
