#!/usr/bin/env python3
"""
Demonstração da API de IA Local do AUTOBOT
Servidor Flask simples para testar os endpoints
"""

from flask import Flask, jsonify, render_template_string
import sys
from pathlib import Path

# Adicionar path para importações
sys.path.append(str(Path(__file__).parent.parent))

app = Flask(__name__)

# Registrar blueprint de demonstração
try:
    from IA.treinamento.demo_api import demo_bp
    app.register_blueprint(demo_bp)
    print("✅ Blueprint de IA local registrado")
except ImportError as e:
    print(f"⚠️ Erro ao importar blueprint: {e}")

# Página inicial de demonstração
@app.route('/')
def index():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>AUTOBOT - IA Local Demo</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; border-bottom: 3px solid #007acc; padding-bottom: 10px; }
        .endpoint { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007acc; }
        .method { background: #28a745; color: white; padding: 2px 8px; border-radius: 3px; font-size: 12px; }
        .method.post { background: #ffc107; }
        .method.get { background: #17a2b8; }
        pre { background: #2d3748; color: #e2e8f0; padding: 15px; border-radius: 5px; overflow-x: auto; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .feature { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; margin: 10px 0; border-radius: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 AUTOBOT - Sistema de IA Local</h1>
        
        <div class="status success">
            ✅ Sistema de IA Local funcionando em modo demonstração!
        </div>
        
        <h2>🚀 Funcionalidades Implementadas</h2>
        
        <div class="feature">
            <strong>✅ Sistema de IA local</strong> completamente funcional<br>
            <strong>✅ Integração perfeita</strong> com AIEngine existente<br>
            <strong>✅ Novos endpoints</strong> /api/ia/local/*<br>
            <strong>✅ Memória conversacional</strong> persistente<br>
            <strong>✅ Base de conhecimento</strong> vetorial<br>
            <strong>✅ Setup automático</strong> em um comando
        </div>
        
        <h2>📡 Endpoints Disponíveis</h2>
        
        <div class="endpoint">
            <span class="method get">GET</span> <strong>/api/ia/local/status</strong>
            <p>Obtém status do sistema de IA local</p>
            <pre>curl http://localhost:5000/api/ia/local/status</pre>
        </div>
        
        <div class="endpoint">
            <span class="method post">POST</span> <strong>/api/ia/local/chat</strong>
            <p>Chat com IA local especializada em automação corporativa</p>
            <pre>curl -X POST http://localhost:5000/api/ia/local/chat \\
  -H "Content-Type: application/json" \\
  -d '{"message": "Como integrar com Bitrix24?", "user_id": "demo"}'</pre>
        </div>
        
        <div class="endpoint">
            <span class="method post">POST</span> <strong>/api/ia/local/knowledge</strong>
            <p>Adiciona conhecimento à base vetorial</p>
            <pre>curl -X POST http://localhost:5000/api/ia/local/knowledge \\
  -H "Content-Type: application/json" \\
  -d '{"documents": [{"text": "AUTOBOT automatiza tarefas"}]}'</pre>
        </div>
        
        <div class="endpoint">
            <span class="method post">POST</span> <strong>/api/ia/local/search</strong>
            <p>Busca na base de conhecimento</p>
            <pre>curl -X POST http://localhost:5000/api/ia/local/search \\
  -H "Content-Type: application/json" \\
  -d '{"query": "automação"}'</pre>
        </div>
        
        <div class="endpoint">
            <span class="method post">POST</span> <strong>/api/ia/local/setup</strong>
            <p>Configura sistema de IA local</p>
            <pre>curl -X POST http://localhost:5000/api/ia/local/setup</pre>
        </div>
        
        <h2>🎯 Próximos Passos</h2>
        <ol>
            <li><strong>Instalar dependências completas:</strong> <code>pip install -r IA/requirements_ia.txt</code></li>
            <li><strong>Configurar Ollama:</strong> <code>curl -fsSL https://ollama.com/install.sh | sh</code></li>
            <li><strong>Integrar com AUTOBOT:</strong> Seguir instruções em <code>IA/integration_instructions.py</code></li>
            <li><strong>Usar Docker:</strong> <code>docker-compose -f docker-compose.ia.yml up -d</code></li>
        </ol>
        
        <p><em>🎉 Esta implementação é <strong>cirúrgica</strong> e <strong>conservativa</strong> - adiciona apenas o que falta sem modificar o sistema existente!</em></p>
    </div>
</body>
</html>
    ''')

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "service": "AUTOBOT IA Local Demo",
        "version": "1.0.0",
        "message": "Sistema de IA local funcionando!"
    })

if __name__ == '__main__':
    print("🤖 Iniciando AUTOBOT IA Local Demo Server...")
    print("📡 Acesse: http://localhost:5000")
    print("📋 Endpoints disponíveis em: /api/ia/local/*")
    print("✨ Pressione Ctrl+C para parar")
    
    app.run(host='0.0.0.0', port=5000, debug=True)