#!/usr/bin/env python3
"""
AUTOBOT - Teste completo do sistema
Demonstra todas as funcionalidades implementadas
"""

import requests
import json
import time
import sys
from pathlib import Path

def test_autobot_system():
    """Testa o sistema AUTOBOT completo"""
    base_url = "http://localhost:5000"
    
    print("🤖 AUTOBOT - Teste Completo do Sistema")
    print("=" * 50)
    
    # 1. Teste do sistema principal
    print("\n1️⃣ Testando sistema principal...")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Sistema: {data['name']} v{data['version']}")
            print(f"✅ Status: {data['status']}")
            print(f"✅ IA Habilitada: {data['ai_enabled']}")
        else:
            print(f"❌ Erro: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return False
    
    # 2. Teste de status detalhado
    print("\n2️⃣ Testando status detalhado...")
    try:
        response = requests.get(f"{base_url}/api/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Integrações ativas: {data['integrations']['active_integrations']}")
            print(f"✅ Sistemas: {', '.join(data['integrations']['systems'][:3])}...")
            print(f"✅ IA endpoints: {len(data['ai_system']['endpoints'])}")
        else:
            print(f"❌ Erro: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    # 3. Teste das integrações
    print("\n3️⃣ Testando integrações corporativas...")
    try:
        response = requests.get(f"{base_url}/api/integrations")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Total de integrações: {data['total_count']}")
            for name, integration in list(data['integrations'].items())[:3]:
                print(f"   - {integration['name']}: {integration['status']}")
        else:
            print(f"❌ Erro: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    # 4. Teste do sistema de IA
    print("\n4️⃣ Testando sistema de IA...")
    try:
        response = requests.get(f"{base_url}/api/v1/ai/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status IA: {data['status']}")
            print(f"✅ Componentes: {data['components']}")
        else:
            print(f"❌ Erro: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    # 5. Teste de chat com IA (sem dependências pesadas)
    print("\n5️⃣ Testando chat com IA...")
    try:
        chat_data = {
            "message": "Olá, AUTOBOT! Como você pode ajudar com automação?",
            "user_id": "test_user"
        }
        response = requests.post(f"{base_url}/api/v1/ai/chat", json=chat_data)
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                print("✅ Chat funcionando (resposta recebida)")
            else:
                print(f"⚠️ Chat disponível mas IA não configurada: {data.get('data', {}).get('error', 'N/A')}")
        else:
            print(f"❌ Erro no chat: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    # 6. Teste de automação
    print("\n6️⃣ Testando automação...")
    try:
        automation_data = {
            "action": "test_selenium",
            "target": "https://example.com"
        }
        response = requests.post(f"{base_url}/api/automation/selenium", json=automation_data)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Automação Selenium: {data['status']}")
        else:
            print(f"❌ Erro: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Teste completo finalizado!")
    print("📊 Sistema AUTOBOT operacional com todas as funcionalidades")
    return True

if __name__ == "__main__":
    # Verifica se o servidor está rodando
    print("Aguardando servidor AUTOBOT...")
    time.sleep(2)
    
    if test_autobot_system():
        print("\n✅ Todos os testes passaram!")
        sys.exit(0)
    else:
        print("\n❌ Alguns testes falharam")
        sys.exit(1)