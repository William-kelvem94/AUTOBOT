/**
 * AUTOBOT JavaScript Client
 * Handles WebSocket communication, UI interactions, and API calls
 */

class AutobotClient {
    constructor() {
        this.ws = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.clientId = this.generateClientId();
        this.currentView = 'chat';
        
        this.init();
    }

    generateClientId() {
        return 'client_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    }

    init() {
        this.setupEventListeners();
        this.connectWebSocket();
        this.loadInitialData();
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const view = e.target.getAttribute('data-view');
                this.switchView(view);
            });
        });

        // Chat input
        const messageInput = document.getElementById('message-input');
        const sendBtn = document.getElementById('send-btn');

        messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        messageInput.addEventListener('input', () => {
            this.autoResizeTextarea(messageInput);
        });

        sendBtn.addEventListener('click', () => this.sendMessage());

        // Quick suggestions
        document.querySelectorAll('.suggestion').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const text = e.target.getAttribute('data-text');
                messageInput.value = text;
                this.sendMessage();
            });
        });

        // Voice button
        document.getElementById('voice-btn').addEventListener('click', () => {
            this.startVoiceRecognition();
        });

        // Quick actions
        document.querySelectorAll('.quick-action').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.target.getAttribute('data-action');
                this.handleQuickAction(action);
            });
        });

        // Automation buttons
        document.getElementById('create-automation-btn')?.addEventListener('click', () => {
            this.showCreateAutomationModal();
        });

        // Settings
        this.setupSettingsListeners();
    }

    setupSettingsListeners() {
        const temperatureSlider = document.getElementById('temperature');
        const temperatureValue = document.getElementById('temperature-value');
        
        if (temperatureSlider && temperatureValue) {
            temperatureSlider.addEventListener('input', (e) => {
                temperatureValue.textContent = e.target.value;
            });
        }
    }

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/${this.clientId}`;

        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.updateConnectionStatus(true);
                this.showNotification('Conectado ao AUTOBOT', 'success');
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.isConnected = false;
                this.updateConnectionStatus(false);
                this.attemptReconnect();
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.showNotification('Erro de conexão', 'error');
            };

        } catch (error) {
            console.error('Failed to create WebSocket:', error);
            this.attemptReconnect();
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
            
            setTimeout(() => {
                this.connectWebSocket();
            }, this.reconnectDelay * this.reconnectAttempts);
        } else {
            this.showNotification('Falha ao conectar. Recarregue a página.', 'error');
        }
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'chat_response':
                this.displayMessage(data.message, 'assistant', data.metadata);
                break;
            case 'automation_created':
                this.showNotification(`Automação "${data.name}" criada com sucesso!`, 'success');
                this.loadAutomations();
                break;
            case 'automation_result':
                this.displayAutomationResult(data.result);
                break;
            case 'error':
                this.showNotification(data.message, 'error');
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }

    sendMessage() {
        const messageInput = document.getElementById('message-input');
        const message = messageInput.value.trim();

        if (!message || !this.isConnected) {
            return;
        }

        // Display user message
        this.displayMessage(message, 'user');

        // Send via WebSocket
        this.ws.send(JSON.stringify({
            type: 'chat',
            message: message,
            user_id: 'web_user',
            session_id: this.clientId,
            timestamp: new Date().toISOString()
        }));

        // Clear input
        messageInput.value = '';
        this.autoResizeTextarea(messageInput);

        // Show loading
        this.showTypingIndicator();
    }

    displayMessage(content, sender, metadata = {}) {
        const messagesContainer = document.getElementById('chat-messages');
        
        // Remove typing indicator
        this.hideTypingIndicator();

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Format content
        if (typeof content === 'string') {
            contentDiv.innerHTML = this.formatMessageContent(content);
        } else {
            contentDiv.textContent = JSON.stringify(content);
        }

        // Add metadata if available
        if (metadata && Object.keys(metadata).length > 0) {
            const metadataDiv = document.createElement('div');
            metadataDiv.className = 'message-metadata';
            metadataDiv.innerHTML = `<small>Confiança: ${Math.round((metadata.confidence || 0) * 100)}%</small>`;
            contentDiv.appendChild(metadataDiv);
        }

        messageDiv.appendChild(contentDiv);
        messagesContainer.appendChild(messageDiv);

        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    formatMessageContent(content) {
        // Convert markdown-style formatting
        content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        content = content.replace(/\*(.*?)\*/g, '<em>$1</em>');
        content = content.replace(/`(.*?)`/g, '<code>$1</code>');
        
        // Convert line breaks
        content = content.replace(/\n/g, '<br>');
        
        return content;
    }

    showTypingIndicator() {
        const messagesContainer = document.getElementById('chat-messages');
        
        if (document.querySelector('.typing-indicator')) {
            return; // Already showing
        }

        const typingDiv = document.createElement('div');
        typingDiv.className = 'message assistant typing-indicator';
        typingDiv.innerHTML = `
            <div class="message-content">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;

        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // Add CSS for typing animation
        const style = document.createElement('style');
        style.textContent = `
            .typing-dots {
                display: flex;
                gap: 4px;
                align-items: center;
            }
            .typing-dots span {
                width: 8px;
                height: 8px;
                background: var(--text-secondary);
                border-radius: 50%;
                animation: typing 1.5s infinite;
            }
            .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
            .typing-dots span:nth-child(3) { animation-delay: 0.4s; }
            @keyframes typing {
                0%, 60%, 100% { opacity: 0.3; transform: scale(0.8); }
                30% { opacity: 1; transform: scale(1); }
            }
        `;
        document.head.appendChild(style);
    }

    hideTypingIndicator() {
        const indicator = document.querySelector('.typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    autoResizeTextarea(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }

    switchView(viewName) {
        // Hide all views
        document.querySelectorAll('.view').forEach(view => {
            view.classList.remove('active');
        });

        // Remove active from nav links
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });

        // Show selected view
        const targetView = document.getElementById(`${viewName}-view`);
        if (targetView) {
            targetView.classList.add('active');
            this.currentView = viewName;

            // Add active to nav link
            const navLink = document.querySelector(`[data-view="${viewName}"]`);
            if (navLink) {
                navLink.classList.add('active');
            }

            // Load view-specific data
            this.loadViewData(viewName);
        }
    }

    loadViewData(viewName) {
        switch (viewName) {
            case 'automations':
                this.loadAutomations();
                break;
            case 'integrations':
                this.loadIntegrations();
                break;
            case 'knowledge':
                this.loadKnowledge();
                break;
        }
    }

    async loadAutomations() {
        try {
            const response = await fetch('/api/automation/list');
            const automations = await response.json();
            
            this.displayAutomations(automations);
            this.updateAutomationStats(automations);
        } catch (error) {
            console.error('Error loading automations:', error);
            this.showNotification('Erro ao carregar automações', 'error');
        }
    }

    displayAutomations(automations) {
        const container = document.getElementById('automations-list');
        if (!container) return;

        if (automations.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <h3>Nenhuma automação encontrada</h3>
                    <p>Crie sua primeira automação usando o botão acima ou através do chat.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = automations.map(automation => `
            <div class="automation-card" data-id="${automation.id}">
                <div class="automation-header">
                    <h4>${automation.name}</h4>
                    <div class="automation-actions">
                        <button class="btn-sm" onclick="autobot.executeAutomation('${automation.id}')">▶️ Executar</button>
                        <button class="btn-sm" onclick="autobot.editAutomation('${automation.id}')">✏️ Editar</button>
                        <button class="btn-sm danger" onclick="autobot.deleteAutomation('${automation.id}')">🗑️</button>
                    </div>
                </div>
                <p class="automation-description">${automation.description}</p>
                <div class="automation-stats">
                    <span class="stat">${automation.steps.length} passos</span>
                    <span class="stat">${automation.is_active ? 'Ativa' : 'Inativa'}</span>
                </div>
            </div>
        `).join('');
    }

    updateAutomationStats(automations) {
        document.getElementById('total-automations').textContent = automations.length;
        document.getElementById('active-automations').textContent = 
            automations.filter(a => a.is_active).length;
        // executions-today would need to be fetched from backend
    }

    async loadIntegrations() {
        try {
            const response = await fetch('/api/integration/platforms');
            const data = await response.json();
            
            this.displayIntegrations(data.platforms);
        } catch (error) {
            console.error('Error loading integrations:', error);
        }
    }

    displayIntegrations(platforms) {
        const container = document.getElementById('integrations-grid');
        if (!container) return;

        container.innerHTML = platforms.map(platform => `
            <div class="integration-card ${platform.status}">
                <div class="integration-header">
                    <h4>${platform.name}</h4>
                    <span class="status-badge ${platform.status}">${this.getStatusText(platform.status)}</span>
                </div>
                <p>${platform.description}</p>
                <div class="integration-features">
                    ${platform.features.map(feature => `<span class="feature">${feature}</span>`).join('')}
                </div>
                <div class="integration-actions">
                    ${platform.status === 'available' ? 
                        `<button class="primary-btn" onclick="autobot.configureIntegration('${platform.id}')">Configurar</button>` :
                        `<button class="secondary-btn" disabled>Em breve</button>`
                    }
                </div>
            </div>
        `).join('');
    }

    getStatusText(status) {
        const statusMap = {
            'available': 'Disponível',
            'planned': 'Planejado',
            'configured': 'Configurado'
        };
        return statusMap[status] || status;
    }

    async loadKnowledge() {
        // Implementation for loading knowledge base
        console.log('Loading knowledge base...');
    }

    handleQuickAction(action) {
        switch (action) {
            case 'create-automation':
                this.showCreateAutomationModal();
                break;
            case 'record-actions':
                this.startRecording();
                break;
            case 'list-automations':
                this.switchView('automations');
                break;
        }
    }

    showCreateAutomationModal() {
        const modal = document.getElementById('modal-overlay');
        const content = document.getElementById('modal-content');
        
        content.innerHTML = `
            <h3>Criar Nova Automação</h3>
            <form id="create-automation-form">
                <div class="form-group">
                    <label for="automation-description">Descreva o que você quer automatizar:</label>
                    <textarea id="automation-description" rows="4" 
                        placeholder="Ex: Abrir o navegador Chrome e navegar para o Google"
                        required></textarea>
                </div>
                <div class="form-actions">
                    <button type="button" onclick="autobot.closeModal()" class="secondary-btn">Cancelar</button>
                    <button type="submit" class="primary-btn">Criar Automação</button>
                </div>
            </form>
        `;

        document.getElementById('create-automation-form').addEventListener('submit', (e) => {
            e.preventDefault();
            const description = document.getElementById('automation-description').value;
            this.createAutomation(description);
        });

        modal.classList.add('active');
    }

    createAutomation(description) {
        if (!this.isConnected) {
            this.showNotification('Não conectado ao servidor', 'error');
            return;
        }

        this.ws.send(JSON.stringify({
            type: 'automation',
            action: 'create',
            description: description,
            user_id: 'web_user'
        }));

        this.closeModal();
        this.showNotification('Criando automação...', 'info');
    }

    async executeAutomation(id) {
        try {
            const response = await fetch('/api/automation/execute', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    script_id: id,
                    parameters: {}
                })
            });

            const result = await response.json();
            this.displayAutomationResult(result);
        } catch (error) {
            console.error('Error executing automation:', error);
            this.showNotification('Erro ao executar automação', 'error');
        }
    }

    displayAutomationResult(result) {
        const success = result.success ? 'sucesso' : 'erro';
        const message = `Automação ${result.script_name}: ${success}`;
        this.showNotification(message, result.success ? 'success' : 'error');
    }

    startVoiceRecognition() {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            const recognition = new SpeechRecognition();
            
            recognition.lang = 'pt-BR';
            recognition.continuous = false;
            recognition.interimResults = false;

            recognition.onstart = () => {
                document.getElementById('voice-btn').style.background = 'var(--error)';
                this.showNotification('Ouvindo...', 'info');
            };

            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                document.getElementById('message-input').value = transcript;
                this.sendMessage();
            };

            recognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
                this.showNotification('Erro no reconhecimento de voz', 'error');
            };

            recognition.onend = () => {
                document.getElementById('voice-btn').style.background = '';
            };

            recognition.start();
        } else {
            this.showNotification('Reconhecimento de voz não suportado', 'error');
        }
    }

    closeModal() {
        document.getElementById('modal-overlay').classList.remove('active');
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        // Add styles
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 1001;
            animation: slideIn 0.3s ease;
        `;

        switch (type) {
            case 'success':
                notification.style.background = 'var(--success)';
                break;
            case 'error':
                notification.style.background = 'var(--error)';
                break;
            case 'warning':
                notification.style.background = 'var(--warning)';
                break;
            default:
                notification.style.background = 'var(--primary-color)';
        }

        document.body.appendChild(notification);

        // Auto remove after 3 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);

        // Add slide animations
        if (!document.querySelector('#notification-styles')) {
            const style = document.createElement('style');
            style.id = 'notification-styles';
            style.textContent = `
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                @keyframes slideOut {
                    from { transform: translateX(0); opacity: 1; }
                    to { transform: translateX(100%); opacity: 0; }
                }
            `;
            document.head.appendChild(style);
        }
    }

    updateConnectionStatus(connected) {
        const statusDot = document.getElementById('status-dot');
        const statusText = document.getElementById('status-text');
        
        if (connected) {
            statusDot.className = 'status-dot online';
            statusText.textContent = 'Conectado';
        } else {
            statusDot.className = 'status-dot offline';
            statusText.textContent = 'Desconectado';
        }
    }

    async loadInitialData() {
        // Load system info
        this.updateSystemInfo();
        
        // Load health status
        try {
            const response = await fetch('/health');
            const health = await response.json();
            console.log('System health:', health);
        } catch (error) {
            console.error('Error checking system health:', error);
        }
    }

    updateSystemInfo() {
        // Update CPU and memory usage (placeholder)
        document.getElementById('cpu-usage').textContent = '45%';
        document.getElementById('memory-usage').textContent = '2.1GB';
    }
}

// Initialize AUTOBOT when page loads
let autobot;
document.addEventListener('DOMContentLoaded', () => {
    autobot = new AutobotClient();
});

// Make autobot available globally
window.autobot = autobot;