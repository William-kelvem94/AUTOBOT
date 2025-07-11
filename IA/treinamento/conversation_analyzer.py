"""
Conversation Analyzer - Sistema Avançado de Análise Conversacional
==================================================================

Sistema sofisticado para análise profunda de conversas, extração de insights,
padrões comportamentais e geração de relatórios inteligentes.

Funcionalidades principais:
- Análise de sentimentos em tempo real
- Identificação de tópicos e tendências
- Análise de padrões comportamentais
- Detecção de problemas e oportunidades
- Geração de insights automáticos
- Relatórios de satisfação do usuário
- Análise de eficácia das respostas
- Métricas de engajamento conversacional
"""

import logging
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import sqlite3
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation, NMF
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import re
import networkx as nx
from textblob import TextBlob
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.chunk import ne_chunk
from nltk.tag import pos_tag
from scipy.stats import chi2_contingency, pearsonr
import yake

# Download de recursos NLTK necessários
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
    nltk.download('maxent_ne_chunker', quiet=True)
    nltk.download('words', quiet=True)
except:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ConversationMetrics:
    """Métricas de uma conversa."""
    conversation_id: str
    user_id: str
    total_messages: int
    avg_message_length: float
    conversation_duration: float  # em minutos
    sentiment_progression: List[float]
    topic_diversity: float
    engagement_score: float
    resolution_score: float
    satisfaction_score: float
    complexity_score: float
    timestamp: datetime

@dataclass
class TopicTrend:
    """Tendência de tópico."""
    topic_name: str
    frequency: int
    sentiment_avg: float
    growth_rate: float  # % change over time
    related_topics: List[str]
    peak_hours: List[int]
    user_segments: List[str]

@dataclass
class UserBehaviorPattern:
    """Padrão comportamental do usuário."""
    user_id: str
    communication_style: str  # formal, informal, technical, casual
    preferred_topics: List[str]
    activity_pattern: Dict[str, Any]  # hourly, daily, weekly patterns
    response_preferences: Dict[str, Any]
    sentiment_stability: float
    engagement_level: str  # high, medium, low
    problem_resolution_rate: float

@dataclass
class ConversationInsight:
    """Insight extraído de conversas."""
    insight_type: str  # trend, anomaly, opportunity, problem
    title: str
    description: str
    confidence: float
    impact_level: str  # high, medium, low
    recommended_actions: List[str]
    supporting_data: Dict[str, Any]
    timestamp: datetime

class SentimentAnalyzer:
    """Analisador de sentimentos avançado."""
    
    def __init__(self):
        self.sentiment_keywords = {
            'very_positive': ['excelente', 'perfeito', 'fantástico', 'maravilhoso', 'incrível'],
            'positive': ['bom', 'ótimo', 'legal', 'bacana', 'satisfeito', 'feliz'],
            'neutral': ['ok', 'normal', 'regular', 'comum'],
            'negative': ['ruim', 'chato', 'irritante', 'frustrado', 'decepcionado'],
            'very_negative': ['péssimo', 'horrível', 'terrível', 'detesto', 'odeio']
        }
        
        self.emotion_keywords = {
            'joy': ['alegre', 'feliz', 'contente', 'animado', 'empolgado'],
            'anger': ['irritado', 'furioso', 'bravo', 'nervoso', 'raivoso'],
            'fear': ['medo', 'receoso', 'apreensivo', 'ansioso', 'preocupado'],
            'sadness': ['triste', 'deprimido', 'melancólico', 'desanimado'],
            'surprise': ['surpreso', 'espantado', 'admirado', 'impressionado'],
            'disgust': ['nojento', 'repugnante', 'asqueroso', 'repulsivo']
        }
    
    def analyze_sentiment_progression(self, messages: List[Dict]) -> List[float]:
        """Analisa progressão de sentimento ao longo da conversa."""
        sentiments = []
        
        for message in messages:
            content = message.get('content', '')
            sentiment = self._calculate_sentiment_score(content)
            sentiments.append(sentiment)
        
        return sentiments
    
    def _calculate_sentiment_score(self, text: str) -> float:
        """Calcula score de sentimento (-1.0 a 1.0)."""
        if not text:
            return 0.0
        
        text_lower = text.lower()
        score = 0.0
        
        # Análise baseada em palavras-chave
        for sentiment_type, keywords in self.sentiment_keywords.items():
            count = sum(1 for keyword in keywords if keyword in text_lower)
            
            if sentiment_type == 'very_positive':
                score += count * 1.0
            elif sentiment_type == 'positive':
                score += count * 0.5
            elif sentiment_type == 'negative':
                score -= count * 0.5
            elif sentiment_type == 'very_negative':
                score -= count * 1.0
        
        # Análise com TextBlob
        try:
            blob = TextBlob(text)
            textblob_score = blob.sentiment.polarity
            score = (score + textblob_score) / 2
        except:
            pass
        
        return max(-1.0, min(1.0, score))
    
    def detect_emotions(self, text: str) -> Dict[str, float]:
        """Detecta emoções no texto."""
        emotions = {emotion: 0.0 for emotion in self.emotion_keywords.keys()}
        text_lower = text.lower()
        
        for emotion, keywords in self.emotion_keywords.items():
            count = sum(1 for keyword in keywords if keyword in text_lower)
            emotions[emotion] = min(1.0, count * 0.3)
        
        return emotions

