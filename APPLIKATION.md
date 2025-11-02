# IoT Predictive Maintenance Platform - Application Overview

## Overview

This application is an **IoT platform for predictive maintenance of industrial equipment**. It simulates machine degradation in real-time, processes sensor data through a machine learning model, and alerts operators to potential failures before they occur.

## What Does the Application Do?

The system monitors industrial equipment through continuous sensor monitoring (temperature, vibration, pressure), processes this data through an LSTM deep learning model for failure prediction, and provides operators with an interactive dashboard for control and visualization.

### Core Features:

1. **Sensor Simulation**: Generates realistic machine data with progressive degradation
2. **ML-Based Failure Prediction**: LSTM network predicts failures 10 readings in advance
3. **Real-Time Monitoring**: Live dashboard with sensor trends and ML predictions
4. **Interactive Control**: Operators can manually override sensors or simulate degradation scenarios
5. **Hybrid Risk Assessment**: Combines ML predictions with rule-based thresholds

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (React 19.2.0)                      │
│  Dashboard + Control Panel (Tailwind CSS + Recharts Charts)     │
│         WebSocket (ws://localhost:8080/ws)                      │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                    BACKEND (Go 1.x)                             │
│  HTTP API (port 8080) + WebSocket Server                        │
│  - MQTT Subscriber (sensors/+/data)                             │
│  - ML Service Caller (http://localhost:5000/predict)            │
│  - WebSocket Broadcaster                                        │
└──────────┬───────────────────────────────────┬──────────────────┘
           │                                   │
      ┌────▼─────┐                    ┌────────▼──────────┐
      │   MQTT   │                    │  ML Inference     │
      │  Broker  │                    │   (Flask 3.0)     │
      │  (1883)  │                    │  (port 5000)      │
      └────▲─────┘                    │  - LSTM Model     │
           │                          │  - Scaler/Buffer  │
      ┌────┴──────────┐               └───────────────────┘
      │   Simulator   │
      │   (Python)    │
      │ - Machine     │
      │   Degradation │
      │ - Sensor Gen  │
      │ - Control Sub │
      └───────────────┘
```

---

## Core Components

### 1. Sensor Simulator (`simulator/sensor_simulator.py`)

**Purpose**: Simulates industrial machine sensors and publishes MQTT messages

**Key Features**:
- **MQTT Communication**: Publishes to `sensors/{machine_id}/data` every 2 seconds
- **Degradation Simulation**: Gradually increases sensor values to simulate machine wear
- **Manual Override**: Accepts control commands via `control/{machine_id}` MQTT topic
- **Two Operation Modes**:
  - **Auto Mode**: Gradual degradation with configurable speed (default: 0.5)
  - **Manual Mode**: Direct sensor value control via MQTT messages

**Technology Stack**:
- `paho-mqtt>=1.6.1` - MQTT client
- `numpy>=1.24.0` - Numerical computations

**Published Data Structure**:
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

**Control Command Structure** (received via MQTT):
```json
{
  "temperature": 85.0,
  "pressure": 105.0,
  "vibration": 0.9,
  "degradation_speed": 1.0,
  "reset": true
}
```

---

### 2. ML Training & Inference (`ml/`)

#### A. Model Training (`ml/train_model.py`)

**Purpose**: Trains an LSTM neural network to predict machine failures

**Training Data** (100 cycles with 7 failure scenarios):
- **Normal Operation**: 150 readings at stable values (70°C, 0.5mm/s vibration)
- **Gradual Degradation**: Temperature rises from 70°C to 100°C over 120 readings
- **Temperature Spike**: Sudden temperature jump with recovery
- **Vibration Spike**: Sudden vibration increase
- **Pressure Drop**: Gradual pressure decrease
- **Multi-Failure**: Simultaneous temperature and vibration increase
- **Extreme Hardware Failure**: High temperature and vibration spikes (85°C+, 0.6+ mm/s)

**Model Architecture**:
```
LSTM(128 units) → Dropout(0.3)
↓
LSTM(64 units) → Dropout(0.3)
↓
LSTM(32 units) → Dropout(0.2)
↓
Dense(16) → ReLU
↓
Dense(1) → Sigmoid (Binary classification: failure/no failure)
```

**Input Processing**:
- **Sequence Length**: 50 readings (creates 50-timestep sequences)
- **Features**: Temperature, Vibration, Pressure (3 dimensions)
- **Scaling**: MinMaxScaler normalizes to [0,1] range
- **Prediction Task**: Classify whether failure occurs within next 10 readings

**Training Details**:
- **Optimizer**: Adam
- **Loss**: Binary Crossentropy
- **Metrics**: Accuracy, Precision, Recall
- **Callbacks**: Early Stopping (patience=10), Learning Rate Reduction
- **Train/Test Split**: 80/20
- **Epochs**: Up to 50 (with early stopping)

**Output Files**:
- `models/predictive_model.h5` - Trained Keras model
- `models/scaler.pkl` - MinMaxScaler for data normalization

**Technology Stack**:
- `tensorflow>=2.13.0`, `keras>=2.13.1` - Deep learning
- `scikit-learn>=1.3.0` - Preprocessing & utilities
- `pandas>=2.0.3` - Data handling
- `joblib>=1.3.0` - Model serialization

---

#### B. Inference Service (`ml/inference_service.py`)

**Purpose**: Flask REST API for real-time failure predictions

**Endpoints**:
- `GET /health` - Service health check
- `POST /predict` - Accept sensor reading, return failure prediction
- `POST /reset` - Clear prediction buffer

**Prediction Logic** (Hybrid Approach):

1. **ML-Based Score**:
   - Maintains a rolling buffer of 50 raw sensor readings
   - When buffer reaches 50, scales data and passes to LSTM
   - Returns 0.0-1.0 failure probability

2. **Rule-Based Score**:
   - Temperature > 85°C → 0.9 risk
   - Vibration > 1.0 mm/s → 0.9 risk
   - Pressure < 70 or > 120 PSI → 0.9 risk
   - Otherwise → 0.0 risk

3. **Final Prediction**: `max(ml_prediction, rule_based_score)`

4. **Risk Levels**:
   - `> 0.75`: Critical
   - `0.5-0.75`: Warning
   - `< 0.5`: Normal
   - Initializing: Until 50 readings collected

**Response Format**:
```json
{
  "prediction": 0.75,
  "ml_prediction": 0.65,
  "rule_based": 0.9,
  "risk_level": "critical",
  "buffer_size": 50,
  "confidence": 75.0
}
```

**Technology Stack**:
- `flask>=3.0`, `flask-cors>=4.0` - REST API
- TensorFlow/Keras - Model inference
- scikit-learn - Data scaling

---

### 3. Go Backend (`backend/main.go`)

**Purpose**: Central data aggregation, MQTT subscription, ML service integration, and WebSocket broadcasting

**Core Responsibilities**:
1. **MQTT Connection**: Subscribes to `sensors/+/data` (wildcard pattern)
2. **ML Integration**: Calls Python Flask service for each sensor reading
3. **Buffer Management**: Maintains last 100 sensor readings in memory
4. **WebSocket Broadcasting**: Real-time push to all connected frontend clients
5. **HTTP API**: REST endpoints for data retrieval and control commands

**HTTP Endpoints**:
- `GET /api/health` - Backend health and status
- `GET /api/sensors/latest` - Last 50 sensor readings
- `POST /api/control` - Publish control commands to MQTT topic `control/machine_001`
- `GET /ws` - WebSocket upgrade for real-time streaming

**Message Flow**:
1. MQTT message arrives → `mqttMessageHandler()`
2. Parse SensorData JSON
3. Call `getMLPrediction()` via HTTP POST to Flask service
4. Attach ML prediction to sensor data
5. Store in buffer (max 100 readings)
6. Broadcast via WebSocket to all connected clients
7. Log to console

**Data Structures**:
```go
type SensorData struct {
    MachineID    string      // e.g., "machine_001"
    Timestamp    string      // ISO-8601 format
    Temperature  float64     // Celsius
    Vibration    float64     // mm/s
    Pressure     float64     // PSI
    Status       string      // normal|warning|critical
    Degradation  float64     // 0-100 (simulator state)
    Mode         string      // auto|manual
    MLPrediction *MLResponse // Pointer to ML result
}

type MLResponse struct {
    Prediction   float64 // 0.0-1.0 failure probability
    MLPrediction float64 // Pure ML score
    RuleBased    float64 // Rule-based threshold score
    RiskLevel    string  // critical|warning|normal|initializing
    BufferSize   int     // Number of readings in ML buffer
}
```

**Technology Stack**:
- `github.com/eclipse/paho.mqtt.golang` - MQTT client
- `github.com/gorilla/mux` - HTTP routing
- `github.com/gorilla/websocket` - WebSocket support
- `github.com/rs/cors` - CORS middleware

---

### 4. React Frontend (`frontend/src/`)

**Purpose**: Real-time monitoring dashboard with sensor visualization and simulator control

#### A. MainView (`pages/MainView.jsx`)
- Two-column layout: Dashboard (70%) + Control Panel (30%)
- Responsive flex container with scrolling

#### B. Dashboard (`pages/Dashboard.jsx`)

**Features**:
- **Connection Status**: Real-time WebSocket indicator (green/red dot)
- **ML Alert Box**: Shows critical/warning alerts with confidence score
- **Metric Cards** (4 columns):
  - Temperature (Celsius) with color coding
  - Vibration (mm/s) with thresholds
  - Pressure (PSI)
  - ML Risk Score (0-100%)
- **Line Charts** (Recharts library):
  - Temperature trend over time
  - Vibration trend over time
  - Last 50 readings displayed
- **Mode Indicator**: Shows if simulator is in auto or manual mode

**Color Coding**:
- Green: Normal (Temperature <80°C, Vibration <0.8)
- Yellow: Warning (80-85°C, 0.8-1.0 mm/s)
- Red: Critical (>85°C, >1.0 mm/s)
- Blue: Initializing (ML buffer collecting data)

**Real-Time Updates**:
- WebSocket connection to `ws://localhost:8080/ws`
- Maintains rolling 50-reading buffer for charts
- Auto-updates metric cards on new sensor readings

#### C. Control Panel (`pages/ControlPanel.jsx`)

**Features**:

1. **Connection Status**: Checks backend health via `GET /api/health`

2. **Mode Toggle**:
   - Auto Mode: Simulator runs with gradual degradation
   - Manual Control: Override individual sensor values

3. **Manual Sliders** (displayed when in manual mode):
   - Temperature: 60-110°C (with thresholds marked)
   - Vibration: 0.3-3.0 mm/s
   - Pressure: 60-140 PSI
   - Degradation Speed: 0-5x multiplier

4. **Quick Scenario Presets** (4 buttons):
   - Normal: 70°C, 0.5 mm/s, 100 PSI
   - Warning: 82°C, 0.85 mm/s, 105 PSI
   - Critical: 92°C, 1.2 mm/s, 115 PSI
   - Failure: 98°C, 1.5 mm/s, 120 PSI

5. **Apply Button**:
   - In auto mode: Sends `{"reset": true}` to reset simulator
   - In manual mode: Sends sensor overrides to backend
   - Backend publishes control message to MQTT topic

6. **Status Warnings**: Alerts if backend is unreachable

**Technology Stack**:
- `react@19.2.0` - UI framework
- `react-router-dom@7.9.4` - Routing
- `recharts@3.2.1` - Charts
- `tailwindcss@3.4.1` - Styling

---

## Data Flow

```
1. SENSOR SIMULATOR (Python)
   ↓ (MQTT publish: sensors/machine_001/data)
   ↓
2. MQTT BROKER (localhost:1883)
   ↓ (MQTT subscribe)
   ↓
3. GO BACKEND (port 8080)
   ├→ getMLPrediction() ──→ PYTHON ML SERVICE (port 5000)
   │                           ↓
   │                        LSTM Inference
   │                           ↓
   │                        Return risk_level
   │
   ├→ Store in buffer (max 100)
   │
   └→ Broadcast via WebSocket
       ↓
4. REACT FRONTEND (browser)
   ├→ Update charts
   ├→ Update metric cards
   └→ Display alerts if critical
```

---

## Technology Stack Overview

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Simulator** | Python 3.x | - | MQTT-based sensor simulation |
| **ML Training** | TensorFlow/Keras | 2.13.0 | LSTM deep learning |
| **ML Inference** | Flask | 3.0 | REST API for predictions |
| **Backend** | Go | 1.x | Data aggregation & WebSocket |
| **Frontend** | React | 19.2.0 | Real-time dashboard |
| **Message Bus** | MQTT (Mosquitto) | - | Device-to-backend communication |
| **Charts** | Recharts | 3.2.1 | Time-series visualization |
| **Styling** | Tailwind CSS | 3.4.1 | UI framework |
| **Dependencies** | paho-mqtt, numpy | Various | Supporting libraries |

---

## How Components Work Together

1. **Sensor Simulator** generates realistic equipment telemetry every 2 seconds
2. **MQTT Broker** routes messages between simulator and backend
3. **Go Backend** receives sensor data and immediately calls **Python ML Service**
4. **ML Service** maintains a buffer of 50 readings and runs LSTM inference
5. **Hybrid Risk Score** combines ML prediction (65% confidence) with rule-based thresholds (manual triggers at critical values)
6. **Go Backend** augments sensor data with ML prediction and broadcasts via WebSocket
7. **React Dashboard** receives real-time updates and displays:
   - Color-coded metric cards (green/yellow/red)
   - Live line charts of temperature and vibration trends
   - Alert banners for critical conditions
8. **Control Panel** allows operators to:
   - Simulate scenarios (normal/warning/critical/failure)
   - Manually control individual sensors
   - Reset to automatic degradation mode

---

## Design Patterns

**1. Hybrid Risk Assessment**
- ML for complex pattern detection (temporal trends in 50-reading windows)
- Rule-based for immediate threshold violations (T>85°C triggers instant alert)
- `final_risk = max(ml_score, rule_based_score)` prevents false negatives

**2. Stateful Prediction Buffer**
- ML service maintains rolling 50-reading window (LSTM requirement)
- Allows continuous real-time prediction without re-training
- Buffer reset on `/reset` endpoint

**3. Pub-Sub Architecture**
- Simulator publishes sensor data
- Backend subscribes to all machine topics (`sensors/+/data`)
- Frontend subscribes to WebSocket stream
- Decoupled, scalable messaging

**4. Graceful Degradation**
- If ML service unavailable → rule-based scoring continues
- If MQTT unavailable → backend logs error but stays operational
- If WebSocket fails → frontend falls back to polling

---

## Project Status

**Implemented** (Production-Ready):
- Sensor simulator with degradation algorithm
- LSTM model training pipeline
- Flask inference service
- Go backend with MQTT + WebSocket
- React dashboard with real-time updates
- Control panel with manual override

**Planned**:
- Advanced analytics and failure prediction models
- Multi-machine monitoring
- Predictive maintenance alerts
- Historical data persistence
- API documentation

---

## Deployment Architecture

**Required Services**:
1. **MQTT Broker** (Mosquitto) on `localhost:1883`
2. **Python ML Service** on `localhost:5000`
3. **Go Backend** on `localhost:8080`
4. **React Frontend** on `localhost:3000` (development) or served by backend

**Environment Variables**: None required (hardcoded for development)

**Startup Order**:
1. Start MQTT broker
2. Start Python Flask ML service
3. Start Go backend
4. Start React frontend (or connect browser to backend)
5. Start Python sensor simulator

---

## Summary

This IoT predictive maintenance platform demonstrates a complete modern full-stack system for real-time equipment monitoring with machine learning-powered failure prediction, combining Python (ML), Go (backend), and React (frontend) in a production-capable architecture.
