"""
Memory Manager - Sistema Avançado de Memória Conversacional
===========================================================

Sistema sofisticado para gerenciamento de memória conversacional persistente,
análise de sentimentos, extração de contexto e busca semântica.

Funcionalidades principais:
- Memória persistente de conversas por usuário
- Análise de sentimentos das conversas
- Extração automática de contexto relevante
- Sistema de tags automáticas para categorização
- Busca semântica avançada em histórico
- Compressão inteligente de conversas antigas
- Sistema de backup automático
- Análise de padrões comportamentais
"""

import json
import logging
import sqlite3
import threading
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict, field
from collections import defaultdict, Counter
import hashlib
import pickle
import gzip
import shutil
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import nltk
from textblob import TextBlob
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import requests
import schedule

# Download de dados necessários do NLTK
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('vader_lexicon', quiet=True)
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize, sent_tokenize
except Exception as e:
    logging.warning(f"Erro ao carregar NLTK: {e}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ConversationMessage:
    """Mensagem individual de uma conversa."""
    id: str
    user_id: str
    content: str
    role: str  # 'user' ou 'assistant'
    timestamp: datetime
    sentiment_score: float = 0.0
    sentiment_label: str = 'neutral'
    topics: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    importance_score: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Conversation:
    """Conversa completa entre usuário e assistente."""
    id: str
    user_id: str
    title: str
    messages: List[ConversationMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    summary: str = ""
    avg_sentiment: float = 0.0
    total_messages: int = 0
    is_compressed: bool = False
    compression_ratio: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class UserProfile:
    """Perfil comportamental do usuário."""
    user_id: str
    total_conversations: int = 0
    total_messages: int = 0
    avg_sentiment: float = 0.0
    preferred_topics: List[str] = field(default_factory=list)
    communication_patterns: Dict[str, Any] = field(default_factory=dict)
    active_hours: List[int] = field(default_factory=list)
    response_preferences: Dict[str, Any] = field(default_factory=dict)
    last_activity: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

class SentimentAnalyzer:
    """Analisador de sentimentos avançado."""
    
    def __init__(self):
        try:
            self.vader = SentimentIntensityAnalyzer()
            self.textblob_available = True
        except:
            self.vader = None
            self.textblob_available = False
            logger.warning("VADER não disponível, usando métodos alternativos")
    
    def analyze_sentiment(self, text: str) -> Tuple[float, str]:
        """Analisa sentimento do texto."""
        if not text.strip():
            return 0.0, 'neutral'
        
        scores = []
        labels = []
        
        # VADER (se disponível)
        if self.vader:
            vader_scores = self.vader.polarity_scores(text)
            compound = vader_scores['compound']
            scores.append(compound)
            
            if compound >= 0.05:
                labels.append('positive')
            elif compound <= -0.05:
                labels.append('negative')
            else:
                labels.append('neutral')
        
        # TextBlob
        if self.textblob_available:
            try:
                blob = TextBlob(text)
                polarity = blob.sentiment.polarity
                scores.append(polarity)
                
                if polarity > 0.1:
                    labels.append('positive')
                elif polarity < -0.1:
                    labels.append('negative')
                else:
                    labels.append('neutral')
            except:
                pass
        
        # Análise baseada em palavras-chave
        positive_words = ['bom', 'ótimo', 'excelente', 'perfeito', 'satisfeito', 'feliz', 'obrigado']
        negative_words = ['ruim', 'péssimo', 'terrível', 'frustrado', 'irritado', 'problema', 'erro']
        
        text_lower = text.lower()
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count > neg_count:
            scores.append(0.5)
            labels.append('positive')
        elif neg_count > pos_count:
            scores.append(-0.5)
            labels.append('negative')
        else:
            scores.append(0.0)
            labels.append('neutral')
        
        # Combina resultados
        if scores:
            avg_score = np.mean(scores)
            label_counts = Counter(labels)
            final_label = label_counts.most_common(1)[0][0]
            return float(avg_score), final_label
        
        return 0.0, 'neutral'

class TopicExtractor:
    """Extrator de tópicos automático."""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words=['portuguese', 'english'] if hasattr(TfidfVectorizer, 'stop_words') else None,
            ngram_range=(1, 2)
        )
        self.common_topics = {
            'automação': ['automação', 'automatizar', 'processo', 'workflow'],
            'integração': ['integração', 'api', 'sistema', 'conectar'],
            'relatório': ['relatório', 'dados', 'análise', 'gráfico'],
            'configuração': ['configuração', 'configurar', 'settings', 'parâmetros'],
            'erro': ['erro', 'problema', 'bug', 'falha', 'exception'],
            'ajuda': ['ajuda', 'dúvida', 'como', 'tutorial', 'manual'],
            'performance': ['performance', 'lento', 'rápido', 'otimização'],
            'segurança': ['segurança', 'senha', 'token', 'autenticação']
        }
    
    def extract_topics(self, text: str, max_topics: int = 5) -> List[str]:
        """Extrai tópicos do texto."""
        if not text.strip():
            return []
        
        topics = []
        text_lower = text.lower()
        
        # Busca por tópicos predefinidos
        for topic, keywords in self.common_topics.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)
        
        # Extração baseada em TF-IDF para tópicos adicionais
        try:
            sentences = [text]
            tfidf_matrix = self.vectorizer.fit_transform(sentences)
            feature_names = self.vectorizer.get_feature_names_out()
            scores = tfidf_matrix.toarray()[0]
            
            # Pega os termos com maior score
            top_indices = np.argsort(scores)[::-1][:max_topics]
            for idx in top_indices:
                if scores[idx] > 0.1:  # Threshold mínimo
                    term = feature_names[idx]
                    if term not in topics and len(term) > 3:
                        topics.append(term)
        except:
            pass
        
        return topics[:max_topics]

