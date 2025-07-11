"""
Gerenciador avançado de memória conversacional para AUTOBOT
Utiliza ChromaDB para armazenamento vetorial e análise semântica
"""

import asyncio
import hashlib
import json
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import numpy as np

try:
    import chromadb
except ImportError:
    chromadb = None

try:
    from textblob import TextBlob
except ImportError:
    TextBlob = None

class ConversationMemoryManager:
    """Gerenciador avançado de memória conversacional"""
    
    def __init__(self, chroma_path: str = "IA/memoria_conversas"):
        self.chroma_path = Path(chroma_path)
        self.chroma_path.mkdir(parents=True, exist_ok=True)
        
        self.logger = self._setup_logging()
        
        # Inicializa ChromaDB se disponível
        self.client = None
        self.conversations = None
        self.user_profiles = None
        
        if chromadb:
            try:
                self.client = chromadb.PersistentClient(path=str(self.chroma_path))
                self.conversations = self.client.get_or_create_collection(
                    "conversations",
                    metadata={"description": "Conversas do AUTOBOT"}
                )
                self.user_profiles = self.client.get_or_create_collection(
                    "user_profiles", 
                    metadata={"description": "Perfis de usuário"}
                )
                self.logger.info("✅ ChromaDB inicializado para memória conversacional")
            except Exception as e:
                self.logger.warning(f"⚠️ ChromaDB não disponível: {e}")
        
        self.semantic_cache = {}
        
        # Cache local para quando ChromaDB não está disponível
        self.local_conversations = {}
        self.local_profiles = {}
    
    def _setup_logging(self) -> logging.Logger:
        """Configura logging específico do memory manager"""
        logger = logging.getLogger('autobot_memory')
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        
        return logger
    
    async def save_interaction(
        self,
        user_id: str,
        user_message: str, 
        bot_response: str,
        context: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """Salva interação com análise semântica"""
        
        timestamp = datetime.now()
        interaction_id = self._generate_interaction_id(user_id, timestamp)
        
        # Análise de sentimento se TextBlob disponível
        user_sentiment = None
        bot_sentiment = None
        
        if TextBlob:
            try:
                user_sentiment = TextBlob(user_message).sentiment
                bot_sentiment = TextBlob(bot_response).sentiment
            except Exception as e:
                self.logger.warning(f"Erro na análise de sentimento: {e}")
        
        # Extração de entidades e tópicos
        entities = self._extract_entities(user_message)
        topics = self._extract_topics(user_message, bot_response)
        
        # Monta documento conversacional
        conversation_text = f"""
Usuário: {user_message}
AUTOBOT: {bot_response}
        """
        
        # Metadados enriquecidos
        enriched_metadata = {
            "user_id": user_id,
            "timestamp": timestamp.isoformat(),
            "user_message": user_message,
            "bot_response": bot_response,
            "entities": entities,
            "topics": topics,
            "context": json.dumps(context or {}),
            "metadata": json.dumps(metadata or {}),
            "interaction_length": len(user_message) + len(bot_response),
            "response_quality": self._assess_response_quality(user_message, bot_response)
        }
        
        # Adiciona sentimentos se disponíveis
        if user_sentiment:
            enriched_metadata.update({
                "user_sentiment_polarity": user_sentiment.polarity,
                "user_sentiment_subjectivity": user_sentiment.subjectivity
            })
        
        if bot_sentiment:
            enriched_metadata.update({
                "bot_sentiment_polarity": bot_sentiment.polarity
            })
        
        # Salva na coleção ou cache local
        if self.conversations:
            try:
                self.conversations.add(
                    ids=[interaction_id],
                    documents=[conversation_text],
                    metadatas=[enriched_metadata]
                )
            except Exception as e:
                self.logger.error(f"Erro ao salvar no ChromaDB: {e}")
                self._save_to_local_cache(interaction_id, conversation_text, enriched_metadata)
        else:
            self._save_to_local_cache(interaction_id, conversation_text, enriched_metadata)
        
        # Atualiza perfil do usuário
        await self._update_user_profile(user_id, enriched_metadata)
        
        return interaction_id
    
    def _save_to_local_cache(self, interaction_id: str, text: str, metadata: Dict):
        """Salva conversa no cache local"""
        if interaction_id not in self.local_conversations:
            self.local_conversations[interaction_id] = {
                'text': text,
                'metadata': metadata
            }
    
    async def get_conversation_context(
        self,
        user_id: str,
        limit: int = 5,
        time_window_hours: int = 24
    ) -> Dict[str, Any]:
        """Recupera contexto conversacional inteligente"""
        
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
        
        try:
            conversations = []
            metadatas = []
            
            if self.conversations:
                # Busca no ChromaDB
                results = self.conversations.query(
                    query_texts=[f"user_id:{user_id}"],
                    n_results=limit * 2,  # Busca mais para filtrar
                    where={
                        "user_id": user_id
                    }
                )
                
                if results["documents"] and results["documents"][0]:
                    conversations = results["documents"][0]
                    metadatas = results["metadatas"][0]
            else:
                # Busca no cache local
                for conv_id, conv_data in self.local_conversations.items():
                    meta = conv_data['metadata']
                    if meta.get('user_id') == user_id:
                        try:
                            conv_time = datetime.fromisoformat(meta['timestamp'])
                            if conv_time >= cutoff_time:
                                conversations.append(conv_data['text'])
                                metadatas.append(meta)
                        except Exception:
                            continue
            
            if not conversations:
                return {"conversations": [], "summary": "", "patterns": {}}
            
            # Filtra por relevância e tempo
            filtered_conversations = []
            total_sentiment = 0
            topics_count = {}
            
            for conv, meta in zip(conversations, metadatas):
                if len(filtered_conversations) >= limit:
                    break
                
                # Verifica tempo
                try:
                    conv_time = datetime.fromisoformat(meta["timestamp"])
                    if conv_time < cutoff_time:
                        continue
                except Exception:
                    continue
                    
                filtered_conversations.append({
                    "text": conv,
                    "timestamp": meta["timestamp"],
                    "sentiment": meta.get("user_sentiment_polarity", 0),
                    "topics": meta.get("topics", [])
                })
                
                total_sentiment += meta.get("user_sentiment_polarity", 0)
                
                for topic in meta.get("topics", []):
                    topics_count[topic] = topics_count.get(topic, 0) + 1
            
            # Gera resumo contextual
            avg_sentiment = total_sentiment / len(filtered_conversations) if filtered_conversations else 0
            main_topics = sorted(topics_count.items(), key=lambda x: x[1], reverse=True)[:3]
            
            summary = self._generate_context_summary(
                filtered_conversations, avg_sentiment, main_topics
            )
            
            return {
                "conversations": filtered_conversations,
                "summary": summary,
                "patterns": {
                    "average_sentiment": avg_sentiment,
                    "main_topics": main_topics,
                    "conversation_count": len(filtered_conversations),
                    "time_span_hours": time_window_hours
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao recuperar contexto: {e}")
            return {"conversations": [], "summary": "", "patterns": {}}
    
    def _generate_interaction_id(self, user_id: str, timestamp: datetime) -> str:
        """Gera ID único para interação"""
        return f"{user_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}_{timestamp.microsecond}"
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extrai entidades nomeadas do texto"""
        entities = []
        
        # Entidades específicas do AUTOBOT
        corporate_systems = [
            "bitrix24", "ixcsoft", "locaweb", "fluctus", 
            "newave", "uzera", "playhub"
        ]
        
        text_lower = text.lower()
        for system in corporate_systems:
            if system in text_lower:
                entities.append(system.upper())
        
        # Entidades técnicas
        tech_terms = [
            "api", "webhook", "automation", "selenium", 
            "pyautogui", "flask", "react", "docker"
        ]
        
        for term in tech_terms:
            if term in text_lower:
                entities.append(term.upper())
        
        return entities
    
    def _extract_topics(self, user_message: str, bot_response: str) -> List[str]:
        """Extrai tópicos principais da conversa"""
        combined_text = f"{user_message} {bot_response}".lower()
        
        topic_keywords = {
            "automation": ["automação", "automatizar", "bot", "script"],
            "integration": ["integração", "api", "webhook", "conectar"],
            "error": ["erro", "problema", "falha", "bug"],
            "configuration": ["configurar", "setup", "instalar", "config"],
            "data": ["dados", "relatório", "analytics", "métricas"],
            "security": ["segurança", "token", "auth", "login"],
            "performance": ["performance", "velocidade", "otimizar", "lento"]
        }
        
        detected_topics = []
        for topic, keywords in topic_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                detected_topics.append(topic)
        
        return detected_topics
    
    def _assess_response_quality(self, user_message: str, bot_response: str) -> float:
        """Avalia qualidade da resposta (0-1)"""
        try:
            # Métricas básicas de qualidade
            response_length = len(bot_response)
            question_length = len(user_message)
            
            # Proporção de resposta apropriada
            length_ratio = min(response_length / max(question_length, 1), 5.0) / 5.0
            
            # Presença de informações úteis
            useful_indicators = [
                "exemplo", "código", "passo", "configurar", 
                "porque", "como", "quando", "onde"
            ]
            
            useful_count = sum(1 for indicator in useful_indicators 
                             if indicator in bot_response.lower())
            usefulness_score = min(useful_count / 3.0, 1.0)
            
            # Score final
            quality_score = (length_ratio * 0.3) + (usefulness_score * 0.7)
            return round(quality_score, 2)
            
        except Exception:
            return 0.5  # Score neutro em caso de erro
    
    def _generate_context_summary(
        self, 
        conversations: List[Dict], 
        avg_sentiment: float, 
        main_topics: List[tuple]
    ) -> str:
        """Gera resumo contextual da conversa"""
        
        if not conversations:
            return "Nenhuma conversa recente encontrada."
        
        # Análise de sentimento
        sentiment_text = "neutral"
        if avg_sentiment > 0.1:
            sentiment_text = "positivo"
        elif avg_sentiment < -0.1:
            sentiment_text = "negativo"
        
        # Tópicos principais
        topics_text = "tópicos gerais"
        if main_topics:
            topics_text = ", ".join([topic[0] for topic in main_topics[:2]])
        
        summary = f"""
Resumo da conversa recente:
- {len(conversations)} interações analisadas
- Sentimento geral: {sentiment_text}
- Principais tópicos: {topics_text}
- Última interação: {conversations[0]['timestamp']} (mais recente)

O usuário tem se engajado principalmente em discussões sobre {topics_text} 
com um tom {sentiment_text}.
        """.strip()
        
        return summary
    
    async def _update_user_profile(self, user_id: str, interaction_metadata: Dict):
        """Atualiza perfil do usuário baseado na interação"""
        
        profile_id = f"profile_{user_id}"
        
        # Busca perfil existente
        existing_profile = await self._get_user_profile(user_id)
        
        # Atualiza estatísticas
        updated_profile = {
            "user_id": user_id,
            "last_interaction": interaction_metadata["timestamp"],
            "total_interactions": existing_profile.get("total_interactions", 0) + 1,
            "favorite_topics": self._update_topic_preferences(
                existing_profile.get("favorite_topics", {}),
                interaction_metadata.get("topics", [])
            ),
            "avg_sentiment": self._update_avg_sentiment(
                existing_profile.get("avg_sentiment", 0),
                existing_profile.get("total_interactions", 0),
                interaction_metadata.get("user_sentiment_polarity", 0)
            ),
            "last_entities": interaction_metadata.get("entities", []),
            "profile_updated": datetime.now().isoformat()
        }
        
        # Salva perfil atualizado
        if self.user_profiles:
            try:
                # Remove perfil existente se houver
                try:
                    self.user_profiles.delete(ids=[profile_id])
                except Exception:
                    pass
                
                self.user_profiles.add(
                    ids=[profile_id],
                    documents=[json.dumps(updated_profile)],
                    metadatas=[updated_profile]
                )
            except Exception as e:
                self.logger.error(f"Erro ao atualizar perfil: {e}")
                self.local_profiles[profile_id] = updated_profile
        else:
            self.local_profiles[profile_id] = updated_profile
    
    async def _get_user_profile(self, user_id: str) -> Dict:
        """Recupera perfil do usuário"""
        profile_id = f"profile_{user_id}"
        
        if self.user_profiles:
            try:
                results = self.user_profiles.get(ids=[profile_id])
                if results['metadatas'] and results['metadatas'][0]:
                    return results['metadatas'][0]
            except Exception:
                pass
        
        # Fallback para cache local
        return self.local_profiles.get(profile_id, {})
    
    def _update_topic_preferences(self, current_topics: Dict, new_topics: List[str]) -> Dict:
        """Atualiza preferências de tópicos do usuário"""
        updated_topics = current_topics.copy()
        
        for topic in new_topics:
            updated_topics[topic] = updated_topics.get(topic, 0) + 1
        
        return updated_topics
    
    def _update_avg_sentiment(self, current_avg: float, total_interactions: int, new_sentiment: float) -> float:
        """Atualiza média de sentimento do usuário"""
        if total_interactions == 0:
            return new_sentiment
        
        return ((current_avg * total_interactions) + new_sentiment) / (total_interactions + 1)
    
    def get_memory_stats(self) -> Dict:
        """Retorna estatísticas da memória conversacional"""
        stats = {
            "timestamp": datetime.now().isoformat(),
            "chromadb_available": self.client is not None,
            "local_cache_size": len(self.local_conversations),
            "local_profiles_count": len(self.local_profiles)
        }
        
        if self.conversations:
            try:
                stats["total_conversations"] = self.conversations.count()
            except Exception:
                stats["total_conversations"] = 0
        
        if self.user_profiles:
            try:
                stats["total_profiles"] = self.user_profiles.count()
            except Exception:
                stats["total_profiles"] = 0
        
        return stats
    
    def clear_old_conversations(self, days_old: int = 30) -> int:
        """Remove conversas antigas para otimização"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        removed_count = 0
        
        # Limpa cache local
        for conv_id in list(self.local_conversations.keys()):
            try:
                timestamp_str = self.local_conversations[conv_id]['metadata']['timestamp']
                conv_time = datetime.fromisoformat(timestamp_str)
                if conv_time < cutoff_date:
                    del self.local_conversations[conv_id]
                    removed_count += 1
            except Exception:
                continue
        
        return removed_count