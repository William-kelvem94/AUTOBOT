"""
Dashboard Monitor - Sistema Avançado de Monitoramento
====================================================

Sistema completo de monitoramento em tempo real para o AUTOBOT,
com dashboards interativos, alertas automáticos e visualizações avançadas.

Funcionalidades principais:
- Dashboard web em tempo real
- Monitoramento de métricas de sistema
- Alertas automáticos personalizáveis
- Visualizações interativas
- Relatórios executivos
- Análise de tendências
- Monitoramento de performance de IA
- Dashboards personalizáveis por usuário
"""

import logging
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from collections import deque, defaultdict
import sqlite3
from pathlib import Path
import asyncio
import websockets
import socket
from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import psutil
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import yaml
import schedule

# Importações do sistema AUTOBOT
try:
    from .local_trainer import LocalTrainer
    from .memory_manager import MemoryManager
    from .model_optimizer import ModelOptimizer
    from .conversation_analyzer import ConversationAnalyzer
except ImportError:
    try:
        from local_trainer import LocalTrainer
        from memory_manager import MemoryManager
        from model_optimizer import ModelOptimizer
        from conversation_analyzer import ConversationAnalyzer
    except ImportError:
        LocalTrainer = None
        MemoryManager = None
        ModelOptimizer = None
        ConversationAnalyzer = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AlertRule:
    """Regra de alerta."""
    id: str
    name: str
    metric: str
    condition: str  # >, <, >=, <=, ==
    threshold: float
    duration_minutes: int
    severity: str  # critical, warning, info
    channels: List[str]  # email, webhook, slack
    enabled: bool = True
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0

@dataclass
class SystemMetric:
    """Métrica do sistema."""
    name: str
    value: float
    unit: str
    timestamp: datetime
    category: str  # system, ai, business
    metadata: Dict[str, Any] = None

@dataclass
class DashboardWidget:
    """Widget do dashboard."""
    id: str
    type: str  # chart, metric, table, alert
    title: str
    config: Dict[str, Any]
    position: Dict[str, int]  # x, y, width, height
    refresh_interval: int = 60  # segundos
    data_source: str = "system"