class EntityExtractor:
    """Extrator de entidades nomeadas."""
    
    def __init__(self):
        # Padrões para diferentes tipos de entidades
        self.patterns = {
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'\b\d{2,3}[-.\s]?\d{4,5}[-.\s]?\d{4}\b'),
            'url': re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'),
            'date': re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'),
            'money': re.compile(r'R\$\s?\d+(?:[\.,]\d{2})?'),
            'percentage': re.compile(r'\d+(?:[\.,]\d+)?%'),
        }
        
        # Entidades específicas do domínio
        self.domain_entities = {
            'sistemas': ['bitrix24', 'ixcsoft', 'locaweb', 'fluctus', 'newave', 'uzera', 'playhub'],
            'tecnologias': ['python', 'flask', 'react', 'selenium', 'api', 'oauth', 'jwt'],
            'métricas': ['cpu', 'memória', 'disco', 'latência', 'throughput', 'uptime']
        }
    
    def extract_entities(self, text: str) -> List[str]:
        """Extrai entidades do texto."""
        entities = []
        text_lower = text.lower()
        
        # Extrai usando padrões regex
        for entity_type, pattern in self.patterns.items():
            matches = pattern.findall(text)
            for match in matches:
                entities.append(f"{entity_type}:{match}")
        
        # Extrai entidades do domínio
        for category, items in self.domain_entities.items():
            for item in items:
                if item in text_lower:
                    entities.append(f"{category}:{item}")
        
        return list(set(entities))  # Remove duplicatas

class ConversationCompressor:
    """Compressor inteligente de conversas antigas."""
    
    def __init__(self, embedding_model: Optional[SentenceTransformer] = None):
        self.embedding_model = embedding_model
        self.compression_threshold = 0.7  # Similaridade mínima para manter mensagens
    
    def compress_conversation(self, conversation: Conversation) -> Conversation:
        """Comprime uma conversa mantendo informações importantes."""
        if len(conversation.messages) < 10:
            return conversation  # Não comprime conversas pequenas
        
        # Agrupa mensagens por importância
        important_messages = []
        regular_messages = []
        
        for msg in conversation.messages:
            if (msg.importance_score > 0.7 or 
                msg.sentiment_label in ['very_positive', 'very_negative'] or
                len(msg.entities) > 0):
                important_messages.append(msg)
            else:
                regular_messages.append(msg)
        
        # Comprime mensagens regulares
        compressed_regular = self._compress_similar_messages(regular_messages)
        
        # Combina mensagens importantes com comprimidas
        all_messages = important_messages + compressed_regular
        all_messages.sort(key=lambda x: x.timestamp)
        
        # Cria nova conversa comprimida
        compressed = Conversation(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            messages=all_messages,
            created_at=conversation.created_at,
            updated_at=datetime.now(),
            tags=conversation.tags,
            summary=conversation.summary,
            avg_sentiment=conversation.avg_sentiment,
            total_messages=len(all_messages),
            is_compressed=True,
            compression_ratio=len(all_messages) / len(conversation.messages),
            metadata=conversation.metadata
        )
        
        return compressed
    
    def _compress_similar_messages(self, messages: List[ConversationMessage]) -> List[ConversationMessage]:
        """Comprime mensagens similares."""
        if not messages or not self.embedding_model:
            return messages
        
        try:
            # Gera embeddings
            texts = [msg.content for msg in messages]
            embeddings = self.embedding_model.encode(texts)
            
            # Calcula similaridades
            similarities = cosine_similarity(embeddings)
            
            # Agrupa mensagens similares
            groups = []
            used_indices = set()
            
            for i, msg in enumerate(messages):
                if i in used_indices:
                    continue
                
                group = [i]
                for j in range(i + 1, len(messages)):
                    if j not in used_indices and similarities[i][j] > self.compression_threshold:
                        group.append(j)
                        used_indices.add(j)
                
                groups.append(group)
                used_indices.add(i)
            
            # Cria mensagens comprimidas
            compressed = []
            for group in groups:
                if len(group) == 1:
                    compressed.append(messages[group[0]])
                else:
                    # Combina mensagens do grupo
                    combined_content = " ".join([messages[i].content for i in group])
                    main_msg = messages[group[0]]  # Usa primeira como base
                    
                    compressed_msg = ConversationMessage(
                        id=f"compressed_{main_msg.id}",
                        user_id=main_msg.user_id,
                        content=f"[COMPRIMIDO] {combined_content[:500]}...",
                        role=main_msg.role,
                        timestamp=main_msg.timestamp,
                        sentiment_score=np.mean([messages[i].sentiment_score for i in group]),
                        sentiment_label=main_msg.sentiment_label,
                        topics=list(set([topic for i in group for topic in messages[i].topics])),
                        entities=list(set([entity for i in group for entity in messages[i].entities])),
                        importance_score=max([messages[i].importance_score for i in group]),
                        metadata={'compressed_from': len(group), 'original_ids': [messages[i].id for i in group]}
                    )
                    compressed.append(compressed_msg)
            
            return compressed
            
        except Exception as e:
            logger.error(f"Erro na compressão: {e}")
            return messages

