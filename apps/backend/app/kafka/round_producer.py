"""
Round lifecycle Kafka producer.

Publishes round start, round end, and session summary events
to the 'round-events' topic with user_id as partition key.

Restriction C-01: NEVER include raw image or video bytes in any payload.
Restriction C-02: user_id is ALWAYS the partition key.
"""

import json
from datetime import datetime, timezone
from typing import Any

from confluent_kafka import Producer

from schemas import settings


class RoundProducer:
    """Produces round lifecycle events to the round-events Kafka topic.

    Covers the full lifecycle of a boxing round: start, end (with stats),
    and an end-of-session summary. All messages are keyed by user_id to
    guarantee per-user partition affinity.

    Key: user_id (ALWAYS — restriction C-02)
    Topic: round-events
    """

    def __init__(self) -> None:
        self.topic = settings.KAFKA_TOPIC_ROUNDS
        self._conf = {
            "bootstrap.servers": settings.KAFKA_BROKERS,
        }
        self._producer = Producer(self._conf)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _now_iso() -> str:
        """Return the current UTC time as an ISO 8601 string.

        Returns:
            ISO 8601 UTC timestamp, e.g. "2024-01-15T10:30:00+00:00".
        """
        return datetime.now(timezone.utc).isoformat()

    def _delivery_callback(self, err: Any, msg: Any) -> None:
        """Log Kafka delivery confirmation or failure.

        Args:
            err: Delivery error from librdkafka, or None on success.
            msg: The delivered Kafka message object.
        """
        if err:
            print(f"[RoundProducer] Delivery failed ERROR: {err}")
        else:
            key = msg.key().decode("utf-8")
            payload = json.loads(msg.value().decode("utf-8"))
            print(
                f"[RoundProducer] Delivered to topic={msg.topic()} "
                f"partition={msg.partition()} "
                f"| key={key} event_type={payload.get('event_type')}"
            )

    def _publish(self, user_id: str, message: dict) -> None:
        """Serialize and publish a message, then poll for delivery events.

        Args:
            user_id: Partition key — MUST match message['user_id'].
            message: Fully-formed event dict conforming to the schema.
        """
        self._producer.produce(
            self.topic,
            key=user_id.encode("utf-8"),
            value=json.dumps(message).encode("utf-8"),
            callback=self._delivery_callback,
        )
        self._producer.poll(0)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send_round_start(
        self,
        user_id: str,
        session_id: str,
        round_number: int,
        duration_seconds: int,
    ) -> None:
        """Publish a round_start event when a new boxing round begins.

        Args:
            user_id: Authenticated user identifier — used as partition key.
            session_id: Training session identifier.
            round_number: 1-based index of the round within the session.
            duration_seconds: Planned duration of the round in seconds
                (e.g. 180 for a 3-minute round).
        """
        message = {
            "user_id": user_id,
            "session_id": session_id,
            "timestamp": self._now_iso(),
            "event_type": "round_start",
            "payload": {
                "round_number": round_number,
                "duration_seconds": duration_seconds,
            },
        }
        self._publish(user_id, message)

    def send_round_end(
        self,
        user_id: str,
        session_id: str,
        round_number: int,
        actual_duration: float,
        punch_count: int,
        avg_dtw_score: float,
        peak_heart_rate: int,
    ) -> None:
        """Publish a round_end event with per-round performance statistics.

        Args:
            user_id: Authenticated user identifier — used as partition key.
            session_id: Training session identifier.
            round_number: 1-based index of the round that just ended.
            actual_duration: Actual elapsed time of the round in seconds.
                May differ from the planned duration if the round was
                stopped early or extended.
            punch_count: Total number of punches detected during the round.
            avg_dtw_score: Mean DTW score across all punches in the round.
                Lower values indicate better technique.
            peak_heart_rate: Highest heart rate (bpm) recorded during
                the round.
        """
        message = {
            "user_id": user_id,
            "session_id": session_id,
            "timestamp": self._now_iso(),
            "event_type": "round_end",
            "payload": {
                "round_number": round_number,
                "actual_duration": actual_duration,
                "punch_count": punch_count,
                "avg_dtw_score": avg_dtw_score,
                "peak_heart_rate": peak_heart_rate,
            },
        }
        self._publish(user_id, message)

    def send_session_summary(
        self,
        user_id: str,
        session_id: str,
        total_rounds: int,
        total_punches: int,
        avg_score: float,
        best_punch_type: str,
        session_duration_seconds: float,
    ) -> None:
        """Publish a session_summary event at the end of a training session.

        This event aggregates metrics across all rounds and is intended for
        downstream analytics and coach review dashboards.

        Args:
            user_id: Authenticated user identifier — used as partition key.
            session_id: Training session identifier.
            total_rounds: Number of rounds completed in the session.
            total_punches: Cumulative punch count across all rounds.
            avg_score: Mean DTW score across all punches in the session.
                Lower values indicate better overall technique.
            best_punch_type: The punch type with the lowest (best) mean
                DTW score, e.g. "jab", "cross", "hook", "uppercut".
            session_duration_seconds: Total wall-clock duration of the
                session in seconds, including rest periods between rounds.
        """
        message = {
            "user_id": user_id,
            "session_id": session_id,
            "timestamp": self._now_iso(),
            "event_type": "session_summary",
            "payload": {
                "total_rounds": total_rounds,
                "total_punches": total_punches,
                "avg_score": avg_score,
                "best_punch_type": best_punch_type,
                "session_duration_seconds": session_duration_seconds,
            },
        }
        self._publish(user_id, message)

    def flush(self, timeout: float = 10.0) -> None:
        """Wait for all outstanding messages to be delivered.

        Args:
            timeout: Maximum seconds to wait for delivery. Defaults to 10.
        """
        self._producer.flush(timeout)
