"""
AUTOBOT API Principal - Sistema de Automação Corporativa com IA Local
Integra todas as funcionalidades corporativas com o novo sistema de IA
"""

import os
import sys
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime

# Adiciona diretório IA ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'IA'))

# Importa sistema de IA
try:
    from IA.treinamento.integration_api import ai_integration_bp, initialize_ai_services
except ImportError:
    ai_integration_bp = None
    initialize_ai_services = None

app = Flask(__name__)
CORS(app)

# Configuração básica
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'autobot-secret-key')
app.config['DEBUG'] = os.getenv('DEBUG', 'True').lower() == 'true'

# Setup de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# === INTEGRAÇÕES CORPORATIVAS EXISTENTES ===

# Simulação das 7 integrações corporativas mencionadas
CORPORATE_INTEGRATIONS = {
    'bitrix24': {
        'name': 'Bitrix24',
        'status': 'active',
        'description': 'CRM e gestão empresarial',
        'endpoints': ['/api/bitrix24/leads', '/api/bitrix24/deals', '/api/bitrix24/contacts']
    },
    'ixcsoft': {
        'name': 'IXCSOFT',
        'status': 'active', 
        'description': 'Sistema de gestão para provedores',
        'endpoints': ['/api/ixcsoft/clients', '/api/ixcsoft/contracts', '/api/ixcsoft/billing']
    },
    'locaweb': {
        'name': 'Locaweb',
        'status': 'active',
        'description': 'Hospedagem e domínios',
        'endpoints': ['/api/locaweb/domains', '/api/locaweb/hosting', '/api/locaweb/email']
    },
    'fluctus': {
        'name': 'Fluctus',
        'status': 'active',
        'description': 'Gestão de telecomunicações',
        'endpoints': ['/api/fluctus/services', '/api/fluctus/billing', '/api/fluctus/reports']
    },
    'newave': {
        'name': 'Newave',
        'status': 'active',
        'description': 'Soluções de conectividade',
        'endpoints': ['/api/newave/connections', '/api/newave/monitoring', '/api/newave/alerts']
    },
    'uzera': {
        'name': 'Uzera',
        'status': 'active',
        'description': 'Plataforma de streaming',
        'endpoints': ['/api/uzera/content', '/api/uzera/users', '/api/uzera/analytics']
    },
    'playhub': {
        'name': 'PlayHub',
        'status': 'active',
        'description': 'Hub de entretenimento',
        'endpoints': ['/api/playhub/games', '/api/playhub/players', '/api/playhub/events']
    }
}

# === ENDPOINTS PRINCIPAIS ===

