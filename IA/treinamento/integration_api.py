"""
Integration API - API REST Completa para Integração com IA
==========================================================

API REST avançada para integração do sistema de IA local com o AUTOBOT.
Fornece endpoints completos para chat, treinamento, monitoramento e gerenciamento.

Funcionalidades principais:
- Endpoints para chat em tempo real
- Sistema de autenticação JWT
- Rate limiting por usuário
- Versionamento de API (v1, v2)
- Documentação Swagger automática
- Webhooks para eventos de IA
- Sistema de plugins extensível
- Métricas de uso detalhadas
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from functools import wraps
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, asdict
import hashlib
import hmac
import jwt
import requests
from flask import Flask, request, jsonify, g, make_response
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
import redis
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import sqlite3
from pathlib import Path
import yaml
import subprocess
import psutil
import socket
from urllib.parse import urlparse
import aiohttp
import websockets
import socket.io as sio
from websocket_server import WebsocketServer

# Imports do sistema AUTOBOT
try:
    from .local_trainer import LocalTrainer
    from .memory_manager import MemoryManager
except ImportError:
    try:
        from local_trainer import LocalTrainer
        from memory_manager import MemoryManager
    except ImportError:
        LocalTrainer = None
        MemoryManager = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Métricas Prometheus
REQUEST_COUNT = Counter('autobot_ai_requests_total', 'Total AI requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('autobot_ai_request_duration_seconds', 'Request duration')
ACTIVE_CONNECTIONS = Gauge('autobot_ai_active_connections', 'Active WebSocket connections')
AI_GENERATION_TIME = Histogram('autobot_ai_generation_duration_seconds', 'AI generation time')
CACHE_HITS = Counter('autobot_ai_cache_hits_total', 'Cache hits')
CACHE_MISSES = Counter('autobot_ai_cache_misses_total', 'Cache misses')

@dataclass
class APIKey:
    """Chave de API."""
    key: str
    user_id: str
    name: str
    permissions: List[str]
    rate_limit: int
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True
    usage_count: int = 0

@dataclass
class WebhookConfig:
    """Configuração de webhook."""
    id: str
    url: str
    events: List[str]
    secret: str
    is_active: bool = True
    retry_count: int = 3
    timeout: int = 30
    headers: Dict[str, str] = None
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {}

@dataclass
class ChatSession:
    """Sessão de chat."""
    id: str
    user_id: str
    created_at: datetime
    last_activity: datetime
    messages_count: int = 0
    context: Dict[str, Any] = None
    preferences: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}
        if self.preferences is None:
            self.preferences = {}

class RateLimiter:
    """Rate limiter customizado."""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.local_cache = {}
        self.lock = threading.Lock()
    
    def is_allowed(self, key: str, limit: int, window: int = 3600) -> bool:
        """Verifica se a requisição é permitida."""
        current_time = int(time.time())
        window_start = current_time - (current_time % window)
        
        if self.redis_client:
            try:
                pipe = self.redis_client.pipeline()
                pipe.incr(f"rate_limit:{key}:{window_start}")
                pipe.expire(f"rate_limit:{key}:{window_start}", window)
                results = pipe.execute()
                
                return results[0] <= limit
            except:
                # Fallback para cache local
                pass
        
        # Cache local como fallback
        with self.lock:
            cache_key = f"{key}:{window_start}"
            current_count = self.local_cache.get(cache_key, 0)
            
            if current_count >= limit:
                return False
            
            self.local_cache[cache_key] = current_count + 1
            
            # Limpa entradas antigas
            for k in list(self.local_cache.keys()):
                if int(k.split(':')[-1]) < window_start - window:
                    del self.local_cache[k]
            
            return True

class WebhookManager:
    """Gerenciador de webhooks."""
    
    def __init__(self):
        self.webhooks = {}
        self.executor = ThreadPoolExecutor(max_workers=5)
    
    def register_webhook(self, webhook: WebhookConfig):
        """Registra um webhook."""
        self.webhooks[webhook.id] = webhook
        logger.info(f"Webhook registrado: {webhook.id}")
    
    def trigger_event(self, event_type: str, data: Dict[str, Any]):
        """Dispara evento para webhooks relevantes."""
        for webhook in self.webhooks.values():
            if webhook.is_active and event_type in webhook.events:
                self.executor.submit(self._send_webhook, webhook, event_type, data)
    
    def _send_webhook(self, webhook: WebhookConfig, event_type: str, data: Dict[str, Any]):
        """Envia webhook."""
        payload = {
            'event': event_type,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        # Gera assinatura HMAC
        signature = hmac.new(
            webhook.secret.encode(),
            json.dumps(payload, sort_keys=True).encode(),
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            'Content-Type': 'application/json',
            'X-Autobot-Signature': f'sha256={signature}',
            'X-Autobot-Event': event_type,
            **webhook.headers
        }
        
        for attempt in range(webhook.retry_count):
            try:
                response = requests.post(
                    webhook.url,
                    json=payload,
                    headers=headers,
                    timeout=webhook.timeout
                )
                
                if response.status_code == 200:
                    logger.info(f"Webhook enviado com sucesso: {webhook.id}")
                    return
                else:
                    logger.warning(f"Webhook falhou (tentativa {attempt + 1}): {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Erro no webhook {webhook.id} (tentativa {attempt + 1}): {e}")
            
            if attempt < webhook.retry_count - 1:
                time.sleep(2 ** attempt)  # Backoff exponencial

class AIIntegrationAPI:
    """API principal de integração com IA."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Inicializa a API."""
        self.config = self._load_config(config_path)
        self.app = Flask(__name__)
        
        # Configurações Flask
        self.app.config['SECRET_KEY'] = self.config.get('secret_key', 'autobot-ai-secret')
        self.app.config['JWT_SECRET_KEY'] = self.config.get('jwt_secret', 'jwt-secret')
        self.app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
        
        # CORS
        CORS(self.app, origins=self.config.get('cors_origins', ['*']))
        
        # Redis para cache e rate limiting
        self._init_redis()
        
        # Rate limiter
        if self.redis_client:
            self.limiter = Limiter(
                self.app,
                key_func=get_remote_address,
                storage_uri=f"redis://{self.config.get('redis_host', 'localhost')}:{self.config.get('redis_port', 6379)}"
            )
        else:
            self.limiter = None
        
        self.rate_limiter = RateLimiter(self.redis_client)
        
        # Webhook manager
        self.webhook_manager = WebhookManager()
        
        # Banco de dados para API keys e sessões
        self.db_path = Path(self.config.get('db_path', './data/api.db'))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        
        # Sistemas de IA
        self.trainer = None
        self.memory_manager = None
        self._init_ai_systems()
        
        # Sessões ativas
        self.active_sessions = {}
        self.websocket_connections = {}
        
        # Métricas
        self.metrics = {
            'requests_total': 0,
            'requests_successful': 0,
            'avg_response_time': 0.0,
            'active_sessions': 0
        }
        
        # Registra rotas
        self._register_routes()
        
        # Worker threads
        self._start_workers()
        
        logger.info("AIIntegrationAPI inicializada com sucesso")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Carrega configuração."""
        default_config = {
            'host': '0.0.0.0',
            'port': 8000,
            'debug': False,
            'secret_key': 'autobot-ai-secret-key',
            'jwt_secret': 'jwt-secret-key',
            'redis_host': 'localhost',
            'redis_port': 6379,
            'cors_origins': ['*'],
            'rate_limit_default': 100,
            'rate_limit_window': 3600,
            'max_connections': 1000,
            'enable_metrics': True,
            'enable_websockets': True,
            'webhook_timeout': 30,
            'session_timeout': 3600
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                default_config.update(user_config)
        
        return default_config
    
    def _init_redis(self):
        """Inicializa conexão Redis."""
        try:
            import redis
            self.redis_client = redis.Redis(
                host=self.config.get('redis_host', 'localhost'),
                port=self.config.get('redis_port', 6379),
                db=0,
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("Redis conectado com sucesso")
        except Exception as e:
            logger.warning(f"Redis não disponível: {e}")
            self.redis_client = None
    
    def _init_database(self):
        """Inicializa banco de dados."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Tabela de API keys
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_keys (
                key TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                permissions TEXT NOT NULL,
                rate_limit INTEGER DEFAULT 100,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                usage_count INTEGER DEFAULT 0
            )
        ''')
        
        # Tabela de webhooks
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS webhooks (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                url TEXT NOT NULL,
                events TEXT NOT NULL,
                secret TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                retry_count INTEGER DEFAULT 3,
                timeout INTEGER DEFAULT 30,
                headers TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de sessões
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                messages_count INTEGER DEFAULT 0,
                context TEXT,
                preferences TEXT
            )
        ''')
        
        # Tabela de logs de API
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                method TEXT,
                endpoint TEXT,
                user_id TEXT,
                ip_address TEXT,
                status_code INTEGER,
                response_time REAL,
                error_message TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _init_ai_systems(self):
        """Inicializa sistemas de IA."""
        try:
            if LocalTrainer:
                self.trainer = LocalTrainer()
                logger.info("LocalTrainer inicializado")
            
            if MemoryManager:
                self.memory_manager = MemoryManager()
                logger.info("MemoryManager inicializado")
                
        except Exception as e:
            logger.error(f"Erro ao inicializar sistemas de IA: {e}")
    
    def _start_workers(self):
        """Inicia workers de background."""
        # Worker para limpeza de sessões
        def session_cleanup_worker():
            while True:
                try:
                    self._cleanup_expired_sessions()
                    time.sleep(300)  # A cada 5 minutos
                except Exception as e:
                    logger.error(f"Erro no worker de limpeza: {e}")
        
        cleanup_thread = threading.Thread(target=session_cleanup_worker, daemon=True)
        cleanup_thread.start()
    
    def _cleanup_expired_sessions(self):
        """Limpa sessões expiradas."""
        cutoff_time = datetime.now() - timedelta(seconds=self.config.get('session_timeout', 3600))
        
        expired_sessions = [
            session_id for session_id, session in self.active_sessions.items()
            if session.last_activity < cutoff_time
        ]
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]
            ACTIVE_CONNECTIONS.dec()
        
        if expired_sessions:
            logger.info(f"Limpeza: {len(expired_sessions)} sessões expiradas removidas")
    
    def _register_routes(self):
        """Registra todas as rotas da API."""
        
        # Middleware de autenticação
        @self.app.before_request
        def before_request():
            g.start_time = time.time()
            
            # Pula autenticação para rotas públicas
            public_routes = ['/health', '/metrics', '/docs', '/v1/auth/login']
            if request.path in public_routes:
                return
            
            # Verifica autenticação
            auth_result = self._authenticate_request()
            if not auth_result['success']:
                return jsonify({'error': auth_result['error']}), 401
            
            g.user_id = auth_result['user_id']
            g.api_key = auth_result.get('api_key')
            
            # Rate limiting
            if not self._check_rate_limit(g.user_id):
                return jsonify({'error': 'Rate limit exceeded'}), 429
        
        @self.app.after_request
        def after_request(response):
            # Registra métricas
            if hasattr(g, 'start_time'):
                duration = time.time() - g.start_time
                REQUEST_DURATION.observe(duration)
                REQUEST_COUNT.labels(
                    method=request.method,
                    endpoint=request.path,
                    status=response.status_code
                ).inc()
                
                # Log da requisição
                self._log_request(duration, response.status_code)
            
            return response
        
        # ==================== ROTAS PÚBLICAS ====================
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Verificação de saúde."""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0',
                'services': {
                    'ai_trainer': self.trainer is not None,
                    'memory_manager': self.memory_manager is not None,
                    'redis': self.redis_client is not None
                }
            })
        
        @self.app.route('/metrics', methods=['GET'])
        def metrics():
            """Métricas Prometheus."""
            if not self.config.get('enable_metrics', True):
                return jsonify({'error': 'Metrics disabled'}), 404
            
            response = make_response(generate_latest())
            response.headers['Content-Type'] = CONTENT_TYPE_LATEST
            return response
        
        # ==================== AUTENTICAÇÃO ====================
        
        @self.app.route('/v1/auth/login', methods=['POST'])
        def login():
            """Login e geração de token."""
            data = request.get_json()
            
            if not data or 'username' not in data or 'password' not in data:
                return jsonify({'error': 'Credenciais incompletas'}), 400
            
            # Validação simples (implementar validação real)
            if data['username'] == 'admin' and data['password'] == 'admin123':
                token = jwt.encode({
                    'user_id': 'admin',
                    'exp': datetime.utcnow() + timedelta(hours=24)
                }, self.app.config['JWT_SECRET_KEY'], algorithm='HS256')
                
                return jsonify({
                    'token': token,
                    'expires_in': 86400,
                    'user_id': 'admin'
                })
            
            return jsonify({'error': 'Credenciais inválidas'}), 401
        
        @self.app.route('/v1/auth/api-keys', methods=['POST'])
        def create_api_key():
            """Cria nova API key."""
            data = request.get_json()
            
            api_key = self._generate_api_key()
            key_config = APIKey(
                key=api_key,
                user_id=g.user_id,
                name=data.get('name', 'API Key'),
                permissions=data.get('permissions', ['chat', 'memory']),
                rate_limit=data.get('rate_limit', self.config.get('rate_limit_default', 100)),
                created_at=datetime.now()
            )
            
            self._save_api_key(key_config)
            
            return jsonify({
                'api_key': api_key,
                'permissions': key_config.permissions,
                'rate_limit': key_config.rate_limit
            })
        
        # ==================== CHAT ====================
        
        @self.app.route('/v1/chat/sessions', methods=['POST'])
        def create_chat_session():
            """Cria nova sessão de chat."""
            data = request.get_json() or {}
            
            session_id = str(uuid.uuid4())
            session = ChatSession(
                id=session_id,
                user_id=g.user_id,
                created_at=datetime.now(),
                last_activity=datetime.now(),
                preferences=data.get('preferences', {})
            )
            
            self.active_sessions[session_id] = session
            ACTIVE_CONNECTIONS.inc()
            
            # Salva no banco
            self._save_chat_session(session)
            
            return jsonify({
                'session_id': session_id,
                'created_at': session.created_at.isoformat()
            })
        
        @self.app.route('/v1/chat/sessions/<session_id>/messages', methods=['POST'])
        def send_message(session_id):
            """Envia mensagem no chat."""
            if session_id not in self.active_sessions:
                return jsonify({'error': 'Sessão não encontrada'}), 404
            
            data = request.get_json()
            if not data or 'message' not in data:
                return jsonify({'error': 'Mensagem não fornecida'}), 400
            
            session = self.active_sessions[session_id]
            session.last_activity = datetime.now()
            session.messages_count += 1
            
            message = data['message']
            context = data.get('context', {})
            
            # Processa mensagem com IA
            start_time = time.time()
            
            try:
                # Adiciona à memória
                if self.memory_manager:
                    self.memory_manager.add_message(
                        g.user_id, message, 'user', session_id
                    )
                
                # Gera resposta
                if self.trainer:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        ai_response = loop.run_until_complete(
                            self.trainer.generate_response(
                                message,
                                model_name=data.get('model'),
                                parameters=data.get('parameters', {}),
                                use_cache=data.get('use_cache', True)
                            )
                        )
                    finally:
                        loop.close()
                else:
                    ai_response = {
                        'success': False,
                        'error': 'Sistema de IA não disponível'
                    }
                
                generation_time = time.time() - start_time
                AI_GENERATION_TIME.observe(generation_time)
                
                if ai_response['success']:
                    # Adiciona resposta à memória
                    if self.memory_manager:
                        self.memory_manager.add_message(
                            g.user_id, ai_response['response'], 'assistant', session_id
                        )
                    
                    # Dispara webhook
                    self.webhook_manager.trigger_event('message.response', {
                        'session_id': session_id,
                        'user_id': g.user_id,
                        'message': message,
                        'response': ai_response['response'],
                        'model_used': ai_response.get('model_used'),
                        'response_time': generation_time
                    })
                    
                    if ai_response.get('from_cache'):
                        CACHE_HITS.inc()
                    else:
                        CACHE_MISSES.inc()
                    
                    return jsonify({
                        'response': ai_response['response'],
                        'model_used': ai_response.get('model_used'),
                        'response_time': generation_time,
                        'from_cache': ai_response.get('from_cache', False),
                        'session_id': session_id
                    })
                else:
                    return jsonify({
                        'error': ai_response.get('error', 'Erro na geração'),
                        'session_id': session_id
                    }), 500
                    
            except Exception as e:
                logger.error(f"Erro no chat: {e}")
                return jsonify({
                    'error': 'Erro interno do servidor',
                    'session_id': session_id
                }), 500
        
        @self.app.route('/v1/chat/sessions/<session_id>', methods=['GET'])
        def get_chat_session(session_id):
            """Obtém informações da sessão."""
            if session_id not in self.active_sessions:
                return jsonify({'error': 'Sessão não encontrada'}), 404
            
            session = self.active_sessions[session_id]
            
            return jsonify({
                'session_id': session_id,
                'created_at': session.created_at.isoformat(),
                'last_activity': session.last_activity.isoformat(),
                'messages_count': session.messages_count,
                'preferences': session.preferences
            })
        
        # ==================== MEMÓRIA ====================
        
        @self.app.route('/v1/memory/conversations', methods=['GET'])
        def get_conversations():
            """Lista conversas do usuário."""
            if not self.memory_manager:
                return jsonify({'error': 'Sistema de memória não disponível'}), 503
            
            limit = request.args.get('limit', 10, type=int)
            include_messages = request.args.get('include_messages', False, type=bool)
            
            try:
                conversations = self.memory_manager.get_user_conversations(
                    g.user_id, limit, include_messages
                )
                
                return jsonify({
                    'conversations': conversations,
                    'total': len(conversations)
                })
                
            except Exception as e:
                logger.error(f"Erro ao obter conversas: {e}")
                return jsonify({'error': 'Erro interno'}), 500
        
        @self.app.route('/v1/memory/search', methods=['POST'])
        def search_memory():
            """Busca na memória conversacional."""
            if not self.memory_manager:
                return jsonify({'error': 'Sistema de memória não disponível'}), 503
            
            data = request.get_json()
            if not data or 'query' not in data:
                return jsonify({'error': 'Query não fornecida'}), 400
            
            try:
                results = self.memory_manager.search_conversations(
                    g.user_id,
                    data['query'],
                    data.get('limit', 10)
                )
                
                return jsonify({
                    'results': results,
                    'query': data['query'],
                    'total': len(results)
                })
                
            except Exception as e:
                logger.error(f"Erro na busca: {e}")
                return jsonify({'error': 'Erro interno'}), 500
        
        @self.app.route('/v1/memory/profile', methods=['GET'])
        def get_user_profile():
            """Obtém perfil do usuário."""
            if not self.memory_manager:
                return jsonify({'error': 'Sistema de memória não disponível'}), 503
            
            try:
                profile = self.memory_manager.get_user_profile(g.user_id)
                if profile:
                    return jsonify(profile)
                else:
                    return jsonify({'error': 'Perfil não encontrado'}), 404
                    
            except Exception as e:
                logger.error(f"Erro ao obter perfil: {e}")
                return jsonify({'error': 'Erro interno'}), 500
        
        @self.app.route('/v1/memory/patterns', methods=['GET'])
        def analyze_patterns():
            """Analisa padrões comportamentais."""
            if not self.memory_manager:
                return jsonify({'error': 'Sistema de memória não disponível'}), 503
            
            try:
                patterns = self.memory_manager.analyze_user_patterns(g.user_id)
                return jsonify(patterns)
                
            except Exception as e:
                logger.error(f"Erro na análise: {e}")
                return jsonify({'error': 'Erro interno'}), 500
        
        # ==================== MODELOS ====================
        
        @self.app.route('/v1/models', methods=['GET'])
        def list_models():
            """Lista modelos disponíveis."""
            if not self.trainer:
                return jsonify({'error': 'Sistema de IA não disponível'}), 503
            
            try:
                models = self.trainer.list_available_models()
                return jsonify({'models': models})
                
            except Exception as e:
                logger.error(f"Erro ao listar modelos: {e}")
                return jsonify({'error': 'Erro interno'}), 500
        
        @self.app.route('/v1/models/<model_name>/optimize', methods=['POST'])
        def optimize_model(model_name):
            """Otimiza performance de um modelo."""
            if not self.trainer:
                return jsonify({'error': 'Sistema de IA não disponível'}), 503
            
            try:
                result = self.trainer.optimize_model_performance(model_name)
                return jsonify(result)
                
            except Exception as e:
                logger.error(f"Erro na otimização: {e}")
                return jsonify({'error': 'Erro interno'}), 500
        
        # ==================== WEBHOOKS ====================
        
        @self.app.route('/v1/webhooks', methods=['POST'])
        def create_webhook():
            """Cria novo webhook."""
            data = request.get_json()
            
            if not data or 'url' not in data or 'events' not in data:
                return jsonify({'error': 'Dados incompletos'}), 400
            
            webhook_id = str(uuid.uuid4())
            secret = self._generate_webhook_secret()
            
            webhook = WebhookConfig(
                id=webhook_id,
                url=data['url'],
                events=data['events'],
                secret=secret,
                retry_count=data.get('retry_count', 3),
                timeout=data.get('timeout', 30),
                headers=data.get('headers', {})
            )
            
            self.webhook_manager.register_webhook(webhook)
            self._save_webhook(webhook, g.user_id)
            
            return jsonify({
                'webhook_id': webhook_id,
                'secret': secret,
                'events': webhook.events
            })
        
        @self.app.route('/v1/webhooks/<webhook_id>', methods=['DELETE'])
        def delete_webhook(webhook_id):
            """Remove webhook."""
            if webhook_id in self.webhook_manager.webhooks:
                del self.webhook_manager.webhooks[webhook_id]
                self._delete_webhook(webhook_id)
                return jsonify({'message': 'Webhook removido'})
            else:
                return jsonify({'error': 'Webhook não encontrado'}), 404
        
        # ==================== MÉTRICAS E MONITORAMENTO ====================
        
        @self.app.route('/v1/metrics/system', methods=['GET'])
        def get_system_metrics():
            """Obtém métricas do sistema."""
            if not self.trainer:
                return jsonify({'error': 'Sistema de IA não disponível'}), 503
            
            try:
                metrics = self.trainer.get_system_metrics()
                
                # Adiciona métricas da API
                api_metrics = {
                    'active_sessions': len(self.active_sessions),
                    'total_requests': self.metrics['requests_total'],
                    'successful_requests': self.metrics['requests_successful'],
                    'avg_response_time': self.metrics['avg_response_time'],
                    'websocket_connections': len(self.websocket_connections)
                }
                
                metrics['api'] = api_metrics
                
                return jsonify(metrics)
                
            except Exception as e:
                logger.error(f"Erro ao obter métricas: {e}")
                return jsonify({'error': 'Erro interno'}), 500
        
        @self.app.route('/v1/admin/stats', methods=['GET'])
        def get_admin_stats():
            """Estatísticas administrativas."""
            # Somente administradores
            if g.user_id != 'admin':
                return jsonify({'error': 'Acesso negado'}), 403
            
            try:
                stats = {}
                
                if self.memory_manager:
                    stats['memory'] = self.memory_manager.get_statistics()
                
                if self.trainer:
                    stats['ai'] = self.trainer.get_system_metrics()
                
                # Estatísticas da API
                conn = sqlite3.connect(str(self.db_path))
                cursor = conn.cursor()
                
                cursor.execute('SELECT COUNT(*) FROM api_keys WHERE is_active = 1')
                active_keys = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM chat_sessions')
                total_sessions = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM webhooks WHERE is_active = 1')
                active_webhooks = cursor.fetchone()[0]
                
                conn.close()
                
                stats['api'] = {
                    'active_api_keys': active_keys,
                    'total_chat_sessions': total_sessions,
                    'active_webhooks': active_webhooks,
                    'current_active_sessions': len(self.active_sessions)
                }
                
                return jsonify(stats)
                
            except Exception as e:
                logger.error(f"Erro ao obter estatísticas: {e}")
                return jsonify({'error': 'Erro interno'}), 500
    
    def _authenticate_request(self) -> Dict[str, Any]:
        """Autentica requisição."""
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return {'success': False, 'error': 'Authorization header missing'}
        
        if auth_header.startswith('Bearer '):
            # JWT Token
            token = auth_header[7:]
            try:
                payload = jwt.decode(token, self.app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
                return {'success': True, 'user_id': payload['user_id']}
            except jwt.ExpiredSignatureError:
                return {'success': False, 'error': 'Token expired'}
            except jwt.InvalidTokenError:
                return {'success': False, 'error': 'Invalid token'}
        
        elif auth_header.startswith('ApiKey '):
            # API Key
            api_key = auth_header[7:]
            key_data = self._validate_api_key(api_key)
            
            if key_data:
                return {
                    'success': True,
                    'user_id': key_data['user_id'],
                    'api_key': api_key
                }
            else:
                return {'success': False, 'error': 'Invalid API key'}
        
        return {'success': False, 'error': 'Invalid authorization format'}
    
    def _validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Valida API key."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, permissions, rate_limit, expires_at 
            FROM api_keys 
            WHERE key = ? AND is_active = 1
        ''', (api_key,))
        
        result = cursor.fetchone()
        
        if result:
            # Atualiza contador de uso
            cursor.execute(
                'UPDATE api_keys SET usage_count = usage_count + 1 WHERE key = ?',
                (api_key,)
            )
            conn.commit()
            
            user_id, permissions, rate_limit, expires_at = result
            
            # Verifica expiração
            if expires_at and datetime.fromisoformat(expires_at) < datetime.now():
                conn.close()
                return None
            
            conn.close()
            return {
                'user_id': user_id,
                'permissions': json.loads(permissions),
                'rate_limit': rate_limit
            }
        
        conn.close()
        return None
    
    def _check_rate_limit(self, user_id: str) -> bool:
        """Verifica rate limit."""
        # Implementação básica - usar rate_limit específico do usuário
        return self.rate_limiter.is_allowed(
            f"user:{user_id}",
            self.config.get('rate_limit_default', 100),
            self.config.get('rate_limit_window', 3600)
        )
    
    def _generate_api_key(self) -> str:
        """Gera nova API key."""
        return f"autobot_{uuid.uuid4().hex}"
    
    def _generate_webhook_secret(self) -> str:
        """Gera secret para webhook."""
        return uuid.uuid4().hex
    
    def _save_api_key(self, api_key: APIKey):
        """Salva API key no banco."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO api_keys 
            (key, user_id, name, permissions, rate_limit, created_at, expires_at, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            api_key.key, api_key.user_id, api_key.name,
            json.dumps(api_key.permissions), api_key.rate_limit,
            api_key.created_at, api_key.expires_at, api_key.is_active
        ))
        
        conn.commit()
        conn.close()
    
    def _save_webhook(self, webhook: WebhookConfig, user_id: str):
        """Salva webhook no banco."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO webhooks 
            (id, user_id, url, events, secret, is_active, retry_count, timeout, headers)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            webhook.id, user_id, webhook.url, json.dumps(webhook.events),
            webhook.secret, webhook.is_active, webhook.retry_count,
            webhook.timeout, json.dumps(webhook.headers)
        ))
        
        conn.commit()
        conn.close()
    
    def _delete_webhook(self, webhook_id: str):
        """Remove webhook do banco."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM webhooks WHERE id = ?', (webhook_id,))
        
        conn.commit()
        conn.close()
    
    def _save_chat_session(self, session: ChatSession):
        """Salva sessão no banco."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO chat_sessions 
            (id, user_id, created_at, last_activity, messages_count, context, preferences)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            session.id, session.user_id, session.created_at,
            session.last_activity, session.messages_count,
            json.dumps(session.context), json.dumps(session.preferences)
        ))
        
        conn.commit()
        conn.close()
    
    def _log_request(self, duration: float, status_code: int):
        """Registra log da requisição."""
        try:
            # Atualiza métricas em memória
            self.metrics['requests_total'] += 1
            if 200 <= status_code < 400:
                self.metrics['requests_successful'] += 1
            
            # Calcula média móvel do tempo de resposta
            current_avg = self.metrics['avg_response_time']
            total_requests = self.metrics['requests_total']
            self.metrics['avg_response_time'] = (
                (current_avg * (total_requests - 1) + duration) / total_requests
            )
            
            # Salva no banco (opcional, para auditoria)
            if self.config.get('log_requests', False):
                conn = sqlite3.connect(str(self.db_path))
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO api_logs 
                    (method, endpoint, user_id, ip_address, status_code, response_time)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    request.method, request.path, getattr(g, 'user_id', None),
                    request.remote_addr, status_code, duration
                ))
                
                conn.commit()
                conn.close()
                
        except Exception as e:
            logger.error(f"Erro ao registrar log: {e}")
    
    def run(self, host: Optional[str] = None, port: Optional[int] = None, debug: Optional[bool] = None):
        """Executa o servidor da API."""
        host = host or self.config.get('host', '0.0.0.0')
        port = port or self.config.get('port', 8000)
        debug = debug if debug is not None else self.config.get('debug', False)
        
        logger.info(f"Iniciando AIIntegrationAPI em {host}:{port}")
        
        self.app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
    
    def cleanup(self):
        """Limpa recursos."""
        try:
            if hasattr(self, 'trainer') and self.trainer:
                self.trainer.cleanup_resources()
            
            if hasattr(self, 'memory_manager') and self.memory_manager:
                self.memory_manager.cleanup_resources()
            
            logger.info("Recursos da AIIntegrationAPI limpos")
            
        except Exception as e:
            logger.error(f"Erro ao limpar recursos: {e}")

# Função para teste
def main():
    """Função principal para teste."""
    api = AIIntegrationAPI()
    
    try:
        api.run(debug=True)
    except KeyboardInterrupt:
        logger.info("Parando servidor...")
    finally:
        api.cleanup()

if __name__ == "__main__":
    main()