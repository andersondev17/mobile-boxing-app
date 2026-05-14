---
name: ml-pipeline
description: Apply this skill when building or modifying the boxing ML inference pipeline: DTW scorer, SVM/RF classifier, window buffer, feature extractor, or feedback engine. Also apply when designing the WebSocket handler's interaction with ML. Trigger on: "implement DTW", "window buffer", "punch classifier", "feature extractor", "ml pipeline", "boxing score", "dtw_scorer", "window_buffer", "punch_classifier", "inference pipeline", "30 frames", "landmark features".
---

# ML Pipeline — mobile-boxing-app

## Architecture (Phase 1 — CPU only, no GPU)

```
Mobile TFLite
    → landmarks [[x,y,z]] 33pts per frame
    → WebSocket /boxing/ws/jab
    → ws_tracker.process_landmarks()
    → Redis window buffer (30 frames)
    → [trigger] DTW scorer → score 0-100
    → SVM/RF classifier → punch_type
    → FeedbackEngine → text message
    → WebSocket response (<100ms)
```

## Files in ml_service/

| File | Status | Purpose |
|------|--------|---------|
| `boxing_jab_tracker.py` | ✅ exists | JabTracker state machine |
| `feature_extractor.py` | ✅ exists | 2 features (needs expansion) |
| `feedback_engine.py` | ✅ exists | Rule-based, needs DTW input |
| `boxing_service.py` | ✅ exists | Orchestration singleton |
| `window_buffer.py` | ❌ pending | Redis 30-frame buffer |
| `dtw_scorer.py` | ❌ pending | DTW similarity scorer |
| `punch_classifier.py` | ❌ pending | SVM/RF classifier |

## Current feature_extractor.py (only 2 features)

```python
# Existing — DO NOT REMOVE:
"elbow_angle"    # degrees at elbow joint (shoulder-elbow-wrist angle)
"forward_extent" # wrist.x - shoulder.x (reach distance)

# To add (Phase 1):
"shoulder_rotation"  # angle of shoulder axis vs frontal plane
"hip_rotation"       # angle at hip landmarks 23-24 vs baseline
"guard_distance"     # distance from non-punching hand to face
```

Landmark indices to use:
- 11 = shoulder_L, 12 = shoulder_R
- 13 = elbow_L, 14 = elbow_R
- 15 = wrist_L, 16 = wrist_R
- 23 = hip_L, 24 = hip_R
- Visibility guard: `if lm.visibility < 0.65: return None`

## window_buffer.py — Implementation spec

```python
import asyncio
import json
from typing import Optional
import redis.asyncio as aioredis
from schemas import settings

WINDOW_KEY = "ml:window:{user_id}"
WINDOW_SIZE = 30  # C-03: EXACTLY 30 frames = 1 second

async def push_frame(user_id: str, features: dict, redis: aioredis.Redis) -> Optional[list]:
    """Push features for one frame. Returns full window when ready, else None.

    Args:
        user_id: Partition identifier (always user_id, not device_id).
        features: Dict from extract_features() — elbow_angle, forward_extent, etc.
        redis: Async Redis client.

    Returns:
        List of WINDOW_SIZE feature dicts when buffer is full, else None.
    """
    key = WINDOW_KEY.format(user_id=user_id)
    pipe = redis.pipeline()
    pipe.lpush(key, json.dumps(features))
    pipe.ltrim(key, 0, WINDOW_SIZE - 1)
    pipe.llen(key)
    _, _, length = await pipe.execute()

    if length >= WINDOW_SIZE:
        raw = await redis.lrange(key, 0, WINDOW_SIZE - 1)
        # lrange returns newest first (lpush), reverse for chronological order
        return [json.loads(f) for f in reversed(raw)]
    return None
```

## dtw_scorer.py — Implementation spec

