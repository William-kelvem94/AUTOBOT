# Multi-stage build for production optimization
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    git \
    curl \
    wget \
    unzip \
    sqlite3 \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -s /bin/bash autobot && \
    mkdir -p /app /app/data /app/logs /app/config && \
    chown -R autobot:autobot /app

WORKDIR /app

# Install Python dependencies
COPY requirements*.txt ./
RUN pip install --no-cache-dir -r requirements_ia.txt

# Development stage
FROM base as development

# Copy application code
COPY --chown=autobot:autobot . .

# Switch to non-root user
USER autobot

# Expose ports
EXPOSE 5000 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Default command
CMD ["python", "-m", "autobot.api"]

# Production stage
FROM base as production

# Copy only necessary files
COPY --chown=autobot:autobot autobot/ ./autobot/
COPY --chown=autobot:autobot IA/ ./IA/
COPY --chown=autobot:autobot web/build/ ./web/build/
COPY --chown=autobot:autobot requirements*.txt ./

# Install production dependencies only
RUN pip install --no-cache-dir -r requirements.txt

# Switch to non-root user
USER autobot

# Expose ports
EXPOSE 5000 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Production command with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "autobot.api:app"]