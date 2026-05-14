---
name: boxing-conventions
description: Apply this skill when writing any code for the mobile-boxing-app project. Contains project-specific conventions, naming standards, permanent restrictions, and patterns that all agents must follow. Trigger on: "write code for boxing app", "implement endpoint", "create model", "add feature to boxing", "follow project conventions".
---

# Boxing App — Project Conventions

## Identity
- Project: `mobile-boxing-app` — monorepo at `boxing-api/`
- App name (mobile bundle): `gymshock`
- Team: small (1-2 devs + AI agents)

## Stack (exact names — use in comments, docs, and error messages)
| Layer | Technology |
|-------|-----------|
| Backend | FastAPI 0.120 + Uvicorn, Python 3.11 |
| ORM | Beanie ODM (MongoDB driver: motor) |
| DB | MongoDB 7 (Docker local) |
| Cache | Redis 7-alpine (Docker local, 256MB LRU) |
| Streaming | Kafka 1-node KRaft (Docker local, no Zookeeper) |
| Mobile | React Native + Expo SDK 54 + Expo Dev Build |
| State | Zustand 5 + AsyncStorage |
| Camera | react-native-vision-camera v4.7.2 |
| ML Fase 1 | dtaidistance (DTW) + scikit-learn (SVM/RF) |
| ML Fase 2+ | PyTorch + ONNX Runtime (future) |
| Landmarks | TFLite on-device, 33 points `[[x,y,z]]` float32 |

## Kafka topics (always these exact names)
| Topic | Key | Description |
|-------|-----|-------------|
| `health-metrics` | `user_id` | Smartwatch HR, steps, calories, activity |
| `technical-metrics` | `user_id` | Landmark windows, DTW scores, punch events |
| `round-events` | `user_id` | Round start, round end, session summary |

## Landmark format (universal — backend and mobile)
```python
# Python
landmarks: list[dict]  # [{"x": 0.5, "y": 0.3, "z": -0.1}, ...] — 33 elements

# TypeScript
type Landmark = { x: number; y: number; z: number }
type LandmarkArray = Landmark[]  // 33 elements
```

## Critical landmark indices (MediaPipe/TFLite 33-point model)
- `11` = shoulder_L, `12` = shoulder_R
- `13` = elbow_L, `14` = elbow_R
- `15` = wrist_L, `16` = wrist_R
- `23` = hip_L, `24` = hip_R
- Visibility threshold: `> 0.65` to be considered reliable

## Permanent restrictions (NEVER violate — code that violates must be rejected)
| Code | Rule |
|------|------|
| C-01 | NEVER store video bytes or image bytes — only landmarks `[[x,y,z]]` |
| C-02 | `user_id` ALWAYS as Kafka partition key (not `device_id`, not `email`) |
| C-03 | Inference windows: EXACTLY 30 frames = 1 second at 30fps |
| C-04 | NO ST-GCN, no graph neural networks — CPU only (no GPU) |
| C-05 | Consent (Ley 1581 Colombia) BEFORE persisting any biometric data |
| C-06 | WebSocket response to client: < 100ms |

## Python conventions (backend)
```python
# Docstrings: Google style
def process_frame(frame: np.ndarray) -> dict:
    """Process a single frame and extract boxing features.

    Args:
        frame: Raw BGR frame as numpy array, shape (H, W, 3).

    Returns:
        Dict with keys: elbow_angle, forward_extent, shoulder_rotation.

    Raises:
        ValueError: If frame shape is invalid.
    """

# Type hints: always, everywhere
async def get_user(user_id: str) -> Optional[User]:
    ...

# Env vars: always from Settings, never hardcoded
from app.schemas.env import settings
kafka_brokers = settings.KAFKA_BROKERS  # correct
kafka_brokers = "kafka:9092"  # WRONG

# Beanie queries: async/await
user = await User.find_one(User.email == email)
await session.save()

# Kafka publish from WebSocket: fire-and-forget
asyncio.create_task(producer.send(topic, value=msg, key=user_id.encode()))
# NEVER: await producer.send(...)  — blocks the event loop
```

## TypeScript conventions (mobile)
```typescript
// JSDoc on all exported components and hooks
/**
 * Hook for managing real-time pose analysis via WebSocket.
 * @param userId - Authenticated user ID for session tracking.
 */
export function useRealtimePose(userId: string) { ... }

// Zustand stores: always in store/
import { useAuthStore } from '@/store/authStore'

// API calls: always via lib/api/client.ts
import { apiClient } from '@/lib/api/client'

// Never send base64 frames — only landmarks
const payload = { landmarks: landmarkArray, fps: 30, frame_index: n }
ws.send(JSON.stringify(payload))
```

## File naming conventions
```
Backend Python:    snake_case.py
Backend models:    models/model.py, models/boxing.py
Backend routes:    routes/boxing.py, routes/consent.py
Mobile screens:    app/(tabs)/index.tsx  (Expo Router convention)
Mobile hooks:      hooks/useSomething.ts
Mobile services:   services/somethingService.ts
Mobile stores:     store/somethingStore.ts
Skill files:       .claude/skills/<name>/SKILL.md
Agent files:       .claude/agents/<name>.md
```

## Score thresholds (ML — validated by boxing-domain-expert)
| Range | Meaning |
|-------|---------|
| >= 85 | Competition level |
| 70-84 | Functional, minor correction |
| 50-69 | Specific error identifiable |
| < 50 | Invalid — do not classify as punch |

## MongoDB document conventions
Every Beanie Document must have:
- `created_at: datetime` — set on insert (UTC)
- `updated_at: datetime` — set on update (UTC)

Documents with biometric data must also have:
- `consent_ts: datetime` — when consent was granted (UTC)
- `policy_version: str` — e.g. `"v1.0"`

## App modes (for light development)
| Mode | Services | Use when |
|------|----------|----------|
| `technique` | MongoDB + Redis + backend | Developing ML pipeline |
| `auth` | MongoDB + backend | Developing auth flows |
| `smartwatch` | MongoDB + Redis + Kafka + backend | Developing wearable integration |
| `catalog` | MongoDB + backend | Developing exercise catalog |
| `full` | All services | Integration testing |


