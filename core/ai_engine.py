"""
AI Engine - Central intelligence system for AUTOBOT
Integrates with Ollama for local LLMs and manages AI processing
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

import httpx
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models

logger = logging.getLogger(__name__)

@dataclass
class AIResponse:
    """Response from AI processing"""
    content: str
    confidence: float
    metadata: Dict[str, Any]
    timestamp: datetime
    model_used: str

@dataclass
class ConversationContext:
    """Context for maintaining conversation state"""
    user_id: str
    session_id: str
    history: List[Dict[str, str]]
    metadata: Dict[str, Any]

class AIEngine:
    """
    Central AI engine that coordinates between different AI services
    """
    
    def __init__(self, 
                 ollama_url: str = "http://localhost:11434",
                 qdrant_url: str = "http://localhost:6333",
                 default_model: str = "llama3"):
        self.ollama_url = ollama_url
        self.qdrant_url = qdrant_url
        self.default_model = default_model
        
        # Initialize components
        self.embedding_model = None
        self.vector_client = None
        self.context_store: Dict[str, ConversationContext] = {}
        
    async def initialize(self):
        """Initialize AI components"""
        try:
            # Initialize embedding model
            logger.info("Loading embedding model...")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Initialize vector database
            logger.info("Connecting to Qdrant...")
            self.vector_client = QdrantClient(url=self.qdrant_url)
            
            # Create collections if they don't exist
            await self._setup_collections()
            
            # Test Ollama connection
            await self._test_ollama_connection()
            
            logger.info("AI Engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI Engine: {e}")
            raise
    
    async def _setup_collections(self):
        """Setup Qdrant collections for vector storage"""
        try:
            collections = ["conversations", "knowledge", "automations"]
            
            for collection_name in collections:
                try:
                    self.vector_client.get_collection(collection_name)
                except Exception:
                    # Collection doesn't exist, create it
                    self.vector_client.create_collection(
                        collection_name=collection_name,
                        vectors_config=models.VectorParams(
                            size=384,  # all-MiniLM-L6-v2 embedding size
                            distance=models.Distance.COSINE
                        )
                    )
                    logger.info(f"Created collection: {collection_name}")
                    
        except Exception as e:
            logger.error(f"Failed to setup collections: {e}")
    
    async def _test_ollama_connection(self):
        """Test connection to Ollama service"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.ollama_url}/api/tags")
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    logger.info(f"Connected to Ollama, available models: {[m['name'] for m in models]}")
                else:
                    logger.warning("Ollama connection test failed")
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
    
    async def process_message(self, 
                            message: str, 
                            user_id: str,
                            session_id: str,
                            context: Optional[Dict] = None) -> AIResponse:
        """
        Process a user message and generate an intelligent response
        """
        try:
            # Get or create conversation context
            ctx_key = f"{user_id}_{session_id}"
            if ctx_key not in self.context_store:
                self.context_store[ctx_key] = ConversationContext(
                    user_id=user_id,
                    session_id=session_id,
                    history=[],
                    metadata={}
                )
            
            conversation_ctx = self.context_store[ctx_key]
            
            # Add user message to history
            conversation_ctx.history.append({
                "role": "user",
                "content": message,
                "timestamp": datetime.now().isoformat()
            })
            
            # Search relevant knowledge
            relevant_context = await self._search_knowledge(message)
            
            # Generate response using Ollama
            response_content = await self._generate_response(
                message, 
                conversation_ctx, 
                relevant_context,
                context or {}
            )
            
            # Add AI response to history
            conversation_ctx.history.append({
                "role": "assistant", 
                "content": response_content,
                "timestamp": datetime.now().isoformat()
            })
            
            # Store conversation in vector database
            await self._store_conversation_vector(conversation_ctx, message, response_content)
            
            return AIResponse(
                content=response_content,
                confidence=0.85,  # Could be improved with actual confidence scoring
                metadata={
                    "relevant_context": relevant_context,
                    "context": context or {}
                },
                timestamp=datetime.now(),
                model_used=self.default_model
            )
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return AIResponse(
                content="Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente.",
                confidence=0.0,
                metadata={"error": str(e)},
                timestamp=datetime.now(),
                model_used="error"
            )
    
    async def _search_knowledge(self, query: str, limit: int = 5) -> List[Dict]:
        """Search relevant knowledge from vector database"""
        try:
            if not self.embedding_model or not self.vector_client:
                return []
            
            # Generate embedding for query
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Search in knowledge collection
            results = self.vector_client.search(
                collection_name="knowledge",
                query_vector=query_embedding,
                limit=limit,
                score_threshold=0.7
            )
            
            return [
                {
                    "content": result.payload.get("content", ""),
                    "source": result.payload.get("source", ""),
                    "score": result.score
                }
                for result in results
            ]
            
        except Exception as e:
            logger.error(f"Error searching knowledge: {e}")
            return []
    
    async def _generate_response(self, 
                               message: str, 
                               context: ConversationContext,
                               relevant_context: List[Dict],
                               additional_context: Dict) -> str:
        """Generate response using Ollama"""
        try:
            # Build conversation history for context
            conversation_history = "\n".join([
                f"{msg['role']}: {msg['content']}" 
                for msg in context.history[-10:]  # Last 10 messages
            ])
            
            # Build knowledge context
            knowledge_context = "\n".join([
                f"Conhecimento relevante: {ctx['content']}"
                for ctx in relevant_context[:3]  # Top 3 relevant pieces
            ])
            
            # Build prompt
            system_prompt = """Você é o AUTOBOT, um assistente inteligente local capaz de:
- Responder perguntas e ter conversas naturais
- Executar automações e tarefas do sistema
- Integrar com APIs e webhooks
- Aprender e se adaptar ao usuário

Seja útil, preciso e proativo. Use o contexto fornecido quando relevante."""

            prompt = f"""{system_prompt}

Contexto da conversa:
{conversation_history}

{knowledge_context}

Contexto adicional: {json.dumps(additional_context, ensure_ascii=False)}

Usuário: {message}
Assistente:"""

            # Call Ollama API
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.default_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "top_p": 0.9,
                            "max_tokens": 500
                        }
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "Desculpe, não consegui gerar uma resposta.")
                else:
                    logger.error(f"Ollama API error: {response.status_code}")
                    return "Desculpe, o serviço de IA está temporariamente indisponível."
                    
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "Desculpe, ocorreu um erro ao gerar a resposta."
    
    async def _store_conversation_vector(self, 
                                       context: ConversationContext,
                                       user_message: str,
                                       ai_response: str):
        """Store conversation in vector database for future reference"""
        try:
            if not self.embedding_model or not self.vector_client:
                return
            
            # Create conversation text for embedding
            conversation_text = f"Usuário: {user_message}\nAssistente: {ai_response}"
            
            # Generate embedding
            embedding = self.embedding_model.encode(conversation_text).tolist()
            
            # Store in vector database
            self.vector_client.upsert(
                collection_name="conversations",
                points=[
                    models.PointStruct(
                        id=f"{context.user_id}_{context.session_id}_{len(context.history)}",
                        vector=embedding,
                        payload={
                            "user_id": context.user_id,
                            "session_id": context.session_id,
                            "user_message": user_message,
                            "ai_response": ai_response,
                            "timestamp": datetime.now().isoformat(),
                            "conversation_text": conversation_text
                        }
                    )
                ]
            )
            
        except Exception as e:
            logger.error(f"Error storing conversation vector: {e}")
    
    async def generate_automation(self, description: str, user_id: str) -> Dict:
        """Generate automation script from natural language description"""
        try:
            prompt = f"""Como AUTOBOT, analise esta descrição e gere um script de automação:

Descrição: {description}

Gere um JSON com a seguinte estrutura:
{{
    "name": "nome_da_automacao",
    "description": "descrição detalhada",
    "steps": [
        {{"action": "click", "target": "elemento", "parameters": {{}}}},
        {{"action": "type", "text": "texto", "parameters": {{}}}},
        {{"action": "wait", "duration": 2, "parameters": {{}}}}
    ],
    "triggers": ["evento1", "evento2"],
    "conditions": []
}}

Responda apenas com o JSON válido:"""

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.default_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.3}
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    automation_json = result.get("response", "{}")
                    
                    try:
                        automation = json.loads(automation_json)
                        return automation
                    except json.JSONDecodeError:
                        logger.error("Invalid JSON generated for automation")
                        return {"error": "Não foi possível gerar uma automação válida"}
                        
        except Exception as e:
            logger.error(f"Error generating automation: {e}")
            return {"error": str(e)}
    
    async def learn_from_interaction(self, interaction: Dict):
        """Learn and improve from user interactions"""
        try:
            # Store interaction for learning
            if self.embedding_model and self.vector_client:
                interaction_text = f"Interação: {json.dumps(interaction, ensure_ascii=False)}"
                embedding = self.embedding_model.encode(interaction_text).tolist()
                
                self.vector_client.upsert(
                    collection_name="knowledge",
                    points=[
                        models.PointStruct(
                            id=f"interaction_{datetime.now().timestamp()}",
                            vector=embedding,
                            payload={
                                "type": "interaction",
                                "content": interaction_text,
                                "timestamp": datetime.now().isoformat(),
                                "source": "user_interaction",
                                **interaction
                            }
                        )
                    ]
                )
                
        except Exception as e:
            logger.error(f"Error learning from interaction: {e}")
    
    async def add_knowledge(self, content: str, source: str = "manual", metadata: Dict = None):
        """Add knowledge to the vector database"""
        try:
            if not self.embedding_model or not self.vector_client:
                return False
            
            # Generate embedding
            embedding = self.embedding_model.encode(content).tolist()
            
            # Store in knowledge collection
            self.vector_client.upsert(
                collection_name="knowledge",
                points=[
                    models.PointStruct(
                        id=f"knowledge_{datetime.now().timestamp()}",
                        vector=embedding,
                        payload={
                            "content": content,
                            "source": source,
                            "timestamp": datetime.now().isoformat(),
                            "metadata": metadata or {}
                        }
                    )
                ]
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding knowledge: {e}")
            return False