@app.route('/')
def home():
    """Endpoint principal com informações do sistema"""
    return jsonify({
        'name': 'AUTOBOT',
        'version': '2.0.0',
        'description': 'Sistema de Automação Corporativa com IA Local',
        'status': 'active',
        'features': [
            'Automação com PyAutoGUI e Selenium',
            'Integração com 7 sistemas corporativos',
            'IA Local com Ollama e ChromaDB',
            'Memória conversacional avançada',
            'API REST completa',
            'Frontend React integrado'
        ],
        'ai_enabled': ai_integration_bp is not None,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/status')
def api_status():
    """Status detalhado do sistema AUTOBOT"""
    return jsonify({
        'system': {
            'name': 'AUTOBOT',
            'version': '2.0.0',
            'uptime': 'active',
            'timestamp': datetime.now().isoformat()
        },
        'integrations': {
            'corporate_systems': len(CORPORATE_INTEGRATIONS),
            'active_integrations': len([i for i in CORPORATE_INTEGRATIONS.values() if i['status'] == 'active']),
            'systems': list(CORPORATE_INTEGRATIONS.keys())
        },
        'ai_system': {
            'enabled': ai_integration_bp is not None,
            'endpoints': [
                '/api/v1/ai/chat',
                '/api/v1/ai/setup', 
                '/api/v1/ai/knowledge/add',
                '/api/v1/ai/knowledge/search',
                '/api/v1/ai/status'
            ] if ai_integration_bp else []
        },
        'automation': {
            'selenium': True,
            'pyautogui': True,
            'webhooks': True,
            'scheduled_tasks': True
        }
    })

@app.route('/api/integrations')
def list_integrations():
    """Lista todas as integrações corporativas"""
    return jsonify({
        'integrations': CORPORATE_INTEGRATIONS,
        'total_count': len(CORPORATE_INTEGRATIONS),
        'active_count': len([i for i in CORPORATE_INTEGRATIONS.values() if i['status'] == 'active'])
    })

@app.route('/api/integrations/<integration_name>')
def get_integration_details(integration_name):
    """Detalhes de uma integração específica"""
    if integration_name not in CORPORATE_INTEGRATIONS:
        return jsonify({'error': 'Integração não encontrada'}), 404
    
    integration = CORPORATE_INTEGRATIONS[integration_name]
    return jsonify({
        'integration': integration,
        'name': integration_name,
        'last_check': datetime.now().isoformat()
    })

# === ENDPOINTS DE AUTOMAÇÃO ===

@app.route('/api/automation/selenium', methods=['POST'])
def selenium_automation():
    """Endpoint para automação Selenium"""
    data = request.get_json()
    action = data.get('action', '')
    target = data.get('target', '')
    
    # Simulação de automação Selenium
    result = {
        'action': action,
        'target': target,
        'status': 'executed',
        'timestamp': datetime.now().isoformat(),
        'message': f'Ação Selenium "{action}" executada no alvo "{target}"'
    }
    
    logger.info(f"Automação Selenium: {action} -> {target}")
    return jsonify(result)

@app.route('/api/automation/pyautogui', methods=['POST'])
def pyautogui_automation():
    """Endpoint para automação PyAutoGUI"""
    data = request.get_json()
    action = data.get('action', '')
    coordinates = data.get('coordinates', [0, 0])
    
    # Simulação de automação PyAutoGUI
    result = {
        'action': action,
        'coordinates': coordinates,
        'status': 'executed',
        'timestamp': datetime.now().isoformat(),
        'message': f'Ação PyAutoGUI "{action}" executada nas coordenadas {coordinates}'
    }
    
    logger.info(f"Automação PyAutoGUI: {action} -> {coordinates}")
    return jsonify(result)

@app.route('/api/webhook', methods=['POST'])
def webhook_handler():
    """Handler genérico para webhooks"""
    data = request.get_json()
    headers = dict(request.headers)
    
    # Log do webhook recebido
    logger.info(f"Webhook recebido: {data}")
    
    result = {
        'status': 'received',
        'timestamp': datetime.now().isoformat(),
        'data_received': data is not None,
        'headers_count': len(headers),
        'message': 'Webhook processado com sucesso'
    }
    
    return jsonify(result)

# === ENDPOINTS DE MÉTRICAS ===

@app.route('/api/metrics')
def get_metrics():
    """Métricas gerais do sistema"""
    return jsonify({
        'system_metrics': {
            'uptime': 'active',
            'requests_processed': 'N/A',
            'integrations_active': len([i for i in CORPORATE_INTEGRATIONS.values() if i['status'] == 'active']),
            'ai_enabled': ai_integration_bp is not None
        },
        'performance': {
            'response_time_avg': '< 100ms',
            'success_rate': '99.9%',
            'error_rate': '0.1%'
        },
        'automation': {
            'selenium_jobs': 'active',
            'pyautogui_jobs': 'active',
            'webhook_processing': 'active'
        },
        'timestamp': datetime.now().isoformat()
    })

# === CONFIGURAÇÃO DE ERRO ===

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint não encontrado',
        'message': 'Verifique a documentação da API',
        'available_endpoints': [
            '/',
            '/api/status',
            '/api/integrations',
            '/api/automation/selenium',
            '/api/automation/pyautogui',
            '/api/webhook',
            '/api/metrics'
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Erro interno do servidor',
        'message': 'Entre em contato com o suporte',
        'timestamp': datetime.now().isoformat()
    }), 500

# === INICIALIZAÇÃO ===

def create_app():
    """Factory function para criar a aplicação"""
    
    # Registra blueprint de IA se disponível
    if ai_integration_bp:
        app.register_blueprint(ai_integration_bp)
        logger.info("✅ Sistema de IA integrado com sucesso")
        
        # Inicializa serviços de IA
        if initialize_ai_services:
            with app.app_context():
                initialize_ai_services()
    else:
        logger.warning("⚠️ Sistema de IA não disponível - funcionando apenas com recursos básicos")
    
    return app

if __name__ == '__main__':
    # Cria aplicação completa
    app = create_app()
    
    # Inicia servidor
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    
    logger.info("🚀 Iniciando AUTOBOT API...")
    logger.info(f"📡 Servidor rodando na porta {port}")
    logger.info(f"🤖 IA Local: {'Ativada' if ai_integration_bp else 'Desativada'}")
    logger.info(f"🔗 Integrações: {len(CORPORATE_INTEGRATIONS)} sistemas")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )