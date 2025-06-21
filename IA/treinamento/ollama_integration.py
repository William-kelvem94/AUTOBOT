import os
import requests

# Altere o endpoint do Ollama para usar o nome do serviço Docker
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "ollama")
OLLAMA_PORT = os.getenv("OLLAMA_PORT", "11434")
OLLAMA_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"

def perguntar_ollama(prompt, model="llama3"):
    """
    Envia um prompt para o modelo LLM rodando localmente via Ollama.
    Requer Ollama rodando em http://ollama:11434 (rede Docker Compose)
    """
    resp = requests.post(f'{OLLAMA_URL}/api/generate', json={
        'model': model,
        'prompt': prompt
    })
    if resp.ok:
        return resp.json().get('response', '').strip()
    else:
        return f"[ERRO OLLAMA] {resp.text}"

if __name__ == "__main__":
    print("Teste rápido do modelo local via Ollama!")
    while True:
        prompt = input("Prompt para IA (ou 'sair'): ")
        if prompt.lower() in ["sair", "exit", "quit"]:
            break
        resposta = perguntar_ollama(prompt)
        print("IA:", resposta)
