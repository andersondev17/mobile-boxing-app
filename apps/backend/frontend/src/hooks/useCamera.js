import { useState, useRef, useEffect } from 'react'
import { VIDEO_CONFIG } from '../config/constants'

/**
 * Hook personalizado para manejar la cámara
 */
export const useCamera = () => {
  const videoRef = useRef(null)
  const [isCameraActive, setIsCameraActive] = useState(false)
  const [error, setError] = useState(null)
  const streamRef = useRef(null)

  /**
   * Inicia la cámara
   */
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: VIDEO_CONFIG.width,
          height: VIDEO_CONFIG.height
        }
      })

      if (videoRef.current) {
        videoRef.current.srcObject = stream
        streamRef.current = stream
        setIsCameraActive(true)
        setError(null)
      }
    } catch (err) {
      console.error('Error al acceder a la cámara:', err)
      setError(err.message)
      alert('Error al acceder a la cámara: ' + err.message)
    }
  }

  /**
   * Detiene la cámara
   */
  const stopCamera = () => {
    if (streamRef.current) {
      const tracks = streamRef.current.getTracks()
      tracks.forEach(track => track.stop())
      streamRef.current = null
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null
    }

    setIsCameraActive(false)
  }

  /**
   * Limpieza al desmontar el componente
   */
  useEffect(() => {
    return () => {
      stopCamera()
    }
  }, [])

  return {
    videoRef,
    isCameraActive,
    error,
    startCamera,
    stopCamera
  }
}