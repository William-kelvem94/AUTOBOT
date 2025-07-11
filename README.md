# 🤖 AUTOBOT - Sistema de Automação Corporativa com IA Local

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Sistema completo de automação corporativa com inteligência artificial local, integrando 7 sistemas corporativos e oferecendo capacidades avançadas de IA sem dependência de serviços externos.

## 🚀 Características Principais

### ✅ **Sistema Core Implementado**
- **Backend Flask**: API REST completa com 2.400+ linhas
- **Frontend React**: Interface moderna com 632 linhas
- **7 Integrações Corporativas**: Bitrix24, IXCSOFT, Locaweb, Fluctus, Newave, Uzera, PlayHub
- **Sistema de IA Local**: Ollama + ChromaDB + Redis
- **Memória Conversacional**: Análise semântica avançada
- **Automação**: PyAutoGUI + Selenium + Webhooks

### 🤖 **IA Local Enterprise**
- **Modelos Suportados**: Llama3.2, Mistral, TinyLlama
- **Embeddings**: Sentence Transformers
- **Memória Vetorial**: ChromaDB persistente
- **Cache Inteligente**: Redis com TTL
- **Análise de Sentimento**: TextBlob integrado
- **Contexto Conversacional**: Até 24h de histórico

### 🔗 **Integrações Corporativas**
- **Bitrix24**: CRM e gestão empresarial
- **IXCSOFT**: Sistema para provedores
- **Locaweb**: Hospedagem e domínios
- **Fluctus**: Gestão de telecomunicações
- **Newave**: Soluções de conectividade
- **Uzera**: Plataforma de streaming
- **PlayHub**: Hub de entretenimento

## 📦 Instalação e Configuração

### **Método 1: Instalação Rápida**
```bash
# Clone o repositório
git clone https://github.com/William-kelvem94/AUTOBOT.git
cd AUTOBOT

# Execute o setup automático
python main.py
```

### **Método 2: Docker (Recomendado)**
```bash
# Inicia todos os serviços
docker-compose up -d

# Acessa aplicação
curl http://localhost:5000
```

### **Método 3: Instalação Manual**
```bash
# Instala dependências
pip install -r requirements.txt

# Configura IA local
python IA/setup_completo.py

# Inicia servidor
python autobot/api.py
```

## 🔧 Configuração do Sistema

### **Variáveis de Ambiente**
```bash
# .env
DEBUG=True
SECRET_KEY=autobot-secret-key
PORT=5000

# IA Configuration
OLLAMA_URL=http://localhost:11434
CHROMA_PATH=IA/memoria_conversas
REDIS_HOST=localhost
REDIS_PORT=6379
```

### **Configuração da IA (IA/config.yaml)**
```yaml
ollama:
  host: localhost
  port: 11434
  models:
    - llama3.2
    - mistral
    - tinyllama

ai:
  embedding_model: all-MiniLM-L6-v2
  temperature: 0.7
  max_context_length: 4096
```

## 🌐 API Endpoints

### **Endpoints Principais**
- `GET /` - Informações do sistema
- `GET /api/status` - Status detalhado
- `GET /api/integrations` - Lista integrações
- `POST /api/webhook` - Processamento de webhooks

### **Endpoints de IA**
- `POST /api/v1/ai/chat` - Chat com IA local
- `POST /api/v1/ai/setup` - Configuração inicial
- `POST /api/v1/ai/knowledge/add` - Adiciona conhecimento
- `POST /api/v1/ai/knowledge/search` - Busca na base
- `GET /api/v1/ai/status` - Status da IA
- `GET /api/v1/ai/metrics` - Métricas de performance

### **Endpoints de Automação**
- `POST /api/automation/selenium` - Automação web
- `POST /api/automation/pyautogui` - Automação desktop

## 💬 Exemplo de Uso da IA

```bash
# Chat com IA local
curl -X POST http://localhost:5000/api/v1/ai/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Como integrar o Bitrix24 com automação?",
    "user_id": "user123"
  }'
```

**Resposta:**
```json
{
  "status": "success",
  "data": {
    "response": "Para integrar o Bitrix24 com automação...",
    "model": "autobot-llama3.2",
    "response_time": 1.23,
    "cached": false
  }
}
```

## 🏗️ Arquitetura do Sistema

```
AUTOBOT/
├── 🤖 IA/                          # Sistema de IA Local
│   ├── setup_completo.py          # Configuração principal
│   ├── config.yaml                # Configurações
│   └── treinamento/               # Módulos de IA
│       ├── local_trainer.py       # Treinamento local
│       ├── memory_manager.py      # Memória conversacional
│       └── integration_api.py     # API de integração
│
├── 🌐 autobot/                     # Backend Flask
│   ├── api.py                     # API principal
│   └── integrações/              # Integrações corporativas
│
├── 🎨 web/                        # Frontend React
│   ├── src/App.jsx               # Componente principal
│   ├── src/App.css               # Estilos
│   └── package.json              # Dependências
│
├── 🐳 Docker/                     # Containerização
│   ├── docker-compose.yml        # Orquestração
│   └── Dockerfile                # Build da aplicação
│
└── 📄 Configurações
    ├── requirements.txt           # Deps Python
    ├── main.py                   # Ponto de entrada
    └── .env                      # Variáveis ambiente
```

## 🚀 Funcionalidades Avançadas

### **1. Memória Conversacional**
- Análise semântica automática
- Detecção de entidades e tópicos
- Contexto temporal inteligente
- Perfis de usuário dinâmicos

### **2. Sistema de Cache**
- Cache Redis para respostas
- TTL configurável
- Invalidação inteligente
- Métricas de hit/miss

### **3. Automação Corporativa**
- Selenium para automação web
- PyAutoGUI para desktop
- Webhooks para integração
- Agendamento de tarefas

### **4. Monitoramento**
- Métricas de performance
- Logs estruturados
- Health checks
- Status em tempo real

## 🔧 Desenvolvimento

### **Executar em Modo Debug**
```bash
export DEBUG=True
python main.py
```

### **Executar Testes**
```bash
python -m pytest tests/
```

### **Build para Produção**
```bash
docker build -t autobot:latest .
docker run -p 5000:5000 autobot:latest
```

## 📊 Métricas e Monitoramento

O sistema inclui métricas detalhadas:
- **Performance da IA**: Tempo de resposta, cache hits
- **Integrações**: Status, latência, erros
- **Automação**: Jobs executados, taxa de sucesso
- **Sistema**: CPU, memória, disco

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📋 Roadmap

- [ ] Interface web avançada
- [ ] Mais modelos de IA
- [ ] Integração com mais sistemas
- [ ] API GraphQL
- [ ] Dashboard analytics
- [ ] Mobile app

## 📝 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🆘 Suporte

Para suporte e dúvidas:
- 📧 Email: suporte@autobot.com
- 💬 Discord: [AUTOBOT Community]
- 📖 Documentação: [docs.autobot.com]

---

**Desenvolvido com ❤️ pela equipe AUTOBOT**