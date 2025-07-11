#!/usr/bin/env python3
"""
AUTOBOT - Sistema de IA Corporativa
Servidor principal com health checks avançados
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sys
import sqlite3
import psutil
import time
import requests
from datetime import datetime
from pathlib import Path

# Adiciona o diretório atual ao path para imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
CORS(app)

# Configuração
app.config['DEBUG'] = os.getenv('DEBUG', 'True').lower() == 'true'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'autobot-secret-key')

def get_database_connection():
    """Conecta ao banco de métricas"""
    db_path = Path("metrics/autobot_metrics.db")
    if not db_path.exists():
        return None
    return sqlite3.connect(str(db_path))

def log_api_metric(endpoint, response_time, status_code):
    """Registra métrica de API"""
    try:
        conn = get_database_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO api_metrics (endpoint, response_time, status_code)
                VALUES (?, ?, ?)
            ''', (endpoint, response_time, status_code))
            conn.commit()
            conn.close()
    except Exception as e:
        print(f"Erro ao registrar métrica: {e}")

def log_system_metrics():
    """Registra métricas do sistema"""
    try:
        conn = get_database_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO system_metrics (cpu_usage, memory_usage, disk_usage)
                VALUES (?, ?, ?)
            ''', (
                psutil.cpu_percent(),
                psutil.virtual_memory().percent,
                psutil.disk_usage('/').percent
            ))
            conn.commit()
            conn.close()
    except Exception as e:
        print(f"Erro ao registrar métricas do sistema: {e}")

def advanced_health_check():
    """Verifica integridade completa do sistema"""
    checks = {
        "timestamp": datetime.now().isoformat(),
        "status": "healthy",
        "components": {}
    }
    
    # Verifica Flask
    try:
        checks["components"]["flask"] = {
            "status": "healthy",
            "version": "3.0.0",
            "debug_mode": app.config['DEBUG']
        }
    except Exception as e:
        checks["components"]["flask"] = {"status": "unhealthy", "error": str(e)}
    
    # Verifica banco de dados
    try:
        conn = get_database_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM api_metrics")
            metrics_count = cursor.fetchone()[0]
            conn.close()
            checks["components"]["database"] = {
                "status": "healthy",
                "metrics_count": metrics_count,
                "path": "metrics/autobot_metrics.db"
            }
        else:
            checks["components"]["database"] = {
                "status": "warning",
                "message": "Database not found, will be created on first use"
            }
    except Exception as e:
        checks["components"]["database"] = {"status": "unhealthy", "error": str(e)}
    
    # Verifica dependências Python
    dependencies_status = {}
    required_modules = ['requests', 'pandas', 'numpy', 'psutil']
    
    for module in required_modules:
        try:
            __import__(module)
            dependencies_status[module] = "installed"
        except ImportError:
            dependencies_status[module] = "missing"
    
    checks["components"]["dependencies"] = dependencies_status
    
    # Verifica sistema
    try:
        system_info = {
            "cpu_usage": psutil.cpu_percent(interval=1),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "python_version": sys.version.split()[0]
        }
        checks["components"]["system"] = {
            "status": "healthy",
            "info": system_info
        }
    except Exception as e:
        checks["components"]["system"] = {"status": "unhealthy", "error": str(e)}
    
    # Verifica IA (Ollama)
    try:
        ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        if response.status_code == 200:
            checks["components"]["ai"] = {
                "status": "healthy",
                "ollama_url": ollama_url,
                "models": response.json().get('models', [])
            }
        else:
            checks["components"]["ai"] = {
                "status": "warning",
                "message": "Ollama not responding properly"
            }
    except Exception as e:
        checks["components"]["ai"] = {
            "status": "offline",
            "message": "Ollama not available",
            "error": str(e)
        }
    
    # Determina status geral
    unhealthy_components = [
        name for name, comp in checks["components"].items()
        if isinstance(comp, dict) and comp.get("status") == "unhealthy"
    ]
    
    if unhealthy_components:
        checks["status"] = "unhealthy"
        checks["issues"] = unhealthy_components
    elif any(comp.get("status") == "warning" for comp in checks["components"].values() if isinstance(comp, dict)):
        checks["status"] = "warning"
    
    return checks

@app.before_request
def before_request():
    """Middleware para logging de requests"""
    request.start_time = time.time()

@app.after_request
def after_request(response):
    """Middleware para logging de responses"""
    if hasattr(request, 'start_time'):
        response_time = time.time() - request.start_time
        log_api_metric(request.endpoint or request.path, response_time, response.status_code)
    return response

# Rotas da API

@app.route('/')
def index():
    """Página inicial"""
    return jsonify({
        "message": "🤖 AUTOBOT - Sistema de IA Corporativa",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "/api/health",
            "/api/health/detailed",
            "/api/metrics",
            "/api/system/info"
        ]
    })

@app.route('/api/health')
def health():
    """Health check simples"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "autobot"
    })

