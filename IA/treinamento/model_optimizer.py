"""
Model Optimizer - Sistema de Otimização de Modelos de IA
========================================================

Sistema avançado para otimização automática de performance de modelos,
ajuste de parâmetros, e configuração dinâmica baseada em métricas.

Funcionalidades principais:
- Otimização automática de parâmetros
- Análise de performance em tempo real
- Configuração dinâmica baseada em carga
- Balanceamento de recursos
- Ajuste automático de temperatura e top_p
- Monitoramento de qualidade de resposta
- Sistema de A/B testing para parâmetros
- Cache inteligente de configurações otimizadas
"""

import logging
import time
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import numpy as np
from scipy.optimize import minimize
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import psutil
import sqlite3
from pathlib import Path
import pickle
import hashlib
import asyncio
import yaml
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ModelPerformanceMetrics:
    """Métricas de performance de um modelo."""
    model_name: str
    response_time: float
    memory_usage: float
    cpu_usage: float
    quality_score: float
    error_rate: float
    throughput: float
    user_satisfaction: float
    context_retention: float
    coherence_score: float
    timestamp: datetime

@dataclass
class OptimizationConfig:
    """Configuração de otimização."""
    model_name: str
    temperature: float
    top_p: float
    max_tokens: int
    frequency_penalty: float
    presence_penalty: float
    stop_sequences: List[str]
    performance_target: float
    quality_threshold: float
    optimization_strategy: str  # 'performance', 'quality', 'balanced'
    last_updated: datetime
    success_rate: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return asdict(self)

@dataclass
class ABTestConfig:
    """Configuração de teste A/B."""
    test_id: str
    model_name: str
    config_a: OptimizationConfig
    config_b: OptimizationConfig
    traffic_split: float  # 0.0-1.0, percentual para config_a
    duration_hours: int
    start_time: datetime
    status: str  # 'running', 'completed', 'stopped'
    results: Dict[str, Any] = None

class QualityAnalyzer:
    """Analisador de qualidade de resposta."""
    
    def __init__(self):
        self.coherence_keywords = [
            'então', 'portanto', 'assim', 'dessa forma', 'consequentemente',
            'primeiro', 'segundo', 'finalmente', 'além disso', 'por outro lado'
        ]
        
        self.quality_indicators = {
            'positive': ['claro', 'específico', 'detalhado', 'preciso', 'útil'],
            'negative': ['vago', 'confuso', 'incompleto', 'incorreto', 'irrelevante']
        }
    
    def analyze_response_quality(self, prompt: str, response: str, 
                                context: Dict[str, Any] = None) -> float:
        """Analisa qualidade da resposta (0.0-1.0)."""
        if not response or not response.strip():
            return 0.0
        
        scores = []
        
        # Análise de relevância
        relevance_score = self._analyze_relevance(prompt, response)
        scores.append(relevance_score * 0.3)
        
        # Análise de coerência
        coherence_score = self._analyze_coherence(response)
        scores.append(coherence_score * 0.25)
        
        # Análise de completude
        completeness_score = self._analyze_completeness(prompt, response)
        scores.append(completeness_score * 0.2)
        
        # Análise de clareza
        clarity_score = self._analyze_clarity(response)
        scores.append(clarity_score * 0.15)
        
        # Análise de utilidade
        utility_score = self._analyze_utility(response)
        scores.append(utility_score * 0.1)
        
        return sum(scores)
    
    def _analyze_relevance(self, prompt: str, response: str) -> float:
        """Analisa relevância da resposta em relação ao prompt."""
        prompt_words = set(prompt.lower().split())
        response_words = set(response.lower().split())
        
        # Remove stop words comuns
        stop_words = {'o', 'a', 'de', 'do', 'da', 'em', 'um', 'uma', 'para', 'com', 'por'}
        prompt_words -= stop_words
        response_words -= stop_words
        
        if not prompt_words:
            return 0.5
        
        overlap = len(prompt_words.intersection(response_words))
        return min(1.0, overlap / len(prompt_words))
    
    def _analyze_coherence(self, response: str) -> float:
        """Analisa coerência da resposta."""
        score = 0.5  # Base score
        
        # Verifica conectores lógicos
        coherence_count = sum(1 for keyword in self.coherence_keywords 
                             if keyword in response.lower())
        score += min(0.3, coherence_count * 0.1)
        
        # Verifica estrutura de parágrafos
        sentences = response.split('.')
        if len(sentences) > 1:
            score += 0.1
        
        # Verifica repetição excessiva
        words = response.lower().split()
        unique_words = set(words)
        if len(words) > 0:
            repetition_ratio = len(unique_words) / len(words)
            score += repetition_ratio * 0.1
        
        return min(1.0, score)
    
    def _analyze_completeness(self, prompt: str, response: str) -> float:
        """Analisa completude da resposta."""
        # Heurística simples baseada no comprimento
        prompt_length = len(prompt.split())
        response_length = len(response.split())
        
        if prompt_length == 0:
            return 0.5
        
        # Respostas muito curtas ou muito longas podem ser problemáticas
        ideal_ratio = 2.0  # Resposta 2x maior que prompt
        actual_ratio = response_length / prompt_length
        
        if actual_ratio < 0.5:
            return actual_ratio / 0.5 * 0.5
        elif actual_ratio > 10:
            return max(0.2, 1.0 - (actual_ratio - 10) * 0.1)
        else:
            return min(1.0, actual_ratio / ideal_ratio)
    
    def _analyze_clarity(self, response: str) -> float:
        """Analisa clareza da resposta."""
        score = 0.5
        
        # Verifica indicadores positivos
        for indicator in self.quality_indicators['positive']:
            if indicator in response.lower():
                score += 0.1
        
        # Penaliza indicadores negativos
        for indicator in self.quality_indicators['negative']:
            if indicator in response.lower():
                score -= 0.1
        
        # Verifica pontuação adequada
        if '.' in response and ',' in response:
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _analyze_utility(self, response: str) -> float:
        """Analisa utilidade prática da resposta."""
        utility_keywords = [
            'como', 'passos', 'primeiro', 'exemplo', 'tutorial',
            'configurar', 'instalar', 'executar', 'usar'
        ]
        
        utility_count = sum(1 for keyword in utility_keywords 
                           if keyword in response.lower())
        
        return min(1.0, utility_count * 0.2 + 0.3)

