---
name: architecture-diagrams
description: Apply this skill when generating architecture diagrams, ERDs, sequence diagrams, or flow diagrams for the boxing app. Contains Mermaid templates for all key flows with the exact component names. Trigger on: "generate diagram", "architecture diagram", "sequence diagram", "ERD", "mermaid", "system diagram", "flow diagram", "data flow", "component diagram", "visualize".
---

# Architecture Diagrams — mobile-boxing-app

## Output location
All diagrams go in `docs/diagrams/<category>/`:
```
docs/diagrams/
├── architecture/     # System-level diagrams
├── data/             # ERDs, data flows
├── sequences/        # Request/response flows
└── pipelines/        # ML, ETL pipelines
```

## 1. Real-time inference pipeline

```mermaid
flowchart TD
    A[Mobile Camera\nreact-native-vision-camera] -->|frame at 30fps| B[TFLite on-device\n33 landmarks x,y,z]
    B -->|JSON landmark array| C[WebSocket Client\nrealtimePoseService.ts]
    C -->|WS /boxing/ws/jab| D[FastAPI WS Handler\nroutes/boxing.py]
    D -->|asyncio.create_task| E[Redis Window Buffer\n30 frames exact]
    D -->|immediate response| C
    E -->|buffer full trigger| F[DTW Scorer\ndtaidistance]
    F -->|score 0-100| G[SVM/RF Classifier\nscikit-learn]
    G -->|punch_type + score| H[Feedback Engine\nfeedback_engine.py]
    H -->|text feedback| I[WebSocket Response\nto mobile UI]
    F -->|asyncio.create_task| J[Kafka Producer\ntechnical-metrics]
    J -->|user_id as key| K[Kafka Topic\ntechnical-metrics]
    K -->|Phase 2| L[Databricks\nBronze Layer]
```

## 2. MongoDB Collections ERD

```mermaid
erDiagram
    users {
        ObjectId id PK
        string email
        string name
        ObjectId role FK
        bool email_verified
        string hashed_password
        string provider
        datetime created_at
        datetime updated_at
    }
    roles {
        ObjectId id PK
        string name
    }
    trainings {
        ObjectId id PK
        string user_id FK
        string title
        string status
        datetime started_at
        datetime ended_at
        datetime created_at
    }
    exercises {
        ObjectId id PK
        string title
        ObjectId category FK
        ObjectId difficulty FK
        string poster_url
        string video_url
        string technique
        list muscles
        list equipment
    }
    boxing_sessions {
        ObjectId id PK
        string session_id
        string user_id FK
        string processed_filename
        int frames_analyzed
        list feedback_summary
        string metrics_path
        datetime created_at
    }
    consents {
        ObjectId id PK
        string user_id FK
        string consent_type
        bool granted
        datetime granted_at
        datetime revoked_at
        string policy_version
    }
    auth_codes {
        ObjectId id PK
        string code
        string user_email FK
        datetime expires_at
    }

    users ||--o{ trainings : "has"
    users ||--o{ boxing_sessions : "has"
    users ||--o{ consents : "has"
    users ||--|| roles : "assigned"
    exercises ||--|| roles : "difficulty"
```

## 3. Kafka event flow

```mermaid
sequenceDiagram
    participant SW as Smartwatch
    participant Mobile as Mobile App
    participant Producer as Kafka Producer
    participant Kafka as Kafka Broker
    participant Consumer as Kafka Consumer
    participant Redis as Redis Buffer
    participant API as FastAPI

    SW->>Mobile: BLE heartrate data
    Mobile->>Producer: smartwatch_producer.py
    Producer->>Kafka: health-metrics (key=user_id)

    Mobile->>API: WebSocket /ws/jab
    API->>Producer: technique_producer.py (asyncio.create_task)
    Producer->>Kafka: technical-metrics (key=user_id)

    Kafka->>Consumer: smartwatch_consumer.py
    Consumer->>Redis: append_message() LPUSH
    API->>Redis: GET /kafka/smartwatch/messages
```

## 4. Authentication flow (Google PKCE)

```mermaid
sequenceDiagram
    participant Mobile as Mobile App
    participant Backend as FastAPI Backend
    participant Google as Google OAuth

    Mobile->>Mobile: Generate PKCE (verifier + challenge)
    Mobile->>Backend: GET /auth/login/google?code_challenge=...
    Backend->>Mobile: redirect_url to Google
    Mobile->>Google: Open browser with auth URL
    Google->>Mobile: Callback with auth_code (via deep link gymshock://)
    Mobile->>Backend: POST /auth/mobile/token {code, code_verifier}
    Backend->>Google: Exchange code for user info
    Google->>Backend: user profile (email, name)
    Backend->>Mobile: {access_token, refresh_token, user}
    Mobile->>Mobile: Persist tokens to AsyncStorage
```

## 5. Medallion data architecture (Phase 2)

```mermaid
flowchart LR
    subgraph Sources
        K1[Kafka\nhealth-metrics]
        K2[Kafka\ntechnical-metrics]
        K3[Kafka\nround-events]
    end
    subgraph Bronze
        B1[Raw health events]
        B2[Raw landmark windows]
        B3[Raw round events]
    end
    subgraph Silver
        S1[Cleaned HR data]
        S2[Kalman-filtered\nlandmarks]
        S3[Joined sessions]
    end
    subgraph Gold
        G1[HR vs Punch\nPrecision]
        G2[Fatigue\nDetection]
        G3[Session\nSummaries]
    end

    K1 --> B1 --> S1 --> G1
    K2 --> B2 --> S2 --> G1
    K2 --> B2 --> S2 --> G2
    K3 --> B3 --> S3 --> G3
```

## Conventions for new diagrams
- Use exact component names from the codebase (not generic names)
- Include file paths where relevant
- For sequence diagrams: show the data format at each step
- For ERDs: include index fields, mark FK relationships
- Save as `docs/diagrams/<category>/<name>.md` with the mermaid block