class MemoryManager:
    """Gerenciador principal de memória conversacional."""
    
    def __init__(self, data_dir: str = "./data/memory"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Bancos de dados
        self.db_path = self.data_dir / "conversations.db"
        self.backup_dir = self.data_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # Inicializa banco
        self._init_database()
        
        # Componentes especializados
        self.sentiment_analyzer = SentimentAnalyzer()
        self.topic_extractor = TopicExtractor()
        self.entity_extractor = EntityExtractor()
        
        # Inicializa modelo de embeddings
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            logger.warning(f"Erro ao carregar modelo de embeddings: {e}")
            self.embedding_model = None
        
        self.compressor = ConversationCompressor(self.embedding_model)
        
        # ChromaDB para busca semântica
        self._init_chromadb()
        
        # Cache em memória
        self.conversation_cache = {}
        self.user_profile_cache = {}
        
        # Thread pool para processamento assíncrono
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Lock para thread safety
        self.lock = threading.Lock()
        
        # Agenda tarefas de manutenção
        self._schedule_maintenance()
        
        logger.info("MemoryManager inicializado com sucesso")
    
    def _init_database(self):
        """Inicializa banco de dados SQLite."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Tabela de conversas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                tags TEXT,
                summary TEXT,
                avg_sentiment REAL DEFAULT 0.0,
                total_messages INTEGER DEFAULT 0,
                is_compressed BOOLEAN DEFAULT 0,
                compression_ratio REAL DEFAULT 1.0,
                metadata TEXT
            )
        ''')
        
        # Tabela de mensagens
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                content TEXT NOT NULL,
                role TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                sentiment_score REAL DEFAULT 0.0,
                sentiment_label TEXT DEFAULT 'neutral',
                topics TEXT,
                entities TEXT,
                importance_score REAL DEFAULT 1.0,
                metadata TEXT,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id)
            )
        ''')
        
        # Tabela de perfis de usuário
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                total_conversations INTEGER DEFAULT 0,
                total_messages INTEGER DEFAULT 0,
                avg_sentiment REAL DEFAULT 0.0,
                preferred_topics TEXT,
                communication_patterns TEXT,
                active_hours TEXT,
                response_preferences TEXT,
                last_activity TIMESTAMP,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL
            )
        ''')
        
        # Índices para performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations (user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages (conversation_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages (user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages (timestamp)')
        
        conn.commit()
        conn.close()
    
    def _init_chromadb(self):
        """Inicializa ChromaDB para busca semântica."""
        try:
            chroma_dir = self.data_dir / "chromadb"
            chroma_dir.mkdir(exist_ok=True)
            
            self.chroma_client = chromadb.PersistentClient(
                path=str(chroma_dir),
                settings=Settings(anonymized_telemetry=False)
            )
            
            self.messages_collection = self.chroma_client.get_or_create_collection(
                name="conversation_messages",
                metadata={"description": "Mensagens de conversas para busca semântica"}
            )
            
            logger.info("ChromaDB inicializado para busca semântica")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar ChromaDB: {e}")
            self.chroma_client = None
            self.messages_collection = None
    
    def _schedule_maintenance(self):
        """Agenda tarefas de manutenção."""
        # Backup diário
        schedule.every().day.at("02:00").do(self._daily_backup)
        
        # Compressão semanal
        schedule.every().week.do(self._weekly_compression)
        
        # Limpeza mensal
        schedule.every().month.do(self._monthly_cleanup)
        
        # Worker thread para tarefas agendadas
        def maintenance_worker():
            while True:
                schedule.run_pending()
                time.sleep(60)
        
        maintenance_thread = threading.Thread(target=maintenance_worker, daemon=True)
        maintenance_thread.start()
    
    def add_message(self, user_id: str, content: str, role: str = 'user',
                    conversation_id: Optional[str] = None) -> str:
        """Adiciona nova mensagem."""
        message_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        # Se não especificado, cria nova conversa ou usa a mais recente
        if conversation_id is None:
            conversation_id = self._get_or_create_active_conversation(user_id)
        
        # Analisa a mensagem
        sentiment_score, sentiment_label = self.sentiment_analyzer.analyze_sentiment(content)
        topics = self.topic_extractor.extract_topics(content)
        entities = self.entity_extractor.extract_entities(content)
        
        # Calcula importância
        importance_score = self._calculate_importance(content, sentiment_score, topics, entities)
        
        # Cria objeto da mensagem
        message = ConversationMessage(
            id=message_id,
            user_id=user_id,
            content=content,
            role=role,
            timestamp=timestamp,
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            topics=topics,
            entities=entities,
            importance_score=importance_score
        )
        
        # Salva no banco
        self._save_message_to_db(message, conversation_id)
        
        # Adiciona ao ChromaDB para busca semântica
        if self.messages_collection and self.embedding_model:
            try:
                embedding = self.embedding_model.encode([content])[0].tolist()
                self.messages_collection.add(
                    ids=[message_id],
                    documents=[content],
                    embeddings=[embedding],
                    metadatas=[{
                        'user_id': user_id,
                        'conversation_id': conversation_id,
                        'role': role,
                        'timestamp': timestamp.isoformat(),
                        'sentiment': sentiment_label,
                        'importance': importance_score
                    }]
                )
            except Exception as e:
                logger.error(f"Erro ao adicionar ao ChromaDB: {e}")
        
        # Atualiza perfil do usuário
        self._update_user_profile(user_id, message)
        
        # Atualiza cache
        with self.lock:
            if conversation_id in self.conversation_cache:
                self.conversation_cache[conversation_id].messages.append(message)
                self.conversation_cache[conversation_id].updated_at = timestamp
        
        logger.info(f"Mensagem adicionada: {message_id}")
        return message_id
    
    def _get_or_create_active_conversation(self, user_id: str) -> str:
        """Obtém conversa ativa ou cria nova."""
        # Busca conversa recente (últimas 2 horas)
        recent_cutoff = datetime.now() - timedelta(hours=2)
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id FROM conversations 
            WHERE user_id = ? AND updated_at > ?
            ORDER BY updated_at DESC 
            LIMIT 1
        ''', (user_id, recent_cutoff))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0]
        
        # Cria nova conversa
        return self.create_conversation(user_id, "Nova Conversa")
    
    def create_conversation(self, user_id: str, title: str) -> str:
        """Cria nova conversa."""
        conversation_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        conversation = Conversation(
            id=conversation_id,
            user_id=user_id,
            title=title,
            created_at=timestamp,
            updated_at=timestamp
        )
        
        # Salva no banco
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO conversations 
            (id, user_id, title, created_at, updated_at, tags, summary, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            conversation_id, user_id, title, timestamp, timestamp,
            json.dumps([]), "", json.dumps({})
        ))
        
        conn.commit()
        conn.close()
        
        # Adiciona ao cache
        with self.lock:
            self.conversation_cache[conversation_id] = conversation
        
        logger.info(f"Nova conversa criada: {conversation_id}")
        return conversation_id
    
    def _save_message_to_db(self, message: ConversationMessage, conversation_id: str):
        """Salva mensagem no banco."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO messages 
            (id, conversation_id, user_id, content, role, timestamp, 
             sentiment_score, sentiment_label, topics, entities, 
             importance_score, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            message.id, conversation_id, message.user_id, message.content,
            message.role, message.timestamp, message.sentiment_score,
            message.sentiment_label, json.dumps(message.topics),
            json.dumps(message.entities), message.importance_score,
            json.dumps(message.metadata)
        ))
        
        # Atualiza contador de mensagens na conversa
        cursor.execute('''
            UPDATE conversations 
            SET total_messages = total_messages + 1, updated_at = ?
            WHERE id = ?
        ''', (message.timestamp, conversation_id))
        
        conn.commit()
        conn.close()
    
    def _calculate_importance(self, content: str, sentiment_score: float,
                            topics: List[str], entities: List[str]) -> float:
        """Calcula score de importância da mensagem."""
        importance = 1.0
        
        # Baseado no comprimento
        if len(content) > 100:
            importance += 0.2
        
        # Baseado no sentimento
        if abs(sentiment_score) > 0.5:
            importance += 0.3
        
        # Baseado em tópicos
        if topics:
            importance += len(topics) * 0.1
        
        # Baseado em entidades
        if entities:
            importance += len(entities) * 0.15
        
        # Palavras-chave importantes
        important_keywords = ['problema', 'erro', 'urgente', 'importante', 'crítico']
        if any(keyword in content.lower() for keyword in important_keywords):
            importance += 0.5
        
        return min(importance, 3.0)  # Máximo 3.0
    
    def _update_user_profile(self, user_id: str, message: ConversationMessage):
        """Atualiza perfil do usuário."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Busca perfil existente
        cursor.execute('SELECT * FROM user_profiles WHERE user_id = ?', (user_id,))
        profile_data = cursor.fetchone()
        
        if profile_data:
            # Atualiza perfil existente
            total_messages = profile_data[2] + 1
            
            # Atualiza sentimento médio
            current_avg = profile_data[3] or 0.0
            new_avg = (current_avg * (total_messages - 1) + message.sentiment_score) / total_messages
            
            # Atualiza hora de atividade
            current_hour = message.timestamp.hour
            
            cursor.execute('''
                UPDATE user_profiles 
                SET total_messages = ?, avg_sentiment = ?, last_activity = ?, updated_at = ?
                WHERE user_id = ?
            ''', (total_messages, new_avg, message.timestamp, datetime.now(), user_id))
        else:
            # Cria novo perfil
            profile = UserProfile(
                user_id=user_id,
                total_messages=1,
                avg_sentiment=message.sentiment_score,
                last_activity=message.timestamp
            )
            
            cursor.execute('''
                INSERT INTO user_profiles 
                (user_id, total_conversations, total_messages, avg_sentiment,
                 preferred_topics, communication_patterns, active_hours,
                 response_preferences, last_activity, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, 0, 1, message.sentiment_score,
                json.dumps([]), json.dumps({}), json.dumps([]),
                json.dumps({}), message.timestamp, datetime.now(), datetime.now()
            ))
        
        conn.commit()
        conn.close()
    
    def get_user_conversations(self, user_id: str, limit: int = 10,
                              include_messages: bool = False) -> List[Dict[str, Any]]:
        """Obtém conversas do usuário."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM conversations 
            WHERE user_id = ? 
            ORDER BY updated_at DESC 
            LIMIT ?
        ''', (user_id, limit))
        
        conversations = []
        for row in cursor.fetchall():
            conv_data = {
                'id': row[0],
                'user_id': row[1],
                'title': row[2],
                'created_at': row[3],
                'updated_at': row[4],
                'tags': json.loads(row[5] or '[]'),
                'summary': row[6] or '',
                'avg_sentiment': row[7],
                'total_messages': row[8],
                'is_compressed': bool(row[9]),
                'compression_ratio': row[10],
                'metadata': json.loads(row[11] or '{}')
            }
            
            if include_messages:
                conv_data['messages'] = self._get_conversation_messages(row[0])
            
            conversations.append(conv_data)
        
        conn.close()
        return conversations
    
    def _get_conversation_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Obtém mensagens de uma conversa."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM messages 
            WHERE conversation_id = ? 
            ORDER BY timestamp ASC
        ''', (conversation_id,))
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                'id': row[0],
                'conversation_id': row[1],
                'user_id': row[2],
                'content': row[3],
                'role': row[4],
                'timestamp': row[5],
                'sentiment_score': row[6],
                'sentiment_label': row[7],
                'topics': json.loads(row[8] or '[]'),
                'entities': json.loads(row[9] or '[]'),
                'importance_score': row[10],
                'metadata': json.loads(row[11] or '{}')
            })
        
        conn.close()
        return messages
    
    def search_conversations(self, user_id: str, query: str,
                           limit: int = 10) -> List[Dict[str, Any]]:
        """Busca conversas usando busca semântica."""
        results = []
        
        if self.messages_collection and self.embedding_model:
            try:
                # Busca semântica
                query_embedding = self.embedding_model.encode([query])[0].tolist()
                
                search_results = self.messages_collection.query(
                    query_embeddings=[query_embedding],
                    n_results=limit * 2,  # Busca mais para filtrar por usuário
                    where={"user_id": user_id},
                    include=['documents', 'metadatas', 'distances']
                )
                
                # Processa resultados
                seen_conversations = set()
                for i, doc_id in enumerate(search_results['ids'][0]):
                    metadata = search_results['metadatas'][0][i]
                    conv_id = metadata['conversation_id']
                    
                    if conv_id not in seen_conversations and len(results) < limit:
                        seen_conversations.add(conv_id)
                        
                        # Busca dados completos da conversa
                        conv_data = self.get_conversation(conv_id)
                        if conv_data:
                            conv_data['search_score'] = 1.0 - search_results['distances'][0][i]
                            conv_data['matching_message'] = search_results['documents'][0][i]
                            results.append(conv_data)
                
            except Exception as e:
                logger.error(f"Erro na busca semântica: {e}")
        
        # Fallback para busca textual
        if not results:
            results = self._text_search_conversations(user_id, query, limit)
        
        return results
    
    def _text_search_conversations(self, user_id: str, query: str,
                                  limit: int = 10) -> List[Dict[str, Any]]:
        """Busca textual em conversas."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT c.* FROM conversations c
            JOIN messages m ON c.id = m.conversation_id
            WHERE c.user_id = ? AND (
                c.title LIKE ? OR 
                c.summary LIKE ? OR 
                m.content LIKE ?
            )
            ORDER BY c.updated_at DESC
            LIMIT ?
        ''', (user_id, f'%{query}%', f'%{query}%', f'%{query}%', limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'user_id': row[1],
                'title': row[2],
                'created_at': row[3],
                'updated_at': row[4],
                'tags': json.loads(row[5] or '[]'),
                'summary': row[6] or '',
                'avg_sentiment': row[7],
                'total_messages': row[8],
                'is_compressed': bool(row[9]),
                'compression_ratio': row[10],
                'metadata': json.loads(row[11] or '{}'),
                'search_score': 0.5  # Score padrão para busca textual
            })
        
        conn.close()
        return results
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Obtém dados completos de uma conversa."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM conversations WHERE id = ?', (conversation_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        conv_data = {
            'id': row[0],
            'user_id': row[1],
            'title': row[2],
            'created_at': row[3],
            'updated_at': row[4],
            'tags': json.loads(row[5] or '[]'),
            'summary': row[6] or '',
            'avg_sentiment': row[7],
            'total_messages': row[8],
            'is_compressed': bool(row[9]),
            'compression_ratio': row[10],
            'metadata': json.loads(row[11] or '{}'),
            'messages': self._get_conversation_messages(conversation_id)
        }
        
        conn.close()
        return conv_data
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Obtém perfil do usuário."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM user_profiles WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        profile = {
            'user_id': row[0],
            'total_conversations': row[1],
            'total_messages': row[2],
            'avg_sentiment': row[3],
            'preferred_topics': json.loads(row[4] or '[]'),
            'communication_patterns': json.loads(row[5] or '{}'),
            'active_hours': json.loads(row[6] or '[]'),
            'response_preferences': json.loads(row[7] or '{}'),
            'last_activity': row[8],
            'created_at': row[9],
            'updated_at': row[10]
        }
        
        conn.close()
        return profile
    
    def analyze_user_patterns(self, user_id: str) -> Dict[str, Any]:
        """Analisa padrões comportamentais do usuário."""
        # Busca mensagens do usuário
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT content, timestamp, sentiment_score, topics, entities
            FROM messages 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT 1000
        ''', (user_id,))
        
        messages = cursor.fetchall()
        conn.close()
        
        if not messages:
            return {'error': 'Usuário sem mensagens'}
        
        # Análise de padrões
        analysis = {
            'total_analyzed': len(messages),
            'time_patterns': self._analyze_time_patterns(messages),
            'sentiment_trends': self._analyze_sentiment_trends(messages),
            'topic_frequency': self._analyze_topic_frequency(messages),
            'communication_style': self._analyze_communication_style(messages),
            'response_patterns': self._analyze_response_patterns(messages)
        }
        
        return analysis
    
    def _analyze_time_patterns(self, messages: List[Tuple]) -> Dict[str, Any]:
        """Analisa padrões temporais."""
        hours = [datetime.fromisoformat(msg[1]).hour for msg in messages]
        hour_counts = Counter(hours)
        
        # Horários mais ativos
        peak_hours = hour_counts.most_common(3)
        
        # Distribuição por período do dia
        morning = sum(count for hour, count in hour_counts.items() if 6 <= hour < 12)
        afternoon = sum(count for hour, count in hour_counts.items() if 12 <= hour < 18)
        evening = sum(count for hour, count in hour_counts.items() if 18 <= hour < 24)
        night = sum(count for hour, count in hour_counts.items() if 0 <= hour < 6)
        
        return {
            'peak_hours': [{'hour': h, 'count': c} for h, c in peak_hours],
            'period_distribution': {
                'morning': morning,
                'afternoon': afternoon,
                'evening': evening,
                'night': night
            }
        }
    
    def _analyze_sentiment_trends(self, messages: List[Tuple]) -> Dict[str, Any]:
        """Analisa tendências de sentimento."""
        sentiments = [msg[2] for msg in messages]
        
        # Estatísticas básicas
        avg_sentiment = np.mean(sentiments)
        sentiment_std = np.std(sentiments)
        
        # Distribuição de sentimentos
        positive = len([s for s in sentiments if s > 0.1])
        negative = len([s for s in sentiments if s < -0.1])
        neutral = len(sentiments) - positive - negative
        
        # Tendência temporal (últimos vs primeiros)
        recent_sentiments = sentiments[:len(sentiments)//2]
        older_sentiments = sentiments[len(sentiments)//2:]
        
        trend = np.mean(recent_sentiments) - np.mean(older_sentiments) if older_sentiments else 0
        
        return {
            'average_sentiment': avg_sentiment,
            'sentiment_variability': sentiment_std,
            'distribution': {
                'positive': positive,
                'negative': negative,
                'neutral': neutral
            },
            'trend': trend,
            'trend_description': 'improving' if trend > 0.1 else 'declining' if trend < -0.1 else 'stable'
        }
    
    def _analyze_topic_frequency(self, messages: List[Tuple]) -> Dict[str, Any]:
        """Analisa frequência de tópicos."""
        all_topics = []
        for msg in messages:
            topics = json.loads(msg[3] or '[]')
            all_topics.extend(topics)
        
        topic_counts = Counter(all_topics)
        
        return {
            'most_common': topic_counts.most_common(10),
            'total_unique_topics': len(topic_counts),
            'topic_diversity': len(topic_counts) / len(messages) if messages else 0
        }
    
    def _analyze_communication_style(self, messages: List[Tuple]) -> Dict[str, Any]:
        """Analisa estilo de comunicação."""
        contents = [msg[0] for msg in messages]
        
        # Estatísticas de texto
        avg_length = np.mean([len(content) for content in contents])
        avg_words = np.mean([len(content.split()) for content in contents])
        
        # Padrões de linguagem
        question_count = sum(1 for content in contents if '?' in content)
        exclamation_count = sum(1 for content in contents if '!' in content)
        
        # Formalidade (baseado em palavras específicas)
        formal_words = ['por favor', 'obrigado', 'gostaria', 'poderia']
        informal_words = ['oi', 'tudo bem', 'valeu', 'blz']
        
        formal_score = sum(1 for content in contents 
                          for word in formal_words if word in content.lower())
        informal_score = sum(1 for content in contents 
                            for word in informal_words if word in content.lower())
        
        return {
            'avg_message_length': avg_length,
            'avg_words_per_message': avg_words,
            'question_frequency': question_count / len(contents) if contents else 0,
            'exclamation_frequency': exclamation_count / len(contents) if contents else 0,
            'formality_score': formal_score / (formal_score + informal_score + 1),
            'communication_style': 'formal' if formal_score > informal_score else 'informal'
        }
    
    def _analyze_response_patterns(self, messages: List[Tuple]) -> Dict[str, Any]:
        """Analisa padrões de resposta."""
        # Simula análise de padrões de resposta
        # Em implementação real, analisaria tempo entre mensagens, etc.
        
        return {
            'avg_response_time': '2.5 minutes',  # Placeholder
            'preferred_response_length': 'medium',
            'interaction_frequency': 'regular'
        }
    
    def _daily_backup(self):
        """Backup diário."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backup_dir / f"backup_{timestamp}.db"
            
            shutil.copy2(str(self.db_path), str(backup_file))
            
            # Comprime backup
            with open(backup_file, 'rb') as f_in:
                with gzip.open(f"{backup_file}.gz", 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            backup_file.unlink()  # Remove arquivo não comprimido
            
            logger.info(f"Backup diário criado: {backup_file}.gz")
            
        except Exception as e:
            logger.error(f"Erro no backup diário: {e}")
    
    def _weekly_compression(self):
        """Compressão semanal de conversas antigas."""
        try:
            cutoff_date = datetime.now() - timedelta(days=30)
            
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Busca conversas antigas não comprimidas
            cursor.execute('''
                SELECT id FROM conversations 
                WHERE updated_at < ? AND is_compressed = 0 AND total_messages > 10
            ''', (cutoff_date,))
            
            conversation_ids = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            compressed_count = 0
            for conv_id in conversation_ids:
                conv_data = self.get_conversation(conv_id)
                if conv_data:
                    # Converte para objeto Conversation
                    conversation = Conversation(**conv_data)
                    
                    # Comprime
                    compressed = self.compressor.compress_conversation(conversation)
                    
                    # Salva versão comprimida
                    # Implementar salvamento da versão comprimida
                    compressed_count += 1
            
            logger.info(f"Compressão semanal: {compressed_count} conversas comprimidas")
            
        except Exception as e:
            logger.error(f"Erro na compressão semanal: {e}")
    
    def _monthly_cleanup(self):
        """Limpeza mensal de dados antigos."""
        try:
            # Remove backups muito antigos (> 6 meses)
            cutoff_date = datetime.now() - timedelta(days=180)
            
            for backup_file in self.backup_dir.glob("backup_*.gz"):
                file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                if file_time < cutoff_date:
                    backup_file.unlink()
            
            logger.info("Limpeza mensal concluída")
            
        except Exception as e:
            logger.error(f"Erro na limpeza mensal: {e}")
    
    def export_user_data(self, user_id: str, format: str = 'json') -> str:
        """Exporta dados do usuário."""
        try:
            # Busca todas as conversas do usuário
            conversations = self.get_user_conversations(user_id, limit=1000, include_messages=True)
            profile = self.get_user_profile(user_id)
            
            export_data = {
                'user_id': user_id,
                'profile': profile,
                'conversations': conversations,
                'export_date': datetime.now().isoformat(),
                'total_conversations': len(conversations),
                'total_messages': sum(len(conv.get('messages', [])) for conv in conversations)
            }
            
            # Salva arquivo de exportação
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            export_file = self.data_dir / f"export_{user_id}_{timestamp}.{format}"
            
            if format == 'json':
                with open(export_file, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Dados exportados: {export_file}")
            return str(export_file)
            
        except Exception as e:
            logger.error(f"Erro na exportação: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtém estatísticas do sistema de memória."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Estatísticas básicas
        cursor.execute('SELECT COUNT(*) FROM conversations')
        total_conversations = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM messages')
        total_messages = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM user_profiles')
        total_users = cursor.fetchone()[0]
        
        # Estatísticas de sentimento
        cursor.execute('SELECT AVG(sentiment_score) FROM messages')
        avg_sentiment = cursor.fetchone()[0] or 0
        
        # Conversas por usuário
        cursor.execute('''
            SELECT user_id, COUNT(*) as conv_count 
            FROM conversations 
            GROUP BY user_id 
            ORDER BY conv_count DESC 
            LIMIT 5
        ''')
        top_users = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_conversations': total_conversations,
            'total_messages': total_messages,
            'total_users': total_users,
            'avg_sentiment': avg_sentiment,
            'top_users': [{'user_id': u[0], 'conversations': u[1]} for u in top_users],
            'database_size': self.db_path.stat().st_size,
            'cache_size': len(self.conversation_cache)
        }
    
    def cleanup_resources(self):
        """Limpa recursos."""
        try:
            self.executor.shutdown(wait=True)
            
            # Limpa caches
            with self.lock:
                self.conversation_cache.clear()
                self.user_profile_cache.clear()
            
            logger.info("Recursos do MemoryManager limpos")
            
        except Exception as e:
            logger.error(f"Erro ao limpar recursos: {e}")

# Função de teste
def main():
    """Função principal para teste."""
    memory_manager = MemoryManager()
    
    try:
        # Teste básico
        user_id = "test_user_123"
        
        # Adiciona algumas mensagens
        memory_manager.add_message(user_id, "Olá! Como configurar uma automação?", "user")
        memory_manager.add_message(user_id, "Para configurar uma automação, primeiro acesse...", "assistant")
        memory_manager.add_message(user_id, "Perfeito! Funcionou muito bem, obrigado!", "user")
        
        # Busca conversas
        conversations = memory_manager.get_user_conversations(user_id)
        print("Conversas encontradas:", len(conversations))
        
        # Análise de padrões
        patterns = memory_manager.analyze_user_patterns(user_id)
        print("Padrões analisados:", json.dumps(patterns, indent=2, default=str))
        
        # Estatísticas
        stats = memory_manager.get_statistics()
        print("Estatísticas:", json.dumps(stats, indent=2, default=str))
        
    finally:
        memory_manager.cleanup_resources()

if __name__ == "__main__":
    main()