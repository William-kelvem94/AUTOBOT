#!/usr/bin/env python3
"""
AUTOBOT - Aplicação Principal
Sistema completo de IA local para automação corporativa
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import logging
import os
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Cria e configura a aplicação Flask"""
    
    app = Flask(__name__)
    
    # Configuração
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'autobot-secret-key-2024')
    app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # CORS para desenvolvimento
    CORS(app, origins="*")
    
    # Registro dos blueprints de IA
    try:
        from IA.treinamento import register_training_api
        register_training_api(app)
        logger.info("✅ Endpoints de treinamento de IA registrados")
    except Exception as e:
        logger.error(f"❌ Erro ao registrar endpoints de IA: {e}")
    
    # Rotas principais
    @app.route('/')
    def index():
        """Página inicial do AUTOBOT"""
        return jsonify({
            "message": "🧠 AUTOBOT - Sistema de IA Local",
            "version": "1.0.0",
            "status": "operacional",
            "endpoints": {
                "status": "/api/ia/status",
                "setup": "/api/ia/setup",
                "treinar": "/api/ia/treinar-personalizado",
                "testar": "/api/ia/testar-modelo",
                "modelos": "/api/ia/modelos",
                "memoria": "/api/ia/memoria/*"
            },
            "docs": "https://github.com/William-kelvem94/AUTOBOT"
        })
    
    @app.route('/health')
    def health_check():
        """Health check para monitoramento"""
        try:
            from autobot.ai import get_ai_engine
            import asyncio
            
            engine = get_ai_engine()
            health = asyncio.run(engine.health_check())
            
            return jsonify(health), 200 if health["status"] == "healthy" else 503
            
        except Exception as e:
            return jsonify({
                "status": "unhealthy",
                "error": str(e)
            }), 503
    
    @app.route('/dashboard')
    def dashboard():
        """Dashboard básico do sistema"""
        try:
            from autobot.ai import get_system_status
            
            status = get_system_status()
            
            return jsonify({
                "title": "AUTOBOT Dashboard",
                "sistema": status,
                "componentes": [
                    {"nome": "Ollama", "status": "online", "porta": 11434},
                    {"nome": "ChromaDB", "status": "online", "porta": 8000},
                    {"nome": "AI Engine", "status": "online", "porta": None}
                ]
            })
            
        except Exception as e:
            logger.error(f"Erro no dashboard: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/chat', methods=['POST'])
    def chat_endpoint():
        """Endpoint para conversação com IA"""
        try:
            data = request.get_json()
            
            if not data or 'message' not in data:
                return jsonify({"error": "Mensagem não fornecida"}), 400
            
            from autobot.ai import process_user_message
            import asyncio
            
            result = asyncio.run(process_user_message(
                message=data['message'],
                user_id=data.get('user_id', 'default'),
                context=data.get('context')
            ))
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Erro no chat: {e}")
            return jsonify({
                "status": "error",
                "error": str(e),
                "resposta": "Desculpe, ocorreu um erro no processamento."
            }), 500
    
    @app.errorhandler(404)
    def not_found(error):
        """Handler para 404"""
        return jsonify({
            "error": "Endpoint não encontrado",
            "message": "Verifique a documentação da API"
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handler para erros internos"""
        logger.error(f"Erro interno: {error}")
        return jsonify({
            "error": "Erro interno do servidor",
            "message": "Verifique os logs para mais detalhes"
        }), 500
    
    return app

def main():
    """Função principal"""
    print("🧠 AUTOBOT - Sistema de IA Local")
    print("=" * 50)
    print("🚀 Inicializando aplicação...")
    
    # Verifica se os diretórios necessários existem
    required_dirs = [
        "IA/memoria_vetorial",
        "IA/memoria_conversas",
        "IA/config"
    ]
    
    for dir_path in required_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    # Cria arquivo de configuração se não existir
    config_file = Path("IA/config/config.json")
    if not config_file.exists():
        import json
        default_config = {
            "ollama_host": "http://localhost:11434",
            "default_model": "llama3",
            "fallback_model": "tinyllama",
            "custom_model": "autobot-personalizado",
            "max_tokens": 2048,
            "temperature": 0.7,
            "use_local_ai": True,
            "memory_enabled": True,
            "context_window": 5
        }
        
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        logger.info("✅ Arquivo de configuração criado")
    
    # Cria a aplicação
    app = create_app()
    
    # Configurações de execução
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"🌐 Servidor iniciando em http://{host}:{port}")
    print("📋 Endpoints disponíveis:")
    print("   GET  /                    - Informações da API")
    print("   GET  /health             - Health check")
    print("   GET  /dashboard          - Dashboard do sistema")
    print("   POST /api/chat           - Conversar com IA")
    print("   GET  /api/ia/status      - Status do sistema de IA")
    print("   POST /api/ia/setup       - Configurar sistema")
    print("   POST /api/ia/treinar-*   - Endpoints de treinamento")
    print("=" * 50)
    
    try:
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n👋 AUTOBOT encerrado pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar aplicação: {e}")
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    main()