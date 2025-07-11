"""
AUTOBOT - Advanced Bitrix24 Integration Bot with AI
Enhanced main module with optimized error handling and metrics
"""
import os
import sys
import time
import logging
import traceback
from typing import Dict, Any, Optional, List
from datetime import datetime
import requests
from dotenv import load_dotenv

# Add project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from IA.treinamento.salvar_interacao import salvar_interacao
    from metrics.metrics_collector import collect_metrics, log_operation
except ImportError:
    def salvar_interacao(prompt: str, resposta: str) -> None:
        """Fallback function for interaction saving"""
        pass
    
    def collect_metrics(operation: str, duration: float, success: bool) -> None:
        """Fallback function for metrics collection"""
        pass
    
    def log_operation(operation: str) -> None:
        """Fallback function for operation logging"""
        pass

# Load environment variables
load_dotenv()

# Configuration with fallbacks
BITRIX_WEBHOOK_URL = os.getenv("BITRIX_WEBHOOK_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "localhost")
OLLAMA_PORT = os.getenv("OLLAMA_PORT", "11434")
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

# Setup logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('autobot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutobotError(Exception):
    """Custom exception for Autobot operations"""
    pass

class HealthChecker:
    """Advanced health check system"""
    
    @staticmethod
    def check_dependencies() -> Dict[str, bool]:
        """Check if all required dependencies are available"""
        checks = {}
        
        # Check Bitrix24 connection
        if BITRIX_WEBHOOK_URL:
            try:
                response = requests.get(f"{BITRIX_WEBHOOK_URL}profile", timeout=5)
                checks["bitrix24"] = response.status_code == 200
            except Exception:
                checks["bitrix24"] = False
        else:
            checks["bitrix24"] = False
        
        # Check Ollama connection
        try:
            response = requests.get(f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/tags", timeout=5)
            checks["ollama"] = response.status_code == 200
        except Exception:
            checks["ollama"] = False
        
        # Check Gemini API
        if GEMINI_API_KEY:
            checks["gemini"] = True  # Basic check - API key exists
        else:
            checks["gemini"] = False
        
        return checks
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """Get system information"""
        try:
            import psutil
            return {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "uptime": time.time() - psutil.boot_time()
            }
        except ImportError:
            return {"status": "psutil not available"}

def validate_configuration() -> bool:
    """Validate essential configuration"""
    if not BITRIX_WEBHOOK_URL:
        logger.error("BITRIX_WEBHOOK_URL not configured in .env file")
        return False
    
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not configured - AI features may be limited")
    
    return True

def enhanced_error_handler(func):
    """Decorator for enhanced error handling"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        operation_name = func.__name__
        log_operation(operation_name)
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            collect_metrics(operation_name, duration, True)
            logger.info(f"Operation {operation_name} completed successfully in {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            collect_metrics(operation_name, duration, False)
            logger.error(f"Operation {operation_name} failed after {duration:.2f}s: {str(e)}")
            logger.debug(traceback.format_exc())
            raise AutobotError(f"Failed to execute {operation_name}: {str(e)}")
    
    return wrapper

@enhanced_error_handler
def listar_tarefas_pendentes() -> List[Dict[str, Any]]:
    """List pending tasks with enhanced error handling and caching"""
    if not BITRIX_WEBHOOK_URL:
        raise AutobotError("Bitrix24 webhook URL not configured")
    
    url = f"{BITRIX_WEBHOOK_URL}tasks.task.list"
    params = {
        "filter": {"REAL_STATUS": [2, 3]},  # New and In Progress
        "select": ["ID", "TITLE", "RESPONSIBLE_ID", "STATUS", "DEADLINE", "DESCRIPTION"]
    }
    
    try:
        response = requests.post(url, json=params, timeout=10)
        response.raise_for_status()
        
        result = response.json().get('result', {})
        tasks = result.get('tasks', [])
        
        if not tasks:
            message = "Nenhuma tarefa pendente encontrada."
            logger.info(message)
            salvar_interacao("listar tarefas pendentes", message)
            return []
        
        # Format tasks with enhanced information
        formatted_tasks = []
        for task in tasks:
            formatted_task = {
                "id": task.get('ID'),
                "title": task.get('TITLE', 'Sem título'),
                "status": task.get('STATUS', 'Desconhecido'),
                "deadline": task.get('DEADLINE', 'Sem prazo'),
                "responsible": task.get('RESPONSIBLE_ID', 'Não atribuído'),
                "description": task.get('DESCRIPTION', '')[:100] + '...' if task.get('DESCRIPTION', '') else ''
            }
            formatted_tasks.append(formatted_task)
        
        response_message = f"Encontradas {len(formatted_tasks)} tarefas pendentes"
        logger.info(response_message)
        salvar_interacao("listar tarefas pendentes", response_message)
        
        return formatted_tasks
        
    except requests.RequestException as e:
        error_msg = f"Erro de conexão com Bitrix24: {str(e)}"
        logger.error(error_msg)
        raise AutobotError(error_msg)
    except Exception as e:
        error_msg = f"Erro inesperado ao listar tarefas: {str(e)}"
        logger.error(error_msg)
        raise AutobotError(error_msg)

@enhanced_error_handler
def responder_tarefa(task_id: str, mensagem: str) -> bool:
    """Respond to a task with enhanced validation and error handling"""
    if not BITRIX_WEBHOOK_URL:
        raise AutobotError("Bitrix24 webhook URL not configured")
    
    if not task_id or not mensagem:
        raise AutobotError("Task ID and message are required")
    
    url = f"{BITRIX_WEBHOOK_URL}task.commentitem.add"
    params = {
        "task_id": task_id,
        "fields": {
            "POST_MESSAGE": mensagem,
            "AUTHOR_ID": os.getenv("BITRIX_USER_ID", "1")  # Default to admin user
        }
    }
    
    try:
        response = requests.post(url, json=params, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        if result.get('result'):
            success_msg = f"Comentário enviado com sucesso para tarefa {task_id}"
            logger.info(success_msg)
            salvar_interacao(f"responder tarefa {task_id}: {mensagem}", success_msg)
            return True
        else:
            error_msg = f"Falha ao enviar comentário: {result.get('error', 'Erro desconhecido')}"
            logger.error(error_msg)
            raise AutobotError(error_msg)
            
    except requests.RequestException as e:
        error_msg = f"Erro de conexão ao responder tarefa {task_id}: {str(e)}"
        logger.error(error_msg)
        raise AutobotError(error_msg)
    except Exception as e:
        error_msg = f"Erro inesperado ao responder tarefa {task_id}: {str(e)}"
        logger.error(error_msg)
        raise AutobotError(error_msg)

def create_task(title: str, description: str = "", responsible_id: str = None) -> Dict[str, Any]:
    """Create a new task in Bitrix24"""
    if not BITRIX_WEBHOOK_URL:
        raise AutobotError("Bitrix24 webhook URL not configured")
    
    url = f"{BITRIX_WEBHOOK_URL}tasks.task.add"
    params = {
        "fields": {
            "TITLE": title,
            "DESCRIPTION": description,
            "RESPONSIBLE_ID": responsible_id or os.getenv("BITRIX_USER_ID", "1"),
            "CREATED_BY": os.getenv("BITRIX_USER_ID", "1")
        }
    }
    
    try:
        response = requests.post(url, json=params, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        if result.get('result'):
            task_id = result['result']['task']['id']
            success_msg = f"Tarefa criada com sucesso. ID: {task_id}"
            logger.info(success_msg)
            return {"success": True, "task_id": task_id, "message": success_msg}
        else:
            error_msg = f"Falha ao criar tarefa: {result.get('error', 'Erro desconhecido')}"
            raise AutobotError(error_msg)
            
    except Exception as e:
        error_msg = f"Erro ao criar tarefa: {str(e)}"
        logger.error(error_msg)
        raise AutobotError(error_msg)

def main():
    """Enhanced main function with better command handling"""
    if not validate_configuration():
        sys.exit(1)
    
    logger.info("Starting AUTOBOT with enhanced features...")
    
    # Perform health checks
    health_status = HealthChecker.check_dependencies()
    logger.info(f"Health check results: {health_status}")
    
    if len(sys.argv) < 2:
        print("""
AUTOBOT - Commands available:
  listar                     - List pending tasks
  responder <id> <message>   - Respond to a task
  criar <title> [description] - Create a new task
  health                     - Show system health
  treinar                    - Train AI model
        """)
        return
    
    cmd = sys.argv[1].lower()
    
    try:
        if cmd == "listar":
            tasks = listar_tarefas_pendentes()
            for task in tasks:
                print(f"ID: {task['id']} | {task['title']} | Status: {task['status']} | Prazo: {task['deadline']}")
        
        elif cmd == "responder" and len(sys.argv) >= 4:
            task_id = sys.argv[2]
            message = " ".join(sys.argv[3:])
            responder_tarefa(task_id, message)
        
        elif cmd == "criar" and len(sys.argv) >= 3:
            title = sys.argv[2]
            description = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
            result = create_task(title, description)
            print(result['message'])
        
        elif cmd == "health":
            health = HealthChecker.check_dependencies()
            system_info = HealthChecker.get_system_info()
            print("=== Health Check ===")
            for service, status in health.items():
                print(f"{service}: {'✓ OK' if status else '✗ FAIL'}")
            print(f"\n=== System Info ===")
            for key, value in system_info.items():
                print(f"{key}: {value}")
        
        elif cmd == "treinar":
            logger.info("Starting AI model training...")
            os.system("python IA/treinamento/finetune_llm.py")
        
        else:
            print("Comando inválido. Use 'python -m autobot.main' sem argumentos para ver a ajuda.")
    
    except AutobotError as e:
        logger.error(f"Autobot error: {e}")
        print(f"Erro: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"Erro inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()