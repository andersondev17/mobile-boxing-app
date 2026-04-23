# Plan de Implementación Completo: Backend boxing-api

**Basado en:** `EVALUATION_DESIGN_REVIEW.md` + Análisis de Integración Mobile-Backend  
**Fecha:** 2026-04-22  
**Enfoque:** Ajustar backend para alineación con mobile (NO tocar mobile)

---

## Parte I: Revisión de Arquitectura ML (Resumen)

### Estado de Features y Pipeline
| Componente | Estado | Prioridad |
|------------|--------|-----------|
| DTW + RF híbrido | ✅ Arquitectónicamente correcto | Mantener |
| Feature extraction | ⚠️ 8 features, gaps identificados | Mejorar V2 |
| Baseline generation | ⚠️ Limitado a 30 frames | Corregir |
| Feedback engine | ⚠️ Thresholds absolutos | Normalizar vs baseline |

### Correcciones Técnicas Pendientes (del review original)
1. **Eliminar `FEATURE_ORDER`** en `dtw_scorer.py` — usar solo `DTW_FEATURE_ORDER`
2. **Normalizar thresholds** en `feedback_engine.py` vs baseline, no valores fijos
3. **Documentar estándar de captura** — cámara frontal, 30fps, 1 golpe/video

---

## Parte II: Integración API Mobile-Backend

### Análisis de Mapeo de Endpoints

| Endpoint Mobile | Backend Actual | Estado | Acción Requerida |
|-----------------|----------------|--------|------------------|
| `WS /boxing/ws/jab` | `/boxing/ws/jab` | ✅ Funciona | Ninguna |
| `GET /boxing/status` | `/boxing/status` | ✅ Funciona | Ninguna |
| `POST /boxing/videos/upload` | `/boxing/videos/upload` | ⚠️ **Respuesta incompatible** | **MODIFICAR** |
| `GET /exercises/` | `/exercises/` | ✅ Funciona | Ninguna |
| `GET /exercises/{id}` | `/exercises/{id}` | ✅ Funciona | Ninguna |
| `GET /boxing/videos/pro` | **NO EXISTE** | ❌ Faltante | **CREAR** |
| `POST /boxing/videos/pro/{name}/process` | **NO EXISTE** | ❌ Faltante | **CREAR** |
| `GET /boxing/videos/stream/{session_id}` | **NO EXISTE** | ❌ Faltante | **CREAR** |
| `POST /boxing/confirm-punch-type` | **NO EXISTE** | ❌ Faltante | **CREAR** |

---

### Problema Crítico #1: Respuesta de `/boxing/videos/upload`

**Mobile espera (cvPipelineService.ts):**
```typescript
{
  video_base64: string,        // ← Video procesado en base64
  frames_analyzed: number,
  baseline_used: boolean,
  session_id: string,
  feedback_summary: string[],
  metrics_path: string,
  session_file: string,
  session_rows: number
}
```

**Backend actual devuelve:**
```python
{
  "video_url": "/boxing/videos/processed/{filename}",  // ← URL relativa
  "frames_analyzed": ...,
  # ... falta video_base64
}
```

**Implementación requerida:**

```python
# En routes/boxing.py, función upload_video() ~línea 316

import base64

# ... después de crear el video procesado ...

# Leer archivo procesado y convertir a base64
try:
    with open(processed_path, "rb") as video_file:
        video_base64 = base64.b64encode(video_file.read()).decode("utf-8")
except Exception as e:
    logger.error(f"Error leyendo video procesado: {e}")
    video_base64 = None

return {
    "video_base64": video_base64,  # ← NUEVO: datos del video
    "video_url": f"/boxing/videos/processed/{processed_filename}",  # Mantener para compatibilidad
    "frames_analyzed": result.get("scored_frames", 0),
    "baseline_used": result.get("baseline_type") != "none",
    "session_id": session_id or result.get("run_id"),
    "feedback_summary": result.get("coaching_feedback", []),
    "metrics_path": None,  # TODO: implementar si se necesita
    "session_file": processed_filename,
    "session_rows": result.get("scored_frames", 0),
    # Campos adicionales útiles
    "punch_type_detected": result.get("punch_type_detected"),
    "baseline_type": result.get("baseline_type"),
    "avg_score": result.get("avg_score"),
    "technique_level": result.get("technique_level"),
}
```

