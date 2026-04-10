---
name: legal-consent
description: Apply this skill when implementing any feature that collects, stores, or processes user data — especially biometric data (landmarks, body pose), health data (heart rate from smartwatch), or personal data. Required for Ley 1581 Colombia compliance. Trigger on: "consent", "ley 1581", "datos biométricos", "biometric data", "privacy", "user data", "datos personales", "consentimiento", "gdpr", "data protection", "onboarding flow", "consent screen", "legal compliance".
---

# Legal Consent — Ley 1581 Colombia

## Scope
This project handles biometric data (body landmarks) and health data (heart rate) for Colombian users. Ley 1581 (2012) + Decreto 1377 (2013) classify both as **sensitive personal data**, requiring explicit opt-in consent before collection or processing.

## 4 Required Consent Types

| ID | Type | Required? | When to show |
|----|------|-----------|--------------|
| `personal_data` | General data treatment | MANDATORY | Registration screen (before signup) |
| `biometric_data` | Landmarks / technique analysis | MANDATORY | Before activating camera |
| `health_data` | Smartwatch HR data | MANDATORY | Before linking wearable |
| `data_sharing` | Anonymized data sale/sharing | OPTIONAL | Settings screen, default OFF |

## MongoDB Consent Model (current implementation)

File: `apps/backend/app/models/boxing.py`

```python
class Consent(Document):
    user_id: str              # Indexed
    consent_type: str         # "personal_data" | "biometric_data" | "health_data" | "data_sharing"
    granted: bool
    granted_at: Optional[datetime]
    revoked_at: Optional[datetime]
    ip_address: Optional[str]
    policy_version: str       # e.g. "v1.0"

    class Settings:
        indexes = [
            IndexModel([("user_id", 1), ("consent_type", 1)], unique=True)
        ]
```

## Backend Consent Endpoints (routes/consent.py)

```
POST /consent/              → Grant or revoke a consent (upsert)
GET  /consent/{user_id}     → List all consents for user
GET  /consent/{user_id}/check?consent_type=biometric_data → Quick gate check
```

## Consent Gate Pattern (use before ANY biometric operation)

```python
# In any endpoint that processes biometric data:
async def _require_consent(user_id: str, consent_type: str) -> None:
    """Raise 403 if user has not granted the required consent.

    Args:
        user_id: Authenticated user's ID.
        consent_type: One of "biometric_data", "health_data", "personal_data".

    Raises:
        HTTPException: 403 if consent is missing or revoked.
    """
    consent = await Consent.find_one(
        Consent.user_id == user_id,
        Consent.consent_type == consent_type,
        Consent.granted == True,
    )
    if not consent:
        raise HTTPException(
            status_code=403,
            detail=f"Se requiere consentimiento '{consent_type}' antes de continuar."
        )

# Usage:
await _require_consent(current_user.id, "biometric_data")
# Then proceed with landmark processing...
```

## Fields NEVER permitted in any storage

These fields must NEVER appear in MongoDB, Redis, or Kafka messages:

```python
FORBIDDEN_FIELDS = [
    "video",           # C-01: no video bytes
    "image_bytes",     # C-01: no image bytes
    "frame_data",      # C-01: no frame data
    "base64",          # C-01: no base64 encoded images
    "cedula",          # National ID — requires extra consent
    "id_number",
    "exact_location",  # GPS coordinates
    "raw_audio",
    # full_name is OK if user consented to personal_data
]
```

## Mobile Consent UI Requirements

### Screen 1 — Onboarding (before registration)
- Title: "Política de tratamiento de datos personales"
- Body: Summary of data use + link to full policy
- CTA: "Acepto" (required to continue) | "Rechazar" (exits app)
- On accept: call `POST /consent/` with `{consent_type: "personal_data", granted: true}`

### Screen 2 — Camera activation modal
- Title: "Análisis biométrico de técnica"
- Body: "Usaremos tu cámara para analizar tu postura. Solo se procesan coordenadas de articulaciones, nunca se almacenan imágenes."
- CTA: "Permitir análisis" | "Ahora no"
- On accept: call `POST /consent/` with `{consent_type: "biometric_data", granted: true}`

### Screen 3 — Wearable pairing modal
- Title: "Datos de salud del smartwatch"
- Body: "Tus datos de ritmo cardíaco serán usados para correlacionar con tu desempeño."
- CTA: "Vincular reloj" | "Omitir"
- On accept: call `POST /consent/` with `{consent_type: "health_data", granted: true}`

### Settings screen — Revoke at any time
- User can toggle off any consent
- On toggle off: call `POST /consent/` with `{consent_type: X, granted: false}`
- Effect: backend must stop processing that type of data immediately

## Consent in Pydantic Schemas

```python
# Request (schema.py)
class ConsentCreate(BaseModel):
    consent_type: Literal["personal_data", "biometric_data", "health_data", "data_sharing"]
    granted: bool

# Response
class ConsentResponse(BaseModel):
    user_id: str
    consent_type: str
    granted: bool
    granted_at: Optional[datetime]
    policy_version: str
```

## Data Retention & User Rights (Ley 1581 Art. 8)

Users have the right to:
- **Access**: GET /consent/{user_id} shows what data is collected
- **Rectification**: Update personal data
- **Erasure**: DELETE account removes all data (implement before production)
- **Portability**: Export session data as JSON/CSV

Implement a `DELETE /user/{user_id}` that cascades: User, BoxingSession, Consent, all Redis keys for that user.

## Policy Version
Always include `policy_version: "v1.0"` in consent records. When the privacy policy changes, bump to `"v1.1"`, `"v2.0"`, etc., and require re-consent from existing users.
