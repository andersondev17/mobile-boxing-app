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

        

        # Add security configuration for Confluent Cloud

        if settings.KAFKA_SECURITY_PROTOCOL != "PLAINTEXT":

            self.conf.update({

                "security.protocol": settings.KAFKA_SECURITY_PROTOCOL,

                "sasl.mechanism": settings.KAFKA_SASL_MECHANISM,

                "sasl.username": settings.KAFKA_SASL_USERNAME,

                "sasl.password": settings.KAFKA_SASL_PASSWORD,

            })



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



    def gen_sample(self, device_id="dev-01", user_id="user-1", seq=0, session_phase="warmup"):

        """Generate realistic smartwatch telemetry with progressive fatigue and calorie tracking."""

        

        # Progressive patterns based on session phase

        if session_phase == "warmup":

            base_hr = random.randint(80, 110)

            activity_intensity = random.uniform(0.3, 0.6)

        elif session_phase == "intense":

            base_hr = random.randint(140, 180)

            activity_intensity = random.uniform(0.8, 1.0)

        elif session_phase == "cooldown":

            base_hr = random.randint(90, 120)

            activity_intensity = random.uniform(0.4, 0.7)

        else:  # steady

            base_hr = random.randint(120, 150)

            activity_intensity = random.uniform(0.6, 0.8)

        

        # Add realistic variation

        hr = base_hr + random.randint(-10, 10)

        hr = max(60, min(200, hr))  # Clamp to realistic range

        

        # Heart rate variability (decreases with intensity)

        hr_variability = max(20, 80 - int((hr - 60) * 0.5))

        

        # Progressive fatigue

        fatigue_increment = seq * 0.002  # Gradual fatigue increase

        fatigue_index = min(0.95, round(random.uniform(0.1 + fatigue_increment, 0.9 + fatigue_increment), 2))

        

        # Training load based on heart rate and duration

        training_load = round(((hr - 60) / 140) * activity_intensity * 50, 1)

        

        # Recovery score decreases with fatigue

        recovery_score = max(10, 100 - int(fatigue_index * 80))

        

        # Calorie calculation (simplified MET-based formula)

        met_value = 4.0 * activity_intensity  # Boxing METs range 4-12

        calories_per_minute = met_value * 70 / 200  # Assuming 70kg user

        calories_burned = round(calories_per_minute * 0.5, 1)  # 30-second intervals

        

        # Additional biometric metrics

        steps = random.randint(0, 50) if activity_intensity > 0.7 else 0

        punch_count = random.randint(0, 10) if activity_intensity > 0.6 else 0

        

        return {

            "device_id": device_id,

            "user_id": user_id,

            "timestamp": self._now_iso(),

            "telemetry": {

                "heart_rate": {

                    "value": hr,

                    "unit": "bpm",

                    "hr_variability": hr_variability,

                    "resting_hr": 65  # User's baseline

                },

                "load_metrics": {

                    "fatigue_index": fatigue_index,

                    "training_load": training_load,

                    "recovery_score": recovery_score,

                    "calories_burned": calories_burned,

                    "session_calories": round(seq * calories_per_minute * 0.5, 1)

                },

                "activity": {

                    "type": "boxing" if hr > 120 else "idle",

                    "confidence": activity_intensity,

                    "intensity_zone": self._get_hr_zone(hr),

                    "steps_count": steps,

                    "punch_count": punch_count

                },

                "biometrics": {

                    "skin_temperature": round(random.uniform(32.0, 37.0), 1),

                    "sweat_level": round(fatigue_index * 100, 0),  # 0-100%

                    "movement_efficiency": round(100 - fatigue_index * 50, 1)

                }

            },

            "sequence": seq,

            "session_phase": session_phase

        }

    

    def _get_hr_zone(self, hr):

        """Determine heart rate training zone."""

        age = 30  # Assumed user age

        max_hr = 220 - age

        

        if hr < 0.5 * max_hr:

            return "rest"

        elif hr < 0.6 * max_hr:

            return "fat_burn"

        elif hr < 0.7 * max_hr:

            return "cardio"

        elif hr < 0.85 * max_hr:

            return "peak"

        else:

            return "maximum"



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

        """Run the producer in an infinite loop simulating realistic training sessions."""

        kafka_producer = Producer(self.conf)

        seq = 0

        session_cycle = 0

        

        # Session phases progression

        phases = ["warmup", "steady", "intense", "intense", "cooldown"]

        phase_duration = 20  # Messages per phase

        

        try:

            while True:

                # Determine current phase

                phase_index = (seq // phase_duration) % len(phases)

                current_phase = phases[phase_index]

                

                # Generate realistic user IDs for simulation

                user_ids = ["user-1", "user-2", "user-3"]

                user_id = user_ids[session_cycle % len(user_ids)]

                

                # Generate sample with current phase

                message = self.gen_sample(

                    device_id=f"dev-{(session_cycle % 3) + 1:02d}",

                    user_id=user_id,

                    seq=seq,

                    session_phase=current_phase

                )

                

                self.send_message(kafka_producer, message)

                

                # Progress counters

                seq += 1

                

                # New session every full cycle

                if seq % (len(phases) * phase_duration) == 0:

                    session_cycle += 1

                    print(f"\n=== New Training Session #{session_cycle} ===\n")

                

                # Vary timing based on intensity

                if current_phase == "intense":

                    time.sleep(0.3)  # Faster during intense activity

                elif current_phase == "cooldown":

                    time.sleep(0.8)  # Slower during cooldown

                else:

                    time.sleep(0.5)  # Normal pace

                    

        except KeyboardInterrupt:

            print("Stopping smartwatch producer...")

        finally:

            kafka_producer.flush(10)

            print("Producer stopped cleanly.")





if __name__ == "__main__":

    SmartWatchProducer().start()

