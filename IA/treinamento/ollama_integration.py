"""
Enhanced Ollama Integration for AUTOBOT
Optimized ChromaDB + Ollama integration with conversational memory
"""
import os
import json
import logging
import time
from typing import Dict, Any, List, Optional
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

# Configuration with environment variable support
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "localhost")
OLLAMA_PORT = os.getenv("OLLAMA_PORT", "11434")
OLLAMA_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
REQUEST_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "30"))

# Conversation memory storage
conversation_history = {}
MAX_HISTORY_LENGTH = 10

class OllamaError(Exception):
    """Custom exception for Ollama operations"""
    pass

class ConversationMemory:
    """Enhanced conversation memory management"""
    
    def __init__(self, max_length: int = MAX_HISTORY_LENGTH):
        self.max_length = max_length
        self.conversations = {}
    
    def add_interaction(self, session_id: str, user_input: str, assistant_response: str):
        """Add a new interaction to conversation history"""
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "user": user_input,
            "assistant": assistant_response
        }
        
        self.conversations[session_id].append(interaction)
        
        # Limit history length
        if len(self.conversations[session_id]) > self.max_length:
            self.conversations[session_id] = self.conversations[session_id][-self.max_length:]
    
    def get_context(self, session_id: str, include_last_n: int = 3) -> str:
        """Get conversation context for the session"""
        if session_id not in self.conversations:
            return ""
        
        recent_interactions = self.conversations[session_id][-include_last_n:]
        context_parts = []
        
        for interaction in recent_interactions:
            context_parts.append(f"Usuário: {interaction['user']}")
            context_parts.append(f"Assistente: {interaction['assistant']}")
        
        return "\n".join(context_parts)
    
    def clear_session(self, session_id: str):
        """Clear conversation history for a session"""
        if session_id in self.conversations:
            del self.conversations[session_id]
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get information about a conversation session"""
        if session_id not in self.conversations:
            return {"exists": False}
        
        interactions = self.conversations[session_id]
        return {
            "exists": True,
            "interaction_count": len(interactions),
            "first_interaction": interactions[0]["timestamp"] if interactions else None,
            "last_interaction": interactions[-1]["timestamp"] if interactions else None
        }

# Global conversation memory instance
memory = ConversationMemory()

def check_ollama_health() -> Dict[str, Any]:
    """Check if Ollama service is healthy"""
    try:
        # Check if Ollama is running
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return {
                "status": "healthy",
                "available_models": [model.get("name") for model in models],
                "model_count": len(models)
            }
        else:
            return {
                "status": "unhealthy",
                "error": f"HTTP {response.status_code}: {response.text}"
            }
    except requests.ConnectionError:
        return {
            "status": "unavailable",
            "error": f"Cannot connect to Ollama at {OLLAMA_URL}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def list_available_models() -> List[str]:
    """Get list of available Ollama models"""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return [model.get("name", "unknown") for model in models]
        else:
            logger.error(f"Failed to list models: HTTP {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        return []

def ensure_model_available(model: str) -> bool:
    """Ensure a model is available, try to pull if not"""
    available_models = list_available_models()
    
    if model in available_models:
        return True
    
    logger.info(f"Model {model} not found, attempting to pull...")
    
    try:
        # Attempt to pull the model
        response = requests.post(
            f"{OLLAMA_URL}/api/pull",
            json={"name": model},
            timeout=300  # 5 minutes for model download
        )
        
        if response.status_code == 200:
            logger.info(f"Successfully pulled model {model}")
            return True
        else:
            logger.error(f"Failed to pull model {model}: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error pulling model {model}: {e}")
        return False

def perguntar_ollama(prompt: str, model: str = DEFAULT_MODEL, session_id: str = "default", 
                    use_context: bool = True, temperature: float = 0.7) -> str:
    """
    Enhanced Ollama query with conversation memory and error handling
    """
    if not prompt or not prompt.strip():
        raise OllamaError("Prompt cannot be empty")
    
    prompt = prompt.strip()
    
    # Check Ollama health first
    health = check_ollama_health()
    if health["status"] != "healthy":
        raise OllamaError(f"Ollama service unavailable: {health.get('error', 'Unknown error')}")
    
    # Ensure model is available
    if not ensure_model_available(model):
        # Fallback to any available model
        available_models = list_available_models()
        if available_models:
            model = available_models[0]
            logger.warning(f"Using fallback model: {model}")
        else:
            raise OllamaError("No models available in Ollama")
    
    # Build context-aware prompt
    context_prompt = prompt
    if use_context and session_id:
        context = memory.get_context(session_id)
        if context:
            context_prompt = f"""Contexto da conversa anterior:
{context}