class MetricsCollector:
    """Coletor de métricas do sistema."""
    
    def __init__(self):
        self.metrics_buffer = deque(maxlen=10000)
        self.ai_systems = {}
        self.lock = threading.Lock()
        
    def set_ai_systems(self, trainer=None, memory_manager=None, 
                      optimizer=None, analyzer=None):
        """Configura sistemas de IA para coleta de métricas."""
        self.ai_systems = {
            'trainer': trainer,
            'memory_manager': memory_manager,
            'optimizer': optimizer,
            'analyzer': analyzer
        }
    
    def collect_system_metrics(self) -> List[SystemMetric]:
        """Coleta métricas do sistema."""
        metrics = []
        timestamp = datetime.now()
        
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics.append(SystemMetric(
                name='cpu_usage',
                value=cpu_percent,
                unit='%',
                timestamp=timestamp,
                category='system'
            ))
            
            # Memória
            memory = psutil.virtual_memory()
            metrics.append(SystemMetric(
                name='memory_usage',
                value=memory.percent,
                unit='%',
                timestamp=timestamp,
                category='system'
            ))
            metrics.append(SystemMetric(
                name='memory_available',
                value=memory.available / (1024**3),
                unit='GB',
                timestamp=timestamp,
                category='system'
            ))
            
            # Disco
            disk = psutil.disk_usage('/')
            metrics.append(SystemMetric(
                name='disk_usage',
                value=disk.percent,
                unit='%',
                timestamp=timestamp,
                category='system'
            ))
            
            # Rede
            network = psutil.net_io_counters()
            metrics.append(SystemMetric(
                name='network_bytes_sent',
                value=network.bytes_sent / (1024**2),
                unit='MB',
                timestamp=timestamp,
                category='system'
            ))
            metrics.append(SystemMetric(
                name='network_bytes_recv',
                value=network.bytes_recv / (1024**2),
                unit='MB',
                timestamp=timestamp,
                category='system'
            ))
            
        except Exception as e:
            logger.error(f"Erro ao coletar métricas do sistema: {e}")
        
        return metrics
    
    def collect_ai_metrics(self) -> List[SystemMetric]:
        """Coleta métricas dos sistemas de IA."""
        metrics = []
        timestamp = datetime.now()
        
        try:
            # Métricas do LocalTrainer
            if self.ai_systems.get('trainer'):
                trainer_metrics = self.ai_systems['trainer'].get_system_metrics()
                
                if 'models' in trainer_metrics:
                    for model_name, model_metrics in trainer_metrics['models'].items():
                        metrics.append(SystemMetric(
                            name=f'model_{model_name}_response_time',
                            value=model_metrics.get('avg_response_time', 0),
                            unit='s',
                            timestamp=timestamp,
                            category='ai',
                            metadata={'model': model_name}
                        ))
                        
                        metrics.append(SystemMetric(
                            name=f'model_{model_name}_error_rate',
                            value=model_metrics.get('error_rate', 0) * 100,
                            unit='%',
                            timestamp=timestamp,
                            category='ai',
                            metadata={'model': model_name}
                        ))
            
            # Métricas do MemoryManager
            if self.ai_systems.get('memory_manager'):
                memory_stats = self.ai_systems['memory_manager'].get_statistics()
                
                metrics.append(SystemMetric(
                    name='total_conversations',
                    value=memory_stats.get('total_conversations', 0),
                    unit='count',
                    timestamp=timestamp,
                    category='ai'
                ))
                
                metrics.append(SystemMetric(
                    name='avg_sentiment',
                    value=memory_stats.get('avg_sentiment', 0),
                    unit='score',
                    timestamp=timestamp,
                    category='ai'
                ))
            
            # Métricas do ModelOptimizer
            if self.ai_systems.get('optimizer'):
                optimizer_stats = self.ai_systems['optimizer'].get_optimization_statistics()
                
                if 'performance' in optimizer_stats:
                    perf = optimizer_stats['performance']
                    metrics.append(SystemMetric(
                        name='ai_avg_quality',
                        value=perf.get('avg_quality', 0),
                        unit='score',
                        timestamp=timestamp,
                        category='ai'
                    ))
                    
                    metrics.append(SystemMetric(
                        name='ai_avg_response_time',
                        value=perf.get('avg_response_time', 0),
                        unit='s',
                        timestamp=timestamp,
                        category='ai'
                    ))
        
        except Exception as e:
            logger.error(f"Erro ao coletar métricas de IA: {e}")
        
        return metrics
    
    def collect_business_metrics(self) -> List[SystemMetric]:
        """Coleta métricas de negócio."""
        metrics = []
        timestamp = datetime.now()
        
        try:
            # Métricas do ConversationAnalyzer
            if self.ai_systems.get('analyzer'):
                analytics = self.ai_systems['analyzer'].get_analytics_summary(1)
                
                metrics.append(SystemMetric(
                    name='user_satisfaction',
                    value=analytics.get('avg_satisfaction', 0) * 100,
                    unit='%',
                    timestamp=timestamp,
                    category='business'
                ))
                
                metrics.append(SystemMetric(
                    name='problem_resolution_rate',
                    value=analytics.get('avg_resolution', 0) * 100,
                    unit='%',
                    timestamp=timestamp,
                    category='business'
                ))
                
                metrics.append(SystemMetric(
                    name='user_engagement',
                    value=analytics.get('avg_engagement', 0) * 100,
                    unit='%',
                    timestamp=timestamp,
                    category='business'
                ))
        
        except Exception as e:
            logger.error(f"Erro ao coletar métricas de negócio: {e}")
        
        return metrics
    
    def collect_all_metrics(self) -> List[SystemMetric]:
        """Coleta todas as métricas."""
        all_metrics = []
        
        all_metrics.extend(self.collect_system_metrics())
        all_metrics.extend(self.collect_ai_metrics())
        all_metrics.extend(self.collect_business_metrics())
        
        # Adiciona ao buffer
        with self.lock:
            self.metrics_buffer.extend(all_metrics)
        
        return all_metrics
    
    def get_recent_metrics(self, minutes: int = 60) -> List[SystemMetric]:
        """Obtém métricas recentes."""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        with self.lock:
            recent_metrics = [
                metric for metric in self.metrics_buffer 
                if metric.timestamp >= cutoff_time
            ]
        
        return recent_metrics

