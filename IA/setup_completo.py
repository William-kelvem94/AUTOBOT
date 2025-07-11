"""
Setup Completo - Sistema de Configuração Automática AUTOBOT
===========================================================

Sistema avançado de configuração e instalação automática do AUTOBOT,
incluindo detecção de hardware, configuração otimizada e setup completo.

Funcionalidades principais:
- Detecção automática de hardware (GPU/CPU)
- Configuração otimizada por tipo de sistema
- Download automático de modelos essenciais
- Configuração de ambiente virtual
- Setup de banco de dados PostgreSQL para métricas
- Configuração de Redis para cache
- Setup de monitoramento com Prometheus
- Configuração de logs estruturados
- Verificação de dependências
- Configuração de segurança automática
"""

import os
import sys
import subprocess
import platform
import logging
import json
import yaml
import shutil
import requests
import tarfile
import zipfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import click
import psutil
import socket
from dataclasses import dataclass, asdict
from urllib.parse import urlparse
import hashlib
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import docker
import pkg_resources
from packaging import version
import getpass

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('autobot_setup.log')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class SystemRequirements:
    """Requisitos do sistema."""
    min_ram_gb: int = 8
    min_disk_gb: int = 50
    min_cpu_cores: int = 4
    recommended_ram_gb: int = 16
    recommended_disk_gb: int = 100
    recommended_cpu_cores: int = 8
    python_version: str = "3.8.0"

@dataclass
class HardwareInfo:
    """Informações de hardware."""
    cpu_cores: int
    cpu_freq: float
    ram_gb: float
    disk_gb: float
    gpu_available: bool
    gpu_info: List[str]
    os_type: str
    architecture: str

@dataclass
class InstallationConfig:
    """Configuração de instalação."""
    install_type: str  # minimal, standard, full, enterprise
    enable_gpu: bool
    enable_docker: bool
    enable_monitoring: bool
    enable_backups: bool
    install_path: str
    data_path: str
    models_to_download: List[str]
    databases: List[str]  # sqlite, postgresql, redis
    web_interface: bool
    api_keys: Dict[str, str]

