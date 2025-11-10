import { API_CONFIG } from '../config/constants'

/**
 * Servicio para interactuar con la API del backend
 */
class ApiService {
  /**
   * Reinicia el contador de dominadas
   */
  async resetCounter() {
    try {
      const response = await fetch(
        `${API_CONFIG.API_BASE_URL}${API_CONFIG.RESET_COUNTER}`
      )
      return await response.json()
    } catch (error) {
      console.error('Error al reiniciar contador:', error)
      throw error
    }
  }

  /**
   * Obtiene estadísticas del servidor
   */
  async getStats() {
    try {
      const response = await fetch(
        `${API_CONFIG.API_BASE_URL}${API_CONFIG.STATS}`
      )
      return await response.json()
    } catch (error) {
      console.error('Error al obtener estadísticas:', error)
      throw error
    }
  }

  /**
   * Procesa un video
   */
  async processVideo(file) {
    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch(
        `${API_CONFIG.API_BASE_URL}${API_CONFIG.PROCESS_VIDEO}`,
        {
          method: 'POST',
          body: formData,
        }
      )

      if (!response.ok) {
        throw new Error('Error procesando video')
      }

      return response
    } catch (error) {
      console.error('Error al procesar video:', error)
      throw error
    }
  }

  /**
   * Verifica la salud del servidor
   */
  async checkHealth() {
    try {
      const response = await fetch(`${API_CONFIG.API_BASE_URL}/`)
      return await response.json()
    } catch (error) {
      console.error('Error al verificar salud del servidor:', error)
      return { status: 'error' }
    }
  }
}

export default new ApiService()