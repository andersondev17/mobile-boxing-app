# Design Review: Sistema de Evaluación de Técnica de Boxeo

**Fecha:** 2026-04-22  
**Revisión del código:** `apps/backend/app/build_baseline/` y `apps/backend/app/ml_service/`  
**Autor:** Análisis de arquitectura de software e IA  

---

## 1. Procesamiento de Videos de Baseline — Múltiples Golpes por Video

### Problema Detectado

El pipeline `build_pipeline.py` tiene una limitación crítica en la línea 78:

```python
window = df.head(30)
```

Este código descarta todos los frames posteriores a los primeros 30. Si un video contiene 5 jabs distribuidos en 150 frames:
- Solo se procesa el inicio del video (probablemente guardia o primer jab incompleto)
- Se pierden los jabs 2-5 por completo
- El baseline generado no representa la técnica real

### Impacto
- Baselines sesgados hacia la guardia inicial
- Pérdida de variabilidad de la técnica
- Comparación DTW imprecisa contra usuarios

### Recomendación

**Opción A (Recomendada para MVP):** Grabar videos siguiendo estándar estricto:
- 1 técnica por video
- 3-5 segundos de duración
- 1 ejecución limpia del golpe + retorno a guardia
- Mínimo 30 frames útiles a 30fps

**Opción B (Futuro):** Implementar segmentación automática:
```python
# Pseudocódigo para segmentación por velocidad
def detect_punch_segments(df, speed_threshold=0.8):
    """Detecta múltiples golpes en un video por picos de velocidad."""
    speeds = df['hand_speed'].values
    peaks = find_peaks(speeds, height=speed_threshold, distance=20)
    segments = []
    for peak in peaks:
        start = max(0, peak - 10)
        end = min(len(df), peak + 20)
        segments.append(df.iloc[start:end])
    return segments
```

---

## 2. Variabilidad en Captura — Ángulo, Velocidad y Distancia

### Estado Actual por Factor

| Factor | Estado | Análisis |
|----------|--------|----------|
| **Distancia cámara-boxeador** | ✅ Neutral | MediaPipe normaliza landmarks a coordenadas [0,1], independiente de la distancia física |
| **Ángulo de cámara** | ⚠️ **Problema crítico** | Features como `forward_extent` y `torso_rotation` dependen de la proyección 2D. Un video lateral produce landmarks radicalmente distintos a uno frontal |
| **Velocidad de ejecución** | ⚠️ **Problema moderado** | El baseline usa `WINDOW_SIZE=30` fijo. Un jab lento en 60 frames al resamplearlo a 30 distorsiona las aceleraciones. El augment con `np.random.randint(28, 32)` simula variación artificial, no la real |

### Estándar de Captura Recomendado

```yaml
Cámara:
  posición: frontal, perpendicular al boxeador
  altura: nivel del pecho/cabeza (1.5-1.7m)
  distancia: 2.5-3.5 metros (cuerpo completo visible)
  
Video:
  resolución: mínimo 720p
  fps: exactamente 30fps (no variable)
  iluminación: uniforme, evitar sombras duras
  fondo: limpio, contraste con el boxeador
  
Boxeador:
  vestimenta: ropa ajustada (mejor visibilidad de articulaciones)
  posición_inicial: guardia ortodoxa estándar
  ejecución: 1 golpe técnico, retorno completo a guardia
```

### Consecuencias sin estándar

Sin estas especificaciones, los scores DTW fluctuarán por:
- Cambios de perspectiva (ángulo)
- Velocidad de captura inconsistente
- Oclusión parcial del cuerpo

El sistema interpretará estos como errores de técnica, generando feedback incorrecto.

---

## 3. Cobertura del Dataset de Baselines

### Estado Actual

El pipeline espera un único archivo `{punch}_raw.parquet` por tipo de golpe (`build_pipeline.py:141`). Esto implica que múltiples videos del mismo tipo deben fusionarse antes del procesamiento.

### Recomendación

