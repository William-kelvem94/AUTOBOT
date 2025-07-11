#!/usr/bin/env python3
"""
Script para configurar sistema de IA local completo do AUTOBOT
Automatiza a instalação e configuração de Ollama, ChromaDB e dependências
"""

import subprocess
import sys
import os
import platform
import urllib.request
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Any

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('setup_ia.log')
    ]
)
logger = logging.getLogger(__name__)

class AutobotIASetup:
    """Classe para configuração completa do sistema de IA local"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.architecture = platform.machine().lower()
        self.python_executable = sys.executable
        logger.info(f"Sistema: {self.system}, Arquitetura: {self.architecture}")
    
    def create_directories(self) -> bool:
        """Cria estrutura de diretórios necessária"""
        logger.info("📁 Criando estrutura de diretórios...")
        
        dirs = [
            "IA/memoria_vetorial",
            "IA/memoria_conversas", 
            "IA/modelos_personalizados",
            "IA/datasets",
            "IA/logs",
            "IA/config",
            "IA/backup"
        ]
        
        try:
            for dir_path in dirs:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
                logger.info(f"✅ Criado: {dir_path}")
            
            # Cria arquivo de configuração inicial
            config_file = Path("IA/config/config.json")
            if not config_file.exists():
                config = {
                    "ollama_host": "http://localhost:11434",
                    "chroma_persist_directory": "IA/memoria_vetorial",
                    "memory_persist_directory": "IA/memoria_conversas",
                    "default_model": "llama3",
                    "backup_enabled": True,
                    "max_memory_days": 30
                }
                
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=2)
                logger.info("✅ Arquivo de configuração criado")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar diretórios: {e}")
            return False
    
    def install_python_dependencies(self) -> bool:
        """Instala dependências Python específicas de IA"""
        logger.info("🐍 Instalando dependências Python...")
        
        ia_packages = [
            "chromadb==0.4.22",
            "sentence-transformers==2.2.2", 
            "ollama==0.1.7",
            "numpy>=1.21.0",
            "scipy>=1.7.0",
            "scikit-learn>=1.0.0",
            "torch>=1.9.0",
            "transformers>=4.21.0",
            "datasets>=2.0.0",
            "accelerate>=0.16.0"
        ]
        
        success_count = 0
        for package in ia_packages:
            try:
                logger.info(f"📦 Instalando {package}...")
                result = subprocess.run([
                    self.python_executable, "-m", "pip", "install", 
                    package, "--upgrade", "--quiet"
                ], check=True, capture_output=True, text=True)
                
                logger.info(f"✅ {package} instalado com sucesso")
                success_count += 1
                
            except subprocess.CalledProcessError as e:
                logger.error(f"⚠️ Falha ao instalar {package}: {e}")
                logger.error(f"Stderr: {e.stderr}")
        
        logger.info(f"📊 Instaladas {success_count}/{len(ia_packages)} dependências")
        return success_count >= len(ia_packages) * 0.8  # 80% de sucesso considerado OK
    
    def install_ollama(self) -> bool:
        """Instala Ollama baseado no sistema operacional"""
        logger.info("🦙 Instalando Ollama...")
        
        try:
            # Verifica se Ollama já está instalado
            result = subprocess.run(["ollama", "--version"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("✅ Ollama já está instalado")
                return True
        except FileNotFoundError:
            pass
        
        # Instalação baseada no sistema
        if self.system == "linux":
            return self._install_ollama_linux()
        elif self.system == "darwin":  # macOS
            return self._install_ollama_macos()
        elif self.system == "windows":
            return self._install_ollama_windows()
        else:
            logger.error(f"❌ Sistema {self.system} não suportado para instalação automática")
            return False
    
    def _install_ollama_linux(self) -> bool:
        """Instala Ollama no Linux"""
        try:
            logger.info("📥 Baixando script de instalação do Ollama para Linux...")
            
            # Baixa e executa script oficial
            install_command = "curl -fsSL https://ollama.ai/install.sh | sh"
            result = subprocess.run(install_command, shell=True, check=True)
            
            logger.info("✅ Ollama instalado no Linux")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro na instalação do Ollama no Linux: {e}")
            return False
    
    def _install_ollama_macos(self) -> bool:
        """Instala Ollama no macOS"""
        try:
            logger.info("📥 Instalando Ollama no macOS...")
            
            # Tenta instalar via Homebrew primeiro
            try:
                subprocess.run(["brew", "install", "ollama"], check=True)
                logger.info("✅ Ollama instalado via Homebrew")
                return True
            except:
                logger.info("⚠️ Homebrew não disponível, usando instalador direto...")
            
            # Fallback para instalador direto
            install_command = "curl -fsSL https://ollama.ai/install.sh | sh"
            subprocess.run(install_command, shell=True, check=True)
            
            logger.info("✅ Ollama instalado no macOS")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro na instalação do Ollama no macOS: {e}")
            return False
    
    def _install_ollama_windows(self) -> bool:
        """Instala Ollama no Windows"""
        logger.warning("⚠️ Para Windows, baixe o instalador em: https://ollama.ai/download")
        logger.info("ℹ️ Após instalar, reinicie o terminal e execute este script novamente")
        return False
    
    def start_ollama_service(self) -> bool:
        """Inicia o serviço Ollama"""
        logger.info("🚀 Iniciando serviço Ollama...")
        
        try:
            # Verifica se já está rodando
            result = subprocess.run(["ollama", "list"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("✅ Serviço Ollama já está rodando")
                return True
        except:
            pass
        
        try:
            # Inicia o serviço em background
            if self.system == "windows":
                subprocess.Popen(["ollama", "serve"], 
                               creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen(["ollama", "serve"], 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL)
            
            # Aguarda alguns segundos para o serviço iniciar
            logger.info("⏳ Aguardando serviço inicializar...")
            time.sleep(5)
            
            # Verifica se está funcionando
            result = subprocess.run(["ollama", "list"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("✅ Serviço Ollama iniciado com sucesso")
                return True
            else:
                logger.error("❌ Falha ao verificar serviço Ollama")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar serviço Ollama: {e}")
            return False
    
    def setup_ollama_models(self) -> Dict[str, str]:
        """Configura modelos Ollama essenciais"""
        logger.info("📚 Configurando modelos Ollama...")
        
        models = {
            'tinyllama': 'Modelo pequeno e rápido (637MB)',
            'llama3': 'Modelo principal recomendado (4.7GB)', 
            'mistral': 'Modelo alternativo de qualidade (4.1GB)'
        }
        
        status = {}
        
        for model, description in models.items():
            try:
                logger.info(f"📥 Baixando {model} - {description}")
                
                # Timeout maior para downloads grandes
                result = subprocess.run(
                    ["ollama", "pull", model], 
                    timeout=1800,  # 30 minutos
                    capture_output=True, 
                    text=True
                )
                
                if result.returncode == 0:
                    status[model] = "✅ Instalado com sucesso"
                    logger.info(f"✅ Modelo {model} instalado")
                else:
                    status[model] = f"⚠️ Erro: {result.stderr}"
                    logger.error(f"⚠️ Erro ao instalar {model}: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                status[model] = "⚠️ Timeout no download"
                logger.error(f"⚠️ Timeout ao baixar {model}")
            except Exception as e:
                status[model] = f"⚠️ Erro: {str(e)}"
                logger.error(f"⚠️ Erro ao instalar {model}: {e}")
        
        return status
    
    def test_installation(self) -> bool:
        """Testa a instalação completa do sistema"""
        logger.info("🧪 Testando instalação completa...")
        
        try:
            # Testa importação das dependências
            logger.info("🔍 Testando importações Python...")
            
            import chromadb
            import sentence_transformers
            import ollama
            
            logger.info("✅ Todas as dependências Python importadas")
            
            # Testa conexão com Ollama
            logger.info("🔍 Testando conexão com Ollama...")
            
            client = ollama.Client()
            models = client.list()
            
            logger.info(f"✅ Ollama conectado - {len(models.get('models', []))} modelos disponíveis")
            
            # Testa ChromaDB
            logger.info("🔍 Testando ChromaDB...")
            
            chroma_client = chromadb.PersistentClient(path="IA/memoria_vetorial")
            collection = chroma_client.get_or_create_collection("test")
            
            logger.info("✅ ChromaDB funcionando")
            
            # Testa sentence transformers
            logger.info("🔍 Testando Sentence Transformers...")
            
            encoder = sentence_transformers.SentenceTransformer('all-MiniLM-L6-v2')
            test_embedding = encoder.encode("teste")
            
            logger.info("✅ Sentence Transformers funcionando")
            
            logger.info("🎉 Instalação completa testada com sucesso!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro no teste de instalação: {e}")
            return False
    
    def create_startup_script(self) -> bool:
        """Cria script de inicialização do sistema"""
        logger.info("📜 Criando script de inicialização...")
        
        try:
            if self.system == "windows":
                script_content = """@echo off
