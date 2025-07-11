"""
API de demonstração simplificada para o sistema de IA local
Funciona sem dependências externas para teste inicial
"""

from flask import Blueprint, request, jsonify
import json
import logging
from datetime import datetime

# Blueprint para demonstração
demo_bp = Blueprint('ia_local_demo', __name__, url_prefix='/api/ia/local')

# Configuração de logging
logger = logging.getLogger('autobot.ia.demo')

@demo_bp.route('/status', methods=['GET'])
def get_status():
    """Status do sistema de IA local"""
    try:
        # Tentar importar o trainer
        from .local_trainer_simple import AutobotLocalTrainer
        trainer = AutobotLocalTrainer()
        status = trainer.get_status()
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "system": status,
            "message": "Sistema de IA local funcionando em modo simulação"
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@demo_bp.route('/chat', methods=['POST'])
def chat_demo():
    """Chat de demonstração com IA local"""
    data = request.get_json()
    message = data.get('message', '')
    user_id = data.get('user_id', 'demo_user')
    
    if not message:
        return jsonify({"error": "Mensagem é obrigatória"}), 400
    
    try:
        # Simulação de resposta inteligente
        responses = {
            "como funciona": "O AUTOBOT IA Local funciona com Ollama para processamento local, ChromaDB para armazenamento vetorial e memória conversacional persistente.",
            "bitrix24": "Sim! O AUTOBOT integra perfeitamente com Bitrix24 através de webhooks e APIs para automação de tarefas corporativas.",
            "automação": "O sistema permite automação de tarefas corporativas usando PyAutoGUI, Selenium e navegação web inteligente.",
            "teste": "Sistema de teste funcionando! Todos os componentes de IA local estão operacionais em modo simulação.",
            "status": "Sistema funcionando perfeitamente! IA local ativa, memória vetorial disponível e integração pronta."
        }
        
        # Buscar resposta baseada em palavras-chave
        message_lower = message.lower()
        bot_response = "Sou o AUTOBOT IA Local! Posso ajudar com automação corporativa, integração com Bitrix24, IXCSOFT e outras plataformas. Como posso ajudar?"
        
        for keyword, response in responses.items():
            if keyword in message_lower:
                bot_response = response
                break
        
        # Simular salvamento na memória
        interaction = {
            "user_id": user_id,
            "message": message,
            "response": bot_response,
            "timestamp": datetime.now().isoformat(),
            "model": "autobot-corporativo-demo"
        }
        
        return jsonify({
            "status": "success",
            "response": bot_response,
            "user_id": user_id,
            "model": "autobot-corporativo-demo",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@demo_bp.route('/knowledge', methods=['POST'])
def add_knowledge_demo():
    """Demonstração de adição de conhecimento"""
    data = request.get_json()
    documents = data.get('documents', [])
    collection = data.get('collection', 'autobot_knowledge')
    
    if not documents:
        return jsonify({"error": "Documentos são obrigatórios"}), 400
    
    try:
        from .local_trainer_simple import AutobotLocalTrainer
        trainer = AutobotLocalTrainer()
        result = trainer.add_knowledge(documents, collection)
        
        return jsonify({
            "status": "success", 
            "message": result,
            "documents_added": len(documents),
            "collection": collection
        })
        
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@demo_bp.route('/search', methods=['POST'])
def search_knowledge_demo():
    """Demonstração de busca de conhecimento"""
    data = request.get_json()
    query = data.get('query', '')
    collection = data.get('collection', 'autobot_knowledge')
    limit = data.get('limit', 5)
    
    if not query:
        return jsonify({"error": "Query é obrigatória"}), 400
    
    try:
        from .local_trainer_simple import AutobotLocalTrainer
        trainer = AutobotLocalTrainer()
        results = trainer.search_knowledge(query, collection, limit)
        
        return jsonify({
            "status": "success", 
            "query": query,
            "results": results,
            "collection": collection
        })
        
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@demo_bp.route('/setup', methods=['POST'])
def setup_demo():
    """Demonstração de setup do sistema"""
    try:
        from .local_trainer_simple import AutobotLocalTrainer
        trainer = AutobotLocalTrainer()
        
        # Simular setup de modelos
        models = trainer.setup_models()
        
        # Simular criação de modelo personalizado
        custom_model = trainer.create_custom_model(
            "autobot-corporativo-demo",
            "Você é o AUTOBOT, especialista em automação corporativa"
        )
        
        return jsonify({
            "status": "success",
            "message": "Sistema de IA local configurado com sucesso (modo demo)!",
            "models": models,
            "custom_model": custom_model,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500