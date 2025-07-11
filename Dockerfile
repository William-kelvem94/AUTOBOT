# Enhanced AUTOBOT Dockerfile with optimized dependencies
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with optimization
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY autobot/ ./autobot/
COPY IA/ ./IA/
COPY metrics/ ./metrics/
COPY database/ ./database/
COPY scripts/ ./scripts/

# Create necessary directories
RUN mkdir -p logs database/backups web/dist

# Copy environment template
COPY .env.example .env

# Set Python path
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Expose ports
EXPOSE 5000 3000

# Default command
CMD ["python", "-m", "autobot.api"]