**Meta de cobertura:** 5-10 videos limpios por técnica (jab, cross, hook, uppercut) = 20-40 videos totales.

**Beneficios:**
- Mayor robustez ante variabilidad corporal (alturas, alcances)
- Cobertura de estilos técnicos válidos (jab corto vs largo)
- Scores DTW más estables y reproducibles
- Menor varianza en el feedback

**Estrategia de integración:**
```python
# build_pipeline.py - Modificación sugerida
def merge_video_features(video_paths: list[Path]) -> pd.DataFrame:
    """Concatena features de múltiples videos del mismo tipo de golpe."""
    dfs = []
    for path in video_paths:
        df = extract_features_from_video(path)
        df['source_video'] = path.name
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)
```

---

## 4. Análisis de Features — Cobertura Biomecánica

### Features Actuales (8)

| Feature | Métrica | Adecuación |
|---------|---------|------------|
| `elbow_angle_left/right` | Ángulo del codo | ✅ Básico pero funcional |
| `forward_extent_left/right` | Alcance horizontal de muñeca | ✅ Buen proxy de extensión |
| `torso_rotation` | Rotación hombros vs caderas (Z) | ✅ Crítico para potencia |
| `vertical_displacement` | Desplazamiento vertical de cabeza | ⚠️ Limitado; no distingue drop de bounce |
| `knee_flexion` | Flexión de rodilla | ⚠️ Solo pierna izquierda; incompleto |
| `weight_transfer` | Offset horizontal de cadera | ✅ Buena métrica de transferencia |
| `hand_speed` (augmentado) | Velocidad de muñeca | ✅ Derivado temporal |
| `retraction_speed` (augmentado) | Velocidad de retorno | ✅ Crítico para guardia |

### Gaps Críticos Detectados

1. **Altura de guardia:** No se mide si las manos están protegiendo la barbilla
2. **Estabilidad de cabeza:** Desviación estándar de la posición de la nariz durante el golpe
3. **Balance:** Simetría entre hombros y caderas (inclinación lateral)
4. **Extensión de pierna trasera:** En cross, la extensión de la pierna impulsa la rotación
5. **Trayectoria de muñeca:** Actualmente solo se mide el alcance final, no el path

### Features Recomendados para V2

```python
additional_features = {
    "guard_height": "distancia vertical muñeca-nariz (guardia baja si > 0.3)",
    "head_stability": "std de posición Y de la nariz durante la ventana",
    "shoulder_tilt": "diferencia de altura entre hombros (indica balance)",
    "rear_leg_extension": "ángulo de la rodilla derecha en cross",
    "wrist_trajectory_arc": "curvatura del path de muñeca (jab debería ser casi lineal)"
}
```

---

## 5. Arquitectura ML: DTW vs Deep Learning

### Evaluación del Enfoque Actual

**Arquitectura:** Random Forest (clasificación) + DTW (validación temporal) + Reglas heurísticas (feedback)

### Comparativa de Enfoques

| Aspecto | DTW + Reglas (Actual) | Deep Learning Alternativo |
|---------|----------------------|---------------------------|
| **Datos requeridos** | 10-50 ejemplos etiquetados | 1,000-10,000 videos con scores técnicos |
| **Tiempo de entrenamiento** | Minutos | Horas-días (GPU) |
| **Latencia inferencia** | <50ms en CPU | 100-500ms (depende de modelo) |
| **Interpretabilidad** | ✅ Alta (sabes qué feature falló) | ❌ Baja (caja negra) |
| **Deployment** | CPU local, ligero | GPU o nube, más costoso |
| **Mantenimiento** | Bajo (ajustar thresholds) | Alto (reentrenar con datos nuevos) |
| **Precisión técnica** | Moderada (captura errores obvios) | Potencialmente superior (captura sutilezas) |

### Veredicto

**El enfoque actual es arquitectónicamente correcto para el stage del proyecto.**

