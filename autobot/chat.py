import sys
import os

from autobot.main import listar_tarefas_pendentes, responder_tarefa
from autobot.gemini import gemini_ask

def processa_comando(comando):
    # Interpretação simples de comandos (sem IA)
    if comando.lower().startswith("listar"):
        listar_tarefas_pendentes()
    elif comando.lower().startswith("responder"):
        partes = comando.split()
        if len(partes) >= 3:
            task_id = partes[1]
            mensagem = " ".join(partes[2:])
            responder_tarefa(task_id, mensagem)
        else:
            print("Comando de resposta incompleto.")
    elif comando.lower().startswith("treinar"):
        import os
        os.system("python IA/treinamento/finetune_llm.py")
    elif comando.lower().startswith("gemini"):
        prompt = comando[len("gemini"):].strip()
        if prompt:
            resposta = gemini_ask(prompt)
            print("Gemini:", resposta)
        else:
            print("Forneça um prompt após o comando 'gemini'.")
    else:
        print("Comando não reconhecido. Use: listar, responder <id> <mensagem>, treinar ou gemini <prompt>.")

if __name__ == "__main__":
    print("Chat do Autobot Bitrix24 (digite 'sair' para encerrar):")
    while True:
        comando = input("> ")
        if comando.lower() in ["sair", "exit", "quit"]:
            break
        processa_comando(comando)