class AlertManager:
    """Gerenciador de alertas."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.alert_rules = {}
        self.alert_history = deque(maxlen=1000)
        self.notification_channels = {}
        self.load_config(config_path)
    
    def load_config(self, config_path: Optional[str]):
        """Carrega configuração de alertas."""
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    
                self.notification_channels = config.get('notification_channels', {})
                
                # Carrega regras de alerta
                for rule_config in config.get('alert_rules', []):
                    rule = AlertRule(**rule_config)
                    self.alert_rules[rule.id] = rule
                    
            except Exception as e:
                logger.error(f"Erro ao carregar configuração de alertas: {e}")
    
    def add_alert_rule(self, rule: AlertRule):
        """Adiciona regra de alerta."""
        self.alert_rules[rule.id] = rule
        logger.info(f"Regra de alerta adicionada: {rule.name}")
    
    def check_alerts(self, metrics: List[SystemMetric]):
        """Verifica alertas baseado nas métricas."""
        for rule in self.alert_rules.values():
            if not rule.enabled:
                continue
            
            # Busca métricas relevantes
            relevant_metrics = [m for m in metrics if m.name == rule.metric]
            
            if not relevant_metrics:
                continue
            
            # Verifica condição
            latest_metric = relevant_metrics[-1]
            if self._evaluate_condition(latest_metric.value, rule.condition, rule.threshold):
                self._trigger_alert(rule, latest_metric)
    
    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """Avalia condição de alerta."""
        if condition == '>':
            return value > threshold
        elif condition == '<':
            return value < threshold
        elif condition == '>=':
            return value >= threshold
        elif condition == '<=':
            return value <= threshold
        elif condition == '==':
            return abs(value - threshold) < 0.001
        else:
            return False
    
    def _trigger_alert(self, rule: AlertRule, metric: SystemMetric):
        """Dispara alerta."""
        now = datetime.now()
        
        # Verifica cooldown
        if (rule.last_triggered and 
            (now - rule.last_triggered).total_seconds() < rule.duration_minutes * 60):
            return
        
        rule.last_triggered = now
        rule.trigger_count += 1
        
        alert_data = {
            'rule_name': rule.name,
            'metric_name': metric.name,
            'current_value': metric.value,
            'threshold': rule.threshold,
            'severity': rule.severity,
            'timestamp': now.isoformat()
        }
        
        self.alert_history.append(alert_data)
        
        # Envia notificações
        for channel in rule.channels:
            self._send_notification(channel, alert_data)
        
        logger.warning(f"Alerta disparado: {rule.name} - {metric.name}={metric.value}")
    
    def _send_notification(self, channel: str, alert_data: Dict[str, Any]):
        """Envia notificação."""
        try:
            if channel == 'email':
                self._send_email_notification(alert_data)
            elif channel == 'webhook':
                self._send_webhook_notification(alert_data)
            elif channel == 'slack':
                self._send_slack_notification(alert_data)
        except Exception as e:
            logger.error(f"Erro ao enviar notificação via {channel}: {e}")
    
    def _send_email_notification(self, alert_data: Dict[str, Any]):
        """Envia notificação por email."""
        email_config = self.notification_channels.get('email', {})
        
        if not email_config:
            return
        
        msg = MIMEMultipart()
        msg['From'] = email_config['from']
        msg['To'] = ', '.join(email_config['to'])
        msg['Subject'] = f"AUTOBOT Alert: {alert_data['rule_name']}"
        
        body = f"""
        Alerta AUTOBOT Disparado
        
        Regra: {alert_data['rule_name']}
        Métrica: {alert_data['metric_name']}
        Valor Atual: {alert_data['current_value']}
        Threshold: {alert_data['threshold']}
        Severidade: {alert_data['severity']}
        Timestamp: {alert_data['timestamp']}
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
        if email_config.get('use_tls'):
            server.starttls()
        if email_config.get('username'):
            server.login(email_config['username'], email_config['password'])
        
        server.send_message(msg)
        server.quit()
    
    def _send_webhook_notification(self, alert_data: Dict[str, Any]):
        """Envia notificação via webhook."""
        webhook_config = self.notification_channels.get('webhook', {})
        
        if not webhook_config:
            return
        
        response = requests.post(
            webhook_config['url'],
            json=alert_data,
            headers=webhook_config.get('headers', {}),
            timeout=30
        )
        response.raise_for_status()
    
    def _send_slack_notification(self, alert_data: Dict[str, Any]):
        """Envia notificação para Slack."""
        slack_config = self.notification_channels.get('slack', {})
        
        if not slack_config:
            return
        
        message = {
            'text': f"🚨 AUTOBOT Alert: {alert_data['rule_name']}",
            'attachments': [{
                'color': 'danger' if alert_data['severity'] == 'critical' else 'warning',
                'fields': [
                    {'title': 'Métrica', 'value': alert_data['metric_name'], 'short': True},
                    {'title': 'Valor', 'value': str(alert_data['current_value']), 'short': True},
                    {'title': 'Threshold', 'value': str(alert_data['threshold']), 'short': True},
                    {'title': 'Severidade', 'value': alert_data['severity'], 'short': True}
                ]
            }]
        }
        
        response = requests.post(
            slack_config['webhook_url'],
            json=message,
            timeout=30
        )
        response.raise_for_status()

