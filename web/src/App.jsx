import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

// Componente principal do AUTOBOT
function App() {
  const [systemStatus, setSystemStatus] = useState(null);
  const [aiChat, setAiChat] = useState({ messages: [], loading: false });
  const [currentMessage, setCurrentMessage] = useState('');
  const [integrations, setIntegrations] = useState([]);
  const [activeTab, setActiveTab] = useState('dashboard');

  // Carrega dados iniciais
  useEffect(() => {
    loadSystemStatus();
    loadIntegrations();
  }, []);

  const loadSystemStatus = async () => {
    try {
      const response = await axios.get('/api/status');
      setSystemStatus(response.data);
    } catch (error) {
      console.error('Erro ao carregar status:', error);
    }
  };

  const loadIntegrations = async () => {
    try {
      const response = await axios.get('/api/integrations');
      setIntegrations(Object.entries(response.data.integrations));
    } catch (error) {
      console.error('Erro ao carregar integrações:', error);
    }
  };

  const sendAiMessage = async () => {
    if (!currentMessage.trim()) return;

    setAiChat(prev => ({
      ...prev,
      loading: true,
      messages: [...prev.messages, { type: 'user', content: currentMessage }]
    }));

    try {
      const response = await axios.post('/api/v1/ai/chat', {
        message: currentMessage,
        user_id: 'web_user'
      });

      if (response.data.status === 'success') {
        setAiChat(prev => ({
          ...prev,
          loading: false,
          messages: [...prev.messages, { 
            type: 'bot', 
            content: response.data.data.response,
            model: response.data.data.model,
            responseTime: response.data.data.response_time
          }]
        }));
      } else {
        throw new Error(response.data.error || 'Erro na resposta da IA');
      }
    } catch (error) {
      setAiChat(prev => ({
        ...prev,
        loading: false,
        messages: [...prev.messages, { 
          type: 'error', 
          content: error.response?.data?.error || 'Erro ao comunicar com IA'
        }]
      }));
    }

    setCurrentMessage('');
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendAiMessage();
    }
  };

  return (
    <div className="autobot-app">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <h1>🤖 AUTOBOT</h1>
          <p>Sistema de Automação Corporativa com IA Local</p>
          <div className="status-indicator">
            <span className={`status-dot ${systemStatus?.system?.name ? 'active' : 'inactive'}`}></span>
            {systemStatus?.system?.name ? 'Sistema Ativo' : 'Carregando...'}
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="app-nav">
        <button 
          className={activeTab === 'dashboard' ? 'active' : ''}
          onClick={() => setActiveTab('dashboard')}
        >
          📊 Dashboard
        </button>
        <button 
          className={activeTab === 'ai' ? 'active' : ''}
          onClick={() => setActiveTab('ai')}
        >
          🤖 IA Local
        </button>
        <button 
          className={activeTab === 'integrations' ? 'active' : ''}
          onClick={() => setActiveTab('integrations')}
        >
          🔗 Integrações
        </button>
        <button 
          className={activeTab === 'automation' ? 'active' : ''}
          onClick={() => setActiveTab('automation')}
        >
          ⚙️ Automação
        </button>
      </nav>

      {/* Main Content */}
      <main className="app-main">
        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && (
          <div className="dashboard">
            <h2>📊 Dashboard do Sistema</h2>
            
            {systemStatus && (
              <div className="dashboard-grid">
                <div className="dashboard-card">
                  <h3>💻 Sistema</h3>
                  <p>Versão: {systemStatus.system?.version}</p>
                  <p>Status: {systemStatus.system?.uptime}</p>
                  <p>IA: {systemStatus.ai_system?.enabled ? '✅ Ativa' : '❌ Inativa'}</p>
                </div>

                <div className="dashboard-card">
                  <h3>🔗 Integrações</h3>
                  <p>Total: {systemStatus.integrations?.corporate_systems}</p>
                  <p>Ativas: {systemStatus.integrations?.active_integrations}</p>
                  <p>Sistemas: {systemStatus.integrations?.systems?.join(', ')}</p>
                </div>

                <div className="dashboard-card">
                  <h3>⚙️ Automação</h3>
                  <p>Selenium: {systemStatus.automation?.selenium ? '✅' : '❌'}</p>
                  <p>PyAutoGUI: {systemStatus.automation?.pyautogui ? '✅' : '❌'}</p>
                  <p>Webhooks: {systemStatus.automation?.webhooks ? '✅' : '❌'}</p>
                </div>

                <div className="dashboard-card">
                  <h3>🤖 IA Local</h3>
                  <p>Endpoints: {systemStatus.ai_system?.endpoints?.length || 0}</p>
                  <p>Chat: {systemStatus.ai_system?.enabled ? '✅' : '❌'}</p>
                  <p>Conhecimento: {systemStatus.ai_system?.enabled ? '✅' : '❌'}</p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* AI Chat Tab */}
        {activeTab === 'ai' && (
          <div className="ai-chat">
            <h2>🤖 Chat com IA Local</h2>
            
            <div className="chat-container">
              <div className="chat-messages">
                {aiChat.messages.map((message, index) => (
                  <div key={index} className={`message ${message.type}`}>
                    <div className="message-content">
                      {message.content}
                      {message.model && (
                        <small className="message-meta">
                          Modelo: {message.model} | Tempo: {message.responseTime?.toFixed(2)}s
                        </small>
                      )}
                    </div>
                  </div>
                ))}
                {aiChat.loading && (
                  <div className="message bot loading">
                    <div className="message-content">🤖 Processando...</div>
                  </div>
                )}
              </div>

              <div className="chat-input">
                <textarea
                  value={currentMessage}
                  onChange={(e) => setCurrentMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Digite sua mensagem para o AUTOBOT..."
                  rows="3"
                />
                <button 
                  onClick={sendAiMessage}
                  disabled={!currentMessage.trim() || aiChat.loading}
                >
                  Enviar
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Integrations Tab */}
        {activeTab === 'integrations' && (
          <div className="integrations">
            <h2>🔗 Integrações Corporativas</h2>
            
            <div className="integrations-grid">
              {integrations.map(([key, integration]) => (
                <div key={key} className="integration-card">
                  <h3>{integration.name}</h3>
                  <p>{integration.description}</p>
                  <div className="integration-status">
                    <span className={`status-badge ${integration.status}`}>
                      {integration.status === 'active' ? '✅ Ativo' : '❌ Inativo'}
                    </span>
                  </div>
                  <div className="integration-endpoints">
                    <strong>Endpoints:</strong>
                    <ul>
                      {integration.endpoints.map((endpoint, idx) => (
                        <li key={idx}>{endpoint}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Automation Tab */}
        {activeTab === 'automation' && (
          <div className="automation">
            <h2>⚙️ Automação e Controle</h2>
            
            <div className="automation-sections">
              <div className="automation-section">
                <h3>🌐 Selenium WebDriver</h3>
                <p>Automação de navegadores web</p>
                <button className="automation-btn">Executar Automação Web</button>
              </div>

              <div className="automation-section">
                <h3>🖱️ PyAutoGUI</h3>
                <p>Automação de interface desktop</p>
                <button className="automation-btn">Executar Automação Desktop</button>
              </div>

              <div className="automation-section">
                <h3>🔗 Webhooks</h3>
                <p>Processamento de webhooks externos</p>
                <button className="automation-btn">Configurar Webhooks</button>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <p>AUTOBOT v2.0.0 - Sistema de Automação Corporativa com IA Local</p>
        <p>Desenvolvido com Flask + React + Ollama + ChromaDB</p>
      </footer>
    </div>
  );
}

export default App;