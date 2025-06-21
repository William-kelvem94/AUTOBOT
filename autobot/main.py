import os
import sys
import requests
from dotenv import load_dotenv
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../IA/treinamento')))

try:
    from IA.treinamento.salvar_interacao import salvar_interacao
except ImportError:
    def salvar_interacao(prompt, resposta):
        pass  # fallback se não encontrar o script

load_dotenv()
BITRIX_WEBHOOK_URL = os.getenv("BITRIX_WEBHOOK_URL")

if not BITRIX_WEBHOOK_URL:
    print("Configure o BITRIX_WEBHOOK_URL no arquivo .env")
    sys.exit(1)

def listar_tarefas_pendentes():
    url = f"{BITRIX_WEBHOOK_URL}tasks.task.list"
    params = {
        "filter": {"REAL_STATUS": [2, 3]},
        "select": ["ID", "TITLE", "RESPONSIBLE_ID", "STATUS", "DEADLINE"]
    }
    resp = requests.post(url, json=params)
    resposta = ""
    if resp.ok:
        result = resp.json().get('result', {})
        tasks = result.get('tasks', [])
        if not tasks:
            resposta = "Nenhuma tarefa pendente encontrada."
            print(resposta)
        else:
            resposta = "Tarefas pendentes:\n" + "\n".join([
                f"ID: {t.get('ID')} | {t.get('TITLE')} | Prazo: {t.get('DEADLINE')}" for t in tasks
            ])
            print(resposta)
    else:
        resposta = f"Erro ao buscar tarefas {resp.text}"
        print(resposta)
    salvar_interacao("listar tarefas pendentes", resposta)

def responder_tarefa(task_id, mensagem):
    url = f"{BITRIX_WEBHOOK_URL}task.commentitem.add"
    params = {"task_id": task_id, "fields": {"POST_MESSAGE": mensagem}}
    resp = requests.post(url, json=params)
    resposta = ""
    if resp.ok:
        resposta = "Comentário enviado com sucesso!"
        print(resposta)
    else:
        resposta = f"Erro ao enviar comentário {resp.text}"
        print(resposta)
    salvar_interacao(f"responder tarefa {task_id} {mensagem}", resposta)

def main():
    if len(sys.argv) < 2:
        print("Comandos disponíveis: listar, responder <id> <mensagem>, treinar")
        return
    cmd = sys.argv[1]
    if cmd == "listar":
        listar_tarefas_pendentes()
    elif cmd == "responder" and len(sys.argv) >= 4:
        responder_tarefa(sys.argv[2], " ".join(sys.argv[3:]))
    elif cmd == "treinar":
        os.system("python IA/treinamento/finetune_llm.py")
    else:
        print("Comando inválido.")

if __name__ == "__main__":
    main()