Razones:
1. **Restricción de datos:** No hay corpus de miles de videos de boxeo con ground-truth de técnica
2. **Costo-beneficio:** El 80% del valor se obtiene con el 20% del esfuerzo (DTW)
3. **Debugging:** Es trivial ajustar un threshold de `torso_rotation` vs reentrenar una red
4. **UX:** Latencia baja permite feedback real-time sin lag perceptible

### Cuándo considerar Deep Learning

Solo si se cumplen TODAS estas condiciones:
- Dataset de 1000+ videos con anotaciones de técnica (score 0-100, no solo tipo)
- Recursos de infraestructura (GPU) para entrenamiento e inferencia
- Equipo con expertise en CV/ML (no solo backend generalista)
- Métricas claras de mejora sobre el baseline DTW

### Sobre Databricks Community Edition

**Recomendación:** Overkill actual. Databricks brilla para:
- Datasets masivos (TB)
- Feature engineering distribuido
- Hyperparameter tuning a gran escala

Tu pipeline actual procesa videos de 5 segundos en <100ms en CPU local. No hay problema de escala que justifique la complejidad adicional.

---

## 6. UX: Detección Automática vs Selección Manual

### Enfoque Actual

El usuario enciende la cámara, el sistema detecta el tipo de golpe mediante RF+DTW y compara contra el baseline correspondiente.

### Trade-off Analysis

| Modo | User Experience | Precisión Técnica | Casos de Error |
|------|-----------------|-------------------|----------------|
| **Auto-detección** | ✅ Sin fricción, flujo natural | ⚠️ 85-90% accuracy | Jab/cross similares se confunden; usuario puede hacer shadow boxing sin golpe y el sistema "adivina" |
| **Selección manual** | ⚠️ Friction extra, decisión forzada | ✅ 100% selección baseline | Usuario puede elegir mal (decir "cross" y hacer "hook") |

### Comportamiento observado en el código

`hybrid_classifier.py:239-308` implementa el flujo auto-detect:
1. RF predice top-2 tipos de golpe
2. DTW compara contra baselines de esos tipos
3. Score combinado (0.6*RF + 0.4*DTW)
4. Threshold mínimo de 0.60

El sistema maneja `unknown` cuando la confianza es baja, pero no solicita confirmación al usuario.

### Recomendación Híbrida

**Para MVP actual:** Mantener auto-detección.

**Mejora sugerida (bajo costo, alto impacto):** Añadir confirmación visual:

```
┌─────────────────────────────────────┐
│  🎯 Detectamos: JAB                  │
│                                     │
│  [✅ Correcto]  [❌ Es Cross]       │
│                                     │
│  O elige otro: [Hook] [Uppercut]    │
└─────────────────────────────────────┘
```

Implementación: Añadir endpoint `/boxing/confirm-punch-type` que re-ejecute el análisis contra el baseline seleccionado.

**Escenario futuro:** Si se implementa "combo training" (jab-cross-hook), la selección manual puede ser más predecible que la auto-detección secuencial.

---

## 7. Observaciones de Código Específicas

### `dtw_scorer.py` — Inconsistencia de Feature Order

Hay dos constantes que difieren:

```python
# Línea 27-36
FEATURE_ORDER = [
    "elbow_angle_left", "elbow_angle_right",
    "forward_extent_left", "forward_extent_right",
    "shoulder_rotation", "hip_rotation",  # ❌ No existen en extractor
    "guard_distance",                      # ❌ No existe
    "wrist_lateral_displacement",          # ❌ No existe
]

# Línea 38-47
DTW_FEATURE_ORDER = [
    "elbow_angle_left", "forward_extent_left",
    "torso_rotation", "vertical_displacement",
    "knee_flexion", "weight_transfer",
    "hand_speed", "retraction_speed",
]
```

**Problema:** `FEATURE_ORDER` hace referencia a features que no existen en `feature_extractor.py`. Esto puede causar errores si algún módulo lo importa.

**Acción:** Eliminar `FEATURE_ORDER` y usar exclusivamente `DTW_FEATURE_ORDER`.

