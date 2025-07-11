"""
AUTOBOT - Motor de IA
Módulo de inteligência artificial
"""

from .engine import AIEngine, get_ai_engine, process_user_message, get_system_status

__version__ = "1.0.0"
__author__ = "AUTOBOT Team"

__all__ = [
    "AIEngine",
    "get_ai_engine", 
    "process_user_message",
    "get_system_status"
]