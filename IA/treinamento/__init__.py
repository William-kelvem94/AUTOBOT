"""
Módulo de Treinamento de IA - AUTOBOT
=====================================

Componentes principais para treinamento e gerenciamento de IA local:
- local_trainer: Sistema de treinamento de modelos Ollama
- memory_manager: Gerenciamento de memória conversacional
- integration_api: API REST para integração com IA
"""

from .local_trainer import LocalTrainer
from .memory_manager import MemoryManager
from .integration_api import AIIntegrationAPI

__all__ = ['LocalTrainer', 'MemoryManager', 'AIIntegrationAPI']