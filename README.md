# AUTOBOT - Sistema Completo de IA Local Corporativa

Sistema avançado de automação corporativa com IA local integrada, oferecendo capacidades completas de processamento de linguagem natural, automação de processos e integração com sistemas empresariais.

## 🚀 Características Principais

### ✅ Sistema de IA Local Completo
- **Ollama Integration**: Suporte completo para modelos locais (Llama 3.1, Mistral, CodeLlama)
- **ChromaDB**: Base de conhecimento vetorial para busca semântica
- **Memory Management**: Sistema sofisticado de memória conversacional
- **Model Optimization**: Otimização automática de parâmetros com A/B testing

### ✅ Automação Corporativa Avançada
- **7 Integrações Ativas**: Bitrix24, IXCSOFT, Locaweb, Fluctus, Newave, Uzera, PlayHub
- **PyAutoGUI + Selenium**: Automação completa de interfaces
- **API REST**: Endpoints completos para todas as funcionalidades
- **Rate Limiting**: Controle avançado de taxa e autenticação JWT

### ✅ Monitoramento Enterprise-Grade
- **Dashboard em Tempo Real**: Interface web responsiva com Material-UI
- **Métricas Avançadas**: CPU, memória, disco, performance de IA
- **Sistema de Alertas**: Notificações automáticas por email/webhook/Slack
- **Análise Conversacional**: Insights automáticos e análise de sentimentos

### ✅ Infraestrutura Robusta
- **Docker Completo**: Stack completa com 15+ serviços
- **Backup Automático**: Sistema de backup e recuperação
- **Segurança Bancária**: Criptografia end-to-end, audit logs
- **Escalabilidade Horizontal**: Configuração para múltiplas instâncias

## 🏗️ Arquitetura do Sistema

```
AUTOBOT/
├── autobot/                    # Backend Flask Principal (1,818 linhas)
│   ├── api.py                 # API REST com 7 integrações corporativas
│   └── __init__.py            # Configurações principais
├── IA/                        # Sistema de IA Local (5,000+ linhas)
│   ├── treinamento/           # Core AI Training System
│   │   ├── local_trainer.py   # Ollama + ChromaDB + Caching (500+ linhas)
│   │   ├── memory_manager.py  # Conversation Memory (400+ linhas)
│   │   ├── integration_api.py # REST API for AI (600+ linhas)
│   │   ├── model_optimizer.py # A/B Testing + Optimization (300+ linhas)
│   │   └── conversation_analyzer.py # Advanced Analytics (350+ linhas)
│   ├── dashboard/             # Monitoring & Metrics
│   │   └── monitor.py         # Real-time Dashboard (450+ linhas)
│   ├── backup/                # Backup System
│   ├── plugins/               # Plugin Framework
│   ├── tests/                 # Comprehensive Testing
│   └── setup_completo.py      # Enterprise Setup (800+ linhas)
├── web/                       # React Frontend
│   └── src/
│       └── App.jsx            # Modern UI Dashboard (632+ linhas)
├── docker-compose.full.yml    # Production Docker Stack (200+ linhas)
├── Dockerfile                 # Multi-stage Production Build
└── requirements*.txt          # Complete Dependencies
```

## 🛠️ Instalação Rápida

### Setup Automático (Recomendado)
```bash
# Clone o repositório
git clone https://github.com/William-kelvem94/AUTOBOT.git
cd AUTOBOT

# Execute o setup completo
python IA/setup_completo.py install

# Ou setup interativo
python IA/setup_completo.py install --interactive
```

### Docker (Enterprise)
```bash
# Stack completa com todos os serviços
docker-compose -f docker-compose.full.yml up -d

# Verificar status
docker-compose -f docker-compose.full.yml ps
```

### Manual (Desenvolvimento)
```bash
# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements_ia.txt

# Configurar banco
python -c "from autobot.api import init_database; init_database()"

# Iniciar serviços
python -m autobot.api &
python -m IA.dashboard.monitor &
```

## 🚀 Uso do Sistema

### API Backend
```bash
# Iniciar API principal
python -m autobot.api

# API disponível em: http://localhost:5000
# Documentação: http://localhost:5000/docs
```

### Dashboard de Monitoramento
```bash
# Iniciar dashboard
python -m IA.dashboard.monitor

# Dashboard disponível em: http://localhost:8080
```

### Frontend React
```bash
cd web
npm install
npm start

# Interface em: http://localhost:3000
```

## 📊 Integrações Corporativas

### Sistemas Suportados
- **Bitrix24**: CRM e vendas
- **IXCSOFT**: Provedor de internet
- **Locaweb**: Hospedagem e domínios
- **Fluctus**: Análise financeira
- **Newave**: Gestão de energia
- **Uzera**: E-commerce
- **PlayHub**: Gaming analytics