class ParameterOptimizer:
    """Otimizador de parâmetros de modelo."""
    
    def __init__(self):
        self.optimization_history = deque(maxlen=1000)
        self.best_configs = {}
        
    def optimize_parameters(self, model_name: str, 
                          performance_history: List[ModelPerformanceMetrics],
                          optimization_target: str = 'balanced') -> OptimizationConfig:
        """Otimiza parâmetros do modelo baseado no histórico."""
        
        if not performance_history:
            return self._get_default_config(model_name)
        
        # Analisa padrões no histórico
        patterns = self._analyze_performance_patterns(performance_history)
        
        # Determina estratégia de otimização
        if optimization_target == 'performance':
            target_function = self._performance_objective
        elif optimization_target == 'quality':
            target_function = self._quality_objective
        else:
            target_function = self._balanced_objective
        
        # Busca configuração ótima
        optimal_config = self._search_optimal_config(
            model_name, patterns, target_function
        )
        
        return optimal_config
    
    def _analyze_performance_patterns(self, 
                                    history: List[ModelPerformanceMetrics]) -> Dict[str, Any]:
        """Analisa padrões no histórico de performance."""
        if not history:
            return {}
        
        # Agrupa métricas
        response_times = [m.response_time for m in history]
        quality_scores = [m.quality_score for m in history]
        memory_usage = [m.memory_usage for m in history]
        error_rates = [m.error_rate for m in history]
        
        patterns = {
            'avg_response_time': np.mean(response_times),
            'std_response_time': np.std(response_times),
            'avg_quality': np.mean(quality_scores),
            'std_quality': np.std(quality_scores),
            'avg_memory': np.mean(memory_usage),
            'avg_error_rate': np.mean(error_rates),
            'trend_response_time': self._calculate_trend(response_times),
            'trend_quality': self._calculate_trend(quality_scores),
            'peak_hours': self._identify_peak_hours(history)
        }
        
        return patterns
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calcula tendência dos valores (positiva = crescendo)."""
        if len(values) < 2:
            return 0.0
        
        x = np.arange(len(values))
        y = np.array(values)
        
        # Regressão linear simples
        slope = np.polyfit(x, y, 1)[0]
        return slope
    
    def _identify_peak_hours(self, history: List[ModelPerformanceMetrics]) -> List[int]:
        """Identifica horários de pico de uso."""
        hour_counts = defaultdict(int)
        
        for metric in history:
            hour = metric.timestamp.hour
            hour_counts[hour] += 1
        
        # Retorna horas com uso acima da média
        avg_count = np.mean(list(hour_counts.values()))
        peak_hours = [hour for hour, count in hour_counts.items() 
                     if count > avg_count * 1.2]
        
        return peak_hours
    
    def _search_optimal_config(self, model_name: str, patterns: Dict[str, Any],
                              objective_function: callable) -> OptimizationConfig:
        """Busca configuração ótima usando otimização."""
        
        # Espaço de busca para parâmetros
        parameter_bounds = {
            'temperature': (0.1, 1.0),
            'top_p': (0.1, 1.0),
            'max_tokens': (100, 4096),
            'frequency_penalty': (0.0, 2.0),
            'presence_penalty': (0.0, 2.0)
        }
        
        # Configuração inicial (ponto de partida)
        initial_config = self._get_default_config(model_name)
        initial_params = [
            initial_config.temperature,
            initial_config.top_p,
            initial_config.max_tokens,
            initial_config.frequency_penalty,
            initial_config.presence_penalty
        ]
        
        # Bounds para otimização
        bounds = [parameter_bounds[param] for param in 
                 ['temperature', 'top_p', 'max_tokens', 'frequency_penalty', 'presence_penalty']]
        
        try:
            # Otimização usando scipy
            result = minimize(
                lambda params: -objective_function(params, patterns),  # Maximize
                initial_params,
                bounds=bounds,
                method='L-BFGS-B'
            )
            
            optimal_params = result.x
            
        except Exception as e:
            logger.error(f"Erro na otimização: {e}")
            optimal_params = initial_params
        
        # Cria configuração otimizada
        optimized_config = OptimizationConfig(
            model_name=model_name,
            temperature=float(optimal_params[0]),
            top_p=float(optimal_params[1]),
            max_tokens=int(optimal_params[2]),
            frequency_penalty=float(optimal_params[3]),
            presence_penalty=float(optimal_params[4]),
            stop_sequences=[],
            performance_target=patterns.get('avg_response_time', 2.0),
            quality_threshold=patterns.get('avg_quality', 0.7),
            optimization_strategy='balanced',
            last_updated=datetime.now()
        )
        
        return optimized_config
    
    def _performance_objective(self, params: List[float], 
                              patterns: Dict[str, Any]) -> float:
        """Função objetivo focada em performance."""
        temperature, top_p, max_tokens, freq_penalty, pres_penalty = params
        
        # Modelo de performance baseado em heurísticas
        # Temperaturas mais baixas = respostas mais rápidas mas menos criativas
        performance_score = 1.0 - temperature * 0.3
        
        # Top_p mais baixo = menos variabilidade, mais performance
        performance_score += (1.0 - top_p) * 0.2
        
        # Tokens menores = respostas mais rápidas
        performance_score += (1.0 - max_tokens / 4096) * 0.3
        
        # Penalidades podem afetar performance
        performance_score -= (freq_penalty + pres_penalty) * 0.1
        
        return performance_score
    
    def _quality_objective(self, params: List[float], 
                          patterns: Dict[str, Any]) -> float:
        """Função objetivo focada em qualidade."""
        temperature, top_p, max_tokens, freq_penalty, pres_penalty = params
        
        # Temperatura moderada é melhor para qualidade
        quality_score = 1.0 - abs(temperature - 0.7) * 2
        
        # Top_p moderado permite criatividade controlada
        quality_score += 1.0 - abs(top_p - 0.9) * 2
        
        # Tokens suficientes para respostas completas
        if max_tokens >= 1000:
            quality_score += 0.3
        
        # Penalidades moderadas ajudam na qualidade
        optimal_penalty = 0.5
        penalty_score = 1.0 - abs(freq_penalty - optimal_penalty) - abs(pres_penalty - optimal_penalty)
        quality_score += penalty_score * 0.2
        
        return quality_score
    
    def _balanced_objective(self, params: List[float], 
                           patterns: Dict[str, Any]) -> float:
        """Função objetivo balanceada."""
        performance_score = self._performance_objective(params, patterns)
        quality_score = self._quality_objective(params, patterns)
        
        # Balanceia performance e qualidade
        return performance_score * 0.4 + quality_score * 0.6
    
    def _get_default_config(self, model_name: str) -> OptimizationConfig:
        """Retorna configuração padrão para o modelo."""
        defaults = {
            'llama3.1': {
                'temperature': 0.7,
                'top_p': 0.9,
                'max_tokens': 2048,
                'frequency_penalty': 0.0,
                'presence_penalty': 0.0
            },
            'mistral': {
                'temperature': 0.6,
                'top_p': 0.95,
                'max_tokens': 1024,
                'frequency_penalty': 0.1,
                'presence_penalty': 0.1
            },
            'codellama': {
                'temperature': 0.3,
                'top_p': 0.8,
                'max_tokens': 3072,
                'frequency_penalty': 0.2,
                'presence_penalty': 0.0
            }
        }
        
        config_data = defaults.get(model_name, defaults['llama3.1'])
        
        return OptimizationConfig(
            model_name=model_name,
            temperature=config_data['temperature'],
            top_p=config_data['top_p'],
            max_tokens=config_data['max_tokens'],
            frequency_penalty=config_data['frequency_penalty'],
            presence_penalty=config_data['presence_penalty'],
            stop_sequences=[],
            performance_target=2.0,
            quality_threshold=0.7,
            optimization_strategy='balanced',
            last_updated=datetime.now()
        )

class ABTestManager:
    """Gerenciador de testes A/B."""
    
    def __init__(self):
        self.active_tests = {}
        self.test_results = {}
        
    def create_ab_test(self, model_name: str, config_a: OptimizationConfig,
                      config_b: OptimizationConfig, duration_hours: int = 24,
                      traffic_split: float = 0.5) -> str:
        """Cria novo teste A/B."""
        
        test_id = f"ab_test_{int(time.time())}"
        
        ab_test = ABTestConfig(
            test_id=test_id,
            model_name=model_name,
            config_a=config_a,
            config_b=config_b,
            traffic_split=traffic_split,
            duration_hours=duration_hours,
            start_time=datetime.now(),
            status='running'
        )
        
        self.active_tests[test_id] = ab_test
        
        # Agenda finalização automática
        def finalize_test():
            time.sleep(duration_hours * 3600)
            if test_id in self.active_tests:
                self.finalize_test(test_id)
        
        threading.Thread(target=finalize_test, daemon=True).start()
        
        logger.info(f"Teste A/B criado: {test_id}")
        return test_id
    
    def get_test_config(self, test_id: str, user_id: str = None) -> OptimizationConfig:
        """Obtém configuração para o teste baseada no split de tráfego."""
        
        if test_id not in self.active_tests:
            raise ValueError(f"Teste {test_id} não encontrado")
        
        test = self.active_tests[test_id]
        
        if test.status != 'running':
            return test.config_a  # Default para A se não estiver rodando
        
        # Determina qual configuração usar baseado no hash do user_id
        if user_id:
            hash_value = int(hashlib.md5(user_id.encode()).hexdigest()[:8], 16)
            use_config_a = (hash_value % 100) / 100 < test.traffic_split
        else:
            use_config_a = random.random() < test.traffic_split
        
        return test.config_a if use_config_a else test.config_b
    
    def record_test_result(self, test_id: str, config_used: str,
                          metrics: ModelPerformanceMetrics):
        """Registra resultado do teste."""
        
        if test_id not in self.test_results:
            self.test_results[test_id] = {'A': [], 'B': []}
        
        self.test_results[test_id][config_used].append(metrics)
    
    def finalize_test(self, test_id: str) -> Dict[str, Any]:
        """Finaliza teste e calcula resultados."""
        
        if test_id not in self.active_tests:
            return {'error': 'Teste não encontrado'}
        
        test = self.active_tests[test_id]
        test.status = 'completed'
        
        results_a = self.test_results.get(test_id, {}).get('A', [])
        results_b = self.test_results.get(test_id, {}).get('B', [])
        
        if not results_a or not results_b:
            return {'error': 'Dados insuficientes para análise'}
        
        # Calcula estatísticas
        stats_a = self._calculate_test_stats(results_a)
        stats_b = self._calculate_test_stats(results_b)
        
        # Determina vencedor
        winner = self._determine_winner(stats_a, stats_b)
        
        results = {
            'test_id': test_id,
            'model_name': test.model_name,
            'duration_hours': test.duration_hours,
            'traffic_split': test.traffic_split,
            'config_a_stats': stats_a,
            'config_b_stats': stats_b,
            'winner': winner,
            'confidence': self._calculate_confidence(stats_a, stats_b),
            'recommendation': self._generate_recommendation(winner, stats_a, stats_b)
        }
        
        test.results = results
        
        logger.info(f"Teste A/B finalizado: {test_id}, Vencedor: {winner}")
        return results
    
    def _calculate_test_stats(self, metrics: List[ModelPerformanceMetrics]) -> Dict[str, float]:
        """Calcula estatísticas dos resultados do teste."""
        
        response_times = [m.response_time for m in metrics]
        quality_scores = [m.quality_score for m in metrics]
        error_rates = [m.error_rate for m in metrics]
        
        return {
            'sample_size': len(metrics),
            'avg_response_time': np.mean(response_times),
            'std_response_time': np.std(response_times),
            'avg_quality': np.mean(quality_scores),
            'std_quality': np.std(quality_scores),
            'avg_error_rate': np.mean(error_rates),
            'throughput': len(metrics) / (max([m.timestamp for m in metrics]) - min([m.timestamp for m in metrics])).total_seconds() if len(metrics) > 1 else 0
        }
    
    def _determine_winner(self, stats_a: Dict[str, float], 
                         stats_b: Dict[str, float]) -> str:
        """Determina vencedor do teste."""
        
        # Score composto considerando múltiplas métricas
        score_a = (
            (1.0 / (stats_a['avg_response_time'] + 0.1)) * 0.3 +
            stats_a['avg_quality'] * 0.4 +
            (1.0 - stats_a['avg_error_rate']) * 0.3
        )
        
        score_b = (
            (1.0 / (stats_b['avg_response_time'] + 0.1)) * 0.3 +
            stats_b['avg_quality'] * 0.4 +
            (1.0 - stats_b['avg_error_rate']) * 0.3
        )
        
        return 'A' if score_a > score_b else 'B'
    
    def _calculate_confidence(self, stats_a: Dict[str, float], 
                            stats_b: Dict[str, float]) -> float:
        """Calcula nível de confiança do resultado."""
        
        # Simples heurística baseada no tamanho da amostra e diferença
        min_sample_size = min(stats_a['sample_size'], stats_b['sample_size'])
        
        if min_sample_size < 30:
            return 0.5  # Baixa confiança
        elif min_sample_size < 100:
            return 0.7  # Confiança moderada
        else:
            return 0.9  # Alta confiança
    
    def _generate_recommendation(self, winner: str, stats_a: Dict[str, float],
                               stats_b: Dict[str, float]) -> str:
        """Gera recomendação baseada nos resultados."""
        
        winning_stats = stats_a if winner == 'A' else stats_b
        losing_stats = stats_b if winner == 'A' else stats_a
        
        improvement_quality = (winning_stats['avg_quality'] - losing_stats['avg_quality']) * 100
        improvement_speed = (losing_stats['avg_response_time'] - winning_stats['avg_response_time']) / losing_stats['avg_response_time'] * 100
        
        return f"Configuração {winner} venceu com {improvement_quality:.1f}% melhoria na qualidade e {improvement_speed:.1f}% melhoria na velocidade."

class ModelOptimizer:
    """Otimizador principal de modelos."""
    
    def __init__(self, data_dir: str = "./data/optimization"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Banco de dados para histórico
        self.db_path = self.data_dir / "optimization.db"
        self._init_database()
        
        # Componentes especializados
        self.quality_analyzer = QualityAnalyzer()
        self.parameter_optimizer = ParameterOptimizer()
        self.ab_test_manager = ABTestManager()
        
        # Cache de configurações
        self.config_cache = {}
        self.metrics_cache = deque(maxlen=10000)
        
        # Lock para thread safety
        self.lock = threading.Lock()
        
        # Worker para otimização contínua
        self._start_optimization_worker()
        
        logger.info("ModelOptimizer inicializado com sucesso")
    
    def _init_database(self):
        """Inicializa banco de dados."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Tabela de métricas de performance
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                response_time REAL NOT NULL,
                memory_usage REAL NOT NULL,
                cpu_usage REAL NOT NULL,
                quality_score REAL NOT NULL,
                error_rate REAL NOT NULL,
                throughput REAL NOT NULL,
                user_satisfaction REAL NOT NULL,
                context_retention REAL NOT NULL,
                coherence_score REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de configurações otimizadas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS optimization_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                temperature REAL NOT NULL,
                top_p REAL NOT NULL,
                max_tokens INTEGER NOT NULL,
                frequency_penalty REAL NOT NULL,
                presence_penalty REAL NOT NULL,
                stop_sequences TEXT,
                performance_target REAL NOT NULL,
                quality_threshold REAL NOT NULL,
                optimization_strategy TEXT NOT NULL,
                success_rate REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de testes A/B
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ab_tests (
                test_id TEXT PRIMARY KEY,
                model_name TEXT NOT NULL,
                config_a TEXT NOT NULL,
                config_b TEXT NOT NULL,
                traffic_split REAL NOT NULL,
                duration_hours INTEGER NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                status TEXT NOT NULL,
                results TEXT,
                winner TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _start_optimization_worker(self):
        """Inicia worker para otimização contínua."""
        def optimization_worker():
            while True:
                try:
                    self._run_optimization_cycle()
                    time.sleep(3600)  # Otimiza a cada hora
                except Exception as e:
                    logger.error(f"Erro no worker de otimização: {e}")
                    time.sleep(300)  # Retry em 5 minutos
        
        worker_thread = threading.Thread(target=optimization_worker, daemon=True)
        worker_thread.start()
    
    def record_performance_metrics(self, metrics: ModelPerformanceMetrics):
        """Registra métricas de performance."""
        with self.lock:
            self.metrics_cache.append(metrics)
        
        # Salva no banco
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO performance_metrics 
            (model_name, response_time, memory_usage, cpu_usage, quality_score,
             error_rate, throughput, user_satisfaction, context_retention, 
             coherence_score, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            metrics.model_name, metrics.response_time, metrics.memory_usage,
            metrics.cpu_usage, metrics.quality_score, metrics.error_rate,
            metrics.throughput, metrics.user_satisfaction, metrics.context_retention,
            metrics.coherence_score, metrics.timestamp
        ))
        
        conn.commit()
        conn.close()
    
    def get_optimized_config(self, model_name: str, 
                           optimization_target: str = 'balanced') -> OptimizationConfig:
        """Obtém configuração otimizada para o modelo."""
        
        # Verifica cache
        cache_key = f"{model_name}:{optimization_target}"
        if cache_key in self.config_cache:
            cached_config, cache_time = self.config_cache[cache_key]
            if datetime.now() - cache_time < timedelta(hours=1):  # Cache válido por 1 hora
                return cached_config
        
        # Busca histórico de performance
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM performance_metrics 
            WHERE model_name = ? 
            ORDER BY timestamp DESC 
            LIMIT 1000
        ''', (model_name,))
        
        rows = cursor.fetchall()
        conn.close()
        
        # Converte para objetos de métricas
        performance_history = []
        for row in rows:
            metrics = ModelPerformanceMetrics(
                model_name=row[1],
                response_time=row[2],
                memory_usage=row[3],
                cpu_usage=row[4],
                quality_score=row[5],
                error_rate=row[6],
                throughput=row[7],
                user_satisfaction=row[8],
                context_retention=row[9],
                coherence_score=row[10],
                timestamp=datetime.fromisoformat(row[11])
            )
            performance_history.append(metrics)
        
        # Otimiza parâmetros
        optimized_config = self.parameter_optimizer.optimize_parameters(
            model_name, performance_history, optimization_target
        )
        
        # Atualiza cache
        self.config_cache[cache_key] = (optimized_config, datetime.now())
        
        # Salva configuração no banco
        self._save_optimization_config(optimized_config)
        
        return optimized_config
    
    def _save_optimization_config(self, config: OptimizationConfig):
        """Salva configuração otimizada no banco."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO optimization_configs 
            (model_name, temperature, top_p, max_tokens, frequency_penalty,
             presence_penalty, stop_sequences, performance_target, quality_threshold,
             optimization_strategy, success_rate, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            config.model_name, config.temperature, config.top_p, config.max_tokens,
            config.frequency_penalty, config.presence_penalty, 
            json.dumps(config.stop_sequences), config.performance_target,
            config.quality_threshold, config.optimization_strategy,
            config.success_rate, config.last_updated
        ))
        
        conn.commit()
        conn.close()
    
    def analyze_response_quality(self, prompt: str, response: str, 
                               model_name: str, context: Dict[str, Any] = None) -> float:
        """Analisa qualidade de uma resposta."""
        return self.quality_analyzer.analyze_response_quality(prompt, response, context)
    
    def create_ab_test(self, model_name: str, current_config: OptimizationConfig,
                      experimental_config: OptimizationConfig,
                      duration_hours: int = 24) -> str:
        """Cria teste A/B para comparar configurações."""
        
        test_id = self.ab_test_manager.create_ab_test(
            model_name, current_config, experimental_config, duration_hours
        )
        
        # Salva no banco
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO ab_tests 
            (test_id, model_name, config_a, config_b, traffic_split, 
             duration_hours, start_time, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            test_id, model_name, json.dumps(current_config.to_dict()),
            json.dumps(experimental_config.to_dict()), 0.5,
            duration_hours, datetime.now(), 'running'
        ))
        
        conn.commit()
        conn.close()
        
        return test_id
    
    def get_test_config(self, test_id: str, user_id: str = None) -> OptimizationConfig:
        """Obtém configuração para teste A/B."""
        return self.ab_test_manager.get_test_config(test_id, user_id)
    
    def finalize_ab_test(self, test_id: str) -> Dict[str, Any]:
        """Finaliza teste A/B e retorna resultados."""
        results = self.ab_test_manager.finalize_test(test_id)
        
        # Atualiza banco
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE ab_tests 
            SET end_time = ?, status = ?, results = ?, winner = ?
            WHERE test_id = ?
        ''', (
            datetime.now(), 'completed', json.dumps(results),
            results.get('winner', 'Unknown'), test_id
        ))
        
        conn.commit()
        conn.close()
        
        return results
    
    def _run_optimization_cycle(self):
        """Executa ciclo de otimização automática."""
        try:
            # Identifica modelos que precisam de otimização
            models_to_optimize = self._identify_models_needing_optimization()
            
            for model_name in models_to_optimize:
                # Otimiza configuração
                current_config = self.get_optimized_config(model_name, 'balanced')
                
                # Cria configuração experimental
                experimental_config = self._generate_experimental_config(current_config)
                
                # Inicia teste A/B se configuração experimental for promissora
                if self._is_experimental_config_promising(experimental_config, current_config):
                    test_id = self.create_ab_test(model_name, current_config, experimental_config, 6)
                    logger.info(f"Teste A/B automático criado para {model_name}: {test_id}")
            
            logger.info("Ciclo de otimização automática concluído")
            
        except Exception as e:
            logger.error(f"Erro no ciclo de otimização: {e}")
    
    def _identify_models_needing_optimization(self) -> List[str]:
        """Identifica modelos que precisam de otimização."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Busca modelos com performance degradada nas últimas 24h
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        cursor.execute('''
            SELECT model_name, AVG(quality_score), AVG(response_time), AVG(error_rate)
            FROM performance_metrics 
            WHERE timestamp > ?
            GROUP BY model_name
            HAVING AVG(quality_score) < 0.7 OR AVG(response_time) > 3.0 OR AVG(error_rate) > 0.1
        ''', (cutoff_time,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [row[0] for row in results]
    
    def _generate_experimental_config(self, base_config: OptimizationConfig) -> OptimizationConfig:
        """Gera configuração experimental baseada na configuração atual."""
        
        # Pequenas variações nos parâmetros
        experimental_config = OptimizationConfig(
            model_name=base_config.model_name,
            temperature=max(0.1, min(1.0, base_config.temperature + random.uniform(-0.1, 0.1))),
            top_p=max(0.1, min(1.0, base_config.top_p + random.uniform(-0.05, 0.05))),
            max_tokens=max(100, min(4096, base_config.max_tokens + random.randint(-200, 200))),
            frequency_penalty=max(0.0, min(2.0, base_config.frequency_penalty + random.uniform(-0.1, 0.1))),
            presence_penalty=max(0.0, min(2.0, base_config.presence_penalty + random.uniform(-0.1, 0.1))),
            stop_sequences=base_config.stop_sequences.copy(),
            performance_target=base_config.performance_target,
            quality_threshold=base_config.quality_threshold,
            optimization_strategy=base_config.optimization_strategy,
            last_updated=datetime.now()
        )
        
        return experimental_config
    
    def _is_experimental_config_promising(self, experimental: OptimizationConfig,
                                        current: OptimizationConfig) -> bool:
        """Verifica se configuração experimental é promissora."""
        
        # Heurística simples: se a diferença é significativa mas não extrema
        temp_diff = abs(experimental.temperature - current.temperature)
        top_p_diff = abs(experimental.top_p - current.top_p)
        
        return 0.05 < temp_diff < 0.3 or 0.02 < top_p_diff < 0.2
    
    def get_optimization_statistics(self) -> Dict[str, Any]:
        """Obtém estatísticas de otimização."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Estatísticas de performance
        cursor.execute('''
            SELECT 
                COUNT(*) as total_metrics,
                AVG(quality_score) as avg_quality,
                AVG(response_time) as avg_response_time,
                AVG(error_rate) as avg_error_rate
            FROM performance_metrics 
            WHERE timestamp > datetime('now', '-7 days')
        ''')
        
        performance_stats = cursor.fetchone()
        
        # Estatísticas de testes A/B
        cursor.execute('''
            SELECT 
                COUNT(*) as total_tests,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_tests,
                COUNT(CASE WHEN winner = 'A' THEN 1 END) as config_a_wins,
                COUNT(CASE WHEN winner = 'B' THEN 1 END) as config_b_wins
            FROM ab_tests
        ''')
        
        test_stats = cursor.fetchone()
        
        conn.close()
        
        return {
            'performance': {
                'total_metrics': performance_stats[0],
                'avg_quality': performance_stats[1] or 0,
                'avg_response_time': performance_stats[2] or 0,
                'avg_error_rate': performance_stats[3] or 0
            },
            'ab_testing': {
                'total_tests': test_stats[0],
                'completed_tests': test_stats[1],
                'config_a_wins': test_stats[2],
                'config_b_wins': test_stats[3],
                'improvement_rate': (test_stats[3] / max(1, test_stats[1])) * 100 if test_stats[1] > 0 else 0
            },
            'cache_stats': {
                'cached_configs': len(self.config_cache),
                'metrics_in_memory': len(self.metrics_cache)
            }
        }

