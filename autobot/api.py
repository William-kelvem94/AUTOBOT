"""
AUTOBOT Enhanced API Module
Flask API with improved error handling, caching, and metrics
"""
import os
import time
import logging
from typing import Dict, Any
from functools import wraps
from datetime import datetime, timedelta
import json

from flask import Flask, request, jsonify, g
from flask_cors import CORS
import requests

try:
    from autobot.gemini import gemini_ask
    from IA.treinamento.ollama_integration import perguntar_ollama
    from metrics.metrics_collector import collect_api_metrics, get_metrics_summary
    from autobot.main import listar_tarefas_pendentes, responder_tarefa, create_task, HealthChecker
except ImportError as e:
    logging.warning(f"Import warning: {e}")
    
    # Fallback functions
    def gemini_ask(prompt): return f"Gemini not available: {prompt}"
    def perguntar_ollama(prompt): return f"Ollama not available: {prompt}"
    def collect_api_metrics(*args): pass
    def get_metrics_summary(): return {}
    def listar_tarefas_pendentes(): return []
    def responder_tarefa(task_id, msg): return True
    def create_task(title, desc=""): return {"success": True}
    
    class HealthChecker:
        @staticmethod
        def check_dependencies(): return {}
        @staticmethod
        def get_system_info(): return {}

app = Flask(__name__)
CORS(app, 
     origins=["http://localhost:3000", "http://localhost:5000"],
     methods=["GET", "POST", "PUT", "DELETE"],
     allow_headers=["Content-Type", "Authorization"])

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple in-memory cache for performance
cache = {}
CACHE_TIMEOUT = 300  # 5 minutes

def cache_response(timeout=CACHE_TIMEOUT):
    """Simple caching decorator"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            cache_key = f"{f.__name__}:{hash(str(args) + str(kwargs))}"
            
            if cache_key in cache:
                data, timestamp = cache[cache_key]
                if time.time() - timestamp < timeout:
                    logger.info(f"Cache hit for {f.__name__}")
                    return data
            
            result = f(*args, **kwargs)
            cache[cache_key] = (result, time.time())
            logger.info(f"Cache miss for {f.__name__} - cached result")
            return result
        return wrapper
    return decorator

def track_performance(f):
    """Decorator to track API performance"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        g.start_time = start_time
        
        try:
            result = f(*args, **kwargs)
            duration = time.time() - start_time
            collect_api_metrics(f.__name__, duration, True, 200)
            return result
        except Exception as e:
            duration = time.time() - start_time
            collect_api_metrics(f.__name__, duration, False, 500)
            logger.error(f"API error in {f.__name__}: {e}")
            raise
    return wrapper

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        'error': 'Bad Request',
        'message': 'Invalid request parameters',
        'timestamp': datetime.now().isoformat()
    }), 400

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred',
        'timestamp': datetime.now().isoformat()
    }), 500

@app.before_request
def before_request():
    """Log request details"""
    logger.info(f"API Request: {request.method} {request.path} from {request.remote_addr}")

@app.after_request
def after_request(response):
    """Log response details and add headers"""
    duration = time.time() - getattr(g, 'start_time', time.time())
    logger.info(f"API Response: {response.status_code} in {duration:.3f}s")
    
    # Add security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    return response

