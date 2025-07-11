"""
Sistema avançado de treinamento de IA local para AUTOBOT
Gerencia modelos Ollama, embeddings e geração de respostas
"""

import asyncio
import hashlib
import json
import logging
import numpy as np
import torch
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

try:
    import ollama
except ImportError:
    ollama = None

try:
    import chromadb
except ImportError:
    chromadb = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

try:
    import redis
except ImportError:
    redis = None

class AutobotLocalTrainer:
    """Sistema avançado de treinamento de IA local para AUTOBOT"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        
        # Inicializa clientes apenas se disponíveis
        self.ollama_client = None
        self.chroma_client = None
        self.sentence_model = None
        self.redis_client = None
        
        self._initialize_services()
        
        self.model_cache = {}
        self.performance_metrics = {}
        
    def _setup_logging(self) -> logging.Logger:
        """Configura logging específico do trainer"""
        logger = logging.getLogger('autobot_trainer')
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        
        return logger
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        """Carrega configuração do trainer"""
        if config_path and Path(config_path).exists():
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        
        # Configuração padrão
        return {
            'ollama_url': 'http://localhost:11434',
            'chroma_path': 'IA/memoria_conversas',
            'embedding_model': 'all-MiniLM-L6-v2',
            'redis_host': 'localhost',
            'redis_port': 6379,
            'redis_db': 0,
            'models': {
                'llama3.2': {
                    'size': '3B',
                    'use_case': 'conversação geral',
                    'performance': 'alto',
                    'memory_req': '8GB'
                },
                'mistral': {
                    'size': '7B', 
                    'use_case': 'análise técnica',
                    'performance': 'médio',
                    'memory_req': '12GB'
                },
                'tinyllama': {
                    'size': '1.1B',
                    'use_case': 'respostas rápidas',
                    'performance': 'rápido',
                    'memory_req': '4GB'
                }
            }
        }
    
    def _initialize_services(self):
        """Inicializa serviços disponíveis"""
        # Ollama
        if ollama:
            try:
                self.ollama_client = ollama.Client(self.config['ollama_url'])
                self.logger.info("✅ Cliente Ollama inicializado")
            except Exception as e:
                self.logger.warning(f"⚠️ Ollama não disponível: {e}")
        
        # ChromaDB
        if chromadb:
            try:
                self.chroma_client = chromadb.PersistentClient(
                    path=self.config['chroma_path']
                )
                self.logger.info("✅ ChromaDB inicializado")
            except Exception as e:
                self.logger.warning(f"⚠️ ChromaDB não disponível: {e}")
        
        # Sentence Transformers
        if SentenceTransformer:
            try:
                self.sentence_model = SentenceTransformer(
                    self.config['embedding_model']
                )
                self.logger.info("✅ Modelo de embeddings carregado")
            except Exception as e:
                self.logger.warning(f"⚠️ Modelo de embeddings não disponível: {e}")
        
        # Redis
        if redis:
            try:
                self.redis_client = redis.Redis(
                    host=self.config['redis_host'],
                    port=self.config['redis_port'],
                    db=self.config['redis_db'],
                    decode_responses=True
                )
                self.redis_client.ping()
                self.logger.info("✅ Redis conectado")
            except Exception as e:
                self.logger.warning(f"⚠️ Redis não disponível: {e}")
    
    def setup_models(self) -> Dict[str, Any]:
        """Configura e otimiza modelos Ollama"""
        if not self.ollama_client:
            return {'error': 'Ollama não disponível'}
        
        installed_models = []
        
        for model_name, config in self.config['models'].items():
            try:
                self.logger.info(f"📥 Instalando {model_name}...")
                self.ollama_client.pull(model_name)
                
                # Configura modelo personalizado
                custom_name = f"autobot-{model_name}"
                if self._create_custom_model(model_name, custom_name):
                    installed_models.append({
                        'name': custom_name,
                        'base': model_name,
                        'config': config
                    })
                
            except Exception as e:
                self.logger.error(f"❌ Erro ao instalar {model_name}: {e}")
        
        return {
            'installed': installed_models,
            'total_count': len(installed_models),
            'timestamp': datetime.now().isoformat()
        }
    
    def _create_custom_model(self, base_model: str, custom_name: str) -> bool:
        """Cria modelo personalizado para AUTOBOT"""
        modelfile = f"""
