---
name: technical-writer
description: Apply this skill when writing ADRs (Architecture Decision Records), module READMEs, API documentation, or sprint specs for the boxing app. Trigger on: "write ADR", "document architecture decision", "module README", "API docs", "sprint spec", "technical documentation", "write documentation", "document this decision", "create ADR".
---

# Technical Writer — mobile-boxing-app

## ADR (Architecture Decision Record) Template

Save ADRs in `docs/adr/ADR-NNN-short-title.md`:

```markdown
# ADR-001: Use MongoDB instead of PostgreSQL

**Date**: 2024-01-15
**Status**: Accepted
**Deciders**: Federico (tech lead)

## Context
The app needs to store boxing sessions with flexible schema (feedback arrays,
variable metrics). The team has TypeScript/Python background, not SQL-first.

## Decision
Use MongoDB 7 with Beanie ODM for all persistent data.

## Consequences
+ Flexible schema for session data (list of feedback messages, variable metrics)
+ Native JSON storage matches the API payload format
+ Beanie ODM provides clean async interface
- No JOIN queries (use separate lookups or embed related data)
- Less strict schema enforcement (mitigated by Pydantic validation at API layer)

## Alternatives considered
- PostgreSQL + SQLAlchemy: rejected — rigid schema for session metrics
- Firebase: rejected — vendor lock-in, cost at scale
```

## Module README Template

Save in `apps/backend/app/<module>/README.md`:

```markdown
# ml_service — Boxing ML Pipeline

## Purpose
Real-time technique analysis for boxing punches using DTW similarity
and SVM/RF classification.

## Status (Phase 1)
| Component | Status |
|-----------|--------|
| feature_extractor.py | ✅ 2 features |
| boxing_jab_tracker.py | ✅ state machine |
| feedback_engine.py | ✅ rule-based |
| dtw_scorer.py | ❌ pending |
| window_buffer.py | ❌ pending |
| punch_classifier.py | ❌ pending |

## Key design decisions
- Window size: exactly 30 frames (1 second at 30fps) — non-negotiable
- CPU only: no GPU available — DTW + SVM are the ceiling for Phase 1
- Async: inference scheduled via asyncio.create_task() to keep WS < 100ms

## Running locally
```bash
# In technique mode (MongoDB + Redis only)
docker-compose up mongodb redis backend -d
```

## Testing
```bash
pytest tests/test_ml_service/ -v
```
```

## Sprint Spec Template

For each sprint, document in `docs/sprints/sprint-N.md`:

```markdown
# Sprint N — [Title]

**Dates**: 2024-XX-XX to 2024-XX-XX
**Goal**: One-sentence sprint goal

## Deliverables
- [ ] Owner: backend-builder → Description of deliverable
- [ ] Owner: mobile-dev → Description of deliverable

## Definition of Done
- All 6 permanent restrictions still passing (code-reviewer audit)
- Docker Compose starts without errors
- New functions have docstrings
- PR reviewed and merged

## Issues resolved
- C-01: description of fix
- C-02: description of fix

## Out of scope
- Feature X (pushed to Sprint N+1)
```

## API endpoint documentation (in route docstrings)

```python
@router.websocket("/ws/jab")
async def jab_websocket(websocket: WebSocket):
    """Real-time jab analysis via WebSocket.

    **Protocol**: JSON over WebSocket

    **Request payload** (landmark-based — preferred):
    ```json
    {
        "landmarks": [{"x": 0.5, "y": 0.3, "z": -0.1}, ...],  // 33 elements
        "fps": 30,
        "frame_index": 42,
        "user_id": "uuid"
    }
    ```

    **Response**:
    ```json
    {
        "feedback": "Extiende mas el jab",
        "jab_detected": true,
        "frame_index": 42,
        "tracking_state": "tracking"
    }
    ```

    **Special messages**:
    - Ping: `{"type": "ping", "ts": 1234}` → `{"type": "pong", "ts": 1234}`
    - Reset: `{"action": "reset"}` → `{"status": "reset"}`

    **Restriction**: responds in <100ms (C-06)
    """
```


