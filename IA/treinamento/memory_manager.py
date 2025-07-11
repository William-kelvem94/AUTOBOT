import chromadb
from datetime import datetime
import json
import hashlib

class ConversationMemory:
    """Sistema de memória persistente para conversas do AUTOBOT"""
    
    def __init__(self):
        self.client = chromadb.PersistentClient(path="IA/memoria_conversas")
        self.conversations = self.client.get_or_create_collection("conversations")
        self.context = self.client.get_or_create_collection("context")
        
    def save_interaction(self, user_id: str, user_message: str, bot_response: str, context: dict = None):
        """Salva interação para aprendizado"""
        timestamp = datetime.now().isoformat()
        interaction_id = hashlib.md5(f"{user_id}_{timestamp}".encode()).hexdigest()
        
        conversation_text = f"Usuário: {user_message}\nAUTOBOT: {bot_response}"
        
        metadata = {
            "user_id": user_id,
            "timestamp": timestamp,
            "user_message": user_message,
            "bot_response": bot_response,
            "context": json.dumps(context or {})
        }
        
        self.conversations.add(
            ids=[interaction_id],
            documents=[conversation_text],
            metadatas=[metadata]
        )
        
    def get_user_context(self, user_id: str, limit: int = 10):
        """Recupera contexto recente do usuário"""
        try:
            results = self.conversations.query(
                query_texts=[f"user_id:{user_id}"],
                n_results=limit,
                where={"user_id": user_id}
            )
            
            return {
                "conversations": results["documents"][0] if results["documents"] else [],
                "metadata": results["metadatas"][0] if results["metadatas"] else []
            }
        except Exception as e:
            return {"error": str(e)}
    
    def search_similar_conversations(self, query: str, limit: int = 5):
        """Busca conversas similares para contexto"""
        results = self.conversations.query(
            query_texts=[query],
            n_results=limit
        )
        
        return {
            "similar_conversations": results["documents"][0] if results["documents"] else [],
            "similarity_scores": results["distances"][0] if results.get("distances") else []
        }