### Exemplo de Uso
```python
from autobot.api import AutomationEngine

# Inicializar engine
engine = AutomationEngine()

# Executar automação
result = engine.execute_automation(
    integration='bitrix24',
    action='create_lead',
    parameters={
        'title': 'Novo Lead AUTOBOT',
        'name': 'Cliente Teste',
        'email': 'cliente@empresa.com'
    }
)
```

## 🤖 Sistema de IA Local

### Capacidades
- **Modelos Locais**: Llama 3.1, Mistral, CodeLlama
- **Processamento de Linguagem Natural**: Análise de sentimentos, extração de tópicos
- **Memória Conversacional**: Histórico persistente e busca semântica
- **Otimização Automática**: A/B testing de parâmetros

### Exemplo de Chat
```python
from IA.treinamento.local_trainer import LocalTrainer

# Inicializar trainer
trainer = LocalTrainer()

# Gerar resposta
response = await trainer.generate_response(
    "Como configurar uma integração com o Bitrix24?",
    model_name="llama3.1"
)

print(response['response'])
```

## 📈 Monitoramento e Alertas

### Métricas Monitoradas
- **Sistema**: CPU, RAM, disco, rede
- **IA**: Tempo de resposta, qualidade, erro rate
- **Negócio**: Satisfação, resolução, engajamento

### Configuração de Alertas
```yaml
alert_rules:
  - id: cpu_high
    name: High CPU Usage
    metric: cpu_usage
    condition: ">"
    threshold: 80.0
    severity: warning
    channels: [email, slack]
```

## 🔒 Segurança

### Recursos Implementados
- **Autenticação JWT**: Tokens seguros com expiração
- **Rate Limiting**: Controle de taxa por usuário/IP
- **Criptografia**: End-to-end encryption
- **Audit Logs**: Rastreamento completo de ações
- **API Keys**: Autenticação para integrações

## 🐳 Deploy com Docker

### Stack Completa
O `docker-compose.full.yml` inclui:
- **AUTOBOT API**: Backend principal
- **Dashboard**: Monitoramento em tempo real
- **Ollama**: Servidor de IA local
- **PostgreSQL**: Banco principal
- **Redis**: Cache e sessões
- **Nginx**: Proxy reverso
- **Prometheus + Grafana**: Métricas avançadas
- **ElasticSearch + Kibana**: Logs centralizados
- **ChromaDB**: Base vetorial

### Comandos
```bash
# Iniciar stack completa
docker-compose -f docker-compose.full.yml up -d

# Ver logs
docker-compose -f docker-compose.full.yml logs -f

# Parar serviços
docker-compose -f docker-compose.full.yml down

# Backup
docker-compose -f docker-compose.full.yml exec postgres pg_dump -U autobot autobot > backup.sql
```

## 🧪 Testes

### Executar Testes
```bash
# Testes unitários
pytest IA/tests/test_suite.py -v

# Testes de integração
pytest IA/tests/test_integration.py -v

# Cobertura
pytest --cov=autobot --cov=IA IA/tests/ --cov-report=html
```

## 📖 Documentação

### Estrutura
- `docs/API.md`: Documentação completa da API
- `docs/SETUP.md`: Guia de instalação detalhado
- `docs/ARCHITECTURE.md`: Arquitetura do sistema
- `docs/EXAMPLES.md`: Exemplos de uso

## 🔧 Desenvolvimento

### Requisitos
- **Python**: 3.8+
- **RAM**: 8GB mínimo, 16GB recomendado
- **Disco**: 50GB mínimo, 100GB recomendado
- **GPU**: Opcional (acelera inferência de IA)

### Setup de Desenvolvimento
```bash
# Clone e configure
git clone https://github.com/William-kelvem94/AUTOBOT.git
cd AUTOBOT

# Instalar em modo desenvolvimento
pip install -e .

# Configurar pre-commit hooks
pre-commit install

# Executar em modo debug
AUTOBOT_ENV=development python -m autobot.api
```

## 📊 Métricas de Performance

### Capacidades Esperadas
- **Throughput**: 1000+ requests/minuto
- **Latência**: <2s por resposta de IA
- **Concorrência**: 100+ usuários simultâneos
- **Disponibilidade**: 99.9% uptime
- **Escalabilidade**: Horizontal automática

## 🤝 Contribuição

### Como Contribuir
1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

### Padrões de Código
- **Python**: PEP 8, type hints
- **JavaScript**: ESLint, Prettier
- **Commits**: Conventional Commits
- **Testes**: Cobertura mínima 80%

## 📝 Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🏢 Suporte Empresarial

Para suporte empresarial, customizações ou consultoria:
- **Email**: contato@autobot.com
- **Website**: https://autobot.com
- **Documentação**: https://docs.autobot.com

## 🌟 Roadmap

### Próximas Versões
- **v2.1**: Plugin marketplace
- **v2.2**: Multi-tenant support
- **v2.3**: Advanced ML pipelines
- **v3.0**: Distributed architecture

---

**AUTOBOT v2.0** - Sistema Completo de IA Local Corporativa
Desenvolvido com ❤️ para automação empresarial de próxima geração.