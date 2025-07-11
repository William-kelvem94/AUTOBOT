#!/bin/bash

echo "🤖 AUTOBOT - Sistema de IA Corporativa"
echo "====================================="

# Navega para o diretório do script
cd "$(dirname "$0")"

echo "🔍 Verificando ambiente..."
if [ ! -d ".venv" ]; then
    echo "❌ Ambiente virtual não encontrado!"
    echo "📦 Criando ambiente virtual..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "❌ Erro ao criar ambiente virtual"
        exit 1
    fi
fi

echo "🔄 Ativando ambiente virtual..."
source .venv/bin/activate
if [ $? -ne 0 ]; then
    echo "❌ Erro ao ativar ambiente virtual"
    exit 1
fi

echo "📦 Verificando dependências..."
python -c "import flask" 2>/dev/null || {
    echo "📥 Instalando dependências..."
    python setup_automatico.py
    if [ $? -ne 0 ]; then
        echo "❌ Erro na instalação de dependências"
        exit 1
    fi
}

echo "🗄️ Verificando banco de dados..."
if [ ! -f "metrics/autobot_metrics.db" ]; then
    echo "📊 Criando banco de métricas..."
    python setup_automatico.py
fi

echo "🔍 Verificando health do sistema..."
python -c "
try:
    import requests
    import psutil
    import sqlite3
    print('✅ Dependências principais OK')
except ImportError as e:
    print(f'⚠️ Dependência faltando: {e}')
"

echo ""
echo "🚀 Iniciando AUTOBOT Backend..."

# Função para cleanup ao sair
cleanup() {
    echo ""
    echo "🛑 Parando AUTOBOT..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
    fi
    echo "✅ AUTOBOT parado"
    exit 0
}

# Registra função de cleanup para SIGINT (Ctrl+C)
trap cleanup SIGINT SIGTERM

# Inicia backend em background
python dev_server.py &
BACKEND_PID=$!

echo "⏳ Aguardando backend inicializar..."
sleep 5

echo "🌐 Verificando se frontend existe..."
if [ -f "web/package.json" ]; then
    echo "🌐 Iniciando interface web..."
    cd web
    if [ ! -d "node_modules" ]; then
        echo "📦 Instalando dependências do frontend..."
        npm install
    fi
    npm run dev &
    FRONTEND_PID=$!
    cd ..
else
    echo "⚠️ Frontend não encontrado, apenas backend será executado"
fi

echo ""
echo "✅ AUTOBOT iniciado com sucesso!"
echo ""
echo "🌐 Endpoints disponíveis:"
echo "  Backend: http://localhost:5000"
echo "  Health Check: http://localhost:5000/api/health/detailed"
echo "  Métricas: http://localhost:5000/api/metrics"
if [ -f "web/package.json" ]; then
    echo "  Frontend: http://localhost:5173"
fi
echo ""
echo "📋 Para parar o AUTOBOT: Pressione Ctrl+C"
echo ""

# Mantém o script rodando
wait