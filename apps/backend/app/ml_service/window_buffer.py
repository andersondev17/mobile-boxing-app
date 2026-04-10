"""Redis-backed 30-frame sliding window buffer.

Each frame is a feature dict produced by ``feature_extractor.extract_features``.
The buffer uses a Redis LIST with the LPUSH + LTRIM pattern so that memory
usage stays bounded and each push is O(1).

Key pattern: ``ws_window:{user_id}:{session_id}``

Internal ordering: the Redis list is *newest-first* (LPUSH inserts at the
left end).  The public API returns windows *oldest-first* so callers receive
a temporally ordered (30, N_features) sequence ready for DTW/classifier.
"""

from __future__ import annotations

import json

WINDOW_SIZE = 30  # EXACTLY 30 frames — constraint C-03, never change


class WindowBuffer:
    """Manages per-session 30-frame feature windows backed by Redis.

    Args:
        redis_client: An ``aioredis.Redis`` (or ``redis.asyncio.Redis``) async
            client instance.  The caller owns the connection lifecycle.
        ttl_seconds: How long an idle buffer lives in Redis before automatic
            expiry.  Refreshed on every push.  Default: 5 minutes.
    """

    def __init__(self, redis_client, ttl_seconds: int = 300) -> None:
        self._redis = redis_client
        self._ttl = ttl_seconds

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def push_frame(
        self,
        user_id: str,
        session_id: str,
        features: dict,
    ) -> list[dict] | None:
        """Push one feature frame into the buffer.

        Returns the complete 30-frame window (oldest-first) once the buffer
        reaches exactly WINDOW_SIZE frames.  Returns ``None`` while the
        buffer is still filling up.

        Args:
            user_id: Identifies the athlete.  Used as part of the Redis key.
            session_id: Unique identifier for the current boxing session.
            features: Feature dict as returned by ``extract_features()``.

        Returns:
            A list of 30 feature dicts ordered oldest→newest, or ``None``.
        """
        key = self._make_key(user_id, session_id)

        # Serialize frame and push to the left (newest end).
        serialized = json.dumps(features)
        await self._redis.lpush(key, serialized)

        # Keep only the WINDOW_SIZE most-recent frames.
        await self._redis.ltrim(key, 0, WINDOW_SIZE - 1)

        # Refresh expiry on every write so idle sessions are cleaned up.
        await self._redis.expire(key, self._ttl)

        # Check whether the buffer is full.
        length = await self._redis.llen(key)
        if length < WINDOW_SIZE:
            return None

        # Read all frames (currently newest-first) and reverse to oldest-first.
        raw_frames = await self._redis.lrange(key, 0, WINDOW_SIZE - 1)
        window = [json.loads(frame) for frame in reversed(raw_frames)]
        return window

    async def clear(self, user_id: str, session_id: str) -> None:
        """Delete the buffer for this session.

        Call this when the session ends to free Redis memory immediately
        rather than waiting for TTL expiry.
        """
        key = self._make_key(user_id, session_id)
        await self._redis.delete(key)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _make_key(self, user_id: str, session_id: str) -> str:
        return f"ws_window:{user_id}:{session_id}"
