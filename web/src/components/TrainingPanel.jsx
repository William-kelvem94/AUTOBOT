import React, { useState, useEffect } from 'react';
import './TrainingPanel.css';

const TrainingPanel = () => {
    const [exemplos, setExemplos] = useState('');
    const [nomeModelo, setNomeModelo] = useState('autobot-personalizado');
    const [status, setStatus] = useState('');
    const [loading, setLoading] = useState(false);
    const [modelos, setModelos] = useState([]);
    const [sistemStatus, setSistemStatus] = useState(null);
    const [activeTab, setActiveTab] = useState('treinar');
    const [testePergunta, setTestePergunta] = useState('Como posso automatizar uma tarefa?');
    const [testeResultado, setTesteResultado] = useState('');
    const [estatisticas, setEstatisticas] = useState(null);

    // Carrega status do sistema na inicialização
    useEffect(() => {
        carregarStatusSistema();
        carregarModelos();
        carregarEstatisticas();
    }, []);

    const carregarStatusSistema = async () => {
        try {
            const response = await fetch('/api/ia/status');
            const data = await response.json();
            setSistemStatus(data);
        } catch (error) {
            console.error('Erro ao carregar status:', error);
            setSistemStatus({ status: 'error', erro: 'Falha na conexão' });
        }
    };

    const carregarModelos = async () => {
        try {
            const response = await fetch('/api/ia/modelos');
            const data = await response.json();
            if (data.status === 'success') {
                setModelos(data.modelos || []);
            }
        } catch (error) {
            console.error('Erro ao carregar modelos:', error);
        }
    };

    const carregarEstatisticas = async () => {
        try {
            const response = await fetch('/api/ia/memoria/estatisticas');
            const data = await response.json();
            if (data.status === 'success') {
                setEstatisticas(data.estatisticas);
            }
        } catch (error) {
            console.error('Erro ao carregar estatísticas:', error);
        }
    };

    const configurarSistema = async () => {
        setLoading(true);
        setStatus('Configurando sistema de IA local...');
        
        try {
            const response = await fetch('/api/ia/setup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                setStatus('✅ Sistema configurado com sucesso!');
                await carregarStatusSistema();
                await carregarModelos();
            } else {
                setStatus(`❌ Erro na configuração: ${result.erro || result.message}`);
            }
        } catch (error) {
            setStatus(`❌ Erro de conexão: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    const treinarModelo = async () => {
        if (!exemplos.trim()) {
            setStatus('❌ Por favor, forneça exemplos de treinamento');
            return;
        }

        setLoading(true);
        setStatus('🧠 Treinando modelo personalizado...');
        
        try {
            const response = await fetch('/api/ia/treinar-personalizado', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    exemplos: exemplos,
                    nome_modelo: nomeModelo 
                })
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                setStatus(`✅ Modelo ${result.modelo} treinado com sucesso!`);
                await carregarModelos();
            } else {
                setStatus(`❌ Erro no treinamento: ${result.erro}`);
            }
        } catch (error) {
            setStatus(`❌ Erro de conexão: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    const testarModelo = async () => {
        if (!testePergunta.trim()) {
            setTesteResultado('❌ Por favor, forneça uma pergunta para teste');
            return;
        }

        setLoading(true);
        setTesteResultado('🧪 Testando modelo...');
        
        try {
            const response = await fetch('/api/ia/testar-modelo', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    modelo: nomeModelo,
                    pergunta: testePergunta 
                })
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                setTesteResultado(`✅ Resposta do modelo:\n\n${result.resposta}`);
            } else {
                setTesteResultado(`❌ Erro no teste: ${result.erro}`);
            }
        } catch (error) {
            setTesteResultado(`❌ Erro de conexão: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    const limparMemoria = async () => {
        if (!window.confirm('Deseja realmente limpar conversas antigas? Esta ação não pode ser desfeita.')) {
            return;
        }

        setLoading(true);
        try {
            const response = await fetch('/api/ia/memoria/limpar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ dias: 30 })
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                setStatus(`✅ ${result.message}`);
                await carregarEstatisticas();
            } else {
                setStatus(`❌ Erro na limpeza: ${result.erro}`);
            }
        } catch (error) {
            setStatus(`❌ Erro de conexão: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    const StatusIndicator = ({ status }) => {
        const getStatusColor = () => {
            if (status === 'success' || status === 'operacional') return '#4CAF50';
            if (status === 'warning') return '#FF9800';
            return '#F44336';
        };

        return (
            <div className="status-indicator" style={{ color: getStatusColor() }}>
                ● {status === 'success' || status === 'operacional' ? 'Online' : 
                   status === 'warning' ? 'Parcial' : 'Offline'}
            </div>
        );
    };

    return (
        <div className="training-panel">
            <div className="panel-header">
                <h2>🧠 Sistema de IA Local AUTOBOT</h2>
                {sistemStatus && (
                    <StatusIndicator status={sistemStatus.sistema_ia || sistemStatus.status} />
                )}
            </div>

            <div className="tabs">
                <button 
                    className={`tab ${activeTab === 'treinar' ? 'active' : ''}`}
                    onClick={() => setActiveTab('treinar')}
                >
                    🧠 Treinamento
                </button>
                <button 
                    className={`tab ${activeTab === 'testar' ? 'active' : ''}`}
                    onClick={() => setActiveTab('testar')}
                >
                    🧪 Teste
                </button>
                <button 
                    className={`tab ${activeTab === 'status' ? 'active' : ''}`}
                    onClick={() => setActiveTab('status')}
                >
                    📊 Status
                </button>
                <button 
                    className={`tab ${activeTab === 'memoria' ? 'active' : ''}`}
                    onClick={() => setActiveTab('memoria')}
                >
                    💾 Memória
                </button>
            </div>

            {activeTab === 'treinar' && (
                <div className="tab-content">
                    <h3>Treinamento de Modelo Personalizado</h3>
                    
                    <div className="form-group">
                        <label htmlFor="nomeModelo">Nome do Modelo:</label>
                        <input
                            id="nomeModelo"
                            type="text"
                            value={nomeModelo}
                            onChange={(e) => setNomeModelo(e.target.value)}
                            placeholder="autobot-personalizado"
                            className="form-input"
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="exemplos">Exemplos de Treinamento:</label>
                        <textarea
                            id="exemplos"
                            value={exemplos}
                            onChange={(e) => setExemplos(e.target.value)}
                            placeholder={`Exemplo:

P: Como integrar com Bitrix24?
R: Configure o webhook no Bitrix24 e use a API REST para sincronização automática.

P: Como automatizar cliques?
R: Use PyAutoGUI.click(x, y) para coordenadas específicas ou localize elementos por imagem.

Adicione mais exemplos específicos do seu domínio...`}
                            rows={12}
                            className="form-textarea"
                        />
                    </div>

                    <div className="button-group">
                        <button 
                            onClick={treinarModelo} 
                            disabled={loading}
                            className="btn-primary"
                        >
                            {loading ? '⏳ Treinando...' : '🧠 Treinar Modelo'}
                        </button>
                        
                        <button 
                            onClick={configurarSistema} 
                            disabled={loading}
                            className="btn-secondary"
                        >
                            {loading ? '⏳ Configurando...' : '⚙️ Configurar Sistema'}
                        </button>
                    </div>
                </div>
            )}

            {activeTab === 'testar' && (
                <div className="tab-content">
                    <h3>Teste de Modelo</h3>
                    
                    <div className="form-group">
                        <label htmlFor="modeloTeste">Modelo para Teste:</label>
                        <select
                            id="modeloTeste"
                            value={nomeModelo}
                            onChange={(e) => setNomeModelo(e.target.value)}
                            className="form-select"
                        >
                            <option value="autobot-personalizado">autobot-personalizado</option>
                            {modelos.map(modelo => (
                                <option key={modelo} value={modelo}>{modelo}</option>
                            ))}
                        </select>
                    </div>

                    <div className="form-group">
                        <label htmlFor="testePergunta">Pergunta de Teste:</label>
                        <textarea
                            id="testePergunta"
                            value={testePergunta}
                            onChange={(e) => setTestePergunta(e.target.value)}
                            placeholder="Digite uma pergunta para testar o modelo..."
                            rows={3}
                            className="form-textarea"
                        />
                    </div>

                    <button 
                        onClick={testarModelo} 
                        disabled={loading}
                        className="btn-primary"
                    >
                        {loading ? '⏳ Testando...' : '🧪 Testar Modelo'}
                    </button>

                    {testeResultado && (
                        <div className="result-box">
                            <h4>Resultado do Teste:</h4>
                            <pre className="result-text">{testeResultado}</pre>
                        </div>
                    )}
                </div>
            )}

            {activeTab === 'status' && (
                <div className="tab-content">
                    <h3>Status do Sistema</h3>
                    
                    {sistemStatus && (
                        <div className="status-grid">
                            <div className="status-card">
                                <h4>Sistema IA</h4>
                                <p className={`status-value ${sistemStatus.sistema_ia}`}>
                                    {sistemStatus.sistema_ia || 'Desconhecido'}
                                </p>
                            </div>
                            
                            <div className="status-card">
                                <h4>Modelos Disponíveis</h4>
                                <p className="status-value">
                                    {sistemStatus.modelos_disponiveis?.length || 0}
                                </p>
                            </div>
                            
                            {sistemStatus.modelos_disponiveis && (
                                <div className="status-card full-width">
                                    <h4>Lista de Modelos</h4>
                                    <ul className="models-list">
                                        {sistemStatus.modelos_disponiveis.map(modelo => (
                                            <li key={modelo}>{modelo}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>
                    )}
                    
                    <button 
                        onClick={carregarStatusSistema} 
                        disabled={loading}
                        className="btn-secondary"
                    >
                        🔄 Atualizar Status
                    </button>
                </div>
            )}

            {activeTab === 'memoria' && (
                <div className="tab-content">
                    <h3>Gerenciamento de Memória</h3>
                    
                    {estatisticas && (
                        <div className="stats-grid">
                            <div className="stat-card">
                                <h4>Conversas</h4>
                                <p className="stat-value">{estatisticas.total_conversas}</p>
                            </div>
                            
                            <div className="stat-card">
                                <h4>Conhecimento</h4>
                                <p className="stat-value">{estatisticas.total_conhecimento}</p>
                            </div>
                            
                            <div className="stat-card">
                                <h4>Usuários</h4>
                                <p className="stat-value">{estatisticas.usuarios_unicos}</p>
                            </div>
                            
                            <div className="stat-card">
                                <h4>Preferências</h4>
                                <p className="stat-value">{estatisticas.total_preferencias}</p>
                            </div>
                        </div>
                    )}

                    <div className="button-group">
                        <button 
                            onClick={carregarEstatisticas} 
                            disabled={loading}
                            className="btn-secondary"
                        >
                            🔄 Atualizar
                        </button>
                        
                        <button 
                            onClick={limparMemoria} 
                            disabled={loading}
                            className="btn-danger"
                        >
                            🗑️ Limpar Antigas
                        </button>
                    </div>
                </div>
            )}

            {status && (
                <div className="status-message">
                    {status}
                </div>
            )}
        </div>
    );
};

export default TrainingPanel;