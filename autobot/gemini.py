"""
Enhanced Gemini AI Integration
Improved error handling, retry logic, and response caching
"""
import os
import time
import logging
from typing import Optional, Dict, Any
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

# Response cache for similar prompts
response_cache = {}
CACHE_TIMEOUT = 3600  # 1 hour

class GeminiError(Exception):
    """Custom exception for Gemini API errors"""
    pass

def is_similar_prompt(prompt1: str, prompt2: str, threshold: float = 0.8) -> bool:
    """Simple similarity check for prompts"""
    words1 = set(prompt1.lower().split())
    words2 = set(prompt2.lower().split())
    
    if not words1 or not words2:
        return False
    
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    return intersection / union >= threshold

def get_cached_response(prompt: str) -> Optional[str]:
    """Check if we have a cached response for a similar prompt"""
    current_time = time.time()
    
    # Clean expired cache entries
    expired_keys = [key for key, (_, timestamp) in response_cache.items() 
                   if current_time - timestamp > CACHE_TIMEOUT]
    for key in expired_keys:
        del response_cache[key]
    
    # Look for similar prompts
    for cached_prompt, (response, timestamp) in response_cache.items():
        if current_time - timestamp <= CACHE_TIMEOUT and is_similar_prompt(prompt, cached_prompt):
            logger.info(f"Found cached response for similar prompt")
            return response
    
    return None

def cache_response(prompt: str, response: str):
    """Cache a response for future use"""
    response_cache[prompt] = (response, time.time())
    
    # Limit cache size
    if len(response_cache) > 100:
        oldest_key = min(response_cache.keys(), 
                        key=lambda k: response_cache[k][1])
        del response_cache[oldest_key]

def gemini_ask(prompt: str, max_retries: int = 3, timeout: int = 30) -> str:
    """
    Enhanced Gemini API call with retry logic and caching
    """
    if not GEMINI_API_KEY:
        raise GeminiError("GEMINI_API_KEY not configured in .env file")
    
    if not prompt or not prompt.strip():
        raise GeminiError("Prompt cannot be empty")
    
    prompt = prompt.strip()
    
    # Check cache first
    cached_response = get_cached_response(prompt)
    if cached_response:
        return cached_response
    
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }
    
    data = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 2048,
            "stopSequences": []
        },
        "safetySettings": [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
    }
    
    last_error = None
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Sending request to Gemini (attempt {attempt + 1}/{max_retries})")
            
            response = requests.post(
                GEMINI_API_URL,
                json=data,
                headers=headers,
                timeout=timeout
            )
            
            # Handle different response status codes
            if response.status_code == 200:
                result = response.json()
                
                if "candidates" in result and result["candidates"]:
                    candidate = result["candidates"][0]
                    
                    if "content" in candidate and "parts" in candidate["content"]:
                        text_response = candidate["content"]["parts"][0].get("text", "")
                        if text_response:
                            logger.info("Successfully received response from Gemini")
                            cache_response(prompt, text_response)
                            return text_response
                    
                    # Handle safety filter blocks
                    if candidate.get("finishReason") == "SAFETY":
                        safety_msg = "Resposta bloqueada por filtros de segurança. Tente reformular sua pergunta."
                        logger.warning("Response blocked by safety filters")
                        return safety_msg
                
                # Handle empty response
                error_msg = "Gemini retornou uma resposta vazia"
                logger.warning(error_msg)
                raise GeminiError(error_msg)
            
            elif response.status_code == 400:
                error_data = response.json()
                error_msg = f"Erro na requisição: {error_data.get('error', {}).get('message', 'Dados inválidos')}"
                logger.error(error_msg)
                raise GeminiError(error_msg)
            
            elif response.status_code == 403:
                error_msg = "Chave de API inválida ou acesso negado"
                logger.error(error_msg)
                raise GeminiError(error_msg)
            
            elif response.status_code == 429:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + 1  # Exponential backoff
                    logger.warning(f"Rate limit hit, waiting {wait_time}s before retry")
                    time.sleep(wait_time)
                    continue
                else:
                    error_msg = "Limite de taxa excedido. Tente novamente mais tarde."
                    logger.error(error_msg)
                    raise GeminiError(error_msg)
            
            elif response.status_code >= 500:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + 1
                    logger.warning(f"Server error {response.status_code}, retrying in {wait_time}s")
                    time.sleep(wait_time)
                    continue
                else:
                    error_msg = f"Erro interno do servidor Gemini: {response.status_code}"
                    logger.error(error_msg)
                    raise GeminiError(error_msg)
            
            else:
                error_msg = f"Erro HTTP inesperado: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise GeminiError(error_msg)
                
        except requests.RequestException as e:
            last_error = e
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + 1
                logger.warning(f"Network error, retrying in {wait_time}s: {e}")
                time.sleep(wait_time)
                continue
            else:
                error_msg = f"Erro de conexão com Gemini após {max_retries} tentativas: {e}"
                logger.error(error_msg)
                raise GeminiError(error_msg)
        
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + 1
                logger.warning(f"Unexpected error, retrying in {wait_time}s: {e}")
                time.sleep(wait_time)
                continue
            else:
                error_msg = f"Erro inesperado após {max_retries} tentativas: {e}"
                logger.error(error_msg)
                raise GeminiError(error_msg)
    
    # If we get here, all retries failed
    raise GeminiError(f"Falha ao conectar com Gemini após {max_retries} tentativas. Último erro: {last_error}")

def gemini_ask_with_context(prompt: str, context: str = "", max_retries: int = 3) -> str:
    """
    Ask Gemini with additional context
    """
    if context:
        full_prompt = f"Contexto: {context}\n\nPergunta: {prompt}"
    else:
        full_prompt = prompt
    
    return gemini_ask(full_prompt, max_retries)

def test_gemini_connection() -> Dict[str, Any]:
    """
    Test Gemini API connection and return status
    """
    if not GEMINI_API_KEY:
        return {
            "status": "error",
            "message": "API key not configured"
        }
    
    try:
        response = gemini_ask("Olá! Este é um teste de conexão.", max_retries=1)
        return {
            "status": "success",
            "message": "Connection successful",
            "response": response[:100] + "..." if len(response) > 100 else response
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics
    """
    current_time = time.time()
    active_entries = sum(1 for _, (_, timestamp) in response_cache.items() 
                        if current_time - timestamp <= CACHE_TIMEOUT)
    
    return {
        "total_entries": len(response_cache),
        "active_entries": active_entries,
        "cache_timeout": CACHE_TIMEOUT,
        "oldest_entry": min(response_cache.values(), key=lambda x: x[1])[1] if response_cache else None
    }

if __name__ == "__main__":
    # Test the Gemini integration
    print("Testing Gemini connection...")
    result = test_gemini_connection()
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")
    
    if result['status'] == 'success':
        print(f"Response preview: {result.get('response', 'N/A')}")
        
        # Test caching
        print("\nTesting response caching...")
        start_time = time.time()
        response1 = gemini_ask("Qual é a capital do Brasil?")
        time1 = time.time() - start_time
        
        start_time = time.time()
        response2 = gemini_ask("Qual é a capital do Brasil?")
        time2 = time.time() - start_time
        
        print(f"First request: {time1:.2f}s")
        print(f"Second request (cached): {time2:.2f}s")
        print(f"Cache stats: {get_cache_stats()}")