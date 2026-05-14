"""
Stub technique producer.

The original Kafka-based producer was removed during infrastructure cleanup.
This stub prevents import errors while preserving the interface.

TODO: Re-implement with actual Kafka producer when streaming is re-enabled.
"""

import logging

logger = logging.getLogger(__name__)


class TechniqueProducer:
    """No-op technique producer stub."""

    async def send_punch_detected(
        self,
        user_id: str,
        session_id: str,
        punch_type: str,
        confidence: float,
        dtw_score: float,
        timestamp: str | None = None,
    ) -> None:
        """Log the punch detection event instead of publishing to Kafka."""
        logger.debug(
            "[STUB] Punch detected: user=%s session=%s punch=%s confidence=%.2f dtw=%.2f",
            user_id,
            session_id,
            punch_type,
            confidence,
            dtw_score,
        )