class TopicExtractor:
    """Extrator de tópicos avançado."""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words=self._get_stop_words(),
            ngram_range=(1, 3),
            min_df=2,
            max_df=0.8
        )
        
        self.lda_model = None
        self.nmf_model = None
        self.fitted = False
        
        # Tópicos predefinidos específicos do domínio
        self.domain_topics = {
            'automação': ['automação', 'automatizar', 'processo', 'workflow', 'script'],
            'integração': ['integração', 'api', 'conectar', 'sincronizar', 'webhook'],
            'configuração': ['configuração', 'configurar', 'settings', 'parametros'],
            'problema_técnico': ['erro', 'bug', 'falha', 'exception', 'problema'],
            'suporte': ['ajuda', 'dúvida', 'como', 'tutorial', 'suporte'],
            'performance': ['lento', 'rápido', 'performance', 'otimização', 'velocidade'],
            'dados': ['dados', 'relatório', 'análise', 'informação', 'estatística'],
            'segurança': ['segurança', 'senha', 'token', 'autenticação', 'criptografia']
        }
    
    def _get_stop_words(self) -> List[str]:
        """Obtém lista de stop words."""
        portuguese_stops = [
            'o', 'a', 'de', 'do', 'da', 'em', 'um', 'uma', 'para', 'com', 'por',
            'é', 'ser', 'ter', 'que', 'não', 'se', 'eu', 'você', 'ele', 'ela',
            'como', 'mais', 'muito', 'bem', 'já', 'até', 'aqui', 'quando', 'onde'
        ]
        
        try:
            nltk_stops = list(stopwords.words('portuguese'))
            return list(set(portuguese_stops + nltk_stops))
        except:
            return portuguese_stops
    
    def fit_topic_models(self, documents: List[str], n_topics: int = 10):
        """Treina modelos de tópicos."""
        if not documents:
            return
        
        try:
            # Prepara documentos
            tfidf_matrix = self.vectorizer.fit_transform(documents)
            
            # LDA
            self.lda_model = LatentDirichletAllocation(
                n_components=n_topics,
                random_state=42,
                max_iter=10
            )
            self.lda_model.fit(tfidf_matrix)
            
            # NMF
            self.nmf_model = NMF(
                n_components=n_topics,
                random_state=42,
                max_iter=100
            )
            self.nmf_model.fit(tfidf_matrix)
            
            self.fitted = True
            logger.info(f"Modelos de tópicos treinados com {len(documents)} documentos")
            
        except Exception as e:
            logger.error(f"Erro ao treinar modelos de tópicos: {e}")
    
    def extract_topics(self, text: str, method: str = 'hybrid') -> List[str]:
        """Extrai tópicos do texto."""
        topics = []
        
        # Tópicos predefinidos
        text_lower = text.lower()
        for topic, keywords in self.domain_topics.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)
        
        # Tópicos automáticos (se modelos estiverem treinados)
        if self.fitted and method in ['lda', 'hybrid']:
            topics.extend(self._extract_lda_topics(text))
        
        if self.fitted and method in ['nmf', 'hybrid']:
            topics.extend(self._extract_nmf_topics(text))
        
        # YAKE para palavras-chave
        if method in ['yake', 'hybrid']:
            topics.extend(self._extract_yake_keywords(text))
        
        return list(set(topics))  # Remove duplicatas
    
    def _extract_lda_topics(self, text: str) -> List[str]:
        """Extrai tópicos usando LDA."""
        try:
            tfidf_vector = self.vectorizer.transform([text])
            topic_probs = self.lda_model.transform(tfidf_vector)[0]
            
            # Pega tópicos com probabilidade > 0.1
            feature_names = self.vectorizer.get_feature_names_out()
            topics = []
            
            for topic_idx, prob in enumerate(topic_probs):
                if prob > 0.1:
                    top_words = [feature_names[i] for i in 
                               self.lda_model.components_[topic_idx].argsort()[-3:][::-1]]
                    topic_name = f"lda_topic_{topic_idx}_{'-'.join(top_words[:2])}"
                    topics.append(topic_name)
            
            return topics
        except:
            return []
    
    def _extract_nmf_topics(self, text: str) -> List[str]:
        """Extrai tópicos usando NMF."""
        try:
            tfidf_vector = self.vectorizer.transform([text])
            topic_scores = self.nmf_model.transform(tfidf_vector)[0]
            
            feature_names = self.vectorizer.get_feature_names_out()
            topics = []
            
            for topic_idx, score in enumerate(topic_scores):
                if score > 0.1:
                    top_words = [feature_names[i] for i in 
                               self.nmf_model.components_[topic_idx].argsort()[-3:][::-1]]
                    topic_name = f"nmf_topic_{topic_idx}_{'-'.join(top_words[:2])}"
                    topics.append(topic_name)
            
            return topics
        except:
            return []
    
    def _extract_yake_keywords(self, text: str) -> List[str]:
        """Extrai palavras-chave usando YAKE."""
        try:
            kw_extractor = yake.KeywordExtractor(
                lan="pt",
                n=3,
                dedupLim=0.7,
                top=5
            )
            keywords = kw_extractor.extract_keywords(text)
            return [kw[1] for kw in keywords if kw[0] < 0.1]  # Score baixo = melhor
        except:
            return []