@app.route('/api/health/detailed')
def detailed_health():
    """Health check detalhado"""
    return jsonify(advanced_health_check())

@app.route('/api/metrics')
def get_metrics():
    """Obtém métricas do sistema"""
    try:
        conn = get_database_connection()
        if not conn:
            return jsonify({"error": "Database not available"}), 503
        
        cursor = conn.cursor()
        
        # Métricas de API (últimas 24h)
        cursor.execute('''
            SELECT endpoint, AVG(response_time), COUNT(*), AVG(status_code)
            FROM api_metrics 
            WHERE timestamp > datetime('now', '-1 day')
            GROUP BY endpoint
        ''')
        api_metrics = cursor.fetchall()
        
        # Métricas do sistema (última hora)
        cursor.execute('''
            SELECT timestamp, cpu_usage, memory_usage, disk_usage
            FROM system_metrics 
            WHERE timestamp > datetime('now', '-1 hour')
            ORDER BY timestamp DESC
            LIMIT 60
        ''')
        system_metrics = cursor.fetchall()
        
        conn.close()
        
        # Log métricas atuais do sistema
        log_system_metrics()
        
        return jsonify({
            "api_metrics": [
                {
                    "endpoint": row[0],
                    "avg_response_time": row[1],
                    "request_count": row[2],
                    "avg_status_code": row[3]
                }
                for row in api_metrics
            ],
            "system_metrics": [
                {
                    "timestamp": row[0],
                    "cpu_usage": row[1],
                    "memory_usage": row[2],
                    "disk_usage": row[3]
                }
                for row in system_metrics
            ],
            "current_system": {
                "cpu_usage": psutil.cpu_percent(),
                "memory_usage": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/system/info')
def system_info():
    """Informações do sistema"""
    try:
        return jsonify({
            "python_version": sys.version,
            "platform": sys.platform,
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "disk_total": psutil.disk_usage('/').total,
            "uptime": time.time() - psutil.boot_time(),
            "autobot_version": "1.0.0"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Rotas de IA (placeholder)
@app.route('/api/ai/status')
def ai_status():
    """Status do sistema de IA"""
    try:
        ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        
        if response.status_code == 200:
            return jsonify({
                "status": "online",
                "ollama_url": ollama_url,
                "models": response.json().get('models', [])
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Ollama not responding"
            }), 503
            
    except requests.exceptions.RequestException:
        return jsonify({
            "status": "offline",
            "message": "Ollama not available"
        }), 503

# Rotas de automação (placeholder)
@app.route('/api/tasks')
def list_tasks():
    """Lista tarefas disponíveis"""
    return jsonify({
        "tasks": [
            {"id": 1, "name": "Web Scraping", "status": "ready"},
            {"id": 2, "name": "Data Processing", "status": "ready"},
            {"id": 3, "name": "API Integration", "status": "ready"}
        ]
    })

@app.route('/api/tasks/<int:task_id>/execute', methods=['POST'])
def execute_task(task_id):
    """Executa uma tarefa"""
    # Placeholder para execução de tarefas
    return jsonify({
        "task_id": task_id,
        "status": "executed",
        "message": f"Task {task_id} executed successfully"
    })

if __name__ == '__main__':
    print("🤖 Iniciando AUTOBOT...")
    print("=" * 40)
    
    # Verifica se o setup foi executado
    if not Path("metrics").exists():
        print("⚠️ Diretório de métricas não encontrado")
        print("Execute: python setup_automatico.py")
        sys.exit(1)
    
    port = int(os.getenv('API_PORT', 5000))
    
    print(f"🚀 AUTOBOT rodando em http://localhost:{port}")
    print("📊 Health check: http://localhost:{port}/api/health/detailed")
    print("📈 Métricas: http://localhost:{port}/api/metrics")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=app.config['DEBUG']
    )