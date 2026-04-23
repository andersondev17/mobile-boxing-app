# Estándar de Captura de Videos para Baselines

**Objetivo:** Garantizar consistencia y calidad en los videos de baseline para el sistema de análisis de técnica de boxeo.

---

## Configuración de Cámara

### Posición
- **Ángulo:** Frontal, perpendicular al boxeador
- **Altura:** Nivel del pecho/cabeza (1.5-1.7 metros del suelo)
- **Distancia:** 2.5-3.5 metros (cuerpo completo visible)
- **Centro:** Boxeador centrado en el frame

### Iluminación
- **Tipo:** Uniforme, evitar sombras duras
- **Dirección:** Frontal o lateral suave
- **Fondo:** Limpio, con buen contraste con el boxeador
- **Evitar:** Contraluz, reflejos, sombras que oculten articulaciones

---

## Configuración de Video

### Técnica
- **Resolución:** Mínimo 720p (preferible 1080p)
- **FPS:** Exactamente 30fps (no variable)
- **Formato:** MP4 o MOV
- **Duración:** 3-5 segundos por video

### Contenido
- **1 golpe por video:** Única ejecución limpia de la técnica
- **Secuencia completa:** Guardia inicial -> ejecución -> retorno a guardia
- **Saco de boxeo:** Visible al lado del boxeador (opcional pero recomendado)
- **Espacio:** Suficiente para movimiento completo sin salir del frame

---

## Posición del Boxeador

### Vestimenta
- **Ropa:** Ajustada (mejor visibilidad de articulaciones)
- **Colores:** Contraste con el fondo
- **Evitar:** Ropa holgada, patrones que confundan a MediaPipe

### Guardia Inicial
- **Posición:** Guardia ortodoxa estándar
- **Manos:** Protegiendo barbilla
- **Pies:** Separados a anchura de hombros
- **Peso:** Distribuido 50/50 entre piernas

---

## Ejecución por Tipo de Golpe

### Jab
- **Extensión:** Brazo izquierdo completamente extendido
- **Rotación:** Ligera rotación de cadera y hombros
- **Retorno:** Rápido retorno a guardia
- **Objetivo:** Directo al frente (saco o imaginario)

### Cross
- **Potencia:** Generada desde rotación de cadera
- **Extensión:** Brazo derecho completamente extendido
- **Peso:** Transferencia a pierna delantera
- **Seguimiento:** Acompañar el golpe completamente

### Hook
- **Distancia:** Corto alcance, cerca del cuerpo
- **Codo:** Mantenido en ~90 grados
- **Rotación:** Explosión de cadera
- **Objetivo:** Lateral (costillas o cabeza)

### Uppercut
- **Trajectory:** Vertical hacia arriba
- **Rodillas:** Ligera flexión para generar potencia
- **Distancia:** Cuerpo a cuerpo
- **Objetivo:** Mentón o torso

---

## Errores Comunes a Evitar

### Técnicos
- Múltiples golpes en un solo video
- Golpes incompletos o sin retorno a guardia
- Técnica mixta (ej: jab-cross en un video)
- Movimiento de cámara durante la ejecución

### Técnicos
- Cámara de lado o ángulo diagonal
- Boxeador muy cerca o muy lejos
- Oclusión de articulaciones clave (codos, hombros)
- Iluminación insuficiente o con sombras fuertes

---

## Checklist de Verificación

### Antes de Grabar
- [ ] Cámara en trípode o superficie estable
- [ ] Distancia correcta (cuerpo completo visible)
- [ ] Iluminación uniforme sin sombras
- [ ] Espacio libre para movimiento
- [ ] Boxeador con ropa adecuada

### Durante la Grabación
- [ ] 30fps confirmado
- [ ] Boxeador centrado en frame
- [ ] Guardia inicial correcta
- [ ] 1 sola ejecución por video
- [ ] Retorno completo a guardia

### Después de Grabar
- [ ] Revisar que no haya movimiento de cámara
- [ ] Verificar visibilidad de articulaciones clave
- [ ] Confirmar duración apropiada (3-5 segundos)
- [ ] Nombrar archivo según técnica (ej: "jab_01.mp4")

---

## Ejemplos de Nomenclatura

```
jab_01.mp4        # Primer video de jab
jab_02.mp4        # Segundo video de jab
cross_01.mp4      # Primer video de cross
hook_01.mp4       # Primer video de hook
uppercut_01.mp4   # Primer video de uppercut
```

---

## Impacto en el Sistema

Videos que siguen este estándar garantizan:
- **Consistencia** en extracción de landmarks
- **Precisión** en cálculo de features biomecánicos
- **Reproducibilidad** de scores DTW
- **Feedback** coherente y útil para usuarios

Videos que no siguen el estándar pueden causar:
- Detección incorrecta de landmarks
- Scores DTW inconsistentes
- Feedback engañoso o incorrecto
- Fallos en el pipeline de análisis

---

## Proceso de Validación

1. **Captura** siguiendo este estándar
2. **Revisión** visual del video grabado
3. **Procesamiento** con el pipeline de baselines
4. **Verificación** de que se generen features válidos
5. **Aprobación** para inclusión en dataset final

---

**Nota:** Este estándar evolucionará según los resultados del análisis y el feedback del sistema. Actualizaciones se comunicarán a medida que se identifiquen mejores prácticas.
