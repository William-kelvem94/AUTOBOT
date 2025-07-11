# Sistema de IA Local - AUTOBOT

## Descrição

Este módulo implementa um sistema completo de IA local para o AUTOBOT, incluindo:

- **Treinamento Local** com Ollama
- **Armazenamento Vetorial** com ChromaDB
- **Memória Conversacional** persistente
- **Integração perfeita** com o sistema AUTOBOT existente

## Instalação

### 1. Setup Automático

```bash
python IA/setup_completo.py
```

### 2. Instalação Manual

```bash
# Instalar dependências
pip install -r IA/requirements_ia.txt

# Instalar Ollama (se necessário)
curl -fsSL https://ollama.com/install.sh | sh

# Configurar modelos
ollama pull tinyllama
ollama pull llama3
```

## Uso

### API Endpoints

- `POST /api/ia/local/setup` - Configurar sistema
- `POST /api/ia/local/chat` - Chat com IA local
- `POST /api/ia/local/knowledge` - Adicionar conhecimento
- `POST /api/ia/local/search` - Buscar conhecimento
- `GET /api/ia/local/status` - Status do sistema

### Exemplo de Uso

```python
from IA.treinamento import AutobotLocalTrainer, ConversationMemory

# Inicializar
trainer = AutobotLocalTrainer()
memory = ConversationMemory()

# Adicionar conhecimento
docs = [{"text": "AUTOBOT automatiza tarefas corporativas"}]
trainer.add_knowledge(docs)

# Salvar conversa
memory.save_interaction("user1", "Como usar?", "Resposta do bot")
```

## Docker

```bash
# Iniciar serviços de IA
docker-compose -f docker-compose.ia.yml up -d
```

## Teste

```bash
python IA/test_ia_local.py
```

## Integração

Para integrar com o sistema AUTOBOT existente, veja:
- `IA/integration_instructions.py`

## Estrutura

```
IA/
├── treinamento/           # Módulo principal
│   ├── local_trainer.py   # Sistema de treinamento
│   ├── memory_manager.py  # Gerenciamento de memória
│   └── integration_api.py # API de integração
├── memoria_vetorial/      # Armazenamento ChromaDB
├── memoria_conversas/     # Conversas persistentes
├── modelos_personalizados/# Modelos Ollama
└── logs/                  # Logs do sistema
```

## Funcionalidades

✅ **Sistema de IA local** completamente funcional  
✅ **Integração perfeita** com AIEngine existente  
✅ **Novos endpoints** `/api/ia/local/*`  
✅ **Memória conversacional** persistente  
✅ **Base de conhecimento** vetorial  
✅ **Setup automático** em um comando