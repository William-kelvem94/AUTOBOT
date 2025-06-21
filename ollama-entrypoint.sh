#!/bin/sh
set -e

# Baixa o modelo llama3 se não existir
ollama pull llama3 || true

# Inicia o Ollama normalmente
exec /usr/bin/ollama serve
