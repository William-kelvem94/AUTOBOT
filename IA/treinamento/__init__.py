"""
Sistema de IA Local para AUTOBOT
===============================

Este módulo implementa um sistema completo de IA local incluindo:
- Treinamento com Ollama
- Armazenamento vetorial com ChromaDB
- Memória conversacional persistente
- Integração com o sistema AUTOBOT existente
"""

# Tentar importar versões completas, fallback para versões simplificadas
try:
    from .local_trainer import AutobotLocalTrainer
except ImportError:
    try:
        from .local_trainer_simple import AutobotLocalTrainer
    except ImportError:
        AutobotLocalTrainer = None

try:
    from .memory_manager import ConversationMemory
except ImportError:
    ConversationMemory = None

try:
    from .integration_api import ai_local_bp, register_ai_blueprint
except ImportError:
    ai_local_bp = None
    register_ai_blueprint = None

__all__ = [
    'AutobotLocalTrainer',
    'ConversationMemory', 
    'ai_local_bp',
    'register_ai_blueprint'
]

__version__ = "1.0.0"