class DashboardGenerator:
    """Gerador de dashboards."""
    
    def __init__(self):
        self.color_palette = px.colors.qualitative.Set3
    
    def create_system_overview_chart(self, metrics: List[SystemMetric]) -> Dict[str, Any]:
        """Cria gráfico de overview do sistema."""
        # Filtra métricas de sistema
        system_metrics = [m for m in metrics if m.category == 'system']
        
        if not system_metrics:
            return {'data': [], 'layout': {}}
        
        # Organiza dados por métrica
        data = defaultdict(list)
        timestamps = defaultdict(list)
        
        for metric in system_metrics:
            data[metric.name].append(metric.value)
            timestamps[metric.name].append(metric.timestamp)
        
        # Cria traces
        traces = []
        for i, (metric_name, values) in enumerate(data.items()):
            trace = go.Scatter(
                x=timestamps[metric_name],
                y=values,
                mode='lines+markers',
                name=metric_name.replace('_', ' ').title(),
                line=dict(color=self.color_palette[i % len(self.color_palette)])
            )
            traces.append(trace)
        
        layout = go.Layout(
            title='System Metrics Overview',
            xaxis=dict(title='Time'),
            yaxis=dict(title='Value'),
            hovermode='closest'
        )
        
        return {'data': traces, 'layout': layout}
    
    def create_ai_performance_chart(self, metrics: List[SystemMetric]) -> Dict[str, Any]:
        """Cria gráfico de performance de IA."""
        ai_metrics = [m for m in metrics if m.category == 'ai']
        
        if not ai_metrics:
            return {'data': [], 'layout': {}}
        
        # Agrupa por modelo se disponível
        model_data = defaultdict(lambda: defaultdict(list))
        
        for metric in ai_metrics:
            model_name = metric.metadata.get('model', 'general') if metric.metadata else 'general'
            model_data[model_name][metric.name].append({
                'timestamp': metric.timestamp,
                'value': metric.value
            })
        
        traces = []
        color_idx = 0
        
        for model_name, model_metrics in model_data.items():
            for metric_name, metric_values in model_metrics.items():
                if metric_values:
                    timestamps = [mv['timestamp'] for mv in metric_values]
                    values = [mv['value'] for mv in metric_values]
                    
                    trace = go.Scatter(
                        x=timestamps,
                        y=values,
                        mode='lines+markers',
                        name=f"{model_name} - {metric_name.replace('_', ' ').title()}",
                        line=dict(color=self.color_palette[color_idx % len(self.color_palette)])
                    )
                    traces.append(trace)
                    color_idx += 1
        
        layout = go.Layout(
            title='AI Performance Metrics',
            xaxis=dict(title='Time'),
            yaxis=dict(title='Value'),
            hovermode='closest'
        )
        
        return {'data': traces, 'layout': layout}
    
    def create_business_metrics_chart(self, metrics: List[SystemMetric]) -> Dict[str, Any]:
        """Cria gráfico de métricas de negócio."""
        business_metrics = [m for m in metrics if m.category == 'business']
        
        if not business_metrics:
            return {'data': [], 'layout': {}}
        
        # Cria gráfico de barras para métricas de negócio
        metric_names = []
        metric_values = []
        
        # Pega valores mais recentes de cada métrica
        latest_metrics = {}
        for metric in business_metrics:
            if metric.name not in latest_metrics or metric.timestamp > latest_metrics[metric.name].timestamp:
                latest_metrics[metric.name] = metric
        
        for metric_name, metric in latest_metrics.items():
            metric_names.append(metric_name.replace('_', ' ').title())
            metric_values.append(metric.value)
        
        trace = go.Bar(
            x=metric_names,
            y=metric_values,
            marker=dict(
                color=metric_values,
                colorscale='RdYlGn',
                cmin=0,
                cmax=100
            )
        )
        
        layout = go.Layout(
            title='Business Metrics',
            xaxis=dict(title='Metric'),
            yaxis=dict(title='Value (%)', range=[0, 100]),
            showlegend=False
        )
        
        return {'data': [trace], 'layout': layout}
    
    def create_alerts_summary(self, alert_history: List[Dict]) -> Dict[str, Any]:
        """Cria resumo de alertas."""
        if not alert_history:
            return {
                'total_alerts': 0,
                'critical_alerts': 0,
                'warning_alerts': 0,
                'recent_alerts': []
            }
        
        # Conta alertas por severidade
        severity_counts = defaultdict(int)
        for alert in alert_history:
            severity_counts[alert['severity']] += 1
        
        # Alertas recentes (últimas 24h)
        cutoff_time = datetime.now() - timedelta(hours=24)
        recent_alerts = [
            alert for alert in alert_history
            if datetime.fromisoformat(alert['timestamp']) > cutoff_time
        ]
        
        return {
            'total_alerts': len(alert_history),
            'critical_alerts': severity_counts['critical'],
            'warning_alerts': severity_counts['warning'],
            'info_alerts': severity_counts['info'],
            'recent_alerts': recent_alerts[-10:]  # Últimos 10
        }

