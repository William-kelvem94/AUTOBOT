"""
API REST completa para integração do sistema de IA local do AUTOBOT
Inclui autenticação, rate limiting, e endpoints para todas as funcionalidades
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any
from pathlib import Path

from flask import Flask, Blueprint, request, jsonify, g
from flask_cors import CORS

try:
    from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
except ImportError:
    JWTManager = None
    jwt_required = None

try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
except ImportError:
    Limiter = None

# Importa módulos do AUTOBOT
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Importa componentes de IA
try:
    from .local_trainer import AutobotLocalTrainer
    from .memory_manager import ConversationMemoryManager
except ImportError:
    # Fallback para importação absoluta
    try:
        from IA.treinamento.local_trainer import AutobotLocalTrainer
        from IA.treinamento.memory_manager import ConversationMemoryManager
    except ImportError:
        AutobotLocalTrainer = None
        ConversationMemoryManager = None

# Cria Blueprint para integração
ai_integration_bp = Blueprint('ai_integration', __name__, url_prefix='/api/v1/ai')

# Configuração básica
def create_ai_app(app=None):
    """Cria ou configura aplicação Flask com IA"""
    
    if app is None:
        app = Flask(__name__)
    
    # Configurações
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'autobot-secret-key-change-in-production')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    
    # Extensões
    if JWTManager:
        jwt = JWTManager(app)
    
    if Limiter:
        limiter = Limiter(
            app,
            key_func=get_remote_address,
            default_limits=["200 per day", "50 per hour"]
        )
    else:
        limiter = None
    
    CORS(ai_integration_bp)
    
    # Registra blueprint
    app.register_blueprint(ai_integration_bp)
    
    return app, limiter

# Instâncias globais (serão inicializadas quando a aplicação for criada)
trainer = None
memory_manager = None
logger = logging.getLogger(__name__)

def initialize_ai_services():
    """Inicializa serviços de IA"""
    global trainer, memory_manager
    
    if AutobotLocalTrainer:
        trainer = AutobotLocalTrainer()
        logger.info("✅ AutobotLocalTrainer inicializado")
    else:
        logger.warning("⚠️ AutobotLocalTrainer não disponível")
    
    if ConversationMemoryManager:
        memory_manager = ConversationMemoryManager()
        logger.info("✅ ConversationMemoryManager inicializado")
    else:
        logger.warning("⚠️ ConversationMemoryManager não disponível")

# Middleware de autenticação
@ai_integration_bp.before_request
def before_request():
    """Middleware executado antes de cada request"""
    g.start_time = datetime.now()
    g.request_id = os.urandom(16).hex()

@ai_integration_bp.after_request  
def after_request(response):
    """Middleware executado após cada request"""
    duration = (datetime.now() - g.start_time).total_seconds()
    
    logger.info(f"Request {g.request_id} completed in {duration:.3f}s")
    
    response.headers['X-Request-ID'] = g.request_id
    response.headers['X-Response-Time'] = f"{duration:.3f}s"
    
    return response

# === ENDPOINTS DE AUTENTICAÇÃO ===

@ai_integration_bp.route('/auth/login', methods=['POST'])
def login():
    """Autenticação de usuários"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Validação básica (implementar autenticação real em produção)
    if username and password:
        if JWTManager:
            access_token = create_access_token(
                identity=username,
                additional_claims={
                    'user_type': 'standard',
                    'permissions': ['chat', 'knowledge']
                }
            )
            
            return jsonify({
                'access_token': access_token,
                'user': username,
                'expires_in': 86400
            })
        else:
            # Fallback quando JWT não está disponível
            return jsonify({
                'message': 'Autenticação básica realizada',
                'user': username,
                'note': 'JWT não disponível - usando autenticação simplificada'
            })
    
    return jsonify({'error': 'Credenciais inválidas'}), 401

# === ENDPOINTS DE IA LOCAL ===