FROM {base_model}

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER repeat_penalty 1.1

SYSTEM \"\"\"
Você é o AUTOBOT, um assistente de IA especializado em automação corporativa.

ESPECIALIDADES PRINCIPAIS:
- Integração com sistemas corporativos (Bitrix24, IXCSOFT, Locaweb, Fluctus, Newave, Uzera, PlayHub)
- Automação de processos usando PyAutoGUI e Selenium
- Análise de dados corporativos e métricas
- Navegação web inteligente e web scraping
- Processamento de webhooks e APIs REST
- Suporte a workflows complexos

DIRETRIZES DE RESPOSTA:
1. Seja sempre útil, preciso e focado em soluções corporativas
2. Forneça exemplos práticos quando relevante
3. Considere aspectos de segurança e compliance
4. Sugira otimizações e melhorias quando apropriado
5. Mantenha contexto das conversas anteriores

FORMATO DE RESPOSTA:
- Use linguagem clara e profissional
- Estruture respostas em tópicos quando necessário
- Inclua códigos de exemplo quando solicitado
- Sempre considere o contexto corporativo do AUTOBOT
\"\"\"
        """
        
        try:
            self.ollama_client.create(model=custom_name, modelfile=modelfile)
            self.logger.info(f"✅ Modelo personalizado {custom_name} criado")
            return True
        except Exception as e:
            self.logger.error(f"❌ Erro ao criar modelo {custom_name}: {e}")
            return False
    
    async def generate_response(
        self, 
        prompt: str, 
        model: str = None,
        use_context: bool = True,
        user_id: str = "anonymous"
    ) -> Dict[str, Any]:
        """Gera resposta usando IA local com contexto"""
        
        if not self.ollama_client:
            return {'error': 'Sistema de IA não disponível'}
        
        if not model:
            model = self._select_best_model(prompt)
        
        # Busca contexto se solicitado
        context = ""
        if use_context:
            context = await self._get_conversation_context(user_id)
        
        # Monta prompt final
        final_prompt = self._build_prompt(prompt, context)
        
        # Verifica cache
        cache_key = hashlib.md5(
            f"{model}:{final_prompt}".encode()
        ).hexdigest()
        
        if self.redis_client:
            cached_response = self.redis_client.get(f"response:{cache_key}")
            if cached_response:
                response = json.loads(cached_response)
                response['cached'] = True
                return response
        
        try:
            start_time = datetime.now()
            
            response = await asyncio.to_thread(
                self.ollama_client.generate,
                model=model,
                prompt=final_prompt,
                options={
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'top_k': 40
                }
            )
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            result = {
                'response': response['response'],
                'model': model,
                'response_time': response_time,
                'timestamp': end_time.isoformat(),
                'user_id': user_id,
                'cached': False
            }
            
            # Cache a resposta
            if self.redis_client:
                self.redis_client.setex(
                    f"response:{cache_key}",
                    3600,  # 1 hora
                    json.dumps(result)
                )
            
            # Atualiza métricas
            self._update_performance_metrics(model, response_time)
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao gerar resposta: {e}")
            return {
                'error': str(e),
                'model': model,
                'timestamp': datetime.now().isoformat()
            }
    
    def _select_best_model(self, prompt: str) -> str:
        """Seleciona o melhor modelo baseado no prompt"""
        prompt_lower = prompt.lower()
        
        # Análise técnica - usar Mistral
        if any(term in prompt_lower for term in ['api', 'código', 'script', 'erro', 'debug']):
            return 'autobot-mistral'
        
        # Respostas rápidas - usar TinyLlama
        if len(prompt) < 50:
            return 'autobot-tinyllama'
        
        # Padrão - usar Llama3.2
        return 'autobot-llama3.2'
    
    async def _get_conversation_context(self, user_id: str) -> str:
        """Busca contexto conversacional"""
        # Implementação básica - será expandida pelo memory_manager
        return f"Contexto para usuário: {user_id}"
    
    def _build_prompt(self, prompt: str, context: str) -> str:
        """Constrói prompt final com contexto"""
        if context:
            return f"Contexto da conversa:\n{context}\n\nPergunta atual: {prompt}"
        return prompt
    
    def _update_performance_metrics(self, model: str, response_time: float):
        """Atualiza métricas de performance"""
        if model not in self.performance_metrics:
            self.performance_metrics[model] = {
                'total_requests': 0,
                'avg_response_time': 0,
                'min_response_time': float('inf'),
                'max_response_time': 0
            }
        
        metrics = self.performance_metrics[model]
        metrics['total_requests'] += 1
        metrics['min_response_time'] = min(metrics['min_response_time'], response_time)
        metrics['max_response_time'] = max(metrics['max_response_time'], response_time)
        
        # Calcula nova média
        total = metrics['total_requests']
        current_avg = metrics['avg_response_time']
        metrics['avg_response_time'] = ((current_avg * (total - 1)) + response_time) / total
    
    def add_knowledge(self, documents: List[Dict], collection_name: str = "autobot_knowledge") -> str:
        """Adiciona documentos à base de conhecimento"""
        if not self.chroma_client or not self.sentence_model:
            return "Sistema de conhecimento não disponível"
        
        try:
            # Obtém ou cria coleção
            collection = self.chroma_client.get_or_create_collection(
                name=collection_name,
                metadata={"description": "Base de conhecimento AUTOBOT"}
            )
            
            # Processa documentos
            texts = []
            metadatas = []
            ids = []
            
            for i, doc in enumerate(documents):
                if isinstance(doc, str):
                    texts.append(doc)
                    metadatas.append({'type': 'text', 'index': i})
                    ids.append(f"doc_{i}_{datetime.now().timestamp()}")
                elif isinstance(doc, dict):
                    texts.append(doc.get('text', ''))
                    metadatas.append(doc.get('metadata', {}))
                    ids.append(doc.get('id', f"doc_{i}_{datetime.now().timestamp()}"))
            
            # Gera embeddings
            embeddings = self.sentence_model.encode(texts).tolist()
            
            # Adiciona à coleção
            collection.add(
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            
            return f"Adicionados {len(documents)} documentos à coleção {collection_name}"
            
        except Exception as e:
            self.logger.error(f"Erro ao adicionar conhecimento: {e}")
            return f"Erro: {str(e)}"
    
    def search_knowledge(self, query: str, collection_name: str = "autobot_knowledge", limit: int = 5) -> List[Dict]:
        """Busca na base de conhecimento"""
        if not self.chroma_client or not self.sentence_model:
            return []
        
        try:
            collection = self.chroma_client.get_collection(collection_name)
            
            # Busca por similaridade
            results = collection.query(
                query_texts=[query],
                n_results=limit
            )
            
            documents = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    documents.append({
                        'text': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else 0
                    })
            
            return documents
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar conhecimento: {e}")
            return []
    
    def get_available_models(self) -> List[str]:
        """Lista modelos disponíveis"""
        if not self.ollama_client:
            return []
        
        try:
            models = self.ollama_client.list()
            return [model.get('name', '') for model in models.get('models', [])]
        except Exception:
            return []
    
    def get_performance_metrics(self) -> Dict:
        """Retorna métricas de performance"""
        return {
            'models': self.performance_metrics,
            'timestamp': datetime.now().isoformat(),
            'system_status': {
                'ollama_available': self.ollama_client is not None,
                'chromadb_available': self.chroma_client is not None,
                'embeddings_available': self.sentence_model is not None,
                'redis_available': self.redis_client is not None
            }
        }