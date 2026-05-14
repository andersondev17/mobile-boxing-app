---
name: systematic-debugging
description: Apply this skill when diagnosing bugs, unexpected behavior, or errors in the boxing app. Provides structured root-cause analysis using the 5 Whys method, decision trees by layer, and known error patterns. Trigger on: "bug", "error", "not working", "unexpected behavior", "debug", "why is X happening", "broken", "failing", "crash", "exception", "score is always 0", "websocket timeout", "kafka not working", "connection refused".
---

# Systematic Debugging — mobile-boxing-app

## Method: The 5 Whys

Never stop at the first symptom. Keep asking "why?" until you reach the actionable root cause.

```
Symptom: "Score is always 0.0"
Why 1: FeedbackEngine.compare() returns None
Why 2: self.mean is None (baseline not set)
Why 3: BoxingAnalyticsService.load_baseline() was never called
Why 4: The /boxing/baseline endpoint was never hit
Root cause: Client connects to WebSocket before loading baseline
Fix owner: backend-builder + mobile-dev
```

## Decision Tree by Layer

### Mobile (React Native / Expo)
1. Is the app crashing? → Check Metro bundler logs + Expo dev tools
2. WebSocket not connecting? → Check `EXPO_PUBLIC_LOCAL_IP` in `.env`, verify backend is up
3. Camera not starting? → Permissions not granted, or TFLite model not loaded
4. Auth failing? → Token expired? Call `refreshToken()`, or check `EXPO_PUBLIC_GOOGLE_CLIENT_ID`
5. TypeScript error? → Check interfaces in `interfaces/interfaces.d.ts`

```bash
# Mobile logs
npx expo start --dev-client
# Look for red screen with stack trace
```

### WebSocket Layer
1. Response > 100ms? → ML inference blocking event loop, move to `asyncio.create_task()`
2. Disconnects immediately? → Auth token not passed, or server throws on connect
3. No feedback returned? → Baseline not loaded, or landmarks shape wrong
4. "frame_deprecated" error? → Mobile sending base64 instead of landmarks

```python
# Quick check: is the WebSocket running inference synchronously?
# Look for: await dtw_scorer.score_window(...)  # BAD
# Should be: asyncio.create_task(run_inference(...))  # GOOD
```

### FastAPI Backend
1. 500 on startup? → Missing env var, MongoDB not up, model file not found
2. 403 on biometric endpoint? → Consent not granted for user
3. Beanie query returns None? → Wrong field name, or `await` missing
4. Import error? → Circular import in models/, check `__init__.py`

```bash
# Backend logs
docker-compose logs -f backend
# or
uvicorn main:app --reload  # look for startup errors
```

### ML Service
1. Score always 0? → Check in order:
   - `boxing_service.get_baseline()` is not None
   - `feature_extractor.extract_features()` returns non-None dict
   - `feedback_engine.mean` is not None
   - Window buffer has 30 frames (`window_buffer.push_frame()` returns non-None)
2. Features always None? → Landmark visibility < 0.65, or landmarks list < 16 elements
3. DTW slow? → Window size wrong (must be exactly 30), or baseline has too many windows

```python
# Quick diagnostic: add to WebSocket handler temporarily
print(f"DEBUG: baseline={boxing_service.get_baseline() is not None}")
print(f"DEBUG: features={features}")
print(f"DEBUG: window_len={len(current_window) if current_window else 0}")
```

### Kafka
1. No messages consumed? → Topic doesn't exist, or wrong broker address
2. Producer fails silently? → `delivery_callback` shows error but caller ignores it
3. High latency? → `await producer.send()` in WebSocket handler — must be `create_task()`
4. Messages arriving out of order? → Multiple partitions + multiple consumers (expected for non-keyed topics)

```bash
# List Kafka topics
docker exec boxing-kafka kafka-topics --list --bootstrap-server localhost:9092

# Consume messages manually (debug)
docker exec boxing-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic health-metrics \
  --from-beginning \
  --max-messages 5
```

### Redis
1. Buffer always empty? → Consumer not running, or wrong Redis key
2. `LPUSH` not persisting? → Redis `maxmemory-policy allkeys-lru` evicted under memory pressure
3. Connection refused? → Redis container not up, or wrong URL in `.env`

```bash
# Check Redis state
docker exec boxing-redis redis-cli LLEN smartwatch:telemetry
docker exec boxing-redis redis-cli LRANGE smartwatch:telemetry 0 4
```

### MongoDB / Beanie
1. `None` from `find_one()`? → Document doesn't exist, or wrong filter field
2. `ValidationError` on save? → Required field missing (check model definition)
3. Index not found? → `init_db()` not called at startup, or model not in document_models list
4. Slow queries? → Missing index, use `.explain()` to verify

```python
# Check if Beanie is initialized
from beanie import init_beanie
# Should be called in config/database.py during FastAPI lifespan
```

## Diagnostic Output Template

When reporting a bug, always include:

```
## Bug Report

**Symptom**: [what the user observed]
**Reproducible**: [always / sometimes / one-time]
**Module**: [file:line where failure manifests]

## 5 Whys Chain
1. [first why + evidence]
2. [second why + evidence]
3. [root cause]

## Evidence
```stack trace / log output / code snippet```

## Fix Recommendation
- Owner: [backend-builder | mobile-dev | ml-researcher | kafka-data-eng | devops-engineer]
- File: [exact path]
- Change: [what needs to change]
```

## Never do when debugging
- Don't add try/except to silence errors — find the root cause
- Don't restart containers as a "fix" — containers coming back means the bug is still there
- Don't test with hardcoded credentials — use `.env` values always


