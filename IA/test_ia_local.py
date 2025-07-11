#!/usr/bin/env python3
"""Teste do sistema de IA local"""

import sys
from pathlib import Path

# Adiciona diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from IA.treinamento.local_trainer import AutobotLocalTrainer
    from IA.treinamento.memory_manager import ConversationMemory
    
    print("🧪 Testando sistema de IA local...")
    
    # Teste do trainer
    trainer = AutobotLocalTrainer()
    print("✅ AutobotLocalTrainer inicializado")
    
    # Teste da memória
    memory = ConversationMemory()
    print("✅ ConversationMemory inicializada")
    
    # Teste básico de conhecimento
    docs = [{"text": "AUTOBOT é um sistema de automação corporativa"}]
    result = trainer.add_knowledge(docs)
    print(f"✅ Teste de conhecimento: {result}")
    
    print("🎉 Todos os testes passaram!")
    
except Exception as e:
    print(f"❌ Erro nos testes: {e}")
    sys.exit(1)
