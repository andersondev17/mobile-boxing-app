---
name: test-standards
description: Apply this skill when writing, running, or reviewing tests for the boxing app backend or mobile. Contains pytest conventions, fixture patterns for landmarks, and minimum coverage targets. Trigger on: "write tests", "pytest", "unit test", "integration test", "test fixture", "coverage", "test the function", "add tests", "test suite".
---

# Test Standards — mobile-boxing-app

## Backend: pytest

### Location
```
apps/backend/app/
└── tests/
    ├── conftest.py          # Shared fixtures
    ├── test_ml_service/
    │   ├── test_feature_extractor.py
    │   ├── test_dtw_scorer.py
    │   ├── test_window_buffer.py
    │   └── test_feedback_engine.py
    ├── test_routes/
    │   ├── test_boxing.py   # WebSocket tests
    │   └── test_consent.py
    └── test_kafka/
        └── test_producers.py
```

### Running tests
```bash
# From apps/backend/app/
pytest tests/ -v

# Specific module
pytest tests/test_ml_service/ -v

# With coverage
pytest tests/ --cov=. --cov-report=term-missing

# Run only fast tests (skip integration)
pytest tests/ -m "not integration" -v
```

### Minimum coverage targets
| Module | Target |
|--------|--------|
| `ml_service/feature_extractor.py` | 90% |
| `ml_service/dtw_scorer.py` | 85% |
| `ml_service/window_buffer.py` | 85% |
| `ml_service/feedback_engine.py` | 90% |
| `routes/consent.py` | 80% |
| Overall | 75% |

### Landmark fixtures (conftest.py)

Use realistic landmark arrays based on the actual 33-point TFLite model:

```python
# conftest.py
import pytest
import numpy as np
from unittest.mock import MagicMock

def _make_landmark(x: float, y: float, z: float = 0.0, vis: float = 0.9) -> MagicMock:
    """Create a mock MediaPipe/TFLite landmark."""
    lm = MagicMock()
    lm.x = x
    lm.y = y
    lm.z = z
    lm.visibility = vis
    return lm

@pytest.fixture
def jab_landmarks_extended():
    """33 landmarks representing a fully extended jab (left arm).
    Landmark 13 (elbow_L) at ~170 degrees — competition-level extension.
    """
    lms = [_make_landmark(0.5, 0.5) for _ in range(33)]
    lms[11] = _make_landmark(0.4, 0.35)  # shoulder_L
    lms[13] = _make_landmark(0.55, 0.35)  # elbow_L (extended forward)
    lms[15] = _make_landmark(0.75, 0.35)  # wrist_L (fully extended)
    return lms

@pytest.fixture
def jab_landmarks_bent():
    """33 landmarks representing a poorly executed jab (bent arm).
    Landmark 13 (elbow_L) at ~90 degrees — error state.
    """
    lms = [_make_landmark(0.5, 0.5) for _ in range(33)]
    lms[11] = _make_landmark(0.4, 0.35)  # shoulder_L
    lms[13] = _make_landmark(0.45, 0.45)  # elbow_L (bent downward)
    lms[15] = _make_landmark(0.5, 0.50)  # wrist_L (not extended)
    return lms

@pytest.fixture
def window_30_frames(jab_landmarks_extended):
    """A full 30-frame window of extended jab features."""
    from services.ml.feature_extractor import extract_features
    features = extract_features(jab_landmarks_extended)
    return [features for _ in range(30)]

@pytest.fixture
def baseline_df():
    """Minimal baseline DataFrame for FeedbackEngine."""
    import pandas as pd
    return pd.DataFrame({
        "elbow_angle": [170.0, 168.0, 172.0],
        "forward_extent": [0.30, 0.28, 0.32],
    })
```

### Test patterns

```python
# test_feature_extractor.py
def test_extract_features_extended_jab(jab_landmarks_extended):
    """Extended jab should produce elbow_angle close to 170°."""
    features = extract_features(jab_landmarks_extended)
    assert features is not None
    assert 155 <= features["elbow_angle"] <= 180, "Fully extended jab should be 155-180°"
    assert features["forward_extent"] > 0.2, "Extended jab should have positive reach"

def test_extract_features_too_few_landmarks():
    """Should return None with fewer than 16 landmarks."""
    short_list = [MagicMock()] * 10
    assert extract_features(short_list) is None

# test_feedback_engine.py
def test_feedback_good_technique(baseline_df):
    """Good technique should return positive feedback."""
    engine = FeedbackEngine(baseline_df)
    features = {"elbow_angle": 168.0, "forward_extent": 0.29}
    assert engine.compare(features) == "Buena tecnica, sigue asi."

def test_feedback_bent_elbow(baseline_df):
    """Elbow delta > 15° should trigger elbow feedback."""
    engine = FeedbackEngine(baseline_df)
    features = {"elbow_angle": 140.0, "forward_extent": 0.29}
    feedback = engine.compare(features)
    assert "codo" in feedback.lower()
```

### WebSocket test pattern (pytest-asyncio)

```python
# test_routes/test_boxing.py
import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.mark.asyncio
async def test_websocket_ping_pong():
    async with AsyncClient(transport=ASGITransport(app=app)) as client:
        async with client.websocket_connect("/boxing/ws/jab") as ws:
            await ws.send_json({"type": "ping", "ts": 123456})
            response = await ws.receive_json()
            assert response["type"] == "pong"
            assert response["ts"] == 123456
```

## Mobile: Jest + React Native Testing Library

```bash
# From apps/mobile/
npx jest --watchAll=false
```

Test files: `*.test.ts` / `*.test.tsx` next to the component/hook they test.