---

### Endpoint Faltante #1: Listar Videos Profesionales

```python
# Nuevo endpoint en routes/boxing.py

@router.get("/videos/pro")
async def list_pro_videos():
    """Lista videos profesionales disponibles para comparación."""
    pro_dir = boxing_service.pro_videos_dir
    videos = []
    
    if not pro_dir.exists():
        return {"videos": []}
    
    for f in pro_dir.glob("*.mp4"):
        stat = f.stat()
        videos.append({
            "name": f.stem,
            "size": stat.st_size,
            "modified": stat.st_mtime
        })
    
    return {"videos": videos}
```

---

### Endpoint Faltante #2: Procesar Video Profesional

```python
# Nuevo endpoint en routes/boxing.py

@router.post("/videos/pro/{name}/process")
async def process_pro_video(name: str):
    """Procesa video profesional y devuelve session_id para comparación."""
    from pathlib import Path
    
    video_path = boxing_service.pro_videos_dir / f"{name}.mp4"
    if not video_path.exists():
        raise HTTPException(404, detail=f"Video profesional '{name}' no encontrado")
    
    # Crear sesión única para este video pro
    session_id = f"pro_{name}_{uuid.uuid4().hex[:8]}"
    
    # Procesar (reutilizar lógica existente)
    # Nota: Esto podría requerir extraer la lógica de analyze_video a función compartida
    result = await process_video_internal(video_path, session_id=session_id)
    
    return {
        "session_id": session_id,
        "name": name,
        "frames_analyzed": result.get("scored_frames", 0),
        "baseline_type": result.get("baseline_type"),
        "feedback": result.get("feedback", [])
    }
```

---

### Endpoint Faltante #3: Stream de Video Procesado

```python
# Nuevo endpoint en routes/boxing.py
from fastapi.responses import FileResponse

@router.get("/videos/stream/{session_id}")
async def stream_processed_video(session_id: str):
    """Descarga video procesado por session_id."""
    session = await BoxingSession.find_one(BoxingSession.session_id == session_id)
    if not session:
        raise HTTPException(404, detail="Sesión no encontrada")
    
    video_path = boxing_service.output_dir / session.processed_filename
    if not video_path.exists():
        raise HTTPException(404, detail="Video procesado no encontrado")
    
    return FileResponse(
        path=video_path,
        media_type="video/mp4",
        filename=session.processed_filename
    )
```

---

### Endpoint Faltante #4: Confirmar Tipo de Golpe (Confirmación UX)

Este endpoint permite al usuario corregir la detección automática, re-analizando contra el baseline correcto.

```python
# Nuevo endpoint en routes/boxing.py

from pydantic import BaseModel

class ConfirmPunchTypeRequest(BaseModel):
    session_id: str
    confirmed_type: str  # "jab" | "cross" | "hook" | "uppercut"
    user_id: Optional[str] = None


@router.post("/confirm-punch-type")
async def confirm_punch_type(request: ConfirmPunchTypeRequest):
    """
    Re-analiza sesión contra baseline específico tras confirmación del usuario.
    
    El flujo:
    1. Usuario graba video → sistema detecta "jab" automáticamente
    2. UI muestra: "¿Detectamos JAB? [✅] [❌ Es Cross]"
    3. Si corrige → llama este endpoint con confirmed_type="cross"
    4. Sistema re-analiza landmarks guardados contra baseline de cross
    5. Devuelve nuevos scores y feedback actualizado
    """
    import pandas as pd
    from ml_service.analyzer import boxing_analyzer
    
    # 1. Recuperar sesión con landmarks/features guardados
    session = await BoxingSession.find_one(
        BoxingSession.session_id == request.session_id
    )
    if not session:
        raise HTTPException(404, detail="Sesión no encontrada")
    
    # 2. Cargar baseline del tipo confirmado
    baseline_file = Path("build_baseline/dataset") / request.confirmed_type / f"{request.confirmed_type}_v1.parquet"
    
    if not baseline_file.exists():
        raise HTTPException(
            400, 
            detail=f"Baseline para '{request.confirmed_type}' no disponible"
        )
    
    try:
        baseline_df = pd.read_parquet(baseline_file)
        boxing_analyzer.set_baseline(baseline_df)
    except Exception as exc:
        logger.exception("Error cargando baseline: %s", exc)
        raise HTTPException(500, detail="Error cargando baseline")
    
    # 3. Re-procesar si tenemos el video original guardado
    #    (alternativa: re-procesar desde landmarks si están cacheados en Redis)
    
    # TODO: Implementar re-procesamiento completo
    # Por ahora, retornar confirmación de recepción
    
    # Actualizar sesión con tipo confirmado
    session.punch_type_confirmed = request.confirmed_type
    session.user_corrected = True
    await session.save()
    
    return {
        "success": True,
        "session_id": request.session_id,
        "confirmed_type": request.confirmed_type,
        "message": f"Tipo de golpe confirmado como '{request.confirmed_type}'. Re-análisis pendiente de implementación."
    }
```

