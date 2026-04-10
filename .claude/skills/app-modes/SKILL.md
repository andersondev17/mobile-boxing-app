---
name: app-modes
description: Apply this skill when starting, configuring, or troubleshooting the app's Docker services, or when deciding which services to run for a specific task. Contains the 5 light modes (auth/smartwatch/technique/catalog/full) and their environment variables. Trigger on: "start the app", "run technique mode", "light mode", "EXPO_PUBLIC_MODE", "BACKEND_MODULES", "docker compose up", "which services do I need", "app mode", "start only ML", "run only auth".
---

# App Modes — mobile-boxing-app

## Why modes exist
The dev machine has 8GB RAM. Running the full stack (MongoDB + Kafka + Redis + backend) consumes ~3.5GB. Some tasks only need a subset. Modes prevent unnecessary memory pressure.

## 5 Available Modes

### `auth` — Authentication development
```bash
EXPO_PUBLIC_MODE=auth BACKEND_MODULES=auth
docker-compose up mongodb backend
```
Services: MongoDB + backend
Use for: working on login/register/OAuth flows, JWT logic

---

### `smartwatch` — Wearable integration
```bash
EXPO_PUBLIC_MODE=smartwatch BACKEND_MODULES=health
docker-compose up mongodb redis kafka backend
```
Services: MongoDB + Redis + Kafka + backend
Use for: Kafka producers/consumers, smartwatch telemetry, Redis buffer

---

### `technique` — ML/inference development (most common for Phase 1)
```bash
EXPO_PUBLIC_MODE=technique BACKEND_MODULES=ml
docker-compose up mongodb redis backend
```
Services: MongoDB + Redis + backend (NO Kafka — saves ~600MB)
Use for: DTW pipeline, WebSocket, feature extractor, feedback engine

---

### `catalog` — Exercise catalog
```bash
EXPO_PUBLIC_MODE=catalog BACKEND_MODULES=catalog
docker-compose up mongodb backend
```
Services: MongoDB + backend
Use for: exercise CRUD, seeding, category/difficulty management

---

### `full` — All services
```bash
EXPO_PUBLIC_MODE=full BACKEND_MODULES=all
docker-compose up
```
Services: All (MongoDB + Mongo Express + Redis + Kafka + backend)
Use for: Integration testing, full app demo

---

## How to set env vars (Windows)

```bash
# PowerShell
$env:EXPO_PUBLIC_MODE="technique"; $env:BACKEND_MODULES="ml"; docker-compose up mongodb redis backend

# Git Bash / WSL
EXPO_PUBLIC_MODE=technique BACKEND_MODULES=ml docker-compose up mongodb redis backend
```

## Mobile mode detection (apps/mobile/lib/config/env.ts)

The mobile app reads `EXPO_PUBLIC_MODE` at build time:
```typescript
const mode = process.env.EXPO_PUBLIC_MODE ?? "full"
// Conditionally renders features based on mode
```

## Backend module gating (to implement in main.py)

Currently all routes are always loaded. To support module gating:
```python
import os
modules = os.getenv("BACKEND_MODULES", "all").split(",")

if "all" in modules or "ml" in modules:
    app.include_router(boxing_router)

if "all" in modules or "health" in modules:
    app.include_router(kafka_router)
```

## Memory usage by service (approximate)
| Service | RAM |
|---------|-----|
| MongoDB 7 | ~400MB |
| Redis 7 | ~50MB (256MB limit) |
| Kafka 1-node KRaft | ~600MB |
| Mongo Express | ~100MB |
| Backend FastAPI | ~300MB |
| **Total full mode** | **~1.45GB** |

## Health checks before starting
```bash
# Check all containers are healthy
docker-compose ps

# Test backend is up
curl http://localhost:8000/boxing/status

# Test MongoDB
docker exec boxing-mongodb mongosh --eval "db.adminCommand('ping')"

# Test Redis
docker exec boxing-redis redis-cli ping
```
