"""
AUTOBOT API - Backend Flask Principal
=====================================

Sistema de API RESTful completo para o AUTOBOT.
Integração com 7 sistemas corporativos e IA local.

Funcionalidades:
- APIs REST para todas as integrações corporativas
- Sistema de autenticação e autorização
- Automação PyAutoGUI e Selenium
- Integração com sistema de IA local
- Logging avançado e monitoramento
- Rate limiting e segurança
"""

from flask import Flask, request, jsonify, session, send_file
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import logging
import json
import os
import time
import threading
import requests
import sqlite3
import hashlib
import pyautogui
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import schedule
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
import numpy as np
from cryptography.fernet import Fernet
import redis
import psutil
import socket
from functools import wraps
import uuid
import jwt as pyjwt
from typing import Dict, List, Any, Optional
import asyncio
import aiohttp
import ssl

# Importações do sistema de IA
try:
    from IA.treinamento.local_trainer import LocalTrainer
    from IA.treinamento.memory_manager import MemoryManager
    from IA.treinamento.integration_api import AIIntegrationAPI
except ImportError:
    # Fallback caso os módulos de IA ainda não estejam disponíveis
    LocalTrainer = None
    MemoryManager = None
    AIIntegrationAPI = None

# Configuração do Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'autobot-secret-key-2024')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-autobot')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# CORS para comunicação com frontend React
CORS(app, origins=['http://localhost:3000', 'http://localhost:3001'])

# Rate Limiting
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["1000 per hour"]
)

