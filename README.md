# AUTOBOT - Assistente Inteligente Local

## Visão Geral

AUTOBOT é um sistema completo de IA local inspirado no conceito do Jarvis, que combina:

- IA local com LLMs (Ollama + modelos como Llama3/Mistral)
- Interface de chat responsiva
- Sistema de automação de tarefas
- Integração com webhooks e APIs
- Base de conhecimento vetorial
- Capacidades de aprendizado

## Características Principais

### 🤖 IA Local
- Integração com Ollama para LLMs locais (Llama3, Mistral, CodeLlama)
- Base de conhecimento vetorial com Qdrant
- Processamento de linguagem natural
- Sistema de aprendizado contínuo

### ⚙️ Automação Inteligente
- Criação de automações por linguagem natural
- Gravação de ações do usuário
- Execução de scripts automatizados
- Integração com aplicações web e desktop

### 🔗 Integrações
- Bitrix24 (CRM e gestão empresarial)
- Locaweb (hospedagem e serviços cloud)
- IXCSOFT (gestão para provedores)
- Fluctus (gestão de rede)

### 🌐 Interface Moderna
- Chat responsivo e intuitivo
- Dashboard de automações
- Painel de integrações
- Base de conhecimento pesquisável

## Instalação e Configuração

### Pré-requisitos
- Docker e Docker Compose
- Python 3.11+
- Node.js (para desenvolvimento frontend)

### Instalação Rápida

1. **Clone o repositório:**
```bash
git clone https://github.com/William-kelvem94/AUTOBOT.git
cd AUTOBOT
```

2. **Configure as variáveis de ambiente:**
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

3. **Inicie os serviços:**
```bash
docker-compose up -d
```

4. **Acesse a aplicação:**
- Interface Web: http://localhost
- API Documentation: http://localhost:8000/docs
- Qdrant Dashboard: http://localhost:6333/dashboard

### Configuração Manual

#### 1. Configurar Ollama
```bash
# Baixar e executar modelos
docker exec -it autobot-ollama ollama pull llama3
docker exec -it autobot-ollama ollama pull mistral
docker exec -it autobot-ollama ollama pull codellama
```

#### 2. Configurar Base de Dados
```bash
# O PostgreSQL será configurado automaticamente
# Qdrant será inicializado com as coleções necessárias
```

## Uso

### Chat Inteligente

O AUTOBOT responde a comandos em linguagem natural:

```
Usuário: "Crie uma automação para abrir o Chrome e navegar para o Google"
AUTOBOT: "Automação criada! Ela irá abrir o Chrome e navegar para google.com"

Usuário: "Execute a automação que criamos"
AUTOBOT: "Executando automação... Concluída com sucesso!"
```

### Automações

#### Criar por Linguagem Natural
```
"Automatize o login no sistema X com usuário Y"
"Crie um script para fazer backup dos arquivos"
"Automatize o envio de relatórios por email"
```

#### Gravar Ações
1. Clique em "Gravar Ações"
2. Execute as ações desejadas
3. Pare a gravação
4. Nome e salve a automação

### Integrações

#### Bitrix24
1. Configure o webhook URL no painel de integrações
2. AUTOBOT processará eventos automaticamente
3. Respostas inteligentes baseadas em IA

## Arquitetura

### Componentes Principais

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Interface │────│   FastAPI       │────│   AI Engine     │
│   (HTML/CSS/JS) │    │   Backend       │    │   (Ollama)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐
                       │   Automation    │
                       │   Engine        │
                       └─────────────────┘
                                │
                       ┌─────────────────┐
                       │   Integrations  │
                       │   (Bitrix24+)   │
                       └─────────────────┘
```

### Tecnologias

- **Backend**: Python, FastAPI, SQLAlchemy
- **IA**: Ollama, Transformers, Qdrant
- **Frontend**: HTML5, CSS3, JavaScript
- **Automação**: PyAutoGUI, Selenium, OpenCV
- **Infraestrutura**: Docker, PostgreSQL, Redis

## API

### Endpoints Principais

#### Chat
- `POST /api/chat/message` - Enviar mensagem
- `POST /api/chat/analyze` - Analisar texto
- `POST /api/chat/knowledge` - Adicionar conhecimento

#### Automação
- `POST /api/automation/create` - Criar automação
- `POST /api/automation/execute` - Executar automação
- `GET /api/automation/list` - Listar automações

#### Webhooks
- `POST /api/webhook/bitrix24` - Webhook Bitrix24
- `POST /api/webhook/generic` - Webhook genérico

#### Integrações
- `GET /api/integration/platforms` - Listar plataformas
- `POST /api/integration/configure` - Configurar integração

## Desenvolvimento

### Estrutura do Projeto

```
AUTOBOT/
├── core/                    # Motores principais
│   ├── ai_engine.py        # Interface com IA
│   ├── automation_engine.py # Motor de automação
│   └── nlp_processor.py    # Processamento NLP
├── api/                    # API REST
│   ├── main.py            # Aplicação principal
│   └── routes/            # Rotas da API
├── ui/web/                # Interface web
├── integrations/          # Integrações específicas
├── data/                  # Armazenamento
└── docs/                  # Documentação
```

### Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## Roadmap

### Fase 1 (Atual) ✅
- [x] Core + Chat + Automação básica
- [x] Interface web responsiva
- [x] Integração Bitrix24
- [x] Base de conhecimento

### Fase 2 (Próxima)
- [ ] Sistema de plugins
- [ ] Reconhecimento de voz
- [ ] OCR e visão computacional
- [ ] Mais integrações

### Fase 3 (Futuro)
- [ ] Interface desktop
- [ ] App mobile
- [ ] IA avançada
- [ ] Marketplace de automações

## Segurança

- **Dados Locais**: Tudo roda localmente, sem envio de dados externos
- **Encryption**: Comunicação WebSocket segura
- **Isolation**: Containers Docker isolados
- **Privacy**: Sem telemetria ou tracking

## Suporte

- **Documentação**: [docs/](docs/)
- **Issues**: GitHub Issues
- **Discussões**: GitHub Discussions
- **Wiki**: [GitHub Wiki](https://github.com/William-kelvem94/AUTOBOT/wiki)

## Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## Agradecimentos

- Ollama team pelo LLM local
- Qdrant team pelo banco vetorial
- FastAPI team pelo framework
- Comunidade open source

---

**AUTOBOT** - Seu assistente inteligente local 🤖