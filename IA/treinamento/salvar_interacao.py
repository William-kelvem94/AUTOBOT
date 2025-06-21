import json
from datetime import datetime
import os

def salvar_interacao(prompt, resposta):
    os.makedirs("IA/treinamento/dados_uso", exist_ok=True)
    with open("IA/treinamento/dados_uso/uso_real.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "resposta": resposta
        }) + "\n")

if __name__ == "__main__":
    salvar_interacao("Exemplo de prompt", "Exemplo de resposta")
    print("Interação salva em IA/treinamento/dados_uso/uso_real.jsonl")
