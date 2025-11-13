import { CONNECTION_STATUS, STATUS_MESSAGES } from '../config/constants'

/**
 * Componente que muestra el estado de la conexión
 */
const StatusBanner = ({ status, customMessage }) => {
  const message = customMessage || STATUS_MESSAGES[status] || STATUS_MESSAGES[CONNECTION_STATUS.DISCONNECTED]
  
  const statusClass = status === CONNECTION_STATUS.CONNECTED || customMessage
    ? 'connected'
    : 'disconnected'

  return (
    <div className={`status ${statusClass}`}>
      {message}
    </div>
  )
}

export default StatusBanner