# Função de teste
def main():
    """Função principal para teste."""
    optimizer = ModelOptimizer()
    
    # Simula algumas métricas
    for i in range(10):
        metrics = ModelPerformanceMetrics(
            model_name='llama3.1',
            response_time=random.uniform(1.0, 3.0),
            memory_usage=random.uniform(500, 1500),
            cpu_usage=random.uniform(20, 80),
            quality_score=random.uniform(0.6, 0.9),
            error_rate=random.uniform(0.0, 0.1),
            throughput=random.uniform(5, 15),
            user_satisfaction=random.uniform(0.7, 1.0),
            context_retention=random.uniform(0.8, 1.0),
            coherence_score=random.uniform(0.7, 0.95),
            timestamp=datetime.now() - timedelta(hours=i)
        )
        optimizer.record_performance_metrics(metrics)
    
    # Testa otimização
    config = optimizer.get_optimized_config('llama3.1', 'balanced')
    print("Configuração otimizada:")
    print(json.dumps(config.to_dict(), indent=2, default=str))
    
    # Testa análise de qualidade
    quality = optimizer.analyze_response_quality(
        "Como configurar uma automação?",
        "Para configurar uma automação, primeiro você deve acessar o painel de controle, então selecionar 'Nova Automação' e definir os parâmetros necessários. O sistema irá guiá-lo através de cada etapa."
    )
    print(f"Qualidade da resposta: {quality:.2f}")
    
    # Estatísticas
    stats = optimizer.get_optimization_statistics()
    print("Estatísticas de otimização:")
    print(json.dumps(stats, indent=2, default=str))

if __name__ == "__main__":
    main()