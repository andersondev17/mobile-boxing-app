import json
import logging

from confluent_kafka import Consumer, KafkaError

from kakfa.storage import append_message
from schemas import settings

logger = logging.getLogger(__name__)


class KafkaConsumer:
    def __init__(self):
        self.topic = settings.KAFKA_TOPIC
        self.conf = {
            "bootstrap.servers": settings.KAFKA_BROKERS,
            "group.id": settings.GROUP_ID,
            "client.id": settings.CLIENT_ID,
            "session.timeout.ms": settings.SESSION_TIMEOUT,
            "auto.offset.reset": settings.AUTO_OFFSET_RESET,
        }

    def _handle_message(self, msg):
        payload = json.loads(msg.value().decode("utf-8"))
        append_message(payload)
        hr = payload.get("telemetry", {}).get("heart_rate", {}).get("value")
        logger.info("Received message | Device=%s HR=%s bpm", payload.get("device_id"), hr)

    def start(self):
        consumer = Consumer(self.conf)
        consumer.subscribe([self.topic])
        try:
            while True:
                msg = consumer.poll(0.1)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() != KafkaError._PARTITION_EOF:
                        logger.error("Consumer error: %s", msg.error())
                    continue
                self._handle_message(msg)
        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user.")
        finally:
            consumer.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    KafkaConsumer().start()
