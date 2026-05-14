---
name: kafka-schema
description: Apply this skill when writing or modifying Kafka producers, consumers, or event schemas for the mobile-boxing-app project. Contains the exact schemas for all 3 topics (health-metrics, technical-metrics, round-events), the non-blocking producer pattern required for WebSocket handlers, and the Redis buffer conventions. Trigger on: "create kafka producer", "write kafka event", "add topic", "publish to kafka", "kafka consumer", "kafka schema", "send event to kafka", "technical-metrics", "health-metrics", "round-events".
---

# Kafka Schema — mobile-boxing-app

## Topics (3 — never create others without approval)

| Env var | Topic name | Partition key | Purpose |
|---------|-----------|---------------|---------|
| `KAFKA_TOPIC_HEALTH` | `health-metrics` | `user_id` | Smartwatch HR, steps, calories |
| `KAFKA_TOPIC_TECHNIQUE` | `technical-metrics` | `user_id` | Landmark windows, DTW scores |
| `KAFKA_TOPIC_ROUNDS` | `round-events` | `user_id` | Round start, end, session summary |

**Restriction C-02 (permanent):** `user_id` is ALWAYS the partition key. Never use `device_id`, `email`, or any other field as the key.

## Library: confluent-kafka
All producers and consumers use `confluent_kafka` (not `kafka-python`).
Config is loaded from `schemas.settings` (pydantic-settings from `.env`).

---

## Schema: health-metrics

Used by `SmartWatchProducer`. Each message represents one telemetry reading.

```python
{
    "device_id": str,          # e.g. "dev-01"
    "user_id": str,            # PARTITION KEY — always present
    "manufacturer": str,       # e.g. "AcmeWatch"
    "model": str,              # e.g. "AcmeX-2"
    "firmware_version": str,   # e.g. "1.4.7"
    "timestamp": str,          # ISO 8601 UTC: datetime.now(timezone.utc).isoformat()
    "telemetry": {
        "battery": {
            "level": int,          # 0-100
            "charging": bool
        },
        "heart_rate": {
            "value": int,          # bpm, e.g. 72
            "unit": "bpm",
            "confidence": float    # 0.0-1.0
        },
        "steps": {
            "total": int,          # cumulative
            "delta": int           # since last reading
        },
        "calories": {
            "total_kcal": float
        },
        "activity": {
            "type": str,           # "idle" | "walking" | "running" | "boxing"
            "confidence": float    # 0.0-1.0
        }
    },
    "sequence": int            # monotonically increasing per session
}
```

**Kafka key:** `message["user_id"].encode("utf-8")`

---

## Schema: technical-metrics

For landmark windows and ML scores. To be produced by `technique_producer.py` (pending implementation).

```python
{
    "user_id": str,             # PARTITION KEY
    "session_id": str,          # UUID of the boxing session
    "timestamp": str,           # ISO 8601 UTC of the window end
    "event_type": str,          # "landmark_window" | "punch_detected" | "dtw_score"
    "payload": {
        # For event_type == "landmark_window":
        "landmarks": [          # EXACTLY 30 frames
            [                   # Each frame: 33 points
                {"x": float, "y": float, "z": float},  # index 0 = nose
                # ... 33 total
            ]
        ],
        "fps": int,             # always 30
        "frame_start": int,     # global frame index of window start

        # For event_type == "punch_detected":
        "punch_type": str,      # "jab" | "cross" | "hook" | "null"
        "dtw_score": float,     # 0.0-100.0
        "frame_index": int,

        # For event_type == "dtw_score":
        "score": float,         # 0.0-100.0
        "punch_type": str,
        "features": dict        # elbow_angle, forward_extent, shoulder_rotation, etc.
    }
}
```

**Critical:** landmarks are `[[x,y,z]]` only — NEVER include image bytes (C-01).

---

## Schema: round-events

For round lifecycle. To be produced by `round_producer.py` (pending implementation).