class BehaviorAnalyzer:
    """Analisador de padrões comportamentais."""
    
    def __init__(self):
        self.communication_styles = {
            'formal': ['por favor', 'obrigado', 'gostaria', 'poderia', 'senhor', 'senhora'],
            'informal': ['oi', 'tudo bem', 'valeu', 'blz', 'cara', 'galera'],
            'technical': ['api', 'código', 'função', 'variável', 'classe', 'método'],
            'casual': ['né', 'tipo', 'meio que', 'sei lá', 'talvez']
        }
    
    def analyze_user_behavior(self, user_messages: List[Dict]) -> UserBehaviorPattern:
        """Analisa padrão comportamental do usuário."""
        if not user_messages:
            return None
        
        user_id = user_messages[0].get('user_id', 'unknown')
        
        # Analisa estilo de comunicação
        communication_style = self._detect_communication_style(user_messages)
        
        # Analisa tópicos preferidos
        preferred_topics = self._extract_preferred_topics(user_messages)
        
        # Analisa padrões de atividade
        activity_pattern = self._analyze_activity_patterns(user_messages)
        
        # Analisa preferências de resposta
        response_preferences = self._analyze_response_preferences(user_messages)
        
        # Calcula estabilidade de sentimento
        sentiment_stability = self._calculate_sentiment_stability(user_messages)
        
        # Determina nível de engajamento
        engagement_level = self._determine_engagement_level(user_messages)
        
        # Calcula taxa de resolução de problemas
        problem_resolution_rate = self._calculate_problem_resolution_rate(user_messages)
        
        return UserBehaviorPattern(
            user_id=user_id,
            communication_style=communication_style,
            preferred_topics=preferred_topics,
            activity_pattern=activity_pattern,
            response_preferences=response_preferences,
            sentiment_stability=sentiment_stability,
            engagement_level=engagement_level,
            problem_resolution_rate=problem_resolution_rate
        )
    
    def _detect_communication_style(self, messages: List[Dict]) -> str:
        """Detecta estilo de comunicação predominante."""
        style_scores = {style: 0 for style in self.communication_styles.keys()}
        
        for message in messages:
            content = message.get('content', '').lower()
            for style, keywords in self.communication_styles.items():
                score = sum(1 for keyword in keywords if keyword in content)
                style_scores[style] += score
        
        if not any(style_scores.values()):
            return 'neutral'
        
        return max(style_scores.keys(), key=lambda k: style_scores[k])
    
    def _extract_preferred_topics(self, messages: List[Dict]) -> List[str]:
        """Extrai tópicos preferidos do usuário."""
        topic_counter = Counter()
        
        for message in messages:
            topics = message.get('topics', [])
            topic_counter.update(topics)
        
        # Retorna top 5 tópicos
        return [topic for topic, count in topic_counter.most_common(5)]
    
    def _analyze_activity_patterns(self, messages: List[Dict]) -> Dict[str, Any]:
        """Analisa padrões de atividade temporal."""
        hours = []
        days = []
        
        for message in messages:
            timestamp_str = message.get('timestamp')
            if timestamp_str:
                try:
                    if isinstance(timestamp_str, str):
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    else:
                        timestamp = timestamp_str
                    
                    hours.append(timestamp.hour)
                    days.append(timestamp.weekday())
                except:
                    continue
        
        if not hours:
            return {}
        
        hour_distribution = Counter(hours)
        day_distribution = Counter(days)
        
        # Identifica padrões
        most_active_hours = [hour for hour, count in hour_distribution.most_common(3)]
        most_active_days = [day for day, count in day_distribution.most_common(3)]
        
        return {
            'most_active_hours': most_active_hours,
            'most_active_days': most_active_days,
            'hour_distribution': dict(hour_distribution),
            'day_distribution': dict(day_distribution),
            'total_messages': len(messages)
        }
    
    def _analyze_response_preferences(self, messages: List[Dict]) -> Dict[str, Any]:
        """Analisa preferências de resposta."""
        avg_length = np.mean([len(msg.get('content', '')) for msg in messages])
        
        # Analisa tipos de pergunta
        question_types = {
            'how': 0,
            'what': 0,
            'why': 0,
            'when': 0,
            'where': 0
        }
        
        for message in messages:
            content = message.get('content', '').lower()
            if 'como' in content or 'how' in content:
                question_types['how'] += 1
            elif 'que' in content or 'what' in content:
                question_types['what'] += 1
            elif 'por que' in content or 'why' in content:
                question_types['why'] += 1
            elif 'quando' in content or 'when' in content:
                question_types['when'] += 1
            elif 'onde' in content or 'where' in content:
                question_types['where'] += 1
        
        return {
            'preferred_message_length': 'short' if avg_length < 50 else 'medium' if avg_length < 150 else 'long',
            'question_type_preference': max(question_types.keys(), key=lambda k: question_types[k]) if any(question_types.values()) else 'general',
            'avg_message_length': avg_length
        }
    
    def _calculate_sentiment_stability(self, messages: List[Dict]) -> float:
        """Calcula estabilidade do sentimento."""
        sentiments = [msg.get('sentiment_score', 0.0) for msg in messages]
        
        if len(sentiments) < 2:
            return 0.5
        
        # Calcula variabilidade (inverso do desvio padrão normalizado)
        std_dev = np.std(sentiments)
        stability = max(0.0, 1.0 - std_dev)
        
        return stability
    
    def _determine_engagement_level(self, messages: List[Dict]) -> str:
        """Determina nível de engajamento."""
        # Calcula métricas de engajamento
        total_messages = len(messages)
        avg_length = np.mean([len(msg.get('content', '')) for msg in messages])
        
        # Calcula frequência temporal
        if total_messages > 1:
            timestamps = []
            for msg in messages:
                timestamp_str = msg.get('timestamp')
                if timestamp_str:
                    try:
                        if isinstance(timestamp_str, str):
                            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        else:
                            timestamp = timestamp_str
                        timestamps.append(timestamp)
                    except:
                        continue
            
            if len(timestamps) > 1:
                time_span = (max(timestamps) - min(timestamps)).total_seconds()
                frequency = total_messages / (time_span / 3600)  # mensagens por hora
            else:
                frequency = 0
        else:
            frequency = 0
        
        # Determina nível baseado em heurísticas
        if total_messages >= 20 and avg_length >= 50 and frequency >= 2:
            return 'high'
        elif total_messages >= 10 and avg_length >= 30:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_problem_resolution_rate(self, messages: List[Dict]) -> float:
        """Calcula taxa de resolução de problemas."""
        problem_indicators = ['problema', 'erro', 'não funciona', 'bug', 'falha']
        resolution_indicators = ['resolvido', 'funcionou', 'obrigado', 'perfeito', 'solucionado']
        
        problems = 0
        resolutions = 0
        
        for message in messages:
            content = message.get('content', '').lower()
            
            if any(indicator in content for indicator in problem_indicators):
                problems += 1
            
            if any(indicator in content for indicator in resolution_indicators):
                resolutions += 1
        
        if problems == 0:
            return 1.0  # Sem problemas = 100% resolução
        
        return min(1.0, resolutions / problems)

