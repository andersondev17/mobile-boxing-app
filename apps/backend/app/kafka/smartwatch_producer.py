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
        """Generate a single smartwatch telemetry sample."""
        hr = random.randint(55, 110)
        return {
            "device_id": device_id,
            "user_id": user_id,
            "manufacturer": "AcmeWatch",
            "model": "AcmeX-2",
            "firmware_version": "1.4.7",
            "timestamp": self._now_iso(),
            "telemetry": {
                "battery": {
                    "level": random.randint(10, 100),
                    "charging": random.choice([False, False, True]),
                },
                "heart_rate": {
                    "value": hr,
                    "unit": "bpm",
                    "confidence": round(random.uniform(0.8, 0.99), 2),
                },
                "steps": {
                    "total": random.randint(0, 15000),
                    "delta": random.randint(0, 20),
                },
                "calories": {
                    "total_kcal": round(random.uniform(100, 900), 1),
                },
                "activity": {
                    "type": random.choice(["idle", "walking", "running", "boxing"]),
                    "confidence": round(random.uniform(0.5, 1.0), 2),
                },
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
