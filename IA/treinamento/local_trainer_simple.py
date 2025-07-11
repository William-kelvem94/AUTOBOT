"""
Versão simplificada do local_trainer.py para demonstração
Funciona mesmo sem as dependências externas instaladas
"""

import json
import logging
from pathlib import Path

class AutobotLocalTrainer:
    """Sistema de treinamento de IA local integrado ao AUTOBOT existente"""
    
    def __init__(self):
        # Configuração básica que funciona sem dependências externas
        self.logger = logging.getLogger(__name__)
        self.base_path = Path("IA")
        self.base_path.mkdir(exist_ok=True)
        
        # Simuladores para quando as dependências não estão disponíveis
        self.ollama_available = False
        self.chroma_available = False
        self.transformers_available = False
        
        try:
            import ollama
            self.ollama_client = ollama.Client("http://localhost:11434")
            self.ollama_available = True
        except ImportError:
            self.logger.warning("Ollama não disponível - usando simulação")
            self.ollama_client = None
            
        try:
            import chromadb
            self.chroma_client = chromadb.PersistentClient(path="IA/memoria_vetorial")
            self.chroma_available = True
        except ImportError:
            self.logger.warning("ChromaDB não disponível - usando simulação")
            self.chroma_client = None
            
        try:
            from sentence_transformers import SentenceTransformer
            self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
            self.transformers_available = True
        except ImportError:
            self.logger.warning("SentenceTransformers não disponível - usando simulação")
            self.encoder = None
        
    def setup_models(self):
        """Configura modelos Ollama essenciais"""
        if not self.ollama_available:
            return ["simulação: llama3", "simulação: mistral", "simulação: tinyllama"]
            
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
        if not self.ollama_available:
            return {"status": "success", "model": f"simulado_{name}", "message": "Modelo simulado criado"}
            
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
        if not self.chroma_available:
            # Simulação com arquivo JSON
            knowledge_file = self.base_path / f"{collection_name}.json"
            existing_docs = []
            
            if knowledge_file.exists():
                try:
                    with open(knowledge_file, 'r', encoding='utf-8') as f:
                        existing_docs = json.load(f)
                except:
                    existing_docs = []
            
            # Adicionar novos documentos
            for i, doc in enumerate(documents):
                if isinstance(doc, dict):
                    text = doc.get('text', '')
                    metadata = doc.get('metadata', {})
                else:
                    text = str(doc)
                    metadata = {}
                
                existing_docs.append({
                    'id': f"doc_{collection_name}_{len(existing_docs) + i}",
                    'text': text,
                    'metadata': metadata
                })
            
            # Salvar
            with open(knowledge_file, 'w', encoding='utf-8') as f:
                json.dump(existing_docs, f, indent=2, ensure_ascii=False)
            
            return f"Adicionados {len(documents)} documentos à {collection_name} (simulação)"
        
        # Implementação real com ChromaDB quando disponível
        collection = self.chroma_client.get_or_create_collection(collection_name)
        
        for i, doc in enumerate(documents):
            if isinstance(doc, dict):
                text = doc.get('text', '')
                metadata = doc.get('metadata', {})
            else:
                text = str(doc)
                metadata = {}
            
            embedding = self.encoder.encode(text) if self.encoder else [0.1] * 768
            collection.add(
                embeddings=[embedding.tolist() if hasattr(embedding, 'tolist') else embedding],
                documents=[text],
                metadatas=[metadata],
                ids=[f"doc_{collection_name}_{i}"]
            )
        
        return f"Adicionados {len(documents)} documentos à {collection_name}"
    
    def search_knowledge(self, query: str, collection_name: str = "autobot_knowledge", limit: int = 5):
        """Busca na base de conhecimento"""
        if not self.chroma_available:
            # Simulação com arquivo JSON
            knowledge_file = self.base_path / f"{collection_name}.json"
            
            if not knowledge_file.exists():
                return {"documents": [], "metadatas": []}
            
            try:
                with open(knowledge_file, 'r', encoding='utf-8') as f:
                    docs = json.load(f)
                
                # Busca simples por texto
                query_lower = query.lower()
                results = []
                
                for doc in docs:
                    if query_lower in doc['text'].lower():
                        results.append(doc)
                        if len(results) >= limit:
                            break
                
                return {
                    "documents": [r['text'] for r in results],
                    "metadatas": [r['metadata'] for r in results]
                }
            except:
                return {"documents": [], "metadatas": []}
        
        # Implementação real quando disponível
        try:
            collection = self.chroma_client.get_collection(collection_name)
            results = collection.query(query_texts=[query], n_results=limit)
            
            return {
                "documents": results["documents"][0] if results["documents"] else [],
                "metadatas": results["metadatas"][0] if results["metadatas"] else []
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_status(self):
        """Obtém status do sistema"""
        return {
            "ollama_available": self.ollama_available,
            "chroma_available": self.chroma_available,
            "transformers_available": self.transformers_available,
            "ready": True  # Sempre pronto em modo simulação
        }