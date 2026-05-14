"""Event producers for external integrations (Kafka, etc.)."""

from .technique_producer import TechniqueProducer


def load_messages(*, limit: int = 1, device_id: str) -> list:
    """Stub: query buffered smartwatch telemetry from Redis.

    TODO: Re-implement with actual Redis reader when telemetry pipeline is re-enabled.
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.debug("[STUB] load_messages called: device_id=%s limit=%d", device_id, limit)
    return []
