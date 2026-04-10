# Data Capture & Schema Strategy (Ley 1581 Compliant)

## 1. Compliance (Ley 1581)
- **Explicit Consent**: Prior to capturing any biometric data, users must explicitly grant consent (`biometric_data` type). Without this, processing stops immediately.
- **Minimization**: We never store video or images. We only extract structural indices (landmarks).
- **Transparency**: Uses the MongoDB `Consent` table to track who approved what data types (`personal_data`, `biometric_data`, `health_data`).

## 2. Models for Long-Term Analytics & Training

### Biomechanical Pipeline Storage
We capture a streamlined set of metrics rather than raw frames:
- Form factors (elbow angles, forward extensions, guard distances)
- Speeds (hand speed, retraction velocity)
- Tracking fidelity (`tracking_state` - whether the trunk is visible)

**Data model representation (Parquet or MongoDB timeseries):**
```json
{
  "user_id": "uuid",
  "session_id": "uuid",
  "timestamp": "iso-8601",
  "device_metadata": {
    "os": "Android/iOS",
    "processor": "...",
    "camera_fps": 30
  },
  "frame_index": 105,
  "features": {
    "elbow_angle_left": 120.5,
    "forward_extent_left": 0.4,
    "hand_speed": 1.2,
    "retraction_speed": 0.0
  },
  "punch_detected": "jab",
  "dtw_score": 85.2,
  "label": "good"
}
```

### Performance History (Analytics)
Long-term growth is tracked using rolled-up aggregate session metrics rather than keeping dense time-series active. High-fidelity TS data is offloaded to S3 bucket / Data lake for model training datasets.

- `user_id` -> session history -> average DTW scores over time -> macro progression.

## 3. Data Flow
Mobile App (Websocket) -> Backend (Extracts & Validates) -> Redis (30-frame window sliding buffer)
- Triggers DTW
- Yields Label
-> Kafka (Async punch publish) -> Consumer -> MongoDB TimeSeries Storage / Parquet Archiving.
