# CLAUDE.md — mobile-boxing-app

## Proyecto
App móvil de entrenamiento de boxeo con análisis de técnica en tiempo real.
Monorepo en `boxing-api/` con dos workspaces: `apps/backend/` y `apps/mobile/`.

## Stack real (estado actual — branch: feature/sprint1-mongodb-migration)

| Capa | Tecnología | Estado |
|------|-----------|--------|
| Backend | FastAPI 0.120 + Uvicorn, Python 3.11 | ✅ Funcional |
| DB | MongoDB 7 Docker (motor + Beanie ODM) | ✅ Funcional |
| Cache | Redis 7 Docker (256MB LRU) | ✅ Funcional |
| Streaming | Kafka 1-nodo KRaft Docker (sin Zookeeper) | ✅ Funcional |
| Auth | JWT (HS256) + Google OAuth PKCE | ✅ Funcional |
| Mobile | React Native + Expo SDK 54 + Expo Dev Build | ✅ Funcional |
| ML Fase 1 | Heurísticas (sin DTW aún) | ⚠️ Parcial |
| TFLite on-device | No implementado (mobile envía base64) | ❌ Pendiente |
| Consentimiento | routes/consent.py existe, falta flujo mobile | ⚠️ Parcial |

## Restricciones permanentes (NUNCA violar — en ningún archivo)

1. **C-01**: NUNCA almacenar video ni bytes de imagen — solo landmarks `[[x,y,z]]` float32
2. **C-02**: `user_id` SIEMPRE como key de partición en Kafka (no `device_id`)
3. **C-03**: Ventanas de inferencia: EXACTAMENTE 30 frames = 1 segundo a 30fps
4. **C-04**: NO ST-GCN hasta tener GPU — usar DTW + SVM/RF en Fase 1
5. **C-05**: Consentimiento explícito (Ley 1581 Colombia) antes de persistir cualquier dato biométrico
6. **C-06**: WebSocket debe responder al cliente en menos de 100ms

## Estructura de carpetas

```
boxing-api/
├── .claude/
│   ├── CLAUDE.md              # Este archivo
│   ├── agents/                # 11 subagentes del proyecto
│   └── skills/                # 20 skills del proyecto
├── apps/
│   ├── backend/
│   │   ├── docker-compose.yml # MongoDB + Kafka + Redis + backend
│   │   ├── .env.example       # Variables requeridas
│   │   └── app/
│   │       ├── main.py        # FastAPI entry, 7 routers, lifespan
│   │       ├── auth/          # JWT + Google OAuth PKCE
│   │       ├── config/        # database.py (Beanie init), seed.py
│   │       ├── kafka/         # Producers, consumers, Redis storage
│   │       ├── ml_service/    # Boxing analysis pipeline
│   │       ├── models/        # Beanie Documents: User, BoxingSession, Consent...
│   │       ├── routes/        # boxing, training, exercise, user, consent, kafka
│   │       └── schemas/       # Pydantic schemas + env.py (Settings)
│   └── mobile/
│       ├── app/               # Expo Router screens (auth, tabs, exercises, realtime)
│       ├── lib/               # api/ (auth.ts, client.ts), config/, db/, utils/
│       ├── store/             # authStore.ts (Zustand)
│       ├── services/          # realtimePoseService.ts, exerciseService.ts...
│       ├── hooks/             # useSavedExercises.ts
│       ├── interfaces/        # interfaces.d.ts (JabRealtimeFramePayload...)
│       └── types/             # auth.d.ts, type.d.ts
└── docs/
    └── diagrams/              # Mermaid + Excalidraw (por crear)
```

## Qué funciona hoy (MVP básico)
- Auth completo: registro email, login, Google OAuth PKCE, refresh token
- Catálogo de ejercicios: CRUD, seeding con 4 ejercicios iniciales
- WebSocket de jab (`/boxing/ws/jab`): acepta landmarks, retorna feedback heurístico
- Kafka health-metrics: producer fake + consumer → Redis buffer
- Consentimiento: endpoint `/consent/` para grant/revoke (Ley 1581)
- Docker Compose: levanta todo el stack en un comando

