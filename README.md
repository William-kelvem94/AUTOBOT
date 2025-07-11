# 🧠 AUTOBOT - Sistema de IA Local Completo

Sistema avançado de inteligência artificial local para automação corporativa, integrando Ollama, ChromaDB e modelos personalizados.

## 🎯 **Características Principais**

### ✅ **Sistema de IA Local Completo**
- **Ollama Integration**: Modelos de linguagem rodando localmente
- **ChromaDB**: Base de dados vetorial para memória persistente  
- **Modelos Personalizados**: Treinamento específico para seu domínio
- **Memória Conversacional**: Aprendizado contínuo das interações

### 🔧 **Funcionalidades**
- 🧠 **Treinamento Local**: Crie modelos específicos para sua empresa
- 💾 **Memória Persistente**: Salva e recupera contexto de conversas
- 🔍 **Busca Semântica**: Encontra informações relevantes automaticamente
- 📊 **Métricas e Estatísticas**: Monitore o desempenho do sistema
- 🌐 **API REST Completa**: Integração fácil com outras aplicações
- 🎨 **Interface React**: Painel de controle intuitivo

### 🏢 **Especialidades Corporativas**
- **Bitrix24**: Integração e automação
- **IXCSOFT**: Sincronização de dados
- **Locaweb**: Gestão de serviços
- **PyAutoGUI**: Automação de interface
- **Selenium**: Automação web
- **OCR/Tesseract**: Processamento de documentos

## 🚀 **Instalação e Configuração**

### **Instalação Automática (Recomendada)**

```bash
# 1. Clone o repositório
git clone https://github.com/William-kelvem94/AUTOBOT.git
cd AUTOBOT

# 2. Execute o script de configuração automática
python IA/setup_ia_completo.py
```

O script automaticamente:
- ✅ Instala todas as dependências Python
- ✅ Configura Ollama e baixa modelos essenciais
- ✅ Cria estrutura de diretórios necessária
- ✅ Testa a instalação completa

### **Instalação Manual**

```bash
# 1. Instalar dependências Python
pip install -r requirements.txt

# 2. Instalar Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 3. Baixar modelos essenciais
ollama pull llama3
ollama pull mistral
ollama pull tinyllama

# 4. Criar diretórios
mkdir -p IA/{memoria_vetorial,memoria_conversas,modelos_personalizados,datasets}
```

### **Docker (Opcional)**

```bash
# Executar com Docker Compose
docker-compose -f docker-compose-ia.yml up -d

# Verificar status
docker-compose -f docker-compose-ia.yml ps
```

## 📖 **Uso do Sistema**

### **1. Inicialização**

```python
from autobot.ai import get_ai_engine
import asyncio

# Inicializar motor de IA
engine = get_ai_engine()

# Verificar status
status = engine.get_system_info()
print(f"Status: {status}")
```

### **2. Processamento de Mensagens**

```python
# Processar mensagem com IA local
result = await engine.process_message(
    message="Como integrar com Bitrix24?",
    user_id="usuario123",
    context={"empresa": "MinhaEmpresa"}
)

print(f"Resposta: {result['resposta']}")
```

### **3. Treinamento de Modelo Personalizado**

```python
from IA.treinamento import AutobotLocalTrainer

trainer = AutobotLocalTrainer()

# Exemplos de treinamento específicos
exemplos = """
P: Como configurar webhook no Bitrix24?
R: Acesse Configurações > Webhook > Criar novo webhook com URL e eventos específicos.

P: Como automatizar clique em botão?
R: Use PyAutoGUI.click(x, y) para coordenadas ou pyautogui.locateOnScreen('botao.png').
"""

# Treinar modelo personalizado
resultado = trainer.train_custom_model(exemplos, "minha-empresa-bot")
print(f"Treinamento: {resultado}")
```

### **4. Gerenciamento de Memória**

```python
from IA.treinamento import AutobotMemoryManager

memory = AutobotMemoryManager()

# Salvar conversa
memory.salvar_conversa(
    usuario="user123",
    pergunta="Como automatizar processo?",
    resposta="Use PyAutoGUI para automação de GUI",
    categoria="automacao"
)

# Buscar contexto relevante
contexto = memory.buscar_contexto("automatizar")
print(f"Encontrado: {contexto['total_encontrado']} contextos")
```

## 🌐 **API REST**

### **Endpoints Principais**

```bash
# Status do sistema
GET /api/ia/status

# Configurar sistema
POST /api/ia/setup

# Treinar modelo personalizado
POST /api/ia/treinar-personalizado
{
  "exemplos": "P: Como... R: ...",
  "nome_modelo": "meu-modelo"
}

# Testar modelo
POST /api/ia/testar-modelo
{
  "modelo": "meu-modelo",
  "pergunta": "Como automatizar?"
}

# Listar modelos
GET /api/ia/modelos

# Salvar conversa na memória
POST /api/ia/memoria/salvar
{
  "usuario": "user123",
  "pergunta": "Como integrar?",
  "resposta": "Use a API...",
  "categoria": "integracao"
}

# Buscar contexto
POST /api/ia/memoria/buscar
{
  "pergunta": "integração",
  "usuario": "user123",
  "limite": 5
}

# Estatísticas de memória
GET /api/ia/memoria/estatisticas
```

### **Integração com Flask**

```python
from flask import Flask
from IA.treinamento import register_training_api

app = Flask(__name__)

# Registrar endpoints de IA
register_training_api(app)

if __name__ == "__main__":
    app.run(debug=True)
```

