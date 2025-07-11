"""
AUTOBOT API Drivers - Integrações com APIs externas
"""

import requests
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

class BitrixAPI:
    """Driver para integração com Bitrix24"""
    
    def __init__(self):
        self.webhook_url = os.getenv('BITRIX24_WEBHOOK_URL')
        self.api_key = os.getenv('BITRIX24_API_KEY')
        
    def test_connection(self) -> Dict[str, Any]:
        """Testa conexão com Bitrix24"""
        if not self.webhook_url:
            return {"status": "error", "message": "Webhook URL não configurado"}
        
        try:
            response = requests.get(f"{self.webhook_url}/crm.lead.list", timeout=10)
            if response.status_code == 200:
                return {"status": "success", "message": "Conexão OK"}
            else:
                return {"status": "error", "message": f"Erro HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_leads(self, limit: int = 10) -> Dict[str, Any]:
        """Obtém leads do Bitrix24"""
        if not self.webhook_url:
            return {"error": "Webhook URL não configurado"}
        
        try:
            params = {"order": {"DATE_CREATE": "DESC"}, "filter": {}, "select": ["*"]}
            response = requests.post(
                f"{self.webhook_url}/crm.lead.list",
                json=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {"status": "success", "leads": data.get("result", [])}
            else:
                return {"status": "error", "message": f"Erro HTTP {response.status_code}"}
                
        except Exception as e:
            return {"status": "error", "message": str(e)}

class OllamaAPI:
    """Driver para integração com Ollama IA"""
    
    def __init__(self):
        self.base_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        
    def test_connection(self) -> Dict[str, Any]:
        """Testa conexão com Ollama"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return {
                    "status": "success", 
                    "message": f"Ollama OK - {len(models)} modelos disponíveis",
                    "models": models
                }
            else:
                return {"status": "error", "message": f"Erro HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def generate_text(self, prompt: str, model: str = "llama2") -> Dict[str, Any]:
        """Gera texto usando Ollama"""
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "success",
                    "response": data.get("response", ""),
                    "model": model,
                    "total_duration": data.get("total_duration", 0)
                }
            else:
                return {"status": "error", "message": f"Erro HTTP {response.status_code}"}
                
        except Exception as e:
            return {"status": "error", "message": str(e)}

class WebScrapingAPI:
    """Driver para web scraping"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AUTOBOT Web Scraper 1.0'
        })
    
    def scrape_url(self, url: str, selector: Optional[str] = None) -> Dict[str, Any]:
        """Faz scraping de uma URL"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            if selector:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.content, 'html.parser')
                elements = soup.select(selector)
                data = [elem.get_text(strip=True) for elem in elements]
            else:
                data = response.text
            
            return {
                "status": "success",
                "url": url,
                "data": data,
                "content_length": len(response.content),
                "status_code": response.status_code
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e), "url": url}

# Factory para criar drivers
def create_driver(driver_type: str):
    """Cria um driver específico"""
    drivers = {
        "bitrix": BitrixAPI,
        "ollama": OllamaAPI,
        "webscraping": WebScrapingAPI
    }
    
    if driver_type in drivers:
        return drivers[driver_type]()
    else:
        raise ValueError(f"Driver '{driver_type}' não suportado")

# Teste de todos os drivers
def test_all_drivers() -> Dict[str, Any]:
    """Testa todos os drivers disponíveis"""
    results = {}
    
    # Testa Bitrix
    try:
        bitrix = create_driver("bitrix")
        results["bitrix"] = bitrix.test_connection()
    except Exception as e:
        results["bitrix"] = {"status": "error", "message": str(e)}
    
    # Testa Ollama
    try:
        ollama = create_driver("ollama")
        results["ollama"] = ollama.test_connection()
    except Exception as e:
        results["ollama"] = {"status": "error", "message": str(e)}
    
    # Testa Web Scraping
    try:
        scraper = create_driver("webscraping")
        test_result = scraper.scrape_url("https://httpbin.org/get")
        results["webscraping"] = {
            "status": "success" if test_result["status"] == "success" else "error",
            "message": "Web scraping funcionando" if test_result["status"] == "success" else test_result.get("message")
        }
    except Exception as e:
        results["webscraping"] = {"status": "error", "message": str(e)}
    
    return results