class ConversationAnalyzer:
    """Analisador principal de conversas."""
    
    def __init__(self, data_dir: str = "./data/analysis"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Banco de dados
        self.db_path = self.data_dir / "conversation_analysis.db"
        self._init_database()
        
        # Componentes especializados
        self.sentiment_analyzer = SentimentAnalyzer()
        self.topic_extractor = TopicExtractor()
        self.behavior_analyzer = BehaviorAnalyzer()
        
        # Cache para resultados
        self.analysis_cache = {}
        
        # Lock para thread safety
        self.lock = threading.Lock()
        
        # Worker para análise contínua
        self._start_analysis_worker()
        
        logger.info("ConversationAnalyzer inicializado com sucesso")
    
    def _init_database(self):
        """Inicializa banco de dados."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Tabela de métricas de conversa
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                total_messages INTEGER NOT NULL,
                avg_message_length REAL NOT NULL,
                conversation_duration REAL NOT NULL,
                sentiment_progression TEXT NOT NULL,
                topic_diversity REAL NOT NULL,
                engagement_score REAL NOT NULL,
                resolution_score REAL NOT NULL,
                satisfaction_score REAL NOT NULL,
                complexity_score REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de tendências de tópicos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS topic_trends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_name TEXT NOT NULL,
                frequency INTEGER NOT NULL,
                sentiment_avg REAL NOT NULL,
                growth_rate REAL NOT NULL,
                related_topics TEXT,
                peak_hours TEXT,
                user_segments TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de padrões comportamentais
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_behavior_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                communication_style TEXT NOT NULL,
                preferred_topics TEXT,
                activity_pattern TEXT,
                response_preferences TEXT,
                sentiment_stability REAL NOT NULL,
                engagement_level TEXT NOT NULL,
                problem_resolution_rate REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de insights
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                insight_type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                confidence REAL NOT NULL,
                impact_level TEXT NOT NULL,
                recommended_actions TEXT,
                supporting_data TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _start_analysis_worker(self):
        """Inicia worker para análise contínua."""
        def analysis_worker():
            while True:
                try:
                    self._run_analysis_cycle()
                    time.sleep(3600)  # Análise a cada hora
                except Exception as e:
                    logger.error(f"Erro no worker de análise: {e}")
                    time.sleep(300)  # Retry em 5 minutos
        
        worker_thread = threading.Thread(target=analysis_worker, daemon=True)
        worker_thread.start()
    
    def analyze_conversation(self, conversation_data: Dict[str, Any]) -> ConversationMetrics:
        """Analisa uma conversa completa."""
        conversation_id = conversation_data.get('id', 'unknown')
        user_id = conversation_data.get('user_id', 'unknown')
        messages = conversation_data.get('messages', [])
        
        if not messages:
            return None
        
        # Calcula métricas básicas
        total_messages = len(messages)
        message_lengths = [len(msg.get('content', '')) for msg in messages]
        avg_message_length = np.mean(message_lengths)
        
        # Calcula duração da conversa
        timestamps = []
        for msg in messages:
            timestamp_str = msg.get('timestamp')
            if timestamp_str:
                try:
                    if isinstance(timestamp_str, str):
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    else:
                        timestamp = timestamp_str
                    timestamps.append(timestamp)
                except:
                    continue
        
        if len(timestamps) > 1:
            conversation_duration = (max(timestamps) - min(timestamps)).total_seconds() / 60  # minutos
        else:
            conversation_duration = 1.0  # 1 minuto mínimo
        
        # Analisa progressão de sentimento
        sentiment_progression = self.sentiment_analyzer.analyze_sentiment_progression(messages)
        
        # Calcula diversidade de tópicos
        all_topics = []
        for msg in messages:
            topics = msg.get('topics', [])
            all_topics.extend(topics)
        
        topic_diversity = len(set(all_topics)) / max(1, len(all_topics)) if all_topics else 0.0
        
        # Calcula scores compostos
        engagement_score = self._calculate_engagement_score(messages, conversation_duration)
        resolution_score = self._calculate_resolution_score(messages)
        satisfaction_score = self._calculate_satisfaction_score(sentiment_progression)
        complexity_score = self._calculate_complexity_score(messages)
        
        metrics = ConversationMetrics(
            conversation_id=conversation_id,
            user_id=user_id,
            total_messages=total_messages,
            avg_message_length=avg_message_length,
            conversation_duration=conversation_duration,
            sentiment_progression=sentiment_progression,
            topic_diversity=topic_diversity,
            engagement_score=engagement_score,
            resolution_score=resolution_score,
            satisfaction_score=satisfaction_score,
            complexity_score=complexity_score,
            timestamp=datetime.now()
        )
        
        # Salva no banco
        self._save_conversation_metrics(metrics)
        
        return metrics
    
    def _calculate_engagement_score(self, messages: List[Dict], duration: float) -> float:
        """Calcula score de engajamento."""
        if not messages:
            return 0.0
        
        # Fatores de engajamento
        message_frequency = len(messages) / duration  # mensagens por minuto
        avg_length = np.mean([len(msg.get('content', '')) for msg in messages])
        
        # Presença de perguntas
        question_count = sum(1 for msg in messages if '?' in msg.get('content', ''))
        question_ratio = question_count / len(messages)
        
        # Score composto
        frequency_score = min(1.0, message_frequency / 5)  # Normaliza para máx 5 msg/min
        length_score = min(1.0, avg_length / 100)  # Normaliza para máx 100 chars
        interaction_score = question_ratio
        
        engagement_score = (frequency_score * 0.4 + length_score * 0.3 + interaction_score * 0.3)
        
        return engagement_score
    
    def _calculate_resolution_score(self, messages: List[Dict]) -> float:
        """Calcula score de resolução."""
        resolution_indicators = ['resolvido', 'funcionou', 'obrigado', 'perfeito', 'solucionado', 'entendi']
        problem_indicators = ['problema', 'erro', 'não funciona', 'bug', 'falha', 'dúvida']
        
        problems = 0
        resolutions = 0
        
        for msg in messages:
            content = msg.get('content', '').lower()
            
            if any(indicator in content for indicator in problem_indicators):
                problems += 1
            
            if any(indicator in content for indicator in resolution_indicators):
                resolutions += 1
        
        if problems == 0:
            return 1.0 if resolutions > 0 else 0.5
        
        return min(1.0, resolutions / problems)
    
    def _calculate_satisfaction_score(self, sentiment_progression: List[float]) -> float:
        """Calcula score de satisfação."""
        if not sentiment_progression:
            return 0.5
        
        # Score baseado na progressão do sentimento
        final_sentiment = sentiment_progression[-1]
        avg_sentiment = np.mean(sentiment_progression)
        
        # Melhoria do sentimento ao longo da conversa
        if len(sentiment_progression) > 1:
            sentiment_trend = sentiment_progression[-1] - sentiment_progression[0]
        else:
            sentiment_trend = 0
        
        # Score composto
        satisfaction_score = (
            (final_sentiment + 1) / 2 * 0.5 +  # Sentimento final (normalizado para 0-1)
            (avg_sentiment + 1) / 2 * 0.3 +    # Sentimento médio
            max(0, sentiment_trend) * 0.2       # Melhoria do sentimento
        )
        
        return min(1.0, satisfaction_score)
    
    def _calculate_complexity_score(self, messages: List[Dict]) -> float:
        """Calcula score de complexidade."""
        if not messages:
            return 0.0
        
        # Fatores de complexidade
        total_words = sum(len(msg.get('content', '').split()) for msg in messages)
        avg_words_per_message = total_words / len(messages)
        
        # Presença de termos técnicos
        technical_terms = ['api', 'código', 'função', 'erro', 'configuração', 'integração']
        technical_count = sum(
            1 for msg in messages 
            for term in technical_terms 
            if term in msg.get('content', '').lower()
        )
        
        # Número de tópicos diferentes
        all_topics = []
        for msg in messages:
            all_topics.extend(msg.get('topics', []))
        unique_topics = len(set(all_topics))
        
        # Score composto
        length_complexity = min(1.0, avg_words_per_message / 50)
        technical_complexity = min(1.0, technical_count / len(messages))
        topic_complexity = min(1.0, unique_topics / 10)
        
        complexity_score = (length_complexity * 0.4 + technical_complexity * 0.4 + topic_complexity * 0.2)
        
        return complexity_score
    
    def analyze_topic_trends(self, time_period_days: int = 7) -> List[TopicTrend]:
        """Analisa tendências de tópicos."""
        cutoff_date = datetime.now() - timedelta(days=time_period_days)
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Busca métricas recentes
        cursor.execute('''
            SELECT * FROM conversation_metrics 
            WHERE timestamp > ?
            ORDER BY timestamp DESC
        ''', (cutoff_date,))
        
        metrics_data = cursor.fetchall()
        conn.close()
        
        if not metrics_data:
            return []
        
        # Analisa tendências (implementação simplificada)
        # Em produção, seria mais sofisticada
        
        trends = []
        # Placeholder para análise de tendências complexa
        
        return trends
    
    def generate_insights(self, analysis_window_hours: int = 24) -> List[ConversationInsight]:
        """Gera insights automáticos."""
        cutoff_time = datetime.now() - timedelta(hours=analysis_window_hours)
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Busca dados recentes
        cursor.execute('''
            SELECT * FROM conversation_metrics 
            WHERE timestamp > ?
        ''', (cutoff_time,))
        
        recent_metrics = cursor.fetchall()
        conn.close()
        
        if not recent_metrics:
            return []
        
        insights = []
        
        # Insight 1: Satisfação baixa
        low_satisfaction_count = sum(1 for row in recent_metrics if row[10] < 0.5)  # satisfaction_score
        if low_satisfaction_count > len(recent_metrics) * 0.3:
            insight = ConversationInsight(
                insight_type='problem',
                title='Alta Taxa de Insatisfação',
                description=f'{low_satisfaction_count} de {len(recent_metrics)} conversas tiveram baixa satisfação',
                confidence=0.8,
                impact_level='high',
                recommended_actions=[
                    'Revisar qualidade das respostas',
                    'Treinar modelo com foco em satisfação',
                    'Analisar conversas com baixa satisfação'
                ],
                supporting_data={'low_satisfaction_conversations': low_satisfaction_count},
                timestamp=datetime.now()
            )
            insights.append(insight)
        
        # Insight 2: Baixa resolução de problemas
        low_resolution_count = sum(1 for row in recent_metrics if row[9] < 0.6)  # resolution_score
        if low_resolution_count > len(recent_metrics) * 0.2:
            insight = ConversationInsight(
                insight_type='opportunity',
                title='Oportunidade de Melhoria na Resolução',
                description=f'{low_resolution_count} conversas tiveram baixa taxa de resolução',
                confidence=0.7,
                impact_level='medium',
                recommended_actions=[
                    'Melhorar base de conhecimento',
                    'Treinar assistente com mais exemplos de resolução',
                    'Implementar escalação automática para humanos'
                ],
                supporting_data={'low_resolution_conversations': low_resolution_count},
                timestamp=datetime.now()
            )
            insights.append(insight)
        
        # Insight 3: Engajamento crescente
        recent_engagement = np.mean([row[8] for row in recent_metrics[-10:]])  # últimas 10
        older_engagement = np.mean([row[8] for row in recent_metrics[:10]])    # primeiras 10
        
        if len(recent_metrics) >= 20 and recent_engagement > older_engagement * 1.1:
            insight = ConversationInsight(
                insight_type='trend',
                title='Engajamento em Crescimento',
                description=f'Engajamento aumentou {((recent_engagement/older_engagement-1)*100):.1f}%',
                confidence=0.9,
                impact_level='medium',
                recommended_actions=[
                    'Identificar fatores que levaram ao aumento',
                    'Replicar estratégias bem-sucedidas',
                    'Monitorar para manter tendência'
                ],
                supporting_data={
                    'recent_engagement': recent_engagement,
                    'older_engagement': older_engagement
                },
                timestamp=datetime.now()
            )
            insights.append(insight)
        
        # Salva insights no banco
        for insight in insights:
            self._save_insight(insight)
        
        return insights
    
    def _save_conversation_metrics(self, metrics: ConversationMetrics):
        """Salva métricas no banco."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO conversation_metrics 
            (conversation_id, user_id, total_messages, avg_message_length,
             conversation_duration, sentiment_progression, topic_diversity,
             engagement_score, resolution_score, satisfaction_score, complexity_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            metrics.conversation_id, metrics.user_id, metrics.total_messages,
            metrics.avg_message_length, metrics.conversation_duration,
            json.dumps(metrics.sentiment_progression), metrics.topic_diversity,
            metrics.engagement_score, metrics.resolution_score,
            metrics.satisfaction_score, metrics.complexity_score
        ))
        
        conn.commit()
        conn.close()
    
    def _save_insight(self, insight: ConversationInsight):
        """Salva insight no banco."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO conversation_insights 
            (insight_type, title, description, confidence, impact_level,
             recommended_actions, supporting_data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            insight.insight_type, insight.title, insight.description,
            insight.confidence, insight.impact_level,
            json.dumps(insight.recommended_actions),
            json.dumps(insight.supporting_data, default=str)
        ))
        
        conn.commit()
        conn.close()
    
    def _run_analysis_cycle(self):
        """Executa ciclo de análise automática."""
        try:
            # Gera insights automáticos
            insights = self.generate_insights(24)
            
            if insights:
                logger.info(f"Gerados {len(insights)} insights automáticos")
                
                for insight in insights:
                    logger.info(f"Insight: {insight.title} ({insight.impact_level} impact)")
            
        except Exception as e:
            logger.error(f"Erro no ciclo de análise: {e}")
    
    def get_analytics_summary(self, days: int = 7) -> Dict[str, Any]:
        """Obtém resumo analítico."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Estatísticas básicas
        cursor.execute('''
            SELECT 
                COUNT(*) as total_conversations,
                AVG(satisfaction_score) as avg_satisfaction,
                AVG(resolution_score) as avg_resolution,
                AVG(engagement_score) as avg_engagement,
                AVG(complexity_score) as avg_complexity
            FROM conversation_metrics 
            WHERE timestamp > ?
        ''', (cutoff_date,))
        
        stats = cursor.fetchone()
        
        # Insights recentes
        cursor.execute('''
            SELECT insight_type, COUNT(*) as count
            FROM conversation_insights 
            WHERE timestamp > ?
            GROUP BY insight_type
        ''', (cutoff_date,))
        
        insights_by_type = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'period_days': days,
            'total_conversations': stats[0] or 0,
            'avg_satisfaction': stats[1] or 0,
            'avg_resolution': stats[2] or 0,
            'avg_engagement': stats[3] or 0,
            'avg_complexity': stats[4] or 0,
            'insights_by_type': insights_by_type,
            'generated_at': datetime.now().isoformat()
        }
    
    def export_analysis_report(self, output_path: str, days: int = 30) -> str:
        """Exporta relatório de análise."""
        try:
            summary = self.get_analytics_summary(days)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Relatório exportado: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Erro ao exportar relatório: {e}")
            raise