**Esquema añadir a `models/boxing.py`:**

```python
class BoxingSession(Document):
    # ... campos existentes ...
    
    punch_type_detected: Optional[str] = None  # Tipo detectado automáticamente
    punch_type_confirmed: Optional[str] = None  # Tipo confirmado por usuario
    user_corrected: bool = False  # Si el usuario corrigió la detección
```

---

## Parte III: Plan de Implementación Priorizado

### Fase 1: Mínimo Viable (MVP Mobile Funcional)

**Objetivo:** El mobile puede subir videos y recibir resultados sin errores.

| # | Tarea | Archivo | Esfuerzo Est. |
|---|-------|---------|---------------|
| 1 | Modificar respuesta `upload_video` para incluir `video_base64` | `routes/boxing.py:316` | 30 min |
| 2 | Crear endpoint `GET /boxing/videos/pro` | `routes/boxing.py` | 20 min |
| 3 | Crear endpoint `POST /boxing/videos/pro/{name}/process` | `routes/boxing.py` | 45 min |
| 4 | Crear endpoint `GET /boxing/videos/stream/{session_id}` | `routes/boxing.py` | 20 min |
| 5 | Actualizar schema `BoxingSession` con campos de confirmación | `models/boxing.py` | 15 min |

**Total Fase 1:** ~2 horas de desarrollo

### Fase 2: UX de Confirmación (Mejora de Precisión)

| # | Tarea | Archivo | Esfuerzo Est. |
|---|-------|---------|---------------|
| 6 | Implementar lógica completa de `confirm-punch-type` | `routes/boxing.py` | 2 horas |
| 7 | Cachear landmarks en Redis para re-análisis rápido | `window_buffer.py` | 1 hora |
| 8 | Guardar video original en sesión para re-procesamiento | `models/boxing.py` | 30 min |

**Total Fase 2:** ~3.5 horas de desarrollo

### Fase 3: Correcciones Técnicas del Review Original

| # | Tarea | Archivo | Esfuerzo Est. |
|---|-------|---------|---------------|
| 9 | Eliminar `FEATURE_ORDER` duplicado/inconsistente | `dtw_scorer.py:27` | 10 min |
| 10 | Normalizar thresholds de feedback vs baseline | `feedback_engine.py:62-88` | 1 hora |
| 11 | Documentar estándar de captura en README | `docs/capture_standard.md` | 30 min |

---

## Parte IV: Especificación de Esquemas Pydantic

Añadir a `schemas/boxing.py`:

```python
from typing import List, Optional
from pydantic import BaseModel


class ProVideoResponse(BaseModel):
    name: str
    size: int
    modified: float


class ProVideoListResponse(BaseModel):
    videos: List[ProVideoResponse]


class ProVideoProcessResponse(BaseModel):
    session_id: str
    name: str
    frames_analyzed: int
    baseline_type: Optional[str]
    feedback: List[str]


class ConfirmPunchTypeRequest(BaseModel):
    session_id: str
    confirmed_type: str  # jab | cross | hook | uppercut
    user_id: Optional[str] = None


class ConfirmPunchTypeResponse(BaseModel):
    success: bool
    session_id: str
    confirmed_type: str
    message: str


class VideoUploadResponse(BaseModel):
    video_base64: Optional[str]  # ← Campo crítico para mobile
    video_url: str
    frames_analyzed: int
    baseline_used: bool
    session_id: Optional[str]
    feedback_summary: List[str]
    session_file: str
    session_rows: int
    punch_type_detected: Optional[str]
    baseline_type: Optional[str]
    avg_score: Optional[float]
    technique_level: Optional[str]
```

