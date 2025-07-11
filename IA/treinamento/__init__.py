"""
AUTOBOT - Sistema de IA Local
Pacote de treinamento e gerenciamento de IA local
"""

from .local_trainer import AutobotLocalTrainer
from .memory_manager import AutobotMemoryManager
from .training_api import training_bp, register_training_api

__version__ = "1.0.0"
__author__ = "AUTOBOT Team"

__all__ = [
    "AutobotLocalTrainer",
    "AutobotMemoryManager", 
    "training_bp",
    "register_training_api"
]