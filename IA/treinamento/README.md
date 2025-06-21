# Treinamento de IA Local para Integração com Bitrix24

Este diretório contém tudo o que você precisa para treinar, rodar e integrar uma IA local (LLM) ao seu bot Bitrix24.

## 1. Modelos recomendados
- Llama 3 (Meta)
- Mistral
- Phi-3 (Microsoft)
- Falcon, Zephyr, Vicuna, OpenHermes, MythoMax

## 2. Ferramentas sugeridas
- [Ollama](https://ollama.com/) — para rodar modelos LLM localmente com facilidade
- [LM Studio](https://lmstudio.ai/) — interface gráfica para rodar e testar modelos
- [HuggingFace Transformers](https://huggingface.co/docs/transformers/index) — para customização e treinamento avançado

## 3. Como rodar um modelo local (exemplo com Ollama)
1. Instale o Ollama: https://ollama.com/download
2. No terminal, rode:
   ```
   ollama run llama3
   ```
3. Para integração Python, use:
   ```python
   import requests
   def perguntar_ollama(prompt):
       resp = requests.post('http://localhost:11434/api/generate', json={
           'model': 'llama3',
           'prompt': prompt
       })
       return resp.json()['response']
   ```

## 4. Treinamento e ajuste fino
- Para treinar ou ajustar o modelo, use datasets em português e scripts de fine-tuning do HuggingFace.
- Coloque seus dados de treinamento nesta pasta.

## 5. Integração com o bot
- O bot envia comandos do usuário para o modelo local.
- O modelo interpreta e retorna a ação (ex: listar tarefas, responder tarefa, etc).
- O bot executa a ação via webhook Bitrix24.

## 6. Segurança
- Tudo roda localmente, sem custos por requisição e com privacidade total.

---

Coloque aqui seus scripts, datasets e instruções de treinamento personalizados.
