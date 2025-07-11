"""
AUTOBOT - Sistema Completo de IA Local Corporativa
===================================================

Sistema de automação corporativa com IA local integrada.
Suporte para múltiplas integrações: Bitrix24, IXCSOFT, Locaweb, Fluctus, Newave, Uzera, PlayHub.

Módulos principais:
- api: Backend Flask principal
- automação: PyAutoGUI + Selenium
- ai: Sistema de IA local com Ollama
- integrations: Conectores para sistemas corporativos
"""

__version__ = "2.0.0"
__author__ = "AUTOBOT Team"
__description__ = "Sistema Completo de IA Local Corporativa"

# Configurações principais
DEFAULT_CONFIG = {
    'host': '0.0.0.0',
    'port': 5000,
    'debug': False,
    'ai_enabled': True,
    'ai_model': 'llama3.1',
    'max_workers': 10,
    'timeout': 30
}

# Integrações disponíveis
AVAILABLE_INTEGRATIONS = [
    'bitrix24',
    'ixcsoft', 
    'locaweb',
    'fluctus',
    'newave',
    'uzera',
    'playhub'
]