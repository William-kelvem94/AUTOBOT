from flask import Flask, request, jsonify
from flask_cors import CORS
from autobot.gemini import gemini_ask
from IA.treinamento.ollama_integration import perguntar_ollama
import subprocess
import json
import os

app = Flask(__name__)
CORS(app)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    prompt = data.get('prompt', '')
    ia = data.get('ia', 'gemini')  # padrão: gemini
    if not prompt:
        return jsonify({'error': 'Prompt vazio'}), 400
    if ia == 'ollama':
        resposta = perguntar_ollama(prompt)
    else:
        resposta = gemini_ask(prompt)
    return jsonify({'resposta': resposta})

@app.route('/api/train', methods=['POST'])
def train():
    data = request.json
    exemplos = data.get('exemplos', '')
    # Salva exemplos no dataset se enviados
    if exemplos.strip():
        dataset_path = 'IA/treinamento/meu_dataset.jsonl'
        with open(dataset_path, 'a', encoding='utf-8') as f:
            for linha in exemplos.strip().split('\n'):
                if '|' in linha:
                    pergunta, resposta = linha.split('|', 1)
                    f.write(json.dumps({"prompt": pergunta.strip(), "resposta": resposta.strip()}) + "\n")
    # Executa o script de treinamento real
    try:
        result = subprocess.run(
            ["python", "IA/treinamento/finetune_llm.py"],
            capture_output=True, text=True, check=True
        )
        return jsonify({"status": "ok", "output": result.stdout})
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "erro", "output": e.stderr}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
