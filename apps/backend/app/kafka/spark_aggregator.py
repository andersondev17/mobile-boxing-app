"""
PySpark Structured Streaming Aggregator.
Consumes 'health-metrics' and produces aggregated metrics to 'health-enriched'.
"""

import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, window, avg, max, stddev
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType, TimestampType

# Topic names
KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BROKERS", "localhost:19092")
TOPIC_RAW = "health-metrics"
TOPIC_ENRICHED = "health-enriched"

schema = StructType([
    StructField("user_id", StringType(), True),
    StructField("timestamp", StringType(), True),
    StructField("telemetry", StructType([
        StructField("heart_rate", StructType([
            StructField("value", IntegerType(), True),
            StructField("hr_variability", IntegerType(), True)
        ])),
        StructField("load_metrics", StructType([
            StructField("fatigue_index", DoubleType(), True),
            StructField("training_load", DoubleType(), True)
        ]))
    ]))
])

def start_aggregator():
    spark = SparkSession.builder \
        .appName("BoxingStreamAggregator") \
        .getOrCreate()
        
    spark.sparkContext.setLogLevel("WARN")

    # Read from Kafka
    raw_df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP) \
        .option("subscribe", TOPIC_RAW) \
        .load()

    # Parse JSON
    parsed_df = raw_df.selectExpr("CAST(value AS STRING)") \
        .select(from_json(col("value"), schema).alias("data")) \
        .select("data.*") \
        .withColumn("ts", col("timestamp").cast(TimestampType()))

    # Windowed Aggregation (1 minute window, 30s sliding)
    agg_df = parsed_df \
        .withWatermark("ts", "2 minutes") \
        .groupBy(
            window(col("ts"), "1 minute", "30 seconds"),
            col("user_id")
        ) \
        .agg(
            avg("telemetry.heart_rate.value").alias("avg_heart_rate"),
            max("telemetry.load_metrics.fatigue_index").alias("max_fatigue"),
            avg("telemetry.heart_rate.hr_variability").alias("avg_hrv")
        ) \
        .selectExpr("user_id", "to_json(struct(*)) AS value")

    # Write back to Kafka
    query = agg_df.writeStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP) \
        .option("topic", TOPIC_ENRICHED) \
        .option("checkpointLocation", "/tmp/spark-checkpoints") \
        .start()

    query.awaitTermination()

if __name__ == "__main__":
    start_aggregator()
