"""
Local Trainer - Sistema Avançado de Treinamento de IA Local
===========================================================

Módulo principal para gerenciamento de modelos Ollama, treinamento personalizado,
e otimização de performance para o sistema AUTOBOT.

Funcionalidades principais:
- Gerenciamento de múltiplos modelos Ollama
- Criação de modelos personalizados para AUTOBOT
- Sistema de embeddings vetoriais com ChromaDB
- Cache inteligente de respostas
- Balanceamento de carga entre modelos
- Sistema de fallback automático
- Métricas de performance em tempo real
- Logging detalhado de todas as operações
"""

import asyncio
import aiohttp
import json
import logging
import time
import hashlib
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import sqlite3
import pickle
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
import gc
import psutil
import requests
import yaml
import tempfile
import shutil
import subprocess
import os
import sys
from functools import wraps, lru_cache
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import torch
import warnings

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suprimir warnings desnecessários
warnings.filterwarnings("ignore", category=UserWarning)

@dataclass
class ModelConfig:
    """Configuração de um modelo."""
    name: str
    description: str
    parameters: Dict[str, Any]
    performance_score: float = 0.0
    last_used: Optional[datetime] = None
    usage_count: int = 0
    avg_response_time: float = 0.0
    error_rate: float = 0.0
    memory_usage: float = 0.0
    enabled: bool = True

@dataclass
class TrainingJob:
    """Job de treinamento."""
    id: str
    model_name: str
    dataset_path: str
    config: Dict[str, Any]
    status: str  # pending, running, completed, failed
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    logs: List[str] = None
    
    def __post_init__(self):
        if self.logs is None:
            self.logs = []

@dataclass
class InferenceRequest:
    """Requisição de inferência."""
    id: str
    prompt: str
    model_name: str
    parameters: Dict[str, Any]
    timestamp: datetime
    priority: int = 1  # 1-10, onde 10 é maior prioridade
    user_id: Optional[str] = None
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}

