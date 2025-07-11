#!/usr/bin/env python3
"""
Sistema de configuração completa do AUTOBOT IA Local
Versão Enterprise com todas as funcionalidades
"""

import os
import sys
import subprocess
import json
import logging
from pathlib import Path
from datetime import datetime
import platform
import psutil
import requests
from typing import Dict, List, Optional, Tuple
import yaml

class AutobotSetupManager:
    """Gerenciador principal de configuração do AUTOBOT"""
    
    def __init__(self):
        self.root_path = Path(__file__).parent.parent
        self.logger = self._setup_logging()
        self.config = self._load_config()
        self.system_info = self._detect_system()
        
    def _setup_logging(self) -> logging.Logger:
        """Configura sistema de logging avançado"""
        log_dir = Path("IA/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        logger = logging.getLogger('autobot_setup')
        logger.setLevel(logging.INFO)
        
        # Handler para arquivo
        file_handler = logging.FileHandler(log_dir / 'setup.log')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Handler para console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def _load_config(self) -> Dict:
        """Carrega configuração do sistema"""
        config_path = Path("IA/config.yaml")
        
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        
        # Configuração padrão
        default_config = {
            'ollama': {
                'host': 'localhost',
                'port': 11434,
                'models': ['llama3.2', 'mistral', 'tinyllama']
            },
            'chromadb': {
                'path': 'IA/memoria_conversas',
                'collection_prefix': 'autobot'
            },
            'redis': {
                'host': 'localhost',
                'port': 6379,
                'db': 0
            },
            'ai': {
                'embedding_model': 'all-MiniLM-L6-v2',
                'max_context_length': 4096,
                'temperature': 0.7
            }
        }
        
        # Salva configuração padrão
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False)
        
        return default_config
    
    def _detect_system(self) -> Dict:
        """Detecta especificações do sistema"""
        return {
            'os': platform.system(),
            'cpu_cores': psutil.cpu_count(),
            'memory_gb': round(psutil.virtual_memory().total / (1024**3)),
            'disk_free_gb': round(psutil.disk_usage('/').free / (1024**3)),
            'python_version': platform.python_version(),
            'has_gpu': self._detect_gpu(),
            'docker_available': self._check_docker(),
        }
    
    def _detect_gpu(self) -> bool:
        """Detecta se há GPU NVIDIA disponível"""
        try:
            subprocess.run(['nvidia-smi'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _check_docker(self) -> bool:
        """Verifica se Docker está disponível"""
        try:
            subprocess.run(['docker', '--version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def setup_full_enterprise(self):
        """Configuração completa enterprise"""
        self.logger.info("🚀 Iniciando configuração AUTOBOT Enterprise")
        
        # Fase 1: Estrutura
        self._create_directory_structure()
        
        # Fase 2: Dependências
        self._install_dependencies()
        
        # Fase 3: Modelos IA
        self._setup_ai_models()
        
        # Fase 4: Banco de dados
        self._setup_databases()
        
        # Fase 5: Docker
        self._setup_docker_environment()
        
        # Fase 6: Testes
        self._run_initial_tests()
        
        self.logger.info("✅ Configuração completa finalizada!")
    
    def _create_directory_structure(self):
        """Cria estrutura de diretórios necessária"""
        directories = [
            'IA/logs',
            'IA/modelos',
            'IA/memoria_conversas',
            'IA/treinamento',
            'autobot/integrações',
            'web/src/components',
            'docker/ai-services',
            'tests/ai'
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            self.logger.info(f"📁 Diretório criado: {directory}")
    
    def _install_dependencies(self):
        """Instala dependências Python"""
        try:
            self.logger.info("📦 Instalando dependências...")
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
            ], check=True, capture_output=True)
            self.logger.info("✅ Dependências instaladas com sucesso")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"❌ Erro ao instalar dependências: {e}")
    
    def _setup_ai_models(self):
        """Configura modelos de IA"""
        self.logger.info("🤖 Configurando modelos de IA...")
        
        # Verifica se Ollama está disponível
        try:
            subprocess.run(['ollama', 'version'], check=True, capture_output=True)
            self.logger.info("✅ Ollama detectado")
            
            # Instala modelos básicos
            models = self.config['ollama']['models']
            for model in models:
                try:
                    self.logger.info(f"📥 Baixando modelo: {model}")
                    subprocess.run(['ollama', 'pull', model], check=True)
                    self.logger.info(f"✅ Modelo {model} instalado")
                except subprocess.CalledProcessError:
                    self.logger.warning(f"⚠️ Falha ao instalar modelo: {model}")
        
        except subprocess.CalledProcessError:
            self.logger.warning("⚠️ Ollama não disponível. Instale manualmente.")
    
    def _setup_databases(self):
        """Configura bancos de dados"""
        self.logger.info("🗄️ Configurando bancos de dados...")
        
        # ChromaDB - configuração básica
        chroma_path = Path(self.config['chromadb']['path'])
        chroma_path.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"✅ ChromaDB configurado em: {chroma_path}")
        
        # Redis - verifica disponibilidade
        try:
            import redis
            r = redis.Redis(
                host=self.config['redis']['host'],
                port=self.config['redis']['port'],
                db=self.config['redis']['db']
            )
            r.ping()
            self.logger.info("✅ Redis conectado com sucesso")
        except Exception:
            self.logger.warning("⚠️ Redis não disponível. Funcionará sem cache.")
    
    def _setup_docker_environment(self):
        """Configura ambiente Docker"""
        if not self.system_info['docker_available']:
            self.logger.warning("⚠️ Docker não disponível")
            return
        
        self.logger.info("🐳 Configurando ambiente Docker...")
        
        # Cria docker-compose.yml para serviços de IA
        docker_compose = {
            'version': '3.8',
            'services': {
                'redis': {
                    'image': 'redis:7-alpine',
                    'ports': ['6379:6379'],
                    'volumes': ['redis_data:/data']
                },
                'ollama': {
                    'image': 'ollama/ollama:latest',
                    'ports': ['11434:11434'],
                    'volumes': ['ollama_data:/root/.ollama']
                }
            },
            'volumes': {
                'redis_data': {},
                'ollama_data': {}
            }
        }
        
        docker_path = Path('docker/docker-compose.yml')
        docker_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(docker_path, 'w') as f:
            yaml.dump(docker_compose, f, default_flow_style=False)
        
        self.logger.info("✅ Docker Compose configurado")
    
    def _run_initial_tests(self):
        """Executa testes iniciais do sistema"""
        self.logger.info("🧪 Executando testes iniciais...")
        
        # Teste básico de importações
        try:
            import torch
            import chromadb
            from sentence_transformers import SentenceTransformer
            self.logger.info("✅ Bibliotecas de IA importadas com sucesso")
        except ImportError as e:
            self.logger.error(f"❌ Erro ao importar bibliotecas: {e}")
        
        # Teste de modelo de embeddings
        try:
            model = SentenceTransformer(self.config['ai']['embedding_model'])
            test_embedding = model.encode("Teste de embedding")
            self.logger.info(f"✅ Modelo de embedding funcionando: {len(test_embedding)} dimensões")
        except Exception as e:
            self.logger.error(f"❌ Erro no modelo de embedding: {e}")
    
    def get_system_status(self) -> Dict:
        """Retorna status detalhado do sistema"""
        return {
            'timestamp': datetime.now().isoformat(),
            'system_info': self.system_info,
            'config': self.config,
            'services': {
                'ollama': self._check_service('ollama'),
                'redis': self._check_service('redis'),
                'chromadb': True  # ChromaDB é sempre disponível localmente
            }
        }
    
    def _check_service(self, service: str) -> bool:
        """Verifica se um serviço está disponível"""
        if service == 'ollama':
            try:
                subprocess.run(['ollama', 'version'], check=True, capture_output=True)
                return True
            except subprocess.CalledProcessError:
                return False
        elif service == 'redis':
            try:
                import redis
                r = redis.Redis(
                    host=self.config['redis']['host'],
                    port=self.config['redis']['port']
                )
                r.ping()
                return True
            except Exception:
                return False
        return False

if __name__ == "__main__":
    setup_manager = AutobotSetupManager()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--status":
        status = setup_manager.get_system_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
    else:
        setup_manager.setup_full_enterprise()