@app.route('/api/health', methods=['GET'])
@track_performance
def health_check():
    """Enhanced health check endpoint"""
    try:
        dependencies = HealthChecker.check_dependencies()
        system_info = HealthChecker.get_system_info()
        
        overall_health = all(dependencies.values()) if dependencies else False
        
        return jsonify({
            'status': 'healthy' if overall_health else 'degraded',
            'timestamp': datetime.now().isoformat(),
            'dependencies': dependencies,
            'system': system_info,
            'version': '2.0.0',
            'cache_size': len(cache)
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/chat', methods=['POST'])
@track_performance
def chat():
    """Enhanced chat endpoint with fallback AI providers"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        prompt = data.get('prompt', '').strip()
        ai_provider = data.get('ai', 'gemini').lower()
        
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
        
        if len(prompt) > 4000:  # Limit prompt size
            return jsonify({'error': 'Prompt too long (max 4000 characters)'}), 400
        
        logger.info(f"Chat request: provider={ai_provider}, prompt_length={len(prompt)}")
        
        start_time = time.time()
        
        try:
            if ai_provider == 'ollama':
                resposta = perguntar_ollama(prompt)
            elif ai_provider == 'gemini':
                resposta = gemini_ask(prompt)
            else:
                # Fallback to available provider
                try:
                    resposta = gemini_ask(prompt)
                except:
                    resposta = perguntar_ollama(prompt)
        except Exception as e:
            logger.error(f"AI provider error: {e}")
            resposta = f"Desculpe, houve um erro ao processar sua solicitação: {str(e)}"
        
        duration = time.time() - start_time
        
        return jsonify({
            'resposta': resposta,
            'provider': ai_provider,
            'processing_time': round(duration, 3),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        return jsonify({
            'error': 'Failed to process chat request',
            'message': str(e)
        }), 500

@app.route('/api/tasks', methods=['GET'])
@track_performance
@cache_response(timeout=60)  # Cache for 1 minute
def get_tasks():
    """Get tasks with caching and pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        
        if limit > 50:  # Limit to prevent abuse
            limit = 50
        
        tasks = listar_tarefas_pendentes()
        
        # Simple pagination
        start = (page - 1) * limit
        end = start + limit
        paginated_tasks = tasks[start:end]
        
        return jsonify({
            'tasks': paginated_tasks,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': len(tasks),
                'pages': (len(tasks) + limit - 1) // limit
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Tasks endpoint error: {e}")
        return jsonify({
            'error': 'Failed to fetch tasks',
            'message': str(e)
        }), 500

@app.route('/api/tasks/<task_id>/respond', methods=['POST'])
@track_performance
def respond_to_task(task_id):
    """Respond to a specific task"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        message = data.get('message', '').strip()
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        if len(message) > 2000:  # Limit message size
            return jsonify({'error': 'Message too long (max 2000 characters)'}), 400
        
        success = responder_tarefa(task_id, message)
        
        return jsonify({
            'success': success,
            'task_id': task_id,
            'message': 'Response sent successfully',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Task response error: {e}")
        return jsonify({
            'error': 'Failed to respond to task',
            'message': str(e)
        }), 500

@app.route('/api/tasks', methods=['POST'])
@track_performance
def create_new_task():
    """Create a new task"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        responsible_id = data.get('responsible_id')
        
        if not title:
            return jsonify({'error': 'Title is required'}), 400
        
        result = create_task(title, description, responsible_id)
        
        return jsonify({
            'success': result.get('success', False),
            'task_id': result.get('task_id'),
            'message': result.get('message', 'Task created'),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Task creation error: {e}")
        return jsonify({
            'error': 'Failed to create task',
            'message': str(e)
        }), 500

@app.route('/api/train', methods=['POST'])
@track_performance
def train_model():
    """Enhanced training endpoint with better error handling"""
    try:
        data = request.get_json()
        exemplos = data.get('exemplos', '') if data else ''
        
        # Save training examples if provided
        if exemplos.strip():
            dataset_path = 'IA/treinamento/meu_dataset.jsonl'
            os.makedirs(os.path.dirname(dataset_path), exist_ok=True)
            
            with open(dataset_path, 'a', encoding='utf-8') as f:
                for linha in exemplos.strip().split('\n'):
                    if '|' in linha:
                        pergunta, resposta = linha.split('|', 1)
                        f.write(json.dumps({
                            "prompt": pergunta.strip(), 
                            "resposta": resposta.strip(),
                            "timestamp": datetime.now().isoformat()
                        }) + "\n")
        
        # Execute training (in background for better UX)
        import subprocess
        
        try:
            result = subprocess.run(
                ["python", "IA/treinamento/finetune_llm.py"],
                capture_output=True, 
                text=True, 
                timeout=300  # 5 minute timeout
            )
            
            return jsonify({
                "status": "success" if result.returncode == 0 else "error",
                "output": result.stdout if result.returncode == 0 else result.stderr,
                "return_code": result.returncode,
                "timestamp": datetime.now().isoformat()
            })
            
        except subprocess.TimeoutExpired:
            return jsonify({
                "status": "timeout",
                "message": "Training process timed out",
                "timestamp": datetime.now().isoformat()
            }), 408
            
    except Exception as e:
        logger.error(f"Training error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/metrics', methods=['GET'])
@track_performance
def get_metrics():
    """Get system metrics and performance data"""
    try:
        metrics = get_metrics_summary()
        
        return jsonify({
            'metrics': metrics,
            'cache_stats': {
                'size': len(cache),
                'keys': list(cache.keys())[:10]  # First 10 cache keys
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        return jsonify({
            'error': 'Failed to fetch metrics',
            'message': str(e)
        }), 500

@app.route('/api/cache/clear', methods=['POST'])
@track_performance
def clear_cache():
    """Clear the application cache"""
    try:
        cache_size = len(cache)
        cache.clear()
        
        return jsonify({
            'message': f'Cache cleared. Removed {cache_size} entries.',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Cache clear error: {e}")
        return jsonify({
            'error': 'Failed to clear cache',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
    
    logger.info(f"Starting AUTOBOT API on port {port} (debug={'on' if debug else 'off'})")
    
    app.run(
        host='0.0.0.0', 
        port=port, 
        debug=debug,
        threaded=True
    )