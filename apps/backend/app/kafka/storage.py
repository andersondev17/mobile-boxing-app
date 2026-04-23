import json
from functools import lru_cache
from typing import List, Optional

from redis import Redis

from app.schemas import settings

REDIS_KEY = "smartwatch:telemetry"


@lru_cache
def get_redis_client() -> Redis:
    return Redis.from_url(settings.REDIS_URL)


def append_message(payload: dict) -> None:
    client = get_redis_client()
    pipe = client.pipeline()
    pipe.lpush(REDIS_KEY, json.dumps(payload))
    pipe.ltrim(REDIS_KEY, 0, max(0, settings.SMARTWATCH_BUFFER_SIZE - 1))
    pipe.execute()


def load_messages(
    limit: Optional[int] = None,
    device_id: Optional[str] = None,
) -> List[dict]:
    client = get_redis_client()
    max_fetch = settings.SMARTWATCH_BUFFER_SIZE
    raw_items = client.lrange(REDIS_KEY, 0, max_fetch - 1)

    messages: List[dict] = []
    for item in raw_items:
        if isinstance(item, bytes):
            item = item.decode("utf-8")
        try:
            data = json.loads(item)
        except (json.JSONDecodeError, TypeError):
            continue
        if device_id and data.get("device_id") != device_id:
            continue
        messages.append(data)
        if limit and len(messages) >= limit:
            break

    return messages
