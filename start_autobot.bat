@echo off
echo 🤖 AUTOBOT - Sistema de IA Corporativa
echo =====================================

cd /d "%~dp0"

echo 🔍 Verificando ambiente...
if not exist ".venv" (
    echo ❌ Ambiente virtual não encontrado!
    echo 📦 Criando ambiente virtual...
    python -m venv .venv
    if errorlevel 1 (
        echo ❌ Erro ao criar ambiente virtual
        pause
        exit /b 1
    )
)

echo 🔄 Ativando ambiente virtual...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Erro ao ativar ambiente virtual
    pause
    exit /b 1
)

echo 📦 Verificando dependências...
python -c "import flask" 2>nul || (
    echo 📥 Instalando dependências...
    python setup_automatico.py
    if errorlevel 1 (
        echo ❌ Erro na instalação de dependências
        pause
        exit /b 1
    )
)

echo 🗄️ Verificando banco de dados...
if not exist "metrics\autobot_metrics.db" (
    echo 📊 Criando banco de métricas...
    python setup_automatico.py
)

echo 🔍 Verificando health do sistema...
python -c "
try:
    import requests
    import psutil
    import sqlite3
    print('✅ Dependências principais OK')
except ImportError as e:
    print(f'⚠️ Dependência faltando: {e}')
"

echo.
echo 🚀 Iniciando AUTOBOT Backend...
start "AUTOBOT Backend" cmd /k "python dev_server.py"

echo ⏳ Aguardando backend inicializar...
timeout /t 5 /nobreak >nul

echo 🌐 Verificando se frontend existe...
if exist "web\package.json" (
    echo 🌐 Iniciando interface web...
    cd web
    if not exist "node_modules" (
        echo 📦 Instalando dependências do frontend...
        npm install
    )
    start "AUTOBOT Frontend" cmd /k "npm run dev"
    cd ..
) else (
    echo ⚠️ Frontend não encontrado, apenas backend será executado
)

echo.
echo ✅ AUTOBOT iniciado com sucesso!
echo.
echo 🌐 Endpoints disponíveis:
echo   Backend: http://localhost:5000
echo   Health Check: http://localhost:5000/api/health/detailed
echo   Métricas: http://localhost:5000/api/metrics
if exist "web\package.json" (
    echo   Frontend: http://localhost:5173
)
echo.
echo 📋 Para parar o AUTOBOT:
echo   - Feche as janelas dos terminais
echo   - Ou pressione Ctrl+C em cada terminal
echo.
pause