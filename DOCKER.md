# Docker Setup - IoT Predictive Maintenance Platform

This document explains how the application runs in Docker and how to deploy it.

## Quick Start (TL;DR)

```bash
# 1. Clone Repository
git clone https://github.com/michael-hanf/iot-predictive-maintenance
cd iot-predictive-maintenance

# 2. Start all services
docker-compose up

# 3. Open in browser
http://localhost:3000
```

That's it! The application starts automatically. The ML model is downloaded on first startup.

---

## What Happens During Startup?

### Phase 1: Services Start (~ 5-10 seconds)
```
docker-compose up

[+] Building 45.3s (...)
[+] Creating iot-mosquitto ... done
[+] Creating iot-ml-service ... done
[+] Creating iot-backend ... done
[+] Creating iot-simulator ... done
[+] Creating iot-frontend ... done
```

### Phase 2: ML Model is Downloaded (~ 30-60 seconds, first startup only)
```
ml-service_1 | ============================================================
ml-service_1 | ML Model not found locally
ml-service_1 | ============================================================
ml-service_1 | Downloading predictive_model.h5...
ml-service_1 | Download progress: 100%
ml-service_1 | ✓ predictive_model.h5 downloaded successfully
```

### Phase 3: System Ready
```
frontend_1   | Compiled successfully!
backend_1    | ML Service available at http://ml-service:5000
simulator_1  | Publishing sensor data...
```

→ Open browser at `http://localhost:3000`
→ Dashboard shows live data

---

## Service Details

### MQTT Broker (mosquitto)
- **Port**: 1883 (internal), 9001 (WebSocket)
- **Status**: Central message bus
- **Logs**: `docker-compose logs mosquitto`

### ML Inference Service (Python Flask)
- **Port**: 5000
- **Status**: ML predictions ready
- **Logs**: `docker-compose logs ml-service`
- **Health Check**: http://localhost:5000/health
- **Note**: Loads models on startup (first seconds/minutes)

### Backend Service (Go)
- **Port**: 8080
- **Status**: REST API + WebSocket
- **Logs**: `docker-compose logs backend`
- **Health Check**: http://localhost:8080/api/health
- **Endpoints**:
  - `GET /api/health` - Backend status
  - `GET /api/sensors/latest` - Last 50 sensor readings
  - `POST /api/control` - Send simulator control commands
  - `GET /ws` - WebSocket for live updates

### Sensor Simulator (Python)
- **Status**: Runs in background
- **Logs**: `docker-compose logs simulator`
- **Function**: Publishes sensor data every 2 seconds via MQTT

### Frontend (React + Nginx)
- **Port**: 3000
- **URL**: http://localhost:3000
- **Logs**: `docker-compose logs frontend`
- **Status**: Real-time monitoring dashboard with charts

---

## Useful Commands

### View Logs
```bash
# All service logs
docker-compose logs -f

# ML service only
docker-compose logs -f ml-service

# Backend only
docker-compose logs -f backend

# Simulator only
docker-compose logs -f simulator
```

### Stop / Restart Services
```bash
# Stop everything
docker-compose down

# Restart everything
docker-compose restart

# Restart specific service
docker-compose restart simulator

# Delete containers and rebuild
docker-compose down --volumes
docker-compose build --no-cache
docker-compose up
```

### Check Status
```bash
# All containers and status
docker-compose ps

# Check specific service
docker-compose ps ml-service
```

### Access Container Shell
```bash
# Shell in backend container
docker-compose exec backend sh

# Python REPL in ML service
docker-compose exec ml-service python

# Shell in frontend container
docker-compose exec frontend sh
```

### Logs and Monitoring
```bash
# Live logs with timestamps
docker-compose logs -f --timestamps

# Last 50 lines only
docker-compose logs -f --tail=50

# Docker system stats
docker stats
```

---

## Troubleshooting

### Problem: "docker-compose: command not found"
**Solution**: Docker Compose is not installed. Install Docker Desktop (includes docker-compose).

### Problem: Port 3000 / 8080 / 5000 already in use
**Solution**: Another application is using the same port. Options:
```bash
# 1. Stop other application
# 2. Change ports in docker-compose.yml:
# Example: Port 8080 → 8081
ports:
  - "8081:8080"
```

### Problem: ML service doesn't become ready
**Check logs**:
```bash
docker-compose logs ml-service
```

**If download fails**:
- Check internet connection
- Is GitHub release URL correct? (see `ml/inference_service.py` lines 19-20)
- Manually download models: see "Offline Setup" below

