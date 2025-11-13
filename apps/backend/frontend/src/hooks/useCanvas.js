import { useRef, useEffect } from 'react'
import { CANVAS_CONFIG } from '../config/constants'

/**
 * Hook personalizado para manejar el canvas y dibujar landmarks
 */
export const useCanvas = (videoRef) => {
  const canvasRef = useRef(null)

  /**
   * Configura el canvas cuando el video está listo
   */
  useEffect(() => {
    const video = videoRef.current
    const canvas = canvasRef.current

    if (video && canvas) {
      const handleLoadedMetadata = () => {
        canvas.width = video.videoWidth
        canvas.height = video.videoHeight
      }

      video.addEventListener('loadedmetadata', handleLoadedMetadata)

      return () => {
        video.removeEventListener('loadedmetadata', handleLoadedMetadata)
      }
    }
  }, [videoRef])

  /**
   * Dibuja un punto en el canvas
   */
  const drawPoint = (ctx, point, color) => {
    ctx.fillStyle = color
    ctx.beginPath()
    ctx.arc(point[0], point[1], CANVAS_CONFIG.pointRadius, 0, 2 * Math.PI)
    ctx.fill()
  }

  /**
   * Dibuja los landmarks en el canvas
   */
  const drawLandmarks = (landmarks) => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const {
      right_shoulder,
      right_elbow,
      right_wrist,
      left_shoulder,
      left_elbow,
      left_wrist,
      angle_r,
      angle_l
    } = landmarks

    // Configurar estilo de líneas
    ctx.strokeStyle = CANVAS_CONFIG.colors.line
    ctx.lineWidth = CANVAS_CONFIG.lineWidth

    // Dibujar brazo derecho
    ctx.beginPath()
    ctx.moveTo(right_shoulder[0], right_shoulder[1])
    ctx.lineTo(right_elbow[0], right_elbow[1])
    ctx.lineTo(right_wrist[0], right_wrist[1])
    ctx.stroke()

    // Dibujar brazo izquierdo
    ctx.beginPath()
    ctx.moveTo(left_shoulder[0], left_shoulder[1])
    ctx.lineTo(left_elbow[0], left_elbow[1])
    ctx.lineTo(left_wrist[0], left_wrist[1])
    ctx.stroke()

    // Dibujar puntos
    drawPoint(ctx, right_shoulder, CANVAS_CONFIG.colors.shoulder)
    drawPoint(ctx, right_elbow, CANVAS_CONFIG.colors.elbow)
    drawPoint(ctx, right_wrist, CANVAS_CONFIG.colors.wrist)
    drawPoint(ctx, left_shoulder, CANVAS_CONFIG.colors.shoulder)
    drawPoint(ctx, left_elbow, CANVAS_CONFIG.colors.elbow)
    drawPoint(ctx, left_wrist, CANVAS_CONFIG.colors.wrist)

    // Dibujar ángulos
    ctx.fillStyle = CANVAS_CONFIG.colors.text
    ctx.font = `bold ${CANVAS_CONFIG.fontSize} ${CANVAS_CONFIG.fontFamily}`
    ctx.fillText(
      `${Math.round(angle_r)}°`,
      right_elbow[0] + 20,
      right_elbow[1] - 20
    )
    ctx.fillText(
      `${Math.round(angle_l)}°`,
      left_elbow[0] + 20,
      left_elbow[1] - 20
    )
  }

  /**
   * Limpia el canvas
   */
  const clearCanvas = () => {
    const canvas = canvasRef.current
    if (canvas) {
      const ctx = canvas.getContext('2d')
      ctx.clearRect(0, 0, canvas.width, canvas.height)
    }
  }

  return {
    canvasRef,
    drawLandmarks,
    clearCanvas
  }
}