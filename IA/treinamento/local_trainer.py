import ollama
import chromadb
from sentence_transformers import SentenceTransformer
from pathlib import Path
import json
import logging

class AutobotLocalTrainer:
    """Sistema de treinamento de IA local integrado ao AUTOBOT existente"""
    
    def __init__(self):
        self.ollama_client = ollama.Client("http://localhost:11434")
        self.chroma_client = chromadb.PersistentClient(path="IA/memoria_vetorial")
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.logger = logging.getLogger(__name__)
        
    def setup_models(self):
        """Configura modelos Ollama essenciais"""
        models = {
            'llama3': 'Modelo principal de conversação',
            'mistral': 'Modelo alternativo rápido',
            'tinyllama': 'Modelo leve para hardware limitado'
        }
        
        installed = []
        for model, description in models.items():
            try:
                self.ollama_client.pull(model)
                self.logger.info(f"✅ {model} instalado: {description}")
                installed.append(model)
            except Exception as e:
                self.logger.warning(f"⚠️ Falha {model}: {e}")
        
        return installed
    
    def create_custom_model(self, name: str, system_prompt: str, base_model: str = "llama3"):
        """Cria modelo personalizado para AUTOBOT"""
        modelfile = f"""
FROM {base_model}
PARAMETER temperature 0.7
PARAMETER top_p 0.9
SYSTEM \"\"\"{system_prompt}\"\"\"
        """
        
        try:
            self.ollama_client.create(model=name, modelfile=modelfile)
            return {"status": "success", "model": name}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def add_knowledge(self, documents: list, collection_name: str = "autobot_knowledge"):
        """Adiciona documentos à base de conhecimento vetorial"""
        collection = self.chroma_client.get_or_create_collection(collection_name)
        
        for i, doc in enumerate(documents):
            if isinstance(doc, dict):
                text = doc.get('text', '')
                metadata = doc.get('metadata', {})
            else:
                text = str(doc)
                metadata = {}
            
            embedding = self.encoder.encode(text)
            collection.add(
                embeddings=[embedding.tolist()],
                documents=[text],
                metadatas=[metadata],
                ids=[f"doc_{collection_name}_{i}"]
            )
        
        return f"Adicionados {len(documents)} documentos à {collection_name}"
    
    def search_knowledge(self, query: str, collection_name: str = "autobot_knowledge", limit: int = 5):
        """Busca na base de conhecimento"""
        try:
            collection = self.chroma_client.get_collection(collection_name)
            results = collection.query(query_texts=[query], n_results=limit)
            
            return {
                "documents": results["documents"][0] if results["documents"] else [],
                "metadatas": results["metadatas"][0] if results["metadatas"] else []
            }
        except Exception as e:
            return {"error": str(e)}