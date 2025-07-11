"""
IA - Sistema de Inteligência Artificial Local
==============================================

Módulo principal do sistema de IA local do AUTOBOT.
Implementa capacidades avançadas de processamento de linguagem natural,
memória conversacional e integração com modelos Ollama.

Componentes principais:
- treinamento: Gerenciamento de modelos e treinamento
- dashboard: Monitoramento e métricas
- backup: Sistema de backup e recuperação
- plugins: Sistema extensível de plugins
- tests: Suite de testes automatizados
"""

__version__ = "1.0.0"
__author__ = "AUTOBOT AI Team"

# Configurações de IA
AI_CONFIG = {
    'ollama_host': 'http://localhost:11434',
    'chromadb_path': './data/chromadb',
    'models': ['llama3.1', 'codellama', 'mistral'],
    'embedding_model': 'nomic-embed-text',
    'max_context_length': 4096,
    'temperature': 0.7,
    'top_p': 0.9
}

# Configurações de memória
MEMORY_CONFIG = {
    'max_conversations': 10000,
    'compression_threshold': 1000,
    'backup_interval': 3600,  # 1 hora
    'sentiment_analysis': True,
    'auto_tagging': True
}