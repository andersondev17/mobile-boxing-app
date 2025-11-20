import json
from confluent_kafka import Consumer, KafkaError
from dotenv import load_dotenv
import os

load_dotenv()

class KafkaConsumer():
    def __init__(self):
        self.topic = os.getenv("KAFKA_TOPIC")
        self.conf = {
            "bootstrap.servers": os.getenv("KAFKA_BROKERS"),
            "group.id": os.getenv("GROUP_ID"),
            "client.id": os.getenv("CLIENT_ID"),
            "session.timeout.ms": int(os.getenv("SESSION_TIMEOUT")),
            "auto.offset.reset": os.getenv("AUTO_OFFSET_RESET")
        }

    def read_message(self, consumer):
        consumer.subscribe([self.topic])
        try:
            while True:
                msg = consumer.poll(0.1)
                if msg is None:
                    continue
                elif msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        print(f"Error ocurred: {msg.error()}")
                else:
                    print(f"Received message: {msg.value().decode('utf-8')}")
                    data = json.loads(msg.value().decode("utf-8"))
                    print(f"Received message | Device: {data['device_id']}, HR: {data['telemetry']['heart_rate']['value']} bpm")
        except KeyboardInterrupt:
            print("Interrupted by user")
        finally:
            consumer.close()

    def start(self):
        kafka_consumer = Consumer(self.conf)
        self.read_message(kafka_consumer)

if __name__ == "__main__":
    smartwatch_consumer = KafkaConsumer()
    smartwatch_consumer.start()