## Issues pendientes (Sprint actual)

### Críticos
- **C-01 violation**: `realtimePoseService.ts` en mobile envía base64 frames, no landmarks
- **C-02 violation**: `kafka/smartwatch_producer.py` usa `device_id` como key (debe ser `user_id`)
- **DTW pipeline**: no existe — `ml_service/` solo tiene heurísticas hardcodeadas
- **TFLite on-device**: no implementado — mobile usa `expo-camera` con base64

### Importantes
- Residual: `react-native-appwrite` en `package.json` mobile (no se usa)
- `feature_extractor.py` solo tiene 2 features (`elbow_angle`, `forward_extent`) — necesita `shoulder_rotation`, `hip_rotation`, `guard_distance`
- CORS abierto `allow_origins=["*"]` — restringir antes de producción
- Falta flujo de consentimiento en mobile (pantallas de onboarding con Ley 1581)

## Kafka topics
| Topic | Key | Propósito |
|-------|-----|-----------|
| `health-metrics` | `user_id` | HR, pasos, calorías del smartwatch |
| `technical-metrics` | `user_id` | Ventanas de landmarks, scores DTW |
| `round-events` | `user_id` | Inicio/fin de round, resumen de sesión |

## Modos light (para no explotar los 8GB de RAM)
```bash
# Solo ML (desarrollo del pipeline de inferencia)
EXPO_PUBLIC_MODE=technique BACKEND_MODULES=ml docker-compose up mongodb redis backend

# Solo auth
EXPO_PUBLIC_MODE=auth BACKEND_MODULES=auth docker-compose up mongodb backend

# Todo
docker-compose up
```

## Modelos Beanie (MongoDB)
- `User` — email, name, role, provider, email_verified, created_at
- `Role` — name
- `Training` — user_id, title, status, started_at, ended_at
- `Exercise` — title, category, difficulty, poster_url, video_url, technique, muscles
- `Category`, `Difficulty` — listas de referencia
- `BoxingSession` — session_id, user_id, frames_analyzed, feedback_summary, metrics_path
- `Consent` — user_id, consent_type, granted, granted_at, revoked_at, policy_version
- `AuthCode` — code, user_email, expires_at (TTL 2min, OAuth temporal)

## Subagentes disponibles
| Agente | Territorio | Cuándo invocar |
|--------|-----------|----------------|
| `backend-builder` | apps/backend/ | Endpoints, schemas, modelos Beanie, Kafka producers |
| `mobile-dev` | apps/mobile/ | Screens, hooks, WebSocket client, TFLite |
| `ml-researcher` | apps/backend/app/ml_service/ | DTW pipeline, clasificador, buffer |
| `code-reviewer` | Todo el proyecto | Revisión antes de merge, auditorías |
| `kafka-data-eng` | apps/backend/app/kafka/ | Topics, producers, schemas de eventos |
| `boxing-domain-expert` | Consultor | Validar umbrales ML antes de commitear |
| `data-architect` | Consultor | Nuevas colecciones o decisiones de modelado |
| `legal-expert` | Consultor (global) | Cambios que tocan datos de usuarios |
| `business-strategist` | Consultor (global) | Decisiones de negocio y roadmap |
| `devops-engineer` | docker-compose, .env | Infraestructura, modos light, CI/CD |
| `debugger` | Todo (read-only) | Bugs y comportamientos inesperados |
| `databricks-analyst` | apps/notebooks/ | Analytics Fase 2+ |
| `diagram-generator` | docs/diagrams/ | Diagramas de arquitectura |

## Reglas de operación del coordinador
1. `boxing-domain-expert` valida TODA decisión ML antes de commitear
2. `legal-expert` aprueba cambios que tocan datos de usuario
3. NUNCA violar las 6 restricciones permanentes
4. Usar modos light para testear (no levantar el stack completo innecesariamente)
5. `/compact` antes de cambiar de módulo para mantener el contexto limpio
