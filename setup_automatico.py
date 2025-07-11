#!/usr/bin/env python3
"""
Setup Automático AUTOBOT - Versão Melhorada
Instala dependências, configura banco e valida sistema
"""

import subprocess
import sys
import sqlite3
import os
from pathlib import Path

def install_dependencies():
    """Instala dependências com fallbacks"""
    print("📦 Instalando dependências Python...")
    
    essential_packages = [
        "flask==3.0.0",
        "flask-cors==4.0.0", 
        "requests==2.31.0",
        "python-dotenv==1.0.0",
        "beautifulsoup4==4.12.3",
        "pandas==2.2.0",
        "numpy==1.26.3"
    ]
    
    # Primeiro tenta instalar do requirements.txt
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependências instaladas via requirements.txt")
        return
    except:
        print("⚠️ Falha ao instalar via requirements.txt, tentando pacotes essenciais...")
    
    # Fallback para pacotes essenciais
    for package in essential_packages:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)
            print(f"✅ {package} instalado")
        except:
            print(f"⚠️ Falha ao instalar {package}")

def create_metrics_database():
    """Cria banco de métricas automaticamente"""
    print("🗄️ Configurando banco de métricas...")
    
    db_path = Path("metrics/autobot_metrics.db")
    db_path.parent.mkdir(exist_ok=True)
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Tabelas de métricas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_metrics (
                id INTEGER PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                endpoint TEXT,
                response_time REAL,
                status_code INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                cpu_usage REAL,
                memory_usage REAL,
                disk_usage REAL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_metrics (
                id INTEGER PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                task_name TEXT,
                execution_time REAL,
                success BOOLEAN,
                error_message TEXT
            )
        ''')
        
        conn.commit()
    print("✅ Banco de métricas criado com tabelas: api_metrics, system_metrics, task_metrics")

def create_env_file():
    """Cria arquivo .env com configurações padrão"""
    print("⚙️ Criando arquivo de configuração...")
    
    env_content = """# AUTOBOT Configuration
DEBUG=True
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=sqlite:///metrics/autobot_metrics.db

# API Configuration
API_PORT=5000
WEB_PORT=5173

# IA Configuration
OLLAMA_URL=http://localhost:11434
AI_MODEL=llama2

# Bitrix24 Integration
BITRIX24_WEBHOOK_URL=
BITRIX24_API_KEY=

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/autobot.log
"""
    
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write(env_content)
        print("✅ Arquivo .env criado")
    else:
        print("⚠️ Arquivo .env já existe, mantendo configurações atuais")

def create_directory_structure():
    """Cria estrutura de diretórios necessária"""
    print("📁 Criando estrutura de diretórios...")
    
    directories = [
        "autobot/api_drivers",
        "autobot/navigation_flows", 
        "autobot/recorded_tasks",
        "backups",
        "IA/treinamento",
        "src",
        "web/src",
        "web/public",
        "metrics",
        "logs",
        "tests"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        
    print("✅ Estrutura de diretórios criada")

def validate_installation():
    """Valida se a instalação foi bem-sucedida"""
    print("🔍 Validando instalação...")
    
    checks = {
        "Flask": False,
        "Requests": False,
        "Pandas": False,
        "Database": False,
        "Env File": False
    }
    
    # Verifica imports Python
    try:
        import flask
        checks["Flask"] = True
    except ImportError:
        pass
    
    try:
        import requests
        checks["Requests"] = True
    except ImportError:
        pass
        
    try:
        import pandas
        checks["Pandas"] = True
    except ImportError:
        pass
    
    # Verifica banco de dados
    if Path("metrics/autobot_metrics.db").exists():
        checks["Database"] = True
    
    # Verifica arquivo .env
    if Path(".env").exists():
        checks["Env File"] = True
    
    # Relatório de validação
    print("\n📊 Relatório de Validação:")
    for component, status in checks.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {component}")
    
    success_rate = sum(checks.values()) / len(checks) * 100
    print(f"\n🎯 Taxa de Sucesso: {success_rate:.1f}%")
    
    return success_rate >= 80

if __name__ == "__main__":
    print("🤖 AUTOBOT - Setup Automático")
    print("=" * 40)
    
    try:
        create_directory_structure()
        install_dependencies()
        create_metrics_database()
        create_env_file()
        
        if validate_installation():
            print("\n🚀 Setup concluído com sucesso!")
            print("Para iniciar o AUTOBOT:")
            print("  Windows: start_autobot.bat")
            print("  Linux/Mac: ./start_autobot.sh")
        else:
            print("\n⚠️ Setup concluído com alguns problemas")
            print("Verifique as dependências manualmente")
            
    except Exception as e:
        print(f"\n❌ Erro durante o setup: {e}")
        sys.exit(1)