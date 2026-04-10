---
name: databricks-patterns
description: Apply this skill when writing Spark notebooks for Databricks Community Edition: Bronze/Silver/Gold data pipeline from Kafka, Kalman filter on landmarks, HR vs punch precision analysis. This is a Phase 2+ skill. Trigger on: "databricks", "spark notebook", "bronze layer", "silver layer", "gold layer", "medallion", "kalman filter", "hr vs precision", "spark streaming", "databricks community".
---

# Databricks Patterns — mobile-boxing-app (Phase 2+)

## Environment
- Databricks Community Edition (free tier)
- No GPU available
- Cluster auto-terminates after 2 hours — always checkpoint
- Spark 3.5+ with Kafka connector

## Medallion Architecture

```
Kafka (Docker local / Confluent Cloud)
    ↓
Bronze: raw events (no transformation)
    ↓
Silver: cleaned + Kalman-filtered landmarks
    ↓
Gold: HR vs punch precision, fatigue detection
```

## Bronze Layer — Kafka ingestion

```python
# bronze/01_ingest_health_metrics.ipynb

# Read from Kafka (streaming)
health_raw = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", dbutils.secrets.get("boxing", "kafka_brokers"))
    .option("subscribe", "health-metrics")
    .option("startingOffsets", "earliest")
    .option("kafka.group.id", "databricks-bronze-health")
    .load()
)

# Parse JSON value
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StringType, TimestampType, DoubleType

health_schema = StructType() \
    .add("user_id", StringType()) \
    .add("device_id", StringType()) \
    .add("timestamp", StringType()) \
    .add("telemetry", StructType()
        .add("heart_rate", StructType()
            .add("value", DoubleType())
            .add("confidence", DoubleType())
        )
        .add("activity", StructType()
            .add("type", StringType())
        )
    )

health_parsed = health_raw.select(
    from_json(col("value").cast("string"), health_schema).alias("data"),
    col("timestamp").alias("kafka_ts")
).select("data.*", "kafka_ts")

# Write to Delta Lake (Bronze)
(
    health_parsed.writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", "/dbfs/boxing/checkpoints/bronze_health")
    .table("boxing_bronze.health_metrics")
)
```

## Silver Layer — Kalman filter on landmarks

```python
# silver/01_clean_landmarks.ipynb

import numpy as np

def kalman_filter_landmarks(landmark_sequence: list) -> list:
    """Apply Kalman filter to smooth noisy landmark coordinates.

    Args:
        landmark_sequence: List of 30 landmark arrays [[x,y,z] x33].

    Returns:
        Smoothed landmark sequence of same length.
    """
    # Simple 1D Kalman for each coordinate
    Q = 0.01   # process noise
    R = 0.1    # measurement noise
    
    result = []
    for coord_idx in range(3):  # x, y, z
        estimates = []
        P = 1.0
        x_est = landmark_sequence[0][0][coord_idx]
        
        for frame in landmark_sequence:
            # Predict
            P_pred = P + Q
            # Update
            K = P_pred / (P_pred + R)
            measurement = frame[0][coord_idx]
            x_est = x_est + K * (measurement - x_est)
            P = (1 - K) * P_pred
            estimates.append(x_est)
        result.append(estimates)
    
    return result

# Register as Spark UDF
from pyspark.sql.functions import udf
kalman_udf = udf(kalman_filter_landmarks)
```

## Gold Layer — HR vs Punch Precision

```python
# gold/01_hr_vs_precision.ipynb

# Join health (HR) with technical (punch scores) on user_id + time window
from pyspark.sql.functions import window, avg, max as spark_max

health_windowed = (
    health_silver
    .groupBy("user_id", window("timestamp", "30 seconds"))
    .agg(avg("heart_rate").alias("avg_hr"))
)

technique_windowed = (
    technique_silver
    .filter("punch_type != 'null'")
    .groupBy("user_id", window("timestamp", "30 seconds"))
    .agg(avg("dtw_score").alias("avg_score"), spark_max("dtw_score").alias("peak_score"))
)

# Join
hr_precision = health_windowed.join(
    technique_windowed,
    on=["user_id", "window"],
    how="inner"
)

# Analysis: does high HR correlate with lower score?
hr_precision.groupBy("user_id").agg(
    avg("avg_hr").alias("session_avg_hr"),
    avg("avg_score").alias("session_avg_score")
).orderBy("session_avg_score", ascending=False)
```

## Watermarks (handle late mobile data)
```python
# Mobile may send data 30s late (WiFi reconnection burst)
df.withWatermark("timestamp", "30 seconds")
```

## Checkpointing (critical — cluster auto-terminates)
```python
# Always include checkpoint location for streaming queries
.option("checkpointLocation", "/dbfs/boxing/checkpoints/<job_name>")
```

## Cluster settings for Community Edition
- Runtime: 14.3 LTS (Spark 3.5, Scala 2.12)
- Node type: Standard_DS3_v2 (14GB RAM) — single node
- Auto-terminate: 120 minutes
- Libraries: `dtaidistance`, `scikit-learn` (install via cluster UI or %pip)