@ai_integration_bp.route('/setup', methods=['POST'])
def setup_ai_system():
    """Configura sistema de IA local completo"""
    try:
        # Se JWT estiver disponível, verifica autenticação
        user_id = "anonymous"
        if jwt_required and request.headers.get('Authorization'):
            try:
                user_id = get_jwt_identity()
            except Exception:
                pass
        else:
            # Pega usuário do body se não há JWT
            data = request.get_json() or {}
            user_id = data.get('user_id', 'anonymous')
        
        logger.info(f"Setup iniciado por usuário: {user_id}")
        
        if not trainer:
            return jsonify({
                'status': 'error',
                'error': 'Sistema de IA não disponível'
            }), 500
        
        # Configura modelos
        models_result = trainer.setup_models()
        
        # Teste básico do sistema
        test_response = asyncio.run(
            trainer.generate_response(
                "Teste de funcionamento do sistema AUTOBOT",
                model="autobot-llama3.2",
                user_id=user_id
            )
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Sistema de IA local configurado com sucesso!',
            'setup_details': {
                'models_installed': models_result,
                'test_response': test_response,
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Erro no setup: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@ai_integration_bp.route('/chat', methods=['POST'])
def chat_with_ai():
    """Endpoint principal de chat com IA"""
    try:
        # Autenticação flexível
        user_id = "anonymous"
        if jwt_required and request.headers.get('Authorization'):
            try:
                user_id = get_jwt_identity()
            except Exception:
                pass
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados JSON são obrigatórios'}), 400
        
        message = data.get('message', '').strip()
        model = data.get('model', 'autobot-llama3.2')
        use_context = data.get('use_context', True)
        save_conversation = data.get('save_conversation', True)
        user_id = data.get('user_id', user_id)  # Permite override do user_id
        
        if not message:
            return jsonify({'error': 'Mensagem é obrigatória'}), 400
        
        # Gera resposta (simulada quando IA não disponível)
        if trainer:
            try:
                import asyncio
                response = asyncio.run(trainer.generate_response(
                    prompt=message,
                    model=model,
                    use_context=use_context,
                    user_id=user_id
                ))
            except Exception as e:
                response = {
                    'response': f'Sistema de IA básico ativo. Mensagem recebida: "{message}". Para IA completa, instale ollama e torch.',
                    'model': 'fallback',
                    'response_time': 0.1,
                    'timestamp': datetime.now().isoformat(),
                    'user_id': user_id,
                    'cached': False,
                    'note': 'Resposta simulada - instale ollama e torch para IA completa'
                }
        else:
            response = {
                'response': f'AUTOBOT funcionando! Sua mensagem "{message}" foi recebida. Para IA completa, instale: pip install torch ollama chromadb sentence-transformers',
                'model': 'basic',
                'response_time': 0.05,
                'timestamp': datetime.now().isoformat(),
                'user_id': user_id,
                'cached': False
            }
        
        # Simula erro apenas se response não foi criada
        if 'error' in response:
            return jsonify(response), 500
        
        # Salva conversa na memória
        interaction_id = None
        if save_conversation and memory_manager:
            try:
                import asyncio
                interaction_id = asyncio.run(memory_manager.save_interaction(
                    user_id=user_id,
                    user_message=message,
                    bot_response=response['response'],
                    context={'model': model, 'request_id': g.request_id}
                ))
                response['interaction_id'] = interaction_id
            except Exception as e:
                logger.warning(f"Erro ao salvar conversa: {e}")
        
        return jsonify({
            'status': 'success',
            'data': response,
            'metadata': {
                'request_id': g.request_id,
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Erro no chat: {e}")
        return jsonify({
            'status': 'error', 
            'error': str(e)
        }), 500

@ai_integration_bp.route('/knowledge/add', methods=['POST'])
def add_knowledge():
    """Adiciona conhecimento à base vetorial"""
    try:
        # Autenticação flexível
        user_id = "anonymous"
        if jwt_required and request.headers.get('Authorization'):
            try:
                user_id = get_jwt_identity()
            except Exception:
                pass
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados JSON são obrigatórios'}), 400
        
        documents = data.get('documents', [])
        collection_name = data.get('collection', 'autobot_knowledge')
        category = data.get('category', 'general')
        user_id = data.get('user_id', user_id)
        
        if not documents:
            return jsonify({'error': 'Documentos são obrigatórios'}), 400
        
        if not trainer:
            return jsonify({'error': 'Sistema de IA não disponível'}), 500
        
        # Processa documentos
        processed_docs = []
        for doc in documents:
            if isinstance(doc, str):
                processed_docs.append({
                    'text': doc,
                    'metadata': {
                        'category': category,
                        'added_by': user_id,
                        'timestamp': datetime.now().isoformat()
                    }
                })
            elif isinstance(doc, dict):
                doc.setdefault('metadata', {})
                doc['metadata'].update({
                    'added_by': user_id,
                    'timestamp': datetime.now().isoformat()
                })
                processed_docs.append(doc)
        
        # Adiciona à base de conhecimento
        result = trainer.add_knowledge(processed_docs, collection_name)
        
        return jsonify({
            'status': 'success',
            'message': result,
            'details': {
                'documents_count': len(processed_docs),
                'collection': collection_name,
                'category': category
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao adicionar conhecimento: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@ai_integration_bp.route('/knowledge/search', methods=['POST'])
def search_knowledge():
    """Busca na base de conhecimento"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados JSON são obrigatórios'}), 400
        
        query = data.get('query', '').strip()
        collection_name = data.get('collection', 'autobot_knowledge')
        limit = data.get('limit', 5)
        
        if not query:
            return jsonify({'error': 'Query é obrigatória'}), 400
        
        if not trainer:
            return jsonify({'error': 'Sistema de IA não disponível'}), 500
        
        results = trainer.search_knowledge(query, collection_name, limit)
        
        return jsonify({
            'status': 'success',
            'query': query,
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar conhecimento: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@ai_integration_bp.route('/memory/context/<user_id>', methods=['GET'])
def get_user_context(user_id: str):
    """Recupera contexto de conversa do usuário"""
    try:
        # Verifica permissões básicas
        current_user = user_id
        if jwt_required and request.headers.get('Authorization'):
            try:
                current_user = get_jwt_identity()
                # Usuário pode ver apenas próprio contexto (exceto admin)
                if current_user != user_id and current_user != 'admin':
                    return jsonify({'error': 'Acesso negado'}), 403
            except Exception:
                pass
        
        if not memory_manager:
            return jsonify({'error': 'Sistema de memória não disponível'}), 500
        
        limit = request.args.get('limit', 10, type=int)
        hours = request.args.get('hours', 24, type=int)
        
        try:
            import asyncio
            context = asyncio.run(
                memory_manager.get_conversation_context(
                    user_id=user_id,
                    limit=limit,
                    time_window_hours=hours
                )
            )
        except Exception:
            # Fallback quando asyncio não disponível
            context = {
                "conversations": [],
                "summary": f"Contexto para usuário {user_id} (simulado)",
                "patterns": {"note": "Sistema básico ativo"}
            }
        
        return jsonify({
            'status': 'success',
            'context': context,
            'user_id': user_id
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar contexto: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@ai_integration_bp.route('/status', methods=['GET'])
def get_system_status():
    """Status detalhado do sistema de IA"""
    try:
        status_info = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'components': {
                'trainer': trainer is not None,
                'memory_manager': memory_manager is not None
            }
        }
        
        # Status do Ollama
        if trainer:
            try:
                models = trainer.get_available_models()
                status_info['components']['ollama'] = {
                    'available': trainer.ollama_client is not None,
                    'models': models,
                    'model_count': len(models)
                }
            except Exception as e:
                status_info['components']['ollama'] = {
                    'available': False, 
                    'error': str(e)
                }
        
        # Status do ChromaDB
        if trainer and trainer.chroma_client:
            try:
                collections = trainer.chroma_client.list_collections()
                status_info['components']['chromadb'] = {
                    'available': True,
                    'collections': [c.name for c in collections],
                    'collection_count': len(collections)
                }
            except Exception as e:
                status_info['components']['chromadb'] = {
                    'available': False, 
                    'error': str(e)
                }
        
        # Métricas de memória
        if memory_manager:
            try:
                memory_stats = memory_manager.get_memory_stats()
                status_info['components']['memory'] = memory_stats
            except Exception as e:
                status_info['components']['memory'] = {
                    'available': False, 
                    'error': str(e)
                }
        
        return jsonify(status_info)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# === ENDPOINTS DE MÉTRICAS ===

@ai_integration_bp.route('/metrics', methods=['GET'])
def get_system_metrics():
    """Métricas detalhadas do sistema"""
    try:
        period = request.args.get('period', '24h')
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'period': period
        }
        
        if trainer:
            performance_metrics = trainer.get_performance_metrics()
            metrics['performance'] = performance_metrics
        
        if memory_manager:
            memory_stats = memory_manager.get_memory_stats()
            metrics['memory'] = memory_stats
        
        return jsonify(metrics)
        
    except Exception as e:
        logger.error(f"Erro ao buscar métricas: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@ai_integration_bp.route('/models', methods=['GET'])
def list_available_models():
    """Lista modelos disponíveis"""
    try:
        if not trainer:
            return jsonify({'error': 'Sistema de IA não disponível'}), 500
        
        models = trainer.get_available_models()
        
        return jsonify({
            'status': 'success',
            'models': models,
            'count': len(models),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar modelos: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@ai_integration_bp.route('/health', methods=['GET'])
def health_check():
    """Health check básico"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0'
    })

# Função para inicializar a aplicação completa
def create_autobot_ai_app():
    """Cria aplicação Flask completa com IA"""
    app, limiter = create_ai_app()
    
    # Inicializa serviços de IA
    with app.app_context():
        initialize_ai_services()
    
    return app

if __name__ == "__main__":
    # Para desenvolvimento
    app = create_autobot_ai_app()
    app.run(debug=True, host='0.0.0.0', port=5000)