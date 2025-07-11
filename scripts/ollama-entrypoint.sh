#!/bin/sh
# Enhanced Ollama entrypoint with model management and health checks

set -e

# Configuration
MODEL=${OLLAMA_MODEL:-llama3}
HOST=${OLLAMA_HOST:-0.0.0.0}
PORT=${OLLAMA_PORT:-11434}

echo "Starting Ollama server on $HOST:$PORT"

# Start Ollama server in background
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "Waiting for Ollama to start..."
for i in $(seq 1 30); do
    if curl -s "http://localhost:$PORT/api/tags" > /dev/null 2>&1; then
        echo "Ollama is ready!"
        break
    fi
    echo "Waiting for Ollama... ($i/30)"
    sleep 2
done

# Check if Ollama started successfully
if ! curl -s "http://localhost:$PORT/api/tags" > /dev/null 2>&1; then
    echo "Failed to start Ollama server"
    exit 1
fi

# Pull the specified model if it doesn't exist
echo "Checking for model: $MODEL"
if ! ollama list | grep -q "$MODEL"; then
    echo "Pulling model: $MODEL"
    ollama pull "$MODEL" || {
        echo "Failed to pull model $MODEL, trying fallback models..."
        
        # Try fallback models
        for fallback in "llama2" "codellama" "mistral"; do
            echo "Trying fallback model: $fallback"
            if ollama pull "$fallback"; then
                echo "Successfully pulled fallback model: $fallback"
                break
            fi
        done
    }
else
    echo "Model $MODEL is already available"
fi

# List available models
echo "Available models:"
ollama list

# Keep the container running and forward signals
trap "kill $OLLAMA_PID; wait $OLLAMA_PID" TERM INT

# Wait for the Ollama process
wait $OLLAMA_PID