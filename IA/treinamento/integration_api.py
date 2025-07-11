"""
API de Integração com Sistema Existente
======================================

Este módulo implementa endpoints REST para interação com o motor de IA.
"""

import os
import json
import logging
import sys
from typing import Dict, Any
from flask import Blueprint, request, jsonify, current_app, g
from functools import wraps

# Adiciona o diretório raiz ao path para importar módulos existentes
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from autobot.ai.engine import AIEngine  # Importa o AIEngine existente
except ImportError:
    AIEngine = None

from .local_trainer import AutobotLocalTrainer
from .memory_manager import ConversationMemory

# Configuração de logging
logger = logging.getLogger('autobot.api.ai')

# Criar blueprint
ai_local_bp = Blueprint('ai_local', __name__, url_prefix='/api/ia/local')

# Instâncias globais
trainer = AutobotLocalTrainer()
memory = ConversationMemory()

# Decorator para verificar autenticação
def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Verificar se o usuário está autenticado
        if not g.get('user'):
            return jsonify({
                'success': False,
                'error': 'Unauthorized',
                'message': 'Autenticação necessária'
            }), 401
        return f(*args, **kwargs)
    return decorated

# Endpoint para configurar sistema de IA local
@ai_local_bp.route('/setup', methods=['POST'])
def setup_local_ai():
    """Configura sistema de IA local"""
    try:
        installed_models = trainer.setup_models()
        
        # Cria modelo personalizado AUTOBOT
        autobot_prompt = """
Você é o AUTOBOT, um assistente de IA especializado em automação corporativa.
Suas especialidades incluem:
- Integração com Bitrix24, IXCSOFT, Locaweb, Fluctus, Newave, Uzera, PlayHub
- Automação de tarefas usando PyAutoGUI e Selenium
- Análise de dados corporativos
- Navegação web inteligente
- Processamento de webhooks e APIs

Sempre responda de forma útil, precisa e focada nas necessidades corporativas.
"""
        
        custom_result = trainer.create_custom_model("autobot-corporativo", autobot_prompt)
        
        return jsonify({
            "status": "success",
            "installed_models": installed_models,
            "custom_model": custom_result,
            "message": "Sistema de IA local configurado com sucesso!"
        })
        
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@ai_local_bp.route('/chat', methods=['POST'])
def chat_with_local_ai():
    """Chat usando IA local"""
    data = request.get_json()
    message = data.get('message', '')
    user_id = data.get('user_id', 'anonymous')
    use_context = data.get('use_context', True)
    
    if not message:
        return jsonify({"error": "Mensagem é obrigatória"}), 400
    
    try:
        # Busca contexto se solicitado
        context = ""
        if use_context:
            user_context = memory.get_user_context(user_id, limit=5)
            if user_context.get('conversations'):
                context = "Contexto das conversas anteriores:\n" + "\n".join(user_context['conversations'][-3:])
        
        # Processa com Ollama
        prompt = f"{context}\n\nPergunta atual: {message}" if context else message
        
        response = trainer.ollama_client.generate(
            model="autobot-corporativo",
            prompt=prompt,
            options={"temperature": 0.7}
        )
        
        bot_response = response.get('response', 'Desculpe, não consegui processar sua mensagem.')
        
        # Salva na memória
        memory.save_interaction(user_id, message, bot_response)
        
        return jsonify({
            "status": "success",
            "response": bot_response,
            "model": "autobot-corporativo",
            "user_id": user_id
        })
        
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@ai_local_bp.route('/knowledge', methods=['POST'])
def add_knowledge():
    """Adiciona conhecimento à base vetorial"""
    data = request.get_json()
    documents = data.get('documents', [])
    collection = data.get('collection', 'autobot_knowledge')
    
    if not documents:
        return jsonify({"error": "Documentos são obrigatórios"}), 400
    
    try:
        result = trainer.add_knowledge(documents, collection)
        return jsonify({"status": "success", "message": result})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@ai_local_bp.route('/search', methods=['POST'])
def search_knowledge():
    """Busca na base de conhecimento"""
    data = request.get_json()
    query = data.get('query', '')
    collection = data.get('collection', 'autobot_knowledge')
    limit = data.get('limit', 5)
    
    if not query:
        return jsonify({"error": "Query é obrigatória"}), 400
    
    try:
        results = trainer.search_knowledge(query, collection, limit)
        return jsonify({"status": "success", "results": results})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@ai_local_bp.route('/status', methods=['GET'])
def get_local_ai_status():
    """Status do sistema de IA local"""
    try:
        # Verifica se Ollama está funcionando
        models = trainer.ollama_client.list()
        
        # Verifica ChromaDB
        collections = trainer.chroma_client.list_collections()
        
        return jsonify({
            "status": "healthy",
            "ollama": {
                "available": True,
                "models": [m.get('name', 'unknown') for m in models.get('models', [])]
            },
            "chromadb": {
                "available": True,
                "collections": [c.name for c in collections]
            },
            "memory": {
                "conversations_count": memory.conversations.count(),
                "context_count": memory.context.count()
            }
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "ollama": {"available": False},
            "chromadb": {"available": False}
        }), 500

# Função para registrar o blueprint na aplicação
def register_ai_blueprint(app):
    app.register_blueprint(ai_local_bp)
    logger.info("Blueprint da API de IA registrado com sucesso")