# JWT Manager
jwt_manager = JWTManager(app)

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('autobot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Redis para cache (opcional)
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    REDIS_AVAILABLE = True
except:
    REDIS_AVAILABLE = False
    logger.warning("Redis não disponível. Cache desabilitado.")

# Configurações das integrações
INTEGRATIONS_CONFIG = {
    'bitrix24': {
        'webhook_url': os.environ.get('BITRIX24_WEBHOOK'),
        'user_id': os.environ.get('BITRIX24_USER_ID'),
        'enabled': True
    },
    'ixcsoft': {
        'api_url': os.environ.get('IXCSOFT_API_URL'),
        'token': os.environ.get('IXCSOFT_TOKEN'),
        'enabled': True
    },
    'locaweb': {
        'api_url': os.environ.get('LOCAWEB_API_URL'),
        'api_key': os.environ.get('LOCAWEB_API_KEY'),
        'enabled': True
    },
    'fluctus': {
        'api_url': os.environ.get('FLUCTUS_API_URL'),
        'credentials': os.environ.get('FLUCTUS_CREDENTIALS'),
        'enabled': True
    },
    'newave': {
        'api_url': os.environ.get('NEWAVE_API_URL'),
        'auth_token': os.environ.get('NEWAVE_TOKEN'),
        'enabled': True
    },
    'uzera': {
        'api_url': os.environ.get('UZERA_API_URL'),
        'api_key': os.environ.get('UZERA_API_KEY'),
        'enabled': True
    },
    'playhub': {
        'api_url': os.environ.get('PLAYHUB_API_URL'),
        'access_token': os.environ.get('PLAYHUB_TOKEN'),
        'enabled': True
    }
}

# Banco de dados SQLite para armazenamento local
def init_database():
    """Inicializa o banco de dados SQLite."""
    conn = sqlite3.connect('autobot.db')
    cursor = conn.cursor()
    
    # Tabela de usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # Tabela de logs de automação
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS automation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            integration TEXT NOT NULL,
            action TEXT NOT NULL,
            parameters TEXT,
            result TEXT,
            status TEXT NOT NULL,
            execution_time REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Tabela de configurações
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT,
            description TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de sessões ativas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS active_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_token TEXT UNIQUE NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Tabela de métricas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_name TEXT NOT NULL,
            metric_value REAL NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            tags TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Banco de dados inicializado com sucesso.")

# Sistema de autenticação
class AuthManager:
    """Gerenciador de autenticação e autorização."""
    
    @staticmethod
    def create_user(username: str, email: str, password: str, role: str = 'user') -> bool:
        """Cria um novo usuário."""
        try:
            conn = sqlite3.connect('autobot.db')
            cursor = conn.cursor()
            
            password_hash = generate_password_hash(password)
            cursor.execute(
                'INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)',
                (username, email, password_hash, role)
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    @staticmethod
    def authenticate_user(username: str, password: str) -> Optional[Dict]:
        """Autentica um usuário."""
        conn = sqlite3.connect('autobot.db')
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT id, username, email, password_hash, role FROM users WHERE username = ? AND is_active = 1',
            (username,)
        )
        user = cursor.fetchone()
        
        if user and check_password_hash(user[3], password):
            # Atualiza último login
            cursor.execute(
                'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?',
                (user[0],)
            )
            conn.commit()
            conn.close()
            
            return {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'role': user[4]
            }
        
        conn.close()
        return None

# Sistema de automação
class AutomationEngine:
    """Engine principal para automações."""
    
    def __init__(self):
        self.driver = None
        self.session_id = None
        
    def setup_browser(self, headless: bool = True) -> bool:
        """Configura o navegador Chrome para automação."""
        try:
            chrome_options = Options()
            if headless:
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            return True
        except Exception as e:
            logger.error(f"Erro ao configurar navegador: {e}")
            return False
    
    def close_browser(self):
        """Fecha o navegador."""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def execute_automation(self, integration: str, action: str, parameters: Dict) -> Dict:
        """Executa uma automação específica."""
        start_time = time.time()
        result = {'status': 'error', 'message': '', 'data': None}
        
        try:
            if integration == 'bitrix24':
                result = self._automate_bitrix24(action, parameters)
            elif integration == 'ixcsoft':
                result = self._automate_ixcsoft(action, parameters)
            elif integration == 'locaweb':
                result = self._automate_locaweb(action, parameters)
            elif integration == 'fluctus':
                result = self._automate_fluctus(action, parameters)
            elif integration == 'newave':
                result = self._automate_newave(action, parameters)
            elif integration == 'uzera':
                result = self._automate_uzera(action, parameters)
            elif integration == 'playhub':
                result = self._automate_playhub(action, parameters)
            else:
                result['message'] = f'Integração {integration} não suportada'
                
        except Exception as e:
            result['message'] = f'Erro na automação: {str(e)}'
            logger.error(f"Erro em {integration}.{action}: {e}")
        
        finally:
            execution_time = time.time() - start_time
            self._log_automation(integration, action, parameters, result, execution_time)
        
        return result
    
    def _automate_bitrix24(self, action: str, parameters: Dict) -> Dict:
        """Automações específicas do Bitrix24."""
        config = INTEGRATIONS_CONFIG['bitrix24']
        
        if action == 'create_lead':
            return self._bitrix24_create_lead(parameters, config)
        elif action == 'get_deals':
            return self._bitrix24_get_deals(parameters, config)
        elif action == 'update_contact':
            return self._bitrix24_update_contact(parameters, config)
        else:
            return {'status': 'error', 'message': f'Ação {action} não suportada para Bitrix24'}
    
    def _bitrix24_create_lead(self, parameters: Dict, config: Dict) -> Dict:
        """Cria um lead no Bitrix24."""
        try:
            webhook_url = config['webhook_url']
            if not webhook_url:
                return {'status': 'error', 'message': 'Webhook URL não configurada'}
            
            lead_data = {
                'TITLE': parameters.get('title', 'Lead AUTOBOT'),
                'NAME': parameters.get('name', ''),
                'EMAIL': [{'VALUE': parameters.get('email', ''), 'VALUE_TYPE': 'WORK'}] if parameters.get('email') else [],
                'PHONE': [{'VALUE': parameters.get('phone', ''), 'VALUE_TYPE': 'WORK'}] if parameters.get('phone') else [],
                'SOURCE_ID': parameters.get('source_id', 'WEB'),
                'STATUS_ID': parameters.get('status_id', 'NEW'),
                'COMMENTS': parameters.get('comments', ''),
                'ASSIGNED_BY_ID': config.get('user_id', 1)
            }
            
            response = requests.post(f"{webhook_url}/crm.lead.add.json", json={
                'fields': lead_data
            })
            
            if response.status_code == 200:
                result = response.json()
                if result.get('result'):
                    return {
                        'status': 'success',
                        'message': 'Lead criado com sucesso',
                        'data': {'lead_id': result['result']}
                    }
            
            return {'status': 'error', 'message': 'Falha ao criar lead'}
            
        except Exception as e:
            return {'status': 'error', 'message': f'Erro ao criar lead: {str(e)}'}
    
    def _bitrix24_get_deals(self, parameters: Dict, config: Dict) -> Dict:
        """Obtém negócios do Bitrix24."""
        try:
            webhook_url = config['webhook_url']
            if not webhook_url:
                return {'status': 'error', 'message': 'Webhook URL não configurada'}
            
            filter_params = {}
            if parameters.get('assigned_by_id'):
                filter_params['ASSIGNED_BY_ID'] = parameters['assigned_by_id']
            if parameters.get('stage_id'):
                filter_params['STAGE_ID'] = parameters['stage_id']
            
            response = requests.post(f"{webhook_url}/crm.deal.list.json", json={
                'filter': filter_params,
                'select': ['ID', 'TITLE', 'STAGE_ID', 'OPPORTUNITY', 'CURRENCY_ID', 'ASSIGNED_BY_ID']
            })
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'status': 'success',
                    'message': 'Negócios obtidos com sucesso',
                    'data': result.get('result', [])
                }
            
            return {'status': 'error', 'message': 'Falha ao obter negócios'}
            
        except Exception as e:
            return {'status': 'error', 'message': f'Erro ao obter negócios: {str(e)}'}
    
    def _automate_ixcsoft(self, action: str, parameters: Dict) -> Dict:
        """Automações específicas do IXCSOFT."""
        config = INTEGRATIONS_CONFIG['ixcsoft']
        
        if action == 'get_clients':
            return self._ixcsoft_get_clients(parameters, config)
        elif action == 'create_ticket':
            return self._ixcsoft_create_ticket(parameters, config)
        elif action == 'get_invoices':
            return self._ixcsoft_get_invoices(parameters, config)
        else:
            return {'status': 'error', 'message': f'Ação {action} não suportada para IXCSOFT'}
    
    def _ixcsoft_get_clients(self, parameters: Dict, config: Dict) -> Dict:
        """Obtém clientes do IXCSOFT."""
        try:
            api_url = config['api_url']
            token = config['token']
            
            if not api_url or not token:
                return {'status': 'error', 'message': 'Configuração incompleta para IXCSOFT'}
            
            headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
            
            params = {
                'qtype': 'cliente.buscar',
                'limit': parameters.get('limit', 100),
                'offset': parameters.get('offset', 0)
            }
            
            response = requests.get(f"{api_url}/webservice/v1/", headers=headers, params=params)
            
            if response.status_code == 200:
                return {
                    'status': 'success',
                    'message': 'Clientes obtidos com sucesso',
                    'data': response.json()
                }
            
            return {'status': 'error', 'message': 'Falha ao obter clientes'}
            
        except Exception as e:
            return {'status': 'error', 'message': f'Erro ao obter clientes: {str(e)}'}
    
    def _automate_locaweb(self, action: str, parameters: Dict) -> Dict:
        """Automações específicas da Locaweb."""
        config = INTEGRATIONS_CONFIG['locaweb']
        
        if action == 'get_domains':
            return self._locaweb_get_domains(parameters, config)
        elif action == 'check_hosting':
            return self._locaweb_check_hosting(parameters, config)
        else:
            return {'status': 'error', 'message': f'Ação {action} não suportada para Locaweb'}
    
    def _log_automation(self, integration: str, action: str, parameters: Dict, result: Dict, execution_time: float):
        """Registra log da automação."""
        try:
            conn = sqlite3.connect('autobot.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO automation_logs 
                (integration, action, parameters, result, status, execution_time)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                integration,
                action,
                json.dumps(parameters),
                json.dumps(result),
                result.get('status', 'unknown'),
                execution_time
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao registrar log: {e}")

# Sistema de métricas
class MetricsCollector:
    """Coletor de métricas do sistema."""
    
    @staticmethod
    def collect_system_metrics():
        """Coleta métricas do sistema."""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            MetricsCollector.save_metric('cpu_usage', cpu_percent)
            
            # Memória
            memory = psutil.virtual_memory()
            MetricsCollector.save_metric('memory_usage', memory.percent)
            MetricsCollector.save_metric('memory_available', memory.available / (1024**3))  # GB
            
            # Disco
            disk = psutil.disk_usage('/')
            MetricsCollector.save_metric('disk_usage', disk.percent)
            MetricsCollector.save_metric('disk_free', disk.free / (1024**3))  # GB
            
            # Rede
            network = psutil.net_io_counters()
            MetricsCollector.save_metric('network_bytes_sent', network.bytes_sent)
            MetricsCollector.save_metric('network_bytes_recv', network.bytes_recv)
            
        except Exception as e:
            logger.error(f"Erro ao coletar métricas: {e}")
    
    @staticmethod
    def save_metric(name: str, value: float, tags: str = None):
        """Salva uma métrica no banco."""
        try:
            conn = sqlite3.connect('autobot.db')
            cursor = conn.cursor()
            
            cursor.execute(
                'INSERT INTO metrics (metric_name, metric_value, tags) VALUES (?, ?, ?)',
                (name, value, tags)
            )
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao salvar métrica: {e}")

# Inicialização do sistema de IA (se disponível)
ai_trainer = None
memory_manager = None
ai_api = None

def initialize_ai_system():
    """Inicializa o sistema de IA."""
    global ai_trainer, memory_manager, ai_api
    
    if LocalTrainer and MemoryManager and AIIntegrationAPI:
        try:
            ai_trainer = LocalTrainer()
            memory_manager = MemoryManager()
            ai_api = AIIntegrationAPI()
            logger.info("Sistema de IA inicializado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao inicializar sistema de IA: {e}")

# Instância global do engine de automação
automation_engine = AutomationEngine()

# ==================== ROTAS DA API ====================

@app.route('/health', methods=['GET'])
def health_check():
    """Verificação de saúde da API."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0',
        'services': {
            'database': True,
            'redis': REDIS_AVAILABLE,
            'ai': ai_trainer is not None
        }
    })

@app.route('/api/auth/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    """Registro de novo usuário."""
    data = request.get_json()
    
    if not data or not all(k in data for k in ['username', 'email', 'password']):
        return jsonify({'error': 'Dados incompletos'}), 400
    
    if AuthManager.create_user(data['username'], data['email'], data['password']):
        return jsonify({'message': 'Usuário criado com sucesso'}), 201
    else:
        return jsonify({'error': 'Usuário já existe'}), 409

@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    """Login de usuário."""
    data = request.get_json()
    
    if not data or not all(k in data for k in ['username', 'password']):
        return jsonify({'error': 'Credenciais incompletas'}), 400
    
    user = AuthManager.authenticate_user(data['username'], data['password'])
    if user:
        token = create_access_token(identity=user['id'])
        return jsonify({
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'role': user['role']
            }
        })
    else:
        return jsonify({'error': 'Credenciais inválidas'}), 401

@app.route('/api/integrations', methods=['GET'])
@jwt_required()
def get_integrations():
    """Lista integrações disponíveis."""
    integrations = []
    for name, config in INTEGRATIONS_CONFIG.items():
        integrations.append({
            'name': name,
            'enabled': config.get('enabled', False),
            'configured': bool(config.get('api_url') or config.get('webhook_url'))
        })
    
    return jsonify({'integrations': integrations})

@app.route('/api/automations/execute', methods=['POST'])
@jwt_required()
@limiter.limit("100 per hour")
def execute_automation():
    """Executa uma automação."""
    data = request.get_json()
    
    if not data or not all(k in data for k in ['integration', 'action']):
        return jsonify({'error': 'Dados incompletos'}), 400
    
    integration = data['integration']
    action = data['action']
    parameters = data.get('parameters', {})
    
    if integration not in INTEGRATIONS_CONFIG:
        return jsonify({'error': 'Integração não suportada'}), 400
    
    if not INTEGRATIONS_CONFIG[integration].get('enabled'):
        return jsonify({'error': 'Integração desabilitada'}), 400
    
    result = automation_engine.execute_automation(integration, action, parameters)
    return jsonify(result)

@app.route('/api/automations/logs', methods=['GET'])
@jwt_required()
def get_automation_logs():
    """Obtém logs de automação."""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    integration = request.args.get('integration')
    
    conn = sqlite3.connect('autobot.db')
    cursor = conn.cursor()
    
    query = 'SELECT * FROM automation_logs'
    params = []
    
    if integration:
        query += ' WHERE integration = ?'
        params.append(integration)
    
    query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
    params.extend([per_page, (page - 1) * per_page])
    
    cursor.execute(query, params)
    logs = cursor.fetchall()
    
    # Contar total
    count_query = 'SELECT COUNT(*) FROM automation_logs'
    if integration:
        count_query += ' WHERE integration = ?'
        cursor.execute(count_query, [integration] if integration else [])
    else:
        cursor.execute(count_query)
    
    total = cursor.fetchone()[0]
    conn.close()
    
    return jsonify({
        'logs': [dict(zip([col[0] for col in cursor.description], log)) for log in logs],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page
        }
    })

@app.route('/api/metrics/system', methods=['GET'])
@jwt_required()
def get_system_metrics():
    """Obtém métricas do sistema."""
    period = request.args.get('period', '1h')  # 1h, 24h, 7d, 30d
    
    # Definir intervalo baseado no período
    time_intervals = {
        '1h': datetime.now() - timedelta(hours=1),
        '24h': datetime.now() - timedelta(hours=24),
        '7d': datetime.now() - timedelta(days=7),
        '30d': datetime.now() - timedelta(days=30)
    }
    
    start_time = time_intervals.get(period, time_intervals['1h'])
    
    conn = sqlite3.connect('autobot.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT metric_name, AVG(metric_value) as avg_value, 
               MIN(metric_value) as min_value, MAX(metric_value) as max_value,
               COUNT(*) as count
        FROM metrics 
        WHERE timestamp >= ? 
        GROUP BY metric_name
    ''', (start_time,))
    
    metrics = cursor.fetchall()
    conn.close()
    
    result = {}
    for metric in metrics:
        result[metric[0]] = {
            'average': metric[1],
            'minimum': metric[2],
            'maximum': metric[3],
            'count': metric[4]
        }
    
    return jsonify({'metrics': result, 'period': period})

@app.route('/api/ai/chat', methods=['POST'])
@jwt_required()
@limiter.limit("50 per hour")
def ai_chat():
    """Endpoint para chat com IA."""
    if not ai_api:
        return jsonify({'error': 'Sistema de IA não disponível'}), 503
    
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'Mensagem não fornecida'}), 400
    
    user_id = get_jwt_identity()
    message = data['message']
    context = data.get('context', {})
    
    try:
        response = ai_api.process_chat_message(user_id, message, context)
        return jsonify(response)
    except Exception as e:
        logger.error(f"Erro no chat de IA: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/api/ai/memory', methods=['GET'])
@jwt_required()
def get_ai_memory():
    """Obtém memória conversacional do usuário."""
    if not memory_manager:
        return jsonify({'error': 'Sistema de memória não disponível'}), 503
    
    user_id = get_jwt_identity()
    limit = request.args.get('limit', 10, type=int)
    
    try:
        conversations = memory_manager.get_user_conversations(user_id, limit)
        return jsonify({'conversations': conversations})
    except Exception as e:
        logger.error(f"Erro ao obter memória: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/api/config/settings', methods=['GET', 'POST'])
@jwt_required()
def manage_settings():
    """Gerencia configurações do sistema."""
    user = get_jwt_identity()
    
    if request.method == 'GET':
        conn = sqlite3.connect('autobot.db')
        cursor = conn.cursor()
        cursor.execute('SELECT key, value, description FROM settings')
        settings = cursor.fetchall()
        conn.close()
        
        return jsonify({
            'settings': [{'key': s[0], 'value': s[1], 'description': s[2]} for s in settings]
        })
    
    elif request.method == 'POST':
        data = request.get_json()
        if not data or 'key' not in data or 'value' not in data:
            return jsonify({'error': 'Dados incompletos'}), 400
        
        conn = sqlite3.connect('autobot.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value, description, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (data['key'], data['value'], data.get('description', '')))
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Configuração salva com sucesso'})

@app.route('/api/dashboard/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """Obtém estatísticas para o dashboard."""
    conn = sqlite3.connect('autobot.db')
    cursor = conn.cursor()
    
    # Estatísticas de automações
    cursor.execute('''
        SELECT COUNT(*) as total,
               COUNT(CASE WHEN status = 'success' THEN 1 END) as successful,
               COUNT(CASE WHEN created_at >= datetime('now', '-24 hours') THEN 1 END) as last_24h
        FROM automation_logs
    ''')
    automation_stats = cursor.fetchone()
    
    # Estatísticas de usuários
    cursor.execute('''
        SELECT COUNT(*) as total,
               COUNT(CASE WHEN is_active = 1 THEN 1 END) as active,
               COUNT(CASE WHEN last_login >= datetime('now', '-7 days') THEN 1 END) as active_last_week
        FROM users
    ''')
    user_stats = cursor.fetchone()
    
    # Integrações mais usadas
    cursor.execute('''
        SELECT integration, COUNT(*) as count
        FROM automation_logs
        WHERE created_at >= datetime('now', '-30 days')
        GROUP BY integration
        ORDER BY count DESC
        LIMIT 5
    ''')
    top_integrations = cursor.fetchall()
    
    conn.close()
    
    return jsonify({
        'automations': {
            'total': automation_stats[0],
            'successful': automation_stats[1],
            'last_24h': automation_stats[2],
            'success_rate': (automation_stats[1] / automation_stats[0] * 100) if automation_stats[0] > 0 else 0
        },
        'users': {
            'total': user_stats[0],
            'active': user_stats[1],
            'active_last_week': user_stats[2]
        },
        'top_integrations': [{'name': t[0], 'count': t[1]} for t in top_integrations]
    })

# Endpoints específicos para cada integração
@app.route('/api/bitrix24/leads', methods=['GET', 'POST'])
@jwt_required()
def bitrix24_leads():
    """Gerencia leads do Bitrix24."""
    if request.method == 'GET':
        # Listar leads
        result = automation_engine.execute_automation('bitrix24', 'get_leads', {})
        return jsonify(result)
    elif request.method == 'POST':
        # Criar lead
        data = request.get_json()
        result = automation_engine.execute_automation('bitrix24', 'create_lead', data)
        return jsonify(result)

@app.route('/api/ixcsoft/clients', methods=['GET'])
@jwt_required()
def ixcsoft_clients():
    """Lista clientes do IXCSOFT."""
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    result = automation_engine.execute_automation('ixcsoft', 'get_clients', {
        'limit': limit,
        'offset': offset
    })
    return jsonify(result)

@app.route('/api/locaweb/domains', methods=['GET'])
@jwt_required()
def locaweb_domains():
    """Lista domínios da Locaweb."""
    result = automation_engine.execute_automation('locaweb', 'get_domains', {})
    return jsonify(result)

# Sistema de tarefas agendadas
def scheduled_tasks():
    """Executa tarefas agendadas."""
    # Coleta de métricas a cada 5 minutos
    schedule.every(5).minutes.do(MetricsCollector.collect_system_metrics)
    
    # Limpeza de logs antigos (mais de 30 dias)
    def cleanup_old_logs():
        try:
            conn = sqlite3.connect('autobot.db')
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM automation_logs WHERE created_at < datetime('now', '-30 days')"
            )
            cursor.execute(
                "DELETE FROM metrics WHERE timestamp < datetime('now', '-30 days')"
            )
            conn.commit()
            conn.close()
            logger.info("Limpeza de logs antigos concluída")
        except Exception as e:
            logger.error(f"Erro na limpeza de logs: {e}")
    
    schedule.every().day.at("02:00").do(cleanup_old_logs)
    
    # Loop de execução das tarefas agendadas
    while True:
        schedule.run_pending()
        time.sleep(60)  # Verifica a cada minuto

# Thread para tarefas agendadas
def start_scheduled_tasks():
    """Inicia thread para tarefas agendadas."""
    task_thread = threading.Thread(target=scheduled_tasks, daemon=True)
    task_thread.start()

# Middleware para logging de requests
@app.before_request
def log_request_info():
    """Log de informações da requisição."""
    logger.info(f"{request.method} {request.url} - {request.remote_addr}")

@app.after_request
def log_response_info(response):
    """Log de informações da resposta."""
    logger.info(f"Response: {response.status_code}")
    return response

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint não encontrado'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Erro interno: {error}")
    return jsonify({'error': 'Erro interno do servidor'}), 500

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({'error': 'Limite de taxa excedido', 'retry_after': e.retry_after}), 429

# Inicialização da aplicação
def create_app():
    """Factory function para criar a aplicação."""
    # Inicializar banco de dados
    init_database()
    
    # Inicializar sistema de IA
    initialize_ai_system()
    
    # Criar usuário admin padrão se não existir
    if not AuthManager.authenticate_user('admin', 'admin123'):
        AuthManager.create_user('admin', 'admin@autobot.com', 'admin123', 'admin')
        logger.info("Usuário admin criado com sucesso")
    
    # Iniciar tarefas agendadas
    start_scheduled_tasks()
    
    logger.info("AUTOBOT API inicializada com sucesso")
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('DEBUG', 'False').lower() == 'true'
    )