```python
import numpy as np
from dtaidistance import dtw_ndim

FEATURES = ["elbow_angle", "forward_extent", "shoulder_rotation", "hip_rotation"]

def score_window(user_window: list, baseline_windows: list) -> float:
    """Compute DTW similarity score 0-100 against baseline windows.

    Args:
        user_window: List of 30 feature dicts (chronological order).
        baseline_windows: List of reference windows from baseline parquet.

    Returns:
        Float score 0-100 where 100 = perfect technique.
    """
    user_array = _to_array(user_window)  # shape (30, N_features)

    distances = []
    for baseline_window in baseline_windows:
        baseline_array = _to_array(baseline_window)
        dist = dtw_ndim.distance(user_array, baseline_array)
        distances.append(dist)

    if not distances:
        return 0.0

    min_dist = min(distances)
    # Normalize: 0 distance = 100 score, large distance approaches 0
    score = 100.0 * np.exp(-min_dist / 50.0)  # 50 = normalization constant
    return float(np.clip(score, 0.0, 100.0))

def _to_array(window: list) -> np.ndarray:
    return np.array([[f.get(feat, 0.0) for feat in FEATURES] for f in window], dtype=np.float32)
```

## punch_classifier.py — Implementation spec

```python
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
import joblib
import numpy as np

PUNCH_TYPES = ["jab", "cross", "hook", "null"]
MODEL_PATH = "ml_service/models/punch_classifier.joblib"

class PunchClassifier:
    """SVM classifier for punch type detection."""

    def load(self) -> None:
        """Load pre-trained model. Call once at startup."""
        self.model = joblib.load(MODEL_PATH)
        self.scaler = joblib.load(MODEL_PATH.replace(".joblib", "_scaler.joblib"))

    def predict(self, window: list) -> tuple[str, float]:
        """Classify punch type from a 30-frame window.

        Returns:
            Tuple of (punch_type, confidence) where punch_type is in PUNCH_TYPES.
        """
        features = self._window_to_features(window)
        features_scaled = self.scaler.transform([features])
        punch_type = self.model.predict(features_scaled)[0]
        confidence = float(self.model.predict_proba(features_scaled).max())
        return punch_type, confidence

    def _window_to_features(self, window: list) -> list:
        # Flatten: mean + std of each feature across 30 frames
        arr = np.array([[f.get(feat, 0.0) for feat in FEATURES] for f in window])
        return list(np.concatenate([arr.mean(axis=0), arr.std(axis=0)]))
```

## WebSocket integration pattern (non-blocking)

The WS handler must stay under 100ms (C-06). ML inference goes in a background task:

```python
@router.websocket("/ws/jab")
async def jab_websocket(websocket: WebSocket):
    await websocket.accept()
    tracker = boxing_service.create_realtime_tracker()

    async def _run_inference(features: dict, user_id: str):
        window = await window_buffer.push_frame(user_id, features, redis_client)
        if window:
            score = dtw_scorer.score_window(window, baseline_windows)
            punch_type, conf = punch_classifier.predict(window)
            # Publish to Kafka (fire-and-forget)
            asyncio.create_task(publish_technique_metric({
                "user_id": user_id, "score": score, "punch_type": punch_type
            }))

    while True:
        payload = json.loads(await websocket.receive_text())
        raw_landmarks = payload.get("landmarks")
        if raw_landmarks:
            features, feedback, jab_event = tracker.process_landmarks(raw_landmarks)
            # Schedule inference without awaiting
            asyncio.create_task(_run_inference(features, payload.get("user_id", "")))
            # Respond immediately (<100ms)
            await websocket.send_json({"feedback": feedback, "jab_detected": bool(jab_event)})
```

## Score thresholds (validated by boxing-domain-expert)

| Score | Meaning | Feedback strategy |
|-------|---------|-------------------|
| >= 85 | Competition level | "Excelente técnica" |
| 70-84 | Functional | Identify one specific fault |
| 50-69 | Error identifiable | Named fault + correction cue |
| < 50 | Invalid movement | Do NOT classify as punch |

## Phase 2+ (only after Phase 1 is stable)
- LSTM for temporal pattern recognition (requires GPU or ONNX on mobile)
- TCN (Temporal Convolutional Network)
- Export to ONNX: `torch.onnx.export(model, dummy_input, "model.onnx")`
- Rule: NO ST-GCN until GPU is available (C-04)