### Problem: Frontend shows "Cannot reach backend"
**Check**:
```bash
# Is backend running?
docker-compose ps backend

# Logs:
docker-compose logs backend

# Health check:
curl http://localhost:8080/api/health
```

### Problem: Simulator not sending data
**Check**:
```bash
# Is simulator running?
docker-compose ps simulator

# Is MQTT broker running?
docker-compose ps mosquitto

# Logs:
docker-compose logs simulator
```

---

## Advanced: Custom Ports

If you want different ports, edit `docker-compose.yml`:

```yaml
# Example: Backend on 8081 instead of 8080
backend:
  ports:
    - "8081:8080"  # <-- Change this
```

Then:
```bash
docker-compose down
docker-compose up
```

---

## Advanced: Environment Variables

Services use these environment variables (set in `docker-compose.yml`):

### ML Service
- `FLASK_ENV`: `production` (no debug messages)
- GitHub URLs: `ml/inference_service.py` lines 19-20

### Backend
- `MQTT_BROKER`: `mosquitto:1883` (MQTT broker address)
- `ML_SERVICE_URL`: `http://ml-service:5000` (ML inference service)

### Simulator
- `MQTT_BROKER`: `mosquitto` (MQTT broker)
- `MQTT_PORT`: `1883` (MQTT port)
- `MACHINE_ID`: `machine_001` (machine identifier)

### Frontend
- `REACT_APP_API_URL`: `http://localhost:8080` (backend URL for browser)

---

## Advanced: Offline Setup

If you need to work without internet:

### 1. Manually Download Models

On a machine with internet:
```bash
# Download from GitHub release
curl -L https://github.com/michael-hanf/iot-predictive-maintenance/releases/download/v1.0.0/predictive_model.h5 \
  -o predictive_model.h5

curl -L https://github.com/michael-hanf/iot-predictive-maintenance/releases/download/v1.0.0/scaler.pkl \
  -o scaler.pkl
```

### 2. Copy to Your Project
```bash
mkdir -p ml/models
cp predictive_model.h5 ml/models/
cp scaler.pkl ml/models/
```

### 3. docker-compose up
```bash
docker-compose up
# ML service loads models locally, no internet needed
```

---

## Advanced: Build Individual Images

If you only want to build one service:

```bash
# Build backend
docker build -f backend/Dockerfile -t iot-backend:latest .

# Build ML service
docker build -f ml/Dockerfile -t iot-ml:latest .

# Build frontend
docker build -f frontend/Dockerfile -t iot-frontend:latest .

# Build simulator
docker build -f simulator/Dockerfile -t iot-simulator:latest .
```

---

## Performance & Sizes

### Image Sizes (Approximate)
| Service | Size |
|---------|------|
| Simulator | ~300MB |
| Backend | ~30MB |
| Frontend | ~50MB |
| ML (without model) | ~350MB |
| MQTT | ~50MB |
| **Total** | **~780MB** |
| ML Model (download) | ~500MB |

### Memory Usage (Running)
| Service | RAM |
|---------|-----|
| Simulator | ~50MB |
| Backend | ~30MB |
| Frontend | ~20MB |
| ML Service | ~400MB (TensorFlow) |
| MQTT | ~20MB |
| **Total** | **~520MB** |

### Disk Usage (after `docker-compose up`)
- Built images: ~780MB
- Downloaded model: ~500MB
- Docker volumes: ~20MB
- **Total**: ~1.3GB

---

## CI/CD with Docker

If you want automatic deployment later:

### GitHub Actions Example
```yaml
name: Docker Build

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: docker/setup-buildx-action@v2
      - uses: docker/build-push-action@v4
        with:
          context: .
          file: ./ml/Dockerfile
          push: true
          tags: ${{ secrets.DOCKER_REGISTRY }}/iot-ml:latest
```

---

## Docker Compose Override (Local Development)

If you want to develop locally, create `docker-compose.override.yml`:

```yaml
version: '3.9'

services:
  backend:
    volumes:
      - ./backend:/app
    command: go run main.go  # Auto-reload

  simulator:
    volumes:
      - ./simulator:/app
```

Then `docker-compose up` automatically uses these overrides for local development.

---

## Further Information

- **Application Architecture**: see `APPLIKATION.md`
- **ML Training**: see `ml/train_model.py`
- **Backend API**: see `backend/main.go`
- **Frontend Code**: see `frontend/src/`

---

## Support

If you encounter issues:
1. Check logs: `docker-compose logs -f`
2. Search this document (Troubleshooting above)
3. Create GitHub issue: https://github.com/michael-hanf/iot-predictive-maintenance/issues