Nova pergunta: {prompt}

Responda considerando o contexto da conversa anterior."""
    
    # Prepare request
    data = {
        "model": model,
        "prompt": context_prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "top_p": 0.9,
            "top_k": 40
        }
    }
    
    start_time = time.time()
    
    try:
        logger.info(f"Sending request to Ollama model {model} (session: {session_id})")
        
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json=data,
            timeout=REQUEST_TIMEOUT
        )
        
        response.raise_for_status()
        result = response.json()
        
        if "response" in result:
            response_text = result["response"].strip()
            duration = time.time() - start_time
            
            # Store in conversation memory
            if session_id and use_context:
                memory.add_interaction(session_id, prompt, response_text)
            
            logger.info(f"Received response from Ollama in {duration:.2f}s")
            
            # Add metadata to response for debugging
            if os.getenv("DEBUG_MODE", "false").lower() == "true":
                response_text += f"\n\n[Debug: Model={model}, Duration={duration:.2f}s, Session={session_id}]"
            
            return response_text
        else:
            error_msg = f"Invalid response from Ollama: {result}"
            logger.error(error_msg)
            raise OllamaError(error_msg)
            
    except requests.Timeout:
        error_msg = f"Ollama request timed out after {REQUEST_TIMEOUT}s"
        logger.error(error_msg)
        raise OllamaError(error_msg)
    
    except requests.RequestException as e:
        error_msg = f"Network error connecting to Ollama: {e}"
        logger.error(error_msg)
        raise OllamaError(error_msg)
    
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON response from Ollama: {e}"
        logger.error(error_msg)
        raise OllamaError(error_msg)
    
    except Exception as e:
        error_msg = f"Unexpected error in Ollama integration: {e}"
        logger.error(error_msg)
        raise OllamaError(error_msg)

def perguntar_ollama_streaming(prompt: str, model: str = DEFAULT_MODEL, 
                              session_id: str = "default", callback=None) -> str:
    """
    Stream response from Ollama (for real-time UI updates)
    """
    if not prompt or not prompt.strip():
        raise OllamaError("Prompt cannot be empty")
    
    # Build context-aware prompt
    context_prompt = prompt
    if session_id:
        context = memory.get_context(session_id)
        if context:
            context_prompt = f"Contexto: {context}\n\nPergunta: {prompt}"
    
    data = {
        "model": model,
        "prompt": context_prompt,
        "stream": True
    }
    
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json=data,
            stream=True,
            timeout=REQUEST_TIMEOUT
        )
        
        response.raise_for_status()
        
        full_response = ""
        for line in response.iter_lines():
            if line:
                try:
                    chunk = json.loads(line)
                    if "response" in chunk:
                        token = chunk["response"]
                        full_response += token
                        
                        # Call callback for real-time updates
                        if callback:
                            callback(token)
                        
                        # Check if this is the final chunk
                        if chunk.get("done", False):
                            break
                            
                except json.JSONDecodeError:
                    continue
        
        # Store in conversation memory
        if session_id:
            memory.add_interaction(session_id, prompt, full_response)
        
        return full_response
        
    except Exception as e:
        error_msg = f"Streaming error: {e}"
        logger.error(error_msg)
        raise OllamaError(error_msg)

def get_model_info(model: str = DEFAULT_MODEL) -> Dict[str, Any]:
    """Get detailed information about a model"""
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/show",
            json={"name": model},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Model {model} not found"}
            
    except Exception as e:
        return {"error": str(e)}

def delete_model(model: str) -> Dict[str, Any]:
    """Delete a model from Ollama"""
    try:
        response = requests.delete(
            f"{OLLAMA_URL}/api/delete",
            json={"name": model},
            timeout=30
        )
        
        if response.status_code == 200:
            return {"success": True, "message": f"Model {model} deleted"}
        else:
            return {"success": False, "error": response.text}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_conversation_stats() -> Dict[str, Any]:
    """Get statistics about conversation memory"""
    total_conversations = len(memory.conversations)
    total_interactions = sum(len(conv) for conv in memory.conversations.values())
    
    active_sessions = []
    for session_id, interactions in memory.conversations.items():
        if interactions:
            active_sessions.append({
                "session_id": session_id,
                "interaction_count": len(interactions),
                "last_activity": interactions[-1]["timestamp"]
            })
    
    return {
        "total_conversations": total_conversations,
        "total_interactions": total_interactions,
        "active_sessions": active_sessions,
        "memory_limit": memory.max_length
    }

def clear_conversation_memory(session_id: str = None) -> Dict[str, Any]:
    """Clear conversation memory for a specific session or all sessions"""
    if session_id:
        memory.clear_session(session_id)
        return {"message": f"Cleared memory for session {session_id}"}
    else:
        cleared_count = len(memory.conversations)
        memory.conversations.clear()
        return {"message": f"Cleared memory for {cleared_count} sessions"}

# ChromaDB Integration (if available)
try:
    import chromadb
    from chromadb.config import Settings
    
    class VectorMemory:
        """Vector-based conversation memory using ChromaDB"""
        
        def __init__(self, collection_name: str = "autobot_conversations"):
            self.client = chromadb.Client(Settings(anonymized_telemetry=False))
            self.collection = self.client.get_or_create_collection(collection_name)
        
        def store_interaction(self, session_id: str, user_input: str, assistant_response: str):
            """Store interaction in vector database"""
            doc_id = f"{session_id}_{int(time.time())}"
            document = f"User: {user_input}\nAssistant: {assistant_response}"
            
            self.collection.add(
                documents=[document],
                ids=[doc_id],
                metadatas=[{
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "user_input": user_input,
                    "assistant_response": assistant_response
                }]
            )
        
        def find_similar_conversations(self, query: str, n_results: int = 3) -> List[Dict]:
            """Find similar conversations using vector search"""
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            return [
                {
                    "document": doc,
                    "metadata": meta,
                    "distance": dist
                }
                for doc, meta, dist in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0]
                )
            ]
    
    # Initialize vector memory if ChromaDB is available
    try:
        vector_memory = VectorMemory()
        CHROMADB_AVAILABLE = True
        logger.info("ChromaDB vector memory initialized")
    except Exception as e:
        CHROMADB_AVAILABLE = False
        logger.warning(f"ChromaDB not available: {e}")
        
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.info("ChromaDB not installed - vector memory disabled")

if __name__ == "__main__":
    # Test the Ollama integration
    print("Testing Ollama integration...")
    
    # Check health
    health = check_ollama_health()
    print(f"Ollama health: {health}")
    
    if health["status"] == "healthy":
        # Test basic query
        try:
            response = perguntar_ollama("Olá! Como você está?", session_id="test")
            print(f"Response: {response}")
            
            # Test with context
            response2 = perguntar_ollama("E você, como está se sentindo?", session_id="test")
            print(f"Context response: {response2}")
            
            # Show conversation stats
            stats = get_conversation_stats()
            print(f"Conversation stats: {stats}")
            
        except Exception as e:
            print(f"Error testing Ollama: {e}")
    
    # Test ChromaDB if available
    if CHROMADB_AVAILABLE:
        print("\nTesting ChromaDB integration...")
        try:
            vector_memory.store_interaction("test", "Olá", "Olá! Como posso ajudar?")
            similar = vector_memory.find_similar_conversations("cumprimento")
            print(f"Similar conversations: {similar}")
        except Exception as e:
            print(f"ChromaDB error: {e}")
    
    print("Ollama integration test completed!")