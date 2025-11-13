import { useState, useRef, useEffect, useCallback } from 'react'
import { API_CONFIG, VIDEO_CONFIG, CONNECTION_STATUS } from '../config/constants'

/**
 * Hook personalizado para manejar la conexión WebSocket
 */
export const useWebSocket = (videoRef, canvasRef, drawLandmarks) => {
  const wsRef = useRef(null)
  const [status, setStatus] = useState(CONNECTION_STATUS.DISCONNECTED)
  const [isProcessing, setIsProcessing] = useState(false)
  const [count, setCount] = useState(0)
  const [state, setState] = useState('Esperando')
  const processingIntervalRef = useRef(null)

  /**
   * Procesa y envía un frame al servidor
   */
  const processFrame = useCallback(() => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      return
    }

    const canvas = canvasRef.current
    const video = videoRef.current
    
    if (!canvas || !video) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Dibujar el frame actual
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)

    // Convertir a base64
    const imageData = canvas.toDataURL('image/jpeg', 0.8)
    
    // Enviar al servidor
    wsRef.current.send(imageData)
  }, [videoRef, canvasRef])

  /**
   * Conecta al WebSocket
   */
  const connect = useCallback(() => {
    setStatus(CONNECTION_STATUS.CONNECTING)

    wsRef.current = new WebSocket(API_CONFIG.WS_URL)

    wsRef.current.onopen = () => {
      console.log('✅ WebSocket conectado')
      setStatus(CONNECTION_STATUS.CONNECTED)
      setIsProcessing(true)
    }

    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data)
      setCount(data.count)
      setState(data.state)

      // Dibujar landmarks si existen
      if (data.landmarks) {
        drawLandmarks(data.landmarks)
      }
    }

    wsRef.current.onerror = (error) => {
      console.error('❌ WebSocket error:', error)
      setStatus(CONNECTION_STATUS.ERROR)
    }

    wsRef.current.onclose = () => {
      console.log('🔌 WebSocket desconectado')
      setStatus(CONNECTION_STATUS.DISCONNECTED)
      setIsProcessing(false)
    }
  }, [drawLandmarks])

  /**
   * Desconecta el WebSocket
   */
  const disconnect = useCallback(() => {
    setIsProcessing(false)

    if (processingIntervalRef.current) {
      clearInterval(processingIntervalRef.current)
      processingIntervalRef.current = null
    }

    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    setStatus(CONNECTION_STATUS.DISCONNECTED)
  }, [])

  /**
   * Inicia el procesamiento de frames
   */
  useEffect(() => {
    if (!isProcessing) {
      if (processingIntervalRef.current) {
        clearInterval(processingIntervalRef.current)
        processingIntervalRef.current = null
      }
      return
    }

    const interval = 1000 / VIDEO_CONFIG.fps
    processingIntervalRef.current = setInterval(processFrame, interval)

    return () => {
      if (processingIntervalRef.current) {
        clearInterval(processingIntervalRef.current)
      }
    }
  }, [isProcessing, processFrame])

  /**
   * Limpieza al desmontar
   */
  useEffect(() => {
    return () => {
      disconnect()
    }
  }, [disconnect])

  return {
    status,
    isProcessing,
    count,
    state,
    connect,
    disconnect
  }
}