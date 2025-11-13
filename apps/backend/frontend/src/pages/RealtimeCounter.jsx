import { useState } from 'react'
import { Link } from 'react-router-dom'
import '../App.css'

// Hooks personalizados
import { useCamera } from '../hooks/useCamera'
import { useCanvas } from '../hooks/useCanvas'
import { useWebSocket } from '../hooks/useWebSocket'

// Componentes
import StatusBanner from '../components/StatusBanner'
import VideoStream from '../components/VideoStream'
import StatsDisplay from '../components/StatsDisplay'
import ControlButtons from '../components/ControlButtons'

// Servicios
import apiService from '../services/api'

// Constantes
import { CONNECTION_STATUS, STATUS_MESSAGES } from '../config/constants'

function RealtimeCounter() {
  // Estado local para el banner de estado personalizado
  const [customStatusMessage, setCustomStatusMessage] = useState(null)

  // Hook de cámara
  const { videoRef, isCameraActive, startCamera, stopCamera } = useCamera()

  // Hook de canvas
  const { canvasRef, drawLandmarks, clearCanvas } = useCanvas(videoRef)

  // Hook de WebSocket
  const { status, count, state, connect, disconnect } = useWebSocket(
    videoRef,
    canvasRef,
    drawLandmarks
  )

  /**
   * Maneja el inicio de la cámara
   */
  const handleStartCamera = async () => {
    await startCamera()
    setCustomStatusMessage(STATUS_MESSAGES.CAMERA_ACTIVE)
  }

  /**
   * Maneja la conexión al servidor
   */
  const handleConnect = () => {
    connect()
    setCustomStatusMessage(null)
  }

  /**
   * Maneja el reinicio del contador
   */
  const handleReset = async () => {
    try {
      await apiService.resetCounter()
    } catch (error) {
      alert('Error al reiniciar: ' + error.message)
    }
  }

  /**
   * Maneja la detención completa
   */
  const handleStop = () => {
    disconnect()
    stopCamera()
    clearCanvas()
    setCustomStatusMessage(null)
  }

  return (
    <div className="app">
      <div className="container">
        <div className="page-header">
          <Link to="/" className="back-button">
            ← Volver al inicio
          </Link>
          <h1>💪 Contador en Tiempo Real</h1>
        </div>
        
        <StatusBanner 
          status={status} 
          customMessage={customStatusMessage}
        />

        <VideoStream 
          videoRef={videoRef} 
          canvasRef={canvasRef} 
        />

        <StatsDisplay 
          count={count} 
          state={state} 
        />

        <ControlButtons
          isCameraActive={isCameraActive}
          isConnected={status === CONNECTION_STATUS.CONNECTED}
          onStartCamera={handleStartCamera}
          onConnect={handleConnect}
          onReset={handleReset}
          onStop={handleStop}
        />
      </div>
    </div>
  )
}

export default RealtimeCounter