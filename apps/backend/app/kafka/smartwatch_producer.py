"""
Smartwatch telemetry Kafka producer.

Generates simulated smartwatch health data and publishes
to the 'health-metrics' topic with user_id as partition key.
"""

import json
import time
import random
from datetime import datetime, timezone

from confluent_kafka import Producer

from schemas import settings


class SmartWatchProducer:
    """Produces simulated smartwatch telemetry to Kafka.

    Key: user_id (ALWAYS — see restriction #2)
    Topic: health-metrics
    """

    def __init__(self):
        self.topic = settings.KAFKA_TOPIC_HEALTH
        self.conf = {
            "bootstrap.servers": settings.KAFKA_BROKERS,
        }

    def delivery(self, err, msg):
        if err:
            print(f"Delivery failed ERROR: {err}")
        else:
            key = msg.key().decode("UTF-8")
            payload = json.loads(msg.value().decode("UTF-8"))
            print(
                f"Delivered to topic={msg.topic()} partition={msg.partition()} "
                f"| key={key}, user_id={payload.get('user_id')}"
            )

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def gen_sample(self, device_id="dev-01", user_id="user-1", seq=0):
        """Generate a single smartwatch telemetry sample with Load/Fatigue metrics."""
        hr = random.randint(60, 160)
        # Derived metrics
        hr_variability = random.randint(40, 80)
        fatigue_index = round(random.uniform(0.1, 0.9), 2)
        training_load = round(random.uniform(5.0, 50.0), 1)
        recovery_score = random.randint(10, 100)

        return {
            "device_id": device_id,
            "user_id": user_id,
            "timestamp": self._now_iso(),
            "telemetry": {
                "heart_rate": {
                    "value": hr,
                    "unit": "bpm",
                    "hr_variability": hr_variability
                },
                "load_metrics": {
                    "fatigue_index": fatigue_index,
                    "training_load": training_load,
                    "recovery_score": recovery_score
                },
                "activity": {
                    "type": "boxing" if hr > 120 else "idle",
                    "confidence": 0.95
                }
            },
            "sequence": seq,
        }

    def send_message(self, producer, message):
        # RESTRICTION #2: user_id ALWAYS as partition key
        key = message["user_id"]
        producer.produce(
            self.topic,
            key=key,
            value=json.dumps(message).encode("UTF-8"),
            callback=self.delivery,
        )
        producer.poll(0)
        time.sleep(0.5)

    def start(self):
        """Run the producer in an infinite loop (for development/testing)."""
        kafka_producer = Producer(self.conf)
        seq = 0
        try:
            while True:
                message = self.gen_sample(seq=seq)
                self.send_message(kafka_producer, message)
                seq += 1
        except KeyboardInterrupt:
            print("Stopping...")
        finally:
            kafka_producer.flush(10)


if __name__ == "__main__":
    SmartWatchProducer().start()
