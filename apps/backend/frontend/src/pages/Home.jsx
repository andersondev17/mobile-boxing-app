import { Link } from 'react-router-dom'
import './Home.css'

/**
 * Página principal con opciones de navegación
 */
const Home = () => {
  return (
    <div className="home">
      <div className="home-container">
        <div className="home-header">
          <h1>💪 Contador de Dominadas</h1>
          <p className="subtitle">
            Analiza tus dominadas con inteligencia artificial
          </p>
        </div>

        <div className="options-grid">
          {/* Opción 1: Tiempo Real */}
          <Link to="/realtime" className="option-card">
            <div className="card-icon">📹</div>
            <h2>Tiempo Real</h2>
            <p>
              Usa tu cámara web para contar dominadas en vivo mientras entrenas
            </p>
            <div className="card-features">
              <span className="feature">✓ Feedback instantáneo</span>
              <span className="feature">✓ Detección de postura</span>
              <span className="feature">✓ Contador en vivo</span>
            </div>
            <button className="card-button">
              Iniciar Sesión en Vivo →
            </button>
          </Link>

          {/* Opción 2: Subir Video */}
          <Link to="/upload" className="option-card">
            <div className="card-icon">🎬</div>
            <h2>Subir Video</h2>
            <p>
              Analiza videos grabados de tus entrenamientos anteriores
            </p>
            <div className="card-features">
              <span className="feature">✓ Soporta MP4, AVI, MOV</span>
              <span className="feature">✓ Análisis completo</span>
              <span className="feature">✓ Descarga resultado</span>
            </div>
            <button className="card-button">
              Procesar Video →
            </button>
          </Link>
        </div>

        <div className="home-footer">
          <div className="info-section">
            <h3>🎯 ¿Cómo funciona?</h3>
            <div className="steps">
              <div className="step">
                <span className="step-number">1</span>
                <p>Elige entre tiempo real o subir video</p>
              </div>
              <div className="step">
                <span className="step-number">2</span>
                <p>MediaPipe detecta tu postura y movimientos</p>
              </div>
              <div className="step">
                <span className="step-number">3</span>
                <p>Obtén el conteo automático de repeticiones</p>
              </div>
            </div>
          </div>

          <div className="tech-stack">
            <p className="tech-title">Powered by:</p>
            <div className="tech-badges">
              <span className="badge">MediaPipe</span>
              <span className="badge">FastAPI</span>
              <span className="badge">React</span>
              <span className="badge">OpenCV</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Home