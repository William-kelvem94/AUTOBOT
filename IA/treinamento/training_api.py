"""
API endpoints para treinamento de IA local do AUTOBOT
Integra com Flask para fornecer endpoints REST para o sistema de IA
"""

from flask import Blueprint, request, jsonify, current_app
import logging
import json
from typing import Dict, Any
import asyncio
from functools import wraps

# Imports dos módulos locais
try:
    from .local_trainer import AutobotLocalTrainer
    from .memory_manager import AutobotMemoryManager
except ImportError:
    # Fallback para execução standalone
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from local_trainer import AutobotLocalTrainer
    from memory_manager import AutobotMemoryManager

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Blueprint para endpoints de treinamento
training_bp = Blueprint('training', __name__, url_prefix='/api/ia')

# Instâncias globais (inicializadas no primeiro uso)
trainer = None
memory = None

def get_trainer():
    """Obtém instância do trainer (lazy loading)"""
    global trainer
    if trainer is None:
        try:
            trainer = AutobotLocalTrainer()
            logger.info("✅ AutobotLocalTrainer inicializado")
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar trainer: {e}")
            raise
    return trainer

def get_memory():
    """Obtém instância do memory manager (lazy loading)"""
    global memory
    if memory is None:
        try:
            memory = AutobotMemoryManager()
            logger.info("✅ AutobotMemoryManager inicializado")
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar memory: {e}")
            raise
    return memory

