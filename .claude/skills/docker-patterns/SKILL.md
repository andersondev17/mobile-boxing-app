---
name: docker-patterns
description: Apply this skill when modifying docker-compose.yml, Dockerfiles, or environment configuration for the boxing app. Contains the current service configuration, health check patterns, and volume conventions. Trigger on: "docker compose", "dockerfile", "modify docker", "add service", "container", "docker-compose.yml", "health check", "environment variable", "volume", "networking", "docker".
---

# Docker Patterns — mobile-boxing-app

## docker-compose.yml location
`apps/backend/docker-compose.yml`

## Current services (already correct state)

```yaml
services:
  # ── MongoDB 7 ────────────────────────────────────────────────────────────
  mongodb:
    image: mongo:7
    container_name: boxing-mongodb
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${MONGO_USER}
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD}
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ── Mongo Express (UI) ────────────────────────────────────────────────────
  mongo-express:
    image: mongo-express:latest
    container_name: boxing-mongo-ui
    ports:
      - "8081:8081"
    environment:
      ME_CONFIG_MONGODB_ADMINUSERNAME: ${MONGO_USER}
      ME_CONFIG_MONGODB_ADMINPASSWORD: ${MONGO_PASSWORD}
      ME_CONFIG_MONGODB_SERVER: mongodb
    depends_on:
      mongodb:
        condition: service_healthy

  # ── Redis 7 ──────────────────────────────────────────────────────────────
  redis:
    image: redis:7-alpine
    container_name: boxing-redis
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  # ── Kafka (1-node KRaft, no Zookeeper) ───────────────────────────────────
  kafka:
    image: confluentinc/cp-kafka:7.6.0
    container_name: boxing-kafka
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093,EXTERNAL://0.0.0.0:19092
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092,EXTERNAL://localhost:19092
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka:9093
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_NUM_PARTITIONS: 3
      CLUSTER_ID: boxing-kafka-cluster-001
    ports:
      - "9092:9092"    # Internal (container-to-container)
      - "19092:19092"  # External (host machine access)
    volumes:
      - kafka_data:/var/lib/kafka/data

  # ── FastAPI Backend ───────────────────────────────────────────────────────
  backend:
    build:
      context: .
      dockerfile: app/Dockerfile
    container_name: boxing-backend
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./app:/app
    depends_on:
      mongodb:
        condition: service_healthy
      redis:
        condition: service_healthy

volumes:
  mongodb_data:
  kafka_data:

networks:
  default:
    name: boxing_network
```

## Key networking notes
- Container-to-container: use service names (`mongodb`, `redis`, `kafka:9092`)
- Host-to-container: use `localhost:27017`, `localhost:6379`, `localhost:19092`
- Backend env var `KAFKA_BROKERS=kafka:9092` (inside Docker), `localhost:19092` (outside)

## Adding a new service
1. Add to `docker-compose.yml` under `services:`
2. Add health check if other services depend on it
3. Add environment variables to `.env.example`
4. Verify memory impact: target total < 4GB for all services

## Environment variable pattern
```yaml
# Always load from .env file, never hardcode in docker-compose:
env_file:
  - .env
```

Or reference specific variables:
```yaml
environment:
  MY_VAR: ${MY_VAR}  # from .env
```

## Common commands
```bash
# Start full stack
docker-compose up -d

# Start subset (technique mode)
docker-compose up -d mongodb redis backend

# View logs
docker-compose logs -f backend

# Restart single service
docker-compose restart backend

# Stop all
docker-compose down

# Stop + remove volumes (data wipe)
docker-compose down -v

# Rebuild backend after code changes (with volume mount it's usually not needed)
docker-compose up -d --build backend
```

## Backend Dockerfile patterns
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

For production, remove `--reload` and pin the image digest.


