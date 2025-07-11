#!/usr/bin/env python3
"""
Sistema de treinamento de IA local para AUTOBOT
Implementa integração com Ollama e ChromaDB para IA local completa
"""

import ollama
import chromadb
from sentence_transformers import SentenceTransformer
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
import asyncio

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutobotLocalTrainer:
    """Sistema de treinamento de IA local para AUTOBOT"""
    
    def __init__(self, chroma_path: str = "IA/memoria_vetorial"):
        """
        Inicializa o sistema de treinamento de IA local
        
        Args:
            chroma_path: Caminho para armazenar a base de dados vetorial
        """
        try:
            self.ollama_client = ollama.Client()
            self.chroma_client = chromadb.PersistentClient(path=chroma_path)
            self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ AutobotLocalTrainer inicializado com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar AutobotLocalTrainer: {e}")
            raise
        
    def setup_ollama_models(self) -> Dict[str, str]:
        """
        Configura modelos Ollama locais essenciais
        
        Returns:
            Dict com status de cada modelo instalado
        """
        models = ['llama3', 'mistral', 'tinyllama']
        status = {}
        
        logger.info("🦙 Iniciando configuração de modelos Ollama...")
        
        for model in models:
            try:
                logger.info(f"📥 Baixando modelo {model}...")
                self.ollama_client.pull(model)
                status[model] = "✅ Instalado com sucesso"
                logger.info(f"✅ Modelo {model} instalado")
            except Exception as e:
                status[model] = f"⚠️ Erro: {str(e)}"
                logger.error(f"⚠️ Erro ao instalar {model}: {e}")
        
        return status
    
    def create_knowledge_base(self, training_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Cria base de conhecimento vetorial com dados de treinamento
        
        Args:
            training_data: Lista de dicionários com 'pergunta', 'resposta' e 'fonte'
            
        Returns:
            Dict com status da criação da base de conhecimento
        """
        try:
            collection = self.chroma_client.get_or_create_collection("autobot_knowledge")
            
            logger.info(f"📚 Criando base de conhecimento com {len(training_data)} itens...")
            
            for i, data in enumerate(training_data):
                pergunta = data.get('pergunta', '')
                resposta = data.get('resposta', '')
                fonte = data.get('fonte', 'treinamento')
                
                if not pergunta or not resposta:
                    logger.warning(f"⚠️ Item {i} inválido - pergunta ou resposta vazia")
                    continue
                
                # Cria embedding da pergunta
                embedding = self.encoder.encode(pergunta)
                
                # Adiciona à coleção
                collection.add(
                    embeddings=[embedding.tolist()],
                    documents=[resposta],
                    metadatas=[{"fonte": fonte, "pergunta": pergunta}],
                    ids=[f"doc_{i}"]
                )
            
            logger.info("✅ Base de conhecimento criada com sucesso")
            return {
                "status": "success", 
                "message": f"Base de conhecimento criada com {len(training_data)} itens",
                "total_items": len(training_data)
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar base de conhecimento: {e}")
            return {"status": "error", "erro": str(e)}
    
    def train_custom_model(self, exemplos_treinamento: str, nome_modelo: str = "autobot-personalizado") -> Dict[str, Any]:
        """
        Treina modelo personalizado baseado no AIEngine existente
        
        Args:
            exemplos_treinamento: String com exemplos de treinamento
            nome_modelo: Nome do modelo personalizado a ser criado
            
        Returns:
            Dict com status do treinamento
        """
        try:
            logger.info(f"🧠 Iniciando treinamento do modelo {nome_modelo}...")
            
            # Cria modelfile personalizado
            modelfile = f"""FROM llama3
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40

SYSTEM \"\"\"
Você é o AUTOBOT, um assistente de IA especializado em:
- Automação de tarefas corporativas
- Integração com Bitrix24, IXCSOFT, Locaweb
- Análise de dados e métricas empresariais
- Controle de sistemas via interface
- Processamento de documentos e OCR
- Automação com PyAutoGUI e Selenium

Suas características:
- Respostas precisas e técnicas
- Foco em soluções práticas
- Conhecimento em integrações corporativas
- Expertise em automação de processos

Exemplos de treinamento:
{exemplos_treinamento}

Sempre forneça respostas detalhadas e práticas para ajudar com automação e integrações corporativas.
\"\"\"
"""
            
            # Cria o modelo personalizado
            self.ollama_client.create(model=nome_modelo, modelfile=modelfile)
            
            logger.info(f"✅ Modelo {nome_modelo} criado com sucesso")
            return {
                "status": "success", 
                "modelo": nome_modelo,
                "message": f"Modelo {nome_modelo} treinado e disponível"
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao treinar modelo: {e}")
            return {"status": "error", "erro": str(e)}
    
    def test_model(self, modelo: str = "autobot-personalizado", pergunta: str = "Como posso automatizar uma tarefa?") -> Dict[str, Any]:
        """
        Testa um modelo treinado com uma pergunta de exemplo
        
        Args:
            modelo: Nome do modelo a ser testado
            pergunta: Pergunta de teste
            
        Returns:
            Dict com resposta do modelo e status
        """
        try:
            logger.info(f"🧪 Testando modelo {modelo}...")
            
            response = self.ollama_client.generate(
                model=modelo,
                prompt=pergunta
            )
            
            resposta = response.get('response', 'Sem resposta')
            
            logger.info(f"✅ Teste do modelo {modelo} concluído")
            return {
                "status": "success",
                "modelo": modelo,
                "pergunta": pergunta,
                "resposta": resposta
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao testar modelo: {e}")
            return {"status": "error", "erro": str(e)}
    
    def list_available_models(self) -> List[str]:
        """
        Lista modelos disponíveis no Ollama
        
        Returns:
            Lista de nomes dos modelos disponíveis
        """
        try:
            models = self.ollama_client.list()
            model_names = [model['name'] for model in models.get('models', [])]
            logger.info(f"📋 Modelos disponíveis: {model_names}")
            return model_names
        except Exception as e:
            logger.error(f"❌ Erro ao listar modelos: {e}")
            return []
    
    def get_model_info(self, modelo: str) -> Dict[str, Any]:
        """
        Obtém informações detalhadas sobre um modelo
        
        Args:
            modelo: Nome do modelo
            
        Returns:
            Dict com informações do modelo
        """
        try:
            info = self.ollama_client.show(modelo)
            return {"status": "success", "info": info}
        except Exception as e:
            logger.error(f"❌ Erro ao obter info do modelo {modelo}: {e}")
            return {"status": "error", "erro": str(e)}

# Função de teste para validar a instalação
def test_installation():
    """Testa a instalação e configuração do sistema"""
    try:
        trainer = AutobotLocalTrainer()
        
        # Testa dados de exemplo
        dados_exemplo = [
            {
                "pergunta": "Como integrar com Bitrix24?",
                "resposta": "Para integrar com Bitrix24, use a API REST com webhook configurado para receber eventos em tempo real.",
                "fonte": "documentacao_bitrix"
            },
            {
                "pergunta": "Como automatizar click em botão?",
                "resposta": "Use PyAutoGUI.click(x, y) para clicar em coordenadas específicas ou pyautogui.click('imagem.png') para localizar por imagem.",
                "fonte": "automacao_gui"
            }
        ]
        
        # Cria base de conhecimento
        result = trainer.create_knowledge_base(dados_exemplo)
        print(f"Base de conhecimento: {result}")
        
        # Lista modelos
        models = trainer.list_available_models()
        print(f"Modelos disponíveis: {models}")
        
        print("✅ Teste de instalação concluído com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de instalação: {e}")
        return False

if __name__ == "__main__":
    print("🧠 AUTOBOT - Sistema de Treinamento de IA Local")
    print("=" * 50)
    
    if test_installation():
        print("\n🚀 Sistema pronto para uso!")
        print("Execute: python -c 'from IA.treinamento.local_trainer import AutobotLocalTrainer; trainer = AutobotLocalTrainer()'")
    else:
        print("\n⚠️ Problemas na instalação detectados. Verifique as dependências.")