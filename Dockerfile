# Dockerfile para Autobot Bitrix24 com IA local
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install torch --extra-index-url https://download.pytorch.org/whl/cpu
COPY autobot/ ./autobot/
COPY IA/ ./IA/
COPY .env .
CMD ["python", "-m", "autobot.main"]
