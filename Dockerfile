FROM python:3.11-slim

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Define diretório de trabalho
WORKDIR /app

# Copia arquivos de dependências
COPY requirements.txt .

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia código da aplicação
COPY . .

# Cria diretórios necessários
RUN mkdir -p IA/logs IA/memoria_conversas

# Expõe porta
EXPOSE 5000

# Define variáveis de ambiente
ENV FLASK_APP=autobot.api:create_app
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Comando de inicialização
CMD ["python", "main.py"]