## 🎨 **Interface Web**

### **Componente React**

```jsx
import TrainingPanel from './components/TrainingPanel';

function App() {
  return (
    <div>
      <h1>AUTOBOT - Sistema de IA</h1>
      <TrainingPanel />
    </div>
  );
}
```

O painel inclui:
- 🧠 **Aba Treinamento**: Criar modelos personalizados
- 🧪 **Aba Teste**: Testar modelos treinados  
- 📊 **Aba Status**: Monitorar sistema
- 💾 **Aba Memória**: Gerenciar conversas

## 📊 **Monitoramento**

### **Métricas Disponíveis**

```python
# Estatísticas do sistema
stats = memory.estatisticas_memoria()

print(f"""
📊 Estatísticas AUTOBOT:
- Conversas: {stats['estatisticas']['total_conversas']}
- Conhecimento: {stats['estatisticas']['total_conhecimento']}  
- Usuários: {stats['estatisticas']['usuarios_unicos']}
- Categorias: {stats['estatisticas']['conversas_por_categoria']}
""")
```

### **Health Check**

```python
# Verificar saúde do sistema
health = await engine.health_check()
print(f"Sistema: {health['status']}")
print(f"Componentes: {health['components']}")
```

## 🔧 **Configuração Avançada**

### **Arquivo de Configuração (IA/config/config.json)**

```json
{
  "ollama_host": "http://localhost:11434",
  "default_model": "llama3",
  "fallback_model": "tinyllama", 
  "custom_model": "autobot-personalizado",
  "max_tokens": 2048,
  "temperature": 0.7,
  "use_local_ai": true,
  "memory_enabled": true,
  "context_window": 5,
  "backup_enabled": true,
  "max_memory_days": 30
}
```

### **Variáveis de Ambiente**

```bash
# .env
OLLAMA_HOST=http://localhost:11434
CHROMA_PERSIST_DIR=IA/memoria_vetorial
AUTOBOT_DEBUG=true
AUTOBOT_LOG_LEVEL=INFO
```

## 🐳 **Docker e Produção**

### **Estrutura de Serviços**

- **Ollama**: Modelos de linguagem (porta 11434)
- **ChromaDB**: Base vetorial (porta 8000)  
- **Redis**: Cache e sessões (porta 6379)
- **Nginx**: Proxy reverso (porta 8080)
- **Prometheus**: Métricas (porta 9090)
- **Grafana**: Dashboards (porta 3000)

### **Comandos Docker**

```bash
# Iniciar todos os serviços
docker-compose -f docker-compose-ia.yml up -d

# Ver logs
docker-compose -f docker-compose-ia.yml logs -f

# Parar serviços
docker-compose -f docker-compose-ia.yml down

# Backup de dados
docker-compose -f docker-compose-ia.yml exec ollama ollama list
```

## 🧪 **Testes**

### **Testes Unitários**

```bash
# Executar todos os testes
python -m pytest tests/ -v

# Teste específico do trainer
python IA/treinamento/local_trainer.py

# Teste do memory manager
python IA/treinamento/memory_manager.py

# Teste do AI engine
python autobot/ai/engine.py
```

### **Teste de Integração**

```python
# Teste completo do sistema
from IA.setup_ia_completo import AutobotIASetup

setup = AutobotIASetup()
sucesso = setup.test_installation()
print(f"Sistema OK: {sucesso}")
```

## 🚨 **Troubleshooting**

### **Problemas Comuns**

1. **Ollama não inicia**:
   ```bash
   # Verificar se porta está livre
   lsof -i :11434
   
   # Reiniciar Ollama
   ollama serve
   ```

2. **ChromaDB erro de permissão**:
   ```bash
   # Ajustar permissões
   chmod -R 755 IA/memoria_vetorial
   ```

3. **Modelo não encontrado**:
   ```bash
   # Listar modelos disponíveis
   ollama list
   
   # Baixar modelo faltante
   ollama pull llama3
   ```

4. **Erro de importação**:
   ```bash
   # Reinstalar dependências
   pip install -r requirements.txt --force-reinstall
   ```

### **Logs e Diagnóstico**

```bash
# Logs do sistema
tail -f IA/logs/autobot.log

# Logs de setup
tail -f setup_ia.log

# Status detalhado
curl http://localhost:8080/api/ia/status
```

## 📚 **Exemplos de Uso**

### **Automação Corporativa**

```python
# Integração com Bitrix24
await engine.process_message(
    "Como criar lead automaticamente no Bitrix24?",
    user_id="vendedor1",
    context={"departamento": "vendas"}
)

# Automação GUI
await engine.process_message(
    "Como clicar no botão 'Salvar' automaticamente?",
    user_id="admin",
    context={"aplicacao": "sistema_interno"}
)
```

### **Análise de Dados**

```python
# Consulta sobre métricas
await engine.process_message(
    "Quais são as métricas de conversão deste mês?",
    user_id="gerente",
    context={"periodo": "2024-01", "departamento": "marketing"}
)
```

## 🤝 **Contribuição**

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 **Licença**

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para detalhes.

## 🆘 **Suporte**

- **Issues**: [GitHub Issues](https://github.com/William-kelvem94/AUTOBOT/issues)
- **Documentação**: [Wiki do Projeto](https://github.com/William-kelvem94/AUTOBOT/wiki)
- **Discussões**: [GitHub Discussions](https://github.com/William-kelvem94/AUTOBOT/discussions)

---

**🚀 Desenvolvido com ❤️ para automação corporativa inteligente**