def handle_errors(f):
    """Decorator para tratamento de erros nas rotas"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"❌ Erro na rota {f.__name__}: {e}")
            return jsonify({
                "status": "error",
                "erro": str(e),
                "message": "Erro interno do servidor"
            }), 500
    return decorated_function

@training_bp.route('/status', methods=['GET'])
@handle_errors
def status_sistema():
    """Verifica status do sistema de IA"""
    try:
        trainer_instance = get_trainer()
        memory_instance = get_memory()
        
        # Verifica modelos disponíveis
        modelos = trainer_instance.list_available_models()
        
        # Estatísticas de memória
        stats = memory_instance.estatisticas_memoria()
        
        return jsonify({
            "status": "success",
            "sistema_ia": "operacional",
            "modelos_disponiveis": modelos,
            "estatisticas_memoria": stats.get("estatisticas", {}),
            "message": "Sistema de IA funcionando corretamente"
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "sistema_ia": "com_problemas",
            "erro": str(e),
            "message": "Problemas no sistema de IA"
        }), 500

@training_bp.route('/setup', methods=['POST'])
@handle_errors
def setup_ia_local():
    """Configura sistema de IA local completo"""
    logger.info("🚀 Iniciando configuração do sistema de IA local...")
    
    try:
        trainer_instance = get_trainer()
        
        # Configura modelos Ollama
        status_modelos = trainer_instance.setup_ollama_models()
        
        # Verifica se pelo menos um modelo foi instalado
        modelos_ok = any("✅" in status for status in status_modelos.values())
        
        if modelos_ok:
            logger.info("✅ Configuração do sistema de IA concluída")
            return jsonify({
                "status": "success",
                "message": "Sistema de IA local configurado com sucesso",
                "modelos_status": status_modelos
            })
        else:
            logger.warning("⚠️ Nenhum modelo foi instalado corretamente")
            return jsonify({
                "status": "warning",
                "message": "Sistema configurado, mas alguns modelos falharam",
                "modelos_status": status_modelos
            }), 206  # Partial Content
            
    except Exception as e:
        logger.error(f"❌ Erro na configuração: {e}")
        return jsonify({
            "status": "error",
            "erro": str(e),
            "message": "Falha na configuração do sistema de IA"
        }), 500

@training_bp.route('/treinar-personalizado', methods=['POST'])
@handle_errors
def treinar_modelo_personalizado():
    """Treina modelo personalizado com dados específicos do usuário"""
    data = request.get_json()
    
    if not data:
        return jsonify({
            "status": "error",
            "erro": "Dados JSON não fornecidos"
        }), 400
    
    exemplos = data.get('exemplos', '')
    nome_modelo = data.get('nome_modelo', 'autobot-personalizado')
    
    if not exemplos:
        return jsonify({
            "status": "error",
            "erro": "Exemplos de treinamento não fornecidos"
        }), 400
    
    logger.info(f"🧠 Iniciando treinamento do modelo: {nome_modelo}")
    
    try:
        trainer_instance = get_trainer()
        resultado = trainer_instance.train_custom_model(exemplos, nome_modelo)
        
        if resultado["status"] == "success":
            logger.info(f"✅ Modelo {nome_modelo} treinado com sucesso")
        else:
            logger.error(f"❌ Falha no treinamento: {resultado.get('erro', 'Erro desconhecido')}")
        
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"❌ Erro no treinamento: {e}")
        return jsonify({
            "status": "error",
            "erro": str(e),
            "message": "Falha no treinamento do modelo"
        }), 500

@training_bp.route('/testar-modelo', methods=['POST'])
@handle_errors
def testar_modelo():
    """Testa um modelo treinado com pergunta de exemplo"""
    data = request.get_json()
    
    modelo = data.get('modelo', 'autobot-personalizado')
    pergunta = data.get('pergunta', 'Como posso automatizar uma tarefa?')
    
    logger.info(f"🧪 Testando modelo: {modelo}")
    
    try:
        trainer_instance = get_trainer()
        resultado = trainer_instance.test_model(modelo, pergunta)
        
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"❌ Erro no teste: {e}")
        return jsonify({
            "status": "error",
            "erro": str(e),
            "message": "Falha no teste do modelo"
        }), 500

@training_bp.route('/modelos', methods=['GET'])
@handle_errors
def listar_modelos():
    """Lista todos os modelos disponíveis"""
    try:
        trainer_instance = get_trainer()
        modelos = trainer_instance.list_available_models()
        
        # Informações detalhadas dos modelos
        modelos_info = []
        for modelo in modelos:
            info = trainer_instance.get_model_info(modelo)
            modelos_info.append({
                "nome": modelo,
                "info": info.get("info", {}),
                "disponivel": info["status"] == "success"
            })
        
        return jsonify({
            "status": "success",
            "modelos": modelos,
            "detalhes": modelos_info,
            "total": len(modelos)
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar modelos: {e}")
        return jsonify({
            "status": "error",
            "erro": str(e),
            "message": "Falha ao listar modelos"
        }), 500

@training_bp.route('/memoria/salvar', methods=['POST'])
@handle_errors
def salvar_conversa():
    """Salva conversa na memória persistente"""
    data = request.get_json()
    
    # Validação dos dados obrigatórios
    required_fields = ['usuario', 'pergunta', 'resposta']
    for field in required_fields:
        if not data.get(field):
            return jsonify({
                "status": "error",
                "erro": f"Campo obrigatório não fornecido: {field}"
            }), 400
    
    try:
        memory_instance = get_memory()
        
        resultado = memory_instance.salvar_conversa(
            usuario=data['usuario'],
            pergunta=data['pergunta'], 
            resposta=data['resposta'],
            contexto=data.get('contexto'),
            categoria=data.get('categoria', 'geral')
        )
        
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"❌ Erro ao salvar conversa: {e}")
        return jsonify({
            "status": "error",
            "erro": str(e),
            "message": "Falha ao salvar conversa"
        }), 500

@training_bp.route('/memoria/buscar', methods=['POST'])
@handle_errors
def buscar_contexto():
    """Busca contexto relevante na memória"""
    data = request.get_json()
    
    pergunta = data.get('pergunta')
    if not pergunta:
        return jsonify({
            "status": "error",
            "erro": "Pergunta não fornecida"
        }), 400
    
    try:
        memory_instance = get_memory()
        
        contexto = memory_instance.buscar_contexto(
            pergunta=pergunta,
            usuario=data.get('usuario'),
            limite=data.get('limite', 5),
            categoria=data.get('categoria')
        )
        
        return jsonify({
            "status": "success",
            "contexto": contexto
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar contexto: {e}")
        return jsonify({
            "status": "error",
            "erro": str(e),
            "message": "Falha ao buscar contexto"
        }), 500

@training_bp.route('/memoria/conhecimento', methods=['POST'])
@handle_errors
def salvar_conhecimento():
    """Salva conhecimento especializado"""
    data = request.get_json()
    
    topico = data.get('topico')
    conteudo = data.get('conteudo')
    
    if not topico or not conteudo:
        return jsonify({
            "status": "error",
            "erro": "Tópico e conteúdo são obrigatórios"
        }), 400
    
    try:
        memory_instance = get_memory()
        
        resultado = memory_instance.salvar_conhecimento_especializado(
            topico=topico,
            conteudo=conteudo,
            fonte=data.get('fonte', 'api'),
            tags=data.get('tags', [])
        )
        
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"❌ Erro ao salvar conhecimento: {e}")
        return jsonify({
            "status": "error",
            "erro": str(e),
            "message": "Falha ao salvar conhecimento"
        }), 500

@training_bp.route('/memoria/conhecimento/buscar', methods=['POST'])
@handle_errors
def buscar_conhecimento():
    """Busca conhecimento especializado"""
    data = request.get_json()
    
    consulta = data.get('consulta')
    if not consulta:
        return jsonify({
            "status": "error",
            "erro": "Consulta não fornecida"
        }), 400
    
    try:
        memory_instance = get_memory()
        
        resultado = memory_instance.buscar_conhecimento(
            consulta=consulta,
            limite=data.get('limite', 3)
        )
        
        return jsonify({
            "status": "success",
            "resultado": resultado
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar conhecimento: {e}")
        return jsonify({
            "status": "error",
            "erro": str(e),
            "message": "Falha ao buscar conhecimento"
        }), 500

@training_bp.route('/memoria/estatisticas', methods=['GET'])
@handle_errors
def estatisticas_memoria():
    """Retorna estatísticas da memória do sistema"""
    try:
        memory_instance = get_memory()
        stats = memory_instance.estatisticas_memoria()
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter estatísticas: {e}")
        return jsonify({
            "status": "error",
            "erro": str(e),
            "message": "Falha ao obter estatísticas"
        }), 500

@training_bp.route('/memoria/limpar', methods=['POST'])
@handle_errors
def limpar_memoria_antiga():
    """Remove conversas antigas da memória"""
    data = request.get_json() or {}
    dias = data.get('dias', 30)
    
    try:
        memory_instance = get_memory()
        resultado = memory_instance.limpar_memoria_antiga(dias)
        
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"❌ Erro na limpeza: {e}")
        return jsonify({
            "status": "error",
            "erro": str(e),
            "message": "Falha na limpeza da memória"
        }), 500

@training_bp.route('/base-conhecimento', methods=['POST'])
@handle_errors
def criar_base_conhecimento():
    """Cria base de conhecimento vetorial com dados de treinamento"""
    data = request.get_json()
    
    training_data = data.get('training_data', [])
    if not training_data:
        return jsonify({
            "status": "error",
            "erro": "Dados de treinamento não fornecidos"
        }), 400
    
    try:
        trainer_instance = get_trainer()
        resultado = trainer_instance.create_knowledge_base(training_data)
        
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar base de conhecimento: {e}")
        return jsonify({
            "status": "error",
            "erro": str(e),
            "message": "Falha ao criar base de conhecimento"
        }), 500

# Função para registrar o blueprint em uma app Flask
def register_training_api(app):
    """
    Registra os endpoints de treinamento em uma aplicação Flask
    
    Args:
        app: Instância da aplicação Flask
    """
    app.register_blueprint(training_bp)
    logger.info("✅ Endpoints de treinamento de IA registrados")

# Teste standalone da API
def test_api_endpoints():
    """Testa os endpoints da API (para desenvolvimento)"""
    from flask import Flask
    
    app = Flask(__name__)
    register_training_api(app)
    
    with app.test_client() as client:
        # Teste status
        response = client.get('/api/ia/status')
        print(f"Status: {response.status_code} - {response.get_json()}")
        
        # Teste listar modelos
        response = client.get('/api/ia/modelos')
        print(f"Modelos: {response.status_code} - {response.get_json()}")
        
    print("✅ Teste dos endpoints concluído")

if __name__ == "__main__":
    print("🌐 AUTOBOT - API de Treinamento de IA")
    print("=" * 40)
    
    test_api_endpoints()