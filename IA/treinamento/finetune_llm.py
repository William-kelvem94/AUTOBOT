from datasets import load_dataset, Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
import json
import os

# Modelo base sugerido (pode trocar por outro HuggingFace)
model_name = "mistralai/Mistral-7B-Instruct-v0.2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

def carregar_dados_customizados():
    dados = []
    # Carrega dataset de exemplo
    with open("IA/treinamento/meu_dataset.jsonl", encoding="utf-8") as f:
        for linha in f:
            dados.append(json.loads(linha))
    # Carrega dados de uso real, se existirem
    uso_real_path = "IA/treinamento/dados_uso/uso_real.jsonl"
    if os.path.exists(uso_real_path):
        with open(uso_real_path, encoding="utf-8") as f:
            for linha in f:
                dados.append(json.loads(linha))
    return Dataset.from_list([{"text": f"Usuário: {d['prompt']}\nBot: {d['resposta']}"} for d in dados])

def preprocess(example):
    return tokenizer(example["text"], truncation=True, padding="max_length", max_length=512)

dataset = carregar_dados_customizados()
tokenized = dataset.map(preprocess, batched=True)

args = TrainingArguments(
    output_dir="./results",
    per_device_train_batch_size=2,
    num_train_epochs=1,
    save_steps=100,
    logging_steps=10,
    fp16=True,
)

trainer = Trainer(
    model=model,
    args=args,
    train_dataset=tokenized,
)

if __name__ == "__main__":
    trainer.train()
    print("Fine-tuning concluído!")
