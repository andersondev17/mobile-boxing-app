/**
 * Componente que contiene todos los botones de control
 */
const ControlButtons = ({
  isCameraActive,
  isConnected,
  onStartCamera,
  onConnect,
  onReset,
  onStop
}) => {
  return (
    <div className="controls">
      <button 
        className="btn-primary" 
        onClick={onStartCamera}
        disabled={isCameraActive}
      >
        Iniciar Cámara
      </button>
      
      <button 
        className="btn-secondary" 
        onClick={onConnect}
        disabled={!isCameraActive || isConnected}
      >
        Conectar al Servidor
      </button>
      
      <button 
        className="btn-danger" 
        onClick={onReset}
        disabled={!isConnected}
      >
        Reiniciar Contador
      </button>
      
      <button 
        className="btn-danger" 
        onClick={onStop}
        disabled={!isCameraActive}
      >
        Detener
      </button>
    </div>
  )
}

export default ControlButtons