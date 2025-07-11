"""
NLP Processor - Natural Language Processing utilities for AUTOBOT
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class Intent:
    """Detected user intent"""
    name: str
    confidence: float
    entities: Dict[str, str]
    context: Dict[str, any]

@dataclass
class Entity:
    """Named entity in text"""
    type: str
    value: str
    start: int
    end: int
    confidence: float

class NLPProcessor:
    """
    Natural Language Processing for understanding user intents and extracting entities
    """
    
    def __init__(self):
        self.intent_patterns = self._load_intent_patterns()
        self.entity_patterns = self._load_entity_patterns()
        
    def _load_intent_patterns(self) -> Dict[str, List[str]]:
        """Load intent detection patterns"""
        return {
            "automation_create": [
                r"criar automação",
                r"automatizar",
                r"fazer automação",
                r"gravar ações",
                r"criar script",
                r"automatize"
            ],
            "automation_execute": [
                r"executar automação",
                r"rodar automação",
                r"executar script",
                r"rodar script",
                r"iniciar automação"
            ],
            "automation_list": [
                r"listar automações",
                r"mostrar automações",
                r"ver automações",
                r"automações disponíveis"
            ],
            "question": [
                r"o que é",
                r"como fazer",
                r"me explique",
                r"qual é",
                r"por que",
                r"como funciona"
            ],
            "greeting": [
                r"olá",
                r"oi",
                r"bom dia",
                r"boa tarde",
                r"boa noite",
                r"hey",
                r"e aí"
            ],
            "help": [
                r"ajuda",
                r"help",
                r"socorro",
                r"não sei",
                r"como usar",
                r"o que você faz"
            ],
            "integration": [
                r"integrar com",
                r"conectar",
                r"api",
                r"webhook",
                r"bitrix",
                r"locaweb",
                r"ixcsoft",
                r"fluctus"
            ],
            "system_info": [
                r"status do sistema",
                r"informações",
                r"versão",
                r"logs",
                r"configuração"
            ]
        }
    
    def _load_entity_patterns(self) -> Dict[str, str]:
        """Load entity extraction patterns"""
        return {
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "phone": r"\b\(?\d{2}\)?\s?\d{4,5}-?\d{4}\b",
            "url": r"https?://[^\s]+",
            "number": r"\b\d+\b",
            "time": r"\b\d{1,2}:\d{2}\b",
            "date": r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
            "automation_name": r"automação[:\s]+([\"']?)([^\"'\n]+)\1",
            "file_path": r"[\"']?([A-Za-z]:[\\\/][\w\s\\\/.-]+|\/[\w\s\/.-]+)[\"']?",
            "application": r"\b(chrome|firefox|word|excel|notepad|calculator|outlook)\b",
        }
    
    async def analyze_text(self, text: str, context: Dict = None) -> Dict:
        """
        Analyze text to extract intent, entities, and sentiment
        """
        try:
            text_lower = text.lower().strip()
            
            # Detect intent
            intent = self._detect_intent(text_lower)
            
            # Extract entities
            entities = self._extract_entities(text)
            
            # Analyze sentiment (basic implementation)
            sentiment = self._analyze_sentiment(text_lower)
            
            # Extract keywords
            keywords = self._extract_keywords(text_lower)
            
            return {
                "intent": intent,
                "entities": entities,
                "sentiment": sentiment,
                "keywords": keywords,
                "original_text": text,
                "processed_text": text_lower,
                "context": context or {}
            }
            
        except Exception as e:
            logger.error(f"Error analyzing text: {e}")
            return {
                "intent": Intent("unknown", 0.0, {}, {}),
                "entities": [],
                "sentiment": {"polarity": 0.0, "label": "neutral"},
                "keywords": [],
                "original_text": text,
                "error": str(e)
            }
    
    def _detect_intent(self, text: str) -> Intent:
        """Detect user intent from text"""
        try:
            best_intent = "general"
            best_confidence = 0.0
            entities = {}
            
            for intent_name, patterns in self.intent_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        # Calculate confidence based on pattern match
                        confidence = len(matches) * 0.8
                        if pattern in text:
                            confidence += 0.2  # Exact match bonus
                        
                        if confidence > best_confidence:
                            best_confidence = confidence
                            best_intent = intent_name
            
            # Extract context-specific entities
            if best_intent == "automation_create":
                entities = self._extract_automation_entities(text)
            elif best_intent == "integration":
                entities = self._extract_integration_entities(text)
            
            return Intent(
                name=best_intent,
                confidence=min(best_confidence, 1.0),
                entities=entities,
                context={"detected_patterns": []}
            )
            
        except Exception as e:
            logger.error(f"Error detecting intent: {e}")
            return Intent("unknown", 0.0, {}, {})
    
    def _extract_entities(self, text: str) -> List[Entity]:
        """Extract named entities from text"""
        entities = []
        
        try:
            for entity_type, pattern in self.entity_patterns.items():
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    entity = Entity(
                        type=entity_type,
                        value=match.group(),
                        start=match.start(),
                        end=match.end(),
                        confidence=0.9
                    )
                    entities.append(entity)
            
            return entities
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return []
    
    def _extract_automation_entities(self, text: str) -> Dict[str, str]:
        """Extract automation-specific entities"""
        entities = {}
        
        # Extract automation name
        name_match = re.search(r"automação[:\s]+[\"']?([^\"'\n]+)[\"']?", text, re.IGNORECASE)
        if name_match:
            entities["automation_name"] = name_match.group(1).strip()
        
        # Extract action keywords
        action_keywords = [
            "clicar", "digitar", "abrir", "fechar", "copiar", "colar", 
            "esperar", "screenshot", "navegar", "preencher"
        ]
        
        found_actions = []
        for action in action_keywords:
            if action in text.lower():
                found_actions.append(action)
        
        if found_actions:
            entities["actions"] = found_actions
        
        # Extract applications
        apps = ["chrome", "firefox", "word", "excel", "notepad", "outlook"]
        found_apps = [app for app in apps if app in text.lower()]
        if found_apps:
            entities["applications"] = found_apps
        
        return entities
    
    def _extract_integration_entities(self, text: str) -> Dict[str, str]:
        """Extract integration-specific entities"""
        entities = {}
        
        # Extract integration platforms
        platforms = ["bitrix24", "locaweb", "ixcsoft", "fluctus"]
        for platform in platforms:
            if platform in text.lower():
                entities["platform"] = platform
                break
        
        # Extract API-related keywords
        if "webhook" in text.lower():
            entities["type"] = "webhook"
        elif "api" in text.lower():
            entities["type"] = "api"
        
        return entities
    
    def _analyze_sentiment(self, text: str) -> Dict[str, any]:
        """Basic sentiment analysis"""
        positive_words = [
            "bom", "ótimo", "excelente", "perfeito", "maravilhoso", "gostei",
            "funcionou", "sucesso", "incrível", "fantástico", "legal"
        ]
        
        negative_words = [
            "ruim", "péssimo", "horrível", "erro", "problema", "falhou",
            "não funciona", "bug", "lento", "difícil", "complicado"
        ]
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            polarity = min(positive_count * 0.3, 1.0)
            label = "positive"
        elif negative_count > positive_count:
            polarity = max(-negative_count * 0.3, -1.0)
            label = "negative"
        else:
            polarity = 0.0
            label = "neutral"
        
        return {
            "polarity": polarity,
            "label": label,
            "positive_count": positive_count,
            "negative_count": negative_count
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text"""
        # Remove common stop words
        stop_words = {
            "a", "o", "e", "de", "da", "do", "em", "para", "com", "por", "um", "uma",
            "é", "que", "não", "se", "eu", "você", "ele", "ela", "nós", "eles", "elas",
            "este", "esta", "esse", "essa", "aquele", "aquela", "muito", "mais", "como",
            "quando", "onde", "por que", "porque", "então", "mas", "ou", "já", "ainda"
        }
        
        # Split text into words and filter
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        
        # Count frequency and return most common
        word_freq = {}
        for word in keywords:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and return top keywords
        sorted_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_keywords[:10]]
    
    def extract_automation_steps(self, description: str) -> List[Dict]:
        """Extract automation steps from natural language description"""
        try:
            steps = []
            sentences = re.split(r'[.!?;]', description)
            
            for sentence in sentences:
                sentence = sentence.strip().lower()
                if not sentence:
                    continue
                
                step = self._parse_automation_sentence(sentence)
                if step:
                    steps.append(step)
            
            return steps
            
        except Exception as e:
            logger.error(f"Error extracting automation steps: {e}")
            return []
    
    def _parse_automation_sentence(self, sentence: str) -> Optional[Dict]:
        """Parse a single sentence into an automation step"""
        # Click actions
        if any(word in sentence for word in ["clicar", "clique", "click"]):
            target = self._extract_click_target(sentence)
            return {
                "action": "click",
                "target": target,
                "description": sentence
            }
        
        # Type actions
        elif any(word in sentence for word in ["digitar", "escrever", "type"]):
            text = self._extract_text_to_type(sentence)
            target = self._extract_input_target(sentence)
            return {
                "action": "type",
                "target": target,
                "value": text,
                "description": sentence
            }
        
        # Wait actions
        elif any(word in sentence for word in ["esperar", "aguardar", "wait"]):
            duration = self._extract_wait_duration(sentence)
            return {
                "action": "wait",
                "parameters": {"duration": duration},
                "description": sentence
            }
        
        # Navigate actions
        elif any(word in sentence for word in ["abrir", "navegar", "acessar", "ir para"]):
            url = self._extract_url(sentence)
            if url:
                return {
                    "action": "web_navigate",
                    "target": url,
                    "description": sentence
                }
        
        return None
    
    def _extract_click_target(self, sentence: str) -> str:
        """Extract click target from sentence"""
        # Look for quoted text
        quoted = re.search(r'["\']([^"\']+)["\']', sentence)
        if quoted:
            return quoted.group(1)
        
        # Look for "botão X" pattern
        button_match = re.search(r'botão\s+(\w+)', sentence)
        if button_match:
            return button_match.group(1)
        
        # Look for "em X" pattern
        em_match = re.search(r'em\s+(\w+)', sentence)
        if em_match:
            return em_match.group(1)
        
        return "screen_center"
    
    def _extract_text_to_type(self, sentence: str) -> str:
        """Extract text to type from sentence"""
        # Look for quoted text
        quoted = re.search(r'["\']([^"\']+)["\']', sentence)
        if quoted:
            return quoted.group(1)
        
        # Look for "texto X" pattern
        texto_match = re.search(r'texto\s+(.+)', sentence)
        if texto_match:
            return texto_match.group(1).strip()
        
        return ""
    
    def _extract_input_target(self, sentence: str) -> str:
        """Extract input target from sentence"""
        # Look for "no campo X" pattern
        campo_match = re.search(r'no\s+campo\s+(\w+)', sentence)
        if campo_match:
            return f"name:{campo_match.group(1)}"
        
        # Look for "na caixa X" pattern
        caixa_match = re.search(r'na\s+caixa\s+(\w+)', sentence)
        if caixa_match:
            return f"id:{caixa_match.group(1)}"
        
        return "active_element"
    
    def _extract_wait_duration(self, sentence: str) -> float:
        """Extract wait duration from sentence"""
        # Look for numbers followed by time units
        duration_match = re.search(r'(\d+(?:\.\d+)?)\s*(segundos?|minutos?|s|m)', sentence)
        if duration_match:
            value = float(duration_match.group(1))
            unit = duration_match.group(2).lower()
            
            if unit.startswith('min') or unit == 'm':
                return value * 60
            else:
                return value
        
        return 1.0  # Default 1 second
    
    def _extract_url(self, sentence: str) -> Optional[str]:
        """Extract URL from sentence"""
        url_match = re.search(r'https?://[^\s]+', sentence)
        if url_match:
            return url_match.group()
        
        # Look for domain patterns
        domain_match = re.search(r'(\w+\.\w+(?:\.\w+)?)', sentence)
        if domain_match:
            domain = domain_match.group(1)
            if not domain.startswith('http'):
                return f"https://{domain}"
            return domain
        
        return None