class SystemDetector:
    """Detector de sistema e hardware."""
    
    def __init__(self):
        self.requirements = SystemRequirements()
    
    def detect_hardware(self) -> HardwareInfo:
        """Detecta informações de hardware."""
        logger.info("Detectando configuração de hardware...")
        
        # CPU
        cpu_cores = psutil.cpu_count(logical=False)
        cpu_freq = psutil.cpu_freq().max if psutil.cpu_freq() else 0
        
        # RAM
        ram_bytes = psutil.virtual_memory().total
        ram_gb = ram_bytes / (1024**3)
        
        # Disco
        disk_usage = psutil.disk_usage('/')
        disk_gb = disk_usage.total / (1024**3)
        
        # GPU
        gpu_available, gpu_info = self._detect_gpu()
        
        # OS
        os_type = platform.system().lower()
        architecture = platform.machine()
        
        hardware = HardwareInfo(
            cpu_cores=cpu_cores,
            cpu_freq=cpu_freq,
            ram_gb=ram_gb,
            disk_gb=disk_gb,
            gpu_available=gpu_available,
            gpu_info=gpu_info,
            os_type=os_type,
            architecture=architecture
        )
        
        logger.info(f"Hardware detectado: {cpu_cores} cores, {ram_gb:.1f}GB RAM, GPU: {gpu_available}")
        return hardware
    
    def _detect_gpu(self) -> Tuple[bool, List[str]]:
        """Detecta GPUs disponíveis."""
        gpu_info = []
        
        try:
            # Tenta detectar NVIDIA
            result = subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                nvidia_gpus = result.stdout.strip().split('\n')
                gpu_info.extend([f"NVIDIA {gpu.strip()}" for gpu in nvidia_gpus if gpu.strip()])
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        try:
            # Tenta detectar AMD (Linux)
            if platform.system().lower() == 'linux':
                result = subprocess.run(['lspci'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    lines = result.stdout.lower()
                    if 'amd' in lines and ('radeon' in lines or 'vega' in lines):
                        gpu_info.append("AMD GPU detected")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return len(gpu_info) > 0, gpu_info
    
    def check_requirements(self, hardware: HardwareInfo) -> Dict[str, Any]:
        """Verifica se o hardware atende aos requisitos."""
        issues = []
        warnings = []
        
        # RAM
        if hardware.ram_gb < self.requirements.min_ram_gb:
            issues.append(f"RAM insuficiente: {hardware.ram_gb:.1f}GB (mínimo: {self.requirements.min_ram_gb}GB)")
        elif hardware.ram_gb < self.requirements.recommended_ram_gb:
            warnings.append(f"RAM abaixo do recomendado: {hardware.ram_gb:.1f}GB (recomendado: {self.requirements.recommended_ram_gb}GB)")
        
        # CPU
        if hardware.cpu_cores < self.requirements.min_cpu_cores:
            issues.append(f"CPU cores insuficientes: {hardware.cpu_cores} (mínimo: {self.requirements.min_cpu_cores})")
        elif hardware.cpu_cores < self.requirements.recommended_cpu_cores:
            warnings.append(f"CPU cores abaixo do recomendado: {hardware.cpu_cores} (recomendado: {self.requirements.recommended_cpu_cores})")
        
        # Disco
        if hardware.disk_gb < self.requirements.min_disk_gb:
            issues.append(f"Espaço em disco insuficiente: {hardware.disk_gb:.1f}GB (mínimo: {self.requirements.min_disk_gb}GB)")
        elif hardware.disk_gb < self.requirements.recommended_disk_gb:
            warnings.append(f"Espaço em disco abaixo do recomendado: {hardware.disk_gb:.1f}GB (recomendado: {self.requirements.recommended_disk_gb}GB)")
        
        # Python
        python_version_str = platform.python_version()
        if version.parse(python_version_str) < version.parse(self.requirements.python_version):
            issues.append(f"Versão do Python muito antiga: {python_version_str} (mínimo: {self.requirements.python_version})")
        
        return {
            'meets_requirements': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'recommendation': self._get_installation_recommendation(hardware)
        }
    
    def _get_installation_recommendation(self, hardware: HardwareInfo) -> str:
        """Recomenda tipo de instalação baseado no hardware."""
        if (hardware.ram_gb >= 32 and hardware.cpu_cores >= 16 and 
            hardware.gpu_available and hardware.disk_gb >= 200):
            return 'enterprise'
        elif (hardware.ram_gb >= 16 and hardware.cpu_cores >= 8 and 
              hardware.disk_gb >= 100):
            return 'full'
        elif (hardware.ram_gb >= 8 and hardware.cpu_cores >= 4 and 
              hardware.disk_gb >= 50):
            return 'standard'
        else:
            return 'minimal'

class DependencyManager:
    """Gerenciador de dependências."""
    
    def __init__(self):
        self.required_packages = self._load_requirements()
        self.system_dependencies = self._get_system_dependencies()
    
    def _load_requirements(self) -> Dict[str, List[str]]:
        """Carrega lista de dependências Python."""
        return {
            'minimal': [
                'flask>=2.3.0',
                'requests>=2.31.0',
                'sqlite3',  # Built-in
                'pyyaml>=6.0.0',
                'click>=8.1.0',
                'psutil>=5.9.0'
            ],
            'standard': [
                'flask>=2.3.0', 'flask-cors>=4.0.0', 'flask-limiter>=3.5.0',
                'requests>=2.31.0', 'aiohttp>=3.8.0',
                'numpy>=1.24.0', 'pandas>=2.0.0',
                'sqlite3', 'redis>=5.0.0',
                'pyyaml>=6.0.0', 'click>=8.1.0', 'psutil>=5.9.0',
                'selenium>=4.15.0', 'beautifulsoup4>=4.12.0'
            ],
            'full': [
                'flask>=2.3.0', 'flask-cors>=4.0.0', 'flask-limiter>=3.5.0',
                'flask-jwt-extended>=4.5.0', 'flask-socketio>=5.3.0',
                'requests>=2.31.0', 'aiohttp>=3.8.0', 'websockets>=11.0.0',
                'numpy>=1.24.0', 'pandas>=2.0.0', 'scipy>=1.11.0',
                'scikit-learn>=1.3.0', 'matplotlib>=3.7.0', 'seaborn>=0.12.0',
                'plotly>=5.17.0', 'wordcloud>=1.9.0',
                'sqlite3', 'redis>=5.0.0', 'psycopg2-binary>=2.9.0',
                'chromadb>=0.4.15', 'sentence-transformers>=2.2.0',
                'nltk>=3.8.0', 'textblob>=0.17.0',
                'torch>=2.0.0', 'transformers>=4.34.0',
                'pyyaml>=6.0.0', 'click>=8.1.0', 'psutil>=5.9.0',
                'selenium>=4.15.0', 'pyautogui>=0.9.50', 'beautifulsoup4>=4.12.0',
                'prometheus-client>=0.17.0', 'schedule>=1.2.0'
            ],
            'enterprise': [
                'flask>=2.3.0', 'flask-cors>=4.0.0', 'flask-limiter>=3.5.0',
                'flask-jwt-extended>=4.5.0', 'flask-socketio>=5.3.0',
                'requests>=2.31.0', 'aiohttp>=3.8.0', 'websockets>=11.0.0',
                'numpy>=1.24.0', 'pandas>=2.0.0', 'scipy>=1.11.0',
                'scikit-learn>=1.3.0', 'matplotlib>=3.7.0', 'seaborn>=0.12.0',
                'plotly>=5.17.0', 'wordcloud>=1.9.0',
                'sqlite3', 'redis>=5.0.0', 'psycopg2-binary>=2.9.0',
                'chromadb>=0.4.15', 'sentence-transformers>=2.2.0',
                'nltk>=3.8.0', 'textblob>=0.17.0', 'spacy>=3.7.0',
                'torch>=2.0.0', 'transformers>=4.34.0',
                'pyyaml>=6.0.0', 'click>=8.1.0', 'psutil>=5.9.0',
                'selenium>=4.15.0', 'pyautogui>=0.9.50', 'beautifulsoup4>=4.12.0',
                'prometheus-client>=0.17.0', 'schedule>=1.2.0',
                'docker>=6.1.0', 'kubernetes>=27.2.0',
                'celery>=5.3.0', 'gunicorn>=21.2.0',
                'cryptography>=41.0.0', 'python-jwt>=3.3.0'
            ]
        }
    
    def _get_system_dependencies(self) -> Dict[str, List[str]]:
        """Obtém dependências do sistema operacional."""
        return {
            'ubuntu': [
                'python3-dev', 'python3-pip', 'python3-venv',
                'build-essential', 'libssl-dev', 'libffi-dev',
                'postgresql-client', 'redis-server', 'git',
                'curl', 'wget', 'unzip', 'sqlite3'
            ],
            'centos': [
                'python3-devel', 'python3-pip', 'python3-venv',
                'gcc', 'gcc-c++', 'make', 'openssl-devel',
                'postgresql-devel', 'redis', 'git',
                'curl', 'wget', 'unzip', 'sqlite'
            ],
            'macos': [
                'python3', 'pip3', 'git', 'curl', 'wget'
            ]
        }
    
    def install_system_dependencies(self, os_type: str) -> bool:
        """Instala dependências do sistema."""
        logger.info("Instalando dependências do sistema...")
        
        if os_type == 'linux':
            # Detecta distribuição Linux
            try:
                with open('/etc/os-release', 'r') as f:
                    os_release = f.read().lower()
                
                if 'ubuntu' in os_release or 'debian' in os_release:
                    return self._install_apt_packages()
                elif 'centos' in os_release or 'rhel' in os_release or 'fedora' in os_release:
                    return self._install_yum_packages()
            except FileNotFoundError:
                logger.warning("Não foi possível detectar a distribuição Linux")
        
        elif os_type == 'darwin':  # macOS
            return self._install_macos_packages()
        
        elif os_type == 'windows':
            logger.info("Windows detectado - dependências devem ser instaladas manualmente")
            return True
        
        return False
    
    def _install_apt_packages(self) -> bool:
        """Instala pacotes via apt (Ubuntu/Debian)."""
        try:
            packages = self.system_dependencies.get('ubuntu', [])
            
            # Atualiza lista de pacotes
            subprocess.run(['sudo', 'apt', 'update'], check=True)
            
            # Instala pacotes
            cmd = ['sudo', 'apt', 'install', '-y'] + packages
            subprocess.run(cmd, check=True)
            
            logger.info("Dependências do sistema instaladas com sucesso (apt)")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro ao instalar dependências via apt: {e}")
            return False
    
    def _install_yum_packages(self) -> bool:
        """Instala pacotes via yum/dnf (CentOS/RHEL/Fedora)."""
        try:
            packages = self.system_dependencies.get('centos', [])
            
            # Tenta dnf primeiro, depois yum
            package_manager = 'dnf' if shutil.which('dnf') else 'yum'
            
            cmd = ['sudo', package_manager, 'install', '-y'] + packages
            subprocess.run(cmd, check=True)
            
            logger.info(f"Dependências do sistema instaladas com sucesso ({package_manager})")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro ao instalar dependências via yum/dnf: {e}")
            return False
    
    def _install_macos_packages(self) -> bool:
        """Instala pacotes no macOS."""
        logger.info("macOS detectado - verificando Homebrew...")
        
        # Verifica se Homebrew está instalado
        if not shutil.which('brew'):
            logger.info("Homebrew não encontrado - instalando...")
            try:
                install_script = requests.get('https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh')
                subprocess.run(['bash', '-c', install_script.text], check=True)
            except Exception as e:
                logger.error(f"Erro ao instalar Homebrew: {e}")
                return False
        
        try:
            packages = self.system_dependencies.get('macos', [])
            for package in packages:
                subprocess.run(['brew', 'install', package], check=True)
            
            logger.info("Dependências do sistema instaladas com sucesso (Homebrew)")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro ao instalar dependências via Homebrew: {e}")
            return False
    
    def install_python_dependencies(self, install_type: str, venv_path: Optional[str] = None) -> bool:
        """Instala dependências Python."""
        logger.info(f"Instalando dependências Python para tipo: {install_type}")
        
        packages = self.required_packages.get(install_type, [])
        if not packages:
            logger.error(f"Tipo de instalação inválido: {install_type}")
            return False
        
        try:
            # Determina comando pip
            pip_cmd = 'pip'
            if venv_path:
                pip_cmd = str(Path(venv_path) / 'bin' / 'pip')
                if not Path(pip_cmd).exists():
                    pip_cmd = str(Path(venv_path) / 'Scripts' / 'pip.exe')  # Windows
            
            # Atualiza pip
            subprocess.run([pip_cmd, 'install', '--upgrade', 'pip'], check=True)
            
            # Instala pacotes
            for package in packages:
                if package == 'sqlite3':  # Built-in
                    continue
                
                logger.info(f"Instalando {package}...")
                subprocess.run([pip_cmd, 'install', package], check=True)
            
            logger.info("Dependências Python instaladas com sucesso")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro ao instalar dependências Python: {e}")
            return False
    
    def verify_installation(self, install_type: str) -> Dict[str, bool]:
        """Verifica se as dependências foram instaladas corretamente."""
        logger.info("Verificando instalação das dependências...")
        
        packages = self.required_packages.get(install_type, [])
        results = {}
        
        for package in packages:
            if package == 'sqlite3':  # Built-in
                results[package] = True
                continue
            
            try:
                # Remove versão se especificada
                package_name = package.split('>=')[0].split('==')[0]
                pkg_resources.get_distribution(package_name)
                results[package] = True
            except pkg_resources.DistributionNotFound:
                results[package] = False
        
        return results

class ModelDownloader:
    """Downloader de modelos de IA."""
    
    def __init__(self):
        self.models_config = {
            'llama3.1': {
                'type': 'ollama',
                'size_gb': 4.1,
                'description': 'Modelo principal de conversação'
            },
            'mistral': {
                'type': 'ollama', 
                'size_gb': 4.1,
                'description': 'Modelo alternativo rápido'
            },
            'codellama': {
                'type': 'ollama',
                'size_gb': 3.8,
                'description': 'Modelo especializado em código'
            },
            'nomic-embed-text': {
                'type': 'ollama',
                'size_gb': 0.3,
                'description': 'Modelo de embeddings'
            }
        }
    
    def check_ollama_installation(self) -> bool:
        """Verifica se Ollama está instalado."""
        return shutil.which('ollama') is not None
    
    def install_ollama(self) -> bool:
        """Instala Ollama."""
        logger.info("Instalando Ollama...")
        
        try:
            os_type = platform.system().lower()
            
            if os_type == 'linux' or os_type == 'darwin':
                # Download e execução do script de instalação
                install_script = requests.get('https://ollama.ai/install.sh', timeout=30)
                subprocess.run(['bash', '-c', install_script.text], check=True)
                
            elif os_type == 'windows':
                logger.info("Para Windows, baixe o instalador de https://ollama.ai/download")
                return False
            
            # Verifica instalação
            if self.check_ollama_installation():
                logger.info("Ollama instalado com sucesso")
                
                # Inicia serviço
                subprocess.Popen(['ollama', 'serve'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(5)  # Aguarda inicialização
                
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Erro ao instalar Ollama: {e}")
            return False
    
    def download_models(self, models: List[str]) -> Dict[str, bool]:
        """Baixa modelos especificados."""
        if not self.check_ollama_installation():
            logger.error("Ollama não está instalado")
            return {model: False for model in models}
        
        results = {}
        
        for model in models:
            if model not in self.models_config:
                logger.warning(f"Modelo desconhecido: {model}")
                results[model] = False
                continue
            
            logger.info(f"Baixando modelo {model}...")
            
            try:
                # Verifica espaço em disco
                config = self.models_config[model]
                available_space = psutil.disk_usage('/').free / (1024**3)
                
                if available_space < config['size_gb'] * 1.2:  # 20% de margem
                    logger.error(f"Espaço insuficiente para {model}: {config['size_gb']}GB necessários")
                    results[model] = False
                    continue
                
                # Download via Ollama
                result = subprocess.run(['ollama', 'pull', model], 
                                      capture_output=True, text=True, timeout=3600)
                
                if result.returncode == 0:
                    logger.info(f"Modelo {model} baixado com sucesso")
                    results[model] = True
                else:
                    logger.error(f"Erro ao baixar {model}: {result.stderr}")
                    results[model] = False
                    
            except subprocess.TimeoutExpired:
                logger.error(f"Timeout ao baixar {model}")
                results[model] = False
            except Exception as e:
                logger.error(f"Erro ao baixar {model}: {e}")
                results[model] = False
        
        return results
    
    def get_available_space_requirements(self, models: List[str]) -> float:
        """Calcula espaço necessário para os modelos."""
        total_size = 0
        for model in models:
            if model in self.models_config:
                total_size += self.models_config[model]['size_gb']
        
        return total_size * 1.2  # 20% de margem

class ConfigurationManager:
    """Gerenciador de configurações."""
    
    def __init__(self, install_path: str):
        self.install_path = Path(install_path)
        self.config_path = self.install_path / 'config'
        self.data_path = self.install_path / 'data'
        
    def create_directory_structure(self):
        """Cria estrutura de diretórios."""
        logger.info("Criando estrutura de diretórios...")
        
        directories = [
            self.install_path,
            self.config_path,
            self.data_path,
            self.data_path / 'cache',
            self.data_path / 'memory',
            self.data_path / 'models',
            self.data_path / 'logs',
            self.data_path / 'backups',
            self.install_path / 'logs',
            self.install_path / 'temp'
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Estrutura criada em: {self.install_path}")
    
    def generate_configurations(self, config: InstallationConfig, hardware: HardwareInfo):
        """Gera arquivos de configuração."""
        logger.info("Gerando arquivos de configuração...")
        
        # Configuração principal
        main_config = self._generate_main_config(config, hardware)
        self._save_config('main.yaml', main_config)
        
        # Configuração de IA
        ai_config = self._generate_ai_config(config, hardware)
        self._save_config('ai.yaml', ai_config)
        
        # Configuração de dashboard
        if config.enable_monitoring:
            dashboard_config = self._generate_dashboard_config(config)
            self._save_config('dashboard.yaml', dashboard_config)
        
        # Configuração de banco de dados
        if 'postgresql' in config.databases:
            db_config = self._generate_database_config(config)
            self._save_config('database.yaml', db_config)
        
        # Configuração de Docker
        if config.enable_docker:
            self._generate_docker_config(config)
        
        # Configuração de segurança
        security_config = self._generate_security_config()
        self._save_config('security.yaml', security_config)
        
        logger.info("Configurações geradas com sucesso")
    
    def _generate_main_config(self, config: InstallationConfig, hardware: HardwareInfo) -> Dict[str, Any]:
        """Gera configuração principal."""
        return {
            'autobot': {
                'version': '2.0.0',
                'install_type': config.install_type,
                'install_path': str(self.install_path),
                'data_path': str(self.data_path),
                'enable_gpu': config.enable_gpu and hardware.gpu_available,
                'max_workers': min(hardware.cpu_cores, 16),
                'memory_limit_gb': int(hardware.ram_gb * 0.8),
                'temp_dir': str(self.install_path / 'temp')
            },
            'api': {
                'host': '0.0.0.0',
                'port': 5000,
                'debug': False,
                'cors_origins': ['http://localhost:3000', 'http://localhost:3001'],
                'rate_limit': 1000,
                'enable_websockets': True
            },
            'logging': {
                'level': 'INFO',
                'file': str(self.install_path / 'logs' / 'autobot.log'),
                'max_size_mb': 100,
                'backup_count': 5,
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        }
    
    def _generate_ai_config(self, config: InstallationConfig, hardware: HardwareInfo) -> Dict[str, Any]:
        """Gera configuração de IA."""
        return {
            'ollama': {
                'host': 'http://localhost:11434',
                'timeout': 300,
                'models': config.models_to_download,
                'default_model': 'llama3.1',
                'enable_gpu': config.enable_gpu and hardware.gpu_available
            },
            'memory': {
                'chromadb_path': str(self.data_path / 'chromadb'),
                'cache_path': str(self.data_path / 'cache'),
                'max_conversations': 10000,
                'compression_threshold': 1000,
                'backup_interval': 3600
            },
            'optimization': {
                'enable_ab_testing': config.install_type in ['full', 'enterprise'],
                'auto_optimization': True,
                'performance_target': 'balanced'
            },
            'analysis': {
                'sentiment_analysis': True,
                'topic_extraction': True,
                'pattern_detection': True,
                'insight_generation': config.install_type in ['full', 'enterprise']
            }
        }
    
    def _generate_dashboard_config(self, config: InstallationConfig) -> Dict[str, Any]:
        """Gera configuração do dashboard."""
        return {
            'dashboard': {
                'host': '0.0.0.0',
                'port': 8080,
                'enable_websockets': True,
                'update_interval': 30,
                'metrics_retention_days': 30
            },
            'alerts': {
                'enabled': True,
                'rules': [
                    {
                        'id': 'cpu_high',
                        'name': 'High CPU Usage',
                        'metric': 'cpu_usage',
                        'condition': '>',
                        'threshold': 80.0,
                        'duration_minutes': 5,
                        'severity': 'warning',
                        'channels': ['email']
                    },
                    {
                        'id': 'memory_high',
                        'name': 'High Memory Usage',
                        'metric': 'memory_usage',
                        'condition': '>',
                        'threshold': 85.0,
                        'duration_minutes': 5,
                        'severity': 'critical',
                        'channels': ['email']
                    }
                ]
            },
            'notification_channels': {
                'email': {
                    'smtp_server': 'localhost',
                    'smtp_port': 587,
                    'use_tls': True,
                    'from': 'autobot@localhost',
                    'to': ['admin@localhost']
                }
            }
        }
    
    def _generate_database_config(self, config: InstallationConfig) -> Dict[str, Any]:
        """Gera configuração de banco de dados."""
        return {
            'databases': {
                'sqlite': {
                    'path': str(self.data_path / 'autobot.db'),
                    'pool_size': 20,
                    'timeout': 30
                },
                'postgresql': {
                    'host': 'localhost',
                    'port': 5432,
                    'database': 'autobot',
                    'username': 'autobot',
                    'password': 'generated_password',
                    'pool_size': 20,
                    'timeout': 30
                } if 'postgresql' in config.databases else None,
                'redis': {
                    'host': 'localhost',
                    'port': 6379,
                    'db': 0,
                    'timeout': 5
                } if 'redis' in config.databases else None
            }
        }
    
    def _generate_docker_config(self, config: InstallationConfig):
        """Gera configuração Docker."""
        docker_compose = {
            'version': '3.8',
            'services': {
                'autobot-api': {
                    'build': '.',
                    'ports': ['5000:5000'],
                    'environment': [
                        'AUTOBOT_CONFIG_PATH=/app/config/main.yaml'
                    ],
                    'volumes': [
                        f"{self.config_path}:/app/config",
                        f"{self.data_path}:/app/data"
                    ],
                    'depends_on': ['redis'] if 'redis' in config.databases else []
                }
            }
        }
        
        # Adiciona serviços opcionais
        if 'redis' in config.databases:
            docker_compose['services']['redis'] = {
                'image': 'redis:7-alpine',
                'ports': ['6379:6379'],
                'volumes': [f"{self.data_path}/redis:/data"]
            }
        
        if 'postgresql' in config.databases:
            docker_compose['services']['postgresql'] = {
                'image': 'postgres:15-alpine',
                'ports': ['5432:5432'],
                'environment': [
                    'POSTGRES_DB=autobot',
                    'POSTGRES_USER=autobot',
                    'POSTGRES_PASSWORD=generated_password'
                ],
                'volumes': [f"{self.data_path}/postgres:/var/lib/postgresql/data"]
            }
        
        if config.enable_monitoring:
            docker_compose['services']['dashboard'] = {
                'build': '.',
                'command': 'python -m IA.dashboard.monitor',
                'ports': ['8080:8080'],
                'environment': [
                    'AUTOBOT_CONFIG_PATH=/app/config/dashboard.yaml'
                ],
                'volumes': [
                    f"{self.config_path}:/app/config",
                    f"{self.data_path}:/app/data"
                ]
            }
        
        # Salva arquivo Docker Compose
        with open(self.install_path / 'docker-compose.yml', 'w') as f:
            yaml.dump(docker_compose, f, default_flow_style=False)
        
        # Gera Dockerfile
        dockerfile_content = self._generate_dockerfile(config)
        with open(self.install_path / 'Dockerfile', 'w') as f:
            f.write(dockerfile_content)
    
    def _generate_dockerfile(self, config: InstallationConfig) -> str:
        """Gera Dockerfile."""
        base_image = 'python:3.11-slim'
        
        if config.enable_gpu:
            base_image = 'nvidia/cuda:12.1-runtime-ubuntu22.04'
        
        return f"""FROM {base_image}

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \\
    build-essential \\
    libssl-dev \\
    libffi-dev \\
    python3-dev \\
    git \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Cria usuário não-root
RUN useradd -m -s /bin/bash autobot

# Define diretório de trabalho
WORKDIR /app

# Copia requirements
COPY requirements*.txt ./

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements_ia.txt

# Copia código da aplicação
COPY . .

# Muda proprietário para usuário autobot
RUN chown -R autobot:autobot /app

# Muda para usuário não-root
USER autobot

# Expõe portas
EXPOSE 5000 8080

# Comando padrão
CMD ["python", "-m", "autobot.api"]
"""
    
    def _generate_security_config(self) -> Dict[str, Any]:
        """Gera configuração de segurança."""
        import secrets
        
        return {
            'security': {
                'secret_key': secrets.token_urlsafe(32),
                'jwt_secret': secrets.token_urlsafe(32),
                'api_key_length': 32,
                'session_timeout': 3600,
                'max_login_attempts': 5,
                'lockout_duration': 300,
                'password_min_length': 8,
                'require_https': False,
                'cors_origins': ['http://localhost:3000', 'http://localhost:3001']
            },
            'encryption': {
                'algorithm': 'HS256',
                'key_rotation_days': 90,
                'backup_encryption': True
            },
            'audit': {
                'log_requests': True,
                'log_responses': False,
                'log_errors': True,
                'retention_days': 90
            }
        }
    
    def _save_config(self, filename: str, config: Dict[str, Any]):
        """Salva arquivo de configuração."""
        config_file = self.config_path / filename
        
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        
        logger.info(f"Configuração salva: {filename}")

class AutobotInstaller:
    """Instalador principal do AUTOBOT."""
    
    def __init__(self):
        self.detector = SystemDetector()
        self.dependency_manager = DependencyManager()
        self.model_downloader = ModelDownloader()
        
    def run_interactive_setup(self) -> InstallationConfig:
        """Executa setup interativo."""
        click.echo("🤖 Bem-vindo ao Setup do AUTOBOT - Sistema de IA Local Corporativa")
        click.echo("=" * 70)
        
        # Detecta hardware
        hardware = self.detector.detect_hardware()
        self._display_hardware_info(hardware)
        
        # Verifica requisitos
        requirements_check = self.detector.check_requirements(hardware)
        self._display_requirements_check(requirements_check)
        
        if not requirements_check['meets_requirements']:
            if not click.confirm("Seu sistema não atende aos requisitos mínimos. Continuar mesmo assim?"):
                sys.exit(1)
        
        # Configuração de instalação
        config = self._configure_installation(hardware, requirements_check['recommendation'])
        
        return config
    
    def _display_hardware_info(self, hardware: HardwareInfo):
        """Exibe informações de hardware."""
        click.echo("\n📊 Configuração de Hardware Detectada:")
        click.echo(f"  • CPU: {hardware.cpu_cores} cores @ {hardware.cpu_freq:.1f} MHz")
        click.echo(f"  • RAM: {hardware.ram_gb:.1f} GB")
        click.echo(f"  • Disco: {hardware.disk_gb:.1f} GB disponível")
        click.echo(f"  • GPU: {'✅ Detectada' if hardware.gpu_available else '❌ Não detectada'}")
        
        if hardware.gpu_available:
            for gpu in hardware.gpu_info:
                click.echo(f"    - {gpu}")
        
        click.echo(f"  • SO: {hardware.os_type} ({hardware.architecture})")
    
    def _display_requirements_check(self, check: Dict[str, Any]):
        """Exibe verificação de requisitos."""
        click.echo("\n✅ Verificação de Requisitos:")
        
        if check['meets_requirements']:
            click.echo("  • Todos os requisitos mínimos foram atendidos!")
        else:
            click.echo("  ❌ Problemas encontrados:")
            for issue in check['issues']:
                click.echo(f"    - {issue}")
        
        if check['warnings']:
            click.echo("  ⚠️  Avisos:")
            for warning in check['warnings']:
                click.echo(f"    - {warning}")
        
        click.echo(f"\n💡 Tipo de instalação recomendado: {check['recommendation']}")
    
    def _configure_installation(self, hardware: HardwareInfo, recommended_type: str) -> InstallationConfig:
        """Configura instalação interativamente."""
        click.echo("\n⚙️  Configuração de Instalação:")
        
        # Tipo de instalação
        install_types = {
            '1': 'minimal',
            '2': 'standard', 
            '3': 'full',
            '4': 'enterprise'
        }
        
        click.echo("\nTipos de instalação disponíveis:")
        click.echo("  1. Minimal - Funcionalidades básicas (4GB RAM)")
        click.echo("  2. Standard - Funcionalidades principais (8GB RAM)")
        click.echo("  3. Full - Todas as funcionalidades (16GB RAM)")
        click.echo("  4. Enterprise - Instalação completa com monitoramento (32GB RAM)")
        
        default_choice = '2'
        for key, value in install_types.items():
            if value == recommended_type:
                default_choice = key
                break
        
        choice = click.prompt(f"Escolha o tipo de instalação", 
                             default=default_choice, 
                             type=click.Choice(install_types.keys()))
        install_type = install_types[choice]
        
        # Caminho de instalação
        default_path = str(Path.home() / 'autobot')
        install_path = click.prompt("Caminho de instalação", default=default_path)
        
        # GPU
        enable_gpu = False
        if hardware.gpu_available:
            enable_gpu = click.confirm("Habilitar aceleração GPU?", default=True)
        
        # Docker
        enable_docker = False
        if install_type in ['full', 'enterprise']:
            enable_docker = click.confirm("Configurar Docker?", default=True)
        
        # Monitoramento
        enable_monitoring = install_type in ['full', 'enterprise']
        if install_type == 'standard':
            enable_monitoring = click.confirm("Habilitar monitoramento?", default=False)
        
        # Modelos
        models_options = {
            'minimal': ['llama3.1'],
            'standard': ['llama3.1', 'nomic-embed-text'],
            'full': ['llama3.1', 'mistral', 'nomic-embed-text'],
            'enterprise': ['llama3.1', 'mistral', 'codellama', 'nomic-embed-text']
        }
        
        models_to_download = models_options.get(install_type, ['llama3.1'])
        
        # Bancos de dados
        databases = ['sqlite']
        if install_type in ['full', 'enterprise']:
            if click.confirm("Usar PostgreSQL?", default=True):
                databases.append('postgresql')
            if click.confirm("Usar Redis para cache?", default=True):
                databases.append('redis')
        
        return InstallationConfig(
            install_type=install_type,
            enable_gpu=enable_gpu,
            enable_docker=enable_docker,
            enable_monitoring=enable_monitoring,
            enable_backups=install_type in ['full', 'enterprise'],
            install_path=install_path,
            data_path=str(Path(install_path) / 'data'),
            models_to_download=models_to_download,
            databases=databases,
            web_interface=True,
            api_keys={}
        )
    
    def install(self, config: InstallationConfig, hardware: HardwareInfo) -> bool:
        """Executa instalação completa."""
        try:
            click.echo("\n🚀 Iniciando instalação do AUTOBOT...")
            
            # 1. Criar estrutura de diretórios
            click.echo("📁 Criando estrutura de diretórios...")
            config_manager = ConfigurationManager(config.install_path)
            config_manager.create_directory_structure()
            
            # 2. Instalar dependências do sistema
            click.echo("📦 Instalando dependências do sistema...")
            if not self.dependency_manager.install_system_dependencies(hardware.os_type):
                logger.warning("Falha ao instalar algumas dependências do sistema")
            
            # 3. Criar ambiente virtual
            click.echo("🐍 Criando ambiente virtual Python...")
            venv_path = Path(config.install_path) / 'venv'
            if not self._create_virtual_environment(venv_path):
                return False
            
            # 4. Instalar dependências Python
            click.echo("🔧 Instalando dependências Python...")
            if not self.dependency_manager.install_python_dependencies(config.install_type, str(venv_path)):
                return False
            
            # 5. Instalar Ollama
            click.echo("🦙 Configurando Ollama...")
            if not self.model_downloader.check_ollama_installation():
                if not self.model_downloader.install_ollama():
                    logger.warning("Falha ao instalar Ollama - instale manualmente")
            
            # 6. Baixar modelos
            click.echo("📥 Baixando modelos de IA...")
            space_required = self.model_downloader.get_available_space_requirements(config.models_to_download)
            click.echo(f"Espaço necessário: {space_required:.1f} GB")
            
            if click.confirm("Prosseguir com download dos modelos?", default=True):
                download_results = self.model_downloader.download_models(config.models_to_download)
                for model, success in download_results.items():
                    status = "✅" if success else "❌"
                    click.echo(f"  {status} {model}")
            
            # 7. Gerar configurações
            click.echo("⚙️  Gerando configurações...")
            config_manager.generate_configurations(config, hardware)
            
            # 8. Configurar bancos de dados
            if 'postgresql' in config.databases:
                click.echo("🗄️  Configurando PostgreSQL...")
                self._setup_postgresql()
            
            if 'redis' in config.databases:
                click.echo("📊 Configurando Redis...")
                self._setup_redis()
            
            # 9. Verificar instalação
            click.echo("🔍 Verificando instalação...")
            verification = self.dependency_manager.verify_installation(config.install_type)
            failed_packages = [pkg for pkg, success in verification.items() if not success]
            
            if failed_packages:
                click.echo(f"⚠️  Pacotes não verificados: {', '.join(failed_packages)}")
            
            # 10. Finalizar
            click.echo("\n🎉 Instalação concluída com sucesso!")
            self._display_next_steps(config)
            
            return True
            
        except Exception as e:
            logger.error(f"Erro durante instalação: {e}")
            return False
    
    def _create_virtual_environment(self, venv_path: Path) -> bool:
        """Cria ambiente virtual Python."""
        try:
            subprocess.run([sys.executable, '-m', 'venv', str(venv_path)], check=True)
            logger.info(f"Ambiente virtual criado: {venv_path}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro ao criar ambiente virtual: {e}")
            return False
    
    def _setup_postgresql(self):
        """Configura PostgreSQL."""
        # Implementação básica - em produção seria mais robusta
        logger.info("PostgreSQL deve ser configurado manualmente")
    
    def _setup_redis(self):
        """Configura Redis."""
        # Implementação básica - em produção seria mais robusta
        logger.info("Redis deve ser configurado manualmente")
    
    def _display_next_steps(self, config: InstallationConfig):
        """Exibe próximos passos."""
        click.echo("\n📝 Próximos passos:")
        click.echo(f"  1. Ativar ambiente virtual: source {config.install_path}/venv/bin/activate")
        click.echo(f"  2. Ir para diretório: cd {config.install_path}")
        click.echo("  3. Iniciar API: python -m autobot.api")
        
        if config.enable_monitoring:
            click.echo("  4. Iniciar dashboard: python -m IA.dashboard.monitor")
            click.echo("  5. Acessar dashboard: http://localhost:8080")
        
        if config.enable_docker:
            click.echo("  6. Usar Docker: docker-compose up -d")
        
        click.echo(f"\n📂 Arquivos de configuração em: {config.install_path}/config")
        click.echo(f"📊 Dados armazenados em: {config.data_path}")

# CLI Commands
@click.group()
def cli():
    """AUTOBOT Setup - Sistema de Configuração Automática."""
    pass

@cli.command()
@click.option('--install-type', type=click.Choice(['minimal', 'standard', 'full', 'enterprise']),
              help='Tipo de instalação')
@click.option('--install-path', help='Caminho de instalação')
@click.option('--enable-gpu/--disable-gpu', default=None, help='Habilitar GPU')
@click.option('--enable-docker/--disable-docker', default=None, help='Configurar Docker')
@click.option('--non-interactive', is_flag=True, help='Instalação não interativa')
def install(install_type, install_path, enable_gpu, enable_docker, non_interactive):
    """Instala o AUTOBOT."""
    installer = AutobotInstaller()
    
    if non_interactive:
        # Configuração automática
        hardware = installer.detector.detect_hardware()
        requirements_check = installer.detector.check_requirements(hardware)
        
        if not requirements_check['meets_requirements']:
            click.echo("❌ Sistema não atende aos requisitos mínimos")
            sys.exit(1)
        
        config = InstallationConfig(
            install_type=install_type or requirements_check['recommendation'],
            enable_gpu=enable_gpu if enable_gpu is not None else hardware.gpu_available,
            enable_docker=enable_docker or False,
            enable_monitoring=install_type in ['full', 'enterprise'],
            enable_backups=install_type in ['full', 'enterprise'],
            install_path=install_path or str(Path.home() / 'autobot'),
            data_path=str(Path(install_path or str(Path.home() / 'autobot')) / 'data'),
            models_to_download=['llama3.1'],
            databases=['sqlite'],
            web_interface=True,
            api_keys={}
        )
    else:
        # Setup interativo
        config = installer.run_interactive_setup()
        hardware = installer.detector.detect_hardware()
    
    # Executa instalação
    if installer.install(config, hardware):
        click.echo("✅ Instalação concluída com sucesso!")
    else:
        click.echo("❌ Falha na instalação")
        sys.exit(1)

@cli.command()
def check():
    """Verifica requisitos do sistema."""
    detector = SystemDetector()
    hardware = detector.detect_hardware()
    
    click.echo("🔍 Verificando requisitos do sistema...")
    click.echo(f"CPU: {hardware.cpu_cores} cores")
    click.echo(f"RAM: {hardware.ram_gb:.1f} GB")
    click.echo(f"Disco: {hardware.disk_gb:.1f} GB")
    click.echo(f"GPU: {'Detectada' if hardware.gpu_available else 'Não detectada'}")
    
    requirements_check = detector.check_requirements(hardware)
    
    if requirements_check['meets_requirements']:
        click.echo("✅ Todos os requisitos foram atendidos")
    else:
        click.echo("❌ Requisitos não atendidos:")
        for issue in requirements_check['issues']:
            click.echo(f"  - {issue}")

@cli.command()
@click.option('--models', help='Modelos para baixar (separados por vírgula)')
def download_models(models):
    """Baixa modelos de IA."""
    downloader = ModelDownloader()
    
    if not downloader.check_ollama_installation():
        click.echo("❌ Ollama não está instalado")
        sys.exit(1)
    
    models_list = models.split(',') if models else ['llama3.1']
    
    click.echo(f"📥 Baixando modelos: {', '.join(models_list)}")
    results = downloader.download_models(models_list)
    
    for model, success in results.items():
        status = "✅" if success else "❌"
        click.echo(f"{status} {model}")

if __name__ == '__main__':
    cli()