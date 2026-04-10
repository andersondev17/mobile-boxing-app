flowchart TD
    A[Mobile App] -->|WebSocket: Biometric Data| B(Backend API)
    
    B -->|Frames| C{Redis Window Buffer}
    C -->|30-frame window| D[DTW Scorer]
    C -->|30-frame window| E[Punch Classifier RF]
    
    D -->|Similarity Score| F[Gate & Logic]
    E -->|Punch Class Probabilities| F
    
    F -->|Validation| G{Is valid punch?}
    
    G -->|Yes| H[Generate Feedback & Label]
    G -->|No| I[Ignore]
    
    H -->|Scores & Feedback| B
    B -->|WebSocket Response| A
