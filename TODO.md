# TODO - IoT Predictive Maintenance Platform

## Current Status
- ✅ Docker installed (v20.10.24)
- ✅ Docker-Compose installed (v1.29.2)
- ✅ All 5 service images built successfully
- ⚠️ Service startup sequencing issue - needs fixing

## Outstanding Items

### 1. Fix Docker Startup Sequencing [PRIORITY: HIGH]
**Problem**: Services start too fast, before dependencies are ready
- MQTT Broker needs time to become available
- Simulator tries to connect before MQTT is ready → Connection refused
- Backend needs ML-Service ready first

**Solution Options**:
- [ ] Add retry-logic to simulator (paho-mqtt has built-in reconnect)
- [ ] Add `healthcheck` with proper `depends_on: condition: service_healthy`
- [ ] Use wait-for-it script: https://github.com/vishnubob/wait-for-it
- [ ] Simple approach: Add sleep in entrypoint scripts

**Files to modify**:
- `simulator/sensor_simulator.py` - Add reconnection loop
- `docker-compose.yml` - Re-enable health checks with proper conditions
- Consider adding `entrypoint.sh` wrapper scripts

### 2. Test Full Docker Startup
**After fixing #1**:
```bash
cd /home/michael/develop-privat/iot-predictive-maintenance
sudo docker-compose down --volumes
sudo docker-compose up -d
sleep 30
sudo docker-compose ps
# Should see all 5 containers with "Up" status
```

**Verification**:
- [ ] All 5 containers running: `sudo docker-compose ps`
- [ ] Dashboard accessible: `http://localhost:3000`
- [ ] Backend health: `curl http://localhost:8080/api/health`
- [ ] ML health: `curl http://localhost:5000/health`
- [ ] Simulator publishing data: `sudo docker-compose logs simulator`

### 3. Create GitHub Release with ML Models
**Command**:
```bash
gh auth login
gh release create v1.0.0 \
  --title "ML Model v1.0" \
  ml/models/predictive_model.h5 \
  ml/models/scaler.pkl
```

**Status**: ⏳ Pending (will be needed once docker-compose works)

### 4. Update README for Docker Setup
**Files to update**:
- [ ] Main `README.md` - Add Docker quick start
- [ ] Link to `DOCKER.md` for detailed setup
- [ ] Add screenshot from dashboard (optional but nice for portfolio)

**Sample text**:
```markdown
## Quick Start with Docker

The easiest way to run the entire stack:

```bash
docker-compose up
# Dashboard: http://localhost:3000
```

See [DOCKER.md](DOCKER.md) for detailed setup and troubleshooting.
```

### 5. Commit Everything to Git
**Files to commit**:
- [ ] Dockerfiles (simulator, ml, backend, frontend)
- [ ] docker-compose.yml (fixed version)
- [ ] .dockerignore files
- [ ] DOCKER.md, APPLIKATION.md (English translations)
- [ ] This TODO.md

**Command**:
```bash
git add .
git commit -m "Add Docker orchestration for full-stack deployment"
git push origin main
```

## Notes

### Docker Image Sizes (built successfully)
- Simulator: ~300MB
- Backend: ~30MB
- Frontend: ~50MB
- ML-Service: ~350MB
- MQTT: ~50MB
- **Total**: ~780MB (without models)

### Services Architecture
```
Frontend (React)     → :3000
Backend (Go)         → :8080
ML-Service (Flask)   → :5000
MQTT Broker          → :1883
Simulator (Python)   → (background)
```

### Key Issue Details
When running `sudo docker-compose up -d`:
1. Mosquitto starts (health: starting)
2. Simulator tries to connect immediately → **FAILS** (not ready yet)
3. Backend tries to reach ML-Service → **FAILS** (not ready yet)
4. Frontend nginx can't resolve "backend" DNS → **FAILS** (too early)

This is a classic Docker startup ordering problem. The services need to wait for their dependencies to be truly ready, not just "created".

### Recommended Fix Priority
1. **Quickest fix**: Add sleep/retry in simulator `__init__`
2. **Better solution**: Use proper health checks in docker-compose
3. **Best practice**: Wait-for-it script for production-grade orchestration

## Next Session Checklist
- [ ] Pick one fix approach from #1
- [ ] Implement the fix
- [ ] Test: `docker-compose up` should work cleanly
- [ ] Verify all dashboards/APIs are accessible
- [ ] Create GitHub release (#3)
- [ ] Final git commit
- [ ] Update README with Docker quick start (#4)

---

**Status Last Updated**: 2025-11-02 21:15 UTC
**Session**: Docker Installation & Setup
**Owner**: Michael
