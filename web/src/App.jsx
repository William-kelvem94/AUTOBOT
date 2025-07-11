import React, { useState, useEffect } from 'react'

function App() {
  const [healthData, setHealthData] = useState(null)
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchHealthData()
    fetchMetrics()
    
    // Atualiza dados a cada 30 segundos
    const interval = setInterval(() => {
      fetchHealthData()
      fetchMetrics()
    }, 30000)
    
    return () => clearInterval(interval)
  }, [])

  const fetchHealthData = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/health/detailed')
      const data = await response.json()
      setHealthData(data)
    } catch (error) {
      console.error('Erro ao buscar dados de saúde:', error)
    }
  }

  const fetchMetrics = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/metrics')
      const data = await response.json()
      setMetrics(data)
      setLoading(false)
    } catch (error) {
      console.error('Erro ao buscar métricas:', error)
      setLoading(false)
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'var(--success-color)'
      case 'warning': return 'var(--warning-color)'
      case 'unhealthy': case 'offline': return 'var(--danger-color)'
      default: return 'var(--secondary-color)'
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy': return '✅'
      case 'warning': return '⚠️'
      case 'unhealthy': case 'offline': return '❌'
      default: return '❓'
    }
  }

  if (loading) {
    return (
      <div className="container" style={{ padding: '50px 20px', textAlign: 'center' }}>
        <div className="spinner" style={{ margin: '0 auto' }}></div>
        <p style={{ marginTop: '20px' }}>Carregando AUTOBOT...</p>
      </div>
    )
  }

  return (
    <div>
      {/* Navbar */}
      <nav className="navbar">
        <div className="container">
          <div className="navbar-content">
            <a href="#" className="navbar-brand">🤖 AUTOBOT</a>
            <div className="navbar-nav">
              <a href="#" className="nav-link">Dashboard</a>
              <a href="#" className="nav-link">Tarefas</a>
              <a href="#" className="nav-link">IA</a>
              <a href="#" className="nav-link">Configurações</a>
            </div>
          </div>
        </div>
      </nav>

      {/* Conteúdo Principal */}
      <div className="container" style={{ padding: '30px 20px' }}>
        
        {/* Header */}
        <div className="text-center mb-5">
          <h1>🤖 AUTOBOT - Sistema de IA Corporativa</h1>
          <p className="text-secondary">Dashboard de Monitoramento e Controle</p>
        </div>

        {/* Status Geral */}
        {healthData && (
          <div className="card mb-4">
            <div className="card-header">
              <h3 className="card-title">Status do Sistema</h3>
              <div className="status-indicator" style={{ 
                backgroundColor: `${getStatusColor(healthData.status)}20`,
                color: getStatusColor(healthData.status)
              }}>
                {getStatusIcon(healthData.status)} {healthData.status}
              </div>
            </div>
            <div className="grid grid-2">
              <div>
                <strong>Última Verificação:</strong><br />
                {new Date(healthData.timestamp).toLocaleString('pt-BR')}
              </div>
              <div>
                <strong>Componentes Ativos:</strong><br />
                {Object.keys(healthData.components).length} componentes
              </div>
            </div>
          </div>
        )}

        {/* Métricas do Sistema */}
        {metrics && metrics.current_system && (
          <div className="grid grid-3 mb-4">
            <div className="card metric-card">
              <span className="metric-value">{metrics.current_system.cpu_usage.toFixed(1)}%</span>
              <div className="metric-label">CPU</div>
              <div className="progress-bar mt-2">
                <div className="progress-fill" style={{ width: `${metrics.current_system.cpu_usage}%` }}></div>
              </div>
            </div>
            <div className="card metric-card">
              <span className="metric-value">{metrics.current_system.memory_usage.toFixed(1)}%</span>
              <div className="metric-label">Memória</div>
              <div className="progress-bar mt-2">
                <div className="progress-fill" style={{ width: `${metrics.current_system.memory_usage}%` }}></div>
              </div>
            </div>
            <div className="card metric-card">
              <span className="metric-value">{metrics.current_system.disk_usage.toFixed(1)}%</span>
              <div className="metric-label">Disco</div>
              <div className="progress-bar mt-2">
                <div className="progress-fill" style={{ width: `${metrics.current_system.disk_usage}%` }}></div>
              </div>
            </div>
          </div>
        )}

        {/* Componentes do Sistema */}
        {healthData && healthData.components && (
          <div className="card mb-4">
            <div className="card-header">
              <h3 className="card-title">Componentes do Sistema</h3>
            </div>
            <div className="grid grid-2">
              {Object.entries(healthData.components).map(([name, component]) => (
                <div key={name} className="card" style={{ margin: '10px 0' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <strong style={{ textTransform: 'capitalize' }}>{name}</strong>
                    <div className="status-indicator" style={{ 
                      backgroundColor: `${getStatusColor(component.status || 'unknown')}20`,
                      color: getStatusColor(component.status || 'unknown')
                    }}>
                      {getStatusIcon(component.status || 'unknown')} 
                      {component.status || 'unknown'}
                    </div>
                  </div>
                  {component.message && (
                    <p style={{ margin: '5px 0 0 0', fontSize: '14px', color: 'var(--text-secondary)' }}>
                      {component.message}
                    </p>
                  )}
                  {component.error && (
                    <p style={{ margin: '5px 0 0 0', fontSize: '12px', color: 'var(--danger-color)' }}>
                      Erro: {component.error}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Métricas de API */}
        {metrics && metrics.api_metrics && metrics.api_metrics.length > 0 && (
          <div className="card mb-4">
            <div className="card-header">
              <h3 className="card-title">Métricas de API (24h)</h3>
            </div>
            <table className="table">
              <thead>
                <tr>
                  <th>Endpoint</th>
                  <th>Requests</th>
                  <th>Tempo Médio</th>
                  <th>Status Médio</th>
                </tr>
              </thead>
              <tbody>
                {metrics.api_metrics.map((metric, index) => (
                  <tr key={index}>
                    <td>{metric.endpoint || 'N/A'}</td>
                    <td>{metric.request_count}</td>
                    <td>{(metric.avg_response_time * 1000).toFixed(0)}ms</td>
                    <td>{metric.avg_status_code.toFixed(0)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Ações Rápidas */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Ações Rápidas</h3>
          </div>
          <div className="grid grid-4">
            <button className="btn btn-primary">
              🔄 Atualizar Status
            </button>
            <button className="btn btn-success">
              ▶️ Executar Tarefa
            </button>
            <button className="btn btn-warning">
              🤖 Status IA
            </button>
            <button className="btn btn-secondary">
              ⚙️ Configurações
            </button>
          </div>
        </div>

      </div>

      {/* Footer */}
      <footer style={{ 
        textAlign: 'center', 
        padding: '20px', 
        marginTop: '50px',
        borderTop: '1px solid var(--border-color)',
        color: 'var(--text-secondary)'
      }}>
        <p>🤖 AUTOBOT v1.0.0 - Sistema de IA Corporativa</p>
      </footer>
    </div>
  )
}

export default App