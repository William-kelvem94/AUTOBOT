"""
Gerenciador de memória persistente para conversas do AUTOBOT
Implementa armazenamento vetorial com ChromaDB para aprendizado contínuo
"""

import chromadb
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from sentence_transformers import SentenceTransformer
import json
import hashlib

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutobotMemoryManager:
    """Gerenciador de memória persistente para conversas e conhecimento"""
    
    def __init__(self, memory_path: str = "IA/memoria_conversas"):
        """
        Inicializa o gerenciador de memória
        
        Args:
            memory_path: Caminho para armazenar a memória persistente
        """
        try:
            self.client = chromadb.PersistentClient(path=memory_path)
            self.conversations = self.client.get_or_create_collection("conversas")
            self.knowledge = self.client.get_or_create_collection("conhecimento")
            self.user_preferences = self.client.get_or_create_collection("preferencias_usuario")
            self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
            
            logger.info("✅ AutobotMemoryManager inicializado com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar AutobotMemoryManager: {e}")
            raise
    
    def salvar_conversa(self, usuario: str, pergunta: str, resposta: str, 
                       contexto: Optional[str] = None, categoria: str = "geral") -> Dict[str, Any]:
        """
        Salva conversa para aprendizado contínuo
        
        Args:
            usuario: ID ou nome do usuário
            pergunta: Pergunta feita pelo usuário
            resposta: Resposta gerada pelo sistema
            contexto: Contexto adicional da conversa
            categoria: Categoria da conversa (automacao, integracao, etc.)
            
        Returns:
            Dict com status da operação
        """
        try:
            timestamp = datetime.now().isoformat()
            conversa_id = self._generate_conversation_id(usuario, pergunta, timestamp)
            
            # Cria embedding da pergunta para busca semântica
            embedding = self.encoder.encode(pergunta)
            
            # Prepara documento da conversa
            documento = f"Usuário: {usuario}\nPergunta: {pergunta}\nResposta: {resposta}"
            if contexto:
                documento += f"\nContexto: {contexto}"
            
            # Metadados da conversa
            metadados = {
                "usuario": usuario,
                "timestamp": timestamp,
                "contexto": contexto or "",
                "categoria": categoria,
                "data_formatada": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Salva na coleção de conversas
            self.conversations.add(
                embeddings=[embedding.tolist()],
                documents=[documento],
                metadatas=[metadados],
                ids=[conversa_id]
            )
            
            logger.info(f"💾 Conversa salva: {usuario} - {categoria}")
            return {
                "status": "success", 
                "conversa_id": conversa_id,
                "message": "Conversa salva com sucesso"
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar conversa: {e}")
            return {"status": "error", "erro": str(e)}
    
    def buscar_contexto(self, pergunta: str, usuario: Optional[str] = None, 
                       limite: int = 5, categoria: Optional[str] = None) -> Dict[str, Any]:
        """
        Busca contexto relevante na memória usando similaridade semântica
        
        Args:
            pergunta: Pergunta para buscar contexto
            usuario: Filtrar por usuário específico (opcional)
            limite: Número máximo de resultados
            categoria: Filtrar por categoria (opcional)
            
        Returns:
            Dict com contexto relevante encontrado
        """
        try:
            # Prepara filtros de metadados
            where_filter = {}
            if usuario:
                where_filter["usuario"] = usuario
            if categoria:
                where_filter["categoria"] = categoria
            
            # Busca conversas similares
            kwargs = {
                "query_texts": [pergunta],
                "n_results": limite
            }
            
            if where_filter:
                kwargs["where"] = where_filter
            
            results = self.conversations.query(**kwargs)
            
            if not results["documents"] or not results["documents"][0]:
                return {
                    "contexto_relevante": [],
                    "metadados": [],
                    "total_encontrado": 0
                }
            
            contexto_relevante = results["documents"][0]
            metadados = results["metadatas"][0]
            distancias = results.get("distances", [[]])[0]
            
            # Adiciona score de relevância
            contexto_com_score = []
            for i, (doc, meta, dist) in enumerate(zip(contexto_relevante, metadados, distancias)):
                contexto_com_score.append({
                    "documento": doc,
                    "metadados": meta,
                    "score_relevancia": 1 - dist,  # Converte distância em score
                    "posicao": i + 1
                })
            
            logger.info(f"🔍 Encontrado {len(contexto_relevante)} contextos relevantes")
            return {
                "contexto_relevante": contexto_com_score,
                "metadados": metadados,
                "total_encontrado": len(contexto_relevante)
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar contexto: {e}")
            return {"contexto_relevante": [], "metadados": [], "total_encontrado": 0}
    
    def salvar_conhecimento_especializado(self, topico: str, conteudo: str, 
                                        fonte: str = "manual", tags: List[str] = None) -> Dict[str, Any]:
        """
        Salva conhecimento especializado para consulta posterior
        
        Args:
            topico: Tópico do conhecimento
            conteudo: Conteúdo detalhado
            fonte: Fonte do conhecimento
            tags: Tags para categorização
            
        Returns:
            Dict com status da operação
        """
        try:
            timestamp = datetime.now().isoformat()
            conhecimento_id = self._generate_knowledge_id(topico, fonte, timestamp)
            
            # Cria embedding do tópico
            embedding = self.encoder.encode(topico)
            
            # Metadados do conhecimento
            metadados = {
                "topico": topico,
                "fonte": fonte,
                "timestamp": timestamp,
                "tags": json.dumps(tags or []),
                "data_formatada": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Salva na coleção de conhecimento
            self.knowledge.add(
                embeddings=[embedding.tolist()],
                documents=[conteudo],
                metadatas=[metadados],
                ids=[conhecimento_id]
            )
            
            logger.info(f"📚 Conhecimento salvo: {topico}")
            return {
                "status": "success",
                "conhecimento_id": conhecimento_id,
                "message": "Conhecimento salvo com sucesso"
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar conhecimento: {e}")
            return {"status": "error", "erro": str(e)}
    
    def buscar_conhecimento(self, consulta: str, limite: int = 3) -> Dict[str, Any]:
        """
        Busca conhecimento especializado relevante
        
        Args:
            consulta: Consulta para buscar conhecimento
            limite: Número máximo de resultados
            
        Returns:
            Dict com conhecimento relevante
        """
        try:
            results = self.knowledge.query(
                query_texts=[consulta],
                n_results=limite
            )
            
            if not results["documents"] or not results["documents"][0]:
                return {"conhecimento": [], "total_encontrado": 0}
            
            conhecimento = []
            for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
                conhecimento.append({
                    "conteudo": doc,
                    "topico": meta.get("topico", ""),
                    "fonte": meta.get("fonte", ""),
                    "tags": json.loads(meta.get("tags", "[]")),
                    "data": meta.get("data_formatada", "")
                })
            
            logger.info(f"📖 Encontrado {len(conhecimento)} itens de conhecimento")
            return {
                "conhecimento": conhecimento,
                "total_encontrado": len(conhecimento)
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar conhecimento: {e}")
            return {"conhecimento": [], "total_encontrado": 0}
    
    def salvar_preferencia_usuario(self, usuario: str, preferencia: str, 
                                 valor: Any, categoria: str = "geral") -> Dict[str, Any]:
        """
        Salva preferências específicas do usuário
        
        Args:
            usuario: ID do usuário
            preferencia: Nome da preferência
            valor: Valor da preferência
            categoria: Categoria da preferência
            
        Returns:
            Dict com status da operação
        """
        try:
            timestamp = datetime.now().isoformat()
            pref_id = f"{usuario}_{preferencia}_{categoria}"
            
            # Documento da preferência
            documento = f"Usuário: {usuario}\nPreferência: {preferencia}\nValor: {json.dumps(valor)}"
            
            # Metadados
            metadados = {
                "usuario": usuario,
                "preferencia": preferencia,
                "categoria": categoria,
                "timestamp": timestamp,
                "valor": json.dumps(valor)
            }
            
            # Embedding da preferência
            embedding = self.encoder.encode(f"{preferencia} {categoria}")
            
            # Upsert (atualiza ou insere)
            self.user_preferences.upsert(
                embeddings=[embedding.tolist()],
                documents=[documento],
                metadatas=[metadados],
                ids=[pref_id]
            )
            
            logger.info(f"⚙️ Preferência salva: {usuario} - {preferencia}")
            return {"status": "success", "message": "Preferência salva"}
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar preferência: {e}")
            return {"status": "error", "erro": str(e)}
    
    def obter_preferencias_usuario(self, usuario: str) -> Dict[str, Any]:
        """
        Obtém todas as preferências de um usuário
        
        Args:
            usuario: ID do usuário
            
        Returns:
            Dict com preferências do usuário
        """
        try:
            results = self.user_preferences.get(
                where={"usuario": usuario}
            )
            
            preferencias = {}
            for meta in results.get("metadatas", []):
                pref_nome = meta.get("preferencia", "")
                pref_valor = json.loads(meta.get("valor", "null"))
                categoria = meta.get("categoria", "geral")
                
                if categoria not in preferencias:
                    preferencias[categoria] = {}
                
                preferencias[categoria][pref_nome] = pref_valor
            
            logger.info(f"👤 Carregadas preferências do usuário: {usuario}")
            return {"status": "success", "preferencias": preferencias}
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter preferências: {e}")
            return {"status": "error", "erro": str(e)}
    
    def estatisticas_memoria(self) -> Dict[str, Any]:
        """
        Retorna estatísticas da memória do sistema
        
        Returns:
            Dict com estatísticas detalhadas
        """
        try:
            # Conta itens em cada coleção
            conv_count = self.conversations.count()
            know_count = self.knowledge.count()
            pref_count = self.user_preferences.count()
            
            # Estatísticas por categoria (conversas)
            conversas_por_categoria = {}
            try:
                all_conv = self.conversations.get()
                for meta in all_conv.get("metadatas", []):
                    categoria = meta.get("categoria", "geral")
                    conversas_por_categoria[categoria] = conversas_por_categoria.get(categoria, 0) + 1
            except:
                conversas_por_categoria = {"erro": "Não foi possível calcular"}
            
            # Usuários únicos
            usuarios_unicos = set()
            try:
                all_conv = self.conversations.get()
                for meta in all_conv.get("metadatas", []):
                    usuario = meta.get("usuario", "")
                    if usuario:
                        usuarios_unicos.add(usuario)
            except:
                pass
            
            estatisticas = {
                "total_conversas": conv_count,
                "total_conhecimento": know_count,
                "total_preferencias": pref_count,
                "usuarios_unicos": len(usuarios_unicos),
                "conversas_por_categoria": conversas_por_categoria,
                "ultima_atualizacao": datetime.now().isoformat()
            }
            
            logger.info("📊 Estatísticas de memória calculadas")
            return {"status": "success", "estatisticas": estatisticas}
            
        except Exception as e:
            logger.error(f"❌ Erro ao calcular estatísticas: {e}")
            return {"status": "error", "erro": str(e)}
    
    def limpar_memoria_antiga(self, dias: int = 30) -> Dict[str, Any]:
        """
        Remove conversas mais antigas que o número especificado de dias
        
        Args:
            dias: Número de dias para manter as conversas
            
        Returns:
            Dict com resultado da limpeza
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=dias)
            cutoff_iso = cutoff_date.isoformat()
            
            # Busca conversas antigas
            all_conversations = self.conversations.get()
            ids_para_remover = []
            
            for i, meta in enumerate(all_conversations.get("metadatas", [])):
                timestamp = meta.get("timestamp", "")
                if timestamp and timestamp < cutoff_iso:
                    ids_para_remover.append(all_conversations["ids"][i])
            
            # Remove conversas antigas
            if ids_para_remover:
                self.conversations.delete(ids=ids_para_remover)
                
            logger.info(f"🧹 Removidas {len(ids_para_remover)} conversas antigas")
            return {
                "status": "success",
                "removidas": len(ids_para_remover),
                "message": f"Limpeza concluída: {len(ids_para_remover)} itens removidos"
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na limpeza de memória: {e}")
            return {"status": "error", "erro": str(e)}
    
    def _generate_conversation_id(self, usuario: str, pergunta: str, timestamp: str) -> str:
        """Gera ID único para conversa"""
        content = f"{usuario}_{pergunta}_{timestamp}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _generate_knowledge_id(self, topico: str, fonte: str, timestamp: str) -> str:
        """Gera ID único para conhecimento"""
        content = f"{topico}_{fonte}_{timestamp}"
        return hashlib.md5(content.encode()).hexdigest()

# Função de teste
def test_memory_manager():
    """Testa o gerenciador de memória"""
    try:
        memory = AutobotMemoryManager()
        
        # Teste 1: Salvar conversa
        result = memory.salvar_conversa(
            usuario="teste_user",
            pergunta="Como automatizar um processo?",
            resposta="Use PyAutoGUI para automatizar interfaces gráficas",
            categoria="automacao"
        )
        print(f"Salvar conversa: {result}")
        
        # Teste 2: Buscar contexto
        contexto = memory.buscar_contexto("automatizar processo")
        print(f"Buscar contexto: {contexto['total_encontrado']} itens encontrados")
        
        # Teste 3: Salvar conhecimento
        knowledge_result = memory.salvar_conhecimento_especializado(
            topico="Integração Bitrix24",
            conteudo="Para integrar com Bitrix24, configure webhook e use API REST",
            fonte="documentacao",
            tags=["bitrix24", "integracao", "api"]
        )
        print(f"Salvar conhecimento: {knowledge_result}")
        
        # Teste 4: Estatísticas
        stats = memory.estatisticas_memoria()
        print(f"Estatísticas: {stats}")
        
        print("✅ Teste do Memory Manager concluído com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

if __name__ == "__main__":
    print("💾 AUTOBOT - Gerenciador de Memória")
    print("=" * 40)
    
    if test_memory_manager():
        print("\n🚀 Memory Manager pronto para uso!")
    else:
        print("\n⚠️ Problemas detectados no Memory Manager")