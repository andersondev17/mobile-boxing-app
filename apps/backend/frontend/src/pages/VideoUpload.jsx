import { useState, useRef } from 'react'
import { Link } from 'react-router-dom'
import apiService from '../services/api'
import './VideoUpload.css'

/**
 * Página para subir y procesar videos
 */
const VideoUpload = () => {
  const [selectedFile, setSelectedFile] = useState(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [resultUrl, setResultUrl] = useState(null)
  const [error, setError] = useState(null)
  const [totalPullups, setTotalPullups] = useState(null)
  const fileInputRef = useRef(null)

  /**
   * Maneja la selección de archivo
   */
  const handleFileSelect = (event) => {
    const file = event.target.files[0]
    
    if (!file) return

    // Validar tipo de archivo
    const validTypes = ['video/mp4', 'video/avi', 'video/mov', 'video/quicktime', 'video/x-matroska']
    if (!validTypes.includes(file.type)) {
      setError('Formato no soportado. Use MP4, AVI, MOV o MKV')
      return
    }

    // Validar tamaño (máximo 100MB)
    const maxSize = 100 * 1024 * 1024 // 100MB
    if (file.size > maxSize) {
      setError('El archivo es demasiado grande. Máximo 100MB')
      return
    }

    setSelectedFile(file)
    setError(null)
    setResultUrl(null)
    setTotalPullups(null)
  }

  /**
   * Maneja el procesamiento del video
   */
  const handleProcess = async () => {
    if (!selectedFile) {
      setError('Por favor selecciona un video primero')
      return
    }

    setIsProcessing(true)
    setProgress(0)
    setError(null)
    setResultUrl(null)
    setTotalPullups(null)

    // Simular progreso
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 90) {
          clearInterval(progressInterval)
          return 90
        }
        return prev + 10
      })
    }, 500)

    try {
      console.log('📤 Enviando video al servidor...')
      const response = await apiService.processVideo(selectedFile)
      
      console.log('📥 Respuesta recibida:', response)
      console.log('📊 Status:', response.status)
      console.log('📋 Headers:', response.headers)

      // Verificar si la respuesta es exitosa
      if (!response.ok) {
        throw new Error(`Error del servidor: ${response.status}`)
      }

      // Obtener el total de dominadas del header (si existe)
      const pullups = response.headers.get('X-Total-Pullups')
      if (pullups) {
        setTotalPullups(parseInt(pullups))
        console.log(`✅ Total dominadas: ${pullups}`)
      }
      
      // Crear blob del video
      console.log('🎬 Creando blob del video...')
      const blob = await response.blob()
      console.log('📦 Blob creado:', blob.size, 'bytes, tipo:', blob.type)
      
      // Crear URL del blob
      const url = window.URL.createObjectURL(blob)
      console.log('🔗 URL creada:', url)
      
      setResultUrl(url)
      setProgress(100)
      clearInterval(progressInterval)
      console.log('✅ Video procesado y listo para mostrar')
      
    } catch (err) {
      console.error('❌ Error procesando video:', err)
      setError('Error al procesar el video: ' + err.message)
      clearInterval(progressInterval)
    } finally {
      setIsProcessing(false)
    }
  }

  /**
   * Maneja la descarga del video procesado
   */
  const handleDownload = () => {
    if (!resultUrl) return

    const link = document.createElement('a')
    link.href = resultUrl
    link.download = `procesado_${selectedFile.name}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  /**
   * Reinicia el formulario
   */
  const handleReset = () => {
    // Liberar URL del blob anterior
    if (resultUrl) {
      window.URL.revokeObjectURL(resultUrl)
    }
    
    setSelectedFile(null)
    setResultUrl(null)
    setError(null)
    setProgress(0)
    setTotalPullups(null)
    
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="app">
      <div className="container upload-container">
        <div className="page-header">
          <Link to="/" className="back-button">
            ← Volver al inicio
          </Link>
          <h1>🎬 Procesar Video</h1>
        </div>

        <div className="upload-section">
          {/* Área de selección de archivo */}
          <div className="file-select-area">
            <input
              ref={fileInputRef}
              type="file"
              accept="video/mp4,video/avi,video/mov,video/quicktime,video/x-matroska"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
              id="fileInput"
            />
            
            <label htmlFor="fileInput" className="file-select-label">
              <div className="upload-icon">📁</div>
              <p className="upload-text">
                {selectedFile ? selectedFile.name : 'Haz clic para seleccionar un video'}
              </p>
              <p className="upload-subtext">
                MP4, AVI, MOV o MKV (máx. 100MB)
              </p>
            </label>
          </div>

          {/* Información del archivo seleccionado */}
          {selectedFile && (
            <div className="file-info">
              <h3>📋 Información del archivo</h3>
              <div className="info-grid">
                <div className="info-item">
                  <span className="info-label">Nombre:</span>
                  <span className="info-value">{selectedFile.name}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Tamaño:</span>
                  <span className="info-value">
                    {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                  </span>
                </div>
                <div className="info-item">
                  <span className="info-label">Tipo:</span>
                  <span className="info-value">{selectedFile.type}</span>
                </div>
              </div>
            </div>
          )}

          {/* Barra de progreso */}
          {isProcessing && (
            <div className="progress-section">
              <p className="progress-text">Procesando video... {progress}%</p>
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="progress-subtext">
                Esto puede tomar algunos minutos dependiendo del tamaño del video
              </p>
            </div>
          )}

          {/* Mensaje de error */}
          {error && (
            <div className="error-message">
              ⚠️ {error}
            </div>
          )}

          {/* Resultado */}
          {resultUrl && (
            <div className="result-section">
              <h3>✅ ¡Video procesado exitosamente!</h3>
              {totalPullups !== null && (
                <div className="pullups-badge">
                  <span className="badge-icon">💪</span>
                  <span className="badge-text">
                    {totalPullups} {totalPullups === 1 ? 'dominada' : 'dominadas'} detectadas
                  </span>
                </div>
              )}
              <video 
                src={resultUrl} 
                controls 
                className="result-video"
                preload="metadata"
                onError={(e) => {
                  console.error('❌ Error cargando video:', e)
                  setError('Error al cargar el video procesado')
                }}
                onLoadedData={() => {
                  console.log('✅ Video cargado correctamente en el elemento <video>')
                }}
              />
              <p className="video-info">
                🎥 El video procesado está listo. Puedes reproducirlo o descargarlo.
              </p>
            </div>
          )}

          {/* Botones de control */}
          <div className="upload-controls">
            {!resultUrl ? (
              <>
                <button
                  className="btn-primary btn-large"
                  onClick={handleProcess}
                  disabled={!selectedFile || isProcessing}
                >
                  {isProcessing ? '⏳ Procesando...' : '🚀 Procesar Video'}
                </button>
                {selectedFile && (
                  <button
                    className="btn-secondary btn-large"
                    onClick={handleReset}
                    disabled={isProcessing}
                  >
                    🗑️ Limpiar
                  </button>
                )}
              </>
            ) : (
              <>
                <button
                  className="btn-primary btn-large"
                  onClick={handleDownload}
                >
                  ⬇️ Descargar Video
                </button>
                <button
                  className="btn-secondary btn-large"
                  onClick={handleReset}
                >
                  ➕ Procesar Otro Video
                </button>
              </>
            )}
          </div>
        </div>

        {/* Instrucciones */}
        <div className="instructions">
          <h3>💡 Instrucciones</h3>
          <ol>
            <li>Selecciona un video donde estés haciendo dominadas</li>
            <li>Asegúrate de que todo tu cuerpo sea visible en el video</li>
            <li>Haz clic en "Procesar Video" y espera</li>
            <li>Descarga el video con el contador y análisis incluido</li>
          </ol>
        </div>
      </div>
    </div>
  )
}

export default VideoUpload
