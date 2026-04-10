# Updated Data Flow & ML Pipeline

## ML Pipeline
1. WebSocket receives payload (x, y, z, v).
2. Backend API extracts exactly DTW_FEATURE_ORDER keys.
3. Redis window buffer stores 30-frame window.
4. DTW Scorer uses single shared `normalize_feature_vector()` scale (e.g. angle / 180, speed / 15.0).
5. DTW score computed via `dtaidistance`. Score dynamically maps.

## Data Schema Storage
Records strictly store:
- elbow_angle_left
- forward_extent_left
- hand_speed
- retraction_speed
- consent flag and session identifiers.

## DTW Threshold
- DTW_K = 10.0
- Exact assertion enforces len(window) == 30.
