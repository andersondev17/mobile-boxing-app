import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import RealtimeCounter from './pages/RealtimeCounter'
import VideoUpload from './pages/VideoUpload'
import './App.css'

/**
 * Componente principal de la aplicación
 * Maneja el routing entre las diferentes páginas
 */
function App() {
  return (
    <Router>
      <Routes>
        {/* Página principal */}
        <Route path="/" element={<Home />} />
        
        {/* Contador en tiempo real con cámara */}
        <Route path="/realtime" element={<RealtimeCounter />} />
        
        {/* Subir y procesar videos */}
        <Route path="/upload" element={<VideoUpload />} />
      </Routes>
    </Router>
  )
}

export default App