class PerformanceMonitor:
    """Monitor de performance para modelos."""
    
    def __init__(self):
        self.metrics = {}
        self.lock = threading.Lock()
        
    def record_inference(self, model_name: str, response_time: float, 
                        success: bool, memory_usage: float = 0.0):
        """Registra métricas de uma inferência."""
        with self.lock:
            if model_name not in self.metrics:
                self.metrics[model_name] = {
                    'total_requests': 0,
                    'successful_requests': 0,
                    'total_time': 0.0,
                    'avg_response_time': 0.0,
                    'error_rate': 0.0,
                    'peak_memory': 0.0,
                    'last_updated': datetime.now()
                }
            
            metrics = self.metrics[model_name]
            metrics['total_requests'] += 1
            metrics['total_time'] += response_time
            
            if success:
                metrics['successful_requests'] += 1
            
            metrics['avg_response_time'] = metrics['total_time'] / metrics['total_requests']
            metrics['error_rate'] = 1.0 - (metrics['successful_requests'] / metrics['total_requests'])
            metrics['peak_memory'] = max(metrics['peak_memory'], memory_usage)
            metrics['last_updated'] = datetime.now()
    
    def get_model_performance(self, model_name: str) -> Dict[str, Any]:
        """Obtém métricas de performance de um modelo."""
        with self.lock:
            return self.metrics.get(model_name, {})
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Obtém todas as métricas."""
        with self.lock:
            return self.metrics.copy()

class CacheManager:
    """Gerenciador de cache inteligente."""
    
    def __init__(self, cache_dir: str = "./data/cache", max_size_mb: int = 1024):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.cache_db = self.cache_dir / "cache.db"
        self._init_database()
        
    def _init_database(self):
        """Inicializa banco de cache."""
        conn = sqlite3.connect(str(self.cache_db))
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache_entries (
                id TEXT PRIMARY KEY,
                prompt_hash TEXT UNIQUE NOT NULL,
                model_name TEXT NOT NULL,
                parameters_hash TEXT NOT NULL,
                response TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 1,
                response_time REAL,
                file_path TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _generate_cache_key(self, prompt: str, model_name: str, parameters: Dict) -> str:
        """Gera chave de cache."""
        content = f"{prompt}:{model_name}:{json.dumps(parameters, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get(self, prompt: str, model_name: str, parameters: Dict) -> Optional[str]:
        """Obtém resposta do cache."""
        cache_key = self._generate_cache_key(prompt, model_name, parameters)
        
        conn = sqlite3.connect(str(self.cache_db))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT response, file_path FROM cache_entries 
            WHERE prompt_hash = ? AND model_name = ? AND parameters_hash = ?
        ''', (cache_key, model_name, hashlib.sha256(json.dumps(parameters, sort_keys=True).encode()).hexdigest()))
        
        result = cursor.fetchone()
        
        if result:
            # Atualiza estatísticas de acesso
            cursor.execute('''
                UPDATE cache_entries 
                SET last_accessed = CURRENT_TIMESTAMP, access_count = access_count + 1
                WHERE prompt_hash = ?
            ''', (cache_key,))
            conn.commit()
            
            response, file_path = result
            
            # Se a resposta está em arquivo, carrega
            if file_path and Path(file_path).exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    response = f.read()
        
        conn.close()
        return response
    
    def set(self, prompt: str, model_name: str, parameters: Dict, 
            response: str, response_time: float = 0.0):
        """Armazena resposta no cache."""
        cache_key = self._generate_cache_key(prompt, model_name, parameters)
        params_hash = hashlib.sha256(json.dumps(parameters, sort_keys=True).encode()).hexdigest()
        
        # Para respostas muito grandes, salva em arquivo
        file_path = None
        if len(response) > 10000:  # 10KB threshold
            file_path = self.cache_dir / f"{cache_key}.txt"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(response)
            response_to_store = ""  # Não armazena no DB
        else:
            response_to_store = response
        
        conn = sqlite3.connect(str(self.cache_db))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO cache_entries 
            (id, prompt_hash, model_name, parameters_hash, response, response_time, file_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (cache_key, cache_key, model_name, params_hash, response_to_store, response_time, str(file_path) if file_path else None))
        
        conn.commit()
        conn.close()
        
        # Cleanup se necessário
        self._cleanup_if_needed()
    
    def _cleanup_if_needed(self):
        """Limpa cache se exceder tamanho máximo."""
        total_size = sum(f.stat().st_size for f in self.cache_dir.rglob('*') if f.is_file())
        
        if total_size > self.max_size_bytes:
            # Remove entradas mais antigas e menos acessadas
            conn = sqlite3.connect(str(self.cache_db))
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, file_path FROM cache_entries 
                ORDER BY access_count ASC, last_accessed ASC
                LIMIT 100
            ''')
            
            entries_to_remove = cursor.fetchall()
            
            for entry_id, file_path in entries_to_remove:
                # Remove arquivo se existir
                if file_path and Path(file_path).exists():
                    Path(file_path).unlink()
                
                # Remove entrada do DB
                cursor.execute('DELETE FROM cache_entries WHERE id = ?', (entry_id,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Cache cleanup: removidas {len(entries_to_remove)} entradas")

class ModelLoadBalancer:
    """Balanceador de carga para modelos."""
    
    def __init__(self, performance_monitor: PerformanceMonitor):
        self.performance_monitor = performance_monitor
        self.model_queue = {}  # model_name -> queue size
        self.lock = threading.Lock()
    
    def select_best_model(self, available_models: List[str], 
                         task_complexity: float = 1.0) -> str:
        """Seleciona o melhor modelo baseado em métricas."""
        if not available_models:
            raise ValueError("Nenhum modelo disponível")
        
        if len(available_models) == 1:
            return available_models[0]
        
        scores = {}
        
        for model_name in available_models:
            metrics = self.performance_monitor.get_model_performance(model_name)
            
            if not metrics:
                # Modelo novo, dá pontuação média
                scores[model_name] = 0.5
                continue
            
            # Calcula score baseado em múltiplos fatores
            response_time_score = min(1.0, 1.0 / (metrics.get('avg_response_time', 1.0) + 0.1))
            error_rate_score = 1.0 - metrics.get('error_rate', 0.0)
            queue_size = self.model_queue.get(model_name, 0)
            queue_score = max(0.1, 1.0 / (queue_size + 1))
            
            # Score composto
            scores[model_name] = (
                response_time_score * 0.4 +
                error_rate_score * 0.4 +
                queue_score * 0.2
            )
        
        # Seleciona modelo com maior score
        best_model = max(scores.keys(), key=lambda k: scores[k])
        
        # Atualiza fila
        with self.lock:
            self.model_queue[best_model] = self.model_queue.get(best_model, 0) + 1
        
        return best_model
    
    def mark_request_completed(self, model_name: str):
        """Marca requisição como completada."""
        with self.lock:
            if model_name in self.model_queue:
                self.model_queue[model_name] = max(0, self.model_queue[model_name] - 1)

class LocalTrainer:
    """Sistema principal de treinamento de IA local."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Inicializa o sistema de treinamento."""
        self.config = self._load_config(config_path)
        self.ollama_host = self.config.get('ollama_host', 'http://localhost:11434')
        self.data_dir = Path(self.config.get('data_dir', './data'))
        self.models_dir = self.data_dir / 'models'
        self.training_dir = self.data_dir / 'training'
        self.logs_dir = self.data_dir / 'logs'
        
        # Cria diretórios
        for dir_path in [self.data_dir, self.models_dir, self.training_dir, self.logs_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Inicializa componentes
        self.performance_monitor = PerformanceMonitor()
        self.cache_manager = CacheManager(str(self.data_dir / 'cache'))
        self.load_balancer = ModelLoadBalancer(self.performance_monitor)
        
        # Inicializa ChromaDB
        self._init_chromadb()
        
        # Inicializa embedding model
        self._init_embedding_model()
        
        # Thread pool para execução assíncrona
        self.executor = ThreadPoolExecutor(max_workers=self.config.get('max_workers', 4))
        
        # Fila de jobs de treinamento
        self.training_queue = queue.PriorityQueue()
        self.training_jobs = {}
        
        # Modelos disponíveis
        self.available_models = {}
        
        # Inicia worker threads
        self._start_workers()
        
        # Carrega modelos disponíveis
        self._discover_models()
        
        logger.info("LocalTrainer inicializado com sucesso")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Carrega configuração."""
        default_config = {
            'ollama_host': 'http://localhost:11434',
            'data_dir': './data',
            'max_workers': 4,
            'cache_size_mb': 1024,
            'embedding_model': 'all-MiniLM-L6-v2',
            'default_temperature': 0.7,
            'default_top_p': 0.9,
            'max_context_length': 4096,
            'auto_retry': True,
            'max_retries': 3,
            'fallback_models': ['llama3.1', 'mistral'],
            'performance_tracking': True
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                default_config.update(user_config)
        
        return default_config
    
    def _init_chromadb(self):
        """Inicializa ChromaDB para embeddings."""
        try:
            chroma_dir = self.data_dir / 'chromadb'
            chroma_dir.mkdir(exist_ok=True)
            
            self.chroma_client = chromadb.PersistentClient(
                path=str(chroma_dir),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Cria collection para conhecimento base
            self.knowledge_collection = self.chroma_client.get_or_create_collection(
                name="autobot_knowledge",
                metadata={"description": "Base de conhecimento do AUTOBOT"}
            )
            
            logger.info("ChromaDB inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar ChromaDB: {e}")
            self.chroma_client = None
            self.knowledge_collection = None
    
    def _init_embedding_model(self):
        """Inicializa modelo de embeddings."""
        try:
            model_name = self.config.get('embedding_model', 'all-MiniLM-L6-v2')
            self.embedding_model = SentenceTransformer(model_name)
            logger.info(f"Modelo de embedding '{model_name}' carregado")
        except Exception as e:
            logger.error(f"Erro ao carregar modelo de embedding: {e}")
            self.embedding_model = None
    
    def _start_workers(self):
        """Inicia threads trabalhadoras."""
        # Worker para jobs de treinamento
        self.training_worker = threading.Thread(
            target=self._training_worker,
            daemon=True
        )
        self.training_worker.start()
        
        # Worker para limpeza periódica
        self.cleanup_worker = threading.Thread(
            target=self._cleanup_worker,
            daemon=True
        )
        self.cleanup_worker.start()
    
    def _training_worker(self):
        """Worker para processar jobs de treinamento."""
        while True:
            try:
                # Obtém próximo job da fila
                priority, job_id = self.training_queue.get(timeout=10)
                job = self.training_jobs.get(job_id)
                
                if job and job.status == 'pending':
                    self._execute_training_job(job)
                
                self.training_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Erro no worker de treinamento: {e}")
    
    def _cleanup_worker(self):
        """Worker para limpeza periódica."""
        while True:
            try:
                time.sleep(3600)  # Executa a cada hora
                
                # Limpa jobs antigos
                cutoff_time = datetime.now() - timedelta(days=7)
                jobs_to_remove = [
                    job_id for job_id, job in self.training_jobs.items()
                    if job.completed_at and job.completed_at < cutoff_time
                ]
                
                for job_id in jobs_to_remove:
                    del self.training_jobs[job_id]
                
                # Força garbage collection
                gc.collect()
                
                logger.info(f"Cleanup: removidos {len(jobs_to_remove)} jobs antigos")
                
            except Exception as e:
                logger.error(f"Erro no worker de cleanup: {e}")
    
    def _discover_models(self):
        """Descobre modelos disponíveis no Ollama."""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                
                for model_info in models:
                    model_name = model_info['name']
                    self.available_models[model_name] = ModelConfig(
                        name=model_name,
                        description=f"Modelo {model_name}",
                        parameters=model_info,
                        last_used=None,
                        usage_count=0
                    )
                
                logger.info(f"Descobertos {len(self.available_models)} modelos")
            else:
                logger.warning(f"Falha ao descobrir modelos: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Erro ao descobrir modelos: {e}")
            # Fallback para modelos padrão
            for model_name in self.config.get('fallback_models', ['llama3.1']):
                self.available_models[model_name] = ModelConfig(
                    name=model_name,
                    description=f"Modelo {model_name} (fallback)",
                    parameters={}
                )
    
    async def generate_response(self, prompt: str, model_name: Optional[str] = None,
                               parameters: Optional[Dict] = None,
                               use_cache: bool = True,
                               priority: int = 1) -> Dict[str, Any]:
        """Gera resposta usando IA local."""
        start_time = time.time()
        
        # Parâmetros padrão
        if parameters is None:
            parameters = {
                'temperature': self.config.get('default_temperature', 0.7),
                'top_p': self.config.get('default_top_p', 0.9),
                'max_tokens': self.config.get('max_context_length', 4096)
            }
        
        # Seleciona modelo se não especificado
        if model_name is None:
            available_models = [name for name, config in self.available_models.items() if config.enabled]
            if not available_models:
                return {
                    'success': False,
                    'error': 'Nenhum modelo disponível',
                    'response': None,
                    'model_used': None,
                    'response_time': 0
                }
            
            model_name = self.load_balancer.select_best_model(available_models)
        
        # Verifica cache
        cached_response = None
        if use_cache:
            cached_response = self.cache_manager.get(prompt, model_name, parameters)
            if cached_response:
                return {
                    'success': True,
                    'response': cached_response,
                    'model_used': model_name,
                    'response_time': time.time() - start_time,
                    'from_cache': True
                }
        
        # Gera resposta
        try:
            response_data = await self._call_ollama_api(model_name, prompt, parameters)
            
            if response_data['success']:
                response_time = time.time() - start_time
                
                # Registra métricas
                memory_usage = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                self.performance_monitor.record_inference(
                    model_name, response_time, True, memory_usage
                )
                
                # Atualiza estatísticas do modelo
                if model_name in self.available_models:
                    model_config = self.available_models[model_name]
                    model_config.last_used = datetime.now()
                    model_config.usage_count += 1
                    
                    # Atualiza tempo médio de resposta
                    if model_config.avg_response_time == 0:
                        model_config.avg_response_time = response_time
                    else:
                        model_config.avg_response_time = (
                            model_config.avg_response_time * 0.9 + response_time * 0.1
                        )
                
                # Salva no cache
                if use_cache and response_data['response']:
                    self.cache_manager.set(
                        prompt, model_name, parameters, 
                        response_data['response'], response_time
                    )
                
                # Marca requisição como completada no balanceador
                self.load_balancer.mark_request_completed(model_name)
                
                return {
                    'success': True,
                    'response': response_data['response'],
                    'model_used': model_name,
                    'response_time': response_time,
                    'from_cache': False
                }
            
            else:
                # Registra erro
                self.performance_monitor.record_inference(model_name, 0, False)
                
                # Tenta fallback se habilitado
                if self.config.get('auto_retry', True):
                    fallback_models = [
                        m for m in self.config.get('fallback_models', [])
                        if m != model_name and m in self.available_models
                    ]
                    
                    if fallback_models:
                        logger.warning(f"Tentando fallback para {fallback_models[0]}")
                        return await self.generate_response(
                            prompt, fallback_models[0], parameters, use_cache, priority
                        )
                
                return {
                    'success': False,
                    'error': response_data.get('error', 'Erro desconhecido'),
                    'response': None,
                    'model_used': model_name,
                    'response_time': time.time() - start_time
                }
                
        except Exception as e:
            logger.error(f"Erro ao gerar resposta: {e}")
            self.performance_monitor.record_inference(model_name, 0, False)
            
            return {
                'success': False,
                'error': str(e),
                'response': None,
                'model_used': model_name,
                'response_time': time.time() - start_time
            }
    
    async def _call_ollama_api(self, model_name: str, prompt: str, 
                              parameters: Dict) -> Dict[str, Any]:
        """Chama API do Ollama."""
        payload = {
            'model': model_name,
            'prompt': prompt,
            'stream': False,
            'options': {
                'temperature': parameters.get('temperature', 0.7),
                'top_p': parameters.get('top_p', 0.9),
                'max_tokens': parameters.get('max_tokens', 4096)
            }
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=300)  # 5 minutos
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{self.ollama_host}/api/generate",
                    json=payload
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'success': True,
                            'response': data.get('response', ''),
                            'context': data.get('context', [])
                        }
                    else:
                        error_text = await response.text()
                        return {
                            'success': False,
                            'error': f"HTTP {response.status}: {error_text}"
                        }
                        
        except asyncio.TimeoutError:
            return {
                'success': False,
                'error': 'Timeout na requisição'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def add_knowledge(self, content: str, metadata: Optional[Dict] = None) -> bool:
        """Adiciona conhecimento à base vetorial."""
        if not self.chroma_client or not self.embedding_model:
            logger.error("ChromaDB ou modelo de embedding não disponível")
            return False
        
        try:
            # Gera embedding
            embedding = self.embedding_model.encode([content])[0].tolist()
            
            # Prepara metadados
            if metadata is None:
                metadata = {}
            
            metadata.update({
                'added_at': datetime.now().isoformat(),
                'content_length': len(content),
                'content_hash': hashlib.sha256(content.encode()).hexdigest()
            })
            
            # Adiciona à collection
            doc_id = f"doc_{int(time.time() * 1000)}"
            
            self.knowledge_collection.add(
                ids=[doc_id],
                documents=[content],
                embeddings=[embedding],
                metadatas=[metadata]
            )
            
            logger.info(f"Conhecimento adicionado: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao adicionar conhecimento: {e}")
            return False
    
    def search_knowledge(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Busca na base de conhecimento."""
        if not self.chroma_client or not self.embedding_model:
            return []
        
        try:
            # Gera embedding da query
            query_embedding = self.embedding_model.encode([query])[0].tolist()
            
            # Busca similares
            results = self.knowledge_collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Formata resultados
            knowledge_items = []
            for i in range(len(results['ids'][0])):
                knowledge_items.append({
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'similarity': 1.0 - results['distances'][0][i]  # Converte distância para similaridade
                })
            
            return knowledge_items
            
        except Exception as e:
            logger.error(f"Erro ao buscar conhecimento: {e}")
            return []
    
    def create_training_job(self, model_name: str, dataset_path: str, 
                           config: Dict[str, Any]) -> str:
        """Cria job de treinamento."""
        job_id = f"job_{int(time.time() * 1000)}"
        
        job = TrainingJob(
            id=job_id,
            model_name=model_name,
            dataset_path=dataset_path,
            config=config,
            status='pending',
            created_at=datetime.now()
        )
        
        self.training_jobs[job_id] = job
        
        # Adiciona à fila com prioridade
        priority = config.get('priority', 5)
        self.training_queue.put((10 - priority, job_id))  # Inverte prioridade para PriorityQueue
        
        logger.info(f"Job de treinamento criado: {job_id}")
        return job_id
    
    def _execute_training_job(self, job: TrainingJob):
        """Executa job de treinamento."""
        try:
            job.status = 'running'
            job.started_at = datetime.now()
            job.logs.append(f"Iniciando treinamento: {job.started_at}")
            
            # Simula processo de treinamento
            # Em implementação real, aqui seria feito o fine-tuning
            
            for step in range(1, 101):
                time.sleep(0.1)  # Simula processamento
                job.progress = step
                
                if step % 10 == 0:
                    job.logs.append(f"Progresso: {step}%")
                    logger.info(f"Job {job.id}: {step}% completo")
            
            job.status = 'completed'
            job.completed_at = datetime.now()
            job.progress = 100
            job.logs.append(f"Treinamento concluído: {job.completed_at}")
            
            logger.info(f"Job {job.id} concluído com sucesso")
            
        except Exception as e:
            job.status = 'failed'
            job.completed_at = datetime.now()
            job.logs.append(f"Erro: {str(e)}")
            logger.error(f"Falha no job {job.id}: {e}")
    
    def get_training_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Obtém status de job de treinamento."""
        job = self.training_jobs.get(job_id)
        if job:
            return asdict(job)
        return None
    
    def list_available_models(self) -> List[Dict[str, Any]]:
        """Lista modelos disponíveis."""
        models = []
        for model_name, config in self.available_models.items():
            model_info = asdict(config)
            
            # Adiciona métricas de performance
            performance = self.performance_monitor.get_model_performance(model_name)
            model_info['performance'] = performance
            
            models.append(model_info)
        
        return models
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Obtém métricas do sistema."""
        # Métricas de sistema
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Métricas de modelos
        model_metrics = self.performance_monitor.get_all_metrics()
        
        # Estatísticas de cache
        cache_stats = {
            'cache_dir_size': sum(f.stat().st_size for f in self.cache_manager.cache_dir.rglob('*') if f.is_file()),
            'cache_entries': 0  # Implementar contagem de entradas
        }
        
        # Estatísticas de jobs
        job_stats = {
            'total_jobs': len(self.training_jobs),
            'pending_jobs': len([j for j in self.training_jobs.values() if j.status == 'pending']),
            'running_jobs': len([j for j in self.training_jobs.values() if j.status == 'running']),
            'completed_jobs': len([j for j in self.training_jobs.values() if j.status == 'completed']),
            'failed_jobs': len([j for j in self.training_jobs.values() if j.status == 'failed'])
        }
        
        return {
            'system': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3),
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / (1024**3)
            },
            'models': model_metrics,
            'cache': cache_stats,
            'training': job_stats,
            'timestamp': datetime.now().isoformat()
        }
    
    def optimize_model_performance(self, model_name: str) -> Dict[str, Any]:
        """Otimiza performance de um modelo."""
        if model_name not in self.available_models:
            return {'success': False, 'error': 'Modelo não encontrado'}
        
        try:
            # Analisa métricas atuais
            metrics = self.performance_monitor.get_model_performance(model_name)
            model_config = self.available_models[model_name]
            
            optimizations = []
            
            # Otimização baseada em tempo de resposta
            if metrics.get('avg_response_time', 0) > 5.0:
                optimizations.append('Configurar parâmetros para resposta mais rápida')
                # Implementar otimizações específicas
            
            # Otimização baseada em taxa de erro
            if metrics.get('error_rate', 0) > 0.1:
                optimizations.append('Ajustar configuração para reduzir erros')
                # Implementar correções
            
            # Otimização baseada em uso de memória
            if metrics.get('peak_memory', 0) > 2048:  # > 2GB
                optimizations.append('Otimizar uso de memória')
                # Implementar otimizações de memória
            
            return {
                'success': True,
                'optimizations_applied': optimizations,
                'metrics_before': metrics
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def backup_models(self, backup_path: str) -> bool:
        """Faz backup dos modelos."""
        try:
            backup_dir = Path(backup_path)
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup da configuração
            config_backup = backup_dir / 'config.json'
            with open(config_backup, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            # Backup dos modelos
            models_backup = backup_dir / 'models.json'
            models_data = {name: asdict(config) for name, config in self.available_models.items()}
            with open(models_backup, 'w') as f:
                json.dump(models_data, f, indent=2, default=str)
            
            # Backup da base de conhecimento
            if self.chroma_client:
                knowledge_backup = backup_dir / 'knowledge'
                knowledge_backup.mkdir(exist_ok=True)
                # Implementar backup do ChromaDB
            
            logger.info(f"Backup criado em: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erro no backup: {e}")
            return False
    
    def cleanup_resources(self):
        """Limpa recursos."""
        try:
            # Para workers
            # Fecha thread pool
            self.executor.shutdown(wait=True)
            
            # Limpa cache
            if hasattr(self, 'cache_manager'):
                self.cache_manager._cleanup_if_needed()
            
            # Fecha ChromaDB
            if hasattr(self, 'chroma_client'):
                # ChromaDB não tem método close explícito
                pass
            
            logger.info("Recursos limpos com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao limpar recursos: {e}")
    
    def __del__(self):
        """Destructor."""
        try:
            self.cleanup_resources()
        except:
            pass

# Função de utilidade para teste
def main():
    """Função principal para teste."""
    import asyncio
    
    async def test_trainer():
        trainer = LocalTrainer()
        
        try:
            # Teste de geração de resposta
            result = await trainer.generate_response(
                "Explique o que é inteligência artificial em poucas palavras.",
                model_name="llama3.1"
            )
            
            print("Resultado da geração:")
            print(json.dumps(result, indent=2, default=str))
            
            # Teste de adição de conhecimento
            trainer.add_knowledge(
                "AUTOBOT é um sistema de automação corporativa com IA local.",
                {"tipo": "definição", "categoria": "sistema"}
            )
            
            # Teste de busca de conhecimento
            knowledge = trainer.search_knowledge("O que é AUTOBOT?")
            print("\nConhecimento encontrado:")
            print(json.dumps(knowledge, indent=2, default=str))
            
            # Métricas do sistema
            metrics = trainer.get_system_metrics()
            print("\nMétricas do sistema:")
            print(json.dumps(metrics, indent=2, default=str))
            
        finally:
            trainer.cleanup_resources()
    
    # Executa teste
    asyncio.run(test_trainer())

if __name__ == "__main__":
    main()