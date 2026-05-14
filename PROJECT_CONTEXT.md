# Boxing API — Project Context

**Status:** 37/37 tasks completed ✅ | **Python:** 3.10/3.11 | **Env:** `.venv`

---

## Architecture

```
React Native → FastAPI → PostgreSQL (Auth) + MongoDB (Biometrics) + Redis (Cache)
                     ↓
              ML Pipeline (RF+DTW) + Kafka (Confluent Cloud) + Firebase/AdMob
```

---

## ML Pipeline Deep Dive

### Feature Extraction (8 features)
- `elbow_angle_left/right` — Arm extension
- `forward_extent_left/right` — Reach distance  
- `torso_rotation` — Core power generation
- `vertical_displacement` — Body drop/head movement
- `knee_flexion` — Leg drive
- `weight_transfer` — Lateral weight shift

### Hybrid Classifier (RF + DTW)
1. **Stage 1 - Random Forest:** Fast top-k filtering (jab/cross/hook/uppercut probabilities)
2. **Stage 2 - DTW:** Fine-grained validation vs baselines using `fastdtw`
3. **Final Score:** `0.6 × RF_confidence + 0.4 × DTW_score`
4. **Threshold:** `min_confidence = 0.60`

### DTW Scoring
```python
score = 100 × exp(-distance / 10.0)
≥ 85 = elite | 70-84 = good | 50-69 = developing | < 50 = poor
```

### Feedback Engine (Spanish)
- **Jab:** "Extiende más el brazo", "Gira la cadera"
- **Cross:** "Transfiere el peso", "Gira más el torso"
- **Hook:** "Mantén el codo en 90 grados"
- **Uppercut:** "Trayectoria vertical"

---

## Baseline Generation

### Pipeline Steps
1. **MediaPipe** → 33 landmarks
2. **Filter** → Remove low visibility (< 0.65)
3. **Smooth** → EMA α=0.7
4. **Normalize** → Scale to [0,1]
5. **Augment** → 5 good + 5 acceptable synthetic samples
6. **Output** → `baseline_final.parquet`

### Key Constants
```python
NORM = {
    "elbow_angle_left": 180.0,
    "hand_speed": 15.0,
    "retraction_speed": 5.0,
    "torso_rotation": 0.5,
}
```

---

## Services

| Service | File | Purpose |
|---------|------|---------|
| Auth | `auth/auth_service.py` | OAuth2 + JWT (Google + Local) |
| Gamification | `services/gamification_service.py` | XP, levels 1-10, achievements |
| AdMob | `services/ads_service.py` | Banner, interstitial, rewarded ads |
| Firebase | `services/firebase_service.py` | Analytics, FCM, Project ID: `boxing-app-bf637` |
| Sentry | `main.py:75-96` | Error tracking (optional) |

---

## FastAPI Routers

```python
app.include_router(user_router)        # CRUD users
app.include_router(training_router)    # Training sessions
app.include_router(auth_router)        # Login/OAuth2
app.include_router(boxing_router)      # Video analysis
app.include_router(hybrid_analysis_router)  # RF+DTW endpoint
app.include_router(gamification_router)     # XP/achievements
app.include_router(ads_router)              # AdMob config
```

---

## Docker

```bash
cd apps/backend
docker-compose up -d --build
```

**Services:** PostgreSQL (5433), MongoDB (27017), Redis (6380), Backend (8000)

---

## Environment Variables

```bash
# Critical
FIREBASE_PROJECT_ID=boxing-app-bf637
SENTRY_DSN=your_sentry_dsn
KAFKA_BROKERS=pkc-XXXX.us-east1.gcp.confluent.cloud:9092

# Databases
POSTGRES_USER=admin
MONGO_USER=admin
REDIS_URL=redis://localhost:6380

# Security
SECRET_KEY=your_jwt_secret
GOOGLE_CLIENT_ID=your_oauth_client_id
```

---

## Key Files

| File | Purpose |
|------|---------|
| `apps/backend/app/main.py` | FastAPI entry point |
| `apps/backend/app/ml_service/hybrid_classifier.py` | RF+DTW pipeline |
| `apps/backend/app/build_baseline/build_pipeline.py` | Baseline generation |
| `apps/backend/app/ml_service/feedback_engine.py` | Spanish coaching |
| `apps/backend/docker-compose.yml` | Docker orchestration |

---

## Testing Completed ✅

1. ✅ Baseline generation with real videos
2. ✅ ML service detection (jab/cross/hook/uppercut)
3. ✅ Kafka producer/consumer (Confluent Cloud)
4. ✅ Authentication (OAuth2 + JWT)
5. ✅ Firebase Analytics integration
6. ✅ Sentry error tracking
7. ✅ Google AdMob integration
8. ✅ Ley 1581 consent management
9. ✅ Gamification (XP/achievements)
10. ✅ End-to-end integration

---

## Quick Start New Chat

Paste this + your new task:

> "Continuing Boxing API project. Context: FastAPI + React Native + Kafka + ML Hybrid (RF+DTW) for punch detection. 37 tasks completed. Need help with: [YOUR TASK]"