echo Iniciando AUTOBOT IA Local...
ollama serve
"""
                script_path = "IA/start_autobot_ia.bat"
            else:
                script_content = """#!/bin/bash
echo "Iniciando AUTOBOT IA Local..."

# Inicia Ollama se não estiver rodando
if ! pgrep -f "ollama serve" > /dev/null; then
    echo "Iniciando Ollama..."
    ollama serve &
    sleep 3
fi

echo "✅ Sistema AUTOBOT IA pronto!"
echo "🌐 Ollama disponível em: http://localhost:11434"
echo "💾 ChromaDB persistindo em: IA/memoria_vetorial"
"""
                script_path = "IA/start_autobot_ia.sh"
            
            with open(script_path, 'w') as f:
                f.write(script_content)
            
            # Torna executável no Unix
            if self.system != "windows":
                os.chmod(script_path, 0o755)
            
            logger.info(f"✅ Script criado: {script_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar script: {e}")
            return False
    
    def run_full_setup(self) -> bool:
        """Executa configuração completa do sistema"""
        logger.info("🚀 INICIANDO CONFIGURAÇÃO COMPLETA DO AUTOBOT IA")
        logger.info("=" * 60)
        
        steps = [
            ("Criando diretórios", self.create_directories),
            ("Instalando dependências Python", self.install_python_dependencies),
            ("Instalando Ollama", self.install_ollama),
            ("Iniciando serviço Ollama", self.start_ollama_service),
            ("Configurando modelos", self.setup_ollama_models),
            ("Testando instalação", self.test_installation),
            ("Criando script de inicialização", self.create_startup_script)
        ]
        
        results = {}
        
        for step_name, step_function in steps:
            logger.info(f"\n🔄 {step_name}...")
            try:
                result = step_function()
                results[step_name] = result
                
                if result:
                    logger.info(f"✅ {step_name} - SUCESSO")
                else:
                    logger.error(f"❌ {step_name} - FALHOU")
                    
            except Exception as e:
                logger.error(f"❌ {step_name} - ERRO: {e}")
                results[step_name] = False
        
        # Relatório final
        logger.info("\n" + "=" * 60)
        logger.info("📊 RELATÓRIO FINAL DA CONFIGURAÇÃO")
        logger.info("=" * 60)
        
        success_count = sum(1 for result in results.values() if result)
        total_steps = len(results)
        
        for step, result in results.items():
            status = "✅ SUCESSO" if result else "❌ FALHOU"
            logger.info(f"{step}: {status}")
        
        logger.info(f"\n📈 Taxa de sucesso: {success_count}/{total_steps} ({success_count/total_steps*100:.1f}%)")
        
        if success_count >= total_steps * 0.8:  # 80% de sucesso
            logger.info("🎉 CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!")
            logger.info("\n🚀 Para iniciar o sistema:")
            logger.info("   Linux/macOS: ./IA/start_autobot_ia.sh")
            logger.info("   Windows: IA\\start_autobot_ia.bat")
            return True
        else:
            logger.error("⚠️ CONFIGURAÇÃO PARCIALMENTE FALHOU")
            logger.error("Verifique os logs e tente executar os passos que falharam manualmente")
            return False

def main():
    """Função principal"""
    print("🧠 AUTOBOT - Configuração do Sistema de IA Local")
    print("=" * 60)
    print("Este script irá configurar:")
    print("• Dependências Python para IA")
    print("• Ollama (modelos de linguagem local)")
    print("• ChromaDB (base de dados vetorial)")
    print("• Estrutura de diretórios")
    print("• Scripts de inicialização")
    print("=" * 60)
    
    # Confirmação do usuário
    try:
        resposta = input("\nContinuar com a configuração? (s/n): ").lower()
        if resposta not in ['s', 'sim', 'y', 'yes']:
            print("❌ Configuração cancelada pelo usuário")
            return
    except KeyboardInterrupt:
        print("\n❌ Configuração interrompida")
        return
    
    # Executa configuração
    setup = AutobotIASetup()
    success = setup.run_full_setup()
    
    if success:
        print("\n🎉 Configuração concluída com sucesso!")
        print("Execute 'python IA/treinamento/local_trainer.py' para testar")
    else:
        print("\n⚠️ Configuração teve alguns problemas")
        print("Verifique o arquivo 'setup_ia.log' para detalhes")
    
    return success

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Configuração interrompida pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro fatal na configuração: {e}")
        print(f"❌ Erro fatal: {e}")
        print("Verifique o arquivo 'setup_ia.log' para detalhes completos")