class DashboardMonitor:
    """Monitor principal do dashboard."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        
        # Flask app para dashboard web
        self.app = Flask(__name__)
        self.app.secret_key = self.config.get('secret_key', 'dashboard-secret')
        CORS(self.app)
        
        # Socket.IO para atualizações em tempo real
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Componentes
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager(config_path)
        self.dashboard_generator = DashboardGenerator()
        
        # Banco de dados para histórico
        self.db_path = Path(self.config.get('db_path', './data/dashboard.db'))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        
        # Cache de dados
        self.dashboard_cache = {}
        self.last_update = datetime.now()
        
        # Widgets configuráveis
        self.dashboard_widgets = self._load_default_widgets()
        
        # Registra rotas
        self._register_routes()
        
        # Inicia workers
        self._start_workers()
        
        logger.info("DashboardMonitor inicializado com sucesso")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Carrega configuração."""
        default_config = {
            'host': '0.0.0.0',
            'port': 8080,
            'debug': False,
            'secret_key': 'dashboard-secret-key',
            'update_interval': 30,  # segundos
            'metrics_retention_days': 30,
            'enable_websockets': True
        }
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = yaml.safe_load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.error(f"Erro ao carregar configuração: {e}")
        
        return default_config
    
    def _init_database(self):
        """Inicializa banco de dados."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Tabela de métricas históricas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT,
                category TEXT NOT NULL,
                metadata TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de configurações de dashboard
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dashboard_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                dashboard_name TEXT NOT NULL,
                widgets_config TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_default_widgets(self) -> List[DashboardWidget]:
        """Carrega widgets padrão."""
        return [
            DashboardWidget(
                id='system_overview',
                type='chart',
                title='System Overview',
                config={'chart_type': 'line', 'metrics': ['cpu_usage', 'memory_usage']},
                position={'x': 0, 'y': 0, 'width': 6, 'height': 4}
            ),
            DashboardWidget(
                id='ai_performance',
                type='chart',
                title='AI Performance',
                config={'chart_type': 'line', 'category': 'ai'},
                position={'x': 6, 'y': 0, 'width': 6, 'height': 4}
            ),
            DashboardWidget(
                id='business_metrics',
                type='chart',
                title='Business Metrics',
                config={'chart_type': 'bar', 'category': 'business'},
                position={'x': 0, 'y': 4, 'width': 8, 'height': 3}
            ),
            DashboardWidget(
                id='alerts_summary',
                type='alert',
                title='Active Alerts',
                config={},
                position={'x': 8, 'y': 4, 'width': 4, 'height': 3}
            )
        ]
    
    def _register_routes(self):
        """Registra rotas do Flask."""
        
        @self.app.route('/')
        def dashboard_home():
            """Página principal do dashboard."""
            return render_template('dashboard.html')
        
        @self.app.route('/api/metrics/current')
        def get_current_metrics():
            """API para métricas atuais."""
            metrics = self.metrics_collector.get_recent_metrics(5)  # Últimos 5 minutos
            
            metrics_data = []
            for metric in metrics:
                metrics_data.append({
                    'name': metric.name,
                    'value': metric.value,
                    'unit': metric.unit,
                    'category': metric.category,
                    'timestamp': metric.timestamp.isoformat(),
                    'metadata': metric.metadata
                })
            
            return jsonify(metrics_data)
        
        @self.app.route('/api/charts/system-overview')
        def get_system_overview_chart():
            """API para gráfico de overview do sistema."""
            metrics = self.metrics_collector.get_recent_metrics(60)  # Última hora
            chart_data = self.dashboard_generator.create_system_overview_chart(metrics)
            
            return json.dumps(chart_data, cls=PlotlyJSONEncoder)
        
        @self.app.route('/api/charts/ai-performance')
        def get_ai_performance_chart():
            """API para gráfico de performance de IA."""
            metrics = self.metrics_collector.get_recent_metrics(60)
            chart_data = self.dashboard_generator.create_ai_performance_chart(metrics)
            
            return json.dumps(chart_data, cls=PlotlyJSONEncoder)
        
        @self.app.route('/api/charts/business-metrics')
        def get_business_metrics_chart():
            """API para gráfico de métricas de negócio."""
            metrics = self.metrics_collector.get_recent_metrics(10)
            chart_data = self.dashboard_generator.create_business_metrics_chart(metrics)
            
            return json.dumps(chart_data, cls=PlotlyJSONEncoder)
        
        @self.app.route('/api/alerts/summary')
        def get_alerts_summary():
            """API para resumo de alertas."""
            alert_summary = self.dashboard_generator.create_alerts_summary(
                list(self.alert_manager.alert_history)
            )
            
            return jsonify(alert_summary)
        
        @self.app.route('/api/dashboard/widgets')
        def get_dashboard_widgets():
            """API para configuração de widgets."""
            widgets_data = []
            for widget in self.dashboard_widgets:
                widgets_data.append(asdict(widget))
            
            return jsonify(widgets_data)
        
        # WebSocket handlers
        @self.socketio.on('connect')
        def handle_connect():
            """Handle WebSocket connection."""
            logger.info("Client connected to dashboard")
            
            # Envia dados iniciais
            self.socketio.emit('metrics_update', {
                'timestamp': datetime.now().isoformat(),
                'data': 'Connected to AUTOBOT Dashboard'
            })
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle WebSocket disconnection."""
            logger.info("Client disconnected from dashboard")
    
    def _start_workers(self):
        """Inicia workers de background."""
        
        # Worker de coleta de métricas
        def metrics_worker():
            while True:
                try:
                    metrics = self.metrics_collector.collect_all_metrics()
                    
                    # Salva no banco
                    self._save_metrics_to_db(metrics)
                    
                    # Verifica alertas
                    self.alert_manager.check_alerts(metrics)
                    
                    # Atualiza cache
                    self._update_dashboard_cache(metrics)
                    
                    # Envia para WebSocket
                    if self.config.get('enable_websockets'):
                        self._broadcast_metrics_update(metrics)
                    
                    time.sleep(self.config.get('update_interval', 30))
                    
                except Exception as e:
                    logger.error(f"Erro no worker de métricas: {e}")
                    time.sleep(10)
        
        # Worker de limpeza
        def cleanup_worker():
            while True:
                try:
                    self._cleanup_old_data()
                    time.sleep(3600)  # A cada hora
                except Exception as e:
                    logger.error(f"Erro no worker de limpeza: {e}")
                    time.sleep(300)
        
        # Inicia threads
        metrics_thread = threading.Thread(target=metrics_worker, daemon=True)
        metrics_thread.start()
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
    
    def _save_metrics_to_db(self, metrics: List[SystemMetric]):
        """Salva métricas no banco de dados."""
        if not metrics:
            return
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        for metric in metrics:
            cursor.execute('''
                INSERT INTO metrics_history 
                (name, value, unit, category, metadata, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                metric.name, metric.value, metric.unit, metric.category,
                json.dumps(metric.metadata) if metric.metadata else None,
                metric.timestamp
            ))
        
        conn.commit()
        conn.close()
    
    def _update_dashboard_cache(self, metrics: List[SystemMetric]):
        """Atualiza cache do dashboard."""
        self.dashboard_cache = {
            'system_overview': self.dashboard_generator.create_system_overview_chart(
                self.metrics_collector.get_recent_metrics(60)
            ),
            'ai_performance': self.dashboard_generator.create_ai_performance_chart(
                self.metrics_collector.get_recent_metrics(60)
            ),
            'business_metrics': self.dashboard_generator.create_business_metrics_chart(
                self.metrics_collector.get_recent_metrics(10)
            ),
            'alerts_summary': self.dashboard_generator.create_alerts_summary(
                list(self.alert_manager.alert_history)
            ),
            'last_update': datetime.now().isoformat()
        }
    
    def _broadcast_metrics_update(self, metrics: List[SystemMetric]):
        """Transmite atualizações via WebSocket."""
        try:
            # Prepara dados resumidos para WebSocket
            metrics_summary = {}
            for metric in metrics:
                category = metric.category
                if category not in metrics_summary:
                    metrics_summary[category] = {}
                
                metrics_summary[category][metric.name] = {
                    'value': metric.value,
                    'unit': metric.unit,
                    'timestamp': metric.timestamp.isoformat()
                }
            
            self.socketio.emit('metrics_update', {
                'timestamp': datetime.now().isoformat(),
                'metrics': metrics_summary
            })
            
        except Exception as e:
            logger.error(f"Erro ao transmitir métricas: {e}")
    
    def _cleanup_old_data(self):
        """Limpa dados antigos."""
        retention_days = self.config.get('metrics_retention_days', 30)
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute(
            'DELETE FROM metrics_history WHERE timestamp < ?',
            (cutoff_date,)
        )
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        if deleted_count > 0:
            logger.info(f"Limpeza: {deleted_count} métricas antigas removidas")
    
    def set_ai_systems(self, trainer=None, memory_manager=None, 
                      optimizer=None, analyzer=None):
        """Configura sistemas de IA para monitoramento."""
        self.metrics_collector.set_ai_systems(trainer, memory_manager, optimizer, analyzer)
    
    def add_custom_widget(self, widget: DashboardWidget):
        """Adiciona widget personalizado."""
        self.dashboard_widgets.append(widget)
        logger.info(f"Widget adicionado: {widget.title}")
    
    def generate_report(self, hours: int = 24) -> Dict[str, Any]:
        """Gera relatório executivo."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Métricas resumidas
        cursor.execute('''
            SELECT category, name, AVG(value) as avg_value, MIN(value) as min_value, 
                   MAX(value) as max_value, COUNT(*) as count
            FROM metrics_history 
            WHERE timestamp > ?
            GROUP BY category, name
        ''', (cutoff_time,))
        
        metrics_summary = []
        for row in cursor.fetchall():
            metrics_summary.append({
                'category': row[0],
                'name': row[1],
                'avg_value': row[2],
                'min_value': row[3],
                'max_value': row[4],
                'count': row[5]
            })
        
        conn.close()
        
        # Alertas no período
        recent_alerts = [
            alert for alert in self.alert_manager.alert_history
            if datetime.fromisoformat(alert['timestamp']) > cutoff_time
        ]
        
        report = {
            'period_hours': hours,
            'generated_at': datetime.now().isoformat(),
            'metrics_summary': metrics_summary,
            'alerts_summary': {
                'total_alerts': len(recent_alerts),
                'critical_alerts': len([a for a in recent_alerts if a['severity'] == 'critical']),
                'warning_alerts': len([a for a in recent_alerts if a['severity'] == 'warning'])
            },
            'system_health': self._calculate_system_health(metrics_summary),
            'recommendations': self._generate_recommendations(metrics_summary, recent_alerts)
        }
        
        return report
    
    def _calculate_system_health(self, metrics_summary: List[Dict]) -> str:
        """Calcula saúde geral do sistema."""
        # Heurística simples baseada em métricas críticas
        critical_metrics = {
            'cpu_usage': 80,    # % máximo aceitável
            'memory_usage': 85, # % máximo aceitável
            'disk_usage': 90    # % máximo aceitável
        }
        
        health_score = 100
        
        for metric in metrics_summary:
            if metric['name'] in critical_metrics:
                threshold = critical_metrics[metric['name']]
                if metric['avg_value'] > threshold:
                    health_score -= 20
                elif metric['avg_value'] > threshold * 0.8:
                    health_score -= 10
        
        if health_score >= 90:
            return 'excellent'
        elif health_score >= 70:
            return 'good'
        elif health_score >= 50:
            return 'fair'
        else:
            return 'poor'
    
    def _generate_recommendations(self, metrics_summary: List[Dict], 
                                 recent_alerts: List[Dict]) -> List[str]:
        """Gera recomendações."""
        recommendations = []
        
        # Analisa métricas para recomendações
        for metric in metrics_summary:
            if metric['name'] == 'cpu_usage' and metric['avg_value'] > 80:
                recommendations.append("Considere otimizar processos ou aumentar recursos de CPU")
            
            if metric['name'] == 'memory_usage' and metric['avg_value'] > 85:
                recommendations.append("Memória alta detectada - verificar vazamentos ou aumentar RAM")
            
            if metric['name'] == 'ai_avg_response_time' and metric['avg_value'] > 3:
                recommendations.append("Tempo de resposta da IA alto - considere otimização de modelos")
        
        # Analisa alertas
        if len(recent_alerts) > 10:
            recommendations.append("Alto número de alertas - revisar thresholds e regras")
        
        return recommendations
    
    def run(self, host: Optional[str] = None, port: Optional[int] = None, 
            debug: Optional[bool] = None):
        """Executa o servidor do dashboard."""
        host = host or self.config.get('host', '0.0.0.0')
        port = port or self.config.get('port', 8080)
        debug = debug if debug is not None else self.config.get('debug', False)
        
        logger.info(f"Iniciando Dashboard Monitor em {host}:{port}")
        
        if self.config.get('enable_websockets'):
            self.socketio.run(self.app, host=host, port=port, debug=debug)
        else:
            self.app.run(host=host, port=port, debug=debug)

# Função de teste
def main():
    """Função principal para teste."""
    monitor = DashboardMonitor()
    
    # Adiciona algumas regras de alerta para teste
    cpu_alert = AlertRule(
        id='cpu_high',
        name='High CPU Usage',
        metric='cpu_usage',
        condition='>',
        threshold=80.0,
        duration_minutes=5,
        severity='warning',
        channels=['email']
    )
    monitor.alert_manager.add_alert_rule(cpu_alert)
    
    try:
        monitor.run(debug=True)
    except KeyboardInterrupt:
        logger.info("Parando Dashboard Monitor...")

if __name__ == "__main__":
    main()