"""
AIEngine - Motor de IA do AUTOBOT
Integra sistema de IA local com Ollama e ChromaDB
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import ollama
from pathlib import Path

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIEngine:
    """Motor principal de IA do AUTOBOT com integração local"""
    
    def __init__(self, config_path: str = "IA/config/config.json"):
        """
        Inicializa o motor de IA
        
        Args:
            config_path: Caminho para arquivo de configuração
        """
        self.config = self._load_config(config_path)
        self.ollama_client = None
        self.local_trainer = None
        self.memory_manager = None
        self._initialize_components()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Carrega configuração do sistema"""
        try:
            config_file = Path(config_path)
            if config_file.exists():
                with open(config_file, 'r') as f:
                    return json.load(f)
            else:
                logger.warning(f"Config não encontrado: {config_path}. Usando padrões.")
                return self._default_config()
        except Exception as e:
            logger.error(f"Erro ao carregar config: {e}")
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """Configuração padrão do sistema"""
        return {
            "ollama_host": "http://localhost:11434",
            "default_model": "llama3",
            "fallback_model": "tinyllama",
            "custom_model": "autobot-personalizado",
            "max_tokens": 2048,
            "temperature": 0.7,
            "use_local_ai": True,
            "memory_enabled": True,
            "context_window": 5
        }
    
    def _initialize_components(self):
        """Inicializa componentes do sistema de IA"""
        try:
            # Inicializa cliente Ollama
            self.ollama_client = ollama.Client(host=self.config.get("ollama_host", "http://localhost:11434"))
            
            # Inicializa componentes locais (lazy loading)
            self._local_trainer_instance = None
            self._memory_manager_instance = None
            
            logger.info("✅ AIEngine inicializado com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar AIEngine: {e}")
            raise
    
    @property
    def local_trainer(self):
        """Lazy loading do LocalTrainer"""
        if self._local_trainer_instance is None:
            try:
                from IA.treinamento.local_trainer import AutobotLocalTrainer
                self._local_trainer_instance = AutobotLocalTrainer()
                logger.info("✅ LocalTrainer carregado")
            except Exception as e:
                logger.error(f"❌ Erro ao carregar LocalTrainer: {e}")
        return self._local_trainer_instance
    
    @property
    def memory_manager(self):
        """Lazy loading do MemoryManager"""
        if self._memory_manager_instance is None:
            try:
                from IA.treinamento.memory_manager import AutobotMemoryManager
                self._memory_manager_instance = AutobotMemoryManager()
                logger.info("✅ MemoryManager carregado")
            except Exception as e:
                logger.error(f"❌ Erro ao carregar MemoryManager: {e}")
        return self._memory_manager_instance
    
    async def process_message(self, message: str, user_id: str = "default", 
                            context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Processa mensagem usando IA local ou fallback
        
        Args:
            message: Mensagem do usuário
            user_id: ID do usuário
            context: Contexto adicional
            
        Returns:
            Dict com resposta e metadados
        """
        try:
            logger.info(f"🧠 Processando mensagem do usuário: {user_id}")
            
            # Tenta usar IA local primeiro
            if self.config.get("use_local_ai", True):
                result = await self.process_with_local_ai(message, user_id, context)
                if result["status"] == "success":
                    return result
                else:
                    logger.warning("⚠️ IA local falhou, usando fallback")
            
            # Fallback para modelo básico
            return await self.process_with_fallback(message, user_id, context)
            
        except Exception as e:
            logger.error(f"❌ Erro no processamento: {e}")
            return {
                "status": "error",
                "erro": str(e),
                "resposta": "Desculpe, ocorreu um erro no processamento da sua mensagem.",
                "timestamp": datetime.now().isoformat()
            }
    
    async def process_with_local_ai(self, message: str, user_id: str, 
                                  context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Processa com IA local personalizada
        
        Args:
            message: Mensagem do usuário
            user_id: ID do usuário
            context: Contexto adicional
            
        Returns:
            Dict com resposta da IA local
        """
        try:
            # Busca contexto na memória se habilitado
            contexto_memoria = ""
            if self.config.get("memory_enabled", True) and self.memory_manager:
                memory_context = self.memory_manager.buscar_contexto(
                    pergunta=message,
                    usuario=user_id,
                    limite=self.config.get("context_window", 5)
                )
                
                if memory_context.get("total_encontrado", 0) > 0:
                    contextos = memory_context["contexto_relevante"][:3]  # Top 3
                    contexto_memoria = "\n".join([
                        f"Contexto {i+1}: {ctx.get('documento', '')}" 
                        for i, ctx in enumerate(contextos)
                    ])
            
            # Monta prompt com contexto
            prompt_final = self._build_prompt(message, contexto_memoria, context)
            
            # Usa modelo personalizado se disponível
            modelo = self.config.get("custom_model", "autobot-personalizado")
            
            # Gera resposta
            response = self.ollama_client.generate(
                model=modelo,
                prompt=prompt_final,
                options={
                    "temperature": self.config.get("temperature", 0.7),
                    "num_predict": self.config.get("max_tokens", 2048)
                }
            )
            
            resposta = response.get('response', '').strip()
            
            # Salva na memória se habilitado
            if self.config.get("memory_enabled", True) and self.memory_manager:
                self.memory_manager.salvar_conversa(
                    usuario=user_id,
                    pergunta=message,
                    resposta=resposta,
                    contexto=json.dumps(context) if context else None,
                    categoria=self._categorize_message(message)
                )
            
            logger.info(f"✅ Resposta gerada com IA local: {len(resposta)} chars")
            return {
                "status": "success",
                "resposta": resposta,
                "modelo_usado": modelo,
                "contexto_usado": bool(contexto_memoria),
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na IA local: {e}")
            return {
                "status": "error",
                "erro": str(e),
                "resposta": "Erro na IA local"
            }
    
    async def process_with_fallback(self, message: str, user_id: str, 
                                  context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Processa com modelo de fallback
        
        Args:
            message: Mensagem do usuário
            user_id: ID do usuário
            context: Contexto adicional
            
        Returns:
            Dict com resposta do fallback
        """
        try:
            modelo_fallback = self.config.get("fallback_model", "tinyllama")
            
            # Prompt simplificado para fallback
            prompt = f"""Você é um assistente de automação corporativa. 
Responda de forma concisa e prática.

Pergunta: {message}

Resposta:"""
            
            response = self.ollama_client.generate(
                model=modelo_fallback,
                prompt=prompt,
                options={
                    "temperature": 0.5,
                    "num_predict": 1024
                }
            )
            
            resposta = response.get('response', '').strip()
            
            logger.info(f"✅ Resposta gerada com fallback: {len(resposta)} chars")
            return {
                "status": "success",
                "resposta": resposta,
                "modelo_usado": modelo_fallback,
                "tipo": "fallback",
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"❌ Erro no fallback: {e}")
            return {
                "status": "error",
                "erro": str(e),
                "resposta": "Sistema temporariamente indisponível. Tente novamente."
            }
    
    def _build_prompt(self, message: str, contexto_memoria: str, 
                     context: Optional[Dict[str, Any]] = None) -> str:
        """Constrói prompt completo com contexto"""
        
        prompt_base = """Você é o AUTOBOT, assistente especializado em automação corporativa.

Suas especialidades:
- Integração com Bitrix24, IXCSOFT, Locaweb
- Automação com PyAutoGUI e Selenium
- Análise de dados empresariais
- OCR e processamento de documentos
- Webhook e APIs REST

"""
        
        if contexto_memoria:
            prompt_base += f"Contexto de conversas anteriores:\n{contexto_memoria}\n\n"
        
        if context:
            prompt_base += f"Contexto atual: {json.dumps(context, ensure_ascii=False)}\n\n"
        
        prompt_base += f"Pergunta do usuário: {message}\n\nResposta detalhada e prática:"
        
        return prompt_base
    
    def _categorize_message(self, message: str) -> str:
        """Categoriza mensagem para organização na memória"""
        message_lower = message.lower()
        
        categorias = {
            "automacao": ["automatizar", "pyautogui", "selenium", "click", "bot"],
            "integracao": ["bitrix24", "ixcsoft", "locaweb", "api", "webhook"],
            "dados": ["dados", "análise", "relatório", "métrica", "dashboard"],
            "ocr": ["ocr", "tesseract", "texto", "imagem", "documento"],
            "configuracao": ["configurar", "instalar", "setup", "inicializar"]
        }
        
        for categoria, palavras in categorias.items():
            if any(palavra in message_lower for palavra in palavras):
                return categoria
        
        return "geral"
    
    def get_system_info(self) -> Dict[str, Any]:
        """Retorna informações do sistema de IA"""
        try:
            # Verifica modelos disponíveis
            models = self.ollama_client.list()
            modelos_disponiveis = [model['name'] for model in models.get('models', [])]
            
            # Estatísticas de memória
            memory_stats = {}
            if self.memory_manager:
                stats_result = self.memory_manager.estatisticas_memoria()
                if stats_result["status"] == "success":
                    memory_stats = stats_result["estatisticas"]
            
            return {
                "status": "operational",
                "config": self.config,
                "modelos_disponiveis": modelos_disponiveis,
                "memoria_stats": memory_stats,
                "componentes": {
                    "ollama": bool(self.ollama_client),
                    "local_trainer": self._local_trainer_instance is not None,
                    "memory_manager": self._memory_manager_instance is not None
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter info do sistema: {e}")
            return {
                "status": "error",
                "erro": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do sistema"""
        try:
            # Testa Ollama
            ollama_ok = False
            try:
                models = self.ollama_client.list()
                ollama_ok = len(models.get('models', [])) > 0
            except:
                pass
            
            # Testa memória
            memory_ok = False
            if self.memory_manager:
                try:
                    stats = self.memory_manager.estatisticas_memoria()
                    memory_ok = stats["status"] == "success"
                except:
                    pass
            
            return {
                "status": "healthy" if ollama_ok else "degraded",
                "components": {
                    "ollama": ollama_ok,
                    "memory": memory_ok,
                    "local_trainer": self.local_trainer is not None
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "erro": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Instância global para uso em toda a aplicação
_ai_engine_instance = None

def get_ai_engine() -> AIEngine:
    """Obtém instância global do AIEngine (singleton)"""
    global _ai_engine_instance
    if _ai_engine_instance is None:
        _ai_engine_instance = AIEngine()
    return _ai_engine_instance

# Funções de conveniência para uso externo
async def process_user_message(message: str, user_id: str = "default", 
                             context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Função de conveniência para processar mensagem"""
    engine = get_ai_engine()
    return await engine.process_message(message, user_id, context)

def get_system_status() -> Dict[str, Any]:
    """Função de conveniência para obter status"""
    engine = get_ai_engine()
    return engine.get_system_info()

# Teste do motor de IA
async def test_ai_engine():
    """Testa o motor de IA"""
    try:
        engine = get_ai_engine()
        
        # Teste básico
        result = await engine.process_message(
            "Como automatizar um clique em botão?",
            user_id="test_user"
        )
        
        print(f"Teste AIEngine: {result}")
        
        # Teste de status
        status = engine.get_system_info()
        print(f"Status do sistema: {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

if __name__ == "__main__":
    print("🧠 AUTOBOT - AIEngine")
    print("=" * 30)
    
    # Executa teste
    import asyncio
    result = asyncio.run(test_ai_engine())
    
    if result:
        print("✅ AIEngine funcionando!")
    else:
        print("❌ Problemas no AIEngine")