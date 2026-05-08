"""

Technique analysis Kafka producer.



Publishes landmark windows, DTW scores, and punch detection events

to the 'technical-metrics' topic with user_id as partition key.



Restriction C-01: NEVER include raw image or video bytes in any payload.

Restriction C-02: user_id is ALWAYS the partition key.

"""



import json

from datetime import datetime, timezone

from typing import Any



from confluent_kafka import Producer



from schemas import settings





class TechniqueProducer:

    """Produces technique analysis events to the technical-metrics Kafka topic.



    Publishes landmark window snapshots, DTW comparison scores, and

    real-time punch detection events. All messages are keyed by user_id

    to guarantee per-user partition affinity.



    Key: user_id (ALWAYS — restriction C-02)

    Topic: technical-metrics

    """



    def __init__(self) -> None:

        self.topic = settings.KAFKA_TOPIC_TECHNIQUE

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

            print(f"[TechniqueProducer] Delivery failed ERROR: {err}")

        else:

            key = msg.key().decode("utf-8")

            payload = json.loads(msg.value().decode("utf-8"))

            print(

                f"[TechniqueProducer] Delivered to topic={msg.topic()} "

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



    def send_technique_event(

        self,

        user_id: str,

        session_id: str,

        event_type: str,

        payload: dict,

    ) -> None:

        """Publish a generic technique event to the technical-metrics topic.



        This is the low-level method used by the specialised helpers below.

        Prefer ``send_landmark_window``, ``send_punch_detected``, or

        ``send_dtw_score`` for structured events.



        Args:

            user_id: Authenticated user identifier — used as partition key.

            session_id: Training session identifier.

            event_type: One of "landmark_window", "punch_detected",

                "dtw_score", or a custom string for extension.

            payload: Event-specific data dict. Must NOT contain raw image

                or video bytes (restriction C-01).

        """

        message = {

            "user_id": user_id,

            "session_id": session_id,

            "timestamp": self._now_iso(),

            "event_type": event_type,

            "payload": payload,

        }

        self._publish(user_id, message)



    def send_landmark_window(

        self,

        user_id: str,

        session_id: str,

        landmarks: list[list[dict]],

        fps: int = 30,

        frame_start: int = 0,

    ) -> None:

        """Publish a sliding window of MediaPipe pose landmarks.



        Each element in ``landmarks`` is a list of 33 dicts with keys

        ``x``, ``y``, ``z`` (float32). Raw image/video data must NEVER

        be included (restriction C-01).



        Args:

            user_id: Authenticated user identifier — used as partition key.

            session_id: Training session identifier.

            landmarks: List of frames; each frame is a list of 33 landmark

                dicts ``[{"x": float, "y": float, "z": float}, ...]``.

            fps: Frames per second of the source video stream. Defaults to 30.

            frame_start: Index of the first frame in this window within

                the session timeline.

        """

        payload = {

            "landmarks": landmarks,

            "fps": fps,

            "frame_start": frame_start,

        }

        self.send_technique_event(user_id, session_id, "landmark_window", payload)



    def send_punch_detected(

        self,

        user_id: str,

        session_id: str,

        punch_type: str,

        dtw_score: float,

        frame_index: int,

    ) -> None:

        """Publish a punch detection event with its DTW quality score.



        Args:

            user_id: Authenticated user identifier — used as partition key.

            session_id: Training session identifier.

            punch_type: Punch classification label, e.g. "jab", "cross",

                "hook", "uppercut".

            dtw_score: Dynamic Time Warping similarity score against the

                reference template. Lower is better (0 = perfect match).

            frame_index: Frame number within the session at which the

                punch impact was detected.

        """

        payload = {

            "punch_type": punch_type,

            "dtw_score": dtw_score,

            "frame_index": frame_index,

        }

        self.send_technique_event(user_id, session_id, "punch_detected", payload)



    def send_dtw_score(

        self,

        user_id: str,

        session_id: str,

        punch_type: str,

        dtw_score: float,

        frame_index: int,

    ) -> None:

        """Publish a standalone DTW score for post-analysis pipelines.



        Use this when you want to record a DTW measurement without a full

        punch detection event (e.g. for continuous quality monitoring).



        Args:

            user_id: Authenticated user identifier — used as partition key.

            session_id: Training session identifier.

            punch_type: Punch type the score refers to.

            dtw_score: Dynamic Time Warping similarity score.

            frame_index: Frame number within the session.

        """

        payload = {

            "punch_type": punch_type,

            "dtw_score": dtw_score,

            "frame_index": frame_index,

        }

        self.send_technique_event(user_id, session_id, "dtw_score", payload)



    def flush(self, timeout: float = 10.0) -> None:

        """Wait for all outstanding messages to be delivered.



        Args:

            timeout: Maximum seconds to wait for delivery. Defaults to 10.

        """

        self._producer.flush(timeout)