```python
{
    "user_id": str,             # PARTITION KEY
    "session_id": str,
    "timestamp": str,           # ISO 8601 UTC
    "event_type": str,          # "round_start" | "round_end" | "session_summary"
    "payload": {
        # For round_start:
        "round_number": int,
        "duration_seconds": int,  # planned duration

        # For round_end:
        "round_number": int,
        "actual_duration_seconds": int,
        "punch_count": int,
        "avg_dtw_score": float,
        "peak_heart_rate": int,

        # For session_summary:
        "total_rounds": int,
        "total_punches": int,
        "avg_score": float,
        "best_punch_type": str,
        "session_duration_seconds": int
    }
}
```

---

## Producer pattern (non-blocking — mandatory for WebSocket handlers)

WebSocket handlers must respond in <100ms (C-06). Never `await` a Kafka publish inside a WS handler — use `asyncio.create_task()`.

```python
import asyncio
import json
from confluent_kafka import Producer
from schemas import settings

# Module-level producer (initialize once at startup)
_producer = Producer({"bootstrap.servers": settings.KAFKA_BROKERS})

async def publish_health_metric(message: dict) -> None:
    """Publish health metric to Kafka (fire-and-forget, non-blocking)."""
    def _send():
        _producer.produce(
            settings.KAFKA_TOPIC_HEALTH,
            key=message["user_id"].encode("utf-8"),   # C-02: user_id as key
            value=json.dumps(message).encode("utf-8"),
            callback=_delivery_callback,
        )
        _producer.poll(0)

    # In WebSocket handler: asyncio.create_task(publish_health_metric(msg))
    # This is the right call — it schedules without blocking the event loop
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _send)

def _delivery_callback(err, msg):
    if err:
        print(f"[Kafka] Delivery failed: {err}")
```

**Calling from a WebSocket handler (correct pattern):**
```python
@app.websocket("/boxing/ws/jab")
async def ws_jab(websocket: WebSocket):
    # ... process frame ...
    asyncio.create_task(publish_technique_metric(event))  # non-blocking
    await websocket.send_json(response)                   # <100ms response guaranteed
```

---

## Consumer pattern

Based on `SmartWatchConsumer` (reference implementation):

```python
from confluent_kafka import Consumer, KafkaError
from schemas import settings

consumer = Consumer({
    "bootstrap.servers": settings.KAFKA_BROKERS,
    "group.id": settings.GROUP_ID,
    "client.id": settings.CLIENT_ID,
    "session.timeout.ms": settings.SESSION_TIMEOUT,
    "auto.offset.reset": settings.AUTO_OFFSET_RESET,  # "earliest"
})
consumer.subscribe([settings.KAFKA_TOPIC_HEALTH])

while True:
    msg = consumer.poll(0.1)
    if msg is None:
        continue
    if msg.error():
        if msg.error().code() != KafkaError._PARTITION_EOF:
            logger.error("Consumer error: %s", msg.error())
        continue
    payload = json.loads(msg.value().decode("utf-8"))
    # process payload...
```

---

## Redis buffer (health-metrics only)

After consuming, messages are stored in Redis via `kafka/storage.py`:

```python
from services.events.storage import append_message, load_messages

# On consume:
append_message(payload)  # LPUSH + LTRIM to SMARTWATCH_BUFFER_SIZE (500)

# To query:
messages = load_messages(limit=10, device_id="dev-01")
```

Redis key: `"smartwatch:telemetry"` — ring buffer of last 500 messages.

---

## Timestamp convention

Always UTC, always ISO 8601:
```python
from datetime import datetime, timezone
timestamp = datetime.now(timezone.utc).isoformat()
# Result: "2024-01-15T10:30:00.123456+00:00"
```

---

## File naming for new producers/consumers

Follow existing convention:
- `apps/backend/app/kafka/smartwatch_producer.py` — existing
- `apps/backend/app/kafka/technique_producer.py` — to create (technical-metrics)
- `apps/backend/app/kafka/round_producer.py` — to create (round-events)


