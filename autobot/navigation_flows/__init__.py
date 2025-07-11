"""
AUTOBOT Navigation Flows - Fluxos de automação
"""

import time
import json
from datetime import datetime
from typing import Dict, Any, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class BaseFlow:
    """Classe base para fluxos de automação"""
    
    def __init__(self, name: str):
        self.name = name
        self.steps = []
        self.start_time = None
        self.end_time = None
        
    def add_step(self, action: str, target: str, value: str = "", timeout: int = 10):
        """Adiciona um passo ao fluxo"""
        step = {
            "action": action,
            "target": target,
            "value": value,
            "timeout": timeout,
            "timestamp": None,
            "status": "pending"
        }
        self.steps.append(step)
        
    def execute(self) -> Dict[str, Any]:
        """Executa o fluxo completo"""
        self.start_time = datetime.now()
        results = {
            "flow_name": self.name,
            "start_time": self.start_time.isoformat(),
            "steps_executed": 0,
            "steps_successful": 0,
            "steps_failed": 0,
            "errors": []
        }
        
        driver = None
        try:
            # Configura Chrome em modo headless
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            driver = webdriver.Chrome(options=chrome_options)
            
            for i, step in enumerate(self.steps):
                step["timestamp"] = datetime.now().isoformat()
                results["steps_executed"] += 1
                
                try:
                    self._execute_step(driver, step)
                    step["status"] = "success"
                    results["steps_successful"] += 1
                except Exception as e:
                    step["status"] = "failed"
                    step["error"] = str(e)
                    results["steps_failed"] += 1
                    results["errors"].append(f"Step {i+1}: {str(e)}")
                    
        except Exception as e:
            results["errors"].append(f"Driver initialization failed: {str(e)}")
            
        finally:
            if driver:
                driver.quit()
                
        self.end_time = datetime.now()
        results["end_time"] = self.end_time.isoformat()
        results["total_duration"] = (self.end_time - self.start_time).total_seconds()
        results["success_rate"] = (results["steps_successful"] / results["steps_executed"] * 100) if results["steps_executed"] > 0 else 0
        
        return results
    
    def _execute_step(self, driver, step):
        """Executa um passo individual"""
        action = step["action"]
        target = step["target"]
        value = step["value"]
        timeout = step["timeout"]
        
        wait = WebDriverWait(driver, timeout)
        
        if action == "navigate":
            driver.get(target)
            
        elif action == "click":
            element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, target)))
            element.click()
            
        elif action == "type":
            element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, target)))
            element.clear()
            element.send_keys(value)
            
        elif action == "wait":
            time.sleep(float(target))
            
        elif action == "wait_for_element":
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, target)))
            
        elif action == "screenshot":
            driver.save_screenshot(target)
            
        else:
            raise ValueError(f"Ação não suportada: {action}")

class GoogleSearchFlow(BaseFlow):
    """Fluxo para busca no Google"""
    
    def __init__(self, query: str):
        super().__init__(f"Google Search: {query}")
        self.add_step("navigate", "https://www.google.com")
        self.add_step("type", "input[name='q']", query)
        self.add_step("click", "input[name='btnK']")
        self.add_step("wait_for_element", "#search")

class LoginFlow(BaseFlow):
    """Fluxo genérico de login"""
    
    def __init__(self, url: str, username: str, password: str, 
                 username_selector: str = "input[name='username']",
                 password_selector: str = "input[name='password']",
                 submit_selector: str = "input[type='submit']"):
        super().__init__(f"Login Flow: {url}")
        self.add_step("navigate", url)
        self.add_step("type", username_selector, username)
        self.add_step("type", password_selector, password)
        self.add_step("click", submit_selector)
        self.add_step("wait", "3")  # Aguarda carregamento

class FormFillFlow(BaseFlow):
    """Fluxo para preenchimento de formulários"""
    
    def __init__(self, url: str, form_data: Dict[str, str]):
        super().__init__(f"Form Fill: {url}")
        self.add_step("navigate", url)
        
        for selector, value in form_data.items():
            self.add_step("type", selector, value)

# Factory para criar fluxos
def create_flow(flow_type: str, **kwargs) -> BaseFlow:
    """Cria um fluxo específico"""
    flows = {
        "google_search": lambda: GoogleSearchFlow(kwargs.get("query", "")),
        "login": lambda: LoginFlow(
            kwargs.get("url", ""),
            kwargs.get("username", ""),
            kwargs.get("password", ""),
            kwargs.get("username_selector", "input[name='username']"),
            kwargs.get("password_selector", "input[name='password']"),
            kwargs.get("submit_selector", "input[type='submit']")
        ),
        "form_fill": lambda: FormFillFlow(
            kwargs.get("url", ""),
            kwargs.get("form_data", {})
        )
    }
    
    if flow_type in flows:
        return flows[flow_type]()
    else:
        raise ValueError(f"Fluxo '{flow_type}' não suportado")

# Gerenciador de fluxos
class FlowManager:
    """Gerencia execução de múltiplos fluxos"""
    
    def __init__(self):
        self.flows = []
        self.results = []
    
    def add_flow(self, flow: BaseFlow):
        """Adiciona um fluxo à lista"""
        self.flows.append(flow)
    
    def execute_all(self) -> List[Dict[str, Any]]:
        """Executa todos os fluxos"""
        self.results = []
        
        for flow in self.flows:
            result = flow.execute()
            self.results.append(result)
            
        return self.results
    
    def get_summary(self) -> Dict[str, Any]:
        """Retorna resumo da execução"""
        if not self.results:
            return {"message": "Nenhum fluxo executado"}
        
        total_flows = len(self.results)
        successful_flows = sum(1 for r in self.results if r["steps_failed"] == 0)
        total_steps = sum(r["steps_executed"] for r in self.results)
        successful_steps = sum(r["steps_successful"] for r in self.results)
        
        return {
            "total_flows": total_flows,
            "successful_flows": successful_flows,
            "flow_success_rate": (successful_flows / total_flows * 100) if total_flows > 0 else 0,
            "total_steps": total_steps,
            "successful_steps": successful_steps,
            "step_success_rate": (successful_steps / total_steps * 100) if total_steps > 0 else 0,
            "results": self.results
        }