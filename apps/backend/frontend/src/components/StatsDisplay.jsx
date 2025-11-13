/**
 * Componente que muestra las estadísticas del contador
 */
const StatsDisplay = ({ count, state }) => {
  return (
    <div className="stats">
      <div className="stat-card">
        <h3>Dominadas</h3>
        <div className="value">{count}</div>
      </div>
      <div className="stat-card">
        <h3>Estado</h3>
        <div className="value state-value">{state}</div>
      </div>
    </div>
  )
}

export default StatsDisplay