# Função de teste
def main():
    """Função principal para teste."""
    analyzer = ConversationAnalyzer()
    
    # Simula dados de conversa
    conversation_data = {
        'id': 'test_conv_123',
        'user_id': 'user_456',
        'messages': [
            {
                'content': 'Olá, preciso de ajuda com uma integração',
                'timestamp': datetime.now() - timedelta(minutes=10),
                'topics': ['integração', 'ajuda'],
                'sentiment_score': 0.0
            },
            {
                'content': 'Claro! Posso ajudá-lo. Qual integração você está tentando configurar?',
                'timestamp': datetime.now() - timedelta(minutes=9),
                'topics': ['integração', 'suporte'],
                'sentiment_score': 0.3
            },
            {
                'content': 'É a integração com o Bitrix24, está dando erro',
                'timestamp': datetime.now() - timedelta(minutes=8),
                'topics': ['bitrix24', 'erro'],
                'sentiment_score': -0.2
            },
            {
                'content': 'Perfeito! Funcionou, muito obrigado!',
                'timestamp': datetime.now() - timedelta(minutes=2),
                'topics': ['resolução', 'agradecimento'],
                'sentiment_score': 0.8
            }
        ]
    }
    
    # Analisa conversa
    metrics = analyzer.analyze_conversation(conversation_data)
    print("Métricas da conversa:")
    print(json.dumps(asdict(metrics), indent=2, default=str))
    
    # Gera insights
    insights = analyzer.generate_insights(1)
    print(f"\nInsights gerados: {len(insights)}")
    for insight in insights:
        print(f"- {insight.title}: {insight.description}")
    
    # Resumo analítico
    summary = analyzer.get_analytics_summary(1)
    print("\nResumo analítico:")
    print(json.dumps(summary, indent=2, default=str))

if __name__ == "__main__":
    main()