---

## Parte V: Diagrama de Flujo de Integración

```
┌─────────────────┐     ┌─────────────────────────────────────┐
│   MOBILE APP    │     │           BACKEND API               │
├─────────────────┤     ├─────────────────────────────────────┤
│ 1. Grabar video │────▶│                                     │
│                 │     │ 2. POST /boxing/videos/upload       │
│                 │◄────│    ├─ Procesa con MediaPipe        │
│                 │     │    ├─ Extrae features               │
│                 │     │    ├─ DTW vs baseline detectado     │
│                 │     │    ├─ Crea video anotado            │
│                 │     │    └─ Convierte a base64            │
│                 │     │    Return: {video_base64, scores...}│
│                 │     │                                     │
│ 3. Mostrar      │     │                                     │
│    "Detectamos: │     │                                     │
│    JAB [✅][❌]" │     │                                     │
│                 │     │                                     │
│ 4a. Si correcto │     │                                     │
│    → Fin        │     │                                     │
│                 │     │                                     │
│ 4b. Si corregir │────▶│ 5. POST /boxing/confirm-punch-type │
│    (ej: "cross")│     │    ├─ Carga baseline de "cross"     │
│                 │     │    ├─ Re-analiza landmarks          │
│                 │◄────│    └─ Return: nuevos scores         │
│                 │     │                                     │
│ 6. Mostrar      │     │                                     │
│    comparación  │────▶│ 7. GET /boxing/videos/pro           │
│    con pro      │◄────│    Return: lista videos pro         │
│                 │     │                                     │
│ 8. Elegir video │────▶│ 9. POST /videos/pro/{name}/process │
│    pro para     │◄────│    Return: session_id del pro       │
│    comparar     │     │                                     │
│                 │────▶│ 10. GET /videos/stream/{session}   │
│                 │◄────│    Return: video file (pro)        │
└─────────────────┘     └─────────────────────────────────────┘
```

---

## Parte VI: Testing y Verificación

### Tests Manuales Requeridos

1. **Upload con base64:**
   ```bash
   curl -X POST -F "file=@test_video.mp4" \
        http://localhost:8000/boxing/videos/upload | jq '.video_base64'
   ```
   Verificar que `video_base64` existe y es string no vacío.

2. **Listar videos pro:**
   ```bash
   curl http://localhost:8000/boxing/videos/pro | jq '.videos'
   ```

3. **Confirmar tipo de golpe:**
   ```bash
   curl -X POST http://localhost:8000/boxing/confirm-punch-type \
        -H "Content-Type: application/json" \
        -d '{"session_id": "...", "confirmed_type": "cross"}'
   ```

### Tests de Integración Mobile

- [ ] Mobile puede subir video y recibir `video_base64` decodable
- [ ] Mobile puede listar videos profesionales
- [ ] Mobile puede procesar y comparar con video pro
- [ ] Mobile puede corregir tipo de golpe y recibir nuevos scores

---

## Resumen de Decisiones Arquitectónicas

| Decisión | Justificación |
|----------|---------------|
| **NO tocar mobile** | Código mobile probado, tested en dispositivos. Cambios requieren re-testing completo. |
| **Backend devuelve base64** | Mobile no tiene acceso a filesystem del servidor. URLs relativas no funcionan. |
| **Endpoints REST para videos pro** | WebSocket (`/ws/jab`) es solo para real-time. Videos requieren endpoints HTTP. |
| **`confirm-punch-type` separado** | Permite UX de corrección sin cambiar el flujo de análisis automático. |
| **Fase 1 primero** | Hace el mobile funcional rápidamente. Fase 2 mejora UX pero no es bloqueante. |

---

**Estado del documento:** Listo para implementación  
**Próximo paso:** Implementar Fase 1 (endpoints faltantes + base64)
