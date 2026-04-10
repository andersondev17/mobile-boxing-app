---
name: filesystem-patterns
description: Apply this skill when navigating the boxing-api project structure, creating new files, or determining the correct location for new code. Contains the canonical folder layout and naming conventions. Trigger on: "where should I put", "folder structure", "file location", "create file", "project structure", "where does this go", "new route file", "new model file", "new screen".
---

# Filesystem Patterns — boxing-api

## Root structure
```
boxing-api/                       # Monorepo root
├── .claude/
│   ├── CLAUDE.md                 # Project context (always read first)
│   ├── agents/                   # 11 project subagents
│   └── skills/                   # 20 project skills
├── .mcp.json                     # MCP server configuration
├── apps/
│   ├── backend/
│   │   ├── docker-compose.yml    # All Docker services
│   │   ├── .env.example          # Template for .env
│   │   └── app/
│   │       ├── main.py           # FastAPI entry point
│   │       ├── Dockerfile
│   │       ├── requirements.txt
│   │       ├── auth/             # JWT + Google OAuth
│   │       ├── config/           # MongoDB init + seeding
│   │       ├── kafka/            # Producers, consumers, Redis storage
│   │       ├── ml_service/       # Boxing analysis pipeline
│   │       ├── models/           # Beanie Documents
│   │       ├── routes/           # FastAPI route handlers
│   │       └── schemas/          # Pydantic + env settings
│   └── mobile/
│       ├── app.json              # Expo config (bundle ID: com.anonymous.gymshock)
│       ├── package.json
│       ├── .env.example
│       ├── app/                  # Expo Router screens
│       │   ├── (auth)/
│       │   ├── (tabs)/
│       │   └── exercises/
│       │       ├── realtime/     # WebSocket analysis
│       │       └── technique/    # Technique guides
│       ├── lib/
│       │   ├── api/              # auth.ts, client.ts
│       │   ├── config/           # env.ts
│       │   ├── db/               # Drizzle SQLite schema
│       │   └── utils/            # pkce.ts, helpers
│       ├── store/                # Zustand stores
│       ├── services/             # API service wrappers
│       ├── hooks/                # Custom React hooks
│       ├── components/           # Reusable UI components
│       ├── interfaces/           # TypeScript .d.ts interfaces
│       └── types/                # TypeScript type definitions
└── docs/
    ├── adr/                      # Architecture Decision Records
    ├── diagrams/                 # Mermaid + Excalidraw
    └── sprints/                  # Sprint specs
```

## Where to put new files

### New FastAPI endpoint
→ `apps/backend/app/routes/<resource>.py`
→ Register router in `apps/backend/app/main.py`

### New Beanie model
→ `apps/backend/app/models/model.py` (general) or new file
→ Register in `apps/backend/app/config/database.py` `document_models` list

### New Pydantic schema
→ `apps/backend/app/schemas/schema.py`

### New ML component
→ `apps/backend/app/ml_service/<component>.py`
(e.g., `dtw_scorer.py`, `window_buffer.py`, `punch_classifier.py`)

### New Kafka producer
→ `apps/backend/app/kafka/<resource>_producer.py`

### New Expo screen
→ `apps/mobile/app/<route>/index.tsx` or `apps/mobile/app/<route>/<screen>.tsx`

### New Zustand store
→ `apps/mobile/store/<name>Store.ts`

### New API service (mobile)
→ `apps/mobile/services/<name>Service.ts`

### New custom hook (mobile)
→ `apps/mobile/hooks/use<Name>.ts`

### New TypeScript type
→ `apps/mobile/types/<name>.d.ts` (simple types)
→ `apps/mobile/interfaces/interfaces.d.ts` (complex interfaces shared across files)

### New diagram
→ `docs/diagrams/<category>/<name>.md`

### New ADR
→ `docs/adr/ADR-NNN-<short-title>.md` (NNN = next sequential number)

## Naming conventions
| Type | Convention | Example |
|------|-----------|---------|
| Python modules | `snake_case.py` | `dtw_scorer.py` |
| Python classes | `PascalCase` | `BoxingJabTracker` |
| Python functions | `snake_case` | `extract_features()` |
| TypeScript files | `camelCase.ts` or `PascalCase.tsx` | `authStore.ts`, `HomeScreen.tsx` |
| TypeScript interfaces | `PascalCase` | `JabRealtimeServerMessage` |
| Expo screens | lowercase with dashes | `realtime/index.tsx` |
| Environment vars | `SCREAMING_SNAKE_CASE` | `KAFKA_TOPIC_HEALTH` |