### `hybrid_classifier.py` — Feature Mismatch

Líneas 189-191:
```python
key_features = [
    'elbow_angle_right', 'forward_extent_right', 
    'hand_speed', 'torso_rotation'
]
```

Estos features son correctos para diestro (right-handed), pero el baseline debe tener la estructura correspondiente. Verificar que los baselines de jab/cross para diestros usen `*_right` features.

### `feedback_engine.py` — Hardcoded Thresholds

Líneas 62-88:
```python
if features.get('forward_extent_left', 0) < 0.4:
    messages.append(coaching_set['arm_extension'])
```

**Problema:** Thresholds como `0.4` y `8.0` no están normalizados por antropometría. Un boxeador con brazos cortos nunca alcanzará `0.4`, recibiendo feedback incorrecto persistente.

**Recomendación:** Normalizar thresholds relativos al baseline de la técnica:
```python
baseline_extent = self.baseline_stats["mean"]["forward_extent_left"]
if user_extent < baseline_extent * 0.7:  # 30% por debajo del baseline
    messages.append("Extensión insuficiente vs referencia profesional")
```

---

## 8. Roadmap de Mejoras Priorizadas

### Inmediato (Sprint actual)

1. [ ] **Documentar y comunicar estándar de captura** (sección 2 de este doc)
2. [ ] **Re-grabar videos de baseline** siguiendo estándar: 1 golpe/video, cámara frontal, 30fps
3. [ ] **Corregir `FEATURE_ORDER`** en `dtw_scorer.py` — eliminar referencias a features inexistentes

### Corto plazo (1-2 sprints)

4. [ ] **Añadir 4-5 videos adicionales por técnica** para robustez
5. [ ] **Implementar confirmación visual** de tipo de golpe detectado
6. [ ] **Normalizar thresholds de feedback** contra baseline, no valores absolutos

### Mediano plazo (3-6 meses)

7. [ ] **Añadir features V2:** guard_height, head_stability, shoulder_tilt
8. [ ] **Segmentación automática** de múltiples golpes por video (Opción B, sección 1)
9. [ ] **Evaluación A/B:** DTW actual vs modelo de regresión simple (RandomForestRegressor) entrenado con scores DTW como target

### Largo plazo (6+ meses, condicional)

10. [ ] **Dataset collection:** Recolectar 500+ videos de usuarios con feedback humano de técnica
11. [ ] **Evaluación de DL:** Entrenar modelo de secuencias (LSTM/Transformer) si los datos lo justifican
12. [ ] **Integración con Databricks:** Solo si la escala lo requiere (miles de usuarios concurrentes)

---

## 9. Métricas de Éxito Recomendadas

Para validar mejoras, trackear:

| Métrica | Definición | Target |
|---------|------------|--------|
| **DTW Score Consistency** | Coeficiente de variación (CV) de scores para el mismo boxeador repitiendo la técnica | CV < 15% |
| **User Feedback Accuracy** | % de usuarios que califican el feedback como "útil" en la app | > 75% |
| **Detection Precision** | % de veces que el usuario corrige la detección auto | < 10% corrections |
| **False Positive Rate** | % de videos sin golpe técnico que reciben score > 50 | < 5% |

---

## Conclusión

El sistema actual es **arquitectónicamente sólido para su etapa de desarrollo**. El enfoque DTW+RF proporciona un balance óptimo entre precisión, latencia, costo de implementación y mantenibilidad.

Las principales oportunidades de mejora no están en cambiar la arquitectura ML, sino en:
1. **Calidad de datos:** Estandarizar captura y aumentar cobertura de baselines
2. **UX refinada:** Confirmación de detección para aumentar confianza del usuario
3. **Robustez:** Normalización de thresholds y mejora de cobertura de features

La transición a Deep Learning no está justificada hasta contar con un dataset de al menos 1000 videos etiquetados con scores de técnica detallados, y métricas claras de que el enfoque actual es insuficiente.
