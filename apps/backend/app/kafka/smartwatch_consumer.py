"""
Resilient Kafka consumer for smartwatch health telemetry.

Key hardening:
- Exponential backoff on repeated errors (max 60s)
- Dead-letter logging on deserialization failures
- ENV_MODE guard: skips if kafka_enabled=False
- Structured JSON logging compatible with main.py handler
"""

from __future__ import annotations

import json
import logging
import time
from typing import Optional

from confluent_kafka import Consumer, KafkaError, KafkaException

from kafka.storage import append_message
from schemas import settings

logger = logging.getLogger(__name__)

_BACKOFF_BASE: float = 1.0
_BACKOFF_MAX: float = 60.0
_POLL_TIMEOUT: float = 0.5


class SmartWatchConsumer:
    """Consumes smartwatch telemetry from Kafka → Redis buffer.

    Partition key: user_id (guaranteed by producer).
    Topic: health-metrics
    """

    def __init__(self) -> None:
        self.topic = settings.KAFKA_TOPIC_HEALTH
        self._conf = {
            "bootstrap.servers": settings.KAFKA_BROKERS,
            "group.id": settings.GROUP_ID,
            "client.id": f"{settings.CLIENT_ID}-health",
            "session.timeout.ms": settings.SESSION_TIMEOUT,
            "auto.offset.reset": settings.AUTO_OFFSET_RESET,
            # Prevent duplicate processing on restart
            "enable.auto.commit": True,
            "auto.commit.interval.ms": 5000,
        }
        self._consecutive_errors: int = 0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _backoff(self) -> float:
        """Return exponential backoff seconds, capped at _BACKOFF_MAX."""
        delay = min(_BACKOFF_BASE * (2 ** self._consecutive_errors), _BACKOFF_MAX)
        return delay

    def _handle_message(self, msg) -> None:
        """Deserialize and forward one message to Redis storage."""
        try:
            payload = json.loads(msg.value().decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            logger.error(
                "Dead-letter: failed to parse message from topic=%s partition=%d offset=%d: %s",
                msg.topic(), msg.partition(), msg.offset(), exc,
            )
            return

        # Validate minimum required fields
        user_id: Optional[str] = payload.get("user_id")
        device_id: Optional[str] = payload.get("device_id")
        if not user_id:
            logger.warning("Discarding message: missing user_id (offset=%d)", msg.offset())
            return

        append_message(payload)
        self._consecutive_errors = 0  # reset backoff on success

        hr = payload.get("telemetry", {}).get("heart_rate", {}).get("value")
        fatigue = (
            payload.get("telemetry", {}).get("load_metrics", {}).get("fatigue_index")
        )
        logger.info(
            "health_metric_received",
            extra={
                "user_id": user_id,
                "device_id": device_id,
                "hr_bpm": hr,
                "fatigue_index": fatigue,
                "offset": msg.offset(),
                "partition": msg.partition(),
            },
        )

    def _handle_error(self, error: KafkaError) -> None:
        """Log Kafka errors and apply backoff on fatal ones."""
        if error.code() == KafkaError._PARTITION_EOF:
            # Normal — reached end of partition, not an error
            return
        self._consecutive_errors += 1
        delay = self._backoff()
        logger.error(
            "Kafka consumer error (fatal=%s, backoff=%.1fs): %s",
            error.fatal(), delay, error,
        )
        if error.fatal():
            raise KafkaException(error)
        time.sleep(delay)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Run the consumer loop. Blocks until KeyboardInterrupt or fatal error."""
        if not settings.kafka_enabled:
            logger.info(
                "Kafka consumer skipped (ENV_MODE=%s). "
                "Set ENV_MODE=full or local_real to enable.",
                settings.ENV_MODE,
            )
            return

        consumer = Consumer(self._conf)
        consumer.subscribe([self.topic])
        logger.info("SmartWatchConsumer started: topic=%s", self.topic)

        try:
            while True:
                msg = consumer.poll(_POLL_TIMEOUT)
                if msg is None:
                    continue
                if msg.error():
                    self._handle_error(msg.error())
                    continue
                self._handle_message(msg)

        except KeyboardInterrupt:
            logger.info("SmartWatchConsumer stopped by user.")
        except KafkaException as exc:
            logger.critical("Fatal Kafka exception — consumer terminating: %s", exc)
            raise
        finally:
            consumer.close()
            logger.info("SmartWatchConsumer closed cleanly.")


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    SmartWatchConsumer().start()
