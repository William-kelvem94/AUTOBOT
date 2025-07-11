#!/usr/bin/env python3
"""
AUTOBOT - Script de inicialização principal
Configura e inicia todo o sistema de IA local
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Adiciona paths necessários
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir / "IA"))

def setup_logging():
    """Configura logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger('autobot_main')

def check_dependencies():
    """Verifica dependências básicas"""
    logger = logging.getLogger('autobot_deps')
    
    required_packages = [
        'flask', 'flask_cors', 'requests', 'pyyaml', 'psutil'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            logger.info(f"✅ {package} disponível")
        except ImportError:
            missing_packages.append(package)
            logger.warning(f"⚠️ {package} não encontrado")
    
    if missing_packages:
        logger.info("📦 Instalando dependências faltantes...")
        try:
            subprocess.run([
                sys.executable, '-m', 'pip', 'install'
            ] + missing_packages, check=True)
            logger.info("✅ Dependências instaladas")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Erro ao instalar dependências: {e}")
            return False
    
    return True

def setup_ai_system():
    """Configura sistema de IA"""
    logger = logging.getLogger('autobot_ai')
    
    try:
        # Importa e executa setup
        from IA.setup_completo import AutobotSetupManager
        
        setup_manager = AutobotSetupManager()
        logger.info("🚀 Iniciando configuração do sistema de IA...")
        
        # Executa setup básico (sem modelos pesados para desenvolvimento)
        setup_manager._create_directory_structure()
        setup_manager._setup_databases()
        
        logger.info("✅ Sistema de IA configurado")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao configurar IA: {e}")
        return False

def start_flask_app():
    """Inicia aplicação Flask"""
    logger = logging.getLogger('autobot_flask')
    
    try:
        # Importa e inicia app
        from autobot.api import create_app
        
        app = create_app()
        
        # Configuração para desenvolvimento
        port = int(os.getenv('PORT', 5000))
        debug = os.getenv('DEBUG', 'True').lower() == 'true'
        
        logger.info("🚀 Iniciando AUTOBOT API...")
        logger.info(f"📡 Servidor: http://localhost:{port}")
        logger.info(f"🐛 Debug: {debug}")
        
        app.run(
            host='0.0.0.0',
            port=port,
            debug=debug
        )
        
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar Flask: {e}")
        return False

def main():
    """Função principal"""
    logger = setup_logging()
    
    logger.info("🤖 AUTOBOT - Sistema de Automação Corporativa com IA")
    logger.info("=" * 60)
    
    # Verifica dependências
    if not check_dependencies():
        logger.error("❌ Falha na verificação de dependências")
        return 1
    
    # Configura sistema de IA
    if not setup_ai_system():
        logger.warning("⚠️ Sistema de IA não disponível - continuando sem IA")
    
    # Inicia aplicação
    try:
        start_flask_app()
    except KeyboardInterrupt:
        logger.info("🛑 Sistema interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro crítico: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())