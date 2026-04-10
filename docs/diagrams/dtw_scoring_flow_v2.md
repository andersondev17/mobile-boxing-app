```mermaid
flowchart TD
    A[Mobile App - WebSocket Payload] -->|Consent Verified| B[Backend API]
    B -->|Filter strict DTW_FEATURE_ORDER| C{Redis Window Buffer}
    C -->|Wait until len == 30| D[DTW Process]
    
    D -->|1. Normalize vector| E[Normalize (angle/180, speed/15)]
    E -->|2. Compute distance vs Synthetic Enriched Baseline| F[dtaidistance Nd]
    F -->|3. Score exp(-dist / 10.0)| G[Score 0-100]
    
    G -->|>=80 Good, >=50 Acceptable| H[Publish Kafka Events]
    H -->|Return JSON| A
```
