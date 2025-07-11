"""
AUTOBOT - Advanced Bitrix24 Integration Bot with AI
Enhanced version with optimized dependencies and improved functionality
"""

__version__ = "2.0.0"
__author__ = "AUTOBOT Team"
__description__ = "Advanced automation and AI system for Bitrix24"

# Core modules
from . import main
from . import api
from . import gemini

__all